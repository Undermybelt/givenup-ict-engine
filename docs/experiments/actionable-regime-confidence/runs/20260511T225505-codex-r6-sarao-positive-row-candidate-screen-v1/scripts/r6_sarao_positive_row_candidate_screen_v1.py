#!/usr/bin/env python3
"""Screen official CFTC PDFs for R6 positive direct-row candidates.

This run is intentionally read-only against the shared direct intake. It
materializes candidate rows into the run directory only, then computes a
what-if Wilson95 readback against the existing live positives and the accepted
Nasdaq ITCH sidecar broad-normal controls.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T225505-codex-r6-sarao-positive-row-candidate-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-sarao-positive-row-candidate-screen"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

RAW_ROOT = Path("/tmp/ict-engine-r6-sarao-positive-row-candidate-screen-v1/raw")
LIVE_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE_ROWS = LIVE_INTAKE / "positive_spoofing_layering_rows.csv"
SAME_EVENT_NEGATIVES = LIVE_INTAKE / "matched_negative_normal_activity_rows.csv"
SIDECAR_CONTROLS = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1"
    / "r6-broad-normal-order-lifecycle-screen"
    / "broad_normal_market_order_lifecycle_controls_v1.csv"
)
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

MIN_WILSON = 0.95
Z_95 = 1.96
ROW_FIELDS = [
    "label",
    "source_report",
    "source_section",
    "trade_date",
    "symbol",
    "venue_or_market_center",
    "participant_type_code",
    "participant_identifier",
    "side",
    "earliest_order_received_time",
    "latest_order_received_time",
    "order_count",
    "total_order_quantity",
    "activity_description",
    "matched_negative_group_id",
    "session_bucket",
    "source_row_id",
    "candidate_row_status",
]


@dataclass(frozen=True)
class SourcePdf:
    case_id: str
    url: str
    filename: str
    expected_use: str


SOURCES = [
    SourcePdf(
        "sarao_2015_complaint",
        "https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfsaraocomplaint041715.pdf",
        "enfsaraocomplaint041715.pdf",
        "primary candidate: exact dated/timed positive direct rows",
    ),
    SourcePdf(
        "falloon_2025_order",
        "https://www.cftc.gov/media/12656/enffalloonorder090925/download",
        "enffalloonorder090925.pdf",
        "screened aggregate public order, expected fail-closed for row-level extraction",
    ),
    SourcePdf(
        "mirae_2020_order",
        "https://www.cftc.gov/media/3311/enfmiraeassetorder011320/download",
        "enfmiraeassetorder011320.pdf",
        "screened aggregate public order, expected fail-closed for row-level extraction",
    ),
    SourcePdf(
        "panther_2013_order",
        "https://www.cftc.gov/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfpantherorder072213.pdf",
        "enfpantherorder072213.pdf",
        "screened illustrative order, expected fail-closed for exact trade date/time",
    ),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def download(source: SourcePdf) -> dict[str, object]:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    target = RAW_ROOT / source.filename
    req = urllib.request.Request(source.url, headers={"User-Agent": "ict-engine-board-a-audit/1.0"})
    with urllib.request.urlopen(req, timeout=45) as response:
        body = response.read()
        target.write_bytes(body)
        return {
            "case_id": source.case_id,
            "url": source.url,
            "pdf_path": str(target),
            "http_status": getattr(response, "status", None),
            "content_type": response.headers.get("content-type", ""),
            "bytes": len(body),
            "sha256": sha256(target),
            "expected_use": source.expected_use,
        }


def extract_pdf_text(pdf: Path) -> Path:
    text_path = pdf.with_suffix(".txt")
    if text_path.exists() and text_path.stat().st_size > 0:
        return text_path
    snippet = (
        "from pathlib import Path\n"
        "from pypdf import PdfReader\n"
        f"pdf=Path({str(pdf)!r})\n"
        f"out=Path({str(text_path)!r})\n"
        "out.write_text('\\n'.join(page.extract_text() or '' for page in PdfReader(str(pdf)).pages), encoding='utf-8')\n"
    )
    result = subprocess.run(
        ["uv", "run", "--with", "pypdf", "python", "-c", snippet],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    (COMMAND_OUT / f"extract_{pdf.stem}.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (COMMAND_OUT / f"extract_{pdf.stem}.stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"extract failed for {pdf}: {result.stderr}")
    return text_path


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def additional_successes_needed(current_successes: int, threshold: float = MIN_WILSON) -> int:
    for total in range(current_successes, current_successes + 500):
        if wilson_lcb(total, total) >= threshold:
            return total - current_successes
    return 500


def run_direct_verifier() -> dict[str, object]:
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=45,
        check=False,
    )
    stdout_path = COMMAND_OUT / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = COMMAND_OUT / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    payload = {}
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"parse_error": True, "raw_stdout": result.stdout[:500]}
    return {
        "returncode": result.returncode,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "payload": payload,
    }


def screen_texts(downloads: list[dict[str, object]], text_paths: dict[str, Path]) -> list[dict[str, object]]:
    rows = []
    for item in downloads:
        case_id = str(item["case_id"])
        text = text_paths[case_id].read_text(encoding="utf-8", errors="replace")
        lowered = text.lower()
        exact_time_hits = sum(token in lowered for token in ["11:00:36.846", "11:12:38.762", "11:38:31.826", "11:38:32.336", "12:30:49.165", "12:30:49.708"])
        rows.append(
            {
                "case_id": case_id,
                "url": item["url"],
                "pdf_sha256": item["sha256"],
                "text_bytes": text_paths[case_id].stat().st_size,
                "mentions_spoof": "spoof" in lowered,
                "mentions_genuine": "genuine" in lowered,
                "mentions_cancel": "cancel" in lowered,
                "exact_time_hits": exact_time_hits,
                "row_materializable": case_id == "sarao_2015_complaint",
                "accepted_now": False,
                "reason": {
                    "sarao_2015_complaint": "CFTC complaint contains exact dated/timed examples; materialized as proposed sidecar positives only.",
                    "falloon_2025_order": "Order is recent and official but aggregate only: >400 events and >1900 spoof orders without event-level timestamps/quantities.",
                    "mirae_2020_order": "Order describes trader pattern and relevant period but no single dated/timed row examples.",
                    "panther_2013_order": "Order contains one illustrative pattern but no exact trade date/time for the example.",
                }[case_id],
            }
        )
    return rows


def sarao_candidate_rows() -> list[dict[str, str]]:
    source_report = "CFTC Complaint: Navinder Singh Sarao and Nav Sarao Futures Limited PLC, filed Apr. 17 2015"
    participant = "Navinder Singh Sarao / Nav Sarao Futures Limited PLC"
    common = {
        "label": "positive_spoofing_layering",
        "source_report": source_report,
        "symbol": "E-mini S&P 500 futures",
        "venue_or_market_center": "CME Globex",
        "participant_type_code": "CFTC defendant trader; proprietary account",
        "participant_identifier": participant,
        "session_bucket": "regular_us_central_time",
        "candidate_row_status": "proposed_sidecar_not_shared_intake",
    }
    rows = []
    for price in ["1173.25", "1173.50", "1173.75", "1174.00"]:
        rows.append(
            {
                **common,
                "source_section": "Complaint paragraph 58, May 4 2010 layering algorithm example",
                "trade_date": "2010-05-04",
                "side": f"sell-side Layering Algorithm order at price {price}",
                "earliest_order_received_time": "11:00:36.846 America/Chicago",
                "latest_order_received_time": "11:12:38.762 America/Chicago",
                "order_count": "one sell order modified 152 times within four-order layer",
                "total_order_quantity": "600 contracts",
                "activity_description": (
                    "Public CFTC complaint describes four nearly simultaneous 600-lot sell-side layering orders, "
                    "each modified repeatedly and canceled without any portion filled; notional value exceeded $140 million."
                ),
                "matched_negative_group_id": "cftc_sarao_20100504_layering_110036",
                "source_row_id": f"cftc_sarao_20100504_layering_sell_600_{price.replace('.', '_')}",
            }
        )
    rows.append(
        {
            **common,
            "source_section": "Complaint paragraph 69, March 3 2014 2000 Lot Spoofing example",
            "trade_date": "2014-03-03",
            "side": "buy-side 2000 Lot Spoofing order opposite sell order",
            "earliest_order_received_time": "11:38:31.826 America/Chicago",
            "latest_order_received_time": "11:38:32.336 America/Chicago",
            "order_count": "one buy-side 2000 lot spoofing order",
            "total_order_quantity": "2000 contracts",
            "activity_description": (
                "Public CFTC complaint describes a second buy-side 2000 Lot Spoofing order at 1839.25; "
                "within one millisecond defendants filled the remainder of a 169-lot sell order and canceled the spoof order about one half-second later before execution."
            ),
            "matched_negative_group_id": "cftc_sarao_20140303_2000_lot_spoof",
            "source_row_id": "cftc_sarao_20140303_buy_2000_lot_spoof_second",
        }
    )
    rows.append(
        {
            **common,
            "source_section": "Complaint paragraph 70, September 30 2013 2000 Lot Spoofing example",
            "trade_date": "2013-09-30",
            "side": "buy-side 2000 Lot Spoofing order opposite sell-side order",
            "earliest_order_received_time": "12:30:49.165 America/Chicago",
            "latest_order_received_time": "12:30:49.708 America/Chicago",
            "order_count": "one buy-side 2000 lot spoofing order",
            "total_order_quantity": "2000 contracts",
            "activity_description": (
                "Public CFTC complaint describes a third buy-side 2000 Lot Spoofing order at 1678.50; "
                "while active, defendants filled the rest of the sell-side order and canceled this final spoof order in less than one second."
            ),
            "matched_negative_group_id": "cftc_sarao_20130930_2000_lot_spoof",
            "source_row_id": "cftc_sarao_20130930_buy_2000_lot_spoof_third",
        }
    )
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256(BOARD)
    direct_verifier = run_direct_verifier()
    current_positive_count = int(direct_verifier.get("payload", {}).get("positive_rows", 0) or 0)
    sidecar_count = len(read_csv(SIDECAR_CONTROLS)) if SIDECAR_CONTROLS.exists() else 0
    same_event_negative_count = len(read_csv(SAME_EVENT_NEGATIVES)) if SAME_EVENT_NEGATIVES.exists() else 0

    downloads = []
    text_paths = {}
    for source in SOURCES:
        item = download(source)
        downloads.append(item)
        text_paths[source.case_id] = extract_pdf_text(Path(str(item["pdf_path"])))

    source_screen_rows = screen_texts(downloads, text_paths)
    proposed_rows = sarao_candidate_rows()
    proposed_count = len(proposed_rows)
    what_if_positive_count = current_positive_count + proposed_count
    current_positive_lcb = wilson_lcb(current_positive_count, current_positive_count)
    what_if_positive_lcb = wilson_lcb(what_if_positive_count, what_if_positive_count)
    sidecar_lcb = wilson_lcb(sidecar_count, sidecar_count)
    current_min_lcb = min(current_positive_lcb, sidecar_lcb)
    what_if_min_lcb = min(what_if_positive_lcb, sidecar_lcb)

    write_csv(OUT / "r6_positive_row_source_screen_v1_cases.csv", source_screen_rows, list(source_screen_rows[0].keys()))
    write_csv(OUT / "r6_sarao_positive_row_candidates_v1.csv", proposed_rows, ROW_FIELDS)

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash_before,
        "source_screen_count": len(source_screen_rows),
        "row_materializable_sources": [row["case_id"] for row in source_screen_rows if row["row_materializable"]],
        "proposed_positive_rows": proposed_count,
        "proposed_rows_path": str(OUT / "r6_sarao_positive_row_candidates_v1.csv"),
        "source_screen_path": str(OUT / "r6_positive_row_source_screen_v1_cases.csv"),
        "downloads": downloads,
        "direct_verifier": direct_verifier,
        "current_positive_rows": current_positive_count,
        "current_same_event_negative_rows": same_event_negative_count,
        "sidecar_broad_normal_control_rows": sidecar_count,
        "current_positive_wilson95_lcb": round(current_positive_lcb, 12),
        "sidecar_broad_normal_wilson95_lcb": round(sidecar_lcb, 12),
        "current_min_wilson95_lcb": round(current_min_lcb, 12),
        "what_if_positive_rows": what_if_positive_count,
        "what_if_positive_wilson95_lcb": round(what_if_positive_lcb, 12),
        "what_if_min_wilson95_lcb": round(what_if_min_lcb, 12),
        "additional_positive_rows_needed_now": additional_successes_needed(current_positive_count),
        "additional_positive_rows_needed_after_proposed_if_all_accepted": additional_successes_needed(what_if_positive_count),
        "shared_intake_mutated": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "gate_result": "r6_sarao_positive_row_candidate_screen_v1=proposed_rows_only_positive_confidence_still_blocked",
        "next_action": (
            "Review/lock shared intake before any append; if accepted, Sarao adds 6 source-owned proposed positives, "
            "still leaving additional all-correct positives needed for pooled Wilson95 and split support."
        ),
    }

    json_path = OUT / "r6_sarao_positive_row_candidate_screen_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    report = [
        "# R6 Sarao Positive Row Candidate Screen v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Official CFTC sources screened: `{len(source_screen_rows)}`.",
        f"- Materializable source: `{', '.join(result['row_materializable_sources'])}`.",
        f"- Proposed Sarao positive sidecar rows: `{proposed_count}`.",
        f"- Shared intake mutated: `{result['shared_intake_mutated']}`.",
        f"- Current direct positives: `{current_positive_count}`; sidecar broad-normal controls: `{sidecar_count}`.",
        f"- Current min Wilson95 LCB: `{result['current_min_wilson95_lcb']}`.",
        f"- What-if positives after accepting proposed rows: `{what_if_positive_count}`.",
        f"- What-if min Wilson95 LCB: `{result['what_if_min_wilson95_lcb']}`.",
        f"- Additional positive rows needed now: `{result['additional_positive_rows_needed_now']}`.",
        f"- Additional positive rows needed after proposed rows if all accepted: `{result['additional_positive_rows_needed_after_proposed_if_all_accepted']}`.",
        f"- Gate result: `{result['gate_result']}`.",
        f"- Strict full objective achieved: `{result['strict_full_objective_achieved']}`; `update_goal={result['update_goal']}`.",
        "",
        "## Fail-Closed Notes",
        "",
        "- Falloon 2025 and Mirae 2020 remain aggregate official orders, not row-level examples.",
        "- Panther 2013 order contains an illustrative pattern but lacks exact trade date/time for the example.",
        "- The Sarao rows are proposed sidecar positives only; no shared intake mutation occurred in this run.",
    ]
    (OUT / "r6_sarao_positive_row_candidate_screen_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"shared_intake_mutated={result['shared_intake_mutated']}",
        f"proposed_positive_rows={proposed_count}",
        f"what_if_min_wilson95_lcb={result['what_if_min_wilson95_lcb']}",
        f"new_confidence_gate={result['new_confidence_gate']}",
        f"strict_full_objective_achieved={result['strict_full_objective_achieved']}",
        f"update_goal={result['update_goal']}",
    ]
    (CHECKS / "r6_sarao_positive_row_candidate_screen_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "run_id": RUN_ID, "proposed_positive_rows": proposed_count, "what_if_min_wilson95_lcb": result["what_if_min_wilson95_lcb"], "update_goal": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
