#!/usr/bin/env python3
"""Append official CFTC Zhao/Skudder exact spoofing examples to R6 intake."""

from __future__ import annotations

import csv
import fcntl
import hashlib
import json
import math
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


RUN_ID = "20260511T213113-codex-r6-zhao-skudder-cftc-row-uplift-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-zhao-skudder-cftc-row-uplift"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"
LOCK = INTAKE / ".r6_zhao_skudder_cftc_row_uplift_v1.lock"
TMP_ROOT = Path("/tmp/ict-engine-r6-zhao-skudder-cftc-row-uplift-v1")
RAW = TMP_ROOT / "raw"
TEXT = TMP_ROOT / "text"
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
GS = Path("/opt/homebrew/bin/gs")
# The official PDFs were fetched into TMP_ROOT during the source preflight for
# this run before the artifact script was executed.
EXTERNAL_REQUESTS_SENT_IN_SOURCE_PREFLIGHT = True
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

SOURCES = {
    "zhao": {
        "url": "https://www.cftc.gov/idc/groups/public/@lrenforcementactions/documents/legalpleading/enfjiongshengorder012918.pdf",
        "pdf": RAW / "zhao.pdf",
        "text": TEXT / "zhao.txt",
        "report": "CFTC Complaint: CFTC v. Jiongsheng Zhao, No. 1:18-cv-00620",
        "checks": [
            "Event Example 1: April 15, 2013",
            "Event Example 2: March 5, 2014",
            "Event Example 3: March 21, 2016",
            "to sell one",
            "to buy 82 contracts",
        ],
    },
    "skudder": {
        "url": "https://www.cftc.gov/media/7166/enfdavidskuddercomplaint041422/download",
        "pdf": RAW / "skudder.pdf",
        "text": TEXT / "skudder.txt",
        "report": "CFTC Complaint: CFTC v. David Skudder et al., No. 1:22-cv-01925",
        "checks": [
            "Spoof Event Example 1 (Futures Scheme): August 31, 2017",
            "Spoof Event Example 2 (Futures Scheme): December 5, 2017",
            "Spoof Event Example 3 (Options Scheme): July 1, 2016",
            "Spoof Event Example 4 (Options Scheme): July 11, 2016",
            "options on soybean futures",
        ],
    },
}

PARTICIPANT = "CFTC respondent trader; federal complaint"
ZHAO_REPORT = SOURCES["zhao"]["report"]
SKUDDER_REPORT = SOURCES["skudder"]["report"]

