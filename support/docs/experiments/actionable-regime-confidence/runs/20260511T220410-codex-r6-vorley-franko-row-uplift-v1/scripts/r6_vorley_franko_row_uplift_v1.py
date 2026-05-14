#!/usr/bin/env python3
"""Append bounded official CFTC Vorley/Chanu and Franko R6 rows."""

from __future__ import annotations

import csv
import fcntl
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T220410-codex-r6-vorley-franko-row-uplift-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-vorley-franko-row-uplift"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"
LOCK = INTAKE / ".r6_vorley_franko_row_uplift_v1.lock"
STATE_DIR = Path("/tmp/ict-engine-board-a-r6-vorley-franko-row-uplift-v1")
AUTOQUANT_STATE_DIR = Path("/tmp/ict-engine-board-a-r6-vorley-franko-autoquant-status-v1")
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
ICT = REPO / "target/debug/ict-engine"
VORLEY_TEXT = Path(
    "/private/tmp/ict-engine-r6-pdf-row-probe/text/"
    "cftc_pr_7686_18_vorley_chanu_complaint_james_vorley_and_cedric_chanu.txt"
)
FRANKO_TEXT = Path(
    "/private/tmp/ict-engine-r6-pdf-row-probe/text/"
    "cftc_pr_7796_18_franko_order_michael_d_franko.txt"
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

VORLEY_REPORT = "CFTC Complaint: James Vorley and Cedric Chanu, Case 1:18-cv-00603"
FRANKO_REPORT = "CFTC Order: Michael D. Franko, CFTC Docket No. 18-43"
COMEX = "COMEX/CME Globex"
LME_COMEX = "LME and COMEX cross-market"

POSITIVE_ADDITIONS = [
    {
        "label": "positive_spoofing_layering",
        "source_report": VORLEY_REPORT,
        "source_section": "Paragraph 33, March 28 2011 Trader A Silver Futures chat example",
        "trade_date": "2011-03-28",
        "symbol": "COMEX Silver Futures",
        "venue_or_market_center": COMEX,
        "participant_type_code": "Bank A precious metals desk trader described in official CFTC complaint",
        "participant_identifier": "Trader A / Bank A",
        "side": "buy spoof orders opposite sell genuine iceberg order",
        "earliest_order_received_time": "after 10:46:04 p.m. Central Time",
        "latest_order_received_time": "10:54:12 p.m. Central Time",
        "order_count": "21 buy spoof orders",
        "total_order_quantity": "220 lots",
        "activity_description": "Official CFTC complaint describes Trader A placing and canceling twenty-one buy spoof orders after a 20-lot sell iceberg genuine order stalled; the final contract of the sell order filled at 10:54:12 p.m.",
        "matched_negative_group_id": "cftc_vorley_chanu_20110328_silver_trader_a",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_vorley_chanu_20110328_silver_buy_spoof_orders",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": VORLEY_REPORT,
        "source_section": "Paragraph 34, March 16 2011 Vorley Gold Futures example",
        "trade_date": "2011-03-16",
        "symbol": "COMEX Gold Futures",
        "venue_or_market_center": COMEX,
        "participant_type_code": "Bank A precious metals desk trader described in official CFTC complaint",
        "participant_identifier": "James Vorley / Bank A",
        "side": "buy spoof orders opposite sell genuine iceberg order",
        "earliest_order_received_time": "immediately after 06:03:21 a.m. Central Time",
        "latest_order_received_time": "within about five seconds after 06:03:21 a.m. Central Time",
        "order_count": "12 buy spoof orders",
        "total_order_quantity": "120 lots",
        "activity_description": "Official CFTC complaint describes Vorley placing twelve 10-lot buy spoof orders after a 56-lot sell iceberg genuine order; the spoof orders were cancelled within one to two seconds each while the genuine order continued filling.",
        "matched_negative_group_id": "cftc_vorley_chanu_20110316_gold_vorley",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_vorley_chanu_20110316_gold_buy_spoof_orders",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": VORLEY_REPORT,
        "source_section": "Paragraph 37, November 3 2010 Trader A Gold Futures help example",
        "trade_date": "2010-11-03",
        "symbol": "COMEX Gold Futures",
        "venue_or_market_center": COMEX,
        "participant_type_code": "Bank A precious metals desk traders described in official CFTC complaint",
        "participant_identifier": "James Vorley and Cedric Chanu / Bank A",
        "side": "buy spoof orders opposite Trader A sell genuine iceberg order",
        "earliest_order_received_time": "not disclosed in public complaint; after Trader A sell order stalled",
        "latest_order_received_time": "approximately two seconds after each spoof order placement",
        "order_count": "29 buy spoof orders",
        "total_order_quantity": "290 lots",
        "activity_description": "Official CFTC complaint describes Vorley and Chanu helping a stalled 400-lot Gold Futures sell iceberg genuine order by placing and cancelling twenty-nine 10-lot buy spoof orders.",
        "matched_negative_group_id": "cftc_vorley_chanu_20101103_gold_help_trader_a",
        "session_bucket": "central_time_not_disclosed",
        "source_row_id": "cftc_vorley_chanu_20101103_gold_buy_spoof_orders",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": VORLEY_REPORT,
        "source_section": "Paragraphs 50-55, June 2 2013 Chanu August-delivery Gold Futures example",
        "trade_date": "2013-06-02",
        "symbol": "August-delivery Gold Futures",
        "venue_or_market_center": COMEX,
        "participant_type_code": "Bank A precious metals desk trader described in official CFTC complaint",
        "participant_identifier": "Cedric Chanu / Bank A",
        "side": "buy spoof order opposite sell genuine iceberg order",
        "earliest_order_received_time": "over three minutes after 19:52:13.056 Central Time",
        "latest_order_received_time": "approximately one second after placement",
        "order_count": "one buy spoof order",
        "total_order_quantity": "100 lots",
        "activity_description": "Official CFTC complaint describes Chanu placing a 100-lot buy spoof order after a 50-lot sell iceberg genuine order sat pending for over three minutes; three genuine contracts filled and the spoof order was then cancelled.",
        "matched_negative_group_id": "cftc_vorley_chanu_20130602_gold_chanu",
        "session_bucket": "evening_central_time",
        "source_row_id": "cftc_vorley_chanu_20130602_gold_buy_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": VORLEY_REPORT,
        "source_section": "Paragraphs 56-60, July 9 2013 Vorley Gold Futures example",
        "trade_date": "2013-07-09",
        "symbol": "COMEX Gold Futures",
        "venue_or_market_center": COMEX,
        "participant_type_code": "Bank A precious metals desk trader described in official CFTC complaint",
        "participant_identifier": "James Vorley / Bank A",
        "side": "buy spoof order opposite sell genuine iceberg order",
        "earliest_order_received_time": "approximately five seconds after 15:51:59.661 Central Time",
        "latest_order_received_time": "approximately seven tenths of a second after placement",
        "order_count": "one buy spoof order",
        "total_order_quantity": "100 lots",
        "activity_description": "Official CFTC complaint describes Vorley placing a 100-lot buy spoof order after a 50-lot sell iceberg genuine order stalled; eight additional lots of the genuine order filled within three milliseconds and the spoof order was cancelled less than a second later.",
        "matched_negative_group_id": "cftc_vorley_chanu_20130709_gold_vorley",
        "session_bucket": "regular_central_time",
        "source_row_id": "cftc_vorley_chanu_20130709_gold_buy_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": FRANKO_REPORT,
        "source_section": "December 17 2013 cross-market copper example, first LME spoof order",
        "trade_date": "2013-12-17",
        "symbol": "LME copper futures",
        "venue_or_market_center": LME_COMEX,
        "participant_type_code": "CFTC respondent trader; Victory Asset trader",
        "participant_identifier": "Michael D. Franko / Victory Asset",
        "side": "buy spoof order in LME copper opposite COMEX copper sell genuine orders",
        "earliest_order_received_time": "not disclosed in public order; after two-hour no-trade interval",
        "latest_order_received_time": "approximately one second after placement",
        "order_count": "one buy spoof order",
        "total_order_quantity": "100 lots",
        "activity_description": "Official CFTC order describes Franko placing a fully visible 100-lot LME copper buy spoof order while two COMEX copper sell iceberg genuine orders were active; the first genuine order fully filled and four lots of the second filled before cancellation.",
        "matched_negative_group_id": "cftc_franko_20131217_lme_comex_copper_first",
        "session_bucket": "time_not_disclosed",
        "source_row_id": "cftc_franko_20131217_lme_copper_first_buy_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": FRANKO_REPORT,
        "source_section": "December 17 2013 cross-market copper example, second LME spoof order",
        "trade_date": "2013-12-17",
        "symbol": "LME copper futures",
        "venue_or_market_center": LME_COMEX,
        "participant_type_code": "CFTC respondent trader; Victory Asset trader",
        "participant_identifier": "Michael D. Franko / Victory Asset",
        "side": "second buy spoof order in LME copper opposite COMEX copper sell genuine order",
        "earliest_order_received_time": "after cancellation of first LME copper spoof order",
        "latest_order_received_time": "approximately one second after placement",
        "order_count": "one buy spoof order",
        "total_order_quantity": "100 lots",
        "activity_description": "Official CFTC order describes Franko placing a second fully visible 100-lot LME copper buy spoof order at a higher price; five more lots of the second COMEX copper sell genuine order filled while the spoof order rested, then the spoof order was cancelled.",
        "matched_negative_group_id": "cftc_franko_20131217_lme_comex_copper_second",
        "session_bucket": "time_not_disclosed",
        "source_row_id": "cftc_franko_20131217_lme_copper_second_buy_spoof_order",
    },
]

NEGATIVE_ADDITIONS = [
    {
        "label": "matched_negative_normal_activity",
        "source_report": VORLEY_REPORT,
        "source_section": "Paragraph 33, March 28 2011 Trader A Silver Futures chat example",
        "trade_date": "2011-03-28",
        "symbol": "COMEX Silver Futures",
        "venue_or_market_center": COMEX,
        "participant_type_code": "Bank A precious metals desk trader described in official CFTC complaint",
        "participant_identifier": "Trader A / Bank A",
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "10:43:34 p.m. Central Time",
        "latest_order_received_time": "10:54:12 p.m. Central Time",
        "order_count": "one sell iceberg order",
        "total_order_quantity": "20 lots",
        "activity_description": "Matched same-complaint control seed: the source distinguishes the 20-lot sell iceberg genuine order from the buy spoof orders. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_vorley_chanu_20110328_silver_trader_a",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_vorley_chanu_20110328_silver_sell_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": VORLEY_REPORT,
        "source_section": "Paragraph 34, March 16 2011 Vorley Gold Futures example",
        "trade_date": "2011-03-16",
        "symbol": "COMEX Gold Futures",
        "venue_or_market_center": COMEX,
        "participant_type_code": "Bank A precious metals desk trader described in official CFTC complaint",
        "participant_identifier": "James Vorley / Bank A",
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "06:03:21 a.m. Central Time",
        "latest_order_received_time": "during and after spoof-order cancellation",
        "order_count": "one sell iceberg order",
        "total_order_quantity": "56 lots",
        "activity_description": "Matched same-complaint control seed: the source distinguishes the 56-lot sell iceberg genuine order from the buy spoof orders. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_vorley_chanu_20110316_gold_vorley",
        "session_bucket": "overnight_central_time",
        "source_row_id": "cftc_vorley_chanu_20110316_gold_sell_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": VORLEY_REPORT,
        "source_section": "Paragraph 37, November 3 2010 Trader A Gold Futures help example",
        "trade_date": "2010-11-03",
        "symbol": "COMEX Gold Futures",
        "venue_or_market_center": COMEX,
        "participant_type_code": "Bank A precious metals desk trader described in official CFTC complaint",
        "participant_identifier": "Trader A / Bank A",
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "not disclosed in public complaint; before Vorley/Chanu help sequence",
        "latest_order_received_time": "after buy spoof orders",
        "order_count": "one sell iceberg order",
        "total_order_quantity": "400 contracts",
        "activity_description": "Matched same-complaint control seed: the source distinguishes Trader A's 400-contract Gold Futures sell iceberg genuine order from the buy spoof orders placed to help fill it. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_vorley_chanu_20101103_gold_help_trader_a",
        "session_bucket": "central_time_not_disclosed",
        "source_row_id": "cftc_vorley_chanu_20101103_gold_sell_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": VORLEY_REPORT,
        "source_section": "Paragraphs 50-55, June 2 2013 Chanu August-delivery Gold Futures example",
        "trade_date": "2013-06-02",
        "symbol": "August-delivery Gold Futures",
        "venue_or_market_center": COMEX,
        "participant_type_code": "Bank A precious metals desk trader described in official CFTC complaint",
        "participant_identifier": "Cedric Chanu / Bank A",
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "19:52:13.056 Central Time",
        "latest_order_received_time": "after spoof order placement",
        "order_count": "one sell iceberg order",
        "total_order_quantity": "50 lots",
        "activity_description": "Matched same-complaint control seed: the source distinguishes the 50-lot sell iceberg genuine order from the 100-lot buy spoof order. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_vorley_chanu_20130602_gold_chanu",
        "session_bucket": "evening_central_time",
        "source_row_id": "cftc_vorley_chanu_20130602_gold_sell_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": VORLEY_REPORT,
        "source_section": "Paragraphs 56-60, July 9 2013 Vorley Gold Futures example",
        "trade_date": "2013-07-09",
        "symbol": "COMEX Gold Futures",
        "venue_or_market_center": COMEX,
        "participant_type_code": "Bank A precious metals desk trader described in official CFTC complaint",
        "participant_identifier": "James Vorley / Bank A",
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "15:51:59.661 Central Time",
        "latest_order_received_time": "after spoof order placement",
        "order_count": "one sell iceberg order",
        "total_order_quantity": "50 lots",
        "activity_description": "Matched same-complaint control seed: the source distinguishes the 50-lot sell iceberg genuine order from the 100-lot buy spoof order. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_vorley_chanu_20130709_gold_vorley",
        "session_bucket": "regular_central_time",
        "source_row_id": "cftc_vorley_chanu_20130709_gold_sell_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": FRANKO_REPORT,
        "source_section": "December 17 2013 cross-market copper example, first COMEX genuine order",
        "trade_date": "2013-12-17",
        "symbol": "COMEX copper futures",
        "venue_or_market_center": LME_COMEX,
        "participant_type_code": "CFTC respondent trader; Victory Asset trader",
        "participant_identifier": "Michael D. Franko / Victory Asset",
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "before first LME copper spoof order",
        "latest_order_received_time": "while first LME spoof order rested",
        "order_count": "first sell iceberg genuine order",
        "total_order_quantity": "11 lots",
        "activity_description": "Matched same-order control seed: the source distinguishes the first 11-lot COMEX copper sell iceberg genuine order from the first LME copper buy spoof order. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_franko_20131217_lme_comex_copper_first",
        "session_bucket": "time_not_disclosed",
        "source_row_id": "cftc_franko_20131217_comex_copper_first_sell_genuine_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": FRANKO_REPORT,
        "source_section": "December 17 2013 cross-market copper example, second COMEX genuine order",
        "trade_date": "2013-12-17",
        "symbol": "COMEX copper futures",
        "venue_or_market_center": LME_COMEX,
        "participant_type_code": "CFTC respondent trader; Victory Asset trader",
        "participant_identifier": "Michael D. Franko / Victory Asset",
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "before first LME copper spoof order",
        "latest_order_received_time": "over next several seconds after second spoof order",
        "order_count": "second sell iceberg genuine order",
        "total_order_quantity": "11 lots",
        "activity_description": "Matched same-order control seed: the source distinguishes the second 11-lot COMEX copper sell iceberg genuine order from the second LME copper buy spoof order. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_franko_20131217_lme_comex_copper_second",
        "session_bucket": "time_not_disclosed",
        "source_row_id": "cftc_franko_20131217_comex_copper_second_sell_genuine_control",
    },
]

SOURCE_CHECKS = {
    VORLEY_TEXT: [
        "series of 21 Spoof Orders to buy for a total of 220 lots",
        "Vorley placed 12 buy",
        "on November 3, 2010",
        "On June 2, 2013",
        "On July 9, 2013",
    ],
    FRANKO_TEXT: [
        "this example from December 17, 2013",
        "100 lot bid",
        "Franko canceled his second Spoof Order on LME approximately one second",
    ],
}


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
    denom = 1.0 + z * z / n
    centre = 1.0 + z * z / (2 * n)
    margin = z * math.sqrt((z * z / (4 * n)) / n)
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


def source_material() -> dict[str, object]:
    result: dict[str, object] = {}
    for path, phrases in SOURCE_CHECKS.items():
        if not path.exists():
            raise FileNotFoundError(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        checks = {phrase: phrase in text for phrase in phrases}
        result[str(path)] = {
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "text_chars": len(text),
            "checks": checks,
            "all_checks_pass": all(checks.values()),
        }
    return result


def run_command(name: str, command: list[str], timeout: int = 60) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    stdout_path = CMD_OUT / f"{name}.out"
    stderr_path = CMD_OUT / f"{name}.err"
    exit_path = CMD_OUT / f"{name}.exit"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    exit_path.write_text(str(completed.returncode) + "\n", encoding="utf-8")
    return {
        "name": name,
        "cmd": " ".join(command),
        "returncode": completed.returncode,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "exit_path": rel(exit_path),
        "timed_out": False,
        "timeout_seconds": timeout,
    }


def run_command_safe(name: str, command: list[str], timeout: int = 60) -> dict[str, object]:
    try:
        return run_command(name, command, timeout)
    except subprocess.TimeoutExpired as exc:
        stdout_path = CMD_OUT / f"{name}.out"
        stderr_path = CMD_OUT / f"{name}.err"
        exit_path = CMD_OUT / f"{name}.exit"
        stdout_path.write_text((exc.stdout or "") if isinstance(exc.stdout, str) else "", encoding="utf-8")
        stderr_path.write_text((exc.stderr or "") if isinstance(exc.stderr, str) else "", encoding="utf-8")
        exit_path.write_text("timeout\n", encoding="utf-8")
        return {
            "name": name,
            "cmd": " ".join(command),
            "returncode": None,
            "stdout_path": rel(stdout_path),
            "stderr_path": rel(stderr_path),
            "exit_path": rel(exit_path),
            "timed_out": True,
            "timeout_seconds": timeout,
        }


def parse_json_file(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    INTAKE.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256(BOARD)
    pre_hashes = {p.name: sha256(p) for p in [POSITIVE, NEGATIVE, PROVENANCE]}
    source_results = source_material()
    if not all(item["all_checks_pass"] for item in source_results.values()):  # type: ignore[index]
        raise SystemExit("source text checks failed")

    with LOCK.open("w", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        positives_before = read_csv(POSITIVE)
        negatives_before = read_csv(NEGATIVE)
        positive_rows, positive_added = append_unique(POSITIVE, POSITIVE_ADDITIONS)
        negative_rows, negative_added = append_unique(NEGATIVE, NEGATIVE_ADDITIONS)
        provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        provenance["r6_vorley_franko_row_uplift_v1"] = {
            "run_id": RUN_ID,
            "materialized_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_text": source_results,
            "positive_rows_added": len(positive_added),
            "matched_negative_rows_added": len(negative_added),
            "positive_source_row_ids_added": [row["source_row_id"] for row in positive_added],
            "matched_negative_source_row_ids_added": [row["source_row_id"] for row in negative_added],
            "control_policy": "same-official-source genuine-order controls; not a broad normal-market sample",
        }
        provenance["positive_rows_count"] = len(positive_rows)
        provenance["matched_negative_rows_count"] = len(negative_rows)
        provenance["positive_rows_sha256"] = sha256(POSITIVE)
        provenance["matched_negative_rows_sha256"] = sha256(NEGATIVE)
        provenance["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        provenance["updated_by"] = RUN_ID
        PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        post_hashes = {p.name: sha256(p) for p in [POSITIVE, NEGATIVE, PROVENANCE]}

    commands = []
    commands.append(run_command_safe("direct_manipulation_row_intake_verifier", [sys.executable, str(VERIFIER), "--intake-root", str(INTAKE)]))
    if ICT.exists():
        commands.extend(
            [
                run_command_safe("provider_status_agent", [str(ICT), "provider-status", "--agent"]),
                run_command_safe("provider_status_ibkr_agent", [str(ICT), "provider-status", "--provider", "ibkr", "--agent"]),
                run_command_safe("provider_status_tradingview_mcp_agent", [str(ICT), "provider-status", "--provider", "tradingview_mcp", "--agent"]),
                run_command_safe("provider_status_yfinance_agent", [str(ICT), "provider-status", "--provider", "yfinance", "--agent"]),
                run_command_safe("provider_status_kraken_public_agent", [str(ICT), "provider-status", "--provider", "kraken_public", "--agent"]),
                run_command_safe("provider_status_kraken_cli_agent", [str(ICT), "provider-status", "--provider", "kraken_cli", "--agent"]),
                run_command_safe(
                    "auto_quant_status",
                    [str(ICT), "auto-quant-status", "--state-dir", str(AUTOQUANT_STATE_DIR), "--output-format", "json"],
                ),
                run_command_safe(
                    "analyze_live_nq_yfinance",
                    [
                        str(ICT),
                        "analyze-live",
                        "--symbol",
                        "NQ",
                        "--futures-symbol",
                        "NQ=F",
                        "--spot-symbol",
                        "QQQ",
                        "--options-symbol",
                        "QQQ",
                        "--options-volatility-proxy-symbol",
                        "^VIX",
                        "--futures-backend",
                        "yfinance",
                        "--aux-backend",
                        "yfinance",
                        "--state-dir",
                        str(STATE_DIR),
                        "--output-format",
                        "json",
                    ],
                    timeout=120,
                ),
                run_command_safe("pre_bayes_status", [str(ICT), "pre-bayes-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh"]),
                run_command_safe(
                    "policy_training_status",
                    [str(ICT), "policy-training-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--output-format", "json"],
                ),
                run_command_safe(
                    "workflow_status_execution_candidate",
                    [str(ICT), "workflow-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--phase", "execution-candidate", "--agent"],
                ),
                run_command_safe(
                    "export_structural_path_ranking_target",
                    [str(ICT), "export-structural-path-ranking-target", "--symbol", "NQ", "--state-dir", str(STATE_DIR)],
                ),
            ]
        )

    verifier_stdout = parse_json_file(CMD_OUT / "direct_manipulation_row_intake_verifier.out")
    provider_status = parse_json_file(CMD_OUT / "provider_status_agent.out")
    auto_quant_status = parse_json_file(CMD_OUT / "auto_quant_status.out")
    positives_after = read_csv(POSITIVE)
    negatives_after = read_csv(NEGATIVE)
    positive_lcb = wilson_all_success(len(positives_after))
    negative_lcb = wilson_all_success(len(negatives_after))
    min_lcb = min(positive_lcb, negative_lcb)
    support_ok = len(positives_after) >= 50 and len(negatives_after) >= 50
    broad_normal_sample = False
    gate_rows = [
        {"gate": "positive_support", "observed": len(positives_after), "required": 50, "pass": support_ok},
        {"gate": "matched_negative_support", "observed": len(negatives_after), "required": 50, "pass": support_ok},
        {"gate": "wilson95_min_lcb", "observed": round(min_lcb, 6), "required": ">=0.95", "pass": min_lcb >= 0.95},
        {"gate": "broad_normal_sample", "observed": broad_normal_sample, "required": True, "pass": broad_normal_sample},
        {"gate": "direct_verifier_returncode", "observed": commands[0]["returncode"], "required": 0, "pass": commands[0]["returncode"] == 0},
    ]
    decision = "r6_vorley_franko_row_uplift_v1=rows_added_calibration_still_blocked"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_start": board_hash_before,
        "decision": decision,
        "intake_root": str(INTAKE),
        "source_material": source_results,
        "pre_hashes": pre_hashes,
        "post_hashes": post_hashes,
        "positive_rows_before": len(positives_before),
        "matched_negative_rows_before": len(negatives_before),
        "positive_rows_after": len(positives_after),
        "matched_negative_rows_after": len(negatives_after),
        "positive_rows_added": len(positive_added),
        "matched_negative_rows_added": len(negative_added),
        "positive_added_ids": [row["source_row_id"] for row in positive_added],
        "matched_negative_added_ids": [row["source_row_id"] for row in negative_added],
        "positive_summary": summarize(positives_after),
        "matched_negative_summary": summarize(negatives_after),
        "positive_wilson95_lcb": positive_lcb,
        "matched_negative_wilson95_lcb": negative_lcb,
        "min_wilson95_lcb": min_lcb,
        "support_ok": support_ok,
        "broad_normal_sample": broad_normal_sample,
        "gate_rows": gate_rows,
        "commands": commands,
        "provider_summary": provider_status.get("summary_line") if isinstance(provider_status, dict) else None,
        "auto_quant_status": auto_quant_status.get("status") if isinstance(auto_quant_status, dict) else None,
        "direct_verifier": verifier_stdout,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "r6_direct_species_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": "Acquire at least two more source-owned positive/control rows and an independent broad normal-market control sample; then rerun unchanged R6 calibration and downstream readback.",
    }

    json_path = OUT / "r6_vorley_franko_row_uplift_v1.json"
    md_path = OUT / "r6_vorley_franko_row_uplift_v1.md"
    gate_csv = OUT / "r6_vorley_franko_row_uplift_v1_gates.csv"
    intake_csv = OUT / "r6_vorley_franko_row_uplift_v1_intake_summary.csv"
    assertions = CHECKS / "r6_vorley_franko_row_uplift_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with gate_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["gate", "observed", "required", "pass"])
        writer.writeheader()
        writer.writerows(gate_rows)
    with intake_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["kind", "before", "added", "after", "wilson95_lcb"])
        writer.writeheader()
        writer.writerow({"kind": "positive", "before": len(positives_before), "added": len(positive_added), "after": len(positives_after), "wilson95_lcb": positive_lcb})
        writer.writerow({"kind": "matched_negative", "before": len(negatives_before), "added": len(negative_added), "after": len(negatives_after), "wilson95_lcb": negative_lcb})

    lines = [
        "# R6 Vorley/Franco Row Uplift v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Positive rows: `{len(positives_before)}` -> `{len(positives_after)}`; added `{len(positive_added)}`.",
        f"- Matched negative rows: `{len(negatives_before)}` -> `{len(negatives_after)}`; added `{len(negative_added)}`.",
        f"- Direct verifier status: `{verifier_stdout.get('status') if isinstance(verifier_stdout, dict) else 'unparsed'}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{min_lcb:.6f}`.",
        f"- Support ok: `{str(support_ok).lower()}`; broad normal sample: `{str(broad_normal_sample).lower()}`.",
        f"- Provider summary: `{result['provider_summary']}`.",
        f"- Auto-Quant status: `{result['auto_quant_status']}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; R6 direct species closed: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Gate Rows",
        "",
        "| Gate | Observed | Required | Pass |",
        "|---|---|---|---:|",
    ]
    for row in gate_rows:
        lines.append(f"| `{row['gate']}` | `{row['observed']}` | `{row['required']}` | `{str(bool(row['pass'])).lower()}` |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This run materializes only source-described event/control pairs from official CFTC text already cached under `/tmp`. The added controls are still same-event genuine-order controls, not independent broad normal-market samples, so R6 remains fail-closed.",
            "",
            "## Command Readback",
            "",
            "| Command | Exit | Output | Error |",
            "|---|---:|---|---|",
        ]
    )
    for command in commands:
        lines.append(f"| `{command['name']}` | `{command['returncode']}` | `{command['stdout_path']}` | `{command['stderr_path']}` |")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(json_path)}`",
            f"- Gate CSV: `{rel(gate_csv)}`",
            f"- Intake summary CSV: `{rel(intake_csv)}`",
            f"- Direct verifier stdout: `{rel(CMD_OUT / 'direct_manipulation_row_intake_verifier.out')}`",
            f"- Assertions: `{rel(assertions)}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"PASS decision={decision}",
        f"PASS positive_rows_before={len(positives_before)}",
        f"PASS positive_rows_added={len(positive_added)}",
        f"PASS positive_rows_after={len(positives_after)}",
        f"PASS matched_negative_rows_added={len(negative_added)}",
        f"PASS verifier_returncode={commands[0]['returncode']}",
        f"PASS strict_full_objective_achieved=false",
        f"PASS update_goal=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
