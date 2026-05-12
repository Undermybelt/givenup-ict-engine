#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T211606+0800-codex-r6-shak-complaint-row-uplift-gate-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-shak-complaint-row-uplift-gate"
CHECKS = RUN_ROOT / "checks"
COMMAND_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"

SOURCE_DIR = Path("/tmp/ict-engine-r6-shak-cftc-source")
SOURCE_URL = "https://www.cftc.gov/media/7526/enfshakcomplaint080522/download"
SOURCE_PDF = SOURCE_DIR / "enfshakcomplaint080522.pdf"
SOURCE_TEXT = SOURCE_DIR / "enfshakcomplaint080522.txt"

VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

FIELDNAMES = [
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

SOURCE_REPORT = "CFTC Complaint: CFTC v. Daniel Lawrence Shak, Case 2:22-cv-01258, Document 1"
PARTICIPANT = "Daniel Lawrence Shak"

POSITIVE_ADDITIONS = [
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 49-53, Example 1, March 3 2017 April 2017 Gold",
        "trade_date": "2017-03-03",
        "symbol": "April 2017 Gold futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "buy spoof orders opposite sell genuine order",
        "earliest_order_received_time": "07:53:21.124 America/Chicago",
        "latest_order_received_time": "07:53:58.693 America/Chicago",
        "order_count": "ten spoof orders",
        "total_order_quantity": "200 lots",
        "activity_description": "CFTC complaint describes ten buy-side spoof orders entered while a one-lot genuine sell order was worked, then canceled after the genuine order filled.",
        "matched_negative_group_id": "cftc_shak_20170303_gc_example1",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_shak_20170303_gold_buy_spoof_group",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 55-60, Example 2, March 24 2017 April 2017 Gold",
        "trade_date": "2017-03-24",
        "symbol": "April 2017 Gold futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "buy spoof orders opposite sell genuine order",
        "earliest_order_received_time": "08:30:20.375 America/Chicago",
        "latest_order_received_time": "08:30:42.819 America/Chicago",
        "order_count": "five spoof orders",
        "total_order_quantity": "300 lots",
        "activity_description": "CFTC complaint describes one initial 50-lot spoof order and four further buy-side spoof orders opposite a five-lot genuine sell order.",
        "matched_negative_group_id": "cftc_shak_20170324_gc_example2",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_shak_20170324_gold_buy_spoof_group",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 61-66, Example 3, September 18 2017 December 2017 Silver",
        "trade_date": "2017-09-18",
        "symbol": "December 2017 Silver futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "buy spoof orders opposite sell genuine orders",
        "earliest_order_received_time": "06:30:46.389 America/Chicago",
        "latest_order_received_time": "06:31:39.576 America/Chicago",
        "order_count": "eight spoof orders",
        "total_order_quantity": "340 lots",
        "activity_description": "CFTC complaint describes eight buy-side spoof orders opposite two one-lot genuine sell orders, canceled after the genuine orders filled.",
        "matched_negative_group_id": "cftc_shak_20170918_si_example3",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_shak_20170918_silver_buy_spoof_group",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 73-76, Example 4B, October 5 2017 December 2017 Gold",
        "trade_date": "2017-10-05",
        "symbol": "December 2017 Gold futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "buy spoof orders opposite sell genuine iceberg order",
        "earliest_order_received_time": "09:47:34.921 America/Chicago",
        "latest_order_received_time": "09:49:01.332 America/Chicago",
        "order_count": "nine spoof orders",
        "total_order_quantity": "225 lots",
        "activity_description": "CFTC complaint describes nine buy-side spoof orders opposite a sell iceberg order, followed by cancellations after the iceberg order filled.",
        "matched_negative_group_id": "cftc_shak_20171005_gc_example4b",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_shak_20171005_gold_buy_spoof_group",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 79-85, Example 5, January 22 2018 March 2018 Silver",
        "trade_date": "2018-01-22",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "buy spoof orders opposite sell genuine order",
        "earliest_order_received_time": "05:17:44.407 America/Chicago",
        "latest_order_received_time": "05:18:20.286 America/Chicago",
        "order_count": "six spoof orders",
        "total_order_quantity": "300 lots",
        "activity_description": "CFTC complaint describes six buy-side spoof orders opposite a one-lot genuine sell order, canceled quickly after the genuine order filled.",
        "matched_negative_group_id": "cftc_shak_20180122_si_example5",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_shak_20180122_silver_buy_spoof_group",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 86-90, Example 6 first sequence, February 21 2018 March 2018 Silver",
        "trade_date": "2018-02-21",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "sell spoof orders opposite buy genuine order",
        "earliest_order_received_time": "03:19:39.023 America/Chicago",
        "latest_order_received_time": "03:20:06.537 America/Chicago",
        "order_count": "six spoof orders",
        "total_order_quantity": "250 lots",
        "activity_description": "CFTC complaint describes six sell-side spoof orders opposite a three-lot genuine buy order, canceled after the genuine order filled.",
        "matched_negative_group_id": "cftc_shak_20180221_si_example6_buy",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_shak_20180221_silver_sell_spoof_group",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 91-96, Example 6 second sequence, February 21 2018 March 2018 Silver",
        "trade_date": "2018-02-21",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "buy spoof orders opposite sell genuine order",
        "earliest_order_received_time": "03:21:59.867 America/Chicago",
        "latest_order_received_time": "03:22:57.819 America/Chicago",
        "order_count": "seven spoof orders",
        "total_order_quantity": "350 lots",
        "activity_description": "CFTC complaint describes seven buy-side spoof orders opposite a three-lot genuine sell order, canceled after the genuine order filled.",
        "matched_negative_group_id": "cftc_shak_20180221_si_example6_sell",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_shak_20180221_silver_buy_spoof_group",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 98-102, Example 7, February 26 2018 March 2018 Silver",
        "trade_date": "2018-02-26",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "sell spoof orders opposite buy genuine iceberg order",
        "earliest_order_received_time": "13:43:38.337 America/Chicago",
        "latest_order_received_time": "13:44:24.297 America/Chicago",
        "order_count": "seven spoof orders",
        "total_order_quantity": "235 lots",
        "activity_description": "CFTC complaint describes seven sell-side spoof orders opposite a ten-lot buy iceberg order, canceled after the genuine order filled.",
        "matched_negative_group_id": "cftc_shak_20180226_si_example7",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_shak_20180226_silver_sell_spoof_group",
    },
]