POSITIVE_ADDITIONS = [
    {
        "label": "positive_spoofing_layering",
        "source_report": ZHAO_REPORT,
        "source_section": "Paragraph 36, Event Example 1: April 15 2013",
        "trade_date": "2013-04-15",
        "symbol": "E-mini S&P 500 futures",
        "venue_or_market_center": "CME Globex",
        "participant_type_code": PARTICIPANT,
        "participant_identifier": "Jiongsheng Zhao",
        "side": "buy spoof orders opposite sell genuine order",
        "earliest_order_received_time": "01:11:25.537 America/Chicago",
        "latest_order_received_time": "01:11:34.161 America/Chicago",
        "order_count": "two buy spoof orders",
        "total_order_quantity": "322 contracts",
        "activity_description": "CFTC complaint describes Zhao placing 151-contract and 171-contract buy spoof orders at the best-bid level after a one-contract sell genuine order; the genuine order executed after the second spoof order, then the second spoof order was canceled within 798 milliseconds.",
        "matched_negative_group_id": "cftc_zhao_20130415_es_example",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_zhao_20130415_es_buy_spoof_orders",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": ZHAO_REPORT,
        "source_section": "Paragraph 37, Event Example 2: March 5 2014",
        "trade_date": "2014-03-05",
        "symbol": "E-mini S&P 500 futures",
        "venue_or_market_center": "CME Globex",
        "participant_type_code": PARTICIPANT,
        "participant_identifier": "Jiongsheng Zhao",
        "side": "sell spoof order opposite buy genuine order",
        "earliest_order_received_time": "22:44:15.720 America/Chicago",
        "latest_order_received_time": "22:44:16.394 America/Chicago",
        "order_count": "one sell spoof order",
        "total_order_quantity": "201 contracts",
        "activity_description": "CFTC complaint describes Zhao placing a 201-contract sell spoof order at the best-ask level three seconds after a one-contract buy genuine order; the spoof order was canceled after 674 milliseconds and the genuine order later canceled unfilled.",
        "matched_negative_group_id": "cftc_zhao_20140305_es_example",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_zhao_20140305_es_sell_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": ZHAO_REPORT,
        "source_section": "Paragraph 38, Event Example 3: March 21 2016",
        "trade_date": "2016-03-21",
        "symbol": "E-mini S&P 500 futures",
        "venue_or_market_center": "CME Globex",
        "participant_type_code": PARTICIPANT,
        "participant_identifier": "Jiongsheng Zhao",
        "side": "buy spoof order opposite sell genuine order",
        "earliest_order_received_time": "07:31:33.645 America/Chicago",
        "latest_order_received_time": "07:31:34.389 America/Chicago",
        "order_count": "one buy spoof order",
        "total_order_quantity": "82 contracts",
        "activity_description": "CFTC complaint describes Zhao placing an 82-contract buy spoof order at the best-bid level after an 11-contract sell genuine order; the genuine order executed almost immediately, and Zhao canceled the spoof order 744 milliseconds after placing it.",
        "matched_negative_group_id": "cftc_zhao_20160321_es_example",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_zhao_20160321_es_buy_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SKUDDER_REPORT,
        "source_section": "Paragraph 55, Spoof Event Example 1: August 31 2017",
        "trade_date": "2017-08-31",
        "symbol": "CBOT soybean futures",
        "venue_or_market_center": "CBOT/CME Globex",
        "participant_type_code": PARTICIPANT,
        "participant_identifier": "David Skudder / Global Ag / Nesvick",
        "side": "buy spoof order opposite sell genuine iceberg order",
        "earliest_order_received_time": "11:15:21.655 America/Chicago",
        "latest_order_received_time": "11:15:46.217 America/Chicago",
        "order_count": "one buy spoof order",
        "total_order_quantity": "100 soybean futures contracts",
        "activity_description": "CFTC complaint describes a 100-contract fully visible buy spoof order at 943.5 cents per bushel after a 30-contract sell iceberg genuine order at 945; the genuine order filled and the spoof order was canceled.",
        "matched_negative_group_id": "cftc_skudder_20170831_soybean_futures_example",
        "session_bucket": "daytime_central_time",
        "source_row_id": "cftc_skudder_20170831_soybean_buy_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SKUDDER_REPORT,
        "source_section": "Paragraph 56, Spoof Event Example 2: December 5 2017",
        "trade_date": "2017-12-05",
        "symbol": "CBOT soybean futures",
        "venue_or_market_center": "CBOT/CME Globex",
        "participant_type_code": PARTICIPANT,
        "participant_identifier": "David Skudder / Global Ag / Nesvick",
        "side": "buy spoof order opposite sell genuine iceberg order",
        "earliest_order_received_time": "08:48:37.041 America/Chicago",
        "latest_order_received_time": "08:49:01.603 America/Chicago",
        "order_count": "one buy spoof order",
        "total_order_quantity": "500 soybean futures contracts",
        "activity_description": "CFTC complaint describes a 500-contract fully visible buy spoof order at 1010.25 cents per bushel near Skudder's genuine sell iceberg orders; the 1012.5-cent genuine order began trading nine seconds later and fully filled before the spoof order was canceled.",
        "matched_negative_group_id": "cftc_skudder_20171205_soybean_futures_example",
        "session_bucket": "daytime_central_time",
        "source_row_id": "cftc_skudder_20171205_soybean_buy_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SKUDDER_REPORT,
        "source_section": "Paragraph 57, Spoof Event Example 3: July 1 2016",
        "trade_date": "2016-07-01",
        "symbol": "CBOT soybean futures",
        "venue_or_market_center": "CBOT/CME Globex",
        "participant_type_code": PARTICIPANT,
        "participant_identifier": "David Skudder / Global Ag / Nesvick",
        "side": "sell soybean futures spoof order benefiting buy soybean call options",
        "earliest_order_received_time": "11:29:14.696 America/Chicago",
        "latest_order_received_time": "11:29:17.309 America/Chicago",
        "order_count": "one sell futures spoof order",
        "total_order_quantity": "100 soybean futures contracts",
        "activity_description": "CFTC complaint describes Skudder placing a 100-contract sell soybean futures spoof order at 1167.25 cents per bushel while two ten-contract soybean call option buy genuine orders were resting; the options filled one millisecond later and the futures spoof order was canceled less than three seconds later.",
        "matched_negative_group_id": "cftc_skudder_20160701_soybean_options_cross_market_example",
        "session_bucket": "daytime_central_time",
        "source_row_id": "cftc_skudder_20160701_soybean_futures_sell_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SKUDDER_REPORT,
        "source_section": "Paragraph 58, Spoof Event Example 4: July 11 2016",
        "trade_date": "2016-07-11",
        "symbol": "CBOT soybean futures",
        "venue_or_market_center": "CBOT/CME Globex",
        "participant_type_code": PARTICIPANT,
        "participant_identifier": "David Skudder / Global Ag / Nesvick",
        "side": "sell soybean futures spoof order benefiting buy soybean call options",
        "earliest_order_received_time": "10:35:58.647 America/Chicago",
        "latest_order_received_time": "10:36:09.541 America/Chicago",
        "order_count": "one sell futures spoof order modified twice then canceled",
        "total_order_quantity": "100 soybean futures contracts",
        "activity_description": "CFTC complaint describes Skudder placing a 100-contract sell soybean futures spoof order while a two-contract soybean call option buy genuine order was resting; after the option filled, he modified the spoof order away from the market twice and then canceled it.",
        "matched_negative_group_id": "cftc_skudder_20160711_soybean_options_cross_market_example",
        "session_bucket": "daytime_central_time",
        "source_row_id": "cftc_skudder_20160711_soybean_futures_sell_spoof_order",
    },
]

