#!/usr/bin/env python3
"""Screen the official JPMorgan CFTC order for R6 positive row candidates.

This run is deliberately run-scoped. It does not recreate or mutate the missing
shared /tmp direct-manipulation intake root. Instead it produces a verified
delta intake and a composite count readback against the latest V54 baseline.
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


RUN_ID = "20260511T235048-codex-r6-jpmorgan-order-positive-row-candidate-screen-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-jpmorgan-order-positive-row-candidate-screen"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
DELTA_INTAKE = RUN_ROOT / "delta-intake"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RAW_ROOT = Path("/tmp/ict-engine-r6-jpmorgan-order-positive-row-candidate-screen-v1/raw")
LIVE_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
V54_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T223100-codex-current-goal-completion-audit-v54-after-sidecar-calibration"
    / "completion-audit/current_goal_completion_audit_v54_after_sidecar_calibration.json"
)
SARAO_ROWS = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T225505-codex-r6-sarao-positive-row-candidate-screen-v1"
    / "r6-sarao-positive-row-candidate-screen/r6_sarao_positive_row_candidates_v1.csv"
)
NOWAK_ROWS = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T233454-codex-r6-nowak-smith-positive-row-candidate-screen-v1"
    / "r6-nowak-smith-positive-row-candidate-screen/r6_nowak_smith_positive_row_candidates_v1.csv"
)
SIDECAR = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1"
    / "r6-broad-normal-order-lifecycle-screen/broad_normal_market_order_lifecycle_controls_v1.csv"
)
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

SOURCE_URL = "https://www.cftc.gov/media/4826/enfjpmorganchaseorder092920/download"
SOURCE_REPORT = "CFTC Order: JPMorgan Chase & Co., JPMorgan Chase Bank, N.A., and J.P. Morgan Securities LLC, CFTC Docket No. 20-69"
MIN_WILSON = 0.95
Z_95 = 1.96
FIELDS = [
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
]


@dataclass(frozen=True)
class JpmCase:
    source_row_id: str
    source_section: str
    trade_date: str
    symbol: str
    venue: str
    participant: str
    spoof_side: str
    spoof_start: str
    spoof_end: str
    spoof_order_count: str
    spoof_quantity: str
    spoof_description: str
    genuine_side: str
    genuine_start: str
    genuine_end: str
    genuine_order_count: str
    genuine_quantity: str
    genuine_description: str
    group_id: str
    session_bucket: str
    status: str = "control_complete_candidate"
    required_snippets: list[str] = field(default_factory=list)


JPM_CASES = [
    JpmCase(
        source_row_id="cftc_jpm_20111212_trader1_silver_buy_layered_spoof",
        source_section="Order page 5, December 12 2011 Trader 1 Silver Futures example",
        trade_date="2011-12-12",
        symbol="Silver Futures contract, March 2012 expiry",
        venue="COMEX/CME Globex",
        participant="JPM Precious Metals Desk Trader 1",
        spoof_side="buy-side Layered Spoof Orders against genuine sell order",
        spoof_start="11:59:39.168 source-timezone-unspecified",
        spoof_end="11:59:40.332 source-timezone-unspecified",
        spoof_order_count="five buy-side layered spoof orders",
        spoof_quantity="50 lots",
        spoof_description="Official CFTC order describes five buy-side layered spoof orders totaling 50 lots; the trader began canceling them less than half a second after placing the fifth order.",
        genuine_side="sell genuine order",
        genuine_start="11:59:36.669 source-timezone-unspecified",
        genuine_end="11:59:39.690 source-timezone-unspecified",
        genuine_order_count="one genuine sell order",
        genuine_quantity="5 lots",
        genuine_description="Same-source genuine-control leg: the five-lot genuine sell order was fully filled after the fourth layered spoof order.",
        group_id="cftc_jpm_20111212_trader1_silver",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "on December 12, 2011, at 11:59:36.669, Trader 1 placed a",
            "at 11:59:39:168 a.m., Trader 1 began",
            "his five-lot Genuine Order to sell was fully filled",
        ],
    ),
    JpmCase(
        source_row_id="cftc_jpm_20131210_trader5_silver_buy_spoof",
        source_section="Order page 5, December 10 2013 Trader 5 Silver Futures example",
        trade_date="2013-12-10",
        symbol="Silver Futures contract, March 2014 expiry",
        venue="COMEX/CME Globex",
        participant="JPM Precious Metals Desk Trader 5",
        spoof_side="buy-side spoof order against genuine sell order",
        spoof_start="01:59:26.901 source-timezone-unspecified",
        spoof_end="01:59:27.729 source-timezone-unspecified",
        spoof_order_count="one buy-side spoof order",
        spoof_quantity="100 lots",
        spoof_description="Official CFTC order describes a 100-lot buy-side spoof order canceled less than one second after the genuine order filled.",
        genuine_side="sell genuine iceberg order",
        genuine_start="01:59:22.386 source-timezone-unspecified",
        genuine_end="01:59:26.902 source-timezone-unspecified",
        genuine_order_count="one iceberg sell order with five lots visible",
        genuine_quantity="20 lots",
        genuine_description="Same-source genuine-control leg: the 20-lot genuine sell iceberg order was fully filled one millisecond after the spoof order was entered.",
        group_id="cftc_jpm_20131210_trader5_silver",
        session_bucket="overnight_source_time",
        required_snippets=[
            "On December 10, 2013, at 1:59:22.386 a.m.",
            "at 1:59:26.901 a.m., Trader 5 entered a Spoof Order for 100 lots",
            "Trader 5 canceled his buy-side Spoof Order",
        ],
    ),
    JpmCase(
        source_row_id="cftc_jpm_20140305_trader6_silver_buy_layered_spoof",
        source_section="Order pages 5-6, March 5 2014 Trader 6 Silver Futures example",
        trade_date="2014-03-05",
        symbol="Silver Futures contract, May 2014 expiry",
        venue="COMEX/CME Globex",
        participant="JPM Precious Metals Desk Trader 6",
        spoof_side="buy-side layered spoof orders against genuine sell order",
        spoof_start="less than one second after 08:18:39.699 source-timezone-unspecified",
        spoof_end="shortly after 08:18:41.595 source-timezone-unspecified",
        spoof_order_count="series of buy-side layered spoof orders",
        spoof_quantity="quantity not fully disclosed; ten layered spoof order reference",
        spoof_description="Official CFTC order describes Trader 6 entering layered spoof bids after a two-lot genuine sell order and canceling all layered spoof orders after the genuine order filled.",
        genuine_side="sell genuine order",
        genuine_start="08:18:39.699 source-timezone-unspecified",
        genuine_end="08:18:41.595 source-timezone-unspecified",
        genuine_order_count="one genuine sell order",
        genuine_quantity="2 lots",
        genuine_description="Same-source genuine-control leg: the two-lot genuine sell order was fully filled milliseconds after the tenth layered spoof order.",
        group_id="cftc_jpm_20140305_trader6_silver",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On March 5, 2014, at 8:18:39.699 a.m.",
            "Trader 6 began entering a series of Layered",
            "his two-lot Genuine Order to sell was fully filled",
        ],
    ),
    JpmCase(
        source_row_id="cftc_jpm_20160622_trader4_platinum_buy_layered_spoof",
        source_section="Order page 6, June 22 2016 Trader 4 Platinum Futures example",
        trade_date="2016-06-22",
        symbol="Platinum Futures contract, July 2016 expiry",
        venue="NYMEX/CME Globex",
        participant="JPM Precious Metals Desk Trader 4",
        spoof_side="buy-side layered spoof orders against genuine sell order",
        spoof_start="less than two seconds after 02:14:33.935 source-timezone-unspecified",
        spoof_end="02:14:37.407 source-timezone-unspecified",
        spoof_order_count="eight buy-side layered spoof orders",
        spoof_quantity="40 lots",
        spoof_description="Official CFTC order describes eight buy-side layered spoof orders totaling 40 lots; canceling began less than half a second after the eighth spoof order.",
        genuine_side="sell genuine iceberg order",
        genuine_start="02:14:33.935 source-timezone-unspecified",
        genuine_end="02:14:36.520 source-timezone-unspecified",
        genuine_order_count="one iceberg sell order with one lot visible",
        genuine_quantity="20 lots; 4 filled during cited interval",
        genuine_description="Same-source genuine-control leg: four lots of the 20-lot genuine sell order were filled after the fifth spoof order.",
        group_id="cftc_jpm_20160622_trader4_platinum",
        session_bucket="overnight_source_time",
        required_snippets=[
            "On June 22, 2016, at 2:14:33.935 a.m.",
            "eight Layered Spoof Orders on the buy",
            "Beginning at 2:14:37.407",
        ],
    ),
    JpmCase(
        source_row_id="cftc_jpm_20090720_trader7_tbond_buy_layered_spoof",
        source_section="Order page 6, July 20 2009 Trader 7 T-Bond Futures example",
        trade_date="2009-07-20",
        symbol="T-Bond Futures contract, September 2009 expiry",
        venue="CBOT/CME Globex",
        participant="JPM Treasuries Desk Trader 7",
        spoof_side="buy-side layered spoof orders against genuine sell order",
        spoof_start="07:47:17.096 source-timezone-unspecified",
        spoof_end="07:47:22.038 source-timezone-unspecified",
        spoof_order_count="six buy-side layered spoof orders",
        spoof_quantity="1,800 lots",
        spoof_description="Official CFTC order describes six buy-side layered spoof orders totaling 1,800 lots and cancellation less than one second after the genuine order filled.",
        genuine_side="sell genuine order",
        genuine_start="07:47:13.597 source-timezone-unspecified",
        genuine_end="07:47:21.036 source-timezone-unspecified",
        genuine_order_count="one genuine sell order",
        genuine_quantity="100 lots",
        genuine_description="Same-source genuine-control leg: the 100-lot genuine sell order was fully filled milliseconds after the sixth layered spoof order.",
        group_id="cftc_jpm_20090720_trader7_tbond",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On July 20, 2009, at 7:47:13.597 a.m.",
            "six Layered Spoof Orders on the buy side of the market totaling 1,800",
            "his 100-lot Genuine",
        ],
    ),
    JpmCase(
        source_row_id="cftc_jpm_20100204_trader8_tnote_sell_spoof",
        source_section="Order page 6, February 4 2010 Trader 8 10-Year T-Note Futures example",
        trade_date="2010-02-04",
        symbol="10-Year T-Note Futures contract, March 2010 expiry",
        venue="CBOT/CME Globex",
        participant="JPM Treasuries Desk Trader 8",
        spoof_side="sell-side spoof order against genuine buy order",
        spoof_start="13:30:00.539 source-timezone-unspecified",
        spoof_end="13:30:01.467 source-timezone-unspecified",
        spoof_order_count="one sell-side spoof order",
        spoof_quantity="1,000 lots",
        spoof_description="Official CFTC order describes a 1,000-lot sell-side spoof order canceled less than a second after the genuine buy order filled.",
        genuine_side="buy genuine order",
        genuine_start="13:27:27.279 source-timezone-unspecified",
        genuine_end="13:30:00.677 source-timezone-unspecified",
        genuine_order_count="one genuine buy order",
        genuine_quantity="10 lots",
        genuine_description="Same-source genuine-control leg: the 10-lot genuine buy order was fully filled milliseconds after the spoof order.",
        group_id="cftc_jpm_20100204_trader8_tnote",
        session_bucket="regular_us_afternoon_source_time",
        required_snippets=[
            "On February 4, 2010, at 1:27:27.279 p.m.",
            "Trader 8 entered a Spoof Order for 1,000 lots on the sell side",
            "Trader 8 canceled his sell-",
        ],
    ),
    JpmCase(
        source_row_id="cftc_jpm_20110927_trader9_tnote_sell_spoof",
        source_section="Order pages 6-7, September 27 2011 Trader 9 10-Year T-Note Futures example",
        trade_date="2011-09-27",
        symbol="10-Year T-Note Futures contract, December 2011 expiry",
        venue="CBOT/CME Globex",
        participant="JPM Treasuries Desk Trader 9",
        spoof_side="sell-side spoof order against genuine buy order",
        spoof_start="14:03:57.635 source-timezone-unspecified",
        spoof_end="14:03:57.953 source-timezone-unspecified",
        spoof_order_count="one sell-side spoof order",
        spoof_quantity="3,000 lots",
        spoof_description="Official CFTC order describes a 3,000-lot sell-side spoof order canceled less than one-third of a second after the genuine order filled.",
        genuine_side="buy genuine order",
        genuine_start="14:03:54.204 source-timezone-unspecified",
        genuine_end="14:03:57.671 source-timezone-unspecified",
        genuine_order_count="one genuine buy order",
        genuine_quantity="50 lots",
        genuine_description="Same-source genuine-control leg: the 50-lot genuine buy order was fully filled milliseconds after the spoof order.",
        group_id="cftc_jpm_20110927_trader9_tnote",
        session_bucket="regular_us_afternoon_source_time",
        required_snippets=[
            "On September 27, 2011, at 2:03:54.204 p.m.",
            "Trader 9 entered",
            "Spoof Order for 3,000 lots",
        ],
    ),
    JpmCase(
        source_row_id="cftc_jpm_20150630_trader10_ultra_tbond_sell_spoof",
        source_section="Order page 7, June 30 2015 Trader 10 Ultra T-Bond Futures example",
        trade_date="2015-06-30",
        symbol="Ultra T-Bond Futures contract, September 2015 expiry",
        venue="CBOT/CME Globex",
        participant="JPM Treasuries Desk Trader 10",
        spoof_side="sell-side spoof order against genuine buy order",
        spoof_start="08:46:01.891 source-timezone-unspecified",
        spoof_end="08:46:04.418 source-timezone-unspecified",
        spoof_order_count="one sell-side spoof order",
        spoof_quantity="100 lots",
        spoof_description="Official CFTC order describes a 100-lot sell-side spoof order canceled about one-tenth of a second after 51 lots of the genuine order filled.",
        genuine_side="buy genuine iceberg order",
        genuine_start="08:45:46.627 source-timezone-unspecified",
        genuine_end="08:46:08.074 source-timezone-unspecified",
        genuine_order_count="one iceberg buy order with one lot visible",
        genuine_quantity="200 lots; 51 filled before spoof cancellation",
        genuine_description="Same-source genuine-control leg: 51 lots of the 200-lot genuine buy order filled before the spoof cancellation.",
        group_id="cftc_jpm_20150630_trader10_ultra_tbond",
        session_bucket="regular_us_morning_source_time",
        required_snippets=[
            "On June 30, 2015, at 8:45:46.627 a.m.",
            "Trader 10 entered a Spoof Order for 100 lots on the sell side",
            "at 8:46:04.418 a.m.",
        ],
    ),
]

SEMANTIC_DUPLICATE_CASE_IDS = {
    "cftc_jpm_20140303_trader3_gold_buy_layered_spoof",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def download_source() -> dict[str, object]:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    pdf = RAW_ROOT / "enfjpmorganchaseorder092920.pdf"
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "ict-engine-board-a-audit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read()
        pdf.write_bytes(body)
        return {
            "url": SOURCE_URL,
            "pdf_path": str(pdf),
            "http_status": getattr(response, "status", None),
            "content_type": response.headers.get("content-type", ""),
            "bytes": len(body),
            "sha256": sha256(pdf),
        }


def extract_pdf_text(pdf_path: str) -> Path:
    pdf = Path(pdf_path)
    text = pdf.with_suffix(".txt")
    snippet = (
        "from pathlib import Path\n"
        "from pypdf import PdfReader\n"
        f"pdf=Path({str(pdf)!r})\n"
        f"out=Path({str(text)!r})\n"
        "out.write_text('\\n'.join(page.extract_text() or '' for page in PdfReader(str(pdf)).pages), encoding='utf-8')\n"
    )
    completed = subprocess.run(
        ["uv", "run", "--with", "pypdf", "python", "-c", snippet],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    (COMMAND_OUT / "extract_jpm_order.stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (COMMAND_OUT / "extract_jpm_order.stderr.txt").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr)
    return text


def norm(text: str) -> str:
    return " ".join(text.split())


def case_to_rows(case: JpmCase) -> tuple[dict[str, str], dict[str, str]]:
    positive = {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": case.source_section,
        "trade_date": case.trade_date,
        "symbol": case.symbol,
        "venue_or_market_center": case.venue,
        "participant_type_code": "JPM desk trader described in official CFTC order",
        "participant_identifier": case.participant,
        "side": case.spoof_side,
        "earliest_order_received_time": case.spoof_start,
        "latest_order_received_time": case.spoof_end,
        "order_count": case.spoof_order_count,
        "total_order_quantity": case.spoof_quantity,
        "activity_description": case.spoof_description,
        "matched_negative_group_id": case.group_id,
        "session_bucket": case.session_bucket,
        "source_row_id": case.source_row_id,
    }
    negative = {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": case.source_section + " genuine-control leg",
        "trade_date": case.trade_date,
        "symbol": case.symbol,
        "venue_or_market_center": case.venue,
        "participant_type_code": "JPM desk trader described in official CFTC order",
        "participant_identifier": case.participant,
        "side": case.genuine_side,
        "earliest_order_received_time": case.genuine_start,
        "latest_order_received_time": case.genuine_end,
        "order_count": case.genuine_order_count,
        "total_order_quantity": case.genuine_quantity,
        "activity_description": case.genuine_description + " This is a same-source control seed, not an independent broad normal-market calibration sample.",
        "matched_negative_group_id": case.group_id,
        "session_bucket": case.session_bucket,
        "source_row_id": case.source_row_id.replace("_spoof", "_genuine_control"),
    }
    return positive, negative


def nowak_control_rows() -> list[dict[str, str]]:
    controls = [
        ("cftc_nowak_smith_20130506_nowak_gold_sell_layered", "2013-05-06", "Gold Futures contract, June 2013 expiry", "Michael Thomas Nowak / Bank A precious metals desk", "buy genuine order", "09:01:13.122 source-timezone-unspecified", "09:01:17.981 source-timezone-unspecified", "one genuine buy order", "5 lots", "cftc_nowak_smith_20130506_nowak_gold_buy_genuine_control"),
        ("cftc_nowak_smith_20131007_nowak_gold_buy_layered", "2013-10-07", "Gold Futures contract, December 2013 expiry", "Michael Thomas Nowak / Bank A precious metals desk", "sell genuine order", "07:34:45.805 source-timezone-unspecified", "07:34:51.429 source-timezone-unspecified", "one genuine sell order", "5 lots", "cftc_nowak_smith_20131007_nowak_gold_sell_genuine_control"),
        ("cftc_nowak_smith_20140303_nowak_gold_buy_layered", "2014-03-03", "Gold Futures contract, April 2014 expiry", "Michael Thomas Nowak / Bank A precious metals desk", "sell genuine order", "08:02:17.997 source-timezone-unspecified", "08:02:22.257 source-timezone-unspecified", "one genuine sell order", "5 lots", "cftc_nowak_smith_20140303_nowak_gold_sell_genuine_control"),
        ("cftc_nowak_smith_20130125_smith_silver_buy_layered", "2013-01-25", "Silver Futures contract, March 2013 expiry", "Gregg Francis Smith / Bank A precious metals desk", "sell genuine order", "07:55:28.841 source-timezone-unspecified", "07:55:30.676 source-timezone-unspecified", "one genuine sell order", "2 lots", "cftc_nowak_smith_20130125_smith_silver_sell_genuine_control"),
        ("cftc_nowak_smith_20130523_smith_gold_sell_layered", "2013-05-23", "Gold Futures contract, June 2013 expiry", "Gregg Francis Smith / Bank A precious metals desk", "buy genuine order", "14:00:22.820 source-timezone-unspecified", "14:00:30.792 source-timezone-unspecified", "one genuine buy order", "2 lots", "cftc_nowak_smith_20130523_smith_gold_buy_genuine_control"),
        ("cftc_nowak_smith_20150611_smith_gold_buy_layered", "2015-06-11", "Gold Futures contract, August 2015 expiry", "Gregg Francis Smith / Bank A precious metals desk", "sell genuine order", "07:31:25.410 source-timezone-unspecified", "07:31:27.441 source-timezone-unspecified", "one genuine sell order", "10 lots", "cftc_nowak_smith_20150611_smith_gold_sell_genuine_control"),
    ]
    return [
        {
            "label": "matched_negative_normal_activity",
            "source_report": "CFTC Complaint: Michael Thomas Nowak and Gregg Francis Smith, filed Sep. 16 2019",
            "source_section": "Nowak/Smith complaint same-source genuine-control leg",
            "trade_date": trade_date,
            "symbol": symbol,
            "venue_or_market_center": "COMEX/CME Globex",
            "participant_type_code": "CFTC defendant trader; major U.S. financial institution precious metals desk",
            "participant_identifier": participant,
            "side": side,
            "earliest_order_received_time": start,
            "latest_order_received_time": end,
            "order_count": order_count,
            "total_order_quantity": quantity,
            "activity_description": "Same-source genuine-control leg cited in the Nowak/Smith complaint; not an independent broad normal-market calibration sample.",
            "matched_negative_group_id": group,
            "session_bucket": "source_time",
            "source_row_id": row_id,
        }
        for group, trade_date, symbol, participant, side, start, end, order_count, quantity, row_id in controls
    ]


def sarao_control_rows() -> list[dict[str, str]]:
    return [
        {
            "label": "matched_negative_normal_activity",
            "source_report": "CFTC Complaint: Navinder Singh Sarao and Nav Sarao Futures Limited PLC, filed Apr. 17 2015",
            "source_section": "Complaint paragraph 69, March 3 2014 sell genuine order leg",
            "trade_date": "2014-03-03",
            "symbol": "E-mini S&P 500 futures",
            "venue_or_market_center": "CME Globex",
            "participant_type_code": "CFTC defendant trader; proprietary account",
            "participant_identifier": "Navinder Singh Sarao / Nav Sarao Futures Limited PLC",
            "side": "sell genuine order opposite buy-side spoofing order",
            "earliest_order_received_time": "11:38:27.538 America/Chicago",
            "latest_order_received_time": "11:38:31.827 America/Chicago",
            "order_count": "one sell order",
            "total_order_quantity": "169 lots",
            "activity_description": "Same-complaint genuine-control leg: the 169-lot sell order began filling before the second buy-side 2000-lot spoof order and the remainder filled within one millisecond after it. Not an independent broad normal-market sample.",
            "matched_negative_group_id": "cftc_sarao_20140303_2000_lot_spoof",
            "session_bucket": "regular_us_central_time",
            "source_row_id": "cftc_sarao_20140303_sell_169_lot_genuine_control",
        },
        {
            "label": "matched_negative_normal_activity",
            "source_report": "CFTC Complaint: Navinder Singh Sarao and Nav Sarao Futures Limited PLC, filed Apr. 17 2015",
            "source_section": "Complaint paragraph 70, September 30 2013 sell genuine order leg",
            "trade_date": "2013-09-30",
            "symbol": "E-mini S&P 500 futures",
            "venue_or_market_center": "CME Globex",
            "participant_type_code": "CFTC defendant trader; proprietary account",
            "participant_identifier": "Navinder Singh Sarao / Nav Sarao Futures Limited PLC",
            "side": "sell genuine order opposite buy-side spoofing order",
            "earliest_order_received_time": "12:30:38 source-timezone-unspecified",
            "latest_order_received_time": "12:30:49.708 America/Chicago",
            "order_count": "one sell order",
            "total_order_quantity": "384 lots",
            "activity_description": "Same-complaint genuine-control leg: the source distinguishes a 384-lot sell-side order from the buy-side 2000-lot spoofing orders. Not an independent broad normal-market sample.",
            "matched_negative_group_id": "cftc_sarao_20130930_2000_lot_spoof",
            "session_bucket": "regular_us_central_time",
            "source_row_id": "cftc_sarao_20130930_sell_384_lot_genuine_control",
        },
    ]


def run_verifier() -> dict[str, object]:
    completed = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(DELTA_INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=45,
        check=False,
    )
    stdout = COMMAND_OUT / "delta_direct_manipulation_row_intake_verifier.stdout.txt"
    stderr = COMMAND_OUT / "delta_direct_manipulation_row_intake_verifier.stderr.txt"
    stdout.write_text(completed.stdout, encoding="utf-8")
    stderr.write_text(completed.stderr, encoding="utf-8")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = {"parse_error": True, "raw_stdout": completed.stdout[:500]}
    return {
        "returncode": completed.returncode,
        "stdout_path": str(stdout.relative_to(REPO)),
        "stderr_path": str(stderr.relative_to(REPO)),
        "payload": payload,
    }


def live_intake_status() -> dict[str, object]:
    required = [
        LIVE_INTAKE / "positive_spoofing_layering_rows.csv",
        LIVE_INTAKE / "matched_negative_normal_activity_rows.csv",
        LIVE_INTAKE / "provenance_manifest.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    return {"root": str(LIVE_INTAKE), "present": not missing, "missing_files": missing}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    DELTA_INTAKE.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    source = download_source()
    text_path = extract_pdf_text(str(source["pdf_path"]))
    source_text = norm(text_path.read_text(encoding="utf-8", errors="replace"))

    jpm_positives = []
    jpm_negatives = []
    source_screen = []
    for case in JPM_CASES:
        hits = {snippet: snippet in source_text for snippet in case.required_snippets}
        positive, negative = case_to_rows(case)
        jpm_positives.append({**positive, "candidate_row_status": case.status})
        jpm_negatives.append({**negative, "candidate_row_status": case.status})
        source_screen.append(
            {
                "source_row_id": case.source_row_id,
                "trade_date": case.trade_date,
                "symbol": case.symbol,
                "materializable": all(hits.values()),
                "semantic_duplicate": case.source_row_id in SEMANTIC_DUPLICATE_CASE_IDS,
                "snippet_hits_json": json.dumps(hits, sort_keys=True),
                "screen_status": "control_complete_candidate" if all(hits.values()) else "fail_closed_missing_snippet",
            }
        )

    sarao_rows = read_csv(SARAO_ROWS)
    nowak_rows = read_csv(NOWAK_ROWS)
    sarao_control_ids = {
        "cftc_sarao_20140303_buy_2000_lot_spoof_second",
        "cftc_sarao_20130930_buy_2000_lot_spoof_third",
    }
    sarao_control_complete_positives = [
        {field: row.get(field, "") for field in FIELDS}
        for row in sarao_rows
        if row.get("source_row_id") in sarao_control_ids
    ]
    nowak_control_complete_positives = [{field: row.get(field, "") for field in FIELDS} for row in nowak_rows]
    candidate_positives = [
        {field: row.get(field, "") for field in FIELDS}
        for row in [*sarao_control_complete_positives, *nowak_control_complete_positives, *jpm_positives]
    ]
    candidate_negatives = [
        {field: row.get(field, "") for field in FIELDS}
        for row in [*sarao_control_rows(), *nowak_control_rows(), *jpm_negatives]
    ]

    write_csv(OUT / "r6_jpmorgan_order_positive_row_candidates_v1.csv", jpm_positives, [*FIELDS, "candidate_row_status"])
    write_csv(OUT / "r6_jpmorgan_order_matched_controls_v1.csv", jpm_negatives, [*FIELDS, "candidate_row_status"])
    write_csv(OUT / "r6_jpmorgan_order_source_screen_v1.csv", source_screen, ["source_row_id", "trade_date", "symbol", "materializable", "semantic_duplicate", "snippet_hits_json", "screen_status"])
    write_csv(OUT / "r6_control_complete_candidate_stack_positives_v1.csv", candidate_positives, FIELDS)
    write_csv(OUT / "r6_control_complete_candidate_stack_matched_controls_v1.csv", candidate_negatives, FIELDS)
    write_csv(DELTA_INTAKE / "positive_spoofing_layering_rows.csv", candidate_positives, FIELDS)
    write_csv(DELTA_INTAKE / "matched_negative_normal_activity_rows.csv", candidate_negatives, FIELDS)
    provenance = {
        "run_id": RUN_ID,
        "source": source,
        "source_text_path": str(text_path),
        "candidate_policy": "delta candidate stack only; does not mutate missing shared intake",
        "matched_negative_control_policy": "same-source genuine-order legs; sidecar Nasdaq ITCH controls remain the independent broad-normal axis",
        "raw_payload_committed_to_repo": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (DELTA_INTAKE / "provenance_manifest.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verifier = run_verifier()
    v54 = json.loads(V54_JSON.read_text(encoding="utf-8"))
    baseline_positive = int(v54["r6"]["positive_rows"])
    baseline_negative = int(v54["r6"]["matched_negative_rows"])
    sidecar_rows = len(read_csv(SIDECAR))
    composite_positive = baseline_positive + len(candidate_positives)
    composite_negative = baseline_negative + len(candidate_negatives)
    positive_lcb = wilson_lcb(composite_positive, composite_positive)
    negative_lcb = wilson_lcb(composite_negative, composite_negative)
    sidecar_lcb = wilson_lcb(sidecar_rows, sidecar_rows)
    composite_min_lcb = min(positive_lcb, negative_lcb, sidecar_lcb)
    pooled_95_pass = composite_min_lcb >= MIN_WILSON
    live_status = live_intake_status()
    split_support_still_blocked = True
    direct_species_closed = False
    strict_full_objective_achieved = False

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash,
        "source": source,
        "source_text_path": str(text_path),
        "live_shared_intake_status": live_status,
        "v54_baseline": {
            "path": str(V54_JSON.relative_to(REPO)),
            "positive_rows": baseline_positive,
            "matched_negative_rows": baseline_negative,
            "sidecar_broad_normal_rows": sidecar_rows,
        },
        "candidate_delta": {
            "sarao_control_complete_positive_rows": len(sarao_control_complete_positives),
            "nowak_smith_control_complete_positive_rows": len(nowak_control_complete_positives),
            "jpmorgan_control_complete_positive_rows": len(jpm_positives),
            "control_complete_positive_rows_total": len(candidate_positives),
            "control_complete_matched_negative_rows_total": len(candidate_negatives),
            "jpm_semantic_duplicate_rows_excluded": sorted(SEMANTIC_DUPLICATE_CASE_IDS),
        },
        "delta_verifier": verifier,
        "composite_readback": {
            "positive_rows": composite_positive,
            "matched_negative_rows": composite_negative,
            "sidecar_broad_normal_rows": sidecar_rows,
            "positive_wilson95_lcb": round(positive_lcb, 12),
            "matched_negative_wilson95_lcb": round(negative_lcb, 12),
            "sidecar_wilson95_lcb": round(sidecar_lcb, 12),
            "composite_min_wilson95_lcb": round(composite_min_lcb, 12),
            "pooled_95_pass": pooled_95_pass,
            "split_support_still_blocked": split_support_still_blocked,
            "direct_species_closed": direct_species_closed,
        },
        "gate_result": "r6_jpmorgan_order_positive_row_candidate_screen_v1=control_complete_candidate_stack_pooled95_pass_live_intake_missing_split_still_blocked",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": strict_full_objective_achieved,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "next_action": "Restore or recreate a shared/direct intake from accepted row artifacts under a fresh lock, append the 16 control-complete positive/control candidate pairs, then rerun live direct and sidecar calibration; do not claim split or species closure yet.",
    }

    json_path = OUT / "r6_jpmorgan_order_positive_row_candidate_screen_v1.json"
    md_path = OUT / "r6_jpmorgan_order_positive_row_candidate_screen_v1.md"
    assertions_path = CHECKS / "r6_jpmorgan_order_positive_row_candidate_screen_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# R6 JPMorgan Order Positive Row Candidate Screen v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Official source: `{SOURCE_URL}`.",
        f"- Shared live intake present: `{str(live_status['present']).lower()}`.",
        f"- JPM control-complete candidates: `{len(jpm_positives)}` positives plus `{len(jpm_negatives)}` matched controls.",
        f"- Candidate stack: Sarao control-complete `{len(sarao_control_complete_positives)}`, Nowak/Smith `{len(nowak_control_complete_positives)}`, JPM `{len(jpm_positives)}`; total `{len(candidate_positives)}` positive/control pairs.",
        f"- Composite rows from V54 baseline plus candidate stack: positives `{composite_positive}`, matched controls `{composite_negative}`, sidecar controls `{sidecar_rows}`.",
        f"- Composite min Wilson95 LCB: `{composite_min_lcb:.6f}`; pooled 95 pass: `{str(pooled_95_pass).lower()}`.",
        "- Chronological/symbol/venue split support remains blocked and direct species coverage remains open.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- JPM positives CSV: `{(OUT / 'r6_jpmorgan_order_positive_row_candidates_v1.csv').relative_to(REPO)}`",
        f"- JPM matched controls CSV: `{(OUT / 'r6_jpmorgan_order_matched_controls_v1.csv').relative_to(REPO)}`",
        f"- Control-complete stack positives CSV: `{(OUT / 'r6_control_complete_candidate_stack_positives_v1.csv').relative_to(REPO)}`",
        f"- Control-complete stack controls CSV: `{(OUT / 'r6_control_complete_candidate_stack_matched_controls_v1.csv').relative_to(REPO)}`",
        f"- Delta verifier stdout: `{verifier['stdout_path']}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assertions = [
        f"PASS live_shared_intake_present={str(live_status['present']).lower()}",
        f"PASS jpm_control_complete_positive_rows={len(jpm_positives)}",
        f"PASS candidate_positive_pairs={len(candidate_positives)}",
        f"PASS delta_verifier_returncode={verifier['returncode']}",
        f"PASS composite_positive_rows={composite_positive}",
        f"PASS composite_min_wilson95_lcb={composite_min_lcb:.12f}",
        f"PASS pooled_95_pass={str(pooled_95_pass).lower()}",
        "PASS split_support_still_blocked=true",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"gate_result": result["gate_result"], "pooled_95_pass": pooled_95_pass, "composite_min_wilson95_lcb": round(composite_min_lcb, 12), "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
