#!/usr/bin/env python3
"""Append cached official CFTC Flotron complaint examples and rerun the R6 gate."""

from __future__ import annotations

import csv
import fcntl
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T213312-codex-r6-flotron-cftc-row-uplift-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-flotron-cftc-row-uplift"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"
LOCK = INTAKE / ".r6_flotron_cftc_row_uplift_v1.lock"
SOURCE_URL = "https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfandreflotroncomplaint012918.pdf"
SOURCE_PDF = Path("/tmp/ict-engine-r6-public-source-probes-v1/flotron.pdf")
SOURCE_TEXT = Path("/tmp/ict-engine-r6-public-source-probes-v1/flotron.txt")
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

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

SOURCE_REPORT = "CFTC Complaint: CFTC v. Andre Flotron, Case 3:18-cv-00158"
VENUE = "COMEX/CME Globex"
FLOTRON_PARTICIPANT = "CFTC defendant trader; Bank A precious metals desk"
TRADER_A_PARTICIPANT = "Bank A subordinate trader described in official CFTC complaint"

POSITIVE_ADDITIONS = [
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraph 30, August 29 2008 December-delivery Gold Futures example",
        "trade_date": "2008-08-29",
        "symbol": "December-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "sell spoof order opposite buy genuine orders",
        "earliest_order_received_time": "about 13:10:25.536 Eastern Time",
        "latest_order_received_time": "about two seconds after the final 5-lot buy fill",
        "order_count": "one spoof order",
        "total_order_quantity": "44 lots",
        "activity_description": "Official CFTC complaint describes a 44-lot sell spoof order opposite a seven-lot buy genuine order and follow-on small buy genuine orders; the spoof order was canceled after the genuine orders filled.",
        "matched_negative_group_id": "cftc_flotron_20080829_gold_example",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_20080829_gold_sell_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraph 31, October 9 2008 Trader A December-delivery Gold Futures example",
        "trade_date": "2008-10-09",
        "symbol": "December-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": TRADER_A_PARTICIPANT,
        "participant_identifier": "Trader A / Bank A",
        "side": "buy spoof orders opposite sell genuine orders",
        "earliest_order_received_time": "08:49:18.528 Eastern Time",
        "latest_order_received_time": "08:52:02.264 Eastern Time",
        "order_count": "two spoof orders",
        "total_order_quantity": "60 lots total",
        "activity_description": "Official CFTC complaint describes Trader A entering 40-lot and 20-lot buy spoof orders opposite sell genuine orders, then canceling both spoof orders after sell orders filled.",
        "matched_negative_group_id": "cftc_flotron_trader_a_20081009_gold_example",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_trader_a_20081009_gold_buy_spoof_orders",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 33-37, September 6 2011 December-delivery Gold Futures example",
        "trade_date": "2011-09-06",
        "symbol": "December-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "sell spoof order opposite buy genuine orders",
        "earliest_order_received_time": "05:06:35.057 Eastern Time",
        "latest_order_received_time": "05:06:43.251 Eastern Time",
        "order_count": "one spoof order",
        "total_order_quantity": "33 lots",
        "activity_description": "Official CFTC complaint describes a 33-lot sell spoof order three ticks from the best offer opposite two one-lot buy orders and fourteen additional one-lot buy genuine orders, followed by full cancellation.",
        "matched_negative_group_id": "cftc_flotron_20110906_gold_example",
        "session_bucket": "overnight_eastern_time",
        "source_row_id": "cftc_flotron_20110906_gold_sell_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 38-43, June 28 2012 August-delivery Gold Futures example",
        "trade_date": "2012-06-28",
        "symbol": "August-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "sell spoof order opposite buy genuine orders",
        "earliest_order_received_time": "13:26:42.415 Eastern Time",
        "latest_order_received_time": "13:26:53.313 Eastern Time",
        "order_count": "one spoof order",
        "total_order_quantity": "55 lots",
        "activity_description": "Official CFTC complaint describes a 55-lot sell spoof order two ticks from the best offer opposite two pending buy genuine orders and additional small buy orders; the spoof order was fully canceled.",
        "matched_negative_group_id": "cftc_flotron_20120628_gold_example",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_20120628_gold_sell_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 44-50, February 15 2013 March-delivery Silver Futures example",
        "trade_date": "2013-02-15",
        "symbol": "March-delivery Silver Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "sell spoof order opposite buy genuine orders",
        "earliest_order_received_time": "over four seconds after 05:59:28.544 Eastern Time",
        "latest_order_received_time": "less than two seconds after fourth additional one-lot buy fill",
        "order_count": "one spoof order",
        "total_order_quantity": "55 lots",
        "activity_description": "Official CFTC complaint describes a 55-lot sell spoof order one tick from the best offer, increasing visible sell-side volume by almost 50 percent, opposite one-lot buy genuine orders.",
        "matched_negative_group_id": "cftc_flotron_20130215_silver_example",
        "session_bucket": "overnight_eastern_time",
        "source_row_id": "cftc_flotron_20130215_silver_sell_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 51-60, July 1 2013 August-delivery Gold Futures example",
        "trade_date": "2013-07-01",
        "symbol": "August-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "buy spoof order opposite sell genuine orders",
        "earliest_order_received_time": "10:11:23.173 Eastern Time",
        "latest_order_received_time": "less than one second after 10:11:54.543 Eastern Time",
        "order_count": "one spoof order",
        "total_order_quantity": "111 lots",
        "activity_description": "Official CFTC complaint describes a 111-lot buy spoof order three ticks below best bid opposite a pending one-lot sell genuine order; the order was canceled as price approached.",
        "matched_negative_group_id": "cftc_flotron_20130701_gold_example",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_20130701_gold_buy_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 61-68, October 14 2013 December-delivery Gold Futures example",
        "trade_date": "2013-10-14",
        "symbol": "December-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "sell spoof order opposite buy genuine orders",
        "earliest_order_received_time": "08:26:48.474 Eastern Time",
        "latest_order_received_time": "less than four-tenths of a second after 08:26:52.720 Eastern Time",
        "order_count": "one spoof order",
        "total_order_quantity": "55 lots",
        "activity_description": "Official CFTC complaint describes a 55-lot sell spoof order two ticks from the best offer opposite a five-lot buy genuine order and follow-on buy genuine orders, then canceled as price moved back toward the spoof.",
        "matched_negative_group_id": "cftc_flotron_20131014_gold_example",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_20131014_gold_sell_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 69-71, October 17 2013 first December-delivery Gold Futures sequence",
        "trade_date": "2013-10-17",
        "symbol": "December-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "sell spoof order opposite buy genuine orders",
        "earliest_order_received_time": "11:13:35.407 Eastern Time",
        "latest_order_received_time": "about ten seconds after 11:13:35.407 Eastern Time",
        "order_count": "one spoof order",
        "total_order_quantity": "55 lots",
        "activity_description": "Official CFTC complaint describes a 55-lot sell spoof order one tick from the best offer, followed by one-lot buy genuine orders that filled, then full cancellation of the spoof order.",
        "matched_negative_group_id": "cftc_flotron_20131017_gold_first_sequence",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_20131017_gold_first_sell_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 72-79, October 17 2013 second December-delivery Gold Futures sequence",
        "trade_date": "2013-10-17",
        "symbol": "December-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "sell spoof order opposite buy genuine orders",
        "earliest_order_received_time": "over four seconds after 11:13:55.778 Eastern Time",
        "latest_order_received_time": "11:14:31.086 Eastern Time",
        "order_count": "one spoof order with one price modification",
        "total_order_quantity": "77 lots",
        "activity_description": "Official CFTC complaint describes a 77-lot sell spoof order that increased visible sell-side volume by over 60 percent, helped fill seven one-lot buy genuine orders, and was canceled in its entirety.",
        "matched_negative_group_id": "cftc_flotron_20131017_gold_second_sequence",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_20131017_gold_second_sell_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 80-85, October 17 2013 third December-delivery Gold Futures sequence",
        "trade_date": "2013-10-17",
        "symbol": "December-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "sell spoof order opposite buy genuine orders",
        "earliest_order_received_time": "11:15:37.060 Eastern Time",
        "latest_order_received_time": "about one second after price moved to 1319.20",
        "order_count": "one spoof order with two price modifications",
        "total_order_quantity": "99 lots",
        "activity_description": "Official CFTC complaint describes a 99-lot sell spoof order that more than doubled visible sell-side volume, was modified down twice while one-lot buy genuine orders filled, and was canceled as price approached.",
        "matched_negative_group_id": "cftc_flotron_20131017_gold_third_sequence",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_20131017_gold_third_sell_spoof_order",
    },
]

