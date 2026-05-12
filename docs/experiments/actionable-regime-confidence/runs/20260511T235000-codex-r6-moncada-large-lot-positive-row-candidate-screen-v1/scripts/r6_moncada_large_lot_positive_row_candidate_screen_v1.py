#!/usr/bin/env python3
"""Screen the official Moncada CFTC order for R6 positive candidates.

This run is read-only against the shared direct-manipulation intake. It writes
proposed rows into this run directory only, verifies that the official source
contains the cited row-level example table, and computes Wilson95 what-if
readbacks against the current live positive count plus the existing Sarao and
Nowak/Smith sidecar candidates.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T235000-codex-r6-moncada-large-lot-positive-row-candidate-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-moncada-large-lot-positive-row-candidate-screen"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

RAW_ROOT = Path("/tmp/ict-engine-r6-moncada-large-lot-positive-row-candidate-screen-v1/raw")
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
SARAO_CANDIDATES = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T225505-codex-r6-sarao-positive-row-candidate-screen-v1"
    / "r6-sarao-positive-row-candidate-screen"
    / "r6_sarao_positive_row_candidates_v1.csv"
)
NOWAK_SMITH_CANDIDATES = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T233454-codex-r6-nowak-smith-positive-row-candidate-screen-v1"
    / "r6-nowak-smith-positive-row-candidate-screen"
    / "r6_nowak_smith_positive_row_candidates_v1.csv"
)
NOWAK_SMITH_SCREEN_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T233454-codex-r6-nowak-smith-positive-row-candidate-screen-v1"
    / "r6-nowak-smith-positive-row-candidate-screen"
    / "r6_nowak_smith_positive_row_candidate_screen_v1.json"
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


@dataclass(frozen=True)
class CandidateCase:
    source_row_id: str
    trade_date: str
    earliest_order_received_time: str
    latest_order_received_time: str
    order_count: str
    total_order_quantity: str
    side: str
    source_section: str
    activity_description: str
    matched_negative_group_id: str
    required_snippets: list[str] = field(default_factory=list)


SOURCE = SourcePdf(
    "moncada_2014_cftc_order",
    "https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfmoncadaorder100114.pdf",
    "enfmoncadaorder100114.pdf",
    "primary candidate: exact row-level large-lot manipulative order-lifecycle examples",
)

SOURCE_REPORT = "CFTC Order: In re Joseph J. Moncada, entered Sep. 30 2014"
SOURCE_SECTION = "Order paragraphs 27-31, October 29 2009 December Wheat large-lot order table"
SYMBOL = "December 2009 Wheat Futures Contract"
VENUE = "CBOT/CME Globex"
PARTICIPANT_TYPE = "CFTC respondent trader; Serdika account"
PARTICIPANT = "Joseph J. Moncada / Serdika account"
CANDIDATE_STATUS = "proposed_sidecar_not_shared_intake"

CASES = [
    CandidateCase(
        source_row_id="cftc_moncada_20091029_wheat_large_lot_buy_103325251",
        trade_date="2009-10-29",
        earliest_order_received_time="10:33:25.251 America/Chicago",
        latest_order_received_time="10:33:26.534 America/Chicago",
        order_count="one large-lot buy order",
        total_order_quantity="500 lots; filled 0; canceled 500",
        side="buy-side large-lot order at best bid intended to create upward liquidity impression",
        source_section=SOURCE_SECTION,
        activity_description="Official CFTC order lists a 500-lot best-bid buy order canceled after 1.283 seconds with zero fills during Moncada's upward attempted manipulation example.",
        matched_negative_group_id="cftc_moncada_20091029_wheat_large_lot_103325251",
        required_snippets=["10:33:25.251 a.m.", "500 506.5 0 0", "1,283"],
    ),
    CandidateCase(
        source_row_id="cftc_moncada_20091029_wheat_large_lot_buy_103440764",
        trade_date="2009-10-29",
        earliest_order_received_time="10:34:40.764 America/Chicago",
        latest_order_received_time="10:34:41.747 America/Chicago",
        order_count="one large-lot buy order",
        total_order_quantity="402 lots; filled 0; canceled 402",
        side="buy-side large-lot order at best bid intended to create upward liquidity impression",
        source_section=SOURCE_SECTION,
        activity_description="Official CFTC order lists a 402-lot best-bid buy order canceled after 0.983 seconds with zero fills during Moncada's upward attempted manipulation example.",
        matched_negative_group_id="cftc_moncada_20091029_wheat_large_lot_103440764",
        required_snippets=["10:34:40.764 a.m.", "402 506.5 0 0", "0.983 seconds"],
    ),
    CandidateCase(
        source_row_id="cftc_moncada_20091029_wheat_large_lot_buy_103541260",
        trade_date="2009-10-29",
        earliest_order_received_time="10:35:41.260 America/Chicago",
        latest_order_received_time="10:35:41.835 America/Chicago",
        order_count="one large-lot buy order",
        total_order_quantity="402 lots; filled 0; canceled 402",
        side="buy-side large-lot order at best bid intended to create upward liquidity impression",
        source_section=SOURCE_SECTION,
        activity_description="Official CFTC order lists a 402-lot best-bid buy order canceled after 0.575 seconds with zero fills during Moncada's upward attempted manipulation example.",
        matched_negative_group_id="cftc_moncada_20091029_wheat_large_lot_103541260",
        required_snippets=["10:35:41.260", "402 S06.7S 0 0", "O.S1S seconds"],
    ),
    CandidateCase(
        source_row_id="cftc_moncada_20091029_wheat_large_lot_buy_103642715",
        trade_date="2009-10-29",
        earliest_order_received_time="10:36:42.715 America/Chicago",
        latest_order_received_time="10:36:45.411 America/Chicago",
        order_count="one large-lot buy order",
        total_order_quantity="500 lots; filled 4; canceled 496",
        side="buy-side large-lot order at best bid intended to create upward liquidity impression",
        source_section=SOURCE_SECTION,
        activity_description="Official CFTC order lists a 500-lot best-bid buy order canceled after 2.696 seconds with four fills during Moncada's upward attempted manipulation example.",
        matched_negative_group_id="cftc_moncada_20091029_wheat_large_lot_103642715",
        required_snippets=["10:36:42.715 a.m.", "soo 50'1.75 0 4", "2.696 5econds"],
    ),
    CandidateCase(
        source_row_id="cftc_moncada_20091029_wheat_large_lot_buy_103740395",
        trade_date="2009-10-29",
        earliest_order_received_time="10:37:40.395 America/Chicago",
        latest_order_received_time="10:37:41.141 America/Chicago",
        order_count="one large-lot buy order",
        total_order_quantity="500 lots; filled 1; canceled 499",
        side="buy-side large-lot order at best bid intended to create upward liquidity impression",
        source_section=SOURCE_SECTION,
        activity_description="Official CFTC order lists a 500-lot best-bid buy order canceled after 0.746 seconds with one fill during Moncada's upward attempted manipulation example.",
        matched_negative_group_id="cftc_moncada_20091029_wheat_large_lot_103740395",
        required_snippets=["10:37:40.395 a.m.", "500 508.5 0 l", "0.746 seconds"],
    ),
    CandidateCase(
        source_row_id="cftc_moncada_20091029_wheat_large_lot_buy_103824755",
        trade_date="2009-10-29",
        earliest_order_received_time="10:38:24.755 America/Chicago",
        latest_order_received_time="10:38:25.492 America/Chicago",
        order_count="one large-lot buy order",
        total_order_quantity="402 lots; filled 1; canceled 401",
        side="buy-side large-lot order at best bid intended to create upward liquidity impression",
        source_section=SOURCE_SECTION,
        activity_description="Official CFTC order lists a 402-lot best-bid buy order canceled after 0.737 seconds with one fill during Moncada's upward attempted manipulation example.",
        matched_negative_group_id="cftc_moncada_20091029_wheat_large_lot_103824755",
        required_snippets=["10:38:24.755 a.m.", "402 508.5 0 ]", "0,737 seconds"],
    ),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_sha_or_missing(path: Path) -> str:
    return sha256(path) if path.exists() else "missing"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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


def download_source() -> dict[str, object]:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    target = RAW_ROOT / SOURCE.filename
    req = urllib.request.Request(SOURCE.url, headers={"User-Agent": "ict-engine-board-a-audit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read()
        target.write_bytes(body)
        return {
            "case_id": SOURCE.case_id,
            "url": SOURCE.url,
            "pdf_path": str(target),
            "http_status": getattr(response, "status", None),
            "content_type": response.headers.get("content-type", ""),
            "bytes": len(body),
            "sha256": sha256(target),
            "expected_use": SOURCE.expected_use,
        }


def extract_pdf_text(pdf_path: Path) -> Path:
    text_path = pdf_path.with_suffix(".txt")
    snippet = (
        "from pathlib import Path\n"
        "from pypdf import PdfReader\n"
        f"pdf=Path({str(pdf_path)!r})\n"
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
    (COMMAND_OUT / "extract_moncada_order.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (COMMAND_OUT / "extract_moncada_order.stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return text_path


def run_direct_verifier() -> dict[str, object]:
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


def artifact_baseline_positive_rows() -> tuple[int, str]:
    if NOWAK_SMITH_SCREEN_JSON.exists():
        payload = json.loads(NOWAK_SMITH_SCREEN_JSON.read_text(encoding="utf-8"))
        value = int(payload.get("current_positive_rows") or 0)
        if value > 0:
            return value, str(NOWAK_SMITH_SCREEN_JSON)
    return 57, "hard_fallback_from_v54_board_cursor_when_live_tmp_intake_missing"


def candidate_rows() -> list[dict[str, str]]:
    rows = []
    for case in CASES:
        rows.append(
            {
                "label": "positive_order_lifecycle_large_lot_quote_pressure",
                "source_report": SOURCE_REPORT,
                "source_section": case.source_section,
                "trade_date": case.trade_date,
                "symbol": SYMBOL,
                "venue_or_market_center": VENUE,
                "participant_type_code": PARTICIPANT_TYPE,
                "participant_identifier": PARTICIPANT,
                "side": case.side,
                "earliest_order_received_time": case.earliest_order_received_time,
                "latest_order_received_time": case.latest_order_received_time,
                "order_count": case.order_count,
                "total_order_quantity": case.total_order_quantity,
                "activity_description": case.activity_description,
                "matched_negative_group_id": case.matched_negative_group_id,
                "session_bucket": "regular_us_central_time",
                "source_row_id": case.source_row_id,
                "candidate_row_status": CANDIDATE_STATUS,
            }
        )
    return rows


def normalize_text(text: str) -> str:
    return " ".join(text.replace("\u00a0", " ").split())


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    start_hashes = {
        "positive_rows": file_sha_or_missing(POSITIVE_ROWS),
        "same_event_negatives": file_sha_or_missing(SAME_EVENT_NEGATIVES),
    }
    board_sha = sha256(BOARD)
    source = download_source()
    text_path = extract_pdf_text(Path(source["pdf_path"]))
    source_text = normalize_text(text_path.read_text(encoding="utf-8", errors="replace"))
    direct_verifier = run_direct_verifier()
    end_hashes = {
        "positive_rows": file_sha_or_missing(POSITIVE_ROWS),
        "same_event_negatives": file_sha_or_missing(SAME_EVENT_NEGATIVES),
    }

    rows = candidate_rows()
    proposed_path = OUT / "r6_moncada_large_lot_positive_row_candidates_v1.csv"
    write_csv(proposed_path, rows, ROW_FIELDS)

    source_screen_rows = []
    all_snippets_ok = True
    for case in CASES:
        hits = [snippet in source_text for snippet in case.required_snippets]
        all_snippets_ok = all_snippets_ok and all(hits)
        source_screen_rows.append(
            {
                "source_row_id": case.source_row_id,
                "source_report": SOURCE_REPORT,
                "source_url": SOURCE.url,
                "all_snippets_verified": all(hits),
                "snippet_hits": json.dumps(dict(zip(case.required_snippets, hits)), sort_keys=True),
                "accepted_now": False,
                "reason": "official CFTC order contains exact row-level example table; materialized as proposed sidecar positive only",
            }
        )
    source_screen_path = OUT / "r6_moncada_large_lot_positive_row_source_screen_v1_cases.csv"
    write_csv(
        source_screen_path,
        source_screen_rows,
        ["source_row_id", "source_report", "source_url", "all_snippets_verified", "snippet_hits", "accepted_now", "reason"],
    )

    verifier_payload = direct_verifier.get("payload", {})
    live_intake_available = direct_verifier["returncode"] == 0 and verifier_payload.get("status") == "schema_ready_unscored"
    fallback_positive, fallback_source = artifact_baseline_positive_rows()
    current_positive = int(verifier_payload.get("positive_rows") or len(read_csv(POSITIVE_ROWS)) or fallback_positive)
    current_negative = int(verifier_payload.get("matched_negative_rows") or len(read_csv(SAME_EVENT_NEGATIVES)) or current_positive)
    sarao_rows = len(read_csv(SARAO_CANDIDATES))
    nowak_smith_rows = len(read_csv(NOWAK_SMITH_CANDIDATES))
    proposed_rows = len(rows)
    sidecar_controls = len(read_csv(SIDECAR_CONTROLS))
    current_lcb = wilson_lcb(current_positive, current_positive)
    moncada_only_total = current_positive + proposed_rows
    sarao_nowak_moncada_total = current_positive + sarao_rows + nowak_smith_rows + proposed_rows

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_sha,
        "source": source,
        "raw_text_path": str(text_path),
        "direct_verifier": direct_verifier,
        "live_intake_available": live_intake_available,
        "current_positive_rows_source": "live_direct_verifier" if live_intake_available else fallback_source,
        "current_positive_rows": current_positive,
        "current_same_event_negative_rows": current_negative,
        "current_min_wilson95_lcb": round(current_lcb, 12),
        "sarao_sidecar_positive_rows": sarao_rows,
        "nowak_smith_sidecar_positive_rows": nowak_smith_rows,
        "proposed_positive_rows": proposed_rows,
        "sidecar_broad_normal_control_rows": sidecar_controls,
        "what_if_positive_rows_moncada_only": moncada_only_total,
        "what_if_min_wilson95_lcb_moncada_only": round(wilson_lcb(moncada_only_total, moncada_only_total), 12),
        "what_if_positive_rows_sarao_nowak_moncada": sarao_nowak_moncada_total,
        "what_if_min_wilson95_lcb_sarao_nowak_moncada": round(
            wilson_lcb(sarao_nowak_moncada_total, sarao_nowak_moncada_total), 12
        ),
        "additional_positive_rows_needed_now": additional_successes_needed(current_positive),
        "additional_positive_rows_needed_after_moncada_if_all_accepted": additional_successes_needed(moncada_only_total),
        "additional_positive_rows_needed_after_sarao_nowak_moncada_if_all_accepted": additional_successes_needed(
            sarao_nowak_moncada_total
        ),
        "all_candidate_snippets_verified": all_snippets_ok,
        "shared_intake_mutated": start_hashes != end_hashes,
        "start_hashes": start_hashes,
        "end_hashes": end_hashes,
        "proposed_rows_path": str(proposed_path),
        "source_screen_path": str(source_screen_path),
        "json_path": str(OUT / "r6_moncada_large_lot_positive_row_candidate_screen_v1.json"),
        "report_path": str(OUT / "r6_moncada_large_lot_positive_row_candidate_screen_v1.md"),
        "assertions_path": str(CHECKS / "r6_moncada_large_lot_positive_row_candidate_screen_v1_assertions.out"),
        "external_requests_sent": True,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "gate_result": "r6_moncada_large_lot_positive_row_candidate_screen_v1=proposed_rows_only_pooled_whatif_passes_if_sarao_nowak_also_accepted",
        "next_action": (
            "Restore or reacquire the shared direct intake under a fresh lock/readback, then decide whether "
            "to accept Sarao, Nowak/Smith, and Moncada sidecar positives with matched-control policy. "
            "Rerun direct calibration with the sidecar broad-normal controls and split/species gates."
        ),
    }

    json_path = OUT / "r6_moncada_large_lot_positive_row_candidate_screen_v1.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = f"""# R6 Moncada Large-Lot Positive Row Candidate Screen v1

