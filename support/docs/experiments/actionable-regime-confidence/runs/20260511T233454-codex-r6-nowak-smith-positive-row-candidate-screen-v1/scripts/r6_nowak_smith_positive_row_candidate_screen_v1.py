#!/usr/bin/env python3
"""Screen the official Nowak/Smith CFTC complaint for R6 positive candidates.

This run is intentionally read-only against the shared direct-manipulation
intake. It writes proposed rows into this run directory only, verifies that the
source PDF contains the cited row-level examples, and computes Wilson95 what-if
readbacks against the current live positive count and the accepted Nasdaq ITCH
broad-normal sidecar controls.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T233454-codex-r6-nowak-smith-positive-row-candidate-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-nowak-smith-positive-row-candidate-screen"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

RAW_ROOT = Path("/tmp/ict-engine-r6-nowak-smith-positive-row-candidate-screen-v1/raw")
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
    source_section: str
    trade_date: str
    symbol: str
    participant_identifier: str
    side: str
    earliest_order_received_time: str
    latest_order_received_time: str
    order_count: str
    total_order_quantity: str
    activity_description: str
    matched_negative_group_id: str
    session_bucket: str
    required_snippets: list[str] = field(default_factory=list)


SOURCE = SourcePdf(
    "nowak_smith_jpmorgan_2019_complaint",
    "https://www.cftc.gov/media/2506/enfmichaelgreggcomplaint091619/download",
    "enfmichaelgreggcomplaint091619.pdf",
    "primary candidate: exact dated/timed positive direct spoofing rows",
)

SOURCE_REPORT = (
    "CFTC Complaint: Michael Thomas Nowak and Gregg Francis Smith, filed Sep. 16 2019"
)
VENUE = "COMEX/CME Globex"
PARTICIPANT_TYPE = (
    "CFTC defendant trader; major U.S. financial institution precious metals desk"
)
CANDIDATE_STATUS = "proposed_sidecar_not_shared_intake"

CASES = [
    CandidateCase(
        source_row_id="cftc_nowak_smith_20130506_nowak_gold_sell_layered_spoof",
        source_section="Complaint paragraphs 53-56, May 6 2013 Nowak Gold Futures example",
        trade_date="2013-05-06",
        symbol="Gold Futures contract, June 2013 expiry",
        participant_identifier="Michael Thomas Nowak / Bank A precious metals desk",
        side="sell-side Layered Spoof Orders against genuine buy order",
        earliest_order_received_time="09:01:14.497 source-timezone-unspecified",
        latest_order_received_time="09:01:17.981 plus next six seconds source-timezone-unspecified",
        order_count="14 sell offers intended to cancel, including 12 layered spoof orders plus 2 additional offers",
        total_order_quantity="70 lots",
        activity_description=(
            "Official CFTC complaint describes Nowak placing a five-lot genuine bid, "
            "then sell-side layered spoof offers totaling seventy lots, all canceled "
            "without any lots being filled."
        ),
        matched_negative_group_id="cftc_nowak_smith_20130506_nowak_gold_sell_layered",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On May 6, 2013, at 9:01:13.122 a.m., Nowak placed a Genuine Order to buy five lots",
            "Beginning at 9:01:14.497, Nowak began placing a series of offers at decreasing prices",
            "fourteen offers to sell a total of seventy lots, which he intended to cancel",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_nowak_smith_20131007_nowak_gold_buy_layered_spoof",
        source_section="Complaint paragraphs 57-60, October 7 2013 Nowak Gold Futures example",
        trade_date="2013-10-07",
        symbol="Gold Futures contract, December 2013 expiry",
        participant_identifier="Michael Thomas Nowak / Bank A precious metals desk",
        side="buy-side Layered Spoof Orders against genuine sell order",
        earliest_order_received_time="07:34:47.758 source-timezone-unspecified",
        latest_order_received_time="07:34:51.429 plus next several seconds source-timezone-unspecified",
        order_count="14 buy orders intended to cancel",
        total_order_quantity="70 lots",
        activity_description=(
            "Official CFTC complaint describes Nowak placing a five-lot genuine offer, "
            "then fourteen buy-side layered spoof orders totaling seventy lots, all "
            "canceled without any lots being filled."
        ),
        matched_negative_group_id="cftc_nowak_smith_20131007_nowak_gold_buy_layered",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On October 7, 2013, at 7:34:45.805 a.m., Nowak placed a Genuine Order to sell",
            "Beginning at 7:34:47.758, Nowak began placing a series of bids at increasing prices",
            "fourteen orders to buy a total of seventy lots, which he intended to cancel",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_nowak_smith_20140303_nowak_gold_buy_layered_spoof",
        source_section="Complaint paragraphs 61-64, March 3 2014 Nowak Gold Futures example",
        trade_date="2014-03-03",
        symbol="Gold Futures contract, April 2014 expiry",
        participant_identifier="Michael Thomas Nowak / Bank A precious metals desk",
        side="buy-side Layered Spoof Orders against genuine sell order",
        earliest_order_received_time="08:02:19.360 source-timezone-unspecified",
        latest_order_received_time="08:02:22.257 plus next three seconds source-timezone-unspecified",
        order_count="6 buy orders intended to cancel",
        total_order_quantity="30 lots",
        activity_description=(
            "Official CFTC complaint describes Nowak placing a five-lot genuine offer, "
            "then six buy-side layered spoof orders totaling thirty lots, all canceled "
            "without any lots being filled."
        ),
        matched_negative_group_id="cftc_nowak_smith_20140303_nowak_gold_buy_layered",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On March 3, 2014, at 8:02:17.997 a.m., Nowak placed a Genuine Order to sell",
            "Beginning at 8:02:19.360, Nowak began placing a series of bids at increasing prices",
            "six orders to buy a total of thirty lots, which he intended to cancel",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_nowak_smith_20130125_smith_silver_buy_layered_spoof",
        source_section="Complaint paragraphs 72-75, January 25 2013 Smith Silver Futures example",
        trade_date="2013-01-25",
        symbol="Silver Futures contract, March 2013 expiry",
        participant_identifier="Gregg Francis Smith / Bank A precious metals desk",
        side="buy-side Layered Spoof Orders against genuine sell order",
        earliest_order_received_time="07:55:29.473 source-timezone-unspecified",
        latest_order_received_time="07:55:30.676 plus next 600 milliseconds source-timezone-unspecified",
        order_count="6 buy bids intended to cancel",
        total_order_quantity="60 lots",
        activity_description=(
            "Official CFTC complaint describes Smith placing a two-lot genuine offer, "
            "then buy-side layered spoof bids totaling sixty lots, all canceled without "
            "any lots being filled."
        ),
        matched_negative_group_id="cftc_nowak_smith_20130125_smith_silver_buy_layered",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On January 25, 2013, at 7:55:28.841 a.m., Smith placed a Genuine Order to sell",
            "Beginning at 7:55:29.473, Smith began placing a series of bids at increasing prices",
            "six bids to buy a total of sixty lots, which he intended to cancel",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_nowak_smith_20130523_smith_gold_sell_layered_spoof",
        source_section="Complaint paragraphs 76-79, May 23 2013 Smith Gold Futures example",
        trade_date="2013-05-23",
        symbol="Gold Futures contract, June 2013 expiry",
        participant_identifier="Gregg Francis Smith / Bank A precious metals desk",
        side="sell-side Layered Spoof Orders against genuine buy order",
        earliest_order_received_time="14:00:29.414 source-timezone-unspecified",
        latest_order_received_time="14:00:30.792 plus next 1.2 seconds source-timezone-unspecified",
        order_count="6 sell offers intended to cancel",
        total_order_quantity="60 lots",
        activity_description=(
            "Official CFTC complaint describes Smith placing a two-lot genuine bid, "
            "then six sell-side layered spoof offers totaling sixty lots, all canceled "
            "without any lots being filled."
        ),
        matched_negative_group_id="cftc_nowak_smith_20130523_smith_gold_sell_layered",
        session_bucket="regular_us_afternoon_source_time",
        required_snippets=[
            "On May 23, 2013, at 2:00:22.820 p.m., Smith placed a Genuine Order to buy",
            "Beginning at 2:00:29.414, Smith began placing a series of offers at decreasing prices",
            "six offers to sell a total of sixty lots, which he intended to cancel",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_nowak_smith_20150611_smith_gold_buy_layered_spoof",
        source_section="Complaint paragraphs 80-83, June 11 2015 Smith Gold Futures example",
        trade_date="2015-06-11",
        symbol="Gold Futures contract, August 2015 expiry",
        participant_identifier="Gregg Francis Smith / Bank A precious metals desk",
        side="buy-side Layered Spoof Orders against genuine sell order",
        earliest_order_received_time="07:31:26.144 source-timezone-unspecified",
        latest_order_received_time="07:31:27.441 source-timezone-unspecified",
        order_count="5 buy orders intended to cancel",
        total_order_quantity="50 lots",
        activity_description=(
            "Official CFTC complaint describes Smith placing a ten-lot genuine offer, "
            "then five buy-side layered spoof orders totaling fifty lots, all canceled "
            "without any lots being filled."
        ),
        matched_negative_group_id="cftc_nowak_smith_20150611_smith_gold_buy_layered",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On June 11, 2015, at 7:31:25.410 a.m., Smith placed a Genuine Order to sell",
            "Beginning at 7:31:26.144, Smith began placing a series of bids at increasing prices",
            "five orders to buy a total of fifty lots, which he intended to cancel",
        ],
    ),
]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def download_source(source: SourcePdf) -> dict[str, object]:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    target = RAW_ROOT / source.filename
    req = urllib.request.Request(
        source.url,
        headers={"User-Agent": "ict-engine-board-a-audit/1.0"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
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
    gs = shutil.which("gs")
    if gs is None:
        raise RuntimeError("Ghostscript binary 'gs' is required for PDF text extraction")
    result = subprocess.run(
        [
            gs,
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=txtwrite",
            f"-o{text_path}",
            str(pdf),
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    (COMMAND_OUT / "ghostscript_extract.stdout.txt").write_text(
        result.stdout, encoding="utf-8"
    )
    (COMMAND_OUT / "ghostscript_extract.stderr.txt").write_text(
        result.stderr, encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError(f"Ghostscript extraction failed: {result.stderr}")
    return text_path


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    center = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def rows_needed_for_lcb(current_successes: int, threshold: float) -> int:
    needed = 0
    while wilson_lcb(current_successes + needed, current_successes + needed) < threshold:
        needed += 1
    return needed


def run_direct_verifier() -> dict[str, object]:
    result = subprocess.run(
        [
            "python3",
            str(DIRECT_VERIFIER),
            "--intake-root",
            str(LIVE_INTAKE),
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    stdout_path = COMMAND_OUT / "direct_manipulation_row_intake_verifier.stdout.txt"
    stderr_path = COMMAND_OUT / "direct_manipulation_row_intake_verifier.stderr.txt"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    payload = json.loads(result.stdout) if result.stdout.strip() else {}
    return {
        "returncode": result.returncode,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "payload": payload,
    }


def build_candidate_rows(verified_text: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    screens: list[dict[str, object]] = []
    normalized = normalize_text(verified_text)
    for case in CASES:
        snippet_hits = {
            snippet: normalize_text(snippet) in normalized for snippet in case.required_snippets
        }
        materializable = all(snippet_hits.values())
        screens.append(
            {
                "source_row_id": case.source_row_id,
                "source_section": case.source_section,
                "trade_date": case.trade_date,
                "symbol": case.symbol,
                "participant_identifier": case.participant_identifier,
                "materializable": materializable,
                "snippet_hits_json": json.dumps(snippet_hits, sort_keys=True),
                "screen_status": (
                    "row_level_positive_candidate"
                    if materializable
                    else "fail_closed_snippet_mismatch"
                ),
            }
        )
        if not materializable:
            continue
        rows.append(
            {
                "label": "positive_spoofing_layering",
                "source_report": SOURCE_REPORT,
                "source_section": case.source_section,
                "trade_date": case.trade_date,
                "symbol": case.symbol,
                "venue_or_market_center": VENUE,
                "participant_type_code": PARTICIPANT_TYPE,
                "participant_identifier": case.participant_identifier,
                "side": case.side,
                "earliest_order_received_time": case.earliest_order_received_time,
                "latest_order_received_time": case.latest_order_received_time,
                "order_count": case.order_count,
                "total_order_quantity": case.total_order_quantity,
                "activity_description": case.activity_description,
                "matched_negative_group_id": case.matched_negative_group_id,
                "session_bucket": case.session_bucket,
                "source_row_id": case.source_row_id,
                "candidate_row_status": CANDIDATE_STATUS,
            }
        )
    return rows, screens


def write_report(summary: dict[str, object]) -> Path:
    path = OUT / "r6_nowak_smith_positive_row_candidate_screen_v1.md"
    lines = [
        "# R6 Nowak/Smith Positive Row Candidate Screen v1",
        "",
        f"- Run id: `{summary['run_id']}`",
        f"- Generated at UTC: `{summary['generated_at_utc']}`",
        f"- Official source: {SOURCE.url}",
        f"- Shared intake mutated: `{str(summary['shared_intake_mutated']).lower()}`",
        f"- Proposed positive rows: `{summary['proposed_positive_rows']}`",
        f"- Current direct positives: `{summary['current_positive_rows']}`",
        f"- Current min Wilson95 LCB: `{summary['current_min_wilson95_lcb']:.12f}`",
        f"- What-if positives after Nowak/Smith only: `{summary['what_if_positive_rows_nowak_smith_only']}`",
        f"- What-if min Wilson95 LCB after Nowak/Smith only: `{summary['what_if_min_wilson95_lcb_nowak_smith_only']:.12f}`",
        f"- What-if positives after Sarao + Nowak/Smith sidecars: `{summary['what_if_positive_rows_with_sarao_sidecar']}`",
        f"- What-if min Wilson95 LCB after both sidecars: `{summary['what_if_min_wilson95_lcb_with_sarao_sidecar']:.12f}`",
        f"- Additional rows still needed after both sidecars if all accepted: `{summary['additional_positive_rows_needed_after_sarao_and_nowak_smith_if_all_accepted']}`",
        f"- Gate result: `{summary['gate_result']}`",
        f"- Next action: {summary['next_action']}",
        "",
        "## Artifacts",
        f"- JSON: `{summary['json_path']}`",
        f"- Proposed rows CSV: `{summary['proposed_rows_path']}`",
        f"- Source screen CSV: `{summary['source_screen_path']}`",
        f"- Assertions: `{summary['assertions_path']}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    for path in [OUT, COMMAND_OUT, CHECKS, RAW_ROOT]:
        path.mkdir(parents=True, exist_ok=True)

    board_sha = sha256(BOARD)
    download = download_source(SOURCE)
    text_path = extract_pdf_text(Path(download["pdf_path"]))
    text = text_path.read_text(encoding="utf-8", errors="replace")

    proposed_rows, source_screens = build_candidate_rows(text)
    proposed_rows_path = OUT / "r6_nowak_smith_positive_row_candidates_v1.csv"
    source_screen_path = OUT / "r6_nowak_smith_positive_row_source_screen_v1_cases.csv"
    write_csv(proposed_rows_path, proposed_rows, ROW_FIELDS)
    write_csv(
        source_screen_path,
        source_screens,
        [
            "source_row_id",
            "source_section",
            "trade_date",
            "symbol",
            "participant_identifier",
            "materializable",
            "snippet_hits_json",
            "screen_status",
        ],
    )

    verifier = run_direct_verifier()
    if verifier["returncode"] != 0:
        raise RuntimeError("direct verifier failed")
    verifier_payload = verifier["payload"]
    current_positive_rows = int(verifier_payload.get("positive_rows", len(read_csv(POSITIVE_ROWS))))
    current_same_event_negative_rows = int(
        verifier_payload.get("matched_negative_rows", len(read_csv(SAME_EVENT_NEGATIVES)))
    )
    sidecar_broad_normal_control_rows = len(read_csv(SIDECAR_CONTROLS))
    sarao_sidecar_rows = len(read_csv(SARAO_CANDIDATES))

    current_positive_lcb = wilson_lcb(current_positive_rows, current_positive_rows)
    sidecar_broad_normal_lcb = wilson_lcb(
        sidecar_broad_normal_control_rows, sidecar_broad_normal_control_rows
    )
    nowak_count = len(proposed_rows)
    what_if_nowak = current_positive_rows + nowak_count
    what_if_both = current_positive_rows + sarao_sidecar_rows + nowak_count
    what_if_nowak_lcb = wilson_lcb(what_if_nowak, what_if_nowak)
    what_if_both_lcb = wilson_lcb(what_if_both, what_if_both)
    what_if_nowak_min_lcb = min(what_if_nowak_lcb, sidecar_broad_normal_lcb)
    what_if_both_min_lcb = min(what_if_both_lcb, sidecar_broad_normal_lcb)

    summary: dict[str, object] = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_sha,
        "source": download,
        "raw_text_path": str(text_path),
        "source_screen_count": len(source_screens),
        "row_materializable_sources": [
            row["source_row_id"] for row in source_screens if row["materializable"]
        ],
        "proposed_positive_rows": nowak_count,
        "proposed_rows_path": str(proposed_rows_path),
        "source_screen_path": str(source_screen_path),
        "direct_verifier": verifier,
        "current_positive_rows": current_positive_rows,
        "current_same_event_negative_rows": current_same_event_negative_rows,
        "sidecar_broad_normal_control_rows": sidecar_broad_normal_control_rows,
        "sarao_sidecar_positive_rows": sarao_sidecar_rows,
        "current_positive_wilson95_lcb": round(current_positive_lcb, 12),
        "sidecar_broad_normal_wilson95_lcb": round(sidecar_broad_normal_lcb, 12),
        "current_min_wilson95_lcb": round(
            min(current_positive_lcb, sidecar_broad_normal_lcb), 12
        ),
        "what_if_positive_rows_nowak_smith_only": what_if_nowak,
        "what_if_positive_wilson95_lcb_nowak_smith_only": round(what_if_nowak_lcb, 12),
        "what_if_min_wilson95_lcb_nowak_smith_only": round(what_if_nowak_min_lcb, 12),
        "what_if_positive_rows_with_sarao_sidecar": what_if_both,
        "what_if_positive_wilson95_lcb_with_sarao_sidecar": round(what_if_both_lcb, 12),
        "what_if_min_wilson95_lcb_with_sarao_sidecar": round(what_if_both_min_lcb, 12),
        "additional_positive_rows_needed_now": rows_needed_for_lcb(
            current_positive_rows, MIN_WILSON
        ),
        "additional_positive_rows_needed_after_nowak_smith_if_all_accepted": rows_needed_for_lcb(
            what_if_nowak, MIN_WILSON
        ),
        "additional_positive_rows_needed_after_sarao_and_nowak_smith_if_all_accepted": rows_needed_for_lcb(
            what_if_both, MIN_WILSON
        ),
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
        "gate_result": (
            "r6_nowak_smith_positive_row_candidate_screen_v1="
            "proposed_rows_only_positive_confidence_still_blocked"
        ),
        "next_action": (
            "Under a fresh shared-intake lock/readback, decide whether to accept "
            "the Sarao and Nowak/Smith proposed sidecar positives with matched-control "
            "policy, then keep sourcing additional positive direct rows for pooled "
            "Wilson95 and chronological/symbol/venue split support."
        ),
    }

    json_path = OUT / "r6_nowak_smith_positive_row_candidate_screen_v1.json"
    assertions_path = (
        CHECKS / "r6_nowak_smith_positive_row_candidate_screen_v1_assertions.out"
    )
    summary["json_path"] = str(json_path)
    summary["assertions_path"] = str(assertions_path)
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path = write_report(summary)
    summary["report_path"] = str(report_path)
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    assertions = [
        ("direct_verifier_ok", verifier["returncode"] == 0),
        ("source_pdf_downloaded", download["http_status"] == 200 and download["bytes"] > 0),
        ("all_candidate_snippets_verified", len(proposed_rows) == len(CASES)),
        ("proposed_rows_positive_count", len(proposed_rows) == 6),
        ("shared_intake_read_only", summary["shared_intake_mutated"] is False),
        ("confidence_still_blocked_nowak_only", what_if_nowak_min_lcb < MIN_WILSON),
        ("confidence_still_blocked_with_sarao", what_if_both_min_lcb < MIN_WILSON),
        ("strict_full_objective_not_complete", summary["strict_full_objective_achieved"] is False),
        ("no_runtime_code_changed", summary["runtime_code_changed"] is False),
    ]
    failed = [name for name, ok in assertions if not ok]
    assertions_path.write_text(
        "\n".join(f"{name}={'ok' if ok else 'FAIL'}" for name, ok in assertions)
        + "\n",
        encoding="utf-8",
    )
    if failed:
        raise SystemExit(f"assertions failed: {failed}")

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