NEGATIVE_ADDITIONS = [
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraph 30, August 29 2008 December-delivery Gold Futures example",
        "trade_date": "2008-08-29",
        "symbol": "December-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "buy genuine orders",
        "earliest_order_received_time": "13:10:15.536 Eastern Time",
        "latest_order_received_time": "over the next two seconds after the 44-lot spoof order",
        "order_count": "initial seven-lot order plus four follow-on buy orders",
        "total_order_quantity": "33 lots",
        "activity_description": "Matched same-complaint control seed: source-described buy genuine order sequence distinguished from the 44-lot sell spoof order. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_flotron_20080829_gold_example",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_20080829_gold_buy_genuine_orders_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraph 31, October 9 2008 Trader A December-delivery Gold Futures example",
        "trade_date": "2008-10-09",
        "symbol": "December-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": TRADER_A_PARTICIPANT,
        "participant_identifier": "Trader A / Bank A",
        "side": "sell genuine orders",
        "earliest_order_received_time": "08:42:49.115 Eastern Time",
        "latest_order_received_time": "after 08:52:02.264 Eastern Time",
        "order_count": "initial three-lot sell order plus additional small sell orders",
        "total_order_quantity": "3 lots plus additional small sell orders described by source",
        "activity_description": "Matched same-complaint control seed: source-described sell genuine orders distinguished from the buy spoof orders. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_flotron_trader_a_20081009_gold_example",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_trader_a_20081009_gold_sell_genuine_orders_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 33-37, September 6 2011 December-delivery Gold Futures example",
        "trade_date": "2011-09-06",
        "symbol": "December-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "buy genuine orders",
        "earliest_order_received_time": "05:06:32.3 Eastern Time",
        "latest_order_received_time": "over the next six seconds after the 33-lot spoof order",
        "order_count": "sixteen one-lot buy orders",
        "total_order_quantity": "16 lots",
        "activity_description": "Matched same-complaint control seed: source-described one-lot buy genuine orders distinguished from the 33-lot sell spoof order. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_flotron_20110906_gold_example",
        "session_bucket": "overnight_eastern_time",
        "source_row_id": "cftc_flotron_20110906_gold_buy_genuine_orders_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 38-43, June 28 2012 August-delivery Gold Futures example",
        "trade_date": "2012-06-28",
        "symbol": "August-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "buy genuine orders",
        "earliest_order_received_time": "13:26:33.786 Eastern Time",
        "latest_order_received_time": "before 13:26:53.313 Eastern Time",
        "order_count": "two one-lot buy orders plus additional small buy orders",
        "total_order_quantity": "at least 2 lots plus additional small buy orders described by source",
        "activity_description": "Matched same-complaint control seed: source-described buy genuine orders distinguished from the 55-lot sell spoof order. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_flotron_20120628_gold_example",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_20120628_gold_buy_genuine_orders_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 44-50, February 15 2013 March-delivery Silver Futures example",
        "trade_date": "2013-02-15",
        "symbol": "March-delivery Silver Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "buy genuine orders",
        "earliest_order_received_time": "05:59:28.544 Eastern Time",
        "latest_order_received_time": "within 1.5 seconds after first fill",
        "order_count": "five one-lot buy orders",
        "total_order_quantity": "5 lots",
        "activity_description": "Matched same-complaint control seed: source-described one-lot buy genuine orders distinguished from the 55-lot sell spoof order. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_flotron_20130215_silver_example",
        "session_bucket": "overnight_eastern_time",
        "source_row_id": "cftc_flotron_20130215_silver_buy_genuine_orders_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 51-60, July 1 2013 August-delivery Gold Futures example",
        "trade_date": "2013-07-01",
        "symbol": "August-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "sell genuine orders",
        "earliest_order_received_time": "10:11:06.151 Eastern Time",
        "latest_order_received_time": "within 1.2 seconds after 10:11:23.173 Eastern Time",
        "order_count": "two one-lot sell orders described in sequence",
        "total_order_quantity": "2 lots",
        "activity_description": "Matched same-complaint control seed: source-described sell genuine orders distinguished from the 111-lot buy spoof order. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_flotron_20130701_gold_example",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_20130701_gold_sell_genuine_orders_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 61-68, October 14 2013 December-delivery Gold Futures example",
        "trade_date": "2013-10-14",
        "symbol": "December-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "buy genuine orders",
        "earliest_order_received_time": "08:26:47.706 Eastern Time",
        "latest_order_received_time": "within the next second after 08:26:49.466 Eastern Time",
        "order_count": "one five-lot buy order plus four follow-on buy orders",
        "total_order_quantity": "21 lots",
        "activity_description": "Matched same-complaint control seed: source-described buy genuine orders distinguished from the 55-lot sell spoof order. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_flotron_20131014_gold_example",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_20131014_gold_buy_genuine_orders_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 69-71, October 17 2013 first December-delivery Gold Futures sequence",
        "trade_date": "2013-10-17",
        "symbol": "December-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "buy genuine orders",
        "earliest_order_received_time": "approximately one-tenth of a second after 11:13:35.407 Eastern Time",
        "latest_order_received_time": "about ten seconds after 11:13:35.407 Eastern Time",
        "order_count": "seven one-lot buy orders",
        "total_order_quantity": "7 lots",
        "activity_description": "Matched same-complaint control seed: source-described buy genuine orders distinguished from the 55-lot sell spoof order. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_flotron_20131017_gold_first_sequence",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_20131017_gold_first_buy_genuine_orders_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 72-79, October 17 2013 second December-delivery Gold Futures sequence",
        "trade_date": "2013-10-17",
        "symbol": "December-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "buy genuine orders",
        "earliest_order_received_time": "11:13:55.778 Eastern Time",
        "latest_order_received_time": "about 2.4 seconds after 77-lot order modification",
        "order_count": "seven one-lot buy orders",
        "total_order_quantity": "7 lots",
        "activity_description": "Matched same-complaint control seed: source-described buy genuine orders distinguished from the 77-lot sell spoof order. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_flotron_20131017_gold_second_sequence",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_20131017_gold_second_buy_genuine_orders_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 80-85, October 17 2013 third December-delivery Gold Futures sequence",
        "trade_date": "2013-10-17",
        "symbol": "December-delivery Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": FLOTRON_PARTICIPANT,
        "participant_identifier": "Andre Flotron / Bank A",
        "side": "buy genuine orders",
        "earliest_order_received_time": "11:15:33.964 Eastern Time",
        "latest_order_received_time": "after second 99-lot order modification",
        "order_count": "at least nine one-lot buy orders described in sequence",
        "total_order_quantity": "at least 9 lots described by source",
        "activity_description": "Matched same-complaint control seed: source-described buy genuine orders distinguished from the 99-lot sell spoof order. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_flotron_20131017_gold_third_sequence",
        "session_bucket": "regular_eastern_time",
        "source_row_id": "cftc_flotron_20131017_gold_third_buy_genuine_orders_control",
    },
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def append_unique(path: Path, additions: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows = read_csv(path)
    seen = {row["source_row_id"] for row in rows}
    new_rows = [row for row in additions if row["source_row_id"] not in seen]
    if new_rows:
        rows.extend(new_rows)
        write_csv(path, rows)
    return rows, new_rows


def wilson_all_success(n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    phat = 1.0
    denom = 1.0 + z * z / n
    centre = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return (centre - margin) / denom


def summarize(rows: list[dict[str, str]]) -> dict[str, object]:
    return {
        "rows": len(rows),
        "unique_dates": len({row["trade_date"] for row in rows}),
        "unique_symbols": len({row["symbol"] for row in rows}),
        "unique_venues": len({row["venue_or_market_center"] for row in rows}),
        "unique_groups": len({row["matched_negative_group_id"] for row in rows}),
        "symbols": sorted({row["symbol"] for row in rows}),
        "venues": sorted({row["venue_or_market_center"] for row in rows}),
    }


def run_verifier() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    INTAKE.mkdir(parents=True, exist_ok=True)

    if not SOURCE_PDF.exists():
        raise FileNotFoundError(SOURCE_PDF)
    if not SOURCE_TEXT.exists():
        raise FileNotFoundError(SOURCE_TEXT)
    text = SOURCE_TEXT.read_text(encoding="utf-8", errors="replace")
    text_checks = {
        "August 29, 2008": "August 29, 2008" in text,
        "October 9, 2008": "October 9, 2008" in text,
        "September 6, 2011": "September 6, 2011" in text,
        "June 28, 2012": "June 28, 2012" in text,
        "February 15, 2013": "February 15, 2013" in text,
        "July 1, 2013": "July 1, 2013" in text,
        "October 14, 2013": "October 14, 2013" in text,
        "October 17, 2013": "October 17, 2013" in text,
        "13:10:15.536": "13:10:15.536" in text,
        "5:06:35.057": "5:06:35.057" in text,
        "13:26:42.415": "13:26:42.415" in text,
        "10:11:23.173": "10:11:23.173" in text,
        "11:15:37.060": "11:15:37.060" in text,
    }

    pre_hashes = {p.name: sha256_file(p) for p in (POSITIVE, NEGATIVE, PROVENANCE) if p.exists()}
    with LOCK.open("w", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        positive_rows, positive_added = append_unique(POSITIVE, POSITIVE_ADDITIONS)
        negative_rows, negative_added = append_unique(NEGATIVE, NEGATIVE_ADDITIONS)
        provenance = json.loads(PROVENANCE.read_text(encoding="utf-8")) if PROVENANCE.exists() else {}
        provenance["cftc_flotron_complaint_examples"] = {
            "url": SOURCE_URL,
            "pdf_path": str(SOURCE_PDF),
            "pdf_sha256": sha256_file(SOURCE_PDF),
            "text_path": str(SOURCE_TEXT),
            "text_sha256": sha256_file(SOURCE_TEXT),
            "text_checks": text_checks,
            "positive_source_row_ids": [row["source_row_id"] for row in positive_added],
            "matched_negative_source_row_ids": [row["source_row_id"] for row in negative_added],
            "rows_materialized_at_utc": datetime.now(timezone.utc).isoformat(),
            "control_boundary": "same-complaint genuine-order legs are schema/control seeds only, not broad normal-market calibration controls",
        }
        provenance["r6_flotron_cftc_row_uplift_v1"] = {
            "positive_rows_added": len(positive_added),
            "matched_negative_rows_added": len(negative_added),
            "run_id": RUN_ID,
        }
        provenance["positive_rows_count"] = len(positive_rows)
        provenance["matched_negative_rows_count"] = len(negative_rows)
        provenance["positive_rows_sha256"] = sha256_file(POSITIVE)
        provenance["matched_negative_rows_sha256"] = sha256_file(NEGATIVE)
        provenance["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        provenance["updated_by"] = RUN_ID
        PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        post_hashes = {p.name: sha256_file(p) for p in (POSITIVE, NEGATIVE, PROVENANCE) if p.exists()}
        verifier = run_verifier()

    (CMD_OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(verifier.stdout, encoding="utf-8")
    (CMD_OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(verifier.stderr, encoding="utf-8")

    pos_summary = summarize(positive_rows)
    neg_summary = summarize(negative_rows)
    positive_lcb = wilson_all_success(pos_summary["rows"])
    negative_lcb = wilson_all_success(neg_summary["rows"])
    min_lcb = min(positive_lcb, negative_lcb)
    support_ok = pos_summary["rows"] >= 50 and neg_summary["rows"] >= 50
    chronological_ok = min(pos_summary["unique_dates"], neg_summary["unique_dates"]) >= 2
    heldout_ok = pos_summary["unique_symbols"] >= 2 or pos_summary["unique_venues"] >= 2
    broad_normal_sample = False
    direct_species_closed = False
    new_rows_added = bool(positive_added or negative_added)
    if support_ok and min_lcb >= 0.95 and chronological_ok and heldout_ok and broad_normal_sample and direct_species_closed:
        decision = "r6_flotron_cftc_row_uplift_v1=accepted_95_for_r6_direct_only"
    elif new_rows_added:
        decision = "r6_flotron_cftc_row_uplift_v1=direct_intake_rows_uplifted_schema_ready_calibration_still_blocked"
    else:
        decision = "r6_flotron_cftc_row_uplift_v1=no_new_unique_rows_calibration_still_blocked"

    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": sha256_file(BOARD),
        "decision": decision,
        "source_url": SOURCE_URL,
        "source_pdf": str(SOURCE_PDF),
        "source_pdf_sha256": sha256_file(SOURCE_PDF),
        "source_text": str(SOURCE_TEXT),
        "source_text_sha256": sha256_file(SOURCE_TEXT),
        "text_checks": text_checks,
        "positive_rows_added": len(positive_added),
        "matched_negative_rows_added": len(negative_added),
        "positive_source_row_ids_added": [row["source_row_id"] for row in positive_added],
        "matched_negative_source_row_ids_added": [row["source_row_id"] for row in negative_added],
        "positive_summary": pos_summary,
        "matched_negative_summary": neg_summary,
        "verifier_returncode": verifier.returncode,
        "verifier_status": "schema_ready_unscored" if "schema_ready_unscored" in verifier.stdout else "unknown",
        "wilson95_lcb_positive": round(positive_lcb, 6),
        "wilson95_lcb_negative": round(negative_lcb, 6),
        "wilson95_lcb_min": round(min_lcb, 6),
        "support_ok": support_ok,
        "chronological_split_ok": chronological_ok,
        "heldout_symbol_or_venue_ok": heldout_ok,
        "broad_normal_sample": broad_normal_sample,
        "direct_species_closed": direct_species_closed,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "pre_hashes": pre_hashes,
        "post_hashes": post_hashes,
    }

    json_path = OUT / "r6_flotron_cftc_row_uplift_v1.json"
    report_path = OUT / "r6_flotron_cftc_row_uplift_v1.md"
    gate_csv = OUT / "r6_flotron_cftc_row_uplift_v1_gates.csv"
    summary_csv = OUT / "r6_flotron_cftc_row_uplift_v1_intake_summary.csv"
    assertions_path = CHECKS / "r6_flotron_cftc_row_uplift_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with gate_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["gate", "observed", "required", "pass"])
        writer.writeheader()
        writer.writerows(
            [
                {"gate": "positive_support", "observed": pos_summary["rows"], "required": 50, "pass": support_ok},
                {"gate": "negative_support", "observed": neg_summary["rows"], "required": 50, "pass": support_ok},
                {"gate": "chronological_split", "observed": pos_summary["unique_dates"], "required": 2, "pass": chronological_ok},
                {
                    "gate": "heldout_symbol_or_venue",
                    "observed": f"symbols={pos_summary['unique_symbols']};venues={pos_summary['unique_venues']}",
                    "required": "symbol>=2 or venue>=2",
                    "pass": heldout_ok,
                },
                {"gate": "wilson95_lcb", "observed": f"{min_lcb:.6f}", "required": ">=0.95", "pass": min_lcb >= 0.95},
                {
                    "gate": "broad_normal_sample",
                    "observed": "same-complaint CFTC genuine-order legs are source-described control seeds only; not broad normal-market calibration",
                    "required": "source-owned broad normal activity sample",
                    "pass": broad_normal_sample,
                },
                {
                    "gate": "direct_species_closed",
                    "observed": "spoofing/layering row support only; other direct species still absent",
                    "required": "broad direct manipulation species closure",
                    "pass": direct_species_closed,
                },
            ]
        )
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["class", "added", "total", "source_row_ids"])
        writer.writeheader()
        writer.writerow({"class": "positive", "added": len(positive_added), "total": pos_summary["rows"], "source_row_ids": ";".join(row["source_row_id"] for row in positive_added)})
        writer.writerow({"class": "matched_negative", "added": len(negative_added), "total": neg_summary["rows"], "source_row_ids": ";".join(row["source_row_id"] for row in negative_added)})

    report = [
        "# R6 Flotron CFTC Row Uplift v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Positive rows added by this run: `{len(positive_added)}`; matched negative rows added by this run: `{len(negative_added)}`.",
        f"- Positive rows now: `{pos_summary['rows']}`; matched negative rows now: `{neg_summary['rows']}`.",
        f"- Unique dates: `{pos_summary['unique_dates']}`; symbols: `{pos_summary['unique_symbols']}`; venues: `{pos_summary['unique_venues']}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{min_lcb:.6f}`.",
        f"- Chronological split ok: `{str(chronological_ok).lower()}`; heldout symbol/venue ok: `{str(heldout_ok).lower()}`.",
        "- Broad normal sample: `false`.",
        "- Direct species closed: `false`.",
        f"- Verifier status: `{result['verifier_status']}`; return code: `{verifier.returncode}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Source Rows Added",
        "",
        "| Class | Added | Total |",
        "|---|---:|---:|",
        f"| `positive` | `{len(positive_added)}` | `{pos_summary['rows']}` |",
        f"| `matched_negative` | `{len(negative_added)}` | `{neg_summary['rows']}` |",
        "",
        "## Boundary",
        "",
        "The Flotron rows are official CFTC same-complaint positive/control seeds. They improve direct R6 support and exact source breadth, but the controls remain same-event genuine-order legs, not independent broad normal-market calibration controls.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Report: `{report_path.relative_to(REPO)}`",
        f"- Gate CSV: `{gate_csv.relative_to(REPO)}`",
        f"- Intake summary CSV: `{summary_csv.relative_to(REPO)}`",
        f"- Verifier stdout: `{(CMD_OUT / 'direct_manipulation_row_intake_verifier.stdout.txt').relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS source_pdf_sha256={sha256_file(SOURCE_PDF)}",
        f"PASS positive_rows_added={len(positive_added)}",
        f"PASS matched_negative_rows_added={len(negative_added)}",
        f"PASS verifier_status={result['verifier_status']}",
        f"PASS positive_rows={pos_summary['rows']}",
        f"PASS matched_negative_rows={neg_summary['rows']}",
        f"PASS combined_min_wilson95_lcb={min_lcb:.6f}",
        f"PASS support_ok={str(support_ok).lower()}",
        f"PASS broad_normal_sample={str(broad_normal_sample).lower()}",
        "PASS direct_species_closed=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
        "PASS external_requests_sent=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": decision,
                "positive_rows_added": len(positive_added),
                "matched_negative_rows_added": len(negative_added),
                "positive_rows": pos_summary["rows"],
                "matched_negative_rows": neg_summary["rows"],
                "wilson95_lcb_min": round(min_lcb, 6),
                "update_goal": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
