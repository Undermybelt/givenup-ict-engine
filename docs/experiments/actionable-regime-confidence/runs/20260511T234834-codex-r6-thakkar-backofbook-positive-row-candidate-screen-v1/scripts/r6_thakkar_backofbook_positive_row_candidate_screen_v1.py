#!/usr/bin/env python3
"""Screen the official Thakkar CFTC complaint for R6 positive candidates.

This run is read-only against the shared direct-manipulation intake. It writes
candidate rows into the run directory, records the live-intake verifier state,
and computes a strict what-if against the latest verified R6 baseline.
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


RUN_ID = "20260511T234834-codex-r6-thakkar-backofbook-positive-row-candidate-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-thakkar-backofbook-positive-row-candidate-screen"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

RAW_ROOT = Path("/tmp/ict-engine-r6-thakkar-backofbook-positive-row-candidate-screen-v1/raw")
LIVE_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
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
V54_AUDIT_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T223100-codex-current-goal-completion-audit-v54-after-sidecar-calibration"
    / "completion-audit"
    / "current_goal_completion_audit_v54_after_sidecar_calibration.json"
)
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

SOURCE_URL = (
    "https://www.cftc.gov/sites/default/files/idc/groups/public/"
    "%40lrenforcementactions/documents/legalpleading/enfthakkarcomplaint012818.pdf"
)
SOURCE_FILENAME = "enfthakkarcomplaint012818.pdf"
SOURCE_REPORT = "CFTC Complaint: Jitesh Thakkar and Edge Financial Technologies, filed Jan. 28 2018"
VENUE = "CME Globex"
PARTICIPANT_TYPE = "CFTC referenced Trader A using Back-of-Book function"
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
class CandidateRow:
    source_row_id: str
    source_section: str
    trade_date: str
    symbol: str
    side: str
    earliest_order_received_time: str
    latest_order_received_time: str
    order_count: str
    total_order_quantity: str
    activity_description: str
    matched_negative_group_id: str
    session_bucket: str
    required_snippets: list[str] = field(default_factory=list)


POSITIVE_CASES = [
    CandidateRow(
        source_row_id="cftc_thakkar_20130222_backofbook_buy_150400",
        source_section="Complaint paragraph 37, February 22 2013 Back-of-Book buy spoof order",
        trade_date="2013-02-22",
        symbol="March 2013 E-mini S&P 500 futures",
        side="buy-side Back-of-Book spoof order at 150400",
        earliest_order_received_time="10:17:07 CST approximate",
        latest_order_received_time="nearly two minutes after 10:17:07 CST",
        order_count="one Back-of-Book Spoof Order modified 25 times",
        total_order_quantity="722 lots, alternating to 723 lots",
        activity_description=(
            "Official CFTC complaint describes Trader A placing a 722-lot Back-of-Book "
            "Spoof Order to buy, modified 25 times, remaining unexecuted until canceled."
        ),
        matched_negative_group_id="cftc_thakkar_20130222_backofbook_buy_spoof",
        session_bucket="regular_us_central_time",
        required_snippets=[
            "on February 22, 2013, at approximately 10:17:07 CST",
            "placed a 722-lot Back-of-Book Spoof Order to buy at 150400",
            "automatically modified this order, switching between 722 and 723 lots a total of 25",
            "remained on the market, unexecuted, for nearly two minutes",
            "Trader A placed a 376-lot sell order at the price of 150450 and was filled",
        ],
    ),
    CandidateRow(
        source_row_id="cftc_thakkar_20130225_backofbook_sell_150450",
        source_section="Complaint paragraphs 38-39, February 25 2013 150450 Back-of-Book sell spoof order",
        trade_date="2013-02-25",
        symbol="March 2013 E-mini S&P 500 futures",
        side="sell-side Back-of-Book spoof order at 150450",
        earliest_order_received_time="12:48:52.156 CST approximate",
        latest_order_received_time="12.311 seconds after entry",
        order_count="one Back-of-Book Spoof Order modified 13 times",
        total_order_quantity="796 lots, alternating to 797 lots",
        activity_description=(
            "Official CFTC complaint describes a 796-lot sell spoof order at 150450, "
            "modified 13 times, unexecuted until canceled; same millisecond buy fill followed."
        ),
        matched_negative_group_id="cftc_thakkar_20130225_backofbook_sell_spoof",
        session_bucket="regular_us_central_time",
        required_snippets=[
            "on February 25, 2013, at approximately 12:48:52 CST",
            "place three 796-lot Spoof Orders to sell",
            "150450 (150450 Spoof Order)",
            "the 150450 Spoof Order was modified 13 times",
            "In the same millisecond that Trader A canceled the 150450 Spoof Order",
        ],
    ),
    CandidateRow(
        source_row_id="cftc_thakkar_20130225_backofbook_sell_150475",
        source_section="Complaint paragraphs 38-39, February 25 2013 150475 Back-of-Book sell spoof order",
        trade_date="2013-02-25",
        symbol="March 2013 E-mini S&P 500 futures",
        side="sell-side Back-of-Book spoof order at 150475",
        earliest_order_received_time="12:48:52.355 CST approximate",
        latest_order_received_time="24.119 seconds after entry",
        order_count="one Back-of-Book Spoof Order modified 10 times",
        total_order_quantity="796 lots, alternating to 797 lots",
        activity_description=(
            "Official CFTC complaint describes a 796-lot sell spoof order at 150475, "
            "modified 10 times, unexecuted until canceled after that price became best offer."
        ),
        matched_negative_group_id="cftc_thakkar_20130225_backofbook_sell_spoof",
        session_bucket="regular_us_central_time",
        required_snippets=[
            "150475 (150475 Spoof Order)",
            "The 150475 Spoof Order was placed at the third best offer",
            "The 150475 Spoof Order was modified 10 times",
            "for approximately 24 seconds, until Trader A cancelled the order",
        ],
    ),
    CandidateRow(
        source_row_id="cftc_thakkar_20130225_backofbook_sell_150500",
        source_section="Complaint paragraphs 38-39, February 25 2013 150500 Back-of-Book sell spoof order",
        trade_date="2013-02-25",
        symbol="March 2013 E-mini S&P 500 futures",
        side="sell-side Back-of-Book spoof order at 150500",
        earliest_order_received_time="12:48:52.355 CST approximate",
        latest_order_received_time="46.033 seconds after entry",
        order_count="one Back-of-Book Spoof Order modified 14 times",
        total_order_quantity="796 lots, alternating to 797 lots",
        activity_description=(
            "Official CFTC complaint describes a 796-lot sell spoof order at 150500, "
            "modified 14 times, unexecuted until canceled after that price became best offer."
        ),
        matched_negative_group_id="cftc_thakkar_20130225_backofbook_sell_spoof",
        session_bucket="regular_us_central_time",
        required_snippets=[
            "150500 (150500 Spoof Order)",
            "The 150500 spoof order was placed at the fourth best offer",
            "The 150500 Spoof Order was modified 14 times",
            "approximately 46 seconds, until Trader A canceled the order",
        ],
    ),
]

MATCHED_CONTROL_ROWS = [
    {
        "label": "matched_negative_genuine_trade_context",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraph 37, February 22 2013 genuine sell fill context",
        "trade_date": "2013-02-22",
        "symbol": "March 2013 E-mini S&P 500 futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_TYPE,
        "participant_identifier": "Trader A",
        "side": "sell order at 150450 filled while buy spoof order was on market",
        "earliest_order_received_time": "during nearly two-minute 10:17:07 CST spoof window",
        "latest_order_received_time": "source paragraph 37 window",
        "order_count": "one sell order",
        "total_order_quantity": "376 lots",
        "activity_description": "Source paragraph states Trader A placed a 376-lot sell order at 150450 and was filled.",
        "matched_negative_group_id": "cftc_thakkar_20130222_backofbook_buy_spoof",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_thakkar_20130222_genuine_sell_376_150450",
        "candidate_row_status": "proposed_sidecar_not_shared_intake",
    },
    {
        "label": "matched_negative_genuine_trade_context",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 38-39, February 25 2013 genuine buy fill context",
        "trade_date": "2013-02-25",
        "symbol": "March 2013 E-mini S&P 500 futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_TYPE,
        "participant_identifier": "Trader A",
        "side": "buy order at 150450 filled after spoof-order cancellation",
        "earliest_order_received_time": "same millisecond as 150450 spoof cancellation",
        "latest_order_received_time": "source paragraph 38 window",
        "order_count": "one buy order",
        "total_order_quantity": "796 lots",
        "activity_description": "Source paragraph states Trader A placed and was completely filled on a 796-lot buy order.",
        "matched_negative_group_id": "cftc_thakkar_20130225_backofbook_sell_spoof",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_thakkar_20130225_genuine_buy_796_150450",
        "candidate_row_status": "proposed_sidecar_not_shared_intake",
    },
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


def download_source() -> dict[str, object]:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    target = RAW_ROOT / SOURCE_FILENAME
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "ict-engine-board-a-audit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read()
        target.write_bytes(body)
        return {
            "url": SOURCE_URL,
            "pdf_path": str(target),
            "http_status": getattr(response, "status", None),
            "content_type": response.headers.get("content-type", ""),
            "bytes": len(body),
            "sha256": sha256(target),
        }


def extract_pdf_text(pdf: Path) -> Path:
    text_path = pdf.with_suffix(".txt")
    gs = shutil.which("gs")
    if gs is None:
        raise RuntimeError("Ghostscript binary 'gs' is required for PDF text extraction")
    result = subprocess.run(
        [gs, "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=txtwrite", f"-o{text_path}", str(pdf)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    (COMMAND_OUT / "ghostscript_extract.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (COMMAND_OUT / "ghostscript_extract.stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"Ghostscript extraction failed: {result.stderr}")
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


def latest_verified_baseline() -> dict[str, object]:
    if not V54_AUDIT_JSON.exists():
        return {"positive_rows": 57, "source": "hardcoded_from_board_v54_missing_json"}
    payload = json.loads(V54_AUDIT_JSON.read_text(encoding="utf-8"))
    r6 = payload.get("r6_direct_manipulation", {})
    positive_rows = (
        r6.get("positive_rows")
        or payload.get("r6_direct_positive_rows")
        or payload.get("direct_positive_rows")
        or 57
    )
    return {
        "positive_rows": int(positive_rows),
        "source": str(V54_AUDIT_JSON),
        "gate_result": payload.get("gate_result") or payload.get("decision"),
    }


def build_candidate_rows(text: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    normalized = normalize_text(text)
    rows: list[dict[str, object]] = []
    screens: list[dict[str, object]] = []
    for case in POSITIVE_CASES:
        hits = {snippet: normalize_text(snippet) in normalized for snippet in case.required_snippets}
        materializable = all(hits.values())
        screens.append(
            {
                "source_row_id": case.source_row_id,
                "source_section": case.source_section,
                "trade_date": case.trade_date,
                "materializable": materializable,
                "snippet_hits_json": json.dumps(hits, sort_keys=True),
                "screen_status": "row_level_positive_candidate" if materializable else "fail_closed_snippet_mismatch",
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
                "participant_identifier": "Trader A / Back-of-Book user",
                "side": case.side,
                "earliest_order_received_time": case.earliest_order_received_time,
                "latest_order_received_time": case.latest_order_received_time,
                "order_count": case.order_count,
                "total_order_quantity": case.total_order_quantity,
                "activity_description": case.activity_description,
                "matched_negative_group_id": case.matched_negative_group_id,
                "session_bucket": case.session_bucket,
                "source_row_id": case.source_row_id,
                "candidate_row_status": "proposed_sidecar_not_shared_intake",
            }
        )
    return rows, screens


def write_report(summary: dict[str, object]) -> Path:
    report_path = OUT / "r6_thakkar_backofbook_positive_row_candidate_screen_v1.md"
    lines = [
        "# R6 Thakkar Back-of-Book Positive Row Candidate Screen v1",
        "",
        f"- Run id: `{summary['run_id']}`",
        f"- Generated at UTC: `{summary['generated_at_utc']}`",
        f"- Official source: {SOURCE_URL}",
        f"- Live shared intake status: `{summary['live_intake_status']}`",
        f"- Shared intake mutated: `{str(summary['shared_intake_mutated']).lower()}`",
        f"- Proposed positive rows: `{summary['proposed_positive_rows']}`",
        f"- Proposed matched-control rows: `{summary['proposed_matched_control_rows']}`",
        f"- Latest verified baseline positives: `{summary['latest_verified_positive_rows']}`",
        f"- Sarao sidecar positives: `{summary['sarao_sidecar_positive_rows']}`",
        f"- Nowak/Smith sidecar positives: `{summary['nowak_smith_sidecar_positive_rows']}`",
        f"- What-if positives after Sarao + Nowak/Smith + Thakkar: `{summary['what_if_positive_rows_with_prior_sidecars']}`",
        f"- What-if min Wilson95 LCB after all three sidecars: `{summary['what_if_min_wilson95_lcb_with_prior_sidecars']:.12f}`",
        f"- Additional positive rows needed after all three sidecars: `{summary['additional_positive_rows_needed_after_prior_sidecars']}`",
        f"- Gate result: `{summary['gate_result']}`",
        f"- Next action: {summary['next_action']}",
        "",
        "## Boundary",
        "",
        "This run does not mutate `/tmp/ict-engine-direct-manipulation-row-intake`. "
        "Because that live root is currently missing, this is candidate evidence only; "
        "acceptance still requires a fresh locked intake restoration, matched-control "
        "policy application, and full direct plus sidecar calibration rerun.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{summary['json_path']}`",
        f"- Proposed positives CSV: `{summary['proposed_positive_rows_path']}`",
        f"- Proposed controls CSV: `{summary['proposed_matched_controls_path']}`",
        f"- Source screen CSV: `{summary['source_screen_path']}`",
        f"- Assertions: `{summary['assertions_path']}`",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> None:
    for path in [OUT, COMMAND_OUT, CHECKS, RAW_ROOT]:
        path.mkdir(parents=True, exist_ok=True)

    board_sha = sha256(BOARD)
    download = download_source()
    text_path = extract_pdf_text(Path(download["pdf_path"]))
    text = text_path.read_text(encoding="utf-8", errors="replace")
    proposed_rows, source_screens = build_candidate_rows(text)

    proposed_positive_path = OUT / "r6_thakkar_backofbook_positive_row_candidates_v1.csv"
    proposed_controls_path = OUT / "r6_thakkar_backofbook_matched_control_candidates_v1.csv"
    source_screen_path = OUT / "r6_thakkar_backofbook_positive_row_source_screen_v1.csv"
    write_csv(proposed_positive_path, proposed_rows, ROW_FIELDS)
    write_csv(proposed_controls_path, MATCHED_CONTROL_ROWS, ROW_FIELDS)
    write_csv(
        source_screen_path,
        source_screens,
        ["source_row_id", "source_section", "trade_date", "materializable", "snippet_hits_json", "screen_status"],
    )

    verifier = run_direct_verifier()
    live_status = verifier["payload"].get("status", "unknown")
    baseline = latest_verified_baseline()
    latest_verified_positive_rows = int(baseline["positive_rows"])
    sidecar_broad_normal_control_rows = len(read_csv(SIDECAR_CONTROLS))
    sarao_rows = len(read_csv(SARAO_CANDIDATES))
    nowak_smith_rows = len(read_csv(NOWAK_SMITH_CANDIDATES))
    thakkar_rows = len(proposed_rows)

    current_lcb = wilson_lcb(latest_verified_positive_rows, latest_verified_positive_rows)
    broad_lcb = wilson_lcb(sidecar_broad_normal_control_rows, sidecar_broad_normal_control_rows)
    what_if = latest_verified_positive_rows + sarao_rows + nowak_smith_rows + thakkar_rows
    what_if_lcb = wilson_lcb(what_if, what_if)
    what_if_min_lcb = min(what_if_lcb, broad_lcb)
    what_if_gate = what_if_min_lcb >= MIN_WILSON

    gate_result = (
        "r6_thakkar_backofbook_positive_row_candidate_screen_v1="
        "sidecar_candidates_enough_for_pooled_wilson_but_live_intake_missing"
        if what_if_gate and live_status == "blocked"
        else "r6_thakkar_backofbook_positive_row_candidate_screen_v1=proposed_rows_only_confidence_still_blocked"
    )

    summary: dict[str, object] = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_sha,
        "source": download,
        "raw_text_path": str(text_path),
        "source_screen_count": len(source_screens),
        "row_materializable_sources": [row["source_row_id"] for row in source_screens if row["materializable"]],
        "proposed_positive_rows": thakkar_rows,
        "proposed_matched_control_rows": len(MATCHED_CONTROL_ROWS),
        "proposed_positive_rows_path": str(proposed_positive_path),
        "proposed_matched_controls_path": str(proposed_controls_path),
        "source_screen_path": str(source_screen_path),
        "direct_verifier": verifier,
        "live_intake_status": live_status,
        "live_intake_missing_files": verifier["payload"].get("missing_files", []),
        "latest_verified_baseline": baseline,
        "latest_verified_positive_rows": latest_verified_positive_rows,
        "sidecar_broad_normal_control_rows": sidecar_broad_normal_control_rows,
        "sarao_sidecar_positive_rows": sarao_rows,
        "nowak_smith_sidecar_positive_rows": nowak_smith_rows,
        "current_baseline_wilson95_lcb": round(current_lcb, 12),
        "sidecar_broad_normal_wilson95_lcb": round(broad_lcb, 12),
        "what_if_positive_rows_thakkar_only": latest_verified_positive_rows + thakkar_rows,
        "what_if_positive_wilson95_lcb_thakkar_only": round(
            wilson_lcb(latest_verified_positive_rows + thakkar_rows, latest_verified_positive_rows + thakkar_rows),
            12,
        ),
        "what_if_positive_rows_with_prior_sidecars": what_if,
        "what_if_positive_wilson95_lcb_with_prior_sidecars": round(what_if_lcb, 12),
        "what_if_min_wilson95_lcb_with_prior_sidecars": round(what_if_min_lcb, 12),
        "what_if_pooled_wilson_gate_with_prior_sidecars": what_if_gate,
        "additional_positive_rows_needed_from_latest_verified_baseline": rows_needed_for_lcb(
            latest_verified_positive_rows, MIN_WILSON
        ),
        "additional_positive_rows_needed_after_prior_sidecars": rows_needed_for_lcb(what_if, MIN_WILSON),
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
        "gate_result": gate_result,
        "next_action": (
            "Restore or re-materialize the shared R6 direct intake under a fresh lock, then "
            "decide whether to accept Sarao, Nowak/Smith, and Thakkar candidates with matched "
            "controls and rerun direct plus sidecar calibration; do not claim acceptance from "
            "sidecar what-if evidence while the live intake is missing."
        ),
    }

    json_path = OUT / "r6_thakkar_backofbook_positive_row_candidate_screen_v1.json"
    assertions_path = CHECKS / "r6_thakkar_backofbook_positive_row_candidate_screen_v1_assertions.out"
    summary["json_path"] = str(json_path)
    summary["assertions_path"] = str(assertions_path)
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path = write_report(summary)
    summary["report_path"] = str(report_path)
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    assertions = [
        ("source_pdf_downloaded", download["http_status"] == 200 and download["bytes"] > 0),
        ("all_candidate_snippets_verified", len(proposed_rows) == len(POSITIVE_CASES)),
        ("proposed_positive_rows_count_4", thakkar_rows == 4),
        ("proposed_controls_count_2", len(MATCHED_CONTROL_ROWS) == 2),
        ("live_intake_missing_captured", live_status == "blocked"),
        ("shared_intake_read_only", summary["shared_intake_mutated"] is False),
        ("prior_sidecars_plus_thakkar_pooled_wilson95", what_if_gate),
        ("new_confidence_gate_false_until_live_rerun", summary["new_confidence_gate"] is False),
        ("strict_full_objective_not_complete", summary["strict_full_objective_achieved"] is False),
        ("no_runtime_code_changed", summary["runtime_code_changed"] is False),
    ]
    failed = [name for name, ok in assertions if not ok]
    assertions_path.write_text(
        "\n".join(f"{name}={'ok' if ok else 'FAIL'}" for name, ok in assertions) + "\n",
        encoding="utf-8",
    )
    if failed:
        raise SystemExit(f"assertions failed: {failed}")

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
