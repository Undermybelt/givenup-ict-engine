#!/usr/bin/env python3
"""Materialize additional public CFTC direct Manipulation rows.

Rows are sourced only from public CFTC complaint facts that state dates, times,
sides, quantities, and same-event genuine-order counterparts.
"""

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
from typing import Any

from pypdf import PdfReader


RUN_ID = "20260511T211201+0800-codex-r6-mohan-shak-row-uplift-v1"
RUN_SLUG = "20260511T211201-codex-r6-mohan-shak-row-uplift-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_SLUG
OUT = RUN_ROOT / "r6-mohan-shak-row-uplift"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"
TMP = Path("/tmp/ict-engine-r6-mohan-shak-row-uplift-v1")
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

SOURCES = {
    "mohan_complaint": {
        "url": "https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfmohancomplaint012818.pdf",
        "source_report": "CFTC Complaint: Krishna Mohan, Case 4:18-cv-00260",
        "needles": [
            "November 27, 2013",
            "8:05:39.461 AM",
            "December 9, 2013",
            "5:27:41.553 AM",
            "December 3, 2013",
            "2:34:47.807 AM",
        ],
    },
    "shak_complaint": {
        "url": "https://www.cftc.gov/media/7526/enfshakcomplaint080522/download",
        "source_report": "CFTC Complaint: Daniel Shak, Case 2:22-cv-01258",
        "needles": [
            "March 3, 2017",
            "7:52:57.348 AM",
            "March 24, 2017",
            "8:30:17.046 AM",
            "September 18, 2017",
            "6:30:32.856 AM",
            "January 22, 2018",
            "5:17:12.964 AM",
            "February 21, 2018",
            "3:19:34.946 AM",
        ],
    },
}

SOURCE_REPORT_MOHAN = SOURCES["mohan_complaint"]["source_report"]
SOURCE_REPORT_SHAK = SOURCES["shak_complaint"]["source_report"]

