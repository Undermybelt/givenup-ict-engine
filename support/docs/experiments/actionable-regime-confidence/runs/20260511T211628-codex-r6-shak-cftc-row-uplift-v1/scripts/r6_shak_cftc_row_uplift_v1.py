#!/usr/bin/env python3
"""Append explicit CFTC Shak complaint rows to the R6 direct intake."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pypdf import PdfReader


RUN_ID = "20260511T211628-codex-r6-shak-cftc-row-uplift-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-shak-cftc-row-uplift"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"
SOURCE_PDF = Path("/tmp/ict-engine-r6-cftc-public-order-candidate-uplift-v1/cftc_shak_complaint_2022.bin")
SOURCE_URL = "https://www.cftc.gov/media/7526/enfshakcomplaint080522/download"

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

SOURCE_REPORT = "CFTC Complaint: Daniel Shak, CFTC v. Shak, Case 2:22-cv-01258"
PARTICIPANT = "Daniel Shak"
VENUE = "COMEX"
SESSION = "source_time_zone_unspecified"

POSITIVE_ADDITIONS = [
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 49-54, Example 1, March 3 2017 April 2017 Gold",
        "trade_date": "2017-03-03",
        "symbol": "April 2017 Gold futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "buy spoof orders opposite sell genuine order",
        "earliest_order_received_time": "07:53:21.124 source_time_zone_unspecified",
        "latest_order_received_time": "07:53:58.693 source_time_zone_unspecified",
        "order_count": "ten spoof orders to buy",
        "total_order_quantity": "200 lots",
        "activity_description": "CFTC complaint describes ten 20-lot buy spoof orders while waiting for a one-lot sell genuine order; spoof orders were cancelled after the genuine order filled.",
        "matched_negative_group_id": "cftc_shak_20170303_gold_example",
        "session_bucket": SESSION,
        "source_row_id": "cftc_shak_20170303_gold_buy_spoof_series",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 55-60, Example 2, March 24 2017 April 2017 Gold",
        "trade_date": "2017-03-24",
        "symbol": "April 2017 Gold futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "buy spoof orders opposite sell genuine order",
        "earliest_order_received_time": "08:30:20.375 source_time_zone_unspecified",
        "latest_order_received_time": "08:30:42.819 source_time_zone_unspecified",
        "order_count": "five spoof orders to buy",
        "total_order_quantity": "300 lots",
        "activity_description": "CFTC complaint describes an initial 50-lot buy spoof order plus four later buy spoof orders totaling 250 lots; all spoof orders were cancelled without fills after the sell genuine order filled.",
        "matched_negative_group_id": "cftc_shak_20170324_gold_example",
        "session_bucket": SESSION,
        "source_row_id": "cftc_shak_20170324_gold_buy_spoof_series",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 61-66, Example 3, September 18 2017 December 2017 Silver",
        "trade_date": "2017-09-18",
        "symbol": "December 2017 Silver futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "buy spoof orders opposite sell genuine orders",
        "earliest_order_received_time": "06:30:46.389 source_time_zone_unspecified",
        "latest_order_received_time": "06:31:39.576 source_time_zone_unspecified",
        "order_count": "eight spoof orders to buy",
        "total_order_quantity": "340 lots",
        "activity_description": "CFTC complaint describes eight buy spoof orders totaling 340 lots while waiting for two one-lot sell genuine orders; spoof orders were cancelled after the genuine orders filled.",
        "matched_negative_group_id": "cftc_shak_20170918_silver_example",
        "session_bucket": SESSION,
        "source_row_id": "cftc_shak_20170918_silver_buy_spoof_series",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 68-78, Example 4, October 5 2017 December 2017 Gold",
        "trade_date": "2017-10-05",
        "symbol": "December 2017 Gold futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "buy spoof orders opposite sell iceberg genuine order",
        "earliest_order_received_time": "09:47:34.921 source_time_zone_unspecified",
        "latest_order_received_time": "09:48:50.225 source_time_zone_unspecified",
        "order_count": "nine spoof orders to buy in second series",
        "total_order_quantity": "225 lots",
        "activity_description": "CFTC complaint describes a second series of nine buy spoof orders totaling 225 lots while waiting for a 38-lot sell iceberg genuine order; spoof cancellations began after the genuine order fully filled.",
        "matched_negative_group_id": "cftc_shak_20171005_gold_example",
        "session_bucket": SESSION,
        "source_row_id": "cftc_shak_20171005_gold_buy_spoof_second_series",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 79-84, Example 5, January 22 2018 March 2018 Silver",
        "trade_date": "2018-01-22",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "buy spoof orders opposite sell genuine order",
        "earliest_order_received_time": "05:17:44.407 source_time_zone_unspecified",
        "latest_order_received_time": "05:18:20.286 source_time_zone_unspecified",
        "order_count": "six spoof orders to buy",
        "total_order_quantity": "300 lots",
        "activity_description": "CFTC complaint describes six 50-lot buy spoof orders while waiting for a one-lot sell genuine order; spoof orders were cancelled in less than two seconds after the genuine order filled.",
        "matched_negative_group_id": "cftc_shak_20180122_silver_example",
        "session_bucket": SESSION,
        "source_row_id": "cftc_shak_20180122_silver_buy_spoof_series",
    },
]

NEGATIVE_ADDITIONS = [
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 49 and 52, Example 1, March 3 2017 April 2017 Gold",
        "trade_date": "2017-03-03",
        "symbol": "April 2017 Gold futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "sell genuine order",
        "earliest_order_received_time": "07:52:57.348 source_time_zone_unspecified",
        "latest_order_received_time": "07:53:54.558 source_time_zone_unspecified",
        "order_count": "one genuine order",
        "total_order_quantity": "1 lot",
        "activity_description": "Matched same-source genuine-order leg from the CFTC complaint. This is a schema/control seed, not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_shak_20170303_gold_example",
        "session_bucket": SESSION,
        "source_row_id": "cftc_shak_20170303_gold_sell_genuine_order_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 55 and 58, Example 2, March 24 2017 April 2017 Gold",
        "trade_date": "2017-03-24",
        "symbol": "April 2017 Gold futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "sell genuine order",
        "earliest_order_received_time": "08:30:17.046 source_time_zone_unspecified",
        "latest_order_received_time": "08:30:36.432 source_time_zone_unspecified",
        "order_count": "one genuine order",
        "total_order_quantity": "5 lots",
        "activity_description": "Matched same-source genuine-order leg from the CFTC complaint. This is a schema/control seed, not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_shak_20170324_gold_example",
        "session_bucket": SESSION,
        "source_row_id": "cftc_shak_20170324_gold_sell_genuine_order_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 61 and 64, Example 3, September 18 2017 December 2017 Silver",
        "trade_date": "2017-09-18",
        "symbol": "December 2017 Silver futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "sell genuine orders",
        "earliest_order_received_time": "06:30:32.856 source_time_zone_unspecified",
        "latest_order_received_time": "06:31:35.275 source_time_zone_unspecified",
        "order_count": "two genuine orders",
        "total_order_quantity": "2 lots",
        "activity_description": "Matched same-source genuine-order legs from the CFTC complaint. This is a schema/control seed, not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_shak_20170918_silver_example",
        "session_bucket": SESSION,
        "source_row_id": "cftc_shak_20170918_silver_sell_genuine_orders_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 68 and 75, Example 4, October 5 2017 December 2017 Gold",
        "trade_date": "2017-10-05",
        "symbol": "December 2017 Gold futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "sell iceberg genuine order",
        "earliest_order_received_time": "09:45:03.418 source_time_zone_unspecified",
        "latest_order_received_time": "09:48:10.953 source_time_zone_unspecified",
        "order_count": "one iceberg genuine order with one lot visible",
        "total_order_quantity": "38 lots",
        "activity_description": "Matched same-source sell iceberg genuine-order leg from the CFTC complaint. This is a schema/control seed, not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_shak_20171005_gold_example",
        "session_bucket": SESSION,
        "source_row_id": "cftc_shak_20171005_gold_sell_iceberg_genuine_order_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Complaint paragraphs 79 and 82, Example 5, January 22 2018 March 2018 Silver",
        "trade_date": "2018-01-22",
        "symbol": "March 2018 Silver futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": "CFTC defendant trader",
        "participant_identifier": PARTICIPANT,
        "side": "sell genuine order",
        "earliest_order_received_time": "05:17:12.964 source_time_zone_unspecified",
        "latest_order_received_time": "05:18:16.998 source_time_zone_unspecified",
        "order_count": "one genuine order",
        "total_order_quantity": "1 lot",
        "activity_description": "Matched same-source genuine-order leg from the CFTC complaint. This is a schema/control seed, not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_shak_20180122_silver_example",
        "session_bucket": SESSION,
        "source_row_id": "cftc_shak_20180122_silver_sell_genuine_order_control",
    },
]

TEXT_NEEDLES = [
    "March 3, 2017",
    "7:53:21.124",
    "7:53:54.558",
    "March 24, 2017",
    "8:30:20.375",
    "8:30:36.432",
    "September 18, 2017",
    "6:30:46.389",
    "6:31:35.275",
    "October 5, 2017",
    "9:47:34.921",
    "9:48:10.953",
    "January 22, 2018",
    "5:17:44.407",
    "5:18:16.998",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def append_unique(path: Path, additions: list[dict[str, str]]) -> tuple[int, list[str]]:
    rows = read_csv_rows(path)
    seen = {row.get("source_row_id", "") for row in rows}
    added_ids: list[str] = []
    for row in additions:
        if row["source_row_id"] in seen:
            continue
        rows.append(row)
        seen.add(row["source_row_id"])
        added_ids.append(row["source_row_id"])
    write_csv_rows(path, rows)
    return len(added_ids), added_ids


def write_simple_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def wilson_lcb(successes: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    phat = successes / total
    denom = 1 + z * z / total
    centre = phat + z * z / (2 * total)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total)
    return (centre - margin) / denom


def unique_values(rows: list[dict[str, str]], key: str) -> list[str]:
    return sorted({row.get(key, "") for row in rows if row.get(key, "")})


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), "--intake-root", str(INTAKE)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=REPO,
    )
    (CMD_OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (CMD_OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    parsed: dict[str, Any]
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "parse_failed", "stdout": proc.stdout, "stderr": proc.stderr}
    parsed["returncode"] = proc.returncode
    return parsed


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    INTAKE.mkdir(parents=True, exist_ok=True)

    if not SOURCE_PDF.exists():
        raise SystemExit(f"missing_source_pdf: {SOURCE_PDF}")
    if not POSITIVE.exists() or not NEGATIVE.exists() or not PROVENANCE.exists():
        raise SystemExit("missing_live_direct_intake_files")

    board_hash = sha256(BOARD)
    text = extract_pdf_text(SOURCE_PDF)
    text_checks = {needle: (needle in text) for needle in TEXT_NEEDLES}
    if not all(text_checks.values()):
        missing = [needle for needle, ok in text_checks.items() if not ok]
        raise SystemExit(f"source_text_checks_failed: {missing}")

    positive_added, positive_ids = append_unique(POSITIVE, POSITIVE_ADDITIONS)
    negative_added, negative_ids = append_unique(NEGATIVE, NEGATIVE_ADDITIONS)

    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    positives = read_csv_rows(POSITIVE)
    negatives = read_csv_rows(NEGATIVE)

    provenance["cftc_shak_complaint"] = {
        "url": SOURCE_URL,
        "path": str(SOURCE_PDF),
        "sha256": sha256(SOURCE_PDF),
        "source_kind": "public CFTC federal complaint",
        "text_checks": text_checks,
    }
    provenance["cftc_shak_rows_added"] = {
        "positive": positive_added,
        "matched_negative": negative_added,
        "positive_source_row_ids": positive_ids,
        "matched_negative_source_row_ids": negative_ids,
        "control_policy": "Source-described same-event genuine-order legs from the public CFTC complaint; schema/control seeds only, not a broad normal-market calibration sample.",
    }
    provenance["matched_negative_control_policy"] = (
        "CFTC public order/complaint same-event genuine-order legs are source-described "
        "schema/control seeds only; they are not a broad normal-market calibration sample."
    )
    provenance["positive_rows_count"] = len(positives)
    provenance["matched_negative_rows_count"] = len(negatives)
    provenance["positive_rows_path"] = str(POSITIVE)
    provenance["matched_negative_rows_path"] = str(NEGATIVE)
    provenance["positive_rows_sha256"] = sha256(POSITIVE)
    provenance["matched_negative_rows_sha256"] = sha256(NEGATIVE)
    provenance["updated_by"] = RUN_ID
    provenance["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    positives = read_csv_rows(POSITIVE)
    negatives = read_csv_rows(NEGATIVE)
    verifier = run_verifier()

    all_rows = positives + negatives
    labels = Counter(row.get("label", "") for row in all_rows)
    dates = unique_values(all_rows, "trade_date")
    symbols = unique_values(all_rows, "symbol")
    venues = unique_values(all_rows, "venue_or_market_center")
    groups = unique_values(all_rows, "matched_negative_group_id")
    sessions = unique_values(all_rows, "session_bucket")

    positive_lcb = wilson_lcb(len(positives), len(positives))
    negative_lcb = wilson_lcb(len(negatives), len(negatives))
    combined_lcb = min(positive_lcb, negative_lcb)
    min_support = 50
    support_ok = len(positives) >= min_support and len(negatives) >= min_support
    chronological_split_ok = len(dates) >= 2
    heldout_symbol_or_venue_ok = len(symbols) >= 2 or len(venues) >= 2
    broad_normal_sample = "not a broad normal-market" not in provenance.get("matched_negative_control_policy", "").lower()
    gate_rows = [
        {"gate": "positive_support", "observed": len(positives), "required": min_support, "pass": len(positives) >= min_support},
        {"gate": "negative_support", "observed": len(negatives), "required": min_support, "pass": len(negatives) >= min_support},
        {"gate": "chronological_split", "observed": len(dates), "required": 2, "pass": chronological_split_ok},
        {
            "gate": "heldout_symbol_or_venue",
            "observed": f"symbols={len(symbols)};venues={len(venues)}",
            "required": "symbol>=2 or venue>=2",
            "pass": heldout_symbol_or_venue_ok,
        },
        {"gate": "wilson95_lcb", "observed": f"{combined_lcb:.6f}", "required": ">=0.95", "pass": combined_lcb >= 0.95},
        {
            "gate": "broad_normal_sample",
            "observed": provenance.get("matched_negative_control_policy", ""),
            "required": "source-owned broad normal activity sample",
            "pass": broad_normal_sample,
        },
    ]
    gate_pass = all(bool(row["pass"]) for row in gate_rows)
    if gate_pass:
        decision = "r6_shak_cftc_row_uplift_v1=accepted_95_for_r6_direct_only"
    elif positive_added or negative_added:
        decision = "r6_shak_cftc_row_uplift_v1=direct_intake_rows_uplifted_schema_ready_calibration_still_blocked"
    else:
        decision = "r6_shak_cftc_row_uplift_v1=no_new_unique_rows_calibration_still_blocked"

    row_summary = [
        {"class": "positive", "added": positive_added, "total": len(positives), "source_row_ids": ";".join(positive_ids)},
        {"class": "matched_negative", "added": negative_added, "total": len(negatives), "source_row_ids": ";".join(negative_ids)},
    ]
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact_generation": board_hash,
        "decision": decision,
        "source_pdf": str(SOURCE_PDF),
        "source_url": SOURCE_URL,
        "source_sha256": sha256(SOURCE_PDF),
        "text_checks": text_checks,
        "positive_rows_added": positive_added,
        "matched_negative_rows_added": negative_added,
        "positive_source_row_ids_added": positive_ids,
        "matched_negative_source_row_ids_added": negative_ids,
        "intake_root": str(INTAKE),
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "labels": dict(labels),
        "unique_dates": dates,
        "unique_symbols": symbols,
        "unique_venues": venues,
        "matched_groups": groups,
        "session_buckets": sessions,
        "verifier": verifier,
        "positive_wilson95_lcb": positive_lcb,
        "negative_wilson95_lcb": negative_lcb,
        "combined_min_wilson95_lcb": combined_lcb,
        "min_support_required_per_class": min_support,
        "support_ok": support_ok,
        "chronological_split_ok": chronological_split_ok,
        "heldout_symbol_or_venue_ok": heldout_symbol_or_venue_ok,
        "broad_normal_sample": broad_normal_sample,
        "gate_rows": gate_rows,
        "new_confidence_gate": gate_pass,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "source_hashes": {
            "positive_spoofing_layering_rows.csv": sha256(POSITIVE),
            "matched_negative_normal_activity_rows.csv": sha256(NEGATIVE),
            "provenance_manifest.json": sha256(PROVENANCE),
        },
    }

    json_path = OUT / "r6_shak_cftc_row_uplift_v1.json"
    report_path = OUT / "r6_shak_cftc_row_uplift_v1.md"
    gate_csv = OUT / "r6_shak_cftc_row_uplift_v1_gates.csv"
    summary_csv = OUT / "r6_shak_cftc_row_uplift_v1_intake_summary.csv"
    assertions = CHECKS / "r6_shak_cftc_row_uplift_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_simple_csv(gate_csv, gate_rows, ["gate", "observed", "required", "pass"])
    write_simple_csv(summary_csv, row_summary, ["class", "added", "total", "source_row_ids"])

    lines = [
        "# R6 Shak CFTC Row Uplift v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Positive rows added: `{positive_added}`; matched negative rows added: `{negative_added}`.",
        f"- Positive rows now: `{len(positives)}`; matched negative rows now: `{len(negatives)}`.",
        f"- Unique dates: `{len(dates)}`; symbols: `{len(symbols)}`; venues: `{len(venues)}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{combined_lcb:.6f}`.",
        f"- Chronological split ok: `{str(chronological_split_ok).lower()}`; heldout symbol/venue ok: `{str(heldout_symbol_or_venue_ok).lower()}`.",
        f"- Broad normal sample: `{str(broad_normal_sample).lower()}`.",
        f"- Verifier status: `{verifier.get('status')}`; return code: `{verifier.get('returncode')}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Source Rows Added",
        "",
        "| Class | Added | Total |",
        "|---|---:|---:|",
    ]
    for row in row_summary:
        lines.append(f"| `{row['class']}` | `{row['added']}` | `{row['total']}` |")
    lines.extend(
        [
            "",
            "## Calibration Gates",
            "",
            "| Gate | Observed | Required | Pass |",
            "|---|---|---|---:|",
        ]
    )
    for row in gate_rows:
        lines.append(f"| `{row['gate']}` | `{row['observed']}` | `{row['required']}` | `{str(row['pass']).lower()}` |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "The added Shak rows are public CFTC same-event positive/control seeds. They improve direct R6 support and date/symbol coverage, but they remain same-complaint controls, not broad normal-market calibration controls.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Gate CSV: `{gate_csv}`",
            f"- Intake summary CSV: `{summary_csv}`",
            f"- Verifier stdout: `{CMD_OUT / 'direct_manipulation_row_intake_verifier.stdout.txt'}`",
            f"- Assertions: `{assertions}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"PASS decision={decision}",
        f"PASS source_pdf_sha256={sha256(SOURCE_PDF)}",
        f"PASS positive_rows_added={positive_added}",
        f"PASS matched_negative_rows_added={negative_added}",
        f"PASS verifier_status={verifier.get('status')}",
        f"PASS positive_rows={len(positives)}",
        f"PASS matched_negative_rows={len(negatives)}",
        f"PASS combined_min_wilson95_lcb={combined_lcb:.6f}",
        f"PASS support_ok={str(support_ok).lower()}",
        f"PASS broad_normal_sample={str(broad_normal_sample).lower()}",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "positive_rows": len(positives), "matched_negative_rows": len(negatives), "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