NEGATIVE_ADDITIONS = [
    {
        "label": "matched_negative_normal_activity",
        "source_report": ZHAO_REPORT,
        "source_section": "Paragraph 36, Event Example 1: April 15 2013",
        "trade_date": "2013-04-15",
        "symbol": "E-mini S&P 500 futures",
        "venue_or_market_center": "CME Globex",
        "participant_type_code": PARTICIPANT,
        "participant_identifier": "Jiongsheng Zhao",
        "side": "sell genuine order",
        "earliest_order_received_time": "01:11:16.287 America/Chicago",
        "latest_order_received_time": "01:11:33.366 America/Chicago",
        "order_count": "one genuine order",
        "total_order_quantity": "1 contract",
        "activity_description": "Matched same-complaint control seed: the source distinguishes a one-contract sell genuine order at the best-ask level from the buy spoof orders; the genuine order executed after the second spoof order.",
        "matched_negative_group_id": "cftc_zhao_20130415_es_example",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_zhao_20130415_es_sell_genuine_order_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": ZHAO_REPORT,
        "source_section": "Paragraph 37, Event Example 2: March 5 2014",
        "trade_date": "2014-03-05",
        "symbol": "E-mini S&P 500 futures",
        "venue_or_market_center": "CME Globex",
        "participant_type_code": PARTICIPANT,
        "participant_identifier": "Jiongsheng Zhao",
        "side": "buy genuine order",
        "earliest_order_received_time": "22:44:12.924 America/Chicago",
        "latest_order_received_time": "22:44:40.533 America/Chicago",
        "order_count": "one genuine order",
        "total_order_quantity": "1 contract",
        "activity_description": "Matched same-complaint control seed: the source distinguishes a one-contract buy genuine order from the sell spoof order; this genuine order did not fill and was canceled after resting longer.",
        "matched_negative_group_id": "cftc_zhao_20140305_es_example",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_zhao_20140305_es_buy_genuine_order_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": ZHAO_REPORT,
        "source_section": "Paragraph 38, Event Example 3: March 21 2016",
        "trade_date": "2016-03-21",
        "symbol": "E-mini S&P 500 futures",
        "venue_or_market_center": "CME Globex",
        "participant_type_code": PARTICIPANT,
        "participant_identifier": "Jiongsheng Zhao",
        "side": "sell genuine order",
        "earliest_order_received_time": "07:31:28.726 America/Chicago",
        "latest_order_received_time": "07:31:33.981 America/Chicago",
        "order_count": "one genuine order",
        "total_order_quantity": "11 contracts",
        "activity_description": "Matched same-complaint control seed: the source distinguishes an 11-contract sell genuine order from the buy spoof order; the genuine order executed through one trade of one and one trade of ten contracts.",
        "matched_negative_group_id": "cftc_zhao_20160321_es_example",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_zhao_20160321_es_sell_genuine_order_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SKUDDER_REPORT,
        "source_section": "Paragraph 55, Spoof Event Example 1: August 31 2017",
        "trade_date": "2017-08-31",
        "symbol": "CBOT soybean futures",
        "venue_or_market_center": "CBOT/CME Globex",
        "participant_type_code": PARTICIPANT,
        "participant_identifier": "David Skudder / Global Ag / Nesvick",
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "11:15:05.843 America/Chicago",
        "latest_order_received_time": "11:15:24.490 America/Chicago",
        "order_count": "one genuine iceberg order",
        "total_order_quantity": "30 soybean futures contracts",
        "activity_description": "Matched same-complaint control seed: the source distinguishes a 30-contract sell iceberg genuine order with one contract visible at 945 cents per bushel from the buy spoof order; it completely filled.",
        "matched_negative_group_id": "cftc_skudder_20170831_soybean_futures_example",
        "session_bucket": "daytime_central_time",
        "source_row_id": "cftc_skudder_20170831_soybean_sell_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SKUDDER_REPORT,
        "source_section": "Paragraph 56, Spoof Event Example 2: December 5 2017",
        "trade_date": "2017-12-05",
        "symbol": "CBOT soybean futures",
        "venue_or_market_center": "CBOT/CME Globex",
        "participant_type_code": PARTICIPANT,
        "participant_identifier": "David Skudder / Global Ag / Nesvick",
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "08:47:25.000 America/Chicago",
        "latest_order_received_time": "08:48:56.091 America/Chicago",
        "order_count": "one of three sell genuine iceberg orders",
        "total_order_quantity": "100 soybean futures contracts",
        "activity_description": "Matched same-complaint control seed: the source describes a 100-contract sell genuine iceberg order at 1012.5 cents per bushel, with visible quantity of one, that began trading at 08:48:45.769 and fully filled by 08:48:56.091.",
        "matched_negative_group_id": "cftc_skudder_20171205_soybean_futures_example",
        "session_bucket": "daytime_central_time",
        "source_row_id": "cftc_skudder_20171205_soybean_sell_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SKUDDER_REPORT,
        "source_section": "Paragraph 57, Spoof Event Example 3: July 1 2016",
        "trade_date": "2016-07-01",
        "symbol": "CBOT soybean call options",
        "venue_or_market_center": "CBOT/CME Globex",
        "participant_type_code": PARTICIPANT,
        "participant_identifier": "David Skudder / Global Ag / Nesvick",
        "side": "buy soybean call options genuine orders",
        "earliest_order_received_time": "before 11:29:14.696 America/Chicago",
        "latest_order_received_time": "11:29:14.697 America/Chicago",
        "order_count": "two genuine option buy orders",
        "total_order_quantity": "20 soybean call options contracts",
        "activity_description": "Matched cross-market same-complaint control seed: the source distinguishes two existing buy soybean call option genuine orders from the sell soybean futures spoof order; the options filled one millisecond after the futures spoof order was placed.",
        "matched_negative_group_id": "cftc_skudder_20160701_soybean_options_cross_market_example",
        "session_bucket": "daytime_central_time",
        "source_row_id": "cftc_skudder_20160701_soybean_call_options_buy_genuine_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SKUDDER_REPORT,
        "source_section": "Paragraph 58, Spoof Event Example 4: July 11 2016",
        "trade_date": "2016-07-11",
        "symbol": "CBOT soybean call options",
        "venue_or_market_center": "CBOT/CME Globex",
        "participant_type_code": PARTICIPANT,
        "participant_identifier": "David Skudder / Global Ag / Nesvick",
        "side": "buy soybean call options genuine order",
        "earliest_order_received_time": "before 10:35:58.647 America/Chicago",
        "latest_order_received_time": "10:36:00.579 America/Chicago",
        "order_count": "one genuine option buy order",
        "total_order_quantity": "2 soybean call options contracts",
        "activity_description": "Matched cross-market same-complaint control seed: the source distinguishes an existing two-contract buy soybean call option genuine order from the sell soybean futures spoof order; the option order filled after the spoof order was modified to the now-best ask.",
        "matched_negative_group_id": "cftc_skudder_20160711_soybean_options_cross_market_example",
        "session_bucket": "daytime_central_time",
        "source_row_id": "cftc_skudder_20160711_soybean_call_options_buy_genuine_control",
    },
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, path: Path) -> bool:
    if path.exists() and path.stat().st_size > 0:
        return False
    request = Request(url, headers={"User-Agent": "ict-engine-board-a-source-uplift/1.0"})
    with urlopen(request, timeout=60) as response:
        data = response.read()
    path.write_bytes(data)
    return True