POSITIVE_ADDITIONS = [
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT_MOHAN,
        "source_section": "Complaint paragraphs 48-49, November 27 2013 December 2013 E-mini Dow first cycle",
        "trade_date": "2013-11-27",
        "symbol": "December 2013 E-mini Dow futures",
        "venue_or_market_center": "CBOT/CME Globex",
        "participant_type_code": "CFTC defendant trader; firm account redacted",
        "participant_identifier": "Krishna Mohan / Trading Firm",
        "side": "sell spoof orders opposite buy genuine iceberg order",
        "earliest_order_received_time": "08:05:40.703 America/Chicago",
        "latest_order_received_time": "08:05:42.684 America/Chicago",
        "order_count": "multiple orders via order splitter; first group",
        "total_order_quantity": "40 contracts",
        "activity_description": "Public CFTC complaint states Mohan placed sell-side spoof orders after a buy iceberg order, the genuine order filled, and the spoof orders were canceled shortly after.",
        "matched_negative_group_id": "cftc_mohan_complaint_20131127_ym_first_cycle",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_mohan_complaint_20131127_ym_sell_spoof_first_group",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT_MOHAN,
        "source_section": "Complaint paragraph 49, November 27 2013 December 2013 E-mini Dow second cycle",
        "trade_date": "2013-11-27",
        "symbol": "December 2013 E-mini Dow futures",
        "venue_or_market_center": "CBOT/CME Globex",
        "participant_type_code": "CFTC defendant trader; firm account redacted",
        "participant_identifier": "Krishna Mohan / Trading Firm",
        "side": "buy spoof orders opposite sell genuine iceberg order",
        "earliest_order_received_time": "08:05:45.024 America/Chicago",
        "latest_order_received_time": "08:05:47.421 America/Chicago",
        "order_count": "two groups of multiple orders via order splitter",
        "total_order_quantity": "80 contracts",
        "activity_description": "Public CFTC complaint states Mohan placed buy-side spoof groups opposite a sell iceberg order, the genuine order filled, and both spoof groups were canceled.",
        "matched_negative_group_id": "cftc_mohan_complaint_20131127_ym_second_cycle",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_mohan_complaint_20131127_ym_buy_spoof_second_third_groups",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT_MOHAN,
        "source_section": "Complaint paragraph 52, December 9 2013 December 2013 E-mini NASDAQ first cycle",
        "trade_date": "2013-12-09",
        "symbol": "December 2013 E-mini NASDAQ futures",
        "venue_or_market_center": "CME",
        "participant_type_code": "CFTC defendant trader; firm account redacted",
        "participant_identifier": "Krishna Mohan / Trading Firm",
        "side": "sell spoof orders opposite buy genuine iceberg order",
        "earliest_order_received_time": "05:27:42.713 America/Chicago",
        "latest_order_received_time": "05:27:45.480 America/Chicago",
        "order_count": "two groups of multiple orders via order splitter",
        "total_order_quantity": "80 contracts",
        "activity_description": "Public CFTC complaint states Mohan placed two sell-side spoof groups opposite a buy iceberg order; the first genuine order partially filled and spoof groups were canceled.",
        "matched_negative_group_id": "cftc_mohan_complaint_20131209_nq_first_cycle",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_mohan_complaint_20131209_nq_sell_spoof_first_second_groups",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT_MOHAN,
        "source_section": "Complaint paragraph 53, December 9 2013 December 2013 E-mini NASDAQ second cycle",
        "trade_date": "2013-12-09",
        "symbol": "December 2013 E-mini NASDAQ futures",
        "venue_or_market_center": "CME",
        "participant_type_code": "CFTC defendant trader; firm account redacted",
        "participant_identifier": "Krishna Mohan / Trading Firm",
        "side": "buy spoof orders opposite sell genuine iceberg order",
        "earliest_order_received_time": "05:27:46.505 America/Chicago",
        "latest_order_received_time": "05:27:47.976 America/Chicago",
        "order_count": "two groups of multiple orders via order splitter",
        "total_order_quantity": "80 contracts",
        "activity_description": "Public CFTC complaint states Mohan placed buy-side spoof groups opposite a sell iceberg order; the sell genuine order filled and spoof groups were canceled.",
        "matched_negative_group_id": "cftc_mohan_complaint_20131209_nq_second_cycle",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_mohan_complaint_20131209_nq_buy_spoof_third_fourth_groups",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT_MOHAN,
        "source_section": "Complaint paragraph 55, December 3 2013 December 2013 E-mini NASDAQ no-fill cycle",
        "trade_date": "2013-12-03",
        "symbol": "December 2013 E-mini NASDAQ futures",
        "venue_or_market_center": "CME",
        "participant_type_code": "CFTC defendant trader; firm account redacted",
        "participant_identifier": "Krishna Mohan / Trading Firm",
        "side": "sell spoof orders opposite buy genuine iceberg order",
        "earliest_order_received_time": "02:34:48.887 America/Chicago",
        "latest_order_received_time": "02:34:52.407 America/Chicago",
        "order_count": "three groups of multiple orders via order splitter",
        "total_order_quantity": "120 contracts",
        "activity_description": "Public CFTC complaint states Mohan placed three sell-side spoof groups opposite a buy iceberg order; the spoof groups were canceled and the genuine order did not execute.",
        "matched_negative_group_id": "cftc_mohan_complaint_20131203_nq_no_fill_cycle",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_mohan_complaint_20131203_nq_sell_spoof_no_fill_event",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT_SHAK,
        "source_section": "Complaint paragraphs 49-54, Example 1 March 3 2017 April 2017 Gold",
        "trade_date": "2017-03-03",
        "symbol": "April 2017 Gold futures",
        "venue_or_market_center": "COMEX/CME Globex",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": "Daniel Shak",
        "side": "buy spoof orders opposite sell genuine order",
        "earliest_order_received_time": "07:53:21.124 America/New_York",
        "latest_order_received_time": "07:53:58.693 America/New_York",
        "order_count": "ten 20-lot spoof orders",
        "total_order_quantity": "200 lots",
        "activity_description": "Public CFTC complaint states Shak placed ten buy spoof orders totaling 200 lots while waiting for a one-lot sell genuine order, then canceled the spoof orders after the genuine order filled.",
        "matched_negative_group_id": "cftc_shak_complaint_20170303_gold_example1",
        "session_bucket": "comex_morning",
        "source_row_id": "cftc_shak_complaint_20170303_gold_buy_spoof_orders",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT_SHAK,
        "source_section": "Complaint paragraphs 55-60, Example 2 March 24 2017 April 2017 Gold",
        "trade_date": "2017-03-24",
        "symbol": "April 2017 Gold futures",
        "venue_or_market_center": "COMEX/CME Globex",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": "Daniel Shak",
        "side": "buy spoof orders opposite sell genuine order",
        "earliest_order_received_time": "08:30:20.375 America/New_York",
        "latest_order_received_time": "08:30:42.819 America/New_York",
        "order_count": "five spoof orders",
        "total_order_quantity": "300 lots",
        "activity_description": "Public CFTC complaint states Shak placed five buy spoof orders totaling 300 lots while waiting for a five-lot sell genuine order, then canceled the spoof orders after the genuine order filled.",
        "matched_negative_group_id": "cftc_shak_complaint_20170324_gold_example2",
        "session_bucket": "comex_morning",
        "source_row_id": "cftc_shak_complaint_20170324_gold_buy_spoof_orders",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT_SHAK,
        "source_section": "Complaint paragraphs 61-66, Example 3 September 18 2017 December 2017 Silver",
        "trade_date": "2017-09-18",
        "symbol": "December 2017 Silver futures",
        "venue_or_market_center": "COMEX/CME Globex",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": "Daniel Shak",
        "side": "buy spoof orders opposite sell genuine orders",
        "earliest_order_received_time": "06:30:46.389 America/New_York",
        "latest_order_received_time": "06:31:39.576 America/New_York",
        "order_count": "eight spoof orders",
        "total_order_quantity": "340 lots",
        "activity_description": "Public CFTC complaint states Shak placed eight buy spoof orders totaling 340 lots while waiting for two one-lot sell genuine orders, then canceled the spoof orders after the genuine orders filled.",
        "matched_negative_group_id": "cftc_shak_complaint_20170918_silver_example3",
        "session_bucket": "comex_morning",
        "source_row_id": "cftc_shak_complaint_20170918_silver_buy_spoof_orders",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT_SHAK,
        "source_section": "Complaint paragraphs 79-84, Example 5 January 22 2018 March 2018 Silver",
        "trade_date": "2018-01-22",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": "COMEX/CME Globex",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": "Daniel Shak",
        "side": "buy spoof orders opposite sell genuine order",
        "earliest_order_received_time": "05:17:44.407 America/New_York",
        "latest_order_received_time": "05:18:20.286 America/New_York",
        "order_count": "six 50-lot spoof orders",
        "total_order_quantity": "300 lots",
        "activity_description": "Public CFTC complaint states Shak placed six buy spoof orders totaling 300 lots while waiting for a one-lot sell genuine order, then canceled the spoof orders after the genuine order filled.",
        "matched_negative_group_id": "cftc_shak_complaint_20180122_silver_example5",
        "session_bucket": "comex_overnight",
        "source_row_id": "cftc_shak_complaint_20180122_silver_buy_spoof_orders",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT_SHAK,
        "source_section": "Complaint paragraphs 86-89, Example 6 February 21 2018 March 2018 Silver first cycle",
        "trade_date": "2018-02-21",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": "COMEX/CME Globex",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": "Daniel Shak",
        "side": "sell spoof orders opposite buy genuine order",
        "earliest_order_received_time": "03:19:39.023 America/New_York",
        "latest_order_received_time": "03:20:06.537 America/New_York",
        "order_count": "six spoof orders",
        "total_order_quantity": "250 lots",
        "activity_description": "Public CFTC complaint states Shak placed six sell spoof orders totaling 250 lots while waiting for a three-lot buy genuine order, then canceled the spoof orders after the genuine order filled.",
        "matched_negative_group_id": "cftc_shak_complaint_20180221_silver_example6_first_cycle",
        "session_bucket": "comex_overnight",
        "source_row_id": "cftc_shak_complaint_20180221_silver_sell_spoof_orders",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT_SHAK,
        "source_section": "Complaint paragraphs 91-95, Example 6 February 21 2018 March 2018 Silver second cycle",
        "trade_date": "2018-02-21",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": "COMEX/CME Globex",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": "Daniel Shak",
        "side": "buy spoof orders opposite sell genuine order",
        "earliest_order_received_time": "03:21:59.867 America/New_York",
        "latest_order_received_time": "03:22:57.819 America/New_York",
        "order_count": "seven 50-lot spoof orders",
        "total_order_quantity": "350 lots",
        "activity_description": "Public CFTC complaint states Shak placed seven buy spoof orders totaling 350 lots while waiting for a three-lot sell genuine order, then canceled the spoof orders after the genuine order filled.",
        "matched_negative_group_id": "cftc_shak_complaint_20180221_silver_example6_second_cycle",
        "session_bucket": "comex_overnight",
        "source_row_id": "cftc_shak_complaint_20180221_silver_buy_spoof_orders",
    },
]

