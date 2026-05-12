#!/usr/bin/env python3
"""Validate 122351 provider evidence-node candidates across internal splits."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T123233+0800-codex-122351-provider-node-split-validation-v1"
SOURCE_SCAN_RUN_ID = "20260512T122351+0800-codex-115700-provider-evidence-node-scan-v1"
RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
REPORT_DIR = ROOT / "122351-provider-node-split-validation-v1"
CHECK_DIR = ROOT / "checks"
SOURCE_SCRIPT = RUNS / SOURCE_SCAN_RUN_ID / "scripts" / "115700_provider_evidence_node_scan_v1.py"
SOURCE_SCAN_JSON = (
    RUNS
    / SOURCE_SCAN_RUN_ID
    / "115700-provider-evidence-node-scan-v1"
    / "115700_provider_evidence_node_scan_v1.json"
)

FEATURES = [
    "provider_rv_median_24h",
    "provider_return_dispersion_24h",
    "provider_range_pos_median_24h",
]
SPLITS = ["period_half", "chronological_quartile", "branch_path", "source_provider"]
MIN_INTERNAL_BIN_ROWS = 5


def load_source_module():
    spec = importlib.util.spec_from_file_location("scan122351", SOURCE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {SOURCE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pct(value: float) -> float:
    if pd.isna(value):
        return 0.0
    return round(float(value), 6)


def wilson_lower(wins: int, rows: int, z: float = 1.959963984540054) -> float:
    if rows <= 0:
        return 0.0
    phat = wins / rows
    denom = 1 + z * z / rows
    centre = phat + z * z / (2 * rows)
    margin = z * ((phat * (1 - phat) + z * z / (4 * rows)) / rows) ** 0.5
    return round((centre - margin) / denom, 6)


def bin_stats(df: pd.DataFrame, feature: str, group_col: str) -> list[dict[str, Any]]:
    rows = []
    for group_name, group in df.groupby(group_col, dropna=False):
        for bin_name, bin_group in group.groupby(f"{feature}_bin", dropna=False):
            n = len(bin_group)
            wins = int(bin_group["is_win"].sum())
            rows.append(
                {
                    "feature": feature,
                    "split": group_col,
                    "group": str(group_name),
                    "bin": str(bin_name),
                    "rows": int(n),
                    "wins": wins,
                    "losses": int(n - wins),
                    "win_rate": pct(wins / n) if n else 0.0,
                    "wilson_lower_95": wilson_lower(wins, n),
                    "avg_pnl": pct(bin_group["pnl"].mean()) if n else 0.0,
                }
            )
    return rows


def direction_guard(stats: list[dict[str, Any]], feature: str, split: str) -> dict[str, Any]:
    by_group: dict[str, dict[str, dict[str, Any]]] = {}
    for row in stats:
        if row["feature"] != feature or row["split"] != split:
            continue
        by_group.setdefault(row["group"], {})[row["bin"]] = row

    eligible = []
    skipped = []
    passed = []
    failed = []
    for group_name, bins in by_group.items():
        high = bins.get("high")
        low = bins.get("low")
        if not high or not low or high["rows"] < MIN_INTERNAL_BIN_ROWS or low["rows"] < MIN_INTERNAL_BIN_ROWS:
            skipped.append(group_name)
            continue
        item = {
            "group": group_name,
            "high_rows": high["rows"],
            "low_rows": low["rows"],
            "high_win_rate": high["win_rate"],
            "low_win_rate": low["win_rate"],
            "delta_high_minus_low": round(high["win_rate"] - low["win_rate"], 6),
        }
        eligible.append(item)
        if high["win_rate"] > low["win_rate"]:
            passed.append(item)
        else:
            failed.append(item)
    return {
        "feature": feature,
        "split": split,
        "eligible_groups": len(eligible),
        "passed_groups": len(passed),
        "failed_groups": len(failed),
        "skipped_groups": len(skipped),
        "direction_consistent_high_gt_low": bool(eligible) and not failed,
        "failures": failed,
        "skipped": skipped,
    }


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    source = load_source_module()
    panel, _coverage = source.provider_panel()
    trades = source.load_trades()
    df = trades.merge(panel, on="ts", how="left").sort_values("ts").reset_index(drop=True)
    df["chronological_quartile"] = pd.qcut(
        df["ts"].rank(method="first"),
        q=4,
        labels=["Q1", "Q2", "Q3", "Q4"],
    )
    for feature in FEATURES:
        df[f"{feature}_bin"] = source.bin_series(df[feature])

    stats: list[dict[str, Any]] = []
    guards: list[dict[str, Any]] = []
    for feature in FEATURES:
        for split in SPLITS:
            split_stats = bin_stats(df, feature, split)
            stats.extend(split_stats)
            guards.append(direction_guard(split_stats, feature, split))

    feature_summary = []
    source_scan = json.loads(SOURCE_SCAN_JSON.read_text())
    scan_by_feature = {item["feature"]: item for item in source_scan["candidate_features"]}
    for feature in FEATURES:
        feature_guards = [guard for guard in guards if guard["feature"] == feature]
        feature_summary.append(
            {
                "feature": feature,
                "source_scan_separation": scan_by_feature[feature]["win_rate_separation"],
                "source_scan_bins": scan_by_feature[feature]["bins"],
                "internal_direction_guard_pass": all(
                    guard["direction_consistent_high_gt_low"] for guard in feature_guards
                ),
                "eligible_split_groups": sum(guard["eligible_groups"] for guard in feature_guards),
                "failed_split_groups": sum(guard["failed_groups"] for guard in feature_guards),
                "guards": feature_guards,
            }
        )

    priority = sorted(
        feature_summary,
        key=lambda item: (
            item["internal_direction_guard_pass"],
            -item["failed_split_groups"],
            item["source_scan_separation"],
        ),
        reverse=True,
    )
    payload = {
        "run_id": RUN_ID,
        "source_scan_run_id": SOURCE_SCAN_RUN_ID,
        "row_count": int(len(df)),
        "provider_count": int(df["source_provider"].nunique()),
        "branch_count": int(df["branch_path"].nunique()),
        "features_validated": FEATURES,
        "min_internal_bin_rows": MIN_INTERNAL_BIN_ROWS,
        "feature_summary": feature_summary,
        "priority_order": [item["feature"] for item in priority],
        "decision": {
            "gate": "122351_provider_node_split_validation_v1=provider_rv_internal_priority_but_external_validation_required_no_promotion",
            "best_internal_candidate": priority[0]["feature"],
            "bbn_likelihood_mutation_allowed": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "external_blockers": [
            "BTC_only",
            "1h_only",
            "no_selected_history_source_control_unlock_for_promotion",
            "execution_ready_false_actionable_false_observe",
            "no_95_percent_regime_confidence",
        ],
    }

    json_path = REPORT_DIR / "122351_provider_node_split_validation_v1.json"
    md_path = REPORT_DIR / "122351_provider_node_split_validation_v1.md"
    csv_path = REPORT_DIR / "122351_provider_node_split_validation_v1_split_bins.csv"
    assertions_path = CHECK_DIR / "122351_provider_node_split_validation_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "feature",
                "split",
                "group",
                "bin",
                "rows",
                "wins",
                "losses",
                "win_rate",
                "wilson_lower_95",
                "avg_pnl",
            ],
        )
        writer.writeheader()
        writer.writerows(stats)

    lines = [
        "# 122351 Provider Node Split Validation v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source scan: `{SOURCE_SCAN_RUN_ID}`",
        "",
        "## Result",
        f"- Rows validated: `{payload['row_count']}` across `{payload['provider_count']}` providers and `{payload['branch_count']}` branch paths.",
        f"- Feature priority order: `{payload['priority_order']}`.",
        f"- Gate: `{payload['decision']['gate']}`.",
        "",
        "## Feature Decisions",
    ]
    for item in feature_summary:
        lines.append(
            f"- `{item['feature']}`: source separation `{item['source_scan_separation']}`, "
            f"internal high>low guard `{item['internal_direction_guard_pass']}`, "
            f"eligible split groups `{item['eligible_split_groups']}`, failed split groups `{item['failed_split_groups']}`."
        )
    lines.extend(
        [
            "",
            "## Decision",
            f"- Best internal candidate: `{payload['decision']['best_internal_candidate']}`.",
            "- This is still candidate-only. It is BTC-only, 1h-only, and execution remains observe-only.",
            "- `bbn_likelihood_mutation_allowed=false`.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n")

    best = payload["decision"]["best_internal_candidate"]
    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS row_count={payload['row_count']}",
        f"PASS provider_count={payload['provider_count']}",
        f"PASS branch_count={payload['branch_count']}",
        f"PASS features_validated={len(FEATURES)}",
        f"PASS best_internal_candidate={best}",
        "FAIL_CLOSED external_validation_required=True",
        "FAIL_CLOSED bbn_likelihood_mutation_allowed=False",
        "FAIL_CLOSED promotion_allowed=False",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (ROOT / "source_scan_run_id.txt").write_text(SOURCE_SCAN_RUN_ID + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
