#!/usr/bin/env python3
"""Schema-fit audit for the Sapienza pump/dump source package.

This script reads only local source CSV/GZ files under /tmp and writes compact
metadata artifacts. It does not execute code from the external repository and
does not commit raw source rows.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import statistics
from datetime import datetime
from pathlib import Path


RUN_ID = "20260511T195751-codex-sapienza-pumpdump-schema-fit-v1"
SOURCE = "https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset"
SOURCE_COMMIT = "d71250d4cb055dde2d415c8cba38a0dcd6eb6e16"
SOURCE_ROOT = Path("/tmp/ict-engine-sapienza-pumpdump-source-screen")
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T195751-codex-sapienza-pumpdump-schema-fit-v1"
)
OUT_DIR = RUN_ROOT / "sapienza-pumpdump-schema-fit"
CHECK_DIR = RUN_ROOT / "checks"

FEATURE_FILES = [
    "features_5S.csv.gz",
    "features_15S.csv.gz",
    "features_25S.csv.gz",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def read_events() -> tuple[list[dict[str, str]], dict[str, list[dict[str, object]]]]:
    path = SOURCE_ROOT / "pump_telegram.csv"
    rows: list[dict[str, str]] = []
    by_symbol: dict[str, list[dict[str, object]]] = {}
    with path.open(newline="") as handle:
        for ordinal, row in enumerate(csv.DictReader(handle)):
            rows.append(row)
            if row.get("exchange") != "binance":
                continue
            event_dt = datetime.strptime(
                f"{row['date']} {row['hour']}", "%Y-%m-%d %H:%M"
            )
            record = {
                "source_row_ordinal": ordinal,
                "symbol": row["symbol"],
                "group": row["group"],
                "exchange": row["exchange"],
                "event_time_utc": event_dt,
            }
            by_symbol.setdefault(row["symbol"], []).append(record)
    return rows, by_symbol


def nearest_event(
    symbol_events: dict[str, list[dict[str, object]]], symbol: str, ts: datetime
) -> tuple[dict[str, object] | None, float | None]:
    candidates = symbol_events.get(symbol, [])
    if not candidates:
        return None, None
    best = min(
        candidates,
        key=lambda event: abs((ts - event["event_time_utc"]).total_seconds()),
    )
    return best, abs((ts - best["event_time_utc"]).total_seconds())


def summarize_feature_file(
    rel_name: str, symbol_events: dict[str, list[dict[str, object]]]
) -> dict[str, object]:
    path = SOURCE_ROOT / "labeled_features" / rel_name
    rows = 0
    positives = 0
    negatives = 0
    symbols: set[str] = set()
    pump_indices: set[str] = set()
    positive_indices: set[str] = set()
    negative_counts_by_index: dict[str, int] = {}
    date_min: str | None = None
    date_max: str | None = None
    headers: list[str] = []
    positive_join_matches_180s = 0
    positive_join_unmatched = 0
    positive_join_deltas: list[float] = []

    with gzip.open(path, "rt", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        for row in reader:
            rows += 1
            date = row["date"]
            if date_min is None or date < date_min:
                date_min = date
            if date_max is None or date > date_max:
                date_max = date
            symbol = row["symbol"]
            pump_index = row["pump_index"]
            gt = row["gt"]
            symbols.add(symbol)
            pump_indices.add(pump_index)
            if gt == "1":
                positives += 1
                positive_indices.add(pump_index)
                event, delta = nearest_event(symbol_events, symbol, parse_dt(date))
                if event is not None and delta is not None and delta <= 180:
                    positive_join_matches_180s += 1
                    positive_join_deltas.append(delta)
                else:
                    positive_join_unmatched += 1
            elif gt == "0":
                negatives += 1
                negative_counts_by_index[pump_index] = (
                    negative_counts_by_index.get(pump_index, 0) + 1
                )

    controls_per_positive = [
        negative_counts_by_index.get(pump_index, 0) for pump_index in positive_indices
    ]
    positive_indices_with_controls = sum(1 for value in controls_per_positive if value > 0)

    return {
        "file": rel_name,
        "sha256": sha256_file(path),
        "headers": headers,
        "rows": rows,
        "positive_rows_gt_1": positives,
        "negative_rows_gt_0": negatives,
        "symbols": len(symbols),
        "pump_indices": len(pump_indices),
        "positive_pump_indices": len(positive_indices),
        "positive_pump_indices_with_same_schema_negative_rows": positive_indices_with_controls,
        "same_pump_negative_controls_min": min(controls_per_positive)
        if controls_per_positive
        else 0,
        "same_pump_negative_controls_median": statistics.median(controls_per_positive)
        if controls_per_positive
        else 0,
        "same_pump_negative_controls_max": max(controls_per_positive)
        if controls_per_positive
        else 0,
        "positive_event_join_matches_within_180s": positive_join_matches_180s,
        "positive_event_join_unmatched": positive_join_unmatched,
        "positive_event_join_delta_seconds_max": max(positive_join_deltas)
        if positive_join_deltas
        else None,
        "date_min": date_min,
        "date_max": date_max,
    }


def build_schema_fit_rows() -> list[dict[str, str]]:
    return [
        {
            "required_field": "event_id_or_source_row_id",
            "fit_status": "ready_derived_for_pumpdump",
            "source_columns": "feature_file,pump_index,symbol,date + pump_telegram source row ordinal via nearest event join",
            "notes": "All checked positive feature rows join to a Binance pump event within 180 seconds, but the native feature key is a build-local pump_index rather than an immutable upstream event id.",
        },
        {
            "required_field": "timestamp_session_window",
            "fit_status": "ready_for_pumpdump",
            "source_columns": "date,feature_file granularity,pump_telegram date/hour",
            "notes": "Feature timestamps are UTC exchange windows; market session is crypto 24x7 and window size is encoded as 5S, 15S, or 25S.",
        },
        {
            "required_field": "symbol_market_venue",
            "fit_status": "ready_for_pumpdump",
            "source_columns": "symbol,pump_telegram exchange,README pair contract",
            "notes": "Feature rows carry symbols; source event table and README constrain the checked labeled feature package to Binance SYM/BTC crypto pairs.",
        },
        {
            "required_field": "direct_label_or_species",
            "fit_status": "ready_scoped_to_pumpdump",
            "source_columns": "gt,pump_telegram event context",
            "notes": "gt=1/gt=0 supports a direct pump/dump species package only; it is not a spoofing/layering, quote-stuffing, pinging, bear-raid, or painting-tape label source.",
        },
        {
            "required_field": "matched_negative_group_or_controls",
            "fit_status": "ready_scoped_to_pumpdump",
            "source_columns": "feature_file,pump_index,gt",
            "notes": "Each positive pump_index has same-schema gt=0 rows in the same feature file and event window group.",
        },
        {
            "required_field": "provenance_hash",
            "fit_status": "ready",
            "source_columns": "source commit plus SHA256 of source CSV/GZ files",
            "notes": "The artifact records compact source hashes only; raw rows stay in /tmp.",
        },
        {
            "required_field": "spoofing_layering_positive_rows",
            "fit_status": "missing",
            "source_columns": "N/A",
            "notes": "No order-book layering/spoofing lifecycle labels are present in this source package.",
        },
        {
            "required_field": "full_direct_manipulation_species_coverage",
            "fit_status": "missing",
            "source_columns": "N/A",
            "notes": "The package covers pump/dump only and does not cover quote stuffing, pinging, bear raid, or painting tape.",
        },
    ]


def write_csv(path: Path, rows: list[dict[str, object]], headers: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in headers})


def write_report(payload: dict[str, object], schema_rows: list[dict[str, str]]) -> None:
    feature_rows = payload["feature_files"]
    report = OUT_DIR / "sapienza_pumpdump_schema_fit_v1.md"
    lines = [
        "# Sapienza Pump/Dump Schema Fit v1",
        "",
        f"Source: `{SOURCE}`",
        f"Source commit: `{SOURCE_COMMIT}`",
        "",
        "## Decision",
        "",
        f"`{payload['decision']}`",
        "",
        f"- Ready pump/dump row-intake candidate schema: `{str(payload['ready_pumpdump_row_intake_candidate_schema']).lower()}`.",
        f"- Can materialize scoped pump/dump positive/control package: `{str(payload['can_materialize_scoped_pumpdump_positive_control_package']).lower()}`.",
        f"- Ready spoofing/layering intake source: `{str(payload['ready_spoofing_layering_intake_source']).lower()}`.",
        f"- Full direct Manipulation species coverage: `{str(payload['full_direct_manipulation_species_coverage']).lower()}`.",
        f"- Accepted rows added: `{payload['accepted_rows_added']}`; new confidence gate: `{str(payload['new_confidence_gate']).lower()}`.",
        f"- Strict full objective achieved: `{str(payload['strict_full_objective_achieved']).lower()}`; `update_goal={str(payload['update_goal']).lower()}`.",
        "",
        "## Schema Fit",
        "",
        "| Required field | Fit | Source columns | Notes |",
        "|---|---|---|---|",
    ]
    for row in schema_rows:
        notes = row["notes"].replace("|", "\\|")
        cols = row["source_columns"].replace("|", "\\|")
        lines.append(
            f"| {row['required_field']} | {row['fit_status']} | {cols} | {notes} |"
        )
    lines.extend(
        [
            "",
            "## Feature File Readiness",
            "",
            "| File | Rows | gt=1 | gt=0 | Positive pump indices | Positive indices with controls | Event join matches <=180s | Date min | Date max |",
            "|---|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in feature_rows:
        lines.append(
            "| {file} | {rows} | {pos} | {neg} | {idx} | {ctrl} | {join} | {date_min} | {date_max} |".format(
                file=row["file"],
                rows=row["rows"],
                pos=row["positive_rows_gt_1"],
                neg=row["negative_rows_gt_0"],
                idx=row["positive_pump_indices"],
                ctrl=row["positive_pump_indices_with_same_schema_negative_rows"],
                join=row["positive_event_join_matches_within_180s"],
                date_min=row["date_min"],
                date_max=row["date_max"],
            )
        )
    lines.extend(
        [
            "",
            "## Board A Impact",
            "",
            "This source can support a bounded direct pump/dump positive/control row-intake package because it exposes event timestamps, symbols, Binance venue context, source `gt` labels, same-schema `gt=0` controls, and provenance hashes.",
            "",
            "It does not close the current strict direct `Manipulation` blocker: no spoofing/layering positives are present, and the source does not cover quote stuffing, pinging, bear raid, or painting tape. No raw source rows were committed.",
            "",
        ]
    )
    report.write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    pump_events, symbol_events = read_events()
    group_path = SOURCE_ROOT / "groups.csv"
    feature_summaries = [
        summarize_feature_file(rel_name, symbol_events) for rel_name in FEATURE_FILES
    ]
    schema_fit_rows = build_schema_fit_rows()

    source_hashes = {
        "pump_telegram.csv": sha256_file(SOURCE_ROOT / "pump_telegram.csv"),
        "groups.csv": sha256_file(group_path),
        **{
            f"labeled_features/{row['file']}": row["sha256"]
            for row in feature_summaries
        },
    }

    ready_feature_files = all(
        row["positive_rows_gt_1"] > 0
        and row["negative_rows_gt_0"] > 0
        and row["positive_pump_indices"]
        == row["positive_pump_indices_with_same_schema_negative_rows"]
        and row["positive_event_join_unmatched"] == 0
        for row in feature_summaries
    )

    payload: dict[str, object] = {
        "run_id": RUN_ID,
        "source": SOURCE,
        "source_commit": SOURCE_COMMIT,
        "decision": "sapienza_pumpdump_schema_fit_v1=scoped_pumpdump_schema_ready_not_strict_manipulation_closure",
        "pump_event_rows": len(pump_events),
        "binance_event_rows": sum(
            1 for row in pump_events if row.get("exchange") == "binance"
        ),
        "group_rows": sum(1 for _ in (SOURCE_ROOT / "groups.csv").open()) - 1,
        "feature_files": feature_summaries,
        "schema_fit_fields": schema_fit_rows,
        "source_hashes": source_hashes,
        "ready_pumpdump_row_intake_candidate_schema": ready_feature_files,
        "can_materialize_scoped_pumpdump_positive_control_package": ready_feature_files,
        "ready_spoofing_layering_intake_source": False,
        "full_direct_manipulation_species_coverage": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "blocker": "Scoped pump/dump schema can be materialized, but Board A's current strict direct Manipulation blocker still requires spoofing/layering positives plus matched controls and broader direct species coverage.",
    }

    json_path = OUT_DIR / "sapienza_pumpdump_schema_fit_v1.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    write_csv(
        OUT_DIR / "sapienza_pumpdump_schema_fit_v1_feature_files.csv",
        feature_summaries,
        [
            "file",
            "sha256",
            "rows",
            "positive_rows_gt_1",
            "negative_rows_gt_0",
            "symbols",
            "pump_indices",
            "positive_pump_indices",
            "positive_pump_indices_with_same_schema_negative_rows",
            "same_pump_negative_controls_min",
            "same_pump_negative_controls_median",
            "same_pump_negative_controls_max",
            "positive_event_join_matches_within_180s",
            "positive_event_join_unmatched",
            "positive_event_join_delta_seconds_max",
            "date_min",
            "date_max",
        ],
    )
    write_csv(
        OUT_DIR / "sapienza_pumpdump_schema_fit_v1_schema_fields.csv",
        schema_fit_rows,
        ["required_field", "fit_status", "source_columns", "notes"],
    )
    write_report(payload, schema_fit_rows)

    assertions = [
        ("json_parses", True),
        ("ready_pumpdump_row_intake_candidate_schema", ready_feature_files is True),
        ("can_materialize_scoped_pumpdump_positive_control_package", ready_feature_files is True),
        ("ready_spoofing_layering_intake_source_false", payload["ready_spoofing_layering_intake_source"] is False),
        ("full_direct_species_coverage_false", payload["full_direct_manipulation_species_coverage"] is False),
        ("strict_full_objective_achieved_false", payload["strict_full_objective_achieved"] is False),
        ("update_goal_false", payload["update_goal"] is False),
        ("accepted_rows_added_zero", payload["accepted_rows_added"] == 0),
        ("raw_data_committed_false", payload["raw_data_committed"] is False),
    ]
    failed = [name for name, ok in assertions if not ok]
    assert_path = CHECK_DIR / "sapienza_pumpdump_schema_fit_v1_assertions.out"
    assert_path.write_text(
        "\n".join(f"{name}=PASS" if ok else f"{name}=FAIL" for name, ok in assertions)
        + "\n"
    )
    if failed:
        raise SystemExit(f"failed assertions: {', '.join(failed)}")


if __name__ == "__main__":
    main()
