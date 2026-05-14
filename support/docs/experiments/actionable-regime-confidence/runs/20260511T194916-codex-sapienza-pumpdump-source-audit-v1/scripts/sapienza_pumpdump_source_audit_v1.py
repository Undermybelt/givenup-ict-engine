#!/usr/bin/env python3
"""Audit SystemsLab-Sapienza pump/dump labels for Board A direct Manipulation."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import subprocess
from collections import defaultdict
from pathlib import Path


def git_output(source_root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(source_root), *args], text=True).strip()


def count_csv_rows(path: Path) -> int:
    with path.open(newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def feature_summary(path: Path) -> dict:
    rows = 0
    positives = 0
    negatives = 0
    symbols = set()
    pump_indices = set()
    by_pump = defaultdict(lambda: {"positive": 0, "negative": 0})
    min_date = None
    max_date = None

    with gzip.open(path, "rt", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        for row in reader:
            rows += 1
            gt = (row.get("gt") or "").strip()
            pump_index = (row.get("pump_index") or "").strip()
            symbol = (row.get("symbol") or "").strip()
            date = (row.get("date") or "").strip()

            symbols.add(symbol)
            pump_indices.add(pump_index)
            if gt == "1":
                positives += 1
                by_pump[pump_index]["positive"] += 1
            elif gt == "0":
                negatives += 1
                by_pump[pump_index]["negative"] += 1

            if date:
                min_date = date if min_date is None or date < min_date else min_date
                max_date = date if max_date is None or date > max_date else max_date

    positive_pumps = {idx for idx, counts in by_pump.items() if counts["positive"] > 0}
    matched_pumps = {
        idx
        for idx, counts in by_pump.items()
        if counts["positive"] > 0 and counts["negative"] > 0
    }

    return {
        "file": path.name,
        "headers": headers,
        "rows": rows,
        "positive_rows_gt_1": positives,
        "negative_rows_gt_0": negatives,
        "symbols": len(symbols),
        "pump_indices": len(pump_indices),
        "positive_pump_indices": len(positive_pumps),
        "positive_pump_indices_with_same_schema_negative_rows": len(matched_pumps),
        "date_min": min_date,
        "date_max": max_date,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--run-root", required=True)
    args = parser.parse_args()

    source_root = Path(args.source_root)
    run_root = Path(args.run_root)
    out_dir = run_root / "sapienza-pumpdump-source-audit"
    checks_dir = run_root / "checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    feature_files = sorted((source_root / "labeled_features").glob("features_*.csv.gz"))
    summaries = [feature_summary(path) for path in feature_files]
    source_commit = git_output(source_root, "rev-parse", "HEAD")
    source_url = "https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset"

    source_positive_rows = sum(item["positive_rows_gt_1"] for item in summaries)
    source_negative_rows = sum(item["negative_rows_gt_0"] for item in summaries)
    min_matched_indices = min(
        item["positive_pump_indices_with_same_schema_negative_rows"] for item in summaries
    )
    ready_pumpdump_positive_control_source = (
        source_positive_rows > 0 and source_negative_rows > 0 and min_matched_indices > 0
    )

    result = {
        "run_id": "20260511T194916-codex-sapienza-pumpdump-source-audit-v1",
        "source": source_url,
        "source_commit": source_commit,
        "pump_event_rows": count_csv_rows(source_root / "pump_telegram.csv"),
        "group_rows": count_csv_rows(source_root / "groups.csv"),
        "feature_files": summaries,
        "ready_pumpdump_positive_control_source": ready_pumpdump_positive_control_source,
        "ready_spoofing_layering_intake_source": False,
        "full_direct_manipulation_species_coverage": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "decision": (
            "sapienza_pumpdump_source_audit_v1="
            "pumpdump_positive_control_candidate_not_spoofing_layering_intake"
        ),
        "blocker": (
            "Source-owned labels and same-schema normal rows exist for Binance "
            "Telegram pump/dump chunks, but the current strict direct intake gap "
            "requires spoofing/layering positives plus matched negatives and does "
            "not cover quote stuffing, pinging, bear raid, or painting tape."
        ),
    }

    json_path = out_dir / "sapienza_pumpdump_source_audit_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    csv_path = out_dir / "sapienza_pumpdump_source_audit_v1_feature_files.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "file",
                "rows",
                "positive_rows_gt_1",
                "negative_rows_gt_0",
                "symbols",
                "pump_indices",
                "positive_pump_indices",
                "positive_pump_indices_with_same_schema_negative_rows",
                "date_min",
                "date_max",
            ],
        )
        writer.writeheader()
        writer.writerows({key: item[key] for key in writer.fieldnames} for item in summaries)

    md_path = out_dir / "sapienza_pumpdump_source_audit_v1.md"
    md_path.write_text(
        "\n".join(
            [
                "# Sapienza Pump/Dump Source Audit v1",
                "",
                f"Source: `{source_url}`",
                f"Source commit: `{source_commit}`",
                "",
                "## Decision",
                "",
                f"`{result['decision']}`",
                "",
                f"- Pump event rows: `{result['pump_event_rows']}`.",
                f"- Group rows: `{result['group_rows']}`.",
                f"- Ready pump/dump positive/control candidate: `{str(ready_pumpdump_positive_control_source).lower()}`.",
                "- Ready spoofing/layering intake source: `false`.",
                "- Full direct Manipulation species coverage: `false`.",
                "- Accepted rows added: `0`; new confidence gate: `false`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "",
                "## Feature File Readback",
                "",
                "| File | Rows | gt=1 | gt=0 | Symbols | Pump indices | Positive pump indices with gt=0 controls | Date min | Date max |",
                "|---|---:|---:|---:|---:|---:|---:|---|---|",
                *[
                    "| {file} | {rows} | {positive_rows_gt_1} | {negative_rows_gt_0} | {symbols} | {pump_indices} | {positive_pump_indices_with_same_schema_negative_rows} | {date_min} | {date_max} |".format(
                        **item
                    )
                    for item in summaries
                ],
                "",
                "## Board A Impact",
                "",
                "This source is better than positive-only event windows for the Telegram pump/dump slice because it exposes source-labeled `gt` rows and same-schema `gt=0` rows around Binance pump events.",
                "",
                "It still cannot close the current strict direct `Manipulation` intake blocker because the missing intake contract is for spoofing/layering positives plus matched normal controls, and full direct species coverage still lacks quote stuffing, pinging, bear raid, and painting-tape rows.",
                "",
                "Raw source rows remain only under `/tmp`; this repo stores the compact audit and counts.",
            ]
        )
        + "\n"
    )

    assertions = [
        ("decision", result["decision"]),
        ("ready_pumpdump_positive_control_source", str(ready_pumpdump_positive_control_source).lower()),
        ("ready_spoofing_layering_intake_source", "false"),
        ("full_direct_manipulation_species_coverage", "false"),
        ("accepted_rows_added", "0"),
        ("new_confidence_gate", "false"),
        ("strict_full_objective_achieved", "false"),
        ("update_goal", "false"),
    ]
    (checks_dir / "sapienza_pumpdump_source_audit_v1_assertions.out").write_text(
        "\n".join(f"{key}={value}" for key, value in assertions) + "\n"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
