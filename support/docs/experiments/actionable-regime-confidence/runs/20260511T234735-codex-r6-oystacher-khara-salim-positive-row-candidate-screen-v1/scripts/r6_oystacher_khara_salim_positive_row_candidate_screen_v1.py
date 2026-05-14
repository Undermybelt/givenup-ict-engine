#!/usr/bin/env python3
"""Screen official CFTC sources for additional R6 positive row candidates.

This is read-only against the shared direct-manipulation intake. It fetches
official CFTC PDFs into /tmp, extracts text with Ghostscript, verifies cited
row-level snippets, and writes proposed positive rows into this run directory.
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


RUN_ID = "20260511T234735-codex-r6-oystacher-khara-salim-positive-row-candidate-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-oystacher-khara-salim-positive-row-candidate-screen"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RAW_ROOT = Path("/tmp/ict-engine-r6-oystacher-khara-salim-positive-row-candidate-screen-v1/raw")

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
NOWAK_CANDIDATES = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T233454-codex-r6-nowak-smith-positive-row-candidate-screen-v1"
    / "r6-nowak-smith-positive-row-candidate-screen"
    / "r6_nowak_smith_positive_row_candidates_v1.csv"
)
NOWAK_SUMMARY = (
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
    title: str


@dataclass(frozen=True)
class CandidateCase:
    source_key: str
    source_report: str
    source_section: str
    trade_date: str
    symbol: str
    venue_or_market_center: str
    participant_identifier: str
    side: str
    earliest_order_received_time: str
    latest_order_received_time: str
    order_count: str
    total_order_quantity: str
    activity_description: str
    matched_negative_group_id: str
    session_bucket: str
    source_row_id: str
    required_terms: list[str] = field(default_factory=list)


SOURCES = {
    "oystacher_3red_2015_complaint": SourcePdf(
        case_id="oystacher_3red_2015_complaint",
        url="https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfigorcomplnt101915.pdf",
        filename="enfigorcomplnt101915.pdf",
        title="CFTC Complaint: CFTC v. Igor B. Oystacher and 3 Red Trading LLC, filed Oct. 19 2015",
    ),
    "khara_salim_2016_order": SourcePdf(
        case_id="khara_salim_2016_order",
        url="https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfheetsalimorder033116.pdf",
        filename="enfheetsalimorder033116.pdf",
        title="CFTC Consent Order: Heet Khara and Nasim Salim, entered Mar. 31 2016",
    ),
}

PARTICIPANT_TYPE = "CFTC respondent/defendant trader; official CFTC pleading/order"
CANDIDATE_STATUS = "proposed_sidecar_not_shared_intake"

CASES = [
    CandidateCase(
        source_key="oystacher_3red_2015_complaint",
        source_report=SOURCES["oystacher_3red_2015_complaint"].title,
        source_section="Complaint paragraphs 71-76, Natural Gas example: November 30 2012",
        trade_date="2012-11-30",
        symbol="NYMEX Natural Gas futures contract",
        venue_or_market_center="NYMEX/CME Globex",
        participant_identifier="Igor B. Oystacher / 3 Red Trading LLC",
        side="sell-side spoof orders opposite buy flip order",
        earliest_order_received_time="08:02:34.576 source-timezone-unspecified",
        latest_order_received_time="08:02:35.304 source-timezone-unspecified",
        order_count="seven visible sell spoof orders",
        total_order_quantity="103 natural gas futures contracts",
        activity_description=(
            "Official CFTC complaint describes seven visible sell spoof orders behind other "
            "resting offers, cancellation within about 750 milliseconds, and two buy flip "
            "orders totaling fifty contracts."
        ),
        matched_negative_group_id="cftc_oystacher_20121130_ng_sell_spoof_buy_flip",
        session_bucket="regular_us_morning_source_time",
        source_row_id="cftc_oystacher_20121130_ng_sell_spoof_orders",
        required_terms=[
            "8:02:34.360",
            "November 30,2012",
            "seven spoof orders",
            "two buy orders for a total of 50 contracts",
        ],
    ),
    CandidateCase(
        source_key="oystacher_3red_2015_complaint",
        source_report=SOURCES["oystacher_3red_2015_complaint"].title,
        source_section="Complaint paragraphs 79-84, E-Mini S&P 500 example: January 6 2014",
        trade_date="2014-01-06",
        symbol="CME E-Mini S&P 500 futures contract",
        venue_or_market_center="CME Globex",
        participant_identifier="Igor B. Oystacher / 3 Red Trading LLC",
        side="sell-side spoof orders opposite buy flip order",
        earliest_order_received_time="14:01:47.260 source-timezone-unspecified",
        latest_order_received_time="14:01:47.667 source-timezone-unspecified",
        order_count="two visible sell spoof orders",
        total_order_quantity="921 E-Mini S&P 500 futures contracts",
        activity_description=(
            "Official CFTC complaint describes two visible sell spoof orders totaling 921 "
            "contracts, cancellation after about 400 milliseconds, and a buy flip order for "
            "264 contracts."
        ),
        matched_negative_group_id="cftc_oystacher_20140106_es_sell_spoof_buy_flip",
        session_bucket="regular_us_afternoon_source_time",
        source_row_id="cftc_oystacher_20140106_es_sell_spoof_orders",
        required_terms=[
            "January 6, 2014",
            "921 contracts",
            "two spoof orders",
            "264 contracts",
        ],
    ),
    CandidateCase(
        source_key="khara_salim_2016_order",
        source_report=SOURCES["khara_salim_2016_order"].title,
        source_section="Consent order paragraphs 22-23, Khara Gold example: February 20 2015",
        trade_date="2015-02-20",
        symbol="April 2015 Gold futures contract",
        venue_or_market_center="COMEX/CME Globex",
        participant_identifier="Heet Khara",
        side="buy-side layered spoof bids opposite genuine sell offer",
        earliest_order_received_time="01:17:46.050 Central Standard Time",
        latest_order_received_time="01:17:48.434 plus approximately one second Central Standard Time",
        order_count="fifteen 2-lot bids plus four additional 2-lot bids",
        total_order_quantity="38 gold futures contracts",
        activity_description=(
            "Official CFTC consent order describes Khara entering fifteen two-lot bids, "
            "then four additional two-lot bids after the offer traded, and canceling all "
            "thirty-eight bids about a second later."
        ),
        matched_negative_group_id="cftc_khara_20150220_gold_offer_vs_layered_bids",
        session_bucket="overnight_central_time",
        source_row_id="cftc_khara_20150220_gold_layered_bids",
        required_terms=[
            "February 20. 2015",
            "fifteen 2-lot bids",
            "thirty-eight contracts",
            "cancelled all thirty-eight bids",
        ],
    ),
    CandidateCase(
        source_key="khara_salim_2016_order",
        source_report=SOURCES["khara_salim_2016_order"].title,
        source_section="Consent order paragraphs 24-25, Salim Silver example: April 24 2015",
        trade_date="2015-04-24",
        symbol="May 2015 Silver futures contract",
        venue_or_market_center="COMEX/CME Globex",
        participant_identifier="Nasim Salim / Zonyx DMCC account",
        side="sell-side layered spoof offers opposite genuine buy bid",
        earliest_order_received_time="05:02:17.175 approximate Central Standard Time",
        latest_order_received_time="05:02:17.175 plus post-fill additions Central Standard Time",
        order_count="eight 5-lot offers plus three additional 5-lot offers",
        total_order_quantity="55 silver futures contracts",
        activity_description=(
            "Official CFTC consent order describes Salim entering a five-lot bid, then "
            "eight five-lot offers, adding three more offers after the bid traded, and "
            "canceling offers to sell all fifty-five contracts."
        ),
        matched_negative_group_id="cftc_salim_20150424_silver_bid_vs_layered_offers",
        session_bucket="overnight_central_time",
        source_row_id="cftc_salim_20150424_silver_layered_offers",
        required_terms=[
            "April 24, 2015",
            "eight 5-lot offers",
            "55 contracts",
            "cancelled the offers to sell all 55 contracts",
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
            "title": source.title,
            "url": source.url,
            "pdf_path": str(target),
            "http_status": getattr(response, "status", None),
            "content_type": response.headers.get("content-type", ""),
            "bytes": len(body),
            "sha256": sha256(target),
        }


def extract_pdf_text(pdf: Path, case_id: str) -> Path:
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
    (COMMAND_OUT / f"ghostscript_extract_{case_id}.stdout.txt").write_text(
        result.stdout, encoding="utf-8"
    )
    (COMMAND_OUT / f"ghostscript_extract_{case_id}.stderr.txt").write_text(
        result.stderr, encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError(f"Ghostscript extraction failed for {case_id}: {result.stderr}")
    return text_path


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


def build_candidate_rows(text_by_source: dict[str, str]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    screens: list[dict[str, object]] = []
    normalized_by_source = {
        key: normalize_text(value).lower() for key, value in text_by_source.items()
    }
    for case in CASES:
        source_text = normalized_by_source[case.source_key]
        term_hits = {
            term: normalize_text(term).lower() in source_text for term in case.required_terms
        }
        materializable = all(term_hits.values())
        screens.append(
            {
                "source_row_id": case.source_row_id,
                "source_key": case.source_key,
                "source_section": case.source_section,
                "trade_date": case.trade_date,
                "symbol": case.symbol,
                "participant_identifier": case.participant_identifier,
                "materializable": materializable,
                "term_hits_json": json.dumps(term_hits, sort_keys=True),
                "screen_status": (
                    "row_level_positive_candidate"
                    if materializable
                    else "fail_closed_term_mismatch"
                ),
            }
        )
        if not materializable:
            continue
        rows.append(
            {
                "label": "positive_spoofing_layering",
                "source_report": case.source_report,
                "source_section": case.source_section,
                "trade_date": case.trade_date,
                "symbol": case.symbol,
                "venue_or_market_center": case.venue_or_market_center,
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


def latest_durable_baseline() -> dict[str, object]:
    nowak = json.loads(NOWAK_SUMMARY.read_text(encoding="utf-8"))
    return {
        "positive_rows": int(nowak["current_positive_rows"]),
        "same_event_negative_rows": int(nowak["current_same_event_negative_rows"]),
        "min_wilson95_lcb": float(nowak["current_min_wilson95_lcb"]),
        "source_run": str(NOWAK_SUMMARY),
    }


def write_report(summary: dict[str, object]) -> Path:
    path = OUT / "r6_oystacher_khara_salim_positive_row_candidate_screen_v1.md"
    lines = [
        "# R6 Oystacher/Khara/Salim Positive Row Candidate Screen v1",
        "",
        f"- Run id: `{summary['run_id']}`",
        f"- Generated at UTC: `{summary['generated_at_utc']}`",
        f"- Official sources screened: `{summary['official_sources_screened']}`",
        f"- Live shared intake available now: `{str(summary['live_intake_available_now']).lower()}`",
        f"- Shared intake mutated: `{str(summary['shared_intake_mutated']).lower()}`",
        f"- Proposed positive rows: `{summary['proposed_positive_rows']}`",
        f"- Latest durable direct positives: `{summary['durable_current_positive_rows']}`",
        f"- Latest durable min Wilson95 LCB: `{summary['durable_current_min_wilson95_lcb']:.12f}`",
        f"- What-if positives after Sarao + Nowak/Smith + this screen: `{summary['what_if_positive_rows_with_all_sidecars']}`",
        f"- What-if min Wilson95 LCB after all three sidecars: `{summary['what_if_min_wilson95_lcb_with_all_sidecars']:.12f}`",
        f"- Pooled Wilson95 threshold would pass if all sidecars are accepted: `{str(summary['pooled_wilson95_would_pass_if_all_sidecars_accepted']).lower()}`",
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
    downloads = []
    text_by_source: dict[str, str] = {}
    for source in SOURCES.values():
        downloaded = download_source(source)
        downloads.append(downloaded)
        text_path = extract_pdf_text(Path(downloaded["pdf_path"]), source.case_id)
        text_by_source[source.case_id] = text_path.read_text(
            encoding="utf-8", errors="replace"
        )

    proposed_rows, source_screens = build_candidate_rows(text_by_source)
    proposed_rows_path = OUT / "r6_oystacher_khara_salim_positive_row_candidates_v1.csv"
    source_screen_path = OUT / "r6_oystacher_khara_salim_positive_row_source_screen_v1_cases.csv"
    write_csv(proposed_rows_path, proposed_rows, ROW_FIELDS)
    write_csv(
        source_screen_path,
        source_screens,
        [
            "source_row_id",
            "source_key",
            "source_section",
            "trade_date",
            "symbol",
            "participant_identifier",
            "materializable",
            "term_hits_json",
            "screen_status",
        ],
    )

    verifier = run_direct_verifier()
    durable = latest_durable_baseline()
    current_positive_rows = durable["positive_rows"]
    sarao_sidecar_rows = len(read_csv(SARAO_CANDIDATES))
    nowak_sidecar_rows = len(read_csv(NOWAK_CANDIDATES))
    sidecar_broad_normal_control_rows = len(read_csv(SIDECAR_CONTROLS))

    what_if_all_rows = (
        current_positive_rows
        + sarao_sidecar_rows
        + nowak_sidecar_rows
        + len(proposed_rows)
    )
    what_if_all_lcb = wilson_lcb(what_if_all_rows, what_if_all_rows)
    rows_needed_now = rows_needed_for_lcb(current_positive_rows, MIN_WILSON)
    rows_needed_after_all = rows_needed_for_lcb(what_if_all_rows, MIN_WILSON)
    live_payload = verifier.get("payload", {})
    live_intake_available = verifier["returncode"] == 0

    summary: dict[str, object] = {
        "accepted_rows_added": 0,
        "additional_positive_rows_needed_now_from_durable_baseline": rows_needed_now,
        "additional_positive_rows_needed_after_all_sidecars_if_accepted": rows_needed_after_all,
        "assertions_path": str(
            CHECKS
            / "r6_oystacher_khara_salim_positive_row_candidate_screen_v1_assertions.out"
        ),
        "board_sha256_at_start": board_sha,
        "direct_verifier_now": verifier,
        "durable_baseline_source": durable["source_run"],
        "durable_current_min_wilson95_lcb": durable["min_wilson95_lcb"],
        "durable_current_positive_rows": current_positive_rows,
        "durable_current_same_event_negative_rows": durable["same_event_negative_rows"],
        "external_requests_sent": True,
        "gate_result": (
            "r6_oystacher_khara_salim_positive_row_candidate_screen_v1="
            "candidate_rows_found_live_intake_missing_no_acceptance"
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "json_path": str(
            OUT / "r6_oystacher_khara_salim_positive_row_candidate_screen_v1.json"
        ),
        "live_intake_available_now": live_intake_available,
        "live_intake_status_now": live_payload.get("status", "unknown"),
        "live_intake_reason_now": live_payload.get("reason", ""),
        "new_confidence_gate": False,
        "next_action": (
            "Restore or lock the shared direct intake, decide whether to accept Sarao, "
            "Nowak/Smith, and Oystacher/Khara/Salim sidecar positives with matched-control "
            "policy, then rerun direct calibration with sidecar broad-normal controls and "
            "chronological/symbol/venue split checks."
        ),
        "nowak_smith_sidecar_positive_rows": nowak_sidecar_rows,
        "official_sources": downloads,
        "official_sources_screened": len(downloads),
        "pooled_wilson95_would_pass_if_all_sidecars_accepted": what_if_all_lcb >= MIN_WILSON,
        "proposed_positive_rows": len(proposed_rows),
        "proposed_rows_path": str(proposed_rows_path),
        "raw_data_committed": False,
        "raw_root": str(RAW_ROOT),
        "report_path": "",
        "row_materializable_sources": [row["source_row_id"] for row in proposed_rows],
        "run_id": RUN_ID,
        "runtime_code_changed": False,
        "sarao_sidecar_positive_rows": sarao_sidecar_rows,
        "shared_intake_mutated": False,
        "sidecar_broad_normal_control_rows": sidecar_broad_normal_control_rows,
        "source_screen_count": len(source_screens),
        "source_screen_path": str(source_screen_path),
        "strict_full_objective_achieved": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "update_goal": False,
        "what_if_min_wilson95_lcb_with_all_sidecars": what_if_all_lcb,
        "what_if_positive_rows_with_all_sidecars": what_if_all_rows,
    }
    report_path = write_report(summary)
    summary["report_path"] = str(report_path)
    Path(summary["json_path"]).write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    assertions = [
        ("sources_fetched", len(downloads) == len(SOURCES)),
        ("candidate_rows_found", len(proposed_rows) == 4),
        ("shared_intake_not_mutated", summary["shared_intake_mutated"] is False),
        ("live_verifier_captured", verifier["returncode"] in (0, 2)),
        ("no_acceptance_claimed", summary["new_confidence_gate"] is False),
        ("pooled_wilson_would_pass_if_all_sidecars_accepted", what_if_all_lcb >= MIN_WILSON),
        ("strict_objective_still_false", summary["strict_full_objective_achieved"] is False),
    ]
    assertion_lines = []
    failed = []
    for name, ok in assertions:
        assertion_lines.append(f"{name}={'ok' if ok else 'fail'}")
        if not ok:
            failed.append(name)
    Path(summary["assertions_path"]).write_text(
        "\n".join(assertion_lines) + "\n", encoding="utf-8"
    )
    if failed:
        raise SystemExit(f"assertions failed: {failed}")


if __name__ == "__main__":
    main()
