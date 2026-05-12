#!/usr/bin/env python3
"""Build a source-control acquisition matrix from the R6 staging split gaps."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T035823-codex-r6-source-control-acquisition-matrix-after-035433-v1"
SLUG = "r6-source-control-acquisition-matrix-after-035433-v1"


def find_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "AGENTS.md").is_file() and (parent / "src").is_dir():
            return parent
    raise RuntimeError("could not locate ict-engine repo root")


REPO = find_repo_root()
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
COMMAND = RUN_ROOT / "command-output"

UPSTREAM = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T035433-codex-r6-staging-triplet-split-calibration-after-035233-v1/"
    "r6-staging-triplet-split-calibration-after-035233-v1"
)
UPSTREAM_JSON = UPSTREAM / "r6_staging_triplet_split_calibration_after_035233_v1.json"
UPSTREAM_GAPS = UPSTREAM / "r6_staging_triplet_split_gaps_v1.csv"
UPSTREAM_METRICS = UPSTREAM / "r6_staging_triplet_split_metrics_v1.csv"

ACTIVE_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def source_route_hint(split_name: str) -> str:
    text = split_name.lower()
    if "lme" in text:
        return "LME plus linked COMEX owner export or licensed cross-market support route"
    if any(token in text for token in ["ice", "ifeu", "brent"]):
        return "ICE/IFEU owner export or licensed order-lifecycle support route"
    if any(token in text for token in ["cme", "cme globex", "e-mini", "t-note", "t-bond", "ultra t-bond"]):
        return "CME/CME DataMine Market Depth or Market-by-Order owner export"
    if any(token in text for token in ["comex", "gold", "silver", "copper", "platinum"]):
        return "CME/COMEX owner export with source-owned broad normal controls"
    if any(token in text for token in ["nymex", "crude", "natural gas", "rbob", "gasoline"]):
        return "CME/NYMEX owner export with source-owned broad normal controls"
    if any(token in text for token in ["cbot", "soybean", "wheat"]):
        return "CME/CBOT owner export with source-owned broad normal controls"
    if split_name.startswith("chronological_"):
        return "same approved owner-export family, balanced by chronological split bucket"
    return "source-owner export with matched broad normal controls"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    COMMAND.mkdir(parents=True, exist_ok=True)

    board_hash = sha256_file(REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
    (COMMAND / "board_sha256_before_matrix.txt").write_text(
        f"{board_hash}  docs/plans/2026-05-10-actionable-regime-confidence-todo.md\n",
        encoding="utf-8",
    )

    upstream = json.loads(UPSTREAM_JSON.read_text(encoding="utf-8"))
    gaps = read_csv(UPSTREAM_GAPS)
    metrics = read_csv(UPSTREAM_METRICS)

    family_summary: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "split_family": "",
            "failing_cells": 0,
            "max_pair_rows_needed_min": 0,
            "sum_pair_rows_needed_min_if_exact_cells_must_all_pass": 0,
        }
    )
    matrix_rows: list[dict[str, object]] = []
    for row in gaps:
        family = row["split_family"]
        need = int(row["additional_pair_rows_needed_min"])
        summary = family_summary[family]
        summary["split_family"] = family
        summary["failing_cells"] = int(summary["failing_cells"]) + 1
        summary["max_pair_rows_needed_min"] = max(int(summary["max_pair_rows_needed_min"]), need)
        summary["sum_pair_rows_needed_min_if_exact_cells_must_all_pass"] = (
            int(summary["sum_pair_rows_needed_min_if_exact_cells_must_all_pass"]) + need
        )
        matrix_rows.append(
            {
                "split_family": family,
                "split_name": row["split_name"],
                "current_positive_support": int(row["positive_support"]),
                "current_negative_support": int(row["negative_support"]),
                "current_min_wilson95_lcb": float(row["current_min_wilson95_lcb"]),
                "required_positive_support_for_95_if_all_correct": int(
                    row["required_positive_support_for_95_if_all_correct"]
                ),
                "required_negative_support_for_95_if_all_correct": int(
                    row["required_negative_support_for_95_if_all_correct"]
                ),
                "additional_pair_rows_needed_min": need,
                "source_route_hint": source_route_hint(row["split_name"]),
                "allowed_use_before_approval": False,
            }
        )

    matrix_rows.sort(
        key=lambda row: (
            row["split_family"],
            -int(row["additional_pair_rows_needed_min"]),
            str(row["split_name"]),
        )
    )
    family_rows = sorted(family_summary.values(), key=lambda row: str(row["split_family"]))

    active_root_status = {
        str(root): {
            "exists": root.exists(),
            "is_dir": root.is_dir(),
            "file_count": len(list(root.iterdir())) if root.is_dir() else 0,
        }
        for root in ACTIVE_ROOTS
    }

    pooled = next(row for row in metrics if row["split_family"] == "pooled_all_source_rows")
    total_exact_gap = sum(int(row["additional_pair_rows_needed_min"]) for row in matrix_rows)
    gate_result = (
        "r6_source_control_acquisition_matrix_after_035433_v1="
        "split_gap_matrix_ready_no_rows_acquired_no_promotion"
    )
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate_result,
        "board_sha256_before_matrix": board_hash,
        "upstream": {
            "split_calibration_json": rel(UPSTREAM_JSON),
            "split_gaps_csv": rel(UPSTREAM_GAPS),
            "split_metrics_csv": rel(UPSTREAM_METRICS),
            "upstream_gate": upstream.get("decision", {}).get("gate_result")
            or upstream.get("gate_result")
            or "r6_staging_triplet_split_calibration_after_035233_v1=staging_pooled95_pass_split_support_broad_controls_and_policy_blocked_no_promotion",
        },
        "pooled_diagnostic": {
            "positive_support": int(pooled["positive_support"]),
            "negative_support": int(pooled["negative_support"]),
            "min_wilson95_lcb": float(pooled["min_wilson95_lcb"]),
            "pass": pooled["pass"] == "True",
        },
        "family_summary": family_rows,
        "total_additional_pair_rows_if_every_exact_cell_must_pass": total_exact_gap,
        "active_root_status": active_root_status,
        "promotion": {
            "rows_acquired": False,
            "active_owner_export_root_complete": False,
            "explicit_approval_present": False,
            "flip_controls_accepted": False,
            "canonical_merge_allowed": False,
            "downstream_promotion_rerun_allowed": False,
            "strict_full_objective_achieved": False,
            "trade_usable": False,
            "update_goal": False,
        },
    }

    (OUT / "r6_source_control_acquisition_matrix_after_035433_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with (OUT / "r6_source_control_acquisition_matrix_after_035433_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        fields = [
            "split_family",
            "split_name",
            "current_positive_support",
            "current_negative_support",
            "current_min_wilson95_lcb",
            "required_positive_support_for_95_if_all_correct",
            "required_negative_support_for_95_if_all_correct",
            "additional_pair_rows_needed_min",
            "source_route_hint",
            "allowed_use_before_approval",
        ]
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(matrix_rows)

    with (OUT / "r6_source_control_acquisition_family_summary_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        fields = [
            "split_family",
            "failing_cells",
            "max_pair_rows_needed_min",
            "sum_pair_rows_needed_min_if_exact_cells_must_all_pass",
        ]
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(family_rows)

    worst_rows = matrix_rows[:10]
    report = [
        "# R6 Source-Control Acquisition Matrix After 035433 v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Gate result: `{gate_result}`",
        "",
        "## Why This Exists",
        "",
        "The upstream staging triplet passed only the pooled Wilson95 diagnostic. It failed chronological, heldout-symbol, heldout-venue, broad-control, owner-export, approval, and downstream gates. This packet converts those real split gaps into an acquisition matrix; it does not authorize copying any local triplet into the active owner-export root.",
        "",
        "## Summary",
        "",
        f"- Pooled diagnostic Wilson95 LCB: `{payload['pooled_diagnostic']['min_wilson95_lcb']}` with pooled pass `{payload['pooled_diagnostic']['pass']}`.",
        f"- Total additional paired rows if every exact failing cell must pass: `{total_exact_gap}`.",
        f"- Family summaries: `{family_rows}`.",
        "- Active R6/R3/R5 source roots remain absent or incomplete.",
        "- Explicit approval and `FLIP` control approval remain false.",
        "",
        "## Worst Cells",
        "",
    ]
    for row in worst_rows:
        report.append(
            "- "
            f"`{row['split_family']}` / `{row['split_name']}` needs at least "
            f"`{row['additional_pair_rows_needed_min']}` paired source-owned rows; "
            f"route hint: {row['source_route_hint']}."
        )
    report.extend(
        [
            "",
            "## Decision",
            "",
            "No promotion. This is a request/coverage artifact only: rows acquired false, active owner-export root complete false, approval false, canonical merge false, downstream promotion false, strict full objective false, trade usable false, and `update_goal=false`.",
            "",
            "## Artifacts",
            "",
            f"- Matrix JSON: `{rel(OUT / 'r6_source_control_acquisition_matrix_after_035433_v1.json')}`",
            f"- Matrix CSV: `{rel(OUT / 'r6_source_control_acquisition_matrix_after_035433_v1.csv')}`",
            f"- Family summary CSV: `{rel(OUT / 'r6_source_control_acquisition_family_summary_v1.csv')}`",
            f"- Board hash readback: `{rel(COMMAND / 'board_sha256_before_matrix.txt')}`",
        ]
    )
    (OUT / "r6_source_control_acquisition_matrix_after_035433_v1.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    assertions = [
        "PASS gate_result=split_gap_matrix_ready_no_rows_acquired_no_promotion",
        f"PASS pooled_lcb={payload['pooled_diagnostic']['min_wilson95_lcb']}",
        f"PASS total_additional_pair_rows={total_exact_gap}",
        f"PASS family_count={len(family_rows)}",
        "PASS rows_acquired=false",
        "PASS active_owner_export_root_complete=false",
        "PASS explicit_approval_present=false",
        "PASS flip_controls_accepted=false",
        "PASS canonical_merge_allowed=false",
        "PASS downstream_promotion_rerun_allowed=false",
        "PASS strict_full_objective_achieved=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
        "PASS source_roots_mutated=false",
    ]
    (CHECKS / "r6_source_control_acquisition_matrix_after_035433_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )

    print(gate_result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
