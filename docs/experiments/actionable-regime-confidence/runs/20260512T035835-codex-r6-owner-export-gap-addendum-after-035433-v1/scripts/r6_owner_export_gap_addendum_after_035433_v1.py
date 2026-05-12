#!/usr/bin/env python3
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T035835-codex-r6-owner-export-gap-addendum-after-035433-v1"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT = RUN_ROOT / "r6-owner-export-gap-addendum-after-035433-v1"
CHECKS = RUN_ROOT / "checks"
SOURCE_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T035433-codex-r6-staging-triplet-split-calibration-after-035233-v1/"
    "r6-staging-triplet-split-calibration-after-035233-v1/"
    "r6_staging_triplet_split_calibration_after_035233_v1.json"
)
GAPS_CSV = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T035433-codex-r6-staging-triplet-split-calibration-after-035233-v1/"
    "r6-staging-triplet-split-calibration-after-035233-v1/"
    "r6_staging_triplet_split_gaps_v1.csv"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_gap_rows() -> list[dict]:
    with GAPS_CSV.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        for key in [
            "positive_support",
            "negative_support",
            "required_positive_support_for_95_if_all_correct",
            "required_negative_support_for_95_if_all_correct",
            "additional_positive_rows_needed_min",
            "additional_negative_rows_needed_min",
            "additional_pair_rows_needed_min",
        ]:
            row[key] = int(row[key])
        row["current_min_wilson95_lcb"] = float(row["current_min_wilson95_lcb"])
    return rows