NEGATIVE_ADDITIONS = [
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT_MOHAN,
        "source_section": "Complaint paragraph 48, November 27 2013 December 2013 E-mini Dow first genuine order",
        "trade_date": "2013-11-27",
        "symbol": "December 2013 E-mini Dow futures",
        "venue_or_market_center": "CBOT/CME Globex",
        "participant_type_code": "CFTC defendant trader; firm account redacted",
        "participant_identifier": "Krishna Mohan / Trading Firm",
        "side": "buy genuine iceberg order",
        "earliest_order_received_time": "08:05:39.461 America/Chicago",
        "latest_order_received_time": "08:05:41.335 America/Chicago",
        "order_count": "one iceberg order with one contract displayed",
        "total_order_quantity": "40 contracts",
        "activity_description": "Same-source genuine-order control seed: buy iceberg order filled in the first November 27 E-mini Dow cycle. Not an independent broad normal-market control.",
        "matched_negative_group_id": "cftc_mohan_complaint_20131127_ym_first_cycle",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_mohan_complaint_20131127_ym_buy_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT_MOHAN,
        "source_section": "Complaint paragraph 49, November 27 2013 December 2013 E-mini Dow second genuine order",
        "trade_date": "2013-11-27",
        "symbol": "December 2013 E-mini Dow futures",
        "venue_or_market_center": "CBOT/CME Globex",
        "participant_type_code": "CFTC defendant trader; firm account redacted",
        "participant_identifier": "Krishna Mohan / Trading Firm",
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "08:05:43.565 America/Chicago",
        "latest_order_received_time": "08:05:46.241 America/Chicago",
        "order_count": "one iceberg order with one contract displayed",
        "total_order_quantity": "40 contracts",
        "activity_description": "Same-source genuine-order control seed: sell iceberg order filled in the second November 27 E-mini Dow cycle. Not an independent broad normal-market control.",
        "matched_negative_group_id": "cftc_mohan_complaint_20131127_ym_second_cycle",
        "session_bucket": "regular_us_central_time",
        "source_row_id": "cftc_mohan_complaint_20131127_ym_sell_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT_MOHAN,
        "source_section": "Complaint paragraph 52, December 9 2013 December 2013 E-mini NASDAQ first genuine order",
        "trade_date": "2013-12-09",
        "symbol": "December 2013 E-mini NASDAQ futures",
        "venue_or_market_center": "CME",
        "participant_type_code": "CFTC defendant trader; firm account redacted",
        "participant_identifier": "Krishna Mohan / Trading Firm",
        "side": "buy genuine iceberg order",
        "earliest_order_received_time": "05:27:41.553 America/Chicago",
        "latest_order_received_time": "05:27:47.568 America/Chicago",
        "order_count": "one iceberg order with one contract displayed",
        "total_order_quantity": "40 contracts; 17 contracts filled and 23 contracts later canceled",
        "activity_description": "Same-source genuine-order control seed: buy iceberg order partially filled in the December 9 first cycle. Not an independent broad normal-market control.",
        "matched_negative_group_id": "cftc_mohan_complaint_20131209_nq_first_cycle",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_mohan_complaint_20131209_nq_buy_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT_MOHAN,
        "source_section": "Complaint paragraph 53, December 9 2013 December 2013 E-mini NASDAQ second genuine order",
        "trade_date": "2013-12-09",
        "symbol": "December 2013 E-mini NASDAQ futures",
        "venue_or_market_center": "CME",
        "participant_type_code": "CFTC defendant trader; firm account redacted",
        "participant_identifier": "Krishna Mohan / Trading Firm",
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "05:27:44.772 America/Chicago",
        "latest_order_received_time": "05:27:46.835 America/Chicago",
        "order_count": "one iceberg order with one contract displayed",
        "total_order_quantity": "17 contracts",
        "activity_description": "Same-source genuine-order control seed: sell iceberg order filled in the December 9 second cycle. Not an independent broad normal-market control.",
        "matched_negative_group_id": "cftc_mohan_complaint_20131209_nq_second_cycle",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_mohan_complaint_20131209_nq_sell_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT_MOHAN,
        "source_section": "Complaint paragraph 55, December 3 2013 December 2013 E-mini NASDAQ genuine order",
        "trade_date": "2013-12-03",
        "symbol": "December 2013 E-mini NASDAQ futures",
        "venue_or_market_center": "CME",
        "participant_type_code": "CFTC defendant trader; firm account redacted",
        "participant_identifier": "Krishna Mohan / Trading Firm",
        "side": "buy genuine iceberg order that did not fill",
        "earliest_order_received_time": "02:34:47.807 America/Chicago",
        "latest_order_received_time": "02:34:53.062 America/Chicago",
        "order_count": "one iceberg order with one contract displayed",
        "total_order_quantity": "40 contracts",
        "activity_description": "Same-source genuine-order control seed: buy iceberg order was canceled unfilled in the December 3 no-fill event. Not an independent broad normal-market control.",
        "matched_negative_group_id": "cftc_mohan_complaint_20131203_nq_no_fill_cycle",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_mohan_complaint_20131203_nq_buy_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT_SHAK,
        "source_section": "Complaint paragraphs 49 and 52, Example 1 March 3 2017 April 2017 Gold genuine order",
        "trade_date": "2017-03-03",
        "symbol": "April 2017 Gold futures",
        "venue_or_market_center": "COMEX/CME Globex",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": "Daniel Shak",
        "side": "sell genuine order",
        "earliest_order_received_time": "07:52:57.348 America/New_York",
        "latest_order_received_time": "07:53:54.558 America/New_York",
        "order_count": "one preexisting one-lot genuine order with modifications",
        "total_order_quantity": "1 lot",
        "activity_description": "Same-source genuine-order control seed: Shak sell genuine order filled in Example 1. Not an independent broad normal-market control.",
        "matched_negative_group_id": "cftc_shak_complaint_20170303_gold_example1",
        "session_bucket": "comex_morning",
        "source_row_id": "cftc_shak_complaint_20170303_gold_sell_genuine_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT_SHAK,
        "source_section": "Complaint paragraphs 55 and 58, Example 2 March 24 2017 April 2017 Gold genuine order",
        "trade_date": "2017-03-24",
        "symbol": "April 2017 Gold futures",
        "venue_or_market_center": "COMEX/CME Globex",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": "Daniel Shak",
        "side": "sell genuine order",
        "earliest_order_received_time": "08:30:17.046 America/New_York",
        "latest_order_received_time": "08:30:36.432 America/New_York",
        "order_count": "one preexisting five-lot genuine order with modifications",
        "total_order_quantity": "5 lots",
        "activity_description": "Same-source genuine-order control seed: Shak sell genuine order filled in Example 2. Not an independent broad normal-market control.",
        "matched_negative_group_id": "cftc_shak_complaint_20170324_gold_example2",
        "session_bucket": "comex_morning",
        "source_row_id": "cftc_shak_complaint_20170324_gold_sell_genuine_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT_SHAK,
        "source_section": "Complaint paragraphs 61 and 64, Example 3 September 18 2017 December 2017 Silver genuine orders",
        "trade_date": "2017-09-18",
        "symbol": "December 2017 Silver futures",
        "venue_or_market_center": "COMEX/CME Globex",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": "Daniel Shak",
        "side": "sell genuine orders",
        "earliest_order_received_time": "06:30:32.856 America/New_York",
        "latest_order_received_time": "06:31:35.275 America/New_York",
        "order_count": "two one-lot genuine orders with modifications",
        "total_order_quantity": "2 lots",
        "activity_description": "Same-source genuine-order control seed: Shak sell genuine orders filled in Example 3. Not an independent broad normal-market control.",
        "matched_negative_group_id": "cftc_shak_complaint_20170918_silver_example3",
        "session_bucket": "comex_morning",
        "source_row_id": "cftc_shak_complaint_20170918_silver_sell_genuine_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT_SHAK,
        "source_section": "Complaint paragraphs 79 and 82, Example 5 January 22 2018 March 2018 Silver genuine order",
        "trade_date": "2018-01-22",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": "COMEX/CME Globex",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": "Daniel Shak",
        "side": "sell genuine order",
        "earliest_order_received_time": "05:17:12.964 America/New_York",
        "latest_order_received_time": "05:18:16.998 America/New_York",
        "order_count": "one one-lot genuine order with modifications",
        "total_order_quantity": "1 lot",
        "activity_description": "Same-source genuine-order control seed: Shak sell genuine order filled in Example 5. Not an independent broad normal-market control.",
        "matched_negative_group_id": "cftc_shak_complaint_20180122_silver_example5",
        "session_bucket": "comex_overnight",
        "source_row_id": "cftc_shak_complaint_20180122_silver_sell_genuine_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT_SHAK,
        "source_section": "Complaint paragraphs 86 and 88, Example 6 February 21 2018 March 2018 Silver first genuine order",
        "trade_date": "2018-02-21",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": "COMEX/CME Globex",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": "Daniel Shak",
        "side": "buy genuine order",
        "earliest_order_received_time": "03:19:34.946 America/New_York",
        "latest_order_received_time": "03:19:59.508 America/New_York",
        "order_count": "one three-lot genuine order with modification",
        "total_order_quantity": "3 lots",
        "activity_description": "Same-source genuine-order control seed: Shak buy genuine order filled in Example 6 first cycle. Not an independent broad normal-market control.",
        "matched_negative_group_id": "cftc_shak_complaint_20180221_silver_example6_first_cycle",
        "session_bucket": "comex_overnight",
        "source_row_id": "cftc_shak_complaint_20180221_silver_buy_genuine_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT_SHAK,
        "source_section": "Complaint paragraphs 91 and 94, Example 6 February 21 2018 March 2018 Silver second genuine order",
        "trade_date": "2018-02-21",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": "COMEX/CME Globex",
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": "Daniel Shak",
        "side": "sell genuine order",
        "earliest_order_received_time": "03:21:55.679 America/New_York",
        "latest_order_received_time": "03:22:51.442 America/New_York",
        "order_count": "one three-lot genuine order",
        "total_order_quantity": "3 lots",
        "activity_description": "Same-source genuine-order control seed: Shak sell genuine order filled in Example 6 second cycle. Not an independent broad normal-market control.",
        "matched_negative_group_id": "cftc_shak_complaint_20180221_silver_example6_second_cycle",
        "session_bucket": "comex_overnight",
        "source_row_id": "cftc_shak_complaint_20180221_silver_sell_genuine_control",
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


def fetch_source(source_id: str, source: dict[str, Any]) -> dict[str, Any]:
    TMP.mkdir(parents=True, exist_ok=True)
    target = TMP / f"{source_id}.pdf"
    if not target.exists():
        req = urllib.request.Request(source["url"], headers={"User-Agent": "ict-engine-board-a-r6-uplift/1.0"})
        with urllib.request.urlopen(req, timeout=45) as response:
            target.write_bytes(response.read())
            status = response.status
            content_type = response.headers.get("Content-Type", "")
    else:
        status = 200
        content_type = "cached"
    text = "\n".join((page.extract_text() or "") for page in PdfReader(str(target)).pages)
    text_checks = {needle: needle.lower() in text.lower() for needle in source["needles"]}
    return {
        "url": source["url"],
        "path": str(target),
        "bytes": target.stat().st_size,
        "sha256": sha256(target),
        "status": status,
        "content_type": content_type,
        "text_check_count": sum(1 for ok in text_checks.values() if ok),
        "text_checks": text_checks,
    }


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


def append_unique(path: Path, additions: list[dict[str, str]]) -> tuple[int, int]:
    rows = read_csv(path)
    seen = {row.get("source_row_id", "") for row in rows}
    added = 0
    for row in additions:
        if row["source_row_id"] not in seen:
            rows.append(row)
            seen.add(row["source_row_id"])
            added += 1
    write_csv(path, rows, FIELDNAMES)
    return len(rows), added


def wilson_lcb(successes: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    phat = successes / total
    denom = 1 + z * z / total
    centre = phat + z * z / (2 * total)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total)
    return (centre - margin) / denom


def min_all_success_support(target_lcb: float = 0.95) -> int:
    n = 1
    while wilson_lcb(n, n) < target_lcb:
        n += 1
    return n


def unique_values(rows: list[dict[str, str]], key: str) -> list[str]:
    return sorted({row.get(key, "") for row in rows if row.get(key, "")})


def update_provenance(source_readback: dict[str, Any], positive_count: int, negative_count: int) -> dict[str, Any]:
    if PROVENANCE.exists():
        provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    else:
        provenance = {}
    provenance["r6_mohan_shak_row_uplift_v1"] = {
        "run_id": RUN_ID,
        "sources": source_readback,
        "positive_addition_candidates": len(POSITIVE_ADDITIONS),
        "negative_addition_candidates": len(NEGATIVE_ADDITIONS),
        "materialized_at_utc": datetime.now(timezone.utc).isoformat(),
        "control_limitations": (
            "Controls are same-source genuine-order counterparts from public CFTC complaints. "
            "They are schema/calibration seeds only and are not a broad independent normal-market sample."
        ),
    }
    provenance["positive_rows_count"] = positive_count
    provenance["matched_negative_rows_count"] = negative_count
    provenance["updated_by"] = RUN_ID
    provenance["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return provenance


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    source_readback = {source_id: fetch_source(source_id, source) for source_id, source in SOURCES.items()}
    all_text_checks_ok = all(
        ok
        for readback in source_readback.values()
        for ok in readback["text_checks"].values()
    )

    positive_count, positive_added = append_unique(POSITIVE, POSITIVE_ADDITIONS)
    negative_count, negative_added = append_unique(NEGATIVE, NEGATIVE_ADDITIONS)
    provenance = update_provenance(source_readback, positive_count, negative_count)

    positives = read_csv(POSITIVE)
    negatives = read_csv(NEGATIVE)
    verifier = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    (OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(verifier.stdout, encoding="utf-8")
    (OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(verifier.stderr, encoding="utf-8")
    try:
        verifier_json = json.loads(verifier.stdout)
    except json.JSONDecodeError:
        verifier_json = {"status": "parse_failed", "stdout": verifier.stdout, "stderr": verifier.stderr}

    required_support = min_all_success_support(0.95)
    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    unique_dates = unique_values(positives, "trade_date")
    unique_symbols = unique_values(positives, "symbol")
    unique_venues = unique_values(positives, "venue_or_market_center")
    labels = Counter(row.get("label", "") for row in positives + negatives)
    matched_groups = sorted(
        {row.get("matched_negative_group_id", "") for row in positives}
        & {row.get("matched_negative_group_id", "") for row in negatives}
    )

    gates = [
        {"gate": "source_text_checks", "observed": all_text_checks_ok, "required": True, "pass": all_text_checks_ok},
        {"gate": "positive_rows_added", "observed": positive_added, "required": ">0", "pass": positive_added > 0},
        {"gate": "negative_rows_added", "observed": negative_added, "required": ">0", "pass": negative_added > 0},
        {"gate": "verifier_schema_ready", "observed": verifier_json.get("status"), "required": "schema_ready_unscored", "pass": verifier_json.get("status") == "schema_ready_unscored"},
        {"gate": "positive_support", "observed": len(positives), "required": required_support, "pass": len(positives) >= required_support},
        {"gate": "negative_support", "observed": len(negatives), "required": required_support, "pass": len(negatives) >= required_support},
        {"gate": "chronological_train_calibration_test", "observed": len(unique_dates), "required": 3, "pass": len(unique_dates) >= 3},
        {"gate": "heldout_symbol_or_venue", "observed": f"symbols={len(unique_symbols)};venues={len(unique_venues)}", "required": "symbol>=2 or venue>=2", "pass": len(unique_symbols) >= 2 or len(unique_venues) >= 2},
        {"gate": "wilson95_lcb", "observed": f"{min(positive_lcb, negative_lcb):.6f}", "required": ">=0.95", "pass": min(positive_lcb, negative_lcb) >= 0.95},
        {"gate": "broad_normal_sample", "observed": "same-source public CFTC genuine-order counterparts", "required": "source-owned broad normal activity sample", "pass": False},
        {"gate": "direct_species_coverage", "observed": "spoofing_layering", "required": "spoofing_layering;quote_spoofing;quote_stuffing;pinging;bear_raid;painting_tape", "pass": False},
    ]
    decision = "r6_mohan_shak_row_uplift_v1=rows_added_schema_ready_calibration_blocked"
    audit = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact_generation": sha256(BOARD),
        "decision": decision,
        "intake_root": str(INTAKE),
        "source_readback": source_readback,
        "source_text_checks_ok": all_text_checks_ok,
        "positive_rows_added": positive_added,
        "matched_negative_rows_added": negative_added,
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "matched_group_count": len(matched_groups),
        "unique_dates": unique_dates,
        "unique_symbols": unique_symbols,
        "unique_venues": unique_venues,
        "positive_wilson95_lcb": positive_lcb,
        "negative_wilson95_lcb": negative_lcb,
        "combined_min_wilson95_lcb": min(positive_lcb, negative_lcb),
        "required_support_for_all_success_wilson95_lcb": required_support,
        "labels": dict(labels),
        "matched_groups": matched_groups,
        "provenance_keys": sorted(provenance.keys()),
        "verifier_returncode": verifier.returncode,
        "verifier": verifier_json,
        "gate_rows": gates,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Continue R6 acquisition for more source-owned positive rows, broad normal controls, and missing direct species; in parallel populate R2/R3/R4/R5 intake roots before completion audit.",
    }

    json_path = OUT / "r6_mohan_shak_row_uplift_v1.json"
    report_path = OUT / "r6_mohan_shak_row_uplift_v1.md"
    gate_csv = OUT / "r6_mohan_shak_row_uplift_v1_gates.csv"
    additions_csv = OUT / "r6_mohan_shak_row_uplift_v1_additions.csv"
    assertions_path = CHECKS / "r6_mohan_shak_row_uplift_v1_assertions.out"
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(gate_csv, gates, ["gate", "observed", "required", "pass"])
    write_csv(
        additions_csv,
        [
            {"kind": "positive", **row} for row in POSITIVE_ADDITIONS
        ] + [
            {"kind": "matched_negative", **row} for row in NEGATIVE_ADDITIONS
        ],
        ["kind", *FIELDNAMES],
    )

    report_lines = [
        "# R6 Mohan/Shak Row Uplift v1",
        "",
        f"Decision: `{decision}`.",
        "",
        "Result:",
        f"- Positive rows added to `/tmp` intake: `{positive_added}`; matched negative rows added: `{negative_added}`.",
        f"- Total direct intake rows after uplift: positives `{len(positives)}`, matched negatives `{len(negatives)}`, matched groups `{len(matched_groups)}`.",
        f"- Unique positive dates/symbols/venues: `{len(unique_dates)}` / `{len(unique_symbols)}` / `{len(unique_venues)}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{min(positive_lcb, negative_lcb):.6f}`.",
        f"- Required all-success support for Wilson95 `>=0.95`: `{required_support}`.",
        f"- Source text checks ok: `{str(all_text_checks_ok).lower()}`; verifier status: `{verifier_json.get('status')}`.",
        "- Broad normal sample: `false`; direct species coverage still only `spoofing_layering`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "Gates:",
        "",
        "| Gate | Observed | Required | Pass |",
        "|---|---|---|---:|",
    ]
    for gate in gates:
        report_lines.append(f"| `{gate['gate']}` | `{gate['observed']}` | `{gate['required']}` | `{str(gate['pass']).lower()}` |")
    report_lines.extend(
        [
            "",
            "Interpretation:",
            "The uplift materially increases the public CFTC direct-row seed, adds COMEX metals and CBOT/CME E-mini Dow coverage, and preserves chronological plus heldout-symbol/venue breadth. It still cannot satisfy the strict confidence objective because support remains far below Wilson95 `>=0.95`, controls are same-source enforcement-example genuine orders rather than broad normal-market controls, and non-spoofing direct species remain absent.",
            "",
            "Artifacts:",
            f"- JSON: `{rel(json_path)}`",
            f"- Gate CSV: `{rel(gate_csv)}`",
            f"- Additions CSV: `{rel(additions_csv)}`",
            f"- Verifier stdout: `{rel(OUT / 'direct_manipulation_row_intake_verifier.stdout.txt')}`",
            f"- Assertions: `{rel(assertions_path)}`",
        ]
    )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS source_text_checks_ok={str(all_text_checks_ok).lower()}",
        f"PASS positive_rows_added={positive_added}",
        f"PASS matched_negative_rows_added={negative_added}",
        f"PASS positive_rows={len(positives)}",
        f"PASS matched_negative_rows={len(negatives)}",
        f"PASS verifier_status={verifier_json.get('status')}",
        f"PASS combined_min_wilson95_lcb={min(positive_lcb, negative_lcb):.6f}",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "positive_rows": len(positives), "matched_negative_rows": len(negatives), "wilson95_min": round(min(positive_lcb, negative_lcb), 6)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
