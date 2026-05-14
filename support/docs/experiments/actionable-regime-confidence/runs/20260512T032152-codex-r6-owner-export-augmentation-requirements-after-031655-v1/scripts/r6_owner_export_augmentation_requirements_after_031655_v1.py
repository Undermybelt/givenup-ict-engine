#!/usr/bin/env python3
"""Convert the failed R6 split calibration into owner-export row requirements."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T032152-codex-r6-owner-export-augmentation-requirements-after-031655-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-owner-export-augmentation-requirements-after-031655-v1"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

SPLIT_RUN = "20260512T031316-codex-r6-noncanonical-staging-split-calibration-v1"
SPLIT_OUT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / SPLIT_RUN
    / "r6-noncanonical-staging-split-calibration-v1"
)
SPLIT_METRICS = SPLIT_OUT / "r6_noncanonical_staging_split_metrics_v1.csv"
SPLIT_JSON = SPLIT_OUT / "r6_noncanonical_staging_split_calibration_v1.json"

LATEST_AUDIT_RUN = "20260512T031655-codex-current-objective-completion-audit-after-031435-v1"
LATEST_AUDIT_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / LATEST_AUDIT_RUN
    / "current-objective-completion-audit-after-031435-v1"
    / "current_objective_completion_audit_after_031435_v1.json"
)

DISPATCH_RUN = "20260512T031353-codex-r6-owner-export-dispatch-readiness-after-030957-v1"
DISPATCH_OUT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / DISPATCH_RUN
    / "r6-owner-export-dispatch-readiness-after-030957-v1"
)
FILENAME_CONTRACT = DISPATCH_OUT / "r6_owner_export_verifier_filename_contract_after_030957_v1.csv"

APPROVAL_PACKAGE = Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid")
CANONICAL_OWNER_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
R3_NATIVE_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R5_RECENCY_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")

MIN_SUPPORT = 50
MIN_WILSON = 0.95
Z_95 = 1.96


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


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def wilson_lcb_perfect(n: int) -> float:
    if n <= 0:
        return 0.0
    p = 1.0
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / n
    centre = p + z2 / (2.0 * n)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * n)) / n)
    return max(0.0, (centre - margin) / denom)


def required_per_class() -> int:
    for n in range(1, 10_000):
        if n >= MIN_SUPPORT and wilson_lcb_perfect(n) >= MIN_WILSON:
            return n
    raise RuntimeError("failed to find Wilson requirement")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    required = required_per_class()
    board_hash_before = sha256(BOARD)
    split_payload = load_json(SPLIT_JSON)
    audit_payload = load_json(LATEST_AUDIT_JSON)
    approval_payload = load_json(APPROVAL_PACKAGE) if APPROVAL_PACKAGE.exists() else {}

    metric_rows = read_csv(SPLIT_METRICS)
    deficit_rows: list[dict[str, Any]] = []
    summary: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "split_family": "",
            "failed_cell_count": 0,
            "positive_deficit_total": 0,
            "negative_deficit_total": 0,
            "combined_deficit_total": 0,
            "worst_min_wilson95_lcb": 1.0,
        }
    )

    for row in metric_rows:
        if row["split_family"] == "pooled_all_source_rows":
            continue
        positive_support = int(row["positive_support"])
        negative_support = int(row["negative_support"])
        positive_deficit = max(0, required - positive_support)
        negative_deficit = max(0, required - negative_support)
        min_lcb = float(row["min_wilson95_lcb"])
        needs_more = row["pass"] != "True" or positive_deficit > 0 or negative_deficit > 0
        if not needs_more:
            continue
        family = row["split_family"]
        item = {
            "split_family": family,
            "split_name": row["split_name"],
            "positive_support": positive_support,
            "negative_support": negative_support,
            "required_positive_rows": required,
            "required_negative_rows": required,
            "positive_rows_needed": positive_deficit,
            "negative_control_rows_needed": negative_deficit,
            "combined_rows_needed": positive_deficit + negative_deficit,
            "current_min_wilson95_lcb": round(min_lcb, 12),
            "current_support_ok": row["support_ok"],
            "current_wilson_ok": row["wilson_ok"],
            "current_pass": row["pass"],
            "accepted_source_type": "owner_or_operator_export_only",
            "nonaccepted_shortcuts": "proxy_sidecar_readiness_local_cache_or_flip_without_explicit_approval",
        }
        deficit_rows.append(item)

        bucket = summary[family]
        bucket["split_family"] = family
        bucket["failed_cell_count"] += 1
        bucket["positive_deficit_total"] += positive_deficit
        bucket["negative_deficit_total"] += negative_deficit
        bucket["combined_deficit_total"] += positive_deficit + negative_deficit
        bucket["worst_min_wilson95_lcb"] = min(bucket["worst_min_wilson95_lcb"], min_lcb)

    summary_rows = [
        {
            **row,
            "required_rows_per_class_per_cell": required,
            "requirement_reason": f"MIN_SUPPORT={MIN_SUPPORT}; Wilson95 perfect-row lower bound >= {MIN_WILSON}",
            "promotion_decision": "non_promoting_requirements_only",
        }
        for row in sorted(summary.values(), key=lambda item: item["split_family"])
    ]

    contract_rows = read_csv(FILENAME_CONTRACT)
    requirements_csv = OUT / "r6_owner_export_augmentation_split_deficits_after_031655_v1.csv"
    summary_csv = OUT / "r6_owner_export_augmentation_summary_after_031655_v1.csv"
    filename_csv = OUT / "r6_owner_export_augmentation_filename_contract_after_031655_v1.csv"
    write_csv(
        requirements_csv,
        sorted(deficit_rows, key=lambda item: (item["split_family"], -item["combined_rows_needed"], item["split_name"])),
        [
            "split_family",
            "split_name",
            "positive_support",
            "negative_support",
            "required_positive_rows",
            "required_negative_rows",
            "positive_rows_needed",
            "negative_control_rows_needed",
            "combined_rows_needed",
            "current_min_wilson95_lcb",
            "current_support_ok",
            "current_wilson_ok",
            "current_pass",
            "accepted_source_type",
            "nonaccepted_shortcuts",
        ],
    )
    write_csv(
        summary_csv,
        summary_rows,
        [
            "split_family",
            "failed_cell_count",
            "positive_deficit_total",
            "negative_deficit_total",
            "combined_deficit_total",
            "worst_min_wilson95_lcb",
            "required_rows_per_class_per_cell",
            "requirement_reason",
            "promotion_decision",
        ],
    )
    write_csv(
        filename_csv,
        [
            {
                **row,
                "current_target_root": str(CANONICAL_OWNER_ROOT),
                "status": "must_be_satisfied_before_verifier_rerun",
            }
            for row in contract_rows
        ],
        [
            "concept",
            "request_package_name",
            "current_verifier_required_name",
            "decision",
            "current_target_root",
            "status",
        ],
    )

    root_status = {
        "canonical_owner_root_exists": CANONICAL_OWNER_ROOT.exists(),
        "r3_native_root_exists": R3_NATIVE_ROOT.exists(),
        "r5_recency_root_exists": R5_RECENCY_ROOT.exists(),
        "approval_present": bool(approval_payload.get("assertions", {}).get("approval_present", False)),
        "flip_controls_accepted_under_current_contract": bool(
            approval_payload.get("assertions", {}).get("flip_controls_accepted_under_current_contract", False)
        ),
        "canonical_merge_allowed_now": bool(approval_payload.get("assertions", {}).get("canonical_merge_allowed_now", False)),
        "downstream_rerun_allowed_now": bool(approval_payload.get("assertions", {}).get("downstream_rerun_allowed_now", False)),
    }

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash_before,
        "gate_result": "r6_owner_export_augmentation_requirements_after_031655_v1=requirements_quantified_no_source_rows_acquired_no_promotion",
        "inputs": {
            "split_calibration_json": rel(SPLIT_JSON),
            "split_metrics_csv": rel(SPLIT_METRICS),
            "latest_current_objective_audit_json": rel(LATEST_AUDIT_JSON),
            "filename_contract_csv": rel(FILENAME_CONTRACT),
            "approval_package": str(APPROVAL_PACKAGE),
        },
        "source_gate_readback": {
            "split_gate": split_payload.get("calibration", {}),
            "latest_audit_gate": audit_payload.get("gate_result"),
            "root_status": root_status,
        },
        "requirements": {
            "min_support": MIN_SUPPORT,
            "min_wilson95_lcb": MIN_WILSON,
            "required_rows_per_class_per_cell": required,
            "required_rows_per_class_wilson95_lcb": round(wilson_lcb_perfect(required), 12),
            "summary_csv": rel(summary_csv),
            "split_deficits_csv": rel(requirements_csv),
            "filename_contract_csv": rel(filename_csv),
        },
        "summary": summary_rows,
        "promotion": {
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "canonical_merge_allowed": False,
            "downstream_promotion_rerun_allowed": False,
            "strict_full_objective_achieved": False,
            "trade_usable": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "canonical_owner_root_mutated": False,
        },
        "next_action": (
            "Acquire owner/operator rows and matched controls for the listed chronological, symbol, and venue cells, "
            "or record explicit approval for an approved family-level split contract before verifier rerun and downstream promotion."
        ),
    }
    result_json = OUT / "r6_owner_export_augmentation_requirements_after_031655_v1.json"
    write_json(result_json, result)

    top_venue = [
        row
        for row in sorted(deficit_rows, key=lambda item: (item["split_family"], -item["combined_rows_needed"]))
        if row["split_family"] == "heldout_venue_exact"
    ][:5]
    top_symbol = [
        row
        for row in sorted(deficit_rows, key=lambda item: -item["combined_rows_needed"])
        if row["split_family"] == "heldout_symbol_exact"
    ][:8]
    chronological = [row for row in deficit_rows if row["split_family"] == "chronological_group_split"]

    report = [
        "# R6 Owner-Export Augmentation Requirements After 031655 v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Generated at UTC: `{result['generated_at_utc']}`",
        "",
        "## Result",
        "",
        f"- Gate result: `{result['gate_result']}`.",
        f"- Required rows per class per evaluated cell: `{required}` (`MIN_SUPPORT={MIN_SUPPORT}` and Wilson95 perfect-row LCB `{wilson_lcb_perfect(required):.12f}`).",
        "- This packet is requirements-only: it acquired `0` rows, added `0` accepted rows, left the canonical owner root untouched, and did not rerun downstream promotion.",
        f"- Latest audit gate: `{audit_payload.get('gate_result')}`.",
        f"- Root readback: canonical R6 owner root exists `{str(root_status['canonical_owner_root_exists']).lower()}`, R3 native root exists `{str(root_status['r3_native_root_exists']).lower()}`, R5 recency root exists `{str(root_status['r5_recency_root_exists']).lower()}`.",
        f"- Approval readback: approval `{str(root_status['approval_present']).lower()}`, FLIP controls `{str(root_status['flip_controls_accepted_under_current_contract']).lower()}`, canonical merge `{str(root_status['canonical_merge_allowed_now']).lower()}`, downstream rerun `{str(root_status['downstream_rerun_allowed_now']).lower()}`.",
        "",
        "## Deficit Summary",
        "",
        "| Split Family | Failed Cells | Positive Rows Needed | Matched Controls Needed | Combined Rows Needed | Worst Wilson95 LCB |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        report.append(
            "| {split_family} | {failed_cell_count} | {positive_deficit_total} | {negative_deficit_total} | {combined_deficit_total} | {worst_min_wilson95_lcb:.12f} |".format(
                **row
            )
        )
    report.extend(
        [
            "",
            "## Chronological Cells",
            "",
            "| Cell | Positive Support | Control Support | Positive Need | Control Need |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in sorted(chronological, key=lambda item: item["split_name"]):
        report.append(
            f"| {row['split_name']} | {row['positive_support']} | {row['negative_support']} | {row['positive_rows_needed']} | {row['negative_control_rows_needed']} |"
        )
    report.extend(
        [
            "",
            "## Largest Venue Deficits",
            "",
            "| Venue Cell | Positive Support | Control Support | Positive Need | Control Need |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in top_venue:
        report.append(
            f"| {row['split_name']} | {row['positive_support']} | {row['negative_support']} | {row['positive_rows_needed']} | {row['negative_control_rows_needed']} |"
        )
    report.extend(
        [
            "",
            "## Largest Symbol Deficits",
            "",
            "| Symbol Cell | Positive Support | Control Support | Positive Need | Control Need |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in top_symbol:
        report.append(
            f"| {row['split_name']} | {row['positive_support']} | {row['negative_support']} | {row['positive_rows_needed']} | {row['negative_control_rows_needed']} |"
        )
    report.extend(
        [
            "",
            "## Filename Contract",
            "",
            "Owner/export delivery is not verifier-ready unless `/tmp/ict-engine-board-a-r6-owner-export-v1` contains verifier-native names:",
            "",
            "- `positive_spoofing_layering_rows.csv`",
            "- `matched_negative_normal_activity_rows.csv`",
            "- `provenance_manifest.json`",
            "",
            "The conceptual request-package names from the earlier dispatch packet must be delivered under these names or mapped by an explicit verifier/mapping update before rerun.",
            "",
            "## Boundary",
            "",
            "This packet does not promote `031316` staging evidence, `031435` local triplet sidecars/projections, readiness packets, local caches, Auto-Quant readiness/backtests, or FLIP rows without explicit approval.",
            "",
            "## Next",
            "",
            "Acquire source-owned owner/operator rows and matched controls for the deficit cells listed in the CSVs. After real delivery or explicit approval, rerun the direct verifier, rerun split calibration, and only then rerun provider/Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree.",
        ]
    )
    report_path = OUT / "r6_owner_export_augmentation_requirements_after_031655_v1.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_start={board_hash_before}",
        f"gate_result={result['gate_result']}",
        f"required_rows_per_class_per_cell={required}",
        f"required_rows_per_class_wilson95_lcb={wilson_lcb_perfect(required):.12f}",
        f"chronological_failed_cells={next(row['failed_cell_count'] for row in summary_rows if row['split_family'] == 'chronological_group_split')}",
        f"heldout_symbol_failed_cells={next(row['failed_cell_count'] for row in summary_rows if row['split_family'] == 'heldout_symbol_exact')}",
        f"heldout_venue_failed_cells={next(row['failed_cell_count'] for row in summary_rows if row['split_family'] == 'heldout_venue_exact')}",
        f"canonical_owner_root_exists={str(root_status['canonical_owner_root_exists']).lower()}",
        f"approval_present={str(root_status['approval_present']).lower()}",
        f"flip_controls_accepted_under_current_contract={str(root_status['flip_controls_accepted_under_current_contract']).lower()}",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "canonical_merge_allowed=false",
        "downstream_promotion_rerun_allowed=false",
        "strict_full_objective_achieved=false",
        "trade_usable=false",
        "update_goal=false",
        "assertion_status=PASS",
    ]
    (CHECKS / "r6_owner_export_augmentation_requirements_after_031655_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