NEGATIVE_ADDITIONS = [
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 49 and 52, Example 1, March 3 2017 April 2017 Gold",
        "trade_date": "2017-03-03",
        "symbol": "April 2017 Gold futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "sell genuine order",
        "earliest_order_received_time": "07:52:57.348 America/Chicago",
        "latest_order_received_time": "07:53:54.558 America/Chicago",
        "order_count": "one genuine order",
        "total_order_quantity": "1 lot",
        "activity_description": "Same-source genuine sell order leg described by the CFTC complaint. This is a same-event control seed, not independent broad normal-market activity.",
        "matched_negative_group_id": "cftc_shak_20170303_gc_example1",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_shak_20170303_gold_sell_genuine_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 55 and 58, Example 2, March 24 2017 April 2017 Gold",
        "trade_date": "2017-03-24",
        "symbol": "April 2017 Gold futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "sell genuine order",
        "earliest_order_received_time": "08:30:17.046 America/Chicago",
        "latest_order_received_time": "08:30:36.432 America/Chicago",
        "order_count": "one genuine order",
        "total_order_quantity": "5 lots",
        "activity_description": "Same-source genuine sell order leg described by the CFTC complaint. This is a same-event control seed, not independent broad normal-market activity.",
        "matched_negative_group_id": "cftc_shak_20170324_gc_example2",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_shak_20170324_gold_sell_genuine_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 61 and 64, Example 3, September 18 2017 December 2017 Silver",
        "trade_date": "2017-09-18",
        "symbol": "December 2017 Silver futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "sell genuine orders",
        "earliest_order_received_time": "06:30:32.856 America/Chicago",
        "latest_order_received_time": "06:31:35.275 America/Chicago",
        "order_count": "two genuine orders",
        "total_order_quantity": "2 lots total",
        "activity_description": "Same-source genuine sell order legs described by the CFTC complaint. This is a same-event control seed, not independent broad normal-market activity.",
        "matched_negative_group_id": "cftc_shak_20170918_si_example3",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_shak_20170918_silver_sell_genuine_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 75-76, Example 4B, October 5 2017 December 2017 Gold",
        "trade_date": "2017-10-05",
        "symbol": "December 2017 Gold futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "09:47:46.043 America/Chicago",
        "latest_order_received_time": "09:48:10.953 America/Chicago",
        "order_count": "one iceberg genuine order",
        "total_order_quantity": "38 lots",
        "activity_description": "Same-source sell iceberg order leg described by the CFTC complaint. This is a same-event control seed, not independent broad normal-market activity.",
        "matched_negative_group_id": "cftc_shak_20171005_gc_example4b",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_shak_20171005_gold_sell_iceberg_genuine_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 79 and 82, Example 5, January 22 2018 March 2018 Silver",
        "trade_date": "2018-01-22",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "sell genuine order",
        "earliest_order_received_time": "05:17:12.964 America/Chicago",
        "latest_order_received_time": "05:18:16.998 America/Chicago",
        "order_count": "one genuine order",
        "total_order_quantity": "1 lot",
        "activity_description": "Same-source genuine sell order leg described by the CFTC complaint. This is a same-event control seed, not independent broad normal-market activity.",
        "matched_negative_group_id": "cftc_shak_20180122_si_example5",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_shak_20180122_silver_sell_genuine_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 86 and 88, Example 6 first sequence, February 21 2018 March 2018 Silver",
        "trade_date": "2018-02-21",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "buy genuine order",
        "earliest_order_received_time": "03:19:34.946 America/Chicago",
        "latest_order_received_time": "03:19:59.508 America/Chicago",
        "order_count": "one genuine order",
        "total_order_quantity": "3 lots",
        "activity_description": "Same-source genuine buy order leg described by the CFTC complaint. This is a same-event control seed, not independent broad normal-market activity.",
        "matched_negative_group_id": "cftc_shak_20180221_si_example6_buy",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_shak_20180221_silver_buy_genuine_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 91 and 94, Example 6 second sequence, February 21 2018 March 2018 Silver",
        "trade_date": "2018-02-21",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "sell genuine order",
        "earliest_order_received_time": "03:21:55.679 America/Chicago",
        "latest_order_received_time": "03:22:51.442 America/Chicago",
        "order_count": "one genuine order",
        "total_order_quantity": "3 lots",
        "activity_description": "Same-source genuine sell order leg described by the CFTC complaint. This is a same-event control seed, not independent broad normal-market activity.",
        "matched_negative_group_id": "cftc_shak_20180221_si_example6_sell",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_shak_20180221_silver_sell_genuine_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 98 and 100, Example 7, February 26 2018 March 2018 Silver",
        "trade_date": "2018-02-26",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": "COMEX",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "buy genuine iceberg order",
        "earliest_order_received_time": "13:43:33.731 America/Chicago",
        "latest_order_received_time": "13:44:21.442 America/Chicago",
        "order_count": "one iceberg genuine order",
        "total_order_quantity": "10 lots",
        "activity_description": "Same-source buy iceberg order leg described by the CFTC complaint. This is a same-event control seed, not independent broad normal-market activity.",
        "matched_negative_group_id": "cftc_shak_20180226_si_example7",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_shak_20180226_silver_buy_iceberg_genuine_control",
    },
]

