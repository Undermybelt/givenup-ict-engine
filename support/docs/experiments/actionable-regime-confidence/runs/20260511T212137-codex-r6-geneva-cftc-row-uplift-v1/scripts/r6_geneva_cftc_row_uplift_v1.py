#!/usr/bin/env python3
"""Append local cached CFTC Geneva order examples and rerun the R6 gate."""

from __future__ import annotations

import csv
import fcntl
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T212137-codex-r6-geneva-cftc-row-uplift-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-geneva-cftc-row-uplift"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
POSITIVE = INTAKE / "positive_spoofing_layering_rows.csv"
NEGATIVE = INTAKE / "matched_negative_normal_activity_rows.csv"
PROVENANCE = INTAKE / "provenance_manifest.json"
LOCK = INTAKE / ".r6_geneva_cftc_row_uplift_v1.lock"
SOURCE_URL = "https://www.cftc.gov/sites/default/files/2018-09/enfgenevaorder092018.pdf"
SOURCE_PDF_CANDIDATES = [
    Path("/private/tmp/ict-engine-cftc-official-spoofing-expansion/geneva.pdf"),
    Path("/private/tmp/ict-engine-cftc-order-expansion-probe/enfgenevaorder092018.pdf"),
    Path("/private/tmp/ict-engine-r6-cftc-public-order-candidate-uplift-v1/cftc_geneva_order_2018.bin"),
]
SOURCE_TEXT_CANDIDATES = [
    Path("/private/tmp/ict-engine-cftc-official-spoofing-expansion/geneva.txt"),
    Path("/private/tmp/ict-engine-cftc-order-expansion-probe/enfgenevaorder092018.gs.txt"),
]
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

SOURCE_REPORT = "CFTC Order: In re Geneva Trading USA, LLC, CFTC No. 18-25"
VENUE = "CME Group registered futures market (source order)"
PARTICIPANT_CODE = "CFTC respondent trader; public administrative order"

POSITIVE_ADDITIONS = [
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Facts paragraph, April 24 2013 RBOB gasoline example",
        "trade_date": "2013-04-24",
        "symbol": "RBOB gasoline futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_CODE,
        "participant_identifier": "Geneva Trader A",
        "side": "buy spoof orders opposite sell genuine order",
        "earliest_order_received_time": "source_relative_five_second_window",
        "latest_order_received_time": "about 300 milliseconds before spoof cancellation",
        "order_count": "multiple spoof orders",
        "total_order_quantity": "over 40 lots",
        "activity_description": "Official CFTC order states Trader A placed multiple buy spoof orders totaling over forty lots in RBOB gasoline futures, at price levels 1-4, while using a two-lot sell genuine order that immediately filled; spoof orders were then canceled.",
        "matched_negative_group_id": "cftc_geneva_20130424_rbob_example",
        "session_bucket": "source_time_not_stated",
        "source_row_id": "cftc_geneva_20130424_rbob_buy_spoof_orders",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Facts paragraph, May 21 2013 light sweet crude oil example",
        "trade_date": "2013-05-21",
        "symbol": "light sweet crude oil futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_CODE,
        "participant_identifier": "Geneva Trader B",
        "side": "sell spoof order opposite buy genuine order",
        "earliest_order_received_time": "source_relative_before_genuine_order",
        "latest_order_received_time": "about 200 milliseconds after genuine order execution",
        "order_count": "one spoof order",
        "total_order_quantity": "200 lots",
        "activity_description": "Official CFTC order states Trader B placed a 200-lot sell spoof order in light sweet crude oil futures, placed a 15-lot buy genuine order about 400 milliseconds later, and canceled the spoof order about 200 milliseconds after the genuine order executed.",
        "matched_negative_group_id": "cftc_geneva_20130521_crude_example",
        "session_bucket": "source_time_not_stated",
        "source_row_id": "cftc_geneva_20130521_crude_sell_spoof_order",
    },
    {
        "label": "positive_spoofing_layering",
        "source_report": SOURCE_REPORT,
        "source_section": "Facts paragraph, September 1 2015 Soft Red Winter wheat example",
        "trade_date": "2015-09-01",
        "symbol": "Soft Red Winter wheat futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_CODE,
        "participant_identifier": "Geneva Trader C",
        "side": "buy spoof orders opposite sell genuine order",
        "earliest_order_received_time": "about five minutes after sell genuine order",
        "latest_order_received_time": "about six seconds after genuine order fill",
        "order_count": "15 spoof orders",
        "total_order_quantity": "75 lots",
        "activity_description": "Official CFTC order states Trader C placed a five-lot sell genuine order, then placed fifteen five-lot buy spoof orders totaling 75 lots over four seconds; the genuine order filled two milliseconds after the last spoof order, and the spoof orders were modified away then canceled.",
        "matched_negative_group_id": "cftc_geneva_20150901_wheat_example",
        "session_bucket": "source_time_not_stated",
        "source_row_id": "cftc_geneva_20150901_wheat_buy_spoof_orders",
    },
]

