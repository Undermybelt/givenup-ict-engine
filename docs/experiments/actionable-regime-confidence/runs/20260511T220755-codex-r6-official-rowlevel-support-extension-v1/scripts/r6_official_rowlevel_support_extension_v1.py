#!/usr/bin/env python3
"""Append source-backed official row-level R6 examples without relaxing gates."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T220755+0800-codex-r6-official-rowlevel-support-extension-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T220755-codex-r6-official-rowlevel-support-extension-v1"
OUT_DIR = RUN_ROOT / "r6-official-rowlevel-support-extension"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
RAW_DIR = Path("/tmp/ict-engine-r6-official-rowlevel-support-extension-v1/raw")

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"
DIRECT_VERIFIER = REPO / (
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

SOURCES = [
    {
        "id": "roman_banoczay_complaint",
        "url": "https://www.cftc.gov/media/4831/enfromancomplaint092920/download",
        "title": "CFTC Complaint: CFTC v. Roman/Banoczay et al., Case 1:20-cv-05777",
        "checks": [
            "Event Example 1:  January 25, 2018",
            "06:31:45.692",
            "Event Example 2:  February 1, 2018",
            "02:10:35.632",
            "Event Example 3:  February 12, 2018",
            "03:02:13.105",
            "03:02:22.251",
        ],
    },
    {
        "id": "logista_serotta_complaint",
        "url": "https://www.cftc.gov/media/9206/enflogistaadvisorscomplaint090723/download",
        "title": "CFTC Complaint: CFTC v. Logista Advisors LLC and Nicholas Serotta, Case 1:23-cv-07485",
        "checks": [
            "Spoof Event Example 1: January 29, 2020",
            "12:00:06.610 PM",
            "Spoof Event Example 2: February 20, 2020",
            "1:06:29.086 PM",
            "Spoof Event Example 3: March 11, 2020",
            "11:29:48.415 AM",
            "10:56:22.803",
            "8:23",
        ],
    },
]


def row(**kwargs: str) -> dict[str, str]:
    return {field: kwargs.get(field, "") for field in FIELDS}


POSITIVE_ADDITIONS = [
    row(
        label="positive_spoofing_layering",
        source_report=SOURCES[0]["title"],
        source_section="Paragraphs 51-55, Event Example 1: January 25 2018",
        trade_date="2018-01-25",
        symbol="March 2018 Crude Oil futures",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader; federal complaint",
        participant_identifier="Andras Banoczay / Roman et al.",
        side="sell layered spoof orders opposite buy genuine order",
        earliest_order_received_time="06:31:45.692 America/Chicago",
        latest_order_received_time="06:31:56.953 America/Chicago",
        order_count="nine layered spoof orders",
        total_order_quantity="360 crude oil futures contracts",
        activity_description="CFTC complaint describes nine 40-lot sell layered spoof orders entered after the buy genuine order was finalized; the genuine order filled and the remaining spoof orders were canceled within seconds without fills.",
        matched_negative_group_id="cftc_roman_banoczay_20180125_cl_buy_genuine_sell_layered_spoof_example",
        session_bucket="overnight_central_time",
        source_row_id="cftc_roman_banoczay_20180125_cl_sell_layered_spoof_orders",
    ),
    row(
        label="positive_spoofing_layering",
        source_report=SOURCES[0]["title"],
        source_section="Paragraphs 57-61, Event Example 2: February 1 2018",
        trade_date="2018-02-01",
        symbol="March 2018 Crude Oil futures",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader; federal complaint",
        participant_identifier="Andras Banoczay / Roman et al.",
        side="sell layered spoof orders opposite buy genuine order",
        earliest_order_received_time="02:10:35.632 America/Chicago",
        latest_order_received_time="02:10:46.265 America/Chicago",
        order_count="twelve layered spoof orders",
        total_order_quantity="480 crude oil futures contracts",
        activity_description="CFTC complaint describes twelve 40-lot sell layered spoof orders entered after the buy genuine order was modified; the genuine order fully filled and the spoof offers were canceled without fills.",
        matched_negative_group_id="cftc_roman_banoczay_20180201_cl_buy_genuine_sell_layered_spoof_example",
        session_bucket="overnight_central_time",
        source_row_id="cftc_roman_banoczay_20180201_cl_sell_layered_spoof_orders",
    ),
    row(
        label="positive_spoofing_layering",
        source_report=SOURCES[0]["title"],
        source_section="Paragraphs 63-68, Event Example 3 first leg: February 12 2018",
        trade_date="2018-02-12",
        symbol="March 2018 Crude Oil futures",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader; federal complaint",
        participant_identifier="Andras Banoczay / Roman et al.",
        side="buy layered spoof orders opposite sell genuine order",
        earliest_order_received_time="03:02:13.105 America/Chicago",
        latest_order_received_time="03:02:21.233 America/Chicago",
        order_count="eight layered spoof orders",
        total_order_quantity="320 crude oil futures contracts",
        activity_description="CFTC complaint describes eight 40-lot buy layered spoof orders used to put upward pressure on price before a 40-lot aggressive sell genuine order filled; the spoof bids were canceled within seconds without fills.",
        matched_negative_group_id="cftc_roman_banoczay_20180212_cl_sell_genuine_buy_layered_spoof_leg",
        session_bucket="overnight_central_time",
        source_row_id="cftc_roman_banoczay_20180212_cl_buy_layered_spoof_orders_first_leg",
    ),
    row(
        label="positive_spoofing_layering",
        source_report=SOURCES[0]["title"],
        source_section="Paragraphs 69-75, Event Example 3 second leg: February 12 2018",
        trade_date="2018-02-12",
        symbol="March 2018 Crude Oil futures",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader; federal complaint",
        participant_identifier="Andras Banoczay / Roman et al.",
        side="sell layered spoof orders opposite buy genuine order",
        earliest_order_received_time="03:02:22.251 America/Chicago",
        latest_order_received_time="03:02:29.508 America/Chicago",
        order_count="eight layered spoof orders",
        total_order_quantity="320 crude oil futures contracts",
        activity_description="CFTC complaint describes eight 40-lot sell layered spoof orders used to put downward pressure on price before a 40-lot aggressive buy genuine order filled; the spoof offers were canceled within seconds without fills.",
        matched_negative_group_id="cftc_roman_banoczay_20180212_cl_buy_genuine_sell_layered_spoof_leg",
        session_bucket="overnight_central_time",
        source_row_id="cftc_roman_banoczay_20180212_cl_sell_layered_spoof_orders_second_leg",
    ),
    row(
        label="positive_spoofing_layering",
        source_report=SOURCES[1]["title"],
        source_section="Paragraphs 70-73, Spoof Event Example 1: January 29 2020",
        trade_date="2020-01-29",
        symbol="CLM0-CLU0 crude oil June-September 2020 calendar spread",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader/advisor; federal complaint",
        participant_identifier="Nicholas Serotta / Logista Advisors LLC",
        side="sell spoof order opposite buy genuine orders",
        earliest_order_received_time="12:00:06.610 America/Chicago",
        latest_order_received_time="12:00:23.225 America/Chicago",
        order_count="one large spoof order",
        total_order_quantity="301 calendar-spread contracts",
        activity_description="CFTC complaint describes a 301-contract sell spoof order at the second-best offer; buy genuine orders started less than 1.5 seconds later, and the spoof order received zero fills before complete cancellation.",
        matched_negative_group_id="cftc_logista_serotta_20200129_cl_calendar_spread_example",
        session_bucket="regular_us_central_time",
        source_row_id="cftc_logista_serotta_20200129_cl_sell_spoof_order",
    ),
    row(
        label="positive_spoofing_layering",
        source_report=SOURCES[1]["title"],
        source_section="Paragraphs 74-77, Spoof Event Example 2: February 20 2020",
        trade_date="2020-02-20",
        symbol="NGH0-NGJ0 natural gas March-April 2020 calendar spread",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader/advisor; federal complaint",
        participant_identifier="Nicholas Serotta / Logista Advisors LLC",
        side="buy spoof order opposite sell genuine orders",
        earliest_order_received_time="13:06:29.086 America/Chicago",
        latest_order_received_time="13:07:36.935 America/Chicago",
        order_count="one large spoof order",
        total_order_quantity="301 calendar-spread contracts",
        activity_description="CFTC complaint describes a 301-contract buy spoof order at the best-bid price level; sell genuine orders started shortly afterward, and the spoof order received zero fills before complete cancellation.",
        matched_negative_group_id="cftc_logista_serotta_20200220_ng_calendar_spread_example",
        session_bucket="regular_us_central_time",
        source_row_id="cftc_logista_serotta_20200220_ng_buy_spoof_order",
    ),
    row(
        label="positive_spoofing_layering",
        source_report=SOURCES[1]["title"],
        source_section="Paragraphs 78-81, Spoof Event Example 3: March 11 2020",
        trade_date="2020-03-11",
        symbol="CLM0-CLZ0 crude oil June-December 2020 calendar spread",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader/advisor; federal complaint",
        participant_identifier="Nicholas Serotta / Logista Advisors LLC",
        side="buy spoof order opposite sell genuine orders",
        earliest_order_received_time="11:29:48.415 America/Chicago",
        latest_order_received_time="11:30:50.876 America/Chicago",
        order_count="one large spoof order",
        total_order_quantity="301 calendar-spread contracts",
        activity_description="CFTC complaint describes a 301-contract buy spoof order at the second-best bid; sell genuine orders started shortly afterward, and the spoof order received zero fills before complete cancellation.",
        matched_negative_group_id="cftc_logista_serotta_20200311_cl_calendar_spread_example",
        session_bucket="regular_us_central_time",
        source_row_id="cftc_logista_serotta_20200311_cl_buy_spoof_order",
    ),
    row(
        label="positive_spoofing_layering",
        source_report=SOURCES[1]["title"],
        source_section="Paragraphs 82-90, Spoof Event Example 4: February 19 2020",
        trade_date="2020-02-19",
        symbol="NGH0-NGJ0 natural gas March-April 2020 calendar spread",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader/advisor; federal complaint",
        participant_identifier="Nicholas Serotta / Logista Advisors LLC",
        side="sequence of alternating 301-lot spoof orders opposite smaller genuine orders",
        earliest_order_received_time="22:56:22.803 America/Chicago",
        latest_order_received_time="23:12:21.768 America/Chicago",
        order_count="fourteen 301-lot spoof orders",
        total_order_quantity="4214 calendar-spread contracts",
        activity_description="CFTC complaint describes a sixteen-minute sequence with fourteen 301-lot spoof orders alternating sides; none filled, while smaller opposite-side genuine orders filled 2874 lots.",
        matched_negative_group_id="cftc_logista_serotta_20200219_ng_calendar_spread_sequence",
        session_bucket="overnight_central_time",
        source_row_id="cftc_logista_serotta_20200219_ng_alternating_spoof_sequence",
    ),
    row(
        label="positive_spoofing_layering",
        source_report=SOURCES[1]["title"],
        source_section="Paragraphs 91-95, Spoof Event Example 5: February 5 2020",
        trade_date="2020-02-05",
        symbol="ICE Brent/WTI Crude Spread - April 2020",
        venue_or_market_center="IFEU/ICE Futures Europe",
        participant_type_code="CFTC defendant trader/advisor; federal complaint",
        participant_identifier="Nicholas Serotta / Logista Advisors LLC",
        side="sequence of 201-301 lot spoof orders opposite smaller genuine orders",
        earliest_order_received_time="20:23:00 GMT",
        latest_order_received_time="20:41:00 GMT",
        order_count="nineteen large spoof orders plus one immediate reentry",
        total_order_quantity="5919 spread contracts",
        activity_description="CFTC complaint describes an eighteen-minute IFEU sequence with 19 large 201-301 lot spoof orders; no spoof-order contracts filled, while smaller opposite-side genuine orders filled approximately 2513 lots.",
        matched_negative_group_id="cftc_logista_serotta_20200205_ifue_brent_wti_sequence",
        session_bucket="evening_gmt",
        source_row_id="cftc_logista_serotta_20200205_ice_brent_wti_spoof_sequence",
    ),
]

NEGATIVE_ADDITIONS = [
    row(
        label="matched_negative_normal_activity",
        source_report=SOURCES[0]["title"],
        source_section="Paragraphs 51-54, Event Example 1: January 25 2018",
        trade_date="2018-01-25",
        symbol="March 2018 Crude Oil futures",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader; federal complaint",
        participant_identifier="Andras Banoczay / Roman et al.",
        side="buy genuine order",
        earliest_order_received_time="06:31:44.504 America/Chicago",
        latest_order_received_time="06:31:53.559 America/Chicago",
        order_count="one genuine order",
        total_order_quantity="10 crude oil futures contracts",
        activity_description="Same-complaint genuine-order leg: source describes a 10-lot buy genuine order finalized at 06:31:44.504 and fully filled at 06:31:53.559. This is a schema/control seed, not broad normal-market calibration.",
        matched_negative_group_id="cftc_roman_banoczay_20180125_cl_buy_genuine_sell_layered_spoof_example",
        session_bucket="overnight_central_time",
        source_row_id="cftc_roman_banoczay_20180125_cl_buy_genuine_order_control",
    ),
    row(
        label="matched_negative_normal_activity",
        source_report=SOURCES[0]["title"],
        source_section="Paragraphs 57-60, Event Example 2: February 1 2018",
        trade_date="2018-02-01",
        symbol="March 2018 Crude Oil futures",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader; federal complaint",
        participant_identifier="Andras Banoczay / Roman et al.",
        side="buy genuine order",
        earliest_order_received_time="02:10:29.657 America/Chicago",
        latest_order_received_time="02:10:41.859 America/Chicago",
        order_count="one genuine order",
        total_order_quantity="10 crude oil futures contracts",
        activity_description="Same-complaint genuine-order leg: source describes a 10-lot buy genuine order finalized at 02:10:29.657 and fully filled at 02:10:41.859. This is a schema/control seed, not broad normal-market calibration.",
        matched_negative_group_id="cftc_roman_banoczay_20180201_cl_buy_genuine_sell_layered_spoof_example",
        session_bucket="overnight_central_time",
        source_row_id="cftc_roman_banoczay_20180201_cl_buy_genuine_order_control",
    ),
    row(
        label="matched_negative_normal_activity",
        source_report=SOURCES[0]["title"],
        source_section="Paragraphs 63-66, Event Example 3 first leg: February 12 2018",
        trade_date="2018-02-12",
        symbol="March 2018 Crude Oil futures",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader; federal complaint",
        participant_identifier="Andras Banoczay / Roman et al.",
        side="sell genuine order",
        earliest_order_received_time="03:02:18.576 America/Chicago",
        latest_order_received_time="03:02:18.577 America/Chicago",
        order_count="one aggressive genuine order",
        total_order_quantity="40 crude oil futures contracts",
        activity_description="Same-complaint genuine-order leg: source describes a 40-lot aggressive sell genuine order that crossed the spread and fully filled within one millisecond. This is a schema/control seed, not broad normal-market calibration.",
        matched_negative_group_id="cftc_roman_banoczay_20180212_cl_sell_genuine_buy_layered_spoof_leg",
        session_bucket="overnight_central_time",
        source_row_id="cftc_roman_banoczay_20180212_cl_sell_genuine_order_control",
    ),
    row(
        label="matched_negative_normal_activity",
        source_report=SOURCES[0]["title"],
        source_section="Paragraphs 69-72, Event Example 3 second leg: February 12 2018",
        trade_date="2018-02-12",
        symbol="March 2018 Crude Oil futures",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader; federal complaint",
        participant_identifier="Andras Banoczay / Roman et al.",
        side="buy genuine order",
        earliest_order_received_time="03:02:26.928 America/Chicago",
        latest_order_received_time="03:02:26.929 America/Chicago",
        order_count="one aggressive genuine order",
        total_order_quantity="40 crude oil futures contracts",
        activity_description="Same-complaint genuine-order leg: source describes a 40-lot aggressive buy genuine order that crossed the spread and fully filled within one millisecond. This is a schema/control seed, not broad normal-market calibration.",
        matched_negative_group_id="cftc_roman_banoczay_20180212_cl_buy_genuine_sell_layered_spoof_leg",
        session_bucket="overnight_central_time",
        source_row_id="cftc_roman_banoczay_20180212_cl_buy_genuine_order_control",
    ),
    row(
        label="matched_negative_normal_activity",
        source_report=SOURCES[1]["title"],
        source_section="Paragraphs 71-72, Spoof Event Example 1: January 29 2020",
        trade_date="2020-01-29",
        symbol="CLM0-CLU0 crude oil June-September 2020 calendar spread",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader/advisor; federal complaint",
        participant_identifier="Nicholas Serotta / Logista Advisors LLC",
        side="buy genuine orders",
        earliest_order_received_time="12:00:08.033 America/Chicago",
        latest_order_received_time="about 12:00:20.225 America/Chicago",
        order_count="series of smaller genuine orders",
        total_order_quantity="201 contracts involved; 77 contracts filled",
        activity_description="Same-complaint genuine-order leg: source describes buy genuine orders entered less than 1.5 seconds after the spoof order; unfilled volume was canceled before the spoof order cancellation. This is a schema/control seed, not broad normal-market calibration.",
        matched_negative_group_id="cftc_logista_serotta_20200129_cl_calendar_spread_example",
        session_bucket="regular_us_central_time",
        source_row_id="cftc_logista_serotta_20200129_cl_buy_genuine_orders_control",
    ),
    row(
        label="matched_negative_normal_activity",
        source_report=SOURCES[1]["title"],
        source_section="Paragraphs 75-77, Spoof Event Example 2: February 20 2020",
        trade_date="2020-02-20",
        symbol="NGH0-NGJ0 natural gas March-April 2020 calendar spread",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader/advisor; federal complaint",
        participant_identifier="Nicholas Serotta / Logista Advisors LLC",
        side="sell genuine orders",
        earliest_order_received_time="13:06:39.339 America/Chicago",
        latest_order_received_time="before 13:07:31.935 America/Chicago",
        order_count="sixteen 49-lot genuine orders plus short-resting unfilled orders",
        total_order_quantity="269 contracts filled",
        activity_description="Same-complaint genuine-order leg: source describes sell genuine orders entered after the spoof order; almost all aggressive unfilled orders were canceled quickly. This is a schema/control seed, not broad normal-market calibration.",
        matched_negative_group_id="cftc_logista_serotta_20200220_ng_calendar_spread_example",
        session_bucket="regular_us_central_time",
        source_row_id="cftc_logista_serotta_20200220_ng_sell_genuine_orders_control",
    ),
    row(
        label="matched_negative_normal_activity",
        source_report=SOURCES[1]["title"],
        source_section="Paragraphs 79-81, Spoof Event Example 3: March 11 2020",
        trade_date="2020-03-11",
        symbol="CLM0-CLZ0 crude oil June-December 2020 calendar spread",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader/advisor; federal complaint",
        participant_identifier="Nicholas Serotta / Logista Advisors LLC",
        side="sell genuine orders",
        earliest_order_received_time="11:29:54.745 America/Chicago",
        latest_order_received_time="about 11:30:49.876 America/Chicago",
        order_count="series of 25-lot genuine orders",
        total_order_quantity="125 contracts involved; 34 contracts filled",
        activity_description="Same-complaint genuine-order leg: source describes sell genuine orders entered after the spoof order and partially filled before the spoof order was canceled. This is a schema/control seed, not broad normal-market calibration.",
        matched_negative_group_id="cftc_logista_serotta_20200311_cl_calendar_spread_example",
        session_bucket="regular_us_central_time",
        source_row_id="cftc_logista_serotta_20200311_cl_sell_genuine_orders_control",
    ),
    row(
        label="matched_negative_normal_activity",
        source_report=SOURCES[1]["title"],
        source_section="Paragraphs 82-90, Spoof Event Example 4: February 19 2020",
        trade_date="2020-02-19",
        symbol="NGH0-NGJ0 natural gas March-April 2020 calendar spread",
        venue_or_market_center="NYMEX/CME Globex",
        participant_type_code="CFTC defendant trader/advisor; federal complaint",
        participant_identifier="Nicholas Serotta / Logista Advisors LLC",
        side="smaller opposite-side genuine orders",
        earliest_order_received_time="22:56:22.803 America/Chicago",
        latest_order_received_time="23:12:21.768 America/Chicago",
        order_count="numerous smaller genuine orders",
        total_order_quantity="2874 contracts filled",
        activity_description="Same-complaint genuine-order leg: source describes smaller opposite-side genuine orders during the sixteen-minute sequence; over 80% of genuine-order contracts filled. This is a schema/control seed, not broad normal-market calibration.",
        matched_negative_group_id="cftc_logista_serotta_20200219_ng_calendar_spread_sequence",
        session_bucket="overnight_central_time",
        source_row_id="cftc_logista_serotta_20200219_ng_genuine_orders_control",
    ),
    row(
        label="matched_negative_normal_activity",
        source_report=SOURCES[1]["title"],
        source_section="Paragraphs 91-95, Spoof Event Example 5: February 5 2020",
        trade_date="2020-02-05",
        symbol="ICE Brent/WTI Crude Spread - April 2020",
        venue_or_market_center="IFEU/ICE Futures Europe",
        participant_type_code="CFTC defendant trader/advisor; federal complaint",
        participant_identifier="Nicholas Serotta / Logista Advisors LLC",
        side="smaller opposite-side genuine orders",
        earliest_order_received_time="20:23:00 GMT",
        latest_order_received_time="20:41:00 GMT",
        order_count="numerous smaller genuine orders",
        total_order_quantity="approximately 2513 contracts filled",
        activity_description="Same-complaint genuine-order leg: source describes smaller opposite-side genuine orders during the IFEU eighteen-minute sequence; more than 73% of genuine-order contracts filled. This is a schema/control seed, not broad normal-market calibration.",
        matched_negative_group_id="cftc_logista_serotta_20200205_ifue_brent_wti_sequence",
        session_bucket="evening_gmt",
        source_row_id="cftc_logista_serotta_20200205_ice_brent_wti_genuine_orders_control",
    ),
]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_absolute() and path.is_relative_to(REPO) else str(path)


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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in rows:
            writer.writerow({field: item.get(field, "") for field in fields})


def append_unique(path: Path, additions: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows = read_csv(path)
    seen = {item.get("source_row_id", "") for item in rows}
    added = [item for item in additions if item["source_row_id"] not in seen]
    if added:
        write_csv(path, rows + added, FIELDS)
    return read_csv(path), added


def fetch_sources() -> list[dict[str, Any]]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for source in SOURCES:
        pdf_path = RAW_DIR / f"{source['id']}.pdf"
        text_path = RAW_DIR / f"{source['id']}.txt"
        request = urllib.request.Request(source["url"], headers={"User-Agent": "ict-engine-board-a-r6/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
        pdf_path.write_bytes(body)
        extract_script = (
            "from pathlib import Path\n"
            "from pypdf import PdfReader\n"
            f"pdf=Path({str(pdf_path)!r})\n"
            f"out=Path({str(text_path)!r})\n"
            "reader=PdfReader(str(pdf))\n"
            "out.write_text('\\n'.join(page.extract_text() or '' for page in reader.pages), encoding='utf-8')\n"
            "print(len(reader.pages), out.stat().st_size)\n"
        )
        extract = subprocess.run(
            ["uv", "run", "--with", "pypdf", "python", "-c", extract_script],
            cwd=str(REPO),
            text=True,
            capture_output=True,
            check=False,
        )
        text = text_path.read_text(encoding="utf-8") if text_path.exists() else ""
        records.append(
            {
                "id": source["id"],
                "url": source["url"],
                "title": source["title"],
                "pdf_path": str(pdf_path),
                "pdf_sha256": hashlib.sha256(body).hexdigest(),
                "pdf_bytes": len(body),
                "text_path": str(text_path),
                "text_sha256": sha256(text_path) if text_path.exists() else "",
                "text_chars": len(text),
                "extract_returncode": extract.returncode,
                "extract_stdout": extract.stdout.strip(),
                "extract_stderr_path": "",
                "text_checks": {needle: (needle in text) for needle in source["checks"]},
            }
        )
    return records


def run_direct_verifier() -> dict[str, Any]:
    result = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(INTAKE)],
        cwd=str(REPO),
        text=True,
        capture_output=True,
        check=False,
    )
    (CMD_DIR / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (CMD_DIR / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(result.stderr, encoding="utf-8")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"parse_failed": True, "stdout": result.stdout[:1000]}
    return {"returncode": result.returncode, "payload": payload}


def wilson_all_success(n: int) -> float:
    if n <= 0:
        return 0.0
    z = 1.959963984540054
    return n / (n + z * z)


def unique_count(rows: list[dict[str, str]], field: str) -> int:
    return len({item.get(field, "") for item in rows if item.get(field, "")})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)

    before_positive = read_csv(POSITIVE)
    before_negative = read_csv(NEGATIVE)
    before_hashes = {
        "positive": sha256(POSITIVE) if POSITIVE.exists() else "",
        "negative": sha256(NEGATIVE) if NEGATIVE.exists() else "",
        "provenance": sha256(PROVENANCE) if PROVENANCE.exists() else "",
    }
    source_records = fetch_sources()
    text_checks_ok = all(all(record["text_checks"].values()) for record in source_records)

    if not text_checks_ok:
        raise SystemExit("source_text_checks_failed")

    positive_rows, positive_added = append_unique(POSITIVE, POSITIVE_ADDITIONS)
    negative_rows, negative_added = append_unique(NEGATIVE, NEGATIVE_ADDITIONS)

    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    provenance["r6_official_rowlevel_support_extension_v1"] = {
        "run_id": RUN_ID,
        "rows_materialized_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": source_records,
        "positive_source_row_ids": [item["source_row_id"] for item in POSITIVE_ADDITIONS],
        "matched_negative_source_row_ids": [item["source_row_id"] for item in NEGATIVE_ADDITIONS],
        "positive_rows_added_this_run": len(positive_added),
        "matched_negative_rows_added_this_run": len(negative_added),
        "control_boundary": "same-complaint genuine-order legs are schema/control seeds only, not broad normal-market calibration controls",
    }
    provenance["positive_rows_count"] = len(positive_rows)
    provenance["matched_negative_rows_count"] = len(negative_rows)
    provenance["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    provenance["updated_by"] = RUN_ID
    provenance["positive_rows_sha256"] = sha256(POSITIVE)
    provenance["matched_negative_rows_sha256"] = sha256(NEGATIVE)
    provenance["matched_negative_control_policy"] = (
        "CFTC public complaint same-event genuine-order legs are source-described schema/control seeds only; "
        "they are not a broad normal-market calibration sample."
    )
    PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verifier = run_direct_verifier()
    positive_lcb = wilson_all_success(len(positive_rows))
    negative_lcb = wilson_all_success(len(negative_rows))
    min_lcb = min(positive_lcb, negative_lcb)
    support_ok = len(positive_rows) >= 50 and len(negative_rows) >= 50
    broad_normal_sample = False
    direct_species_closed = False
    new_confidence_gate = support_ok and min_lcb >= 0.95 and broad_normal_sample and direct_species_closed

    gates = [
        {"gate": "source_text_checks", "observed": text_checks_ok, "required": True, "pass": text_checks_ok},
        {"gate": "positive_rows_added", "observed": len(positive_added), "required": 9, "pass": len(positive_added) == 9},
        {"gate": "matched_negative_rows_added", "observed": len(negative_added), "required": 9, "pass": len(negative_added) == 9},
        {"gate": "positive_support", "observed": len(positive_rows), "required": ">=50", "pass": len(positive_rows) >= 50},
        {"gate": "matched_negative_support", "observed": len(negative_rows), "required": ">=50", "pass": len(negative_rows) >= 50},
        {"gate": "wilson95_min_lcb", "observed": f"{min_lcb:.6f}", "required": ">=0.95", "pass": min_lcb >= 0.95},
        {"gate": "broad_normal_sample", "observed": broad_normal_sample, "required": True, "pass": broad_normal_sample},
        {"gate": "direct_species_coverage", "observed": direct_species_closed, "required": True, "pass": direct_species_closed},
        {"gate": "unchanged_verifier_schema_ready", "observed": verifier["payload"].get("status"), "required": "schema_ready_unscored", "pass": verifier["payload"].get("status") == "schema_ready_unscored"},
    ]
    write_csv(OUT_DIR / "r6_official_rowlevel_support_extension_v1_gates.csv", gates, ["gate", "observed", "required", "pass"])
    write_csv(
        OUT_DIR / "r6_official_rowlevel_support_extension_v1_added_rows.csv",
        [{"kind": "positive", **item} for item in positive_added] + [{"kind": "matched_negative", **item} for item in negative_added],
        ["kind", *FIELDS],
    )
    write_csv(
        OUT_DIR / "r6_official_rowlevel_support_extension_v1_source_checks.csv",
        [
            {
                "source_id": record["id"],
                "pdf_sha256": record["pdf_sha256"],
                "text_sha256": record["text_sha256"],
                "text_checks_passed": all(record["text_checks"].values()),
                "url": record["url"],
            }
            for record in source_records
        ],
        ["source_id", "pdf_sha256", "text_sha256", "text_checks_passed", "url"],
    )

    decision = {
        "gate_result": "r6_official_rowlevel_support_extension_v1=support_50x50_reached_confidence_still_blocked",
        "board_state": "blocked",
        "accepted_rows_added": 0,
        "new_confidence_gate": new_confidence_gate,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
    }
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": repo_rel(BOARD),
        "board_sha256_at_run": sha256(BOARD),
        "before": {
            "positive_rows": len(before_positive),
            "matched_negative_rows": len(before_negative),
            "positive_sha256": before_hashes["positive"],
            "matched_negative_sha256": before_hashes["negative"],
            "provenance_sha256": before_hashes["provenance"],
        },
        "after": {
            "positive_rows": len(positive_rows),
            "matched_negative_rows": len(negative_rows),
            "positive_sha256": sha256(POSITIVE),
            "matched_negative_sha256": sha256(NEGATIVE),
            "provenance_sha256": sha256(PROVENANCE),
            "matched_group_count": verifier["payload"].get("matched_group_count"),
        },
        "positive_rows_added_this_run": len(positive_added),
        "matched_negative_rows_added_this_run": len(negative_added),
        "source_records": source_records,
        "direct_verifier": verifier,
        "unique_positive_dates": unique_count(positive_rows, "trade_date"),
        "unique_positive_symbols": unique_count(positive_rows, "symbol"),
        "unique_positive_venues": unique_count(positive_rows, "venue_or_market_center"),
        "wilson95_lcb": {
            "positive": positive_lcb,
            "matched_negative": negative_lcb,
            "min": min_lcb,
        },
        "support_50x50": support_ok,
        "broad_normal_sample": broad_normal_sample,
        "direct_species_closed": direct_species_closed,
        "gates": gates,
        "decision": decision,
        "next_action": "Acquire broad source-owned normal-market order-lifecycle controls and enough additional direct rows for Wilson95 >=0.95; keep R5 blocked until source-owner post-cutoff source-panel rows exist.",
    }
    (OUT_DIR / "r6_official_rowlevel_support_extension_v1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# R6 Official Row-Level Support Extension v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Official CFTC source PDFs fetched to `/tmp`: `{len(source_records)}`.",
        f"- Source text checks passed: `{str(text_checks_ok).lower()}`.",
        f"- Rows added: positives `{len(positive_added)}`, matched controls `{len(negative_added)}`.",
        f"- Direct intake after run: positives `{len(positive_rows)}`, matched negatives `{len(negative_rows)}`, matched groups `{verifier['payload'].get('matched_group_count')}`.",
        f"- Unique positive dates/symbols/venues: `{unique_count(positive_rows, 'trade_date')}` / `{unique_count(positive_rows, 'symbol')}` / `{unique_count(positive_rows, 'venue_or_market_center')}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{min_lcb:.6f}`.",
        f"- `50/50` support gate: `{str(support_ok).lower()}`.",
        "- Broad normal sample: `false`; controls remain same-complaint genuine-order schema seeds.",
        "- Direct species coverage closed: `false`.",
        f"- Gate result: `{decision['gate_result']}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Boundary",
        "",
        "This run changes only the shared `/tmp/ict-engine-direct-manipulation-row-intake` files and writes repo-local evidence artifacts. It does not commit raw PDFs/text, change runtime code, relax thresholds, or promote same-event genuine-order controls into broad normal-market controls.",
    ]
    (OUT_DIR / "r6_official_rowlevel_support_extension_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    failures = []
    if len(positive_added) != 9:
        failures.append("positive_added_not_9")
    if len(negative_added) != 9:
        failures.append("negative_added_not_9")
    if verifier["payload"].get("status") != "schema_ready_unscored":
        failures.append("direct_verifier_not_schema_ready")
    if len(positive_rows) < 50 or len(negative_rows) < 50:
        failures.append("support_50x50_not_reached")
    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={result['board_sha256_at_run']}",
        f"positive_rows_before={len(before_positive)}",
        f"matched_negative_rows_before={len(before_negative)}",
        f"positive_rows_added={len(positive_added)}",
        f"matched_negative_rows_added={len(negative_added)}",
        f"positive_rows_after={len(positive_rows)}",
        f"matched_negative_rows_after={len(negative_rows)}",
        f"support_50x50={str(support_ok).lower()}",
        f"wilson95_min_lcb={min_lcb:.6f}",
        f"broad_normal_sample={str(broad_normal_sample).lower()}",
        f"direct_species_closed={str(direct_species_closed).lower()}",
        f"new_confidence_gate={str(new_confidence_gate).lower()}",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "external_requests_sent=true",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        f"assertion_status={'FAIL' if failures else 'PASS'}",
    ]
    if failures:
        assertions.append("failures=" + ",".join(failures))
    (CHECK_DIR / "r6_official_rowlevel_support_extension_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision["gate_result"], "positive_rows": len(positive_rows), "matched_negative_rows": len(negative_rows), "wilson95_min_lcb": round(min_lcb, 6)}, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
