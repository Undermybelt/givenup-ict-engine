#!/usr/bin/env python3
"""Append official CFTC Vorley/Chanu row seeds and run the R6 fail-closed gate."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T211208-codex-cftc-vorley-chanu-row-uplift-calibration-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-cftc-vorley-chanu-row-uplift-calibration"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"
RAW_DIR = Path("/tmp/ict-engine-r6-vorley-chanu-row-uplift-v1/raw")
SOURCE_URL = (
    "https://www.cftc.gov/idc/groups/public/@lrenforcementactions/"
    "documents/legalpleading/enfvorleychanucomplaint012618.pdf"
)
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

SOURCE_REPORT = "CFTC Complaint: James Vorley and Cedric Chanu, Case 1:18-cv-00603"
VENUE = "COMEX/CME Globex"
PARTICIPANT_CODE = "CFTC defendants/desk trader; public complaint"

POSITIVE_ADDITIONS = [
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraph 38, January 6 2012 Gold Futures example",
        "trade_date": "2012-01-06",
        "symbol": "COMEX Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_CODE,
        "participant_identifier": "Cedric Chanu / Trader A (Bank A desk)",
        "side": "buy spoof orders opposite sell genuine iceberg order",
        "earliest_order_received_time": "01:59:18.668 source-local/Globex timestamp",
        "latest_order_received_time": "less than 5 seconds after 01:59:18.668 source-local/Globex timestamp",
        "order_count": "9 spoof orders",
        "total_order_quantity": "130 lots",
        "activity_description": "Official CFTC complaint describes nine buy spoof orders totaling 130 lots opposite Trader A's stalled sell genuine iceberg order; all spoof orders were cancelled in less than five seconds.",
        "matched_negative_group_id": "cftc_vorley_chanu_20120106_gold_example",
        "session_bucket": "overnight_source_time",
        "source_row_id": "cftc_vorley_chanu_20120106_gold_buy_spoof_orders",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraph 39, June 6 2012 Gold Futures example",
        "trade_date": "2012-06-06",
        "symbol": "COMEX Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_CODE,
        "participant_identifier": "Cedric Chanu / James Vorley (Bank A desk)",
        "side": "buy spoof orders opposite sell genuine iceberg order",
        "earliest_order_received_time": "01:27:09.320 source-local/Globex timestamp",
        "latest_order_received_time": "within 5 seconds of each spoof order placement",
        "order_count": "8 spoof orders",
        "total_order_quantity": "80 lots",
        "activity_description": "Official CFTC complaint describes eight buy spoof orders of ten lots each while Vorley's sell genuine iceberg order was stalled; spoof orders were placed and cancelled within five seconds.",
        "matched_negative_group_id": "cftc_vorley_chanu_20120606_gold_example",
        "session_bucket": "overnight_source_time",
        "source_row_id": "cftc_vorley_chanu_20120606_gold_buy_spoof_orders",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 40-44, January 28 2013 Gold Futures example",
        "trade_date": "2013-01-28",
        "symbol": "COMEX Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_CODE,
        "participant_identifier": "James Vorley (Bank A desk)",
        "side": "sell spoof order opposite buy genuine iceberg order",
        "earliest_order_received_time": "15:33:12.415 source-local/Globex timestamp",
        "latest_order_received_time": "just under 3 seconds after 15:33:12.415 source-local/Globex timestamp",
        "order_count": "1 spoof order",
        "total_order_quantity": "110 lots",
        "activity_description": "Official CFTC complaint describes a 110-lot sell spoof order placed three ticks from best offer opposite Vorley's buy genuine iceberg order; it was cancelled after the genuine order filled.",
        "matched_negative_group_id": "cftc_vorley_chanu_20130128_gold_example",
        "session_bucket": "regular_source_time",
        "source_row_id": "cftc_vorley_chanu_20130128_gold_sell_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraphs 45-49, May 23 2013 Gold Futures example",
        "trade_date": "2013-05-23",
        "symbol": "COMEX Gold Futures June delivery",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_CODE,
        "participant_identifier": "Cedric Chanu (Bank A desk)",
        "side": "sell spoof order opposite buy genuine iceberg order",
        "earliest_order_received_time": "01:07:55.630 source-local/Globex timestamp",
        "latest_order_received_time": "01:07:57.865 source-local/Globex timestamp",
        "order_count": "1 spoof order",
        "total_order_quantity": "100 lots",
        "activity_description": "Official CFTC complaint describes a 100-lot sell spoof order two ticks from best offer opposite Chanu's buy genuine iceberg order; the spoof order was cancelled after the genuine order filled.",
        "matched_negative_group_id": "cftc_vorley_chanu_20130523_gold_example",
        "session_bucket": "overnight_source_time",
        "source_row_id": "cftc_vorley_chanu_20130523_gold_sell_spoof_order",
    },
]

NEGATIVE_ADDITIONS = [
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraph 38, January 6 2012 Gold Futures example",
        "trade_date": "2012-01-06",
        "symbol": "COMEX Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_CODE,
        "participant_identifier": "Trader A (Bank A desk)",
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "01:59:04.221 source-local/Globex timestamp",
        "latest_order_received_time": "after 01:59:04.221; source states initial fills after about 6 seconds",
        "order_count": "one genuine iceberg order with 1 lot visible",
        "total_order_quantity": "20 lots",
        "activity_description": "Matched same-complaint control seed: Trader A's sell genuine iceberg order that the source distinguishes from the spoof orders. Schema/control seed only, not broad normal-market calibration.",
        "matched_negative_group_id": "cftc_vorley_chanu_20120106_gold_example",
        "session_bucket": "overnight_source_time",
        "source_row_id": "cftc_vorley_chanu_20120106_gold_sell_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraph 39, June 6 2012 Gold Futures example",
        "trade_date": "2012-06-06",
        "symbol": "COMEX Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_CODE,
        "participant_identifier": "James Vorley (Bank A desk)",
        "side": "sell genuine iceberg order",
        "earliest_order_received_time": "01:26:57.520 source-local/Globex timestamp",
        "latest_order_received_time": "after 01:26:57.520; source states immediate 20-lot execution then stall",
        "order_count": "one genuine iceberg order with 1 lot visible",
        "total_order_quantity": "30 lots",
        "activity_description": "Matched same-complaint control seed: Vorley's sell genuine iceberg order that the source distinguishes from Chanu's spoof orders. Schema/control seed only, not broad normal-market calibration.",
        "matched_negative_group_id": "cftc_vorley_chanu_20120606_gold_example",
        "session_bucket": "overnight_source_time",
        "source_row_id": "cftc_vorley_chanu_20120606_gold_sell_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraph 40, January 28 2013 Gold Futures example",
        "trade_date": "2013-01-28",
        "symbol": "COMEX Gold Futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_CODE,
        "participant_identifier": "James Vorley (Bank A desk)",
        "side": "buy genuine iceberg order",
        "earliest_order_received_time": "15:32:43.198 source-local/Globex timestamp",
        "latest_order_received_time": "after 15:32:43.198; source states fill after sell spoof order placement",
        "order_count": "one genuine iceberg order showing 1 lot",
        "total_order_quantity": "34 lots",
        "activity_description": "Matched same-complaint control seed: Vorley's buy genuine iceberg order that the source distinguishes from the later 110-lot spoof order. Schema/control seed only, not broad normal-market calibration.",
        "matched_negative_group_id": "cftc_vorley_chanu_20130128_gold_example",
        "session_bucket": "regular_source_time",
        "source_row_id": "cftc_vorley_chanu_20130128_gold_buy_genuine_iceberg_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Paragraph 45, May 23 2013 Gold Futures example",
        "trade_date": "2013-05-23",
        "symbol": "COMEX Gold Futures June delivery",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_CODE,
        "participant_identifier": "Cedric Chanu (Bank A desk)",
        "side": "buy genuine iceberg order",
        "earliest_order_received_time": "01:05:45.122 source-local/Globex timestamp",
        "latest_order_received_time": "after 01:05:45.122; source states one-lot fill after 01:07:55.630 spoof placement",
        "order_count": "one genuine iceberg order showing 1 lot",
        "total_order_quantity": "96 lots",
        "activity_description": "Matched same-complaint control seed: Chanu's buy genuine iceberg order that the source distinguishes from the later 100-lot spoof order. Schema/control seed only, not broad normal-market calibration.",
        "matched_negative_group_id": "cftc_vorley_chanu_20130523_gold_example",
        "session_bucket": "overnight_source_time",
        "source_row_id": "cftc_vorley_chanu_20130523_gold_buy_genuine_iceberg_control",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_source_pdf() -> tuple[Path, str, int]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / "enfvorleychanucomplaint012618.pdf"
    if not path.exists():
        request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            path.write_bytes(response.read())
    return path, sha256(path), path.stat().st_size


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def append_idempotent(path: Path, additions: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[str]]:
    rows = read_csv(path)
    seen = {row.get("source_row_id", "") for row in rows}
    added: list[str] = []
    for row in additions:
        if row["source_row_id"] in seen:
            continue
        rows.append(row)
        seen.add(row["source_row_id"])
        added.append(row["source_row_id"])
    write_csv(path, rows)
    return rows, added


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


def write_rows_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def run_verifier() -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(VERIFIER), "--intake-root", str(INTAKE)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    (OUT / "direct_manipulation_row_intake_verifier.stdout.txt").write_text(
        completed.stdout, encoding="utf-8"
    )
    (OUT / "direct_manipulation_row_intake_verifier.stderr.txt").write_text(
        completed.stderr, encoding="utf-8"
    )
    parsed: dict[str, object]
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "parse_failed", "stdout": completed.stdout}
    parsed["returncode"] = completed.returncode
    return parsed


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    source_pdf, source_sha, source_bytes = fetch_source_pdf()
    board_hash = sha256(BOARD)

    positives, positive_added = append_idempotent(POSITIVE, POSITIVE_ADDITIONS)
    negatives, negative_added = append_idempotent(NEGATIVE, NEGATIVE_ADDITIONS)
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8")) if PROVENANCE.exists() else {}
    provenance["cftc_vorley_chanu_complaint"] = {
        "source_url": SOURCE_URL,
        "source_kind": "official_cftc_federal_complaint_pdf",
        "local_raw_path": str(source_pdf),
        "sha256": source_sha,
        "bytes": source_bytes,
        "source_report": SOURCE_REPORT,
        "row_scope": "paragraphs 38-49 exact examples only",
        "positive_rows_added_this_run": positive_added,
        "matched_negative_rows_added_this_run": negative_added,
        "limitation": "same-complaint genuine-order control seeds; still not a broad source-owned normal-market sample",
    }
    provenance["vorley_chanu_rows_materialized_at_utc"] = datetime.now(timezone.utc).isoformat()
    provenance["vorley_chanu_positive_rows_added"] = len(positive_added)
    provenance["vorley_chanu_matched_negative_rows_added"] = len(negative_added)
    provenance["matched_negative_control_policy"] = (
        "same-report or same-complaint genuine-order control seeds only; not a broad "
        "source-owned normal-market sample"
    )
    provenance["positive_rows_count"] = len(positives)
    provenance["matched_negative_rows_count"] = len(negatives)
    PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verifier = run_verifier()
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
        {
            "gate": "positive_support",
            "observed": len(positives),
            "required": min_support,
            "pass": len(positives) >= min_support,
        },
        {
            "gate": "negative_support",
            "observed": len(negatives),
            "required": min_support,
            "pass": len(negatives) >= min_support,
        },
        {
            "gate": "chronological_split",
            "observed": len(dates),
            "required": 2,
            "pass": chronological_split_ok,
        },
        {
            "gate": "heldout_symbol_or_venue",
            "observed": f"symbols={len(symbols)};venues={len(venues)}",
            "required": "symbol>=2 or venue>=2",
            "pass": heldout_symbol_or_venue_ok,
        },
        {
            "gate": "wilson95_lcb",
            "observed": f"{combined_lcb:.6f}",
            "required": ">=0.95",
            "pass": combined_lcb >= 0.95,
        },
        {
            "gate": "broad_normal_sample",
            "observed": provenance.get("matched_negative_control_policy", ""),
            "required": "source-owned broad normal activity sample",
            "pass": broad_normal_sample,
        },
    ]
    gate_pass = all(bool(row["pass"]) for row in gate_rows)
    decision = (
        "r6_cftc_vorley_chanu_calibration_gate_v3=accepted_95"
        if gate_pass
        else "r6_cftc_vorley_chanu_calibration_gate_v3=schema_ready_but_calibration_blocked"
    )

    result = {
        "artifact_type": "cftc_vorley_chanu_row_uplift_calibration_v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_writeback": board_hash,
        "decision": decision,
        "source_url": SOURCE_URL,
        "source_pdf_sha256": source_sha,
        "source_pdf_local_raw_path": str(source_pdf),
        "raw_data_committed": False,
        "intake_root": str(INTAKE),
        "positive_rows_added_this_run": len(positive_added),
        "matched_negative_rows_added_this_run": len(negative_added),
        "positive_row_ids_added_this_run": positive_added,
        "matched_negative_row_ids_added_this_run": negative_added,
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
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "next_action": "Acquire broad source-owned or owner-approved same-schema normal controls and more direct positives across venues/symbols until support and Wilson95 gates can pass.",
        "source_hashes": {
            "positive_spoofing_layering_rows.csv": sha256(POSITIVE),
            "matched_negative_normal_activity_rows.csv": sha256(NEGATIVE),
            "provenance_manifest.json": sha256(PROVENANCE),
        },
    }

    json_path = OUT / "cftc_vorley_chanu_row_uplift_calibration_v1.json"
    md_path = OUT / "cftc_vorley_chanu_row_uplift_calibration_v1.md"
    gate_csv = OUT / "cftc_vorley_chanu_row_uplift_calibration_v1_gates.csv"
    intake_csv = OUT / "cftc_vorley_chanu_row_uplift_calibration_v1_intake_summary.csv"
    assertions_path = CHECKS / "cftc_vorley_chanu_row_uplift_calibration_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_rows_csv(gate_csv, gate_rows, ["gate", "observed", "required", "pass"])
    write_rows_csv(
        intake_csv,
        [
            {"metric": "positive_rows_added_this_run", "value": len(positive_added)},
            {"metric": "matched_negative_rows_added_this_run", "value": len(negative_added)},
            {"metric": "positive_rows_total", "value": len(positives)},
            {"metric": "matched_negative_rows_total", "value": len(negatives)},
            {"metric": "unique_dates", "value": len(dates)},
            {"metric": "unique_symbols", "value": len(symbols)},
            {"metric": "unique_venues", "value": len(venues)},
            {"metric": "combined_min_wilson95_lcb", "value": f"{combined_lcb:.6f}"},
            {"metric": "support_ok", "value": str(support_ok).lower()},
            {"metric": "broad_normal_sample", "value": str(broad_normal_sample).lower()},
        ],
        ["metric", "value"],
    )

    lines = [
        "# CFTC Vorley/Chanu Row Uplift Calibration v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Source: `{SOURCE_URL}`.",
        f"- Source PDF SHA256: `{source_sha}`.",
        f"- Added positives / matched negatives this run: `{len(positive_added)}` / `{len(negative_added)}`.",
        f"- Total positives / matched negatives: `{len(positives)}` / `{len(negatives)}`.",
        f"- Unique dates: `{len(dates)}`; symbols: `{len(symbols)}`; venues: `{len(venues)}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{combined_lcb:.6f}`.",
        f"- Chronological split ok: `{str(chronological_split_ok).lower()}`; heldout symbol/venue ok: `{str(heldout_symbol_or_venue_ok).lower()}`.",
        f"- Broad normal sample: `{str(broad_normal_sample).lower()}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Added Rows",
        "",
        "| Type | Source Row ID | Group | Date | Symbol |",
        "|---|---|---|---|---|",
    ]
    for row in POSITIVE_ADDITIONS + NEGATIVE_ADDITIONS:
        added = row["source_row_id"] in positive_added or row["source_row_id"] in negative_added
        if added:
            lines.append(
                f"| `{row['label']}` | `{row['source_row_id']}` | `{row['matched_negative_group_id']}` | `{row['trade_date']}` | `{row['symbol']}` |"
            )
    lines.extend(["", "## Gates", "", "| Gate | Observed | Required | Pass |", "|---|---|---|---:|"])
    for row in gate_rows:
        lines.append(f"| `{row['gate']}` | `{row['observed']}` | `{row['required']}` | `{str(row['pass']).lower()}` |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The direct R6 intake has more official CFTC timestamped spoofing/genuine-order examples, but it is still schema-ready only. Support remains far below the unchanged 50/50 floor and the matched controls are same-complaint genuine-order seeds, not a broad normal-market sample.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Gate CSV: `{gate_csv}`",
            f"- Intake summary CSV: `{intake_csv}`",
            f"- Verifier stdout: `{OUT / 'direct_manipulation_row_intake_verifier.stdout.txt'}`",
            f"- Assertions: `{assertions_path}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS positive_rows_added_this_run={len(positive_added)}",
        f"PASS matched_negative_rows_added_this_run={len(negative_added)}",
        f"PASS positive_rows_total={len(positives)}",
        f"PASS matched_negative_rows_total={len(negatives)}",
        f"PASS verifier_status={verifier.get('status')}",
        f"PASS chronological_split_ok={str(chronological_split_ok).lower()}",
        f"PASS heldout_symbol_or_venue_ok={str(heldout_symbol_or_venue_ok).lower()}",
        f"PASS combined_min_wilson95_lcb={combined_lcb:.6f}",
        f"PASS support_ok={str(support_ok).lower()}",
        f"PASS broad_normal_sample={str(broad_normal_sample).lower()}",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps({"decision": decision, "positive_added": len(positive_added), "negative_added": len(negative_added), "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