NEGATIVE_ADDITIONS = [
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Facts paragraph, April 24 2013 RBOB gasoline example",
        "trade_date": "2013-04-24",
        "symbol": "RBOB gasoline futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_CODE,
        "participant_identifier": "Geneva Trader A",
        "side": "sell genuine order",
        "earliest_order_received_time": "about one second after last spoof order",
        "latest_order_received_time": "immediate fill after entry",
        "order_count": "one genuine order",
        "total_order_quantity": "2 lots",
        "activity_description": "Matched same-order control seed: the source distinguishes a two-lot sell genuine order from the buy spoof orders. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_geneva_20130424_rbob_example",
        "session_bucket": "source_time_not_stated",
        "source_row_id": "cftc_geneva_20130424_rbob_sell_genuine_order_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Facts paragraph, May 21 2013 light sweet crude oil example",
        "trade_date": "2013-05-21",
        "symbol": "light sweet crude oil futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_CODE,
        "participant_identifier": "Geneva Trader B",
        "side": "buy genuine order",
        "earliest_order_received_time": "about 400 milliseconds after spoof order",
        "latest_order_received_time": "executed within 200 milliseconds",
        "order_count": "one genuine order",
        "total_order_quantity": "15 lots",
        "activity_description": "Matched same-order control seed: the source distinguishes a 15-lot buy genuine order from the sell spoof order. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_geneva_20130521_crude_example",
        "session_bucket": "source_time_not_stated",
        "source_row_id": "cftc_geneva_20130521_crude_buy_genuine_order_control",
    },
    {
        "label": "matched_negative_normal_activity",
        "source_report": SOURCE_REPORT,
        "source_section": "Facts paragraph, September 1 2015 Soft Red Winter wheat example",
        "trade_date": "2015-09-01",
        "symbol": "Soft Red Winter wheat futures",
        "venue_or_market_center": VENUE,
        "participant_type_code": PARTICIPANT_CODE,
        "participant_identifier": "Geneva Trader C",
        "side": "sell genuine order",
        "earliest_order_received_time": "about five minutes before spoof order series",
        "latest_order_received_time": "filled two milliseconds after last spoof order",
        "order_count": "one genuine order",
        "total_order_quantity": "5 lots",
        "activity_description": "Matched same-order control seed: the source distinguishes a five-lot sell genuine order from the buy spoof order series. This is not a broad normal-market calibration sample.",
        "matched_negative_group_id": "cftc_geneva_20150901_wheat_example",
        "session_bucket": "source_time_not_stated",
        "source_row_id": "cftc_geneva_20150901_wheat_sell_genuine_order_control",
    },
]