NEEDLES = [
    "At 7:52:57.348 AM on March 3, 2017",
    "Between 7:53:21.124 and 7:53:50.324",
    "At 8:30:17.046 AM on March 24, 2017",
    "Between 8:30:26.155 and 8:30:32.855",
    "At 6:30:32.856 AM on September 18, 2017",
    "Between 6:30:46.389 and 6:31:19.636",
    "At 5:17:12.964 AM on January 22, 2018",
    "Between 5:17:44.407 and 5:18:12.169",
    "At 3:19:34.946 AM on February 21, 2018",
    "At 1:43:33.731 PM on February 26, 2018",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def append_unique(path: Path, additions: list[dict[str, str]]) -> tuple[int, int]:
    rows = read_rows(path)
    seen = {row.get("source_row_id", "") for row in rows}
    added = 0
    for row in additions:
        if row["source_row_id"] not in seen:
            rows.append(row)
            seen.add(row["source_row_id"])
            added += 1
    write_rows(path, rows)
    return len(rows), added


def ensure_source_text() -> dict[str, object]:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    if not SOURCE_PDF.exists():
        urllib.request.urlretrieve(SOURCE_URL, SOURCE_PDF)
    if not SOURCE_TEXT.exists():
        subprocess.run(
            [
                "gs",
                "-q",
                "-dNOPAUSE",
                "-dBATCH",
                "-sDEVICE=txtwrite",
                f"-sOutputFile={SOURCE_TEXT}",
                str(SOURCE_PDF),
            ],
            check=False,
            text=True,
            capture_output=True,
        )
    text = SOURCE_TEXT.read_text(encoding="utf-8", errors="ignore") if SOURCE_TEXT.exists() else ""
    text_lower = text.lower()
    return {
        "url": SOURCE_URL,
        "pdf_path": str(SOURCE_PDF),
        "pdf_sha256": sha256(SOURCE_PDF),
        "text_path": str(SOURCE_TEXT) if SOURCE_TEXT.exists() else None,
        "text_sha256": sha256(SOURCE_TEXT) if SOURCE_TEXT.exists() else None,
        "text_checks": {needle: needle.lower() in text_lower for needle in NEEDLES},
    }


def update_provenance(source_probe: dict[str, object], positive_count: int, negative_count: int, positive_added: int, negative_added: int) -> dict[str, object]:
    if PROVENANCE.exists():
        try:
            provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            provenance = {}
    else:
        provenance = {}
    provenance["cftc_shak_complaint_examples"] = source_probe
    provenance["shak_complaint_rows_materialized_at_utc"] = datetime.now(timezone.utc).isoformat()
    provenance["shak_complaint_positive_rows_added"] = positive_added
    provenance["shak_complaint_matched_negative_rows_added"] = negative_added
    provenance["positive_rows_count"] = positive_count
    provenance["matched_negative_rows_count"] = negative_count
    provenance["matched_negative_control_policy"] = (
        "Derived only from public CFTC complaint facts describing genuine order legs in the same examples; "
        "schema-ready/unscored seed, not a broad normal-market calibration sample."
    )
    provenance["matched_control_limitations"] = (
        "CFTC same-complaint genuine-order legs are schema/control seeds only; "
        "they are not independent broad normal-market heldout controls."
    )
    provenance["updated_by"] = RUN_ID
    provenance["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return provenance


def wilson_lcb(successes: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    phat = successes / total
    denom = 1 + z * z / total
    centre = phat + z * z / (2 * total)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total)
    return (centre - margin) / denom


def count_values(rows: list[dict[str, str]], key: str) -> list[str]:
    return sorted({row.get(key, "") for row in rows if row.get(key, "")})


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def run_verifier() -> dict[str, object]:
    completed = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE)],
        text=True,
        capture_output=True,
        check=False,
    )
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    (COMMAND_OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (COMMAND_OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(completed.stderr, encoding="utf-8")
    try:
        stdout: object = json.loads(completed.stdout)
    except json.JSONDecodeError:
        stdout = completed.stdout
    return {"returncode": completed.returncode, "stdout": stdout, "stderr": completed.stderr}


def calibrate() -> dict[str, object]:
    positives = read_rows(POSITIVE)
    negatives = read_rows(NEGATIVE)
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8")) if PROVENANCE.exists() else {}
    all_rows = positives + negatives
    labels = Counter(row.get("label", "") for row in all_rows)
    dates = count_values(all_rows, "trade_date")
    symbols = count_values(all_rows, "symbol")
    venues = count_values(all_rows, "venue_or_market_center")
    groups = count_values(all_rows, "matched_negative_group_id")
    sessions = count_values(all_rows, "session_bucket")
    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    combined_lcb = min(positive_lcb, negative_lcb)
    min_support = 50
    support_ok = len(positives) >= min_support and len(negatives) >= min_support
    chronological_split_ok = len(dates) >= 2
    heldout_symbol_or_venue_ok = len(symbols) >= 2 or len(venues) >= 2
    broad_normal_sample = "not a broad" not in provenance.get("matched_negative_control_policy", "").lower()
    gate_rows = [
        {"gate": "positive_support", "observed": len(positives), "required": min_support, "pass": len(positives) >= min_support},
        {"gate": "negative_support", "observed": len(negatives), "required": min_support, "pass": len(negatives) >= min_support},
        {"gate": "chronological_split", "observed": len(dates), "required": 2, "pass": chronological_split_ok},
        {"gate": "heldout_symbol_or_venue", "observed": f"symbols={len(symbols)};venues={len(venues)}", "required": "symbol>=2 or venue>=2", "pass": heldout_symbol_or_venue_ok},
        {"gate": "wilson95_lcb", "observed": f"{combined_lcb:.6f}", "required": ">=0.95", "pass": combined_lcb >= 0.95},
        {"gate": "broad_normal_sample", "observed": provenance.get("matched_negative_control_policy", ""), "required": "source-owned broad normal activity sample", "pass": broad_normal_sample},
    ]
    gate_pass = all(bool(row["pass"]) for row in gate_rows)
    return {
        "decision": "r6_shak_complaint_row_uplift_gate_v1=accepted_95" if gate_pass else "r6_shak_complaint_row_uplift_gate_v1=schema_ready_but_calibration_blocked",
        "gate_pass": gate_pass,
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "labels": dict(labels),
        "unique_dates": dates,
        "unique_symbols": symbols,
        "unique_venues": venues,
        "matched_groups": groups,
        "session_buckets": sessions,
        "positive_wilson95_lcb": positive_lcb,
        "negative_wilson95_lcb": negative_lcb,
        "combined_min_wilson95_lcb": combined_lcb,
        "support_ok": support_ok,
        "chronological_split_ok": chronological_split_ok,
        "heldout_symbol_or_venue_ok": heldout_symbol_or_venue_ok,
        "broad_normal_sample": broad_normal_sample,
        "gate_rows": gate_rows,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    source_probe = ensure_source_text()
    positive_count, positive_added = append_unique(POSITIVE, POSITIVE_ADDITIONS)
    negative_count, negative_added = append_unique(NEGATIVE, NEGATIVE_ADDITIONS)
    provenance = update_provenance(source_probe, positive_count, negative_count, positive_added, negative_added)
    verifier = run_verifier()
    calibration = calibrate()

    gate_csv = OUT / "r6_shak_complaint_row_uplift_gate_v1_gates.csv"
    write_csv(gate_csv, calibration["gate_rows"], ["gate", "observed", "required", "pass"])

    result = {
        "artifact_type": "r6_shak_complaint_row_uplift_gate_v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_writeback": sha256(BOARD),
        "source_probe": source_probe,
        "positive_rows_added_this_run": positive_added,
        "matched_negative_rows_added_this_run": negative_added,
        "provenance_keys": sorted(provenance.keys()),
        "verifier": verifier,
        **calibration,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "r6_direct_species_closed": False,
        "next_action": "Acquire source-owned or owner-approved broad same-schema normal controls and more positive rows until support, Wilson95, chronological, and heldout gates pass without proxy labels.",
        "source_hashes": {
            "positive_spoofing_layering_rows.csv": sha256(POSITIVE),
            "matched_negative_normal_activity_rows.csv": sha256(NEGATIVE),
            "provenance_manifest.json": sha256(PROVENANCE),
        },
    }

    json_path = OUT / "r6_shak_complaint_row_uplift_gate_v1.json"
    md_path = OUT / "r6_shak_complaint_row_uplift_gate_v1.md"
    assertions_path = CHECKS / "r6_shak_complaint_row_uplift_gate_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# R6 Shak Complaint Row Uplift Gate v1",
        "",
        f"- Decision: `{result['decision']}`.",
        f"- Positive rows now: `{result['positive_rows']}`; added this run: `{positive_added}`.",
        f"- Matched negative/control rows now: `{result['matched_negative_rows']}`; added this run: `{negative_added}`.",
        f"- Unique dates: `{len(result['unique_dates'])}`; symbols: `{len(result['unique_symbols'])}`; venues: `{len(result['unique_venues'])}`.",
        f"- Wilson95 LCB positive/negative/min: `{result['positive_wilson95_lcb']:.6f}` / `{result['negative_wilson95_lcb']:.6f}` / `{result['combined_min_wilson95_lcb']:.6f}`.",
        f"- Chronological split ok: `{str(result['chronological_split_ok']).lower()}`; heldout symbol/venue ok: `{str(result['heldout_symbol_or_venue_ok']).lower()}`.",
        f"- Broad normal sample: `{str(result['broad_normal_sample']).lower()}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Boundary",
        "",
        "This slice materializes source-owned CFTC Shak complaint example rows for Gold/Silver spoofing events. The matched controls are same-complaint genuine-order legs only, so they remain schema/control seeds and do not satisfy the broad normal-market calibration requirement.",
        "",
        "## Gates",
        "",
        "| Gate | Observed | Required | Pass |",
        "|---|---|---|---:|",
    ]
    for row in calibration["gate_rows"]:
        lines.append(f"| `{row['gate']}` | `{row['observed']}` | `{row['required']}` | `{str(row['pass']).lower()}` |")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Gate CSV: `{gate_csv}`",
            f"- Verifier stdout: `{COMMAND_OUT / 'direct_manipulation_row_intake_verifier.stdout.txt'}`",
            f"- Assertions: `{assertions_path}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={result['decision']}",
        f"PASS positive_rows={result['positive_rows']}",
        f"PASS matched_negative_rows={result['matched_negative_rows']}",
        f"PASS positive_rows_added_this_run={positive_added}",
        f"PASS matched_negative_rows_added_this_run={negative_added}",
        f"PASS verifier_returncode={verifier['returncode']}",
        f"PASS combined_min_wilson95_lcb={result['combined_min_wilson95_lcb']:.6f}",
        f"PASS support_ok={str(result['support_ok']).lower()}",
        f"PASS broad_normal_sample={str(result['broad_normal_sample']).lower()}",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "positive_rows": result["positive_rows"], "matched_negative_rows": result["matched_negative_rows"], "update_goal": False}, sort_keys=True))
    return 0 if verifier["returncode"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