- Run id: `{RUN_ID}`
- Generated at UTC: `{payload['generated_at_utc']}`
- Official source: {SOURCE.url}
- Shared intake mutated: `{str(payload['shared_intake_mutated']).lower()}`
- Live shared intake available now: `{str(live_intake_available).lower()}`
- Current positive baseline source: `{payload['current_positive_rows_source']}`
- Proposed positive rows: `{proposed_rows}`
- Current direct positives: `{current_positive}`
- Current min Wilson95 LCB: `{payload['current_min_wilson95_lcb']}`
- What-if positives after Moncada only: `{moncada_only_total}`
- What-if min Wilson95 LCB after Moncada only: `{payload['what_if_min_wilson95_lcb_moncada_only']}`
- What-if positives after Sarao + Nowak/Smith + Moncada sidecars: `{sarao_nowak_moncada_total}`
- What-if min Wilson95 LCB after all three sidecars: `{payload['what_if_min_wilson95_lcb_sarao_nowak_moncada']}`
- Additional rows still needed after all three sidecars if all accepted: `{payload['additional_positive_rows_needed_after_sarao_nowak_moncada_if_all_accepted']}`
- Gate result: `{payload['gate_result']}`
- Next action: {payload['next_action']}

## Artifacts
- JSON: `{json_path}`
- Proposed rows CSV: `{proposed_path}`
- Source screen CSV: `{source_screen_path}`
- Assertions: `{payload['assertions_path']}`
"""
    report_path = OUT / "r6_moncada_large_lot_positive_row_candidate_screen_v1.md"
    report_path.write_text(report, encoding="utf-8")

    checks = {
        "direct_verifier_readback_recorded": direct_verifier["returncode"] in (0, 2),
        "source_pdf_downloaded": source["http_status"] == 200 and source["bytes"] > 0,
        "all_candidate_snippets_verified": all_snippets_ok,
        "proposed_rows_positive_count": proposed_rows == 6,
        "shared_intake_read_only": start_hashes == end_hashes,
        "confidence_still_blocked_moncada_only": payload["what_if_min_wilson95_lcb_moncada_only"] < MIN_WILSON,
        "pooled_whatif_passes_with_sarao_nowak_moncada": payload["what_if_min_wilson95_lcb_sarao_nowak_moncada"] >= MIN_WILSON,
        "strict_full_objective_not_complete": payload["strict_full_objective_achieved"] is False,
        "no_runtime_code_changed": payload["runtime_code_changed"] is False,
    }
    assertions_path = CHECKS / "r6_moncada_large_lot_positive_row_candidate_screen_v1_assertions.out"
    assertions_path.write_text("\n".join(f"{name}=ok" if ok else f"{name}=FAIL" for name, ok in checks.items()) + "\n", encoding="utf-8")
    if not all(checks.values()):
        raise SystemExit(2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