def summarize(rows: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        if row["additional_pair_rows_needed_min"] > 0:
            groups.setdefault(row["split_family"], []).append(row)
    summary = []
    for split_family, members in sorted(groups.items()):
        summary.append({
            "split_family": split_family,
            "failing_cells": len(members),
            "max_additional_pair_rows_needed_min": max(r["additional_pair_rows_needed_min"] for r in members),
            "sum_additional_pair_rows_needed_min_if_exact_cells_must_all_pass": sum(r["additional_pair_rows_needed_min"] for r in members),
            "worst_cell": max(members, key=lambda r: r["additional_pair_rows_needed_min"])["split_name"],
        })
    return summary


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    source = json.loads(SOURCE_JSON.read_text())
    decision = source["decision"]
    calibration = source["calibration"]
    rows = read_gap_rows()
    summary = summarize(rows)
    top_rows = sorted(rows, key=lambda r: (-r["additional_pair_rows_needed_min"], r["split_family"], r["split_name"]))[:25]

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact": sha256_file(BOARD),
        "gate_result": "r6_owner_export_gap_addendum_after_035433_v1=gap_addendum_ready_rows_not_acquired_no_promotion",
        "source_run": str(SOURCE_JSON),
        "source_gate": decision["gate_result"],
        "pooled_gate": calibration["pooled_gate"],
        "pooled_min_wilson95_lcb": calibration["pooled_min_wilson95_lcb"],
        "chronological_split_gate": calibration["chronological_split_gate"],
        "heldout_symbol_gate": calibration["heldout_symbol_gate"],
        "heldout_venue_gate": calibration["heldout_venue_gate"],
        "broad_normal_controls_present": calibration["broad_normal_controls_present"],
        "gap_summary": summary,
        "request_addendum": {
            "delivery_root": "/tmp/ict-engine-board-a-r6-owner-export-v1",
            "required_files": [
                "positive_spoofing_layering_rows.csv",
                "matched_negative_normal_activity_rows.csv",
                "provenance_manifest.json",
            ],
            "minimum_contract": "source-owned positive rows and independent normal/non-manipulation controls with provenance; same-exhibit FLIP remains invalid unless explicitly approved",
            "use": "append to 015040 v4 CME/Cboe request drafts and 015055 operator handoff",
        },
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_promotion_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "trade_usable": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "source_roots_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "next_action": "Use this addendum with the 015040 v4 owner-export requests; do not rerun downstream until verifier-native rows or explicit approval unlock the root.",
    }

    json_path = OUT / "r6_owner_export_gap_addendum_after_035433_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_csv(
        OUT / "r6_owner_export_gap_addendum_summary_v1.csv",
        summary,
        [
            "split_family",
            "failing_cells",
            "max_additional_pair_rows_needed_min",
            "sum_additional_pair_rows_needed_min_if_exact_cells_must_all_pass",
            "worst_cell",
        ],
    )
    write_csv(
        OUT / "r6_owner_export_gap_addendum_top_cells_v1.csv",
        top_rows,
        [
            "split_family",
            "split_name",
            "positive_support",
            "negative_support",
            "current_min_wilson95_lcb",
            "required_positive_support_for_95_if_all_correct",
            "required_negative_support_for_95_if_all_correct",
            "additional_positive_rows_needed_min",
            "additional_negative_rows_needed_min",
            "additional_pair_rows_needed_min",
        ],
    )

    summary_lines = "\n".join(
        f"- `{row['split_family']}`: `{row['failing_cells']}` failing cells, max `{row['max_additional_pair_rows_needed_min']}` additional pairs, sum `{row['sum_additional_pair_rows_needed_min_if_exact_cells_must_all_pass']}` if exact cells must all pass; worst cell `{row['worst_cell']}`."
        for row in summary
    )
    top_table = "\n".join(
        f"| `{row['split_family']}` | {row['split_name']} | {row['positive_support']} | {row['negative_support']} | {row['additional_pair_rows_needed_min']} |"
        for row in top_rows[:12]
    )
    md = f"""# R6 Owner-Export Gap Addendum After 035433 v1

Run id: `{RUN_ID}`

Gate result: `{result['gate_result']}`

## Source

- Source split calibration: `20260512T035433-codex-r6-staging-triplet-split-calibration-after-035233-v1`.
- Source gate: `{decision['gate_result']}`.
- Pooled Wilson95 LCB: `{calibration['pooled_min_wilson95_lcb']}`; pooled gate `{calibration['pooled_gate']}`.
- Chronological split gate `{calibration['chronological_split_gate']}`, heldout-symbol gate `{calibration['heldout_symbol_gate']}`, heldout-venue gate `{calibration['heldout_venue_gate']}`, broad independent normal controls `{calibration['broad_normal_controls_present']}`.

## Gap Addendum

The current owner/export request should not ask only for pooled support. It must cover these split gaps with source-owned positive rows plus independent normal/non-manipulation controls:

{summary_lines}

Top gap cells:

| Split family | Cell | Positive support | Negative support | Additional paired rows needed |
|---|---|---:|---:|---:|
{top_table}

## Delivery Contract

- Populate only after owner/export delivery or explicit approval: `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Required files remain `positive_spoofing_layering_rows.csv`, `matched_negative_normal_activity_rows.csv`, and `provenance_manifest.json`.
- Same-exhibit `FLIP` rows remain invalid controls unless explicitly approved.
- Preserve ticket/export/license identifiers, raw delivery hashes, field mapping, normal-control policy, and raw-data commit restrictions in provenance.

## Decision

This is a request addendum only. It acquires no rows, mutates no roots, approves no controls, and does not justify canonical merge or downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree rerun.

Accepted rows added `0`; new confidence gate `false`; canonical merge `false`; downstream promotion rerun `false`; strict full objective `false`; trade usable `false`; `update_goal=false`.
"""
    (OUT / "r6_owner_export_gap_addendum_after_035433_v1.md").write_text(md)

    checks = [
        ("source_pooled_gate_true", calibration["pooled_gate"] is True),
        ("chronological_gate_false", calibration["chronological_split_gate"] is False),
        ("heldout_symbol_gate_false", calibration["heldout_symbol_gate"] is False),
        ("heldout_venue_gate_false", calibration["heldout_venue_gate"] is False),
        ("broad_normal_controls_false", calibration["broad_normal_controls_present"] is False),
        ("gap_families_present", {r["split_family"] for r in summary} == {"chronological_group_split", "heldout_symbol_exact", "heldout_venue_exact"}),
        ("accepted_rows_added_zero", result["accepted_rows_added"] == 0),
        ("canonical_merge_false", result["canonical_merge_allowed"] is False),
        ("downstream_rerun_false", result["downstream_promotion_rerun_allowed"] is False),
        ("strict_objective_false", result["strict_full_objective_achieved"] is False),
        ("update_goal_false", result["update_goal"] is False),
        ("source_roots_mutated_false", result["source_roots_mutated"] is False),
    ]
    with (CHECKS / "r6_owner_export_gap_addendum_after_035433_v1_assertions.out").open("w") as fh:
        for name, ok in checks:
            fh.write(f"{'PASS' if ok else 'FAIL'} {name}\n")
    if not all(ok for _, ok in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
