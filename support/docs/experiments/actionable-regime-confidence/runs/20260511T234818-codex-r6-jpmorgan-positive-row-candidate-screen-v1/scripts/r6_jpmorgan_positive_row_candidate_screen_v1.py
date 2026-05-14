#!/usr/bin/env python3
"""Screen the official JPMorgan CFTC order for R6 positive candidates.

This run is read-only against the shared direct-manipulation intake. It writes
proposed source-owned positive rows into this run directory only and computes
Wilson95 what-if readbacks against the last verifier-backed R6 direct count.
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
from typing import Any


RUN_ID = "20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-jpmorgan-positive-row-candidate-screen"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

RAW_ROOT = Path("/tmp/ict-engine-r6-jpmorgan-positive-row-candidate-screen-v1/raw")
LIVE_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
V54_AUDIT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T223100-codex-current-goal-completion-audit-v54-after-sidecar-calibration"
    / "completion-audit/current_goal_completion_audit_v54_after_sidecar_calibration.json"
)
SARAO_CANDIDATES = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T225505-codex-r6-sarao-positive-row-candidate-screen-v1"
    / "r6-sarao-positive-row-candidate-screen/r6_sarao_positive_row_candidates_v1.csv"
)
NOWAK_CANDIDATES = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T233454-codex-r6-nowak-smith-positive-row-candidate-screen-v1"
    / "r6-nowak-smith-positive-row-candidate-screen/r6_nowak_smith_positive_row_candidates_v1.csv"
)
SIDECAR_CONTROLS = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1"
    / "r6-broad-normal-order-lifecycle-screen/broad_normal_market_order_lifecycle_controls_v1.csv"
)

Z_95 = 1.96
MIN_WILSON = 0.95
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
class CandidateCase:
    source_row_id: str
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
    required_snippets: list[str] = field(default_factory=list)


SOURCE_URL = "https://www.cftc.gov/media/4826/enfjpmorganchaseorder092920/download"
SOURCE_REPORT = "CFTC Order: JPMorgan Chase Bank, N.A., JPMorgan Chase & Co., and J.P. Morgan Securities LLC, Sep. 29 2020"
PARTICIPANT_TYPE = "CFTC respondent trader; JPMorgan precious-metals or treasuries desk"
STATUS = "proposed_sidecar_not_shared_intake"

CASES = [
    CandidateCase(
        source_row_id="cftc_jpm_20111212_trader1_silver_buy_layered_spoof",
        source_section="JPM CFTC order, precious-metals example: December 12 2011 Silver Futures",
        trade_date="2011-12-12",
        symbol="Silver Futures contract, March 2012 expiry",
        venue_or_market_center="COMEX/CME Globex",
        participant_identifier="Trader 1 / JPM precious metals desk",
        side="buy-side Layered Spoof Orders against genuine sell order",
        earliest_order_received_time="11:59:39.168 source-timezone-unspecified",
        latest_order_received_time="11:59:40.332 source-timezone-unspecified",
        order_count="five buy-side layered spoof orders intended to cancel",
        total_order_quantity="50 lots",
        activity_description=(
            "Official CFTC order describes Trader 1 placing a five-lot genuine sell "
            "order, then five buy-side layered spoof orders totaling fifty lots; the "
            "genuine sell filled and the layered spoof orders were then canceled."
        ),
        matched_negative_group_id="cftc_jpm_20111212_trader1_silver_sell_genuine_buy_layered",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "on December 12, 2011, at 11:59:36.669",
            "entering a series of five Layered Spoof Orders on the buy side of the market totaling 50 lots",
            "At 11:59:40.332 a.m.",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_jpm_20131210_trader5_silver_buy_spoof",
        source_section="JPM CFTC order, precious-metals example: December 10 2013 Silver Futures",
        trade_date="2013-12-10",
        symbol="Silver Futures contract, March 2014 expiry",
        venue_or_market_center="COMEX/CME Globex",
        participant_identifier="Trader 5 / JPM precious metals desk",
        side="buy-side Spoof Order against genuine sell order",
        earliest_order_received_time="01:59:26.901 source-timezone-unspecified",
        latest_order_received_time="01:59:27.729 source-timezone-unspecified",
        order_count="one buy-side spoof order intended to cancel",
        total_order_quantity="100 lots",
        activity_description=(
            "Official CFTC order describes Trader 5 placing a twenty-lot iceberg "
            "genuine sell order, then a one-hundred-lot buy-side spoof order; the "
            "genuine sell filled and the spoof order was canceled less than one second later."
        ),
        matched_negative_group_id="cftc_jpm_20131210_trader5_silver_sell_genuine_buy_spoof",
        session_bucket="overnight_source_time",
        required_snippets=[
            "On December 10, 2013, at 1:59:22.386 a.m.",
            "Trader 5 entered a Spoof Order for 100 lots",
            "at 1:59:27.729 a.m.",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_jpm_20140305_trader6_silver_buy_layered_spoof",
        source_section="JPM CFTC order, precious-metals example: March 5 2014 Silver Futures",
        trade_date="2014-03-05",
        symbol="Silver Futures contract, May 2014 expiry",
        venue_or_market_center="COMEX/CME Globex",
        participant_identifier="Trader 6 / JPM precious metals desk",
        side="buy-side Layered Spoof Orders against genuine sell order",
        earliest_order_received_time="08:18:40 source-timezone-unspecified",
        latest_order_received_time="08:18:41.595 source-timezone-unspecified",
        order_count="ten buy-side layered spoof orders intended to cancel",
        total_order_quantity="not stated; ten layered orders",
        activity_description=(
            "Official CFTC order describes Trader 6 placing a two-lot genuine sell "
            "order, then ten buy-side layered spoof orders; the genuine sell filled "
            "milliseconds after the tenth spoof order and the layered spoof orders were canceled."
        ),
        matched_negative_group_id="cftc_jpm_20140305_trader6_silver_sell_genuine_buy_layered",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On March 5, 2014, at 8:18:39.699 a.m.",
            "Trader 6 began entering a series of Layered Spoof Orders on the buy side",
            "8:18:41.595",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_jpm_20160622_trader4_platinum_buy_layered_spoof",
        source_section="JPM CFTC order, precious-metals example: June 22 2016 Platinum Futures",
        trade_date="2016-06-22",
        symbol="Platinum Futures contract, July 2016 expiry",
        venue_or_market_center="NYMEX/CME Globex",
        participant_identifier="Trader 4 / JPM precious metals desk",
        side="buy-side Layered Spoof Orders against genuine sell order",
        earliest_order_received_time="02:14:35 source-timezone-unspecified",
        latest_order_received_time="02:14:37.407 source-timezone-unspecified",
        order_count="eight buy-side layered spoof orders intended to cancel",
        total_order_quantity="40 lots",
        activity_description=(
            "Official CFTC order describes Trader 4 placing a twenty-lot iceberg "
            "genuine sell order, then eight buy-side layered spoof orders totaling "
            "forty lots; genuine order fills began after the fifth layered order and "
            "the layered spoof orders were canceled."
        ),
        matched_negative_group_id="cftc_jpm_20160622_trader4_platinum_sell_genuine_buy_layered",
        session_bucket="overnight_source_time",
        required_snippets=[
            "On June 22, 2016, at 2:14:33.935 a.m.",
            "series of eight Layered Spoof Orders on the buy",
            "2:14:37.407",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_jpm_20090720_trader7_tbond_buy_layered_spoof",
        source_section="JPM CFTC order, treasuries example: July 20 2009 T-Bond Futures",
        trade_date="2009-07-20",
        symbol="T-Bond Futures contract, September 2009 expiry",
        venue_or_market_center="CBOT/CME Globex",
        participant_identifier="Trader 7 / JPM treasuries desk",
        side="buy-side Layered Spoof Orders against genuine sell order",
        earliest_order_received_time="07:47:17.096 source-timezone-unspecified",
        latest_order_received_time="07:47:22.038 source-timezone-unspecified",
        order_count="six buy-side layered spoof orders intended to cancel",
        total_order_quantity="1800 lots",
        activity_description=(
            "Official CFTC order describes Trader 7 placing a one-hundred-lot genuine "
            "sell order, then six buy-side layered spoof orders totaling eighteen "
            "hundred lots; the genuine sell filled and the layered spoof orders were canceled."
        ),
        matched_negative_group_id="cftc_jpm_20090720_trader7_tbond_sell_genuine_buy_layered",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On July 20, 2009, at 7:47:13.597 a.m.",
            "six Layered Spoof Orders on the buy side of the market totaling 1,800",
            "At 7:47:22.038",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_jpm_20100204_trader8_10y_tnote_sell_spoof",
        source_section="JPM CFTC order, treasuries example: February 4 2010 10-Year T-Note Futures",
        trade_date="2010-02-04",
        symbol="10-Year T-Note Futures contract, March 2010 expiry",
        venue_or_market_center="CBOT/CME Globex",
        participant_identifier="Trader 8 / JPM treasuries desk",
        side="sell-side Spoof Order against genuine buy order",
        earliest_order_received_time="13:30:00.539 source-timezone-unspecified",
        latest_order_received_time="13:30:01.467 source-timezone-unspecified",
        order_count="one sell-side spoof order intended to cancel",
        total_order_quantity="1000 lots",
        activity_description=(
            "Official CFTC order describes Trader 8 placing a ten-lot genuine buy "
            "order, then a one-thousand-lot sell-side spoof order; the genuine buy "
            "filled and the spoof order was canceled less than a second later."
        ),
        matched_negative_group_id="cftc_jpm_20100204_trader8_10y_tnote_buy_genuine_sell_spoof",
        session_bucket="regular_us_afternoon_source_time",
        required_snippets=[
            "On February 4, 2010, at 1:27:27.279 p.m.",
            "Trader 8 entered a Spoof Order for 1,000 lots on the sell side",
            "at 1:30:01.467 p.m.",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_jpm_20110927_trader9_10y_tnote_sell_spoof",
        source_section="JPM CFTC order, treasuries example: September 27 2011 10-Year T-Note Futures",
        trade_date="2011-09-27",
        symbol="10-Year T-Note Futures contract, December 2011 expiry",
        venue_or_market_center="CBOT/CME Globex",
        participant_identifier="Trader 9 / JPM treasuries desk",
        side="sell-side Spoof Order against genuine buy order",
        earliest_order_received_time="14:03:57.635 source-timezone-unspecified",
        latest_order_received_time="14:03:57.953 source-timezone-unspecified",
        order_count="one sell-side spoof order intended to cancel",
        total_order_quantity="3000 lots",
        activity_description=(
            "Official CFTC order describes Trader 9 placing a fifty-lot genuine buy "
            "order, then a three-thousand-lot sell-side spoof order; the genuine buy "
            "filled and the spoof order was canceled less than one-third of a second later."
        ),
        matched_negative_group_id="cftc_jpm_20110927_trader9_10y_tnote_buy_genuine_sell_spoof",
        session_bucket="regular_us_afternoon_source_time",
        required_snippets=[
            "On September 27, 2011, at 2:03:54.204 p.m.",
            "Trader 9 entered a Spoof Order for 3,000 lots",
            "at 2:03:57.953 p.m.",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_jpm_20150630_trader10_ultra_tbond_sell_spoof",
        source_section="JPM CFTC order, treasuries example: June 30 2015 Ultra T-Bond Futures",
        trade_date="2015-06-30",
        symbol="Ultra T-Bond Futures contract, September 2015 expiry",
        venue_or_market_center="CBOT/CME Globex",
        participant_identifier="Trader 10 / JPM treasuries desk",
        side="sell-side Spoof Order against genuine buy order",
        earliest_order_received_time="08:46:01.891 source-timezone-unspecified",
        latest_order_received_time="08:46:04.418 source-timezone-unspecified",
        order_count="one sell-side spoof order intended to cancel",
        total_order_quantity="100 lots",
        activity_description=(
            "Official CFTC order describes Trader 10 placing a two-hundred-lot "
            "iceberg genuine buy order, then a one-hundred-lot sell-side spoof "
            "order; fifty-one genuine lots filled and the spoof order was canceled."
        ),
        matched_negative_group_id="cftc_jpm_20150630_trader10_ultra_tbond_buy_genuine_sell_spoof",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On June 30, 2015, at 8:45:46.627 a.m.",
            "Trader 10 entered a Spoof Order for 100 lots on the sell side",
            "at 8:46:04.418 a.m.",
        ],
    ),
]


def normalize(text: str) -> str:
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


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def wilson_lcb(n: int) -> float:
    if n <= 0:
        return 0.0
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / n
    center = 1.0 + z2 / (2.0 * n)
    margin = Z_95 * math.sqrt(z2 / (4.0 * n * n))
    return max(0.0, (center - margin) / denom)


def rows_needed_for_lcb(current_successes: int, threshold: float) -> int:
    needed = 0
    while wilson_lcb(current_successes + needed) < threshold:
        needed += 1
    return needed


def download_source() -> dict[str, Any]:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    target = RAW_ROOT / "enfjpmorganchaseorder092920.pdf"
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "ict-engine-board-a-audit/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        target.write_bytes(response.read())
        return {
            "url": SOURCE_URL,
            "pdf_path": str(target),
            "http_status": getattr(response, "status", None),
            "content_type": response.headers.get("content-type", ""),
            "bytes": target.stat().st_size,
            "sha256": sha256(target),
            "expected_use": "source-owned row-level positive direct spoofing/layering candidates",
        }


def extract_pdf_text(pdf_path: Path) -> Path:
    gs = shutil.which("gs")
    if gs is None:
        raise RuntimeError("Ghostscript binary 'gs' is required")
    text_path = pdf_path.with_suffix(".txt")
    result = subprocess.run(
        [
            gs,
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=txtwrite",
            f"-o{text_path}",
            str(pdf_path),
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    (COMMAND_OUT / "ghostscript_extract.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (COMMAND_OUT / "ghostscript_extract.stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return text_path


def run_direct_verifier() -> dict[str, Any]:
    result = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_INTAKE)],
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
    try:
        payload = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {"status": "unparsed"}
    return {
        "returncode": result.returncode,
        "payload": payload,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
    }


def v54_positive_rows() -> int:
    data = json.loads(V54_AUDIT.read_text(encoding="utf-8"))
    return int(data["direct_verifier"]["payload"]["positive_rows"])


def build_rows(text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    normalized = normalize(text)
    rows: list[dict[str, Any]] = []
    screens: list[dict[str, Any]] = []
    for case in CASES:
        hits = {snippet: normalize(snippet) in normalized for snippet in case.required_snippets}
        materializable = all(hits.values())
        screens.append(
            {
                "source_row_id": case.source_row_id,
                "source_section": case.source_section,
                "trade_date": case.trade_date,
                "symbol": case.symbol,
                "venue_or_market_center": case.venue_or_market_center,
                "participant_identifier": case.participant_identifier,
                "materializable": str(materializable).lower(),
                "snippet_hits_json": json.dumps(hits, sort_keys=True),
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
                "candidate_row_status": STATUS,
            }
        )
    return rows, screens


def write_report(summary: dict[str, Any]) -> Path:
    path = OUT / "r6_jpmorgan_positive_row_candidate_screen_v1.md"
    lines = [
        "# R6 JPMorgan Positive Row Candidate Screen v1",
        "",
        f"- Run id: `{summary['run_id']}`",
        f"- Generated at UTC: `{summary['generated_at_utc']}`",
        f"- Official source: {SOURCE_URL}",
        f"- Shared intake mutated: `{str(summary['shared_intake_mutated']).lower()}`",
        f"- Live verifier status: `{summary['live_verifier_status']}`",
        f"- Baseline positive rows used for what-if: `{summary['baseline_positive_rows']}` from `{summary['baseline_positive_rows_source']}`",
        f"- Proposed positive rows: `{summary['proposed_positive_rows']}`",
        f"- What-if positives after Sarao + Nowak/Smith + JPMorgan sidecars: `{summary['what_if_positive_rows_with_all_sidecars']}`",
        f"- What-if min Wilson95 LCB after all sidecars: `{summary['what_if_min_wilson95_lcb_with_all_sidecars']:.12f}`",
        f"- Additional rows still needed after all sidecars if all accepted: `{summary['additional_positive_rows_needed_after_all_sidecars_if_all_accepted']}`",
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


def main() -> int:
    for path in [OUT, COMMAND_OUT, CHECKS, RAW_ROOT]:
        path.mkdir(parents=True, exist_ok=True)

    download = download_source()
    text_path = extract_pdf_text(Path(download["pdf_path"]))
    text = text_path.read_text(encoding="utf-8", errors="replace")
    proposed_rows, source_screens = build_rows(text)

    proposed_path = OUT / "r6_jpmorgan_positive_row_candidates_v1.csv"
    source_screen_path = OUT / "r6_jpmorgan_positive_row_source_screen_v1_cases.csv"
    write_csv(proposed_path, proposed_rows, ROW_FIELDS)
    write_csv(
        source_screen_path,
        source_screens,
        [
            "source_row_id",
            "source_section",
            "trade_date",
            "symbol",
            "venue_or_market_center",
            "participant_identifier",
            "materializable",
            "snippet_hits_json",
            "screen_status",
        ],
    )

    verifier = run_direct_verifier()
    live_payload = verifier["payload"]
    live_status = str(live_payload.get("status", "unknown"))
    if verifier["returncode"] == 0 and "positive_rows" in live_payload:
        baseline_positive_rows = int(live_payload["positive_rows"])
        baseline_source = "live_direct_verifier"
    else:
        baseline_positive_rows = v54_positive_rows()
        baseline_source = "v54_verifier_artifact_live_intake_missing_or_blocked"

    sarao_count = len(read_csv(SARAO_CANDIDATES))
    nowak_count = len(read_csv(NOWAK_CANDIDATES))
    sidecar_control_count = len(read_csv(SIDECAR_CONTROLS))
    jpm_count = len(proposed_rows)
    after_jpm_only = baseline_positive_rows + jpm_count
    after_all = baseline_positive_rows + sarao_count + nowak_count + jpm_count
    sidecar_lcb = wilson_lcb(sidecar_control_count)
    after_jpm_only_lcb = wilson_lcb(after_jpm_only)
    after_all_lcb = wilson_lcb(after_all)
    after_all_min_lcb = min(after_all_lcb, sidecar_lcb)

    gate_result = (
        "r6_jpmorgan_positive_row_candidate_screen_v1="
        "proposed_rows_reach_pooled_whatif_but_live_intake_missing"
    )
    next_action = (
        "Reconstruct or lock the shared direct intake, accept Sarao/Nowak/JPMorgan "
        "positives only with matched same-source controls, then rerun the direct verifier "
        "and sidecar broad-normal calibration; do not claim a new confidence gate until "
        "live intake and split/species gates pass."
    )

    summary: dict[str, Any] = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "source": download,
        "raw_text_path": str(text_path),
        "shared_intake_mutated": False,
        "live_verifier": verifier,
        "live_verifier_status": live_status,
        "baseline_positive_rows": baseline_positive_rows,
        "baseline_positive_rows_source": baseline_source,
        "sidecar_broad_normal_control_rows": sidecar_control_count,
        "sarao_sidecar_positive_rows": sarao_count,
        "nowak_smith_sidecar_positive_rows": nowak_count,
        "proposed_positive_rows": jpm_count,
        "proposed_rows_path": str(proposed_path),
        "source_screen_path": str(source_screen_path),
        "source_screen_count": len(source_screens),
        "row_materializable_sources": [
            row["source_row_id"] for row in source_screens if row["materializable"] == "true"
        ],
        "what_if_positive_rows_jpmorgan_only": after_jpm_only,
        "what_if_positive_wilson95_lcb_jpmorgan_only": round(after_jpm_only_lcb, 12),
        "what_if_positive_rows_with_all_sidecars": after_all,
        "what_if_positive_wilson95_lcb_with_all_sidecars": round(after_all_lcb, 12),
        "sidecar_broad_normal_wilson95_lcb": round(sidecar_lcb, 12),
        "what_if_min_wilson95_lcb_with_all_sidecars": round(after_all_min_lcb, 12),
        "additional_positive_rows_needed_after_all_sidecars_if_all_accepted": rows_needed_for_lcb(after_all, MIN_WILSON),
        "gate_result": gate_result,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "next_action": next_action,
    }
    json_path = OUT / "r6_jpmorgan_positive_row_candidate_screen_v1.json"
    summary["json_path"] = str(json_path)
    assertions_path = CHECKS / "r6_jpmorgan_positive_row_candidate_screen_v1_assertions.out"
    summary["assertions_path"] = str(assertions_path)
    report_path = write_report(summary)
    summary["report_path"] = str(report_path)
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    assertions = {
        "source_pdf_downloaded": download["bytes"] > 0,
        "all_candidate_snippets_verified": len(proposed_rows) == len(CASES),
        "proposed_rows_positive_count": jpm_count == 8,
        "shared_intake_read_only": summary["shared_intake_mutated"] is False,
        "baseline_source_explicit": bool(baseline_source),
        "what_if_all_sidecars_reaches_pooled_95": after_all_min_lcb >= MIN_WILSON,
        "strict_full_objective_not_complete": summary["strict_full_objective_achieved"] is False,
        "no_runtime_code_changed": summary["runtime_code_changed"] is False,
    }
    assertions_path.write_text(
        "\n".join(f"{name}={'ok' if passed else 'FAIL'}" for name, passed in assertions.items()) + "\n",
        encoding="utf-8",
    )
    if not all(assertions.values()):
        raise SystemExit(2)
    print(json.dumps({"gate_result": gate_result, "proposed_rows": jpm_count, "after_all_min_lcb": round(after_all_min_lcb, 12)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