def extract_text(pdf: Path, text: Path) -> bool:
    if text.exists() and text.stat().st_size > 0:
        return False
    if not GS.exists() and shutil.which("gs") is None:
        raise RuntimeError("ghostscript gs is required for PDF text extraction")
    gs_bin = str(GS if GS.exists() else shutil.which("gs"))
    result = subprocess.run(
        [
            gs_bin,
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=txtwrite",
            f"-sOutputFile={text}",
            str(pdf),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gs text extraction failed for {pdf}: {result.stderr}")
    return True


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


def append_unique(path: Path, additions: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows = read_csv(path)
    seen = {row["source_row_id"] for row in rows}
    new_rows = [row for row in additions if row["source_row_id"] not in seen]
    if new_rows:
        rows.extend(new_rows)
        write_csv(path, rows, FIELDS)
    return rows, new_rows


def wilson_all_success(n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    denom = 1.0 + z * z / n
    centre = 1.0 + z * z / (2 * n)
    margin = z * math.sqrt((z * z / (4 * n)) / n)
    return (centre - margin) / denom


def unique_count(rows: list[dict[str, str]], key: str) -> int:
    return len({row.get(key, "") for row in rows if row.get(key, "")})


def present_count(rows: list[dict[str, str]], additions: list[dict[str, str]]) -> int:
    present = {row["source_row_id"] for row in rows}
    return sum(1 for addition in additions if addition["source_row_id"] in present)


def run_verifier() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )


def source_material() -> dict[str, object]:
    RAW.mkdir(parents=True, exist_ok=True)
    TEXT.mkdir(parents=True, exist_ok=True)
    results = {}
    for key, source in SOURCES.items():
        pdf = source["pdf"]
        text_path = source["text"]
        fetched = download(source["url"], pdf)
        extracted = extract_text(pdf, text_path)
        text = text_path.read_text(encoding="utf-8", errors="replace")
        checks = {phrase: phrase in text for phrase in source["checks"]}
        results[key] = {
            "url": source["url"],
            "pdf_path": str(pdf),
            "pdf_sha256": sha256(pdf),
            "pdf_bytes": pdf.stat().st_size,
            "text_path": str(text_path),
            "text_sha256": sha256(text_path),
            "text_chars": len(text),
            "fetched_this_run": fetched,
            "extracted_this_run": extracted,
            "text_checks": checks,
            "all_text_checks_pass": all(checks.values()),
        }
    return results


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    INTAKE.mkdir(parents=True, exist_ok=True)
    if not POSITIVE.exists() or not NEGATIVE.exists() or not PROVENANCE.exists():
        raise SystemExit("missing direct manipulation intake files")

    board_hash_before = sha256(BOARD)
    pre_hashes = {p.name: sha256(p) for p in [POSITIVE, NEGATIVE, PROVENANCE]}
    source_results = source_material()
    external_requests_sent = EXTERNAL_REQUESTS_SENT_IN_SOURCE_PREFLIGHT or any(
        source["fetched_this_run"] for source in source_results.values()
    )

    with LOCK.open("w", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        positives_before = read_csv(POSITIVE)
        negatives_before = read_csv(NEGATIVE)
        positive_rows, positive_added = append_unique(POSITIVE, POSITIVE_ADDITIONS)
        negative_rows, negative_added = append_unique(NEGATIVE, NEGATIVE_ADDITIONS)
        provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        provenance["cftc_zhao_skudder_examples"] = {
            "run_id": RUN_ID,
            "zhao": source_results["zhao"],
            "skudder": source_results["skudder"],
            "positive_source_row_ids": [row["source_row_id"] for row in POSITIVE_ADDITIONS],
            "matched_negative_source_row_ids": [row["source_row_id"] for row in NEGATIVE_ADDITIONS],
            "control_boundary": "same-complaint genuine-order legs are schema/control seeds only, not broad normal-market calibration controls",
            "rows_materialized_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        provenance["r6_zhao_skudder_cftc_row_uplift_v1"] = {
            "run_id": RUN_ID,
            "positive_rows_added": len(positive_added),
            "matched_negative_rows_added": len(negative_added),
        }
        provenance["positive_rows_count"] = len(positive_rows)
        provenance["matched_negative_rows_count"] = len(negative_rows)
        provenance["updated_by"] = RUN_ID
        provenance["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        verifier = run_verifier()

    positive_rows_materialized = present_count(positive_rows, POSITIVE_ADDITIONS)
    negative_rows_materialized = present_count(negative_rows, NEGATIVE_ADDITIONS)
    (CMD_OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(verifier.stdout, encoding="utf-8")
    (CMD_OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(verifier.stderr, encoding="utf-8")
    try:
        verifier_json = json.loads(verifier.stdout)
    except json.JSONDecodeError:
        verifier_json = {"status": "parse_failed", "stdout": verifier.stdout, "stderr": verifier.stderr}

    positive_lcb = wilson_all_success(len(positive_rows))
    negative_lcb = wilson_all_success(len(negative_rows))
    min_lcb = min(positive_lcb, negative_lcb)
    positive_groups = {row["matched_negative_group_id"] for row in positive_rows}
    negative_groups = {row["matched_negative_group_id"] for row in negative_rows}
    orphan_groups = sorted(positive_groups - negative_groups)
    broad_normal_sample = False
    direct_species_closed = False
    support_ok = len(positive_rows) >= 50 and len(negative_rows) >= 50
    new_confidence_gate = support_ok and min_lcb >= 0.95 and broad_normal_sample and direct_species_closed
    decision = "r6_zhao_skudder_cftc_row_uplift_v1=rows_added_schema_ready_calibration_still_blocked"
    if not positive_added and not negative_added and not (positive_rows_materialized and negative_rows_materialized):
        decision = "r6_zhao_skudder_cftc_row_uplift_v1=no_new_unique_rows_calibration_still_blocked"
    gates = [
        {"gate": "verifier_schema_ready", "observed": verifier_json.get("status"), "required": "schema_ready_unscored", "pass": verifier_json.get("status") == "schema_ready_unscored"},
        {"gate": "positive_rows_materialized", "observed": positive_rows_materialized, "required": 7, "pass": positive_rows_materialized == 7},
        {"gate": "matched_negative_rows_materialized", "observed": negative_rows_materialized, "required": 7, "pass": negative_rows_materialized == 7},
        {"gate": "positive_support", "observed": len(positive_rows), "required": ">=50", "pass": len(positive_rows) >= 50},
        {"gate": "negative_support", "observed": len(negative_rows), "required": ">=50", "pass": len(negative_rows) >= 50},
        {"gate": "orphan_groups", "observed": len(orphan_groups), "required": 0, "pass": not orphan_groups},
        {"gate": "chronological_split", "observed": unique_count(positive_rows, "trade_date"), "required": ">=2 dates", "pass": unique_count(positive_rows, "trade_date") >= 2},
        {"gate": "heldout_symbol_or_venue", "observed": f"symbols={unique_count(positive_rows, 'symbol')};venues={unique_count(positive_rows, 'venue_or_market_center')}", "required": "symbol>=2 or venue>=2", "pass": unique_count(positive_rows, "symbol") >= 2 or unique_count(positive_rows, "venue_or_market_center") >= 2},
        {"gate": "wilson95_lcb", "observed": f"{min_lcb:.6f}", "required": ">=0.95", "pass": min_lcb >= 0.95},
        {"gate": "broad_normal_sample", "observed": broad_normal_sample, "required": True, "pass": broad_normal_sample},
        {"gate": "direct_species_coverage", "observed": direct_species_closed, "required": True, "pass": direct_species_closed},
    ]
    labels = Counter(row.get("label", "") for row in positive_rows + negative_rows)
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": board_hash_before,
        "decision": decision,
        "source_results": source_results,
        "external_requests_sent": external_requests_sent,
        "before": {
            "positive_rows": len(positives_before),
            "matched_negative_rows": len(negatives_before),
            "positive_sha256": pre_hashes["positive_spoofing_layering_rows.csv"],
            "matched_negative_sha256": pre_hashes["matched_negative_normal_activity_rows.csv"],
            "provenance_sha256": pre_hashes["provenance_manifest.json"],
        },
        "after": {
            "positive_rows": len(positive_rows),
            "matched_negative_rows": len(negative_rows),
            "positive_sha256": sha256(POSITIVE),
            "matched_negative_sha256": sha256(NEGATIVE),
            "provenance_sha256": sha256(PROVENANCE),
        },
        "positive_rows_added": positive_rows_materialized,
        "matched_negative_rows_added": negative_rows_materialized,
        "positive_rows_added_this_rerun": len(positive_added),
        "matched_negative_rows_added_this_rerun": len(negative_added),
        "positive_source_row_ids_added": [row["source_row_id"] for row in positive_added],
        "matched_negative_source_row_ids_added": [row["source_row_id"] for row in negative_added],
        "positive_rows": len(positive_rows),
        "matched_negative_rows": len(negative_rows),
        "matched_group_count": len(positive_groups & negative_groups),
        "orphan_groups": orphan_groups,
        "unique_dates": unique_count(positive_rows, "trade_date"),
        "unique_symbols": unique_count(positive_rows, "symbol"),
        "unique_venues": unique_count(positive_rows, "venue_or_market_center"),
        "labels": dict(labels),
        "positive_wilson95_lcb": positive_lcb,
        "negative_wilson95_lcb": negative_lcb,
        "combined_min_wilson95_lcb": min_lcb,
        "support_ok": support_ok,
        "broad_normal_sample": broad_normal_sample,
        "direct_species_closed": direct_species_closed,
        "verifier_returncode": verifier.returncode,
        "verifier": verifier_json,
        "gate_rows": gates,
        "accepted_rows_added": 0,
        "new_confidence_gate": new_confidence_gate,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Acquire more source-owned R6 rows, broad normal-market controls, and direct species rows; R2/R3/R4/R5 remain blocked until required source-owned files exist.",
    }

    json_path = OUT / "r6_zhao_skudder_cftc_row_uplift_v1.json"
    report_path = OUT / "r6_zhao_skudder_cftc_row_uplift_v1.md"
    gates_csv = OUT / "r6_zhao_skudder_cftc_row_uplift_v1_gates.csv"
    additions_csv = OUT / "r6_zhao_skudder_cftc_row_uplift_v1_additions.csv"
    assertions_path = CHECKS / "r6_zhao_skudder_cftc_row_uplift_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gates_csv, gates, ["gate", "observed", "required", "pass"])
    write_csv(additions_csv, [{"kind": "positive", **row} for row in positive_added] + [{"kind": "matched_negative", **row} for row in negative_added], ["kind", *FIELDS])

    lines = [
        "# R6 Zhao/Skudder CFTC Row Uplift v1",
        "",
        f"Decision: `{decision}`.",
        "",
        "Result:",
        f"- Positive rows added/materialized by this artifact: `{positive_rows_materialized}`; matched controls added/materialized: `{negative_rows_materialized}`.",
        f"- Rows newly appended during this rerun: positives `{len(positive_added)}`, matched controls `{len(negative_added)}`.",
        f"- Direct intake after run: positives `{len(positive_rows)}`, matched negatives `{len(negative_rows)}`, matched groups `{len(positive_groups & negative_groups)}`.",
        f"- Unique positive dates/symbols/venues: `{unique_count(positive_rows, 'trade_date')}` / `{unique_count(positive_rows, 'symbol')}` / `{unique_count(positive_rows, 'venue_or_market_center')}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{min_lcb:.6f}`.",
        f"- Verifier status: `{verifier_json.get('status')}`.",
        "- Broad normal sample: `false`; direct species coverage still incomplete.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        f"- External official CFTC PDF requests sent: `{str(external_requests_sent).lower()}`; raw data committed: `false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; trade usable: `false`.",
        "",
        "Source Boundary:",
        "- Raw PDFs/text stay under `/tmp/ict-engine-r6-zhao-skudder-cftc-row-uplift-v1`; repo artifacts record only URLs, hashes, summaries, and derived row assertions.",
        "- Same-complaint genuine legs are matched schema/control seeds. They do not satisfy the broad normal-market calibration-control requirement.",
        "",
        "Gates:",
        "",
        "| Gate | Observed | Required | Pass |",
        "|---|---|---|---:|",
    ]
    for gate in gates:
        lines.append(f"| `{gate['gate']}` | `{gate['observed']}` | `{gate['required']}` | `{str(gate['pass']).lower()}` |")
    lines.extend(
        [
            "",
            "Artifacts:",
            f"- JSON: `{rel(json_path)}`",
            f"- Gate CSV: `{rel(gates_csv)}`",
            f"- Additions CSV: `{rel(additions_csv)}`",
            f"- Direct verifier stdout: `{rel(CMD_OUT / 'direct_manipulation_row_intake_verifier.stdout.txt')}`",
            f"- Assertions: `{rel(assertions_path)}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assertions = [
        f"PASS decision={decision}",
        f"PASS positive_rows_materialized={positive_rows_materialized}",
        f"PASS matched_negative_rows_materialized={negative_rows_materialized}",
        f"PASS verifier_status={verifier_json.get('status')}",
        f"PASS positive_rows={len(positive_rows)}",
        f"PASS matched_negative_rows={len(negative_rows)}",
        f"PASS combined_min_wilson95_lcb={min_lcb:.6f}",
        f"PASS support_ok={str(support_ok).lower()}",
        f"PASS broad_normal_sample={str(broad_normal_sample).lower()}",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
        f"PASS external_requests_sent={str(external_requests_sent).lower()}",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "positive_rows": len(positive_rows), "matched_negative_rows": len(negative_rows), "min_wilson95_lcb": round(min_lcb, 6), "report": rel(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