def first_existing(paths: list[Path]) -> Path:
    for path in paths:
        if path.exists():
            return path
    raise FileNotFoundError("none of the source candidates exists")


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

    source_pdf = first_existing(SOURCE_PDF_CANDIDATES)
    source_text = first_existing(SOURCE_TEXT_CANDIDATES)
    text = source_text.read_text(encoding="utf-8", errors="replace")
    text_checks = {
        "April 24, 2013": "April 24, 2013" in text,
        "May 21, 2013": "May 21, 2013" in text,
        "September 1, 2015": "September 1, 2015" in text,
        "RBOB gasoline": "RBOB gasoline" in text,
        "light sweet crude oil": "light sweet crude oil" in text,
        "Soft Red Winter wheat": "Soft Red Winter wheat" in text,
        "Genuine Order": "Genuine Order" in text,
        "Spoof Orders": "Spoof Orders" in text,
    }

    pre_hashes = {p.name: sha256_file(p) for p in (POSITIVE, NEGATIVE, PROVENANCE) if p.exists()}
    with LOCK.open("w", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        positive_rows, positive_added = append_unique(POSITIVE, POSITIVE_ADDITIONS)
        negative_rows, negative_added = append_unique(NEGATIVE, NEGATIVE_ADDITIONS)
        provenance = json.loads(PROVENANCE.read_text(encoding="utf-8")) if PROVENANCE.exists() else {}
        prior_run = provenance.get("r6_geneva_cftc_row_uplift_v1", {})
        prior_positive_added = int(prior_run.get("positive_rows_added", 0) or 0)
        prior_negative_added = int(prior_run.get("matched_negative_rows_added", 0) or 0)
        provenance["cftc_geneva_order_examples"] = {
            "url": SOURCE_URL,
            "pdf_path": str(source_pdf),
            "pdf_sha256": sha256_file(source_pdf),
            "text_path": str(source_text),
            "text_sha256": sha256_file(source_text),
            "text_checks": text_checks,
            "positive_source_row_ids": [row["source_row_id"] for row in positive_added],
            "matched_negative_source_row_ids": [row["source_row_id"] for row in negative_added],
            "rows_materialized_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        provenance["r6_geneva_cftc_row_uplift_v1"] = {
            "positive_rows_added": len(positive_added),
            "matched_negative_rows_added": len(negative_added),
            "run_id": RUN_ID,
        }
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
    positive_ids_present = {row["source_row_id"] for row in positive_rows}
    negative_ids_present = {row["source_row_id"] for row in negative_rows}
    all_geneva_rows_present = all(row["source_row_id"] in positive_ids_present for row in POSITIVE_ADDITIONS) and all(
        row["source_row_id"] in negative_ids_present for row in NEGATIVE_ADDITIONS
    )
    positive_added_reported = len(positive_added) or (prior_positive_added if all_geneva_rows_present else 0)
    negative_added_reported = len(negative_added) or (prior_negative_added if all_geneva_rows_present else 0)
    new_rows_added = bool(positive_added or negative_added or positive_added_reported or negative_added_reported)
    if support_ok and min_lcb >= 0.95 and chronological_ok and heldout_ok and broad_normal_sample:
        decision = "r6_geneva_cftc_row_uplift_v1=accepted_95_for_r6_direct_only"
    elif new_rows_added:
        decision = "r6_geneva_cftc_row_uplift_v1=direct_intake_rows_uplifted_schema_ready_calibration_still_blocked"
    else:
        decision = "r6_geneva_cftc_row_uplift_v1=no_new_unique_rows_calibration_still_blocked"

    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before": sha256_file(BOARD),
        "decision": decision,
        "source_url": SOURCE_URL,
        "source_pdf": str(source_pdf),
        "source_pdf_sha256": sha256_file(source_pdf),
        "source_text": str(source_text),
        "source_text_sha256": sha256_file(source_text),
        "text_checks": text_checks,
        "positive_rows_added": positive_added_reported,
        "matched_negative_rows_added": negative_added_reported,
        "positive_rows_added_this_rerun": len(positive_added),
        "matched_negative_rows_added_this_rerun": len(negative_added),
        "positive_source_row_ids_added": [row["source_row_id"] for row in positive_added],
        "matched_negative_source_row_ids_added": [row["source_row_id"] for row in negative_added],
        "positive_source_row_ids_materialized": [row["source_row_id"] for row in POSITIVE_ADDITIONS if row["source_row_id"] in positive_ids_present],
        "matched_negative_source_row_ids_materialized": [row["source_row_id"] for row in NEGATIVE_ADDITIONS if row["source_row_id"] in negative_ids_present],
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

    json_path = OUT / "r6_geneva_cftc_row_uplift_v1.json"
    report_path = OUT / "r6_geneva_cftc_row_uplift_v1.md"
    gate_csv = OUT / "r6_geneva_cftc_row_uplift_v1_gates.csv"
    summary_csv = OUT / "r6_geneva_cftc_row_uplift_v1_intake_summary.csv"
    assertions_path = CHECKS / "r6_geneva_cftc_row_uplift_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with gate_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["gate", "observed", "required", "pass"])
        writer.writeheader()
        writer.writerows(
            [
                {"gate": "positive_support", "observed": pos_summary["rows"], "required": 50, "pass": support_ok},
                {"gate": "negative_support", "observed": neg_summary["rows"], "required": 50, "pass": support_ok},
                {"gate": "chronological_split", "observed": pos_summary["unique_dates"], "required": 2, "pass": chronological_ok},
                {"gate": "heldout_symbol_or_venue", "observed": f"symbols={pos_summary['unique_symbols']};venues={pos_summary['unique_venues']}", "required": "symbol>=2 or venue>=2", "pass": heldout_ok},
                {"gate": "wilson95_lcb", "observed": f"{min_lcb:.6f}", "required": ">=0.95", "pass": min_lcb >= 0.95},
                {"gate": "broad_normal_sample", "observed": "same-order CFTC genuine-order legs are source-described control seeds only; not broad normal-market calibration", "required": "source-owned broad normal activity sample", "pass": broad_normal_sample},
            ]
        )
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["class", "added", "total", "source_row_ids"])
        writer.writeheader()
        writer.writerow({"class": "positive", "added": positive_added_reported, "total": pos_summary["rows"], "source_row_ids": ";".join(row["source_row_id"] for row in POSITIVE_ADDITIONS if row["source_row_id"] in positive_ids_present)})
        writer.writerow({"class": "matched_negative", "added": negative_added_reported, "total": neg_summary["rows"], "source_row_ids": ";".join(row["source_row_id"] for row in NEGATIVE_ADDITIONS if row["source_row_id"] in negative_ids_present)})

    report = [
        "# R6 Geneva CFTC Row Uplift v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Positive rows added/materialized by this run: `{positive_added_reported}`; matched negative rows added/materialized by this run: `{negative_added_reported}`.",
        f"- Positive rows now: `{pos_summary['rows']}`; matched negative rows now: `{neg_summary['rows']}`.",
        f"- Unique dates: `{pos_summary['unique_dates']}`; symbols: `{pos_summary['unique_symbols']}`; venues: `{pos_summary['unique_venues']}`.",
        f"- Wilson95 LCB positive/negative/min: `{positive_lcb:.6f}` / `{negative_lcb:.6f}` / `{min_lcb:.6f}`.",
        f"- Chronological split ok: `{str(chronological_ok).lower()}`; heldout symbol/venue ok: `{str(heldout_ok).lower()}`.",
        "- Broad normal sample: `false`.",
        f"- Verifier status: `{result['verifier_status']}`; return code: `{verifier.returncode}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Source Rows Added",
        "",
        "| Class | Added | Total |",
        "|---|---:|---:|",
        f"| `positive` | `{positive_added_reported}` | `{pos_summary['rows']}` |",
        f"| `matched_negative` | `{negative_added_reported}` | `{neg_summary['rows']}` |",
        "",
        "## Boundary",
        "",
        "The Geneva rows are public CFTC same-order positive/control seeds from a cached source. They improve direct R6 support and breadth but do not satisfy the broad normal-market calibration-control requirement.",
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
        f"PASS source_pdf_sha256={sha256_file(source_pdf)}",
        f"PASS positive_rows_added={positive_added_reported}",
        f"PASS matched_negative_rows_added={negative_added_reported}",
        f"PASS verifier_status={result['verifier_status']}",
        f"PASS positive_rows={pos_summary['rows']}",
        f"PASS matched_negative_rows={neg_summary['rows']}",
        f"PASS combined_min_wilson95_lcb={min_lcb:.6f}",
        f"PASS support_ok={str(support_ok).lower()}",
        f"PASS broad_normal_sample={str(broad_normal_sample).lower()}",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
        "PASS external_requests_sent=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "positive_rows": pos_summary["rows"], "matched_negative_rows": neg_summary["rows"], "wilson95_lcb_min": round(min_lcb, 6), "update_goal": False}, indent=2))


if __name__ == "__main__":
    main()
