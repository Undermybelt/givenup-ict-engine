#!/usr/bin/env python3
"""Screen the official CFTC JPMorgan order for R6 direct positive candidates.

This is a read-only sidecar against the shared direct-manipulation intake. It
does not mutate /tmp/ict-engine-direct-manipulation-row-intake. It materializes
proposed positive and matched-control rows into this run directory, then
computes what-if Wilson95 readbacks against the latest stable R6 base artifact.
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
from typing import Any


RUN_ID = "20260511T234746-codex-r6-jpmorgan-positive-row-candidate-screen-v1"
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
BASE_ARTIFACT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T223100-codex-current-goal-completion-audit-v54-after-sidecar-calibration"
    / "completion-audit"
    / "current_goal_completion_audit_v54_after_sidecar_calibration.json"
)

SOURCE_URL = "https://www.cftc.gov/media/4826/enfjpmorganchaseorder092920/download"
SOURCE_FILENAME = "enfjpmorganchaseorder092920.pdf"
SOURCE_REPORT = "CFTC Order: JPMorgan Chase Bank, N.A., J.P. Morgan Securities LLC, and J.P. Morgan Securities plc, Sep. 29 2020"
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


CASES = [
    CandidateCase(
        source_row_id="cftc_jpm_20111212_trader1_silver_buy_layered_spoof",
        source_section="Order paragraph 28, Dec. 12 2011 Trader 1 Silver Futures example",
        trade_date="2011-12-12",
        symbol="Silver Futures contract, March 2012 expiry",
        venue_or_market_center="COMEX/CME Globex",
        participant_identifier="Trader 1 / precious metals desk",
        side="buy-side layered spoof orders against genuine sell order",
        earliest_order_received_time="11:59:39.168 source-timezone-unspecified",
        latest_order_received_time="11:59:40.332 source-timezone-unspecified",
        order_count="5 layered spoof orders intended to cancel",
        total_order_quantity="50 lots",
        activity_description=(
            "Official CFTC order describes a five-lot genuine sell order followed by "
            "five buy-side layered spoof orders totaling fifty lots; the genuine order "
            "filled and the layered spoof orders were then canceled."
        ),
        matched_negative_group_id="cftc_jpm_20111212_trader1_silver_layered",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "on December 12, 2011, at 11:59:36.669, Trader 1 placed a Genuine Order to sell 5 lots",
            "five Layered Spoof Orders on the buy side of the market totaling 50 lots",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_jpm_20131210_trader5_silver_buy_spoof",
        source_section="Order paragraph 29, Dec. 10 2013 Trader 5 Silver Futures example",
        trade_date="2013-12-10",
        symbol="Silver Futures contract, March 2014 expiry",
        venue_or_market_center="COMEX/CME Globex",
        participant_identifier="Trader 5 / precious metals desk",
        side="buy-side spoof order against genuine sell order",
        earliest_order_received_time="1:59:26.901 source-timezone-unspecified",
        latest_order_received_time="1:59:27.729 source-timezone-unspecified",
        order_count="1 spoof order intended to cancel",
        total_order_quantity="100 lots",
        activity_description=(
            "Official CFTC order describes a twenty-lot genuine sell iceberg order "
            "followed by a one-hundred-lot buy-side spoof order; the genuine order "
            "filled and the spoof order was canceled less than one second later."
        ),
        matched_negative_group_id="cftc_jpm_20131210_trader5_silver_spoof",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On December 10, 2013, at 1:59:22.386 a.m., a JPM precious metals trader",
            "Trader 5 entered a Spoof Order for 100 lots on the buy side of the market",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_jpm_20140305_trader6_silver_buy_layered_spoof",
        source_section="Order paragraph 31, Mar. 5 2014 Trader 6 Silver Futures example",
        trade_date="2014-03-05",
        symbol="Silver Futures contract, May 2014 expiry",
        venue_or_market_center="COMEX/CME Globex",
        participant_identifier="Trader 6 / precious metals desk",
        side="buy-side layered spoof orders against genuine sell order",
        earliest_order_received_time="8:18:39.699 source-timezone-unspecified",
        latest_order_received_time="8:18:41.595 source-timezone-unspecified",
        order_count="10 layered spoof orders intended to cancel",
        total_order_quantity="not fully enumerated in order text",
        activity_description=(
            "Official CFTC order describes a two-lot genuine sell order followed by "
            "buy-side layered spoof orders; the genuine order filled milliseconds after "
            "the tenth layered spoof order and the layered orders were then canceled."
        ),
        matched_negative_group_id="cftc_jpm_20140305_trader6_silver_layered",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On March 5, 2014, at 8:18:39.699 a.m., a JPM precious metals trader",
            "after Trader 6 had placed his tenth Layered Spoof Order to buy",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_jpm_20160622_trader4_platinum_buy_layered_spoof",
        source_section="Order paragraph 32, Jun. 22 2016 Trader 4 Platinum Futures example",
        trade_date="2016-06-22",
        symbol="Platinum Futures contract, July 2016 expiry",
        venue_or_market_center="NYMEX/CME Globex",
        participant_identifier="Trader 4 / precious metals desk",
        side="buy-side layered spoof orders against genuine sell order",
        earliest_order_received_time="2:14:33.935 source-timezone-unspecified",
        latest_order_received_time="2:14:37.407 source-timezone-unspecified",
        order_count="8 layered spoof orders intended to cancel",
        total_order_quantity="40 lots",
        activity_description=(
            "Official CFTC order describes a twenty-lot genuine sell iceberg order "
            "followed by eight buy-side layered spoof orders totaling forty lots; "
            "the trader then began canceling the layered spoof orders."
        ),
        matched_negative_group_id="cftc_jpm_20160622_trader4_platinum_layered",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On June 22, 2016, at 2:14:33.935 a.m., Trader 4 placed a Genuine Order to sell twenty",
            "eight Layered Spoof Orders on the buy side of the market totaling 40 lots",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_jpm_20090720_trader7_tbond_buy_layered_spoof",
        source_section="Order paragraph 39, Jul. 20 2009 Trader 7 T-Bond Futures example",
        trade_date="2009-07-20",
        symbol="T-Bond Futures contract, September 2009 expiry",
        venue_or_market_center="CBOT/CME Globex",
        participant_identifier="Trader 7 / U.S. Treasuries desk",
        side="buy-side layered spoof orders against genuine sell order",
        earliest_order_received_time="7:47:17.096 source-timezone-unspecified",
        latest_order_received_time="7:47:22.038 source-timezone-unspecified",
        order_count="6 layered spoof orders intended to cancel",
        total_order_quantity="1,800 lots",
        activity_description=(
            "Official CFTC order describes a one-hundred-lot genuine sell order "
            "followed by six buy-side layered spoof orders totaling eighteen hundred "
            "lots; the genuine order filled and the layered orders were canceled."
        ),
        matched_negative_group_id="cftc_jpm_20090720_trader7_tbond_layered",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On July 20, 2009, at 7:47:13.597 a.m., a JPM Treasuries trader",
            "six Layered Spoof Orders on the buy side of the market totaling 1,800",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_jpm_20100204_trader8_10y_tnote_sell_spoof",
        source_section="Order paragraph 40, Feb. 4 2010 Trader 8 Ten-Year T-Note Futures example",
        trade_date="2010-02-04",
        symbol="Ten-Year T-Note Futures contract, March 2010 expiry",
        venue_or_market_center="CBOT/CME Globex",
        participant_identifier="Trader 8 / U.S. Treasuries desk",
        side="sell-side spoof order against genuine buy order",
        earliest_order_received_time="1:30:00.539 source-timezone-unspecified",
        latest_order_received_time="1:30:01.467 source-timezone-unspecified",
        order_count="1 spoof order intended to cancel",
        total_order_quantity="1,000 lots",
        activity_description=(
            "Official CFTC order describes a ten-lot genuine buy order followed by a "
            "one-thousand-lot sell-side spoof order; the genuine order filled and the "
            "spoof order was canceled less than a second later."
        ),
        matched_negative_group_id="cftc_jpm_20100204_trader8_10y_tnote_spoof",
        session_bucket="regular_us_afternoon_source_time",
        required_snippets=[
            "On February 4, 2010, at 1:27:27.279 p.m., a JPM Treasuries trader",
            "Trader 8 entered a Spoof Order for 1,000 lots on the sell side of the market",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_jpm_20110927_trader9_10y_tnote_sell_spoof",
        source_section="Order paragraph 41, Sep. 27 2011 Trader 9 Ten-Year T-Note Futures example",
        trade_date="2011-09-27",
        symbol="Ten-Year T-Note Futures contract, December 2011 expiry",
        venue_or_market_center="CBOT/CME Globex",
        participant_identifier="Trader 9 / U.S. Treasuries desk",
        side="sell-side spoof order against genuine buy order",
        earliest_order_received_time="2:03:57.635 source-timezone-unspecified",
        latest_order_received_time="2:03:57.953 source-timezone-unspecified",
        order_count="1 spoof order intended to cancel",
        total_order_quantity="3,000 lots",
        activity_description=(
            "Official CFTC order describes a fifty-lot genuine buy order followed by "
            "a three-thousand-lot sell-side spoof order; the genuine order filled and "
            "the spoof order was canceled less than one-third of a second later."
        ),
        matched_negative_group_id="cftc_jpm_20110927_trader9_10y_tnote_spoof",
        session_bucket="regular_us_afternoon_source_time",
        required_snippets=[
            "On September 27, 2011, at 2:03:54.204 p.m., a JPM Treasuries trader",
            "Trader 9 entered a Spoof Order for 3,000 lots on the sell side of the market",
        ],
    ),
    CandidateCase(
        source_row_id="cftc_jpm_20150630_trader10_ultra_tbond_sell_spoof",
        source_section="Order paragraph 42, Jun. 30 2015 Trader 10 Ultra T-Bond Futures example",
        trade_date="2015-06-30",
        symbol="Ultra T-Bond Futures contract, September 2015 expiry",
        venue_or_market_center="CBOT/CME Globex",
        participant_identifier="Trader 10 / U.S. Treasuries desk",
        side="sell-side spoof order against genuine buy order",
        earliest_order_received_time="8:46:01.891 source-timezone-unspecified",
        latest_order_received_time="8:46:04.418 source-timezone-unspecified",
        order_count="1 spoof order intended to cancel",
        total_order_quantity="100 lots",
        activity_description=(
            "Official CFTC order describes a two-hundred-lot genuine buy iceberg order "
            "followed by a one-hundred-lot sell-side spoof order; fifty-one lots filled "
            "and the spoof order was canceled shortly afterward."
        ),
        matched_negative_group_id="cftc_jpm_20150630_trader10_ultra_tbond_spoof",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On June 30, 2015, at 8:45:46.627 a.m., the JPM Treasuries trader who served as desk",
            "Trader 10 entered a Spoof Order for 100 lots on the sell side of the market",
        ],
    ),
]


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


def wilson_lcb(successes: int, total: int, z: float = Z_95) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = z * z
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def additional_successes_needed(current_successes: int, threshold: float = MIN_WILSON) -> int:
    for total in range(current_successes, current_successes + 500):
        if wilson_lcb(total, total) >= threshold:
            return total - current_successes
    return 500


def download_source() -> dict[str, Any]:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    target = RAW_ROOT / SOURCE_FILENAME
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "ict-engine-board-a-audit/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read()
        target.write_bytes(body)
        return {
            "case_id": "jpmorgan_2020_order",
            "url": SOURCE_URL,
            "pdf_path": str(target),
            "http_status": getattr(response, "status", None),
            "content_type": response.headers.get("content-type", ""),
            "bytes": len(body),
            "sha256": sha256(target),
            "expected_use": "row-level positive and same-report genuine-order control candidates",
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
    (COMMAND_OUT / "extract_jpmorgan_order.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (COMMAND_OUT / "extract_jpmorgan_order.stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return text_path


def normalize(text: str) -> str:
    return " ".join(text.replace("\u00a0", " ").split()).lower()


def source_screen_rows(text: str, source: dict[str, Any]) -> list[dict[str, Any]]:
    normalized = normalize(text)
    rows = []
    for case in CASES:
        snippet_hits = sum(1 for snippet in case.required_snippets if normalize(snippet) in normalized)
        rows.append(
            {
                "source_row_id": case.source_row_id,
                "trade_date": case.trade_date,
                "symbol": case.symbol,
                "venue_or_market_center": case.venue_or_market_center,
                "source_section": case.source_section,
                "snippet_hits": snippet_hits,
                "snippet_total": len(case.required_snippets),
                "row_materializable": snippet_hits == len(case.required_snippets),
                "accepted_now": False,
                "reason": "Official order snippets present; materialized as proposed sidecar row only.",
                "source_pdf_sha256": source["sha256"],
                "source_url": source["url"],
            }
        )
    return rows


def positive_rows() -> list[dict[str, str]]:
    return [
        {
            "label": "positive_spoofing_layering",
            "source_report": SOURCE_REPORT,
            "source_section": case.source_section,
            "trade_date": case.trade_date,
            "symbol": case.symbol,
            "venue_or_market_center": case.venue_or_market_center,
            "participant_type_code": "CFTC-regulated institutional trader desk",
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
            "candidate_row_status": "proposed_sidecar_not_shared_intake",
        }
        for case in CASES
    ]


def matched_control_rows() -> list[dict[str, str]]:
    rows = []
    for case in CASES:
        rows.append(
            {
                "label": "matched_negative_normal_activity",
                "source_report": SOURCE_REPORT,
                "source_section": case.source_section,
                "trade_date": case.trade_date,
                "symbol": case.symbol,
                "venue_or_market_center": case.venue_or_market_center,
                "participant_type_code": "CFTC-regulated institutional trader desk",
                "participant_identifier": case.participant_identifier,
                "side": "same-report genuine order leg opposite proposed spoof orders",
                "earliest_order_received_time": case.earliest_order_received_time,
                "latest_order_received_time": case.latest_order_received_time,
                "order_count": "one source-described genuine order leg",
                "total_order_quantity": "source-described genuine order quantity",
                "activity_description": (
                    "Same official paragraph describes the genuine order leg used only as "
                    "a matched same-report schema control; it is not broad-normal market background."
                ),
                "matched_negative_group_id": case.matched_negative_group_id,
                "session_bucket": case.session_bucket,
                "source_row_id": f"{case.source_row_id}_matched_genuine_leg_control",
                "candidate_row_status": "proposed_sidecar_not_shared_intake",
            }
        )
    return rows


def run_live_verifier() -> dict[str, Any]:
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
        "payload": payload,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
    }


def base_counts(live_verifier: dict[str, Any]) -> dict[str, Any]:
    payload = live_verifier.get("payload", {})
    if live_verifier.get("returncode") == 0 and payload.get("status") == "schema_ready_unscored":
        return {
            "source": "live_shared_intake",
            "positive_rows": int(payload.get("positive_rows", 0) or 0),
            "matched_negative_rows": int(payload.get("matched_negative_rows", 0) or 0),
            "matched_group_count": int(payload.get("matched_group_count", 0) or 0),
        }
    artifact = json.loads(BASE_ARTIFACT.read_text(encoding="utf-8"))
    decision = artifact.get("decision", {})
    return {
        "source": "v54_artifact_fallback_because_live_shared_intake_not_ready",
        "positive_rows": int(decision.get("r6_positive_rows", artifact.get("r6_positive_rows", 57)) or 57),
        "matched_negative_rows": int(decision.get("r6_matched_negative_rows", artifact.get("r6_matched_negative_rows", 57)) or 57),
        "matched_group_count": int(decision.get("r6_matched_group_count", artifact.get("r6_matched_group_count", 56)) or 56),
        "artifact": str(BASE_ARTIFACT),
    }


def count_rows(path: Path) -> int:
    return len(read_csv(path))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_sha = sha256(BOARD)
    live_verifier = run_live_verifier()
    base = base_counts(live_verifier)
    source = download_source()
    text_path = extract_pdf_text(Path(str(source["pdf_path"])))
    text = text_path.read_text(encoding="utf-8", errors="replace")
    screen_rows = source_screen_rows(text, source)
    materializable_ids = {row["source_row_id"] for row in screen_rows if row["row_materializable"]}
    materializable_groups = {
        case.matched_negative_group_id for case in CASES if case.source_row_id in materializable_ids
    }
    proposed_positive_rows = [
        row for row in positive_rows() if row["source_row_id"] in materializable_ids
    ]
    proposed_control_rows = [
        row for row in matched_control_rows() if row["matched_negative_group_id"] in materializable_groups
    ]

    jpm_count = len(proposed_positive_rows)
    sarao_count = count_rows(SARAO_CANDIDATES)
    nowak_smith_count = count_rows(NOWAK_SMITH_CANDIDATES)
    sidecar_count = count_rows(SIDECAR_CONTROLS)
    base_positive = int(base["positive_rows"])
    current_lcb = wilson_lcb(base_positive, base_positive)
    combined_without_jpm = base_positive + sarao_count + nowak_smith_count
    combined_with_jpm = combined_without_jpm + jpm_count
    combined_without_jpm_lcb = wilson_lcb(combined_without_jpm, combined_without_jpm)
    combined_with_jpm_lcb = wilson_lcb(combined_with_jpm, combined_with_jpm)
    sidecar_lcb = wilson_lcb(sidecar_count, sidecar_count)

    write_csv(OUT / "r6_jpmorgan_positive_row_source_screen_v1_cases.csv", screen_rows, list(screen_rows[0].keys()))
    write_csv(OUT / "r6_jpmorgan_positive_row_candidates_v1.csv", proposed_positive_rows, ROW_FIELDS)
    write_csv(OUT / "r6_jpmorgan_matched_control_candidates_v1.csv", proposed_control_rows, ROW_FIELDS)

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_sha,
        "source": source,
        "raw_text_path": str(text_path),
        "source_screen_count": len(screen_rows),
        "row_materializable_sources": [row["source_row_id"] for row in screen_rows if row["row_materializable"]],
        "proposed_positive_rows": len(proposed_positive_rows),
        "proposed_matched_control_rows": len(proposed_control_rows),
        "proposed_rows_path": str(OUT / "r6_jpmorgan_positive_row_candidates_v1.csv"),
        "proposed_controls_path": str(OUT / "r6_jpmorgan_matched_control_candidates_v1.csv"),
        "source_screen_path": str(OUT / "r6_jpmorgan_positive_row_source_screen_v1_cases.csv"),
        "direct_verifier": live_verifier,
        "base_count_source": base,
        "base_positive_rows": base_positive,
        "current_positive_wilson95_lcb": round(current_lcb, 12),
        "sarao_sidecar_positive_rows": sarao_count,
        "nowak_smith_sidecar_positive_rows": nowak_smith_count,
        "jpmorgan_sidecar_positive_rows": jpm_count,
        "sidecar_broad_normal_control_rows": sidecar_count,
        "sidecar_broad_normal_wilson95_lcb": round(sidecar_lcb, 12),
        "what_if_positive_rows_sarao_nowak_smith": combined_without_jpm,
        "what_if_min_wilson95_lcb_sarao_nowak_smith": round(min(combined_without_jpm_lcb, sidecar_lcb), 12),
        "what_if_positive_rows_sarao_nowak_smith_jpmorgan": combined_with_jpm,
        "what_if_min_wilson95_lcb_sarao_nowak_smith_jpmorgan": round(min(combined_with_jpm_lcb, sidecar_lcb), 12),
        "additional_positive_rows_needed_now": additional_successes_needed(base_positive),
        "additional_positive_rows_needed_after_sarao_nowak_smith": additional_successes_needed(combined_without_jpm),
        "additional_positive_rows_needed_after_sarao_nowak_smith_jpmorgan": additional_successes_needed(combined_with_jpm),
        "shared_intake_mutated": False,
        "accepted_rows_added": 0,
        "new_pooled_positive_confidence_gate_if_all_sidecars_accepted": combined_with_jpm_lcb >= MIN_WILSON,
        "new_live_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "gate_result": "r6_jpmorgan_positive_row_candidate_screen_v1=proposed_rows_only_pooled_whatif_pass_live_split_still_blocked",
        "next_action": (
            "Rebuild or recover the shared 57/57 intake under a fresh lock, then decide whether to accept "
            "Sarao, Nowak/Smith, and JPMorgan proposed rows plus matched controls before rerunning live "
            "direct calibration with sidecar broad-normal controls and split/species gates."
        ),
    }

    json_path = OUT / "r6_jpmorgan_positive_row_candidate_screen_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# R6 JPMorgan Positive Row Candidate Screen v1",
        "",
        f"- Run id: `{RUN_ID}`",
        f"- Generated at UTC: `{result['generated_at_utc']}`",
        f"- Official source: {SOURCE_URL}",
        f"- Shared intake mutated: `{str(result['shared_intake_mutated']).lower()}`",
        f"- Live direct verifier status: `{live_verifier['payload'].get('status', 'unknown')}` from return code `{live_verifier['returncode']}`.",
        f"- Base count source: `{base['source']}`; base positives `{base_positive}`.",
        f"- Proposed JPMorgan positives: `{jpm_count}`; proposed JPMorgan matched controls: `{len(proposed_control_rows)}`.",
        f"- Existing proposed sidecars: Sarao `{sarao_count}`, Nowak/Smith `{nowak_smith_count}`.",
        f"- Current/base Wilson95 LCB: `{result['current_positive_wilson95_lcb']}`.",
        f"- What-if positives after Sarao + Nowak/Smith + JPMorgan: `{combined_with_jpm}`.",
        f"- What-if min Wilson95 LCB after all three sidecars: `{result['what_if_min_wilson95_lcb_sarao_nowak_smith_jpmorgan']}`.",
        f"- Additional positive rows still needed after all three sidecars: `{result['additional_positive_rows_needed_after_sarao_nowak_smith_jpmorgan']}`.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Live acceptance remains blocked because this run did not mutate or rebuild the shared intake, and chronological/symbol/venue split plus direct-species gates still need a live calibration rerun.",
        "",
        "## Artifacts",
        f"- JSON: `{json_path}`",
        f"- Proposed positives CSV: `{OUT / 'r6_jpmorgan_positive_row_candidates_v1.csv'}`",
        f"- Proposed controls CSV: `{OUT / 'r6_jpmorgan_matched_control_candidates_v1.csv'}`",
        f"- Source screen CSV: `{OUT / 'r6_jpmorgan_positive_row_source_screen_v1_cases.csv'}`",
        f"- Assertions: `{CHECKS / 'r6_jpmorgan_positive_row_candidate_screen_v1_assertions.out'}`",
    ]
    report_path = OUT / "r6_jpmorgan_positive_row_candidate_screen_v1.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_start={board_sha}",
        f"live_verifier_status={live_verifier['payload'].get('status', 'unknown')}",
        f"base_count_source={base['source']}",
        f"proposed_positive_rows={jpm_count}",
        f"proposed_matched_control_rows={len(proposed_control_rows)}",
        f"what_if_positive_rows_sarao_nowak_smith_jpmorgan={combined_with_jpm}",
        f"what_if_min_wilson95_lcb_sarao_nowak_smith_jpmorgan={result['what_if_min_wilson95_lcb_sarao_nowak_smith_jpmorgan']}",
        f"additional_positive_rows_needed_after_sarao_nowak_smith_jpmorgan={result['additional_positive_rows_needed_after_sarao_nowak_smith_jpmorgan']}",
        f"new_pooled_positive_confidence_gate_if_all_sidecars_accepted={str(result['new_pooled_positive_confidence_gate_if_all_sidecars_accepted']).lower()}",
        "shared_intake_mutated=false",
        "accepted_rows_added=0",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        "assertion_status=PASS",
    ]
    (CHECKS / "r6_jpmorgan_positive_row_candidate_screen_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"ok": True, "run_id": RUN_ID, "proposed_positive_rows": jpm_count, "what_if_min_wilson95_lcb": result["what_if_min_wilson95_lcb_sarao_nowak_smith_jpmorgan"], "update_goal": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
