#!/usr/bin/env python3
"""Board B CrossRunRootEnsembleV1 RC-SPA readback.

Run-local additive experiment only. It treats recent completed Board B price-root
candidate rows as a candidate source pool, prefixes every source variant to keep
lineage explicit, and reruns the unchanged RC-SPA hard gates by parent root.
The 205047 scoped Manipulation branch remains a separate component pass.
"""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260511T215453+0800-codex-board-b-cross-run-root-ensemble-v1"
SCHEMA_VERSION = "board-b-cross-run-root-ensemble/v1"
RECIPE_ID = "CrossRunRootEnsembleV1"

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
BASE_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T193803-codex-board-b-root-transition-triad-clean-v1/scripts/"
    "board_b_root_transition_triad_clean_v1.py"
)
CRYPTO_WRAPPER = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T210508-codex-board-b-crypto-liquidity-root-family-v2/scripts/"
    "crypto_liquidity_root_family_v2.py"
)

SOURCE_FILES = [
    (
        "CryptoLiquidityRootFamilyV2",
        REPO_ROOT
        / "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T210508-codex-board-b-crypto-liquidity-root-family-v2/branch-rc-spa/"
        "crypto_liquidity_root_family_variant_rows_v2.csv",
    ),
    (
        "YFinanceDefensiveCrossAssetV1Repaired",
        REPO_ROOT
        / "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T212211-codex-board-b-yfinance-defensive-crossasset-v1-repaired/branch-rc-spa/"
        "yfinance_defensive_crossasset_variant_rows_v1.csv",
    ),
    (
        "ProviderRawDailyConsensusV1",
        REPO_ROOT
        / "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T212329-codex-board-b-provider-raw-daily-consensus-v1/branch-rc-spa/"
        "provider_raw_daily_consensus_variant_rows_v1.csv",
    ),
    (
        "SessionLiquidityIntradayV1",
        REPO_ROOT
        / "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T213155-codex-board-b-session-liquidity-intraday-v1/branch-rc-spa/"
        "session_liquidity_intraday_variant_rows_v1.csv",
    ),
    (
        "VolStressTermStructureBreadthV1",
        REPO_ROOT
        / "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T213339-codex-board-b-vol-stress-term-structure-breadth-v1/branch-rc-spa/"
        "vol_stress_breadth_variant_rows_v1.csv",
    ),
    (
        "IntradayRiskDefensiveRotationV1",
        REPO_ROOT
        / "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T214454-codex-board-b-intraday-risk-defensive-rotation-v1/branch-rc-spa/"
        "intraday_rotation_variant_rows_v1.csv",
    ),
]


def import_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def branch_path(root: str, variant_id: str) -> str:
    source_family = variant_id.split("::", 1)[0] if "::" in variant_id else "unknown_source"
    return f"{root} -> CrossRunRootEnsemble -> {source_family} -> {RECIPE_ID}:{variant_id}"


def normalize_row(row: dict[str, Any], source_name: str, source_path: Path) -> dict[str, Any]:
    original_variant = str(row.get("variant_id", "unknown_variant"))
    variant_id = f"{source_name}::{original_variant}"
    root = str(row.get("parent_regime_root", ""))
    out = dict(row)
    out["schema_version"] = SCHEMA_VERSION
    out["run_id"] = RUN_ID
    out["recipe_id"] = RECIPE_ID
    out["source_candidate_recipe_id"] = source_name
    out["source_candidate_artifact"] = str(source_path.relative_to(REPO_ROOT))
    out["source_candidate_variant_id"] = original_variant
    out["variant_id"] = variant_id
    out["trade_id"] = f"{RECIPE_ID}:{variant_id}:{row.get('trade_id', '')}"
    out["sub_regime_tags"] = "CrossRunRootEnsemble"
    out["sub_sub_regime_or_profit_factor"] = source_name
    out["profit_factor_family"] = "cross_run_root_ensemble"
    out["profit_factor_leaf"] = f"{RECIPE_ID}:{variant_id}"
    out["regime_profit_branch_path"] = branch_path(root, variant_id)
    out["regime_profit_branch_path_version"] = SCHEMA_VERSION
    out["allowed_action"] = "source_variant_research_only_until_branch_rc_spa_passes"
    out["suppression_rule"] = "suppress_if_cross_run_ensemble_branch_rc_spa_fails"
    return out


def load_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_rows: list[dict[str, Any]] = []
    source_summaries: list[dict[str, Any]] = []
    for source_name, source_path in SOURCE_FILES:
        if not source_path.exists() or source_path.stat().st_size == 0:
            source_summaries.append(
                {
                    "source_candidate_recipe_id": source_name,
                    "source_candidate_artifact": str(source_path.relative_to(REPO_ROOT)),
                    "rows_loaded": 0,
                    "status": "missing_or_empty",
                }
            )
            continue
        rows = pd.read_csv(source_path).to_dict("records")
        normalized = [normalize_row(row, source_name, source_path) for row in rows]
        all_rows.extend(normalized)
        source_summaries.append(
            {
                "source_candidate_recipe_id": source_name,
                "source_candidate_artifact": str(source_path.relative_to(REPO_ROOT)),
                "rows_loaded": len(normalized),
                "status": "loaded",
            }
        )
    return all_rows, source_summaries


def write_csv_union(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_report(base: Any, report: dict[str, Any]) -> None:
    decision = report["decision"]
    source_lines = [
        "| Source | Rows | Status |",
        "|---|---:|---|",
    ]
    for row in report["source_summaries"]:
        source_lines.append(
            f"| `{row['source_candidate_recipe_id']}` | {row['rows_loaded']} | `{row['status']}` |"
        )
    branch_lines = [
        "| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["branch_summaries"]:
        branch_lines.append(
            f"| {row['parent_regime_root']} | `{row['selected_variant_id']}` | "
            f"{row['total_trades']} | {row['test_folds']} | "
            f"{row['min_trades_per_test_fold']} | {row['fold_positive_rate']:.4f} | "
            f"{row['bootstrap_edge_lcb_5pct']:.6f} | {row['pbo']:.3f} | "
            f"{row['dsr']:.4f} | {row['rc_spa']:.4f} | `{row['hard_gate_result']}` |"
        )
    lines = [
        "# Cross-Run Root Ensemble RC-SPA v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Stable profit score: `{decision['stable_profit_score']:.4f}`",
        f"- Price-root paths passed: `{decision['price_root_paths_passed']}/4`",
        f"- Scoped Manipulation component pass consumed: `{decision['manipulation_component_pass']}`",
        f"- Variant rows: `{decision['variant_trade_rows']}`",
        f"- Selected rows: `{decision['selected_trade_rows']}`",
        f"- Selected root counts: `{decision['selected_root_trade_counts']}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        f"- Primary blocker: {decision['primary_blocker']}",
        "",
        "## Source Pool",
        "",
        *source_lines,
        "",
        "## Selected Branch Summary",
        "",
        *branch_lines,
        "",
        "## Artifacts",
        "",
        f"- Report JSON: `{base.rel(base.REPORT_JSON)}`",
        f"- Selected rows: `{base.rel(base.SELECTED_ROWS_CSV)}`",
        f"- Variant rows: `{base.rel(base.ALL_ROWS_CSV)}`",
        f"- Branch summary: `{base.rel(base.SUMMARY_CSV)}`",
        f"- Source summary: `{base.rel(base.PANEL_SUMMARY_CSV)}`",
        f"- Fail-closed downstream summary: `{base.rel(base.FAIL_CLOSED_MD)}`",
        f"- Assertions: `{base.rel(base.ASSERTIONS)}`",
        "",
        "## Next",
        "",
        f"- {decision['next_action']}",
    ]
    base.REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    base = import_module(BASE_SCRIPT, "board_b_root_transition_base")
    crypto = import_module(CRYPTO_WRAPPER, "board_b_crypto_wrapper")
    base.RUN_ID = RUN_ID
    base.SCHEMA_VERSION = SCHEMA_VERSION
    base.RECIPE_ID = RECIPE_ID
    base.RUN_ROOT = RUN_ROOT
    base.OUT_DIR = RUN_ROOT / "branch-rc-spa"
    base.CHECK_DIR = RUN_ROOT / "checks"
    base.FAIL_CLOSED_DIR = RUN_ROOT / "ict-engine-fail-closed"
    base.ALL_ROWS_CSV = base.OUT_DIR / "cross_run_root_ensemble_variant_rows_v1.csv"
    base.SELECTED_ROWS_CSV = base.OUT_DIR / "cross_run_root_ensemble_selected_rows_v1.csv"
    base.SUMMARY_CSV = base.OUT_DIR / "cross_run_root_ensemble_branch_summary_v1.csv"
    base.PANEL_SUMMARY_CSV = base.OUT_DIR / "cross_run_root_ensemble_source_summary_v1.csv"
    base.REPORT_JSON = base.OUT_DIR / "cross_run_root_ensemble_rc_spa_report_v1.json"
    base.REPORT_MD = base.OUT_DIR / "cross_run_root_ensemble_rc_spa_report_v1.md"
    base.ASSERTIONS = base.CHECK_DIR / "cross_run_root_ensemble_v1_assertions.out"
    base.FAIL_CLOSED_MD = base.FAIL_CLOSED_DIR / "cross_run_root_ensemble_fail_closed_summary_v1.md"
    base.branch_path = branch_path
    for path in [base.OUT_DIR, base.CHECK_DIR, base.FAIL_CLOSED_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    all_rows, source_summaries = load_rows()
    if not all_rows:
        raise RuntimeError("no source rows loaded")

    branch_summaries: list[dict[str, Any]] = []
    variant_summaries: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    for root in base.ROOTS:
        pbo, pbo_method = base.pbo_for_root(root, all_rows)
        variants = sorted({str(row["variant_id"]) for row in all_rows if row["parent_regime_root"] == root})
        summaries = [
            base.summarize_rows(
                root=root,
                variant_id=variant,
                rows=[
                    row
                    for row in all_rows
                    if row["parent_regime_root"] == root and str(row["variant_id"]) == variant
                ],
                all_rows=all_rows,
                pbo=pbo,
                pbo_method=pbo_method,
            )
            for variant in variants
        ]
        selected = max(summaries, key=lambda row: float(row["rc_spa"]))
        branch_summaries.append(selected)
        variant_summaries.extend(summaries)
        selected_rows.extend(
            [
                row
                for row in all_rows
                if row["parent_regime_root"] == root
                and str(row["variant_id"]) == str(selected["selected_variant_id"])
            ]
        )

    manip_summary, manip_component = crypto.load_manip_component(base)
    branch_summaries.append(manip_summary)
    price_root_summaries = [row for row in branch_summaries if row["parent_regime_root"] in base.ROOTS]
    passed_price_roots = [row for row in price_root_summaries if row["hard_gate_result"] == "pass"]
    manip_pass = manip_summary["hard_gate_result"] == "pass"
    all_required_pass = len(passed_price_roots) == len(base.ROOTS) and manip_pass
    max_price_score = max(float(row["rc_spa"]) for row in price_root_summaries)
    selected_counts = {root: 0 for root in [*base.ROOTS, "Manipulation(scoped)"]}
    for row in selected_rows:
        selected_counts[row["parent_regime_root"]] = selected_counts.get(row["parent_regime_root"], 0) + 1
    selected_counts["Manipulation(scoped)"] = int(manip_component.get("component_positive_rows", 0))
    root_failures = [
        f"{row['parent_regime_root']}={row['hard_gate_result']}"
        for row in price_root_summaries
        if row["hard_gate_result"] != "pass"
    ]
    if not manip_pass:
        root_failures.append("Manipulation(scoped)=missing_205047_component_pass")
    gate_result = "pass" if all_required_pass else "fail:required_root_branch_hard_gates_failed"
    downstream = (
        "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
        if all_required_pass
        else "not_started:blocked_by_branch_rc_spa_hard_gates"
    )
    primary_blocker = "all required branch hard gates passed" if all_required_pass else "; ".join(root_failures)
    next_action = (
        "B5: run Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree branch consumption with the same branch paths."
        if all_required_pass
        else "B2R-repeat: source a genuinely different family/provider panel; do not keep recombining failed source variants."
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "run_root": base.rel(RUN_ROOT),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "recipe_id": RECIPE_ID,
        "source_summaries": source_summaries,
        "decision": {
            "gate_result": gate_result,
            "stable_profit_score": max_price_score,
            "variant_trade_rows": len(all_rows),
            "selected_trade_rows": len(selected_rows),
            "branch_paths_evaluated": len(branch_summaries),
            "branch_paths_passed": len(passed_price_roots) + int(manip_pass),
            "price_root_paths_passed": len(passed_price_roots),
            "manipulation_component_pass": manip_pass,
            "selected_root_trade_counts": selected_counts,
            "downstream_consumption": downstream,
            "primary_blocker": primary_blocker,
            "next_action": next_action,
        },
        "manipulation_component": manip_component,
        "branch_summaries": branch_summaries,
        "variant_summaries": variant_summaries,
        "artifacts": {
            "report_json": base.rel(base.REPORT_JSON),
            "report_md": base.rel(base.REPORT_MD),
            "selected_rows_csv": base.rel(base.SELECTED_ROWS_CSV),
            "all_rows_csv": base.rel(base.ALL_ROWS_CSV),
            "summary_csv": base.rel(base.SUMMARY_CSV),
            "source_summary_csv": base.rel(base.PANEL_SUMMARY_CSV),
            "assertions": base.rel(base.ASSERTIONS),
            "fail_closed_summary": base.rel(base.FAIL_CLOSED_MD),
        },
        "completion": {
            "runtime_code_changed": False,
            "auto_quant_checkout_changed": False,
            "raw_auto_quant_data_committed": False,
            "thresholds_relaxed_after_scoring": False,
            "downstream_runtime_consumed_branch_path": all_required_pass,
        },
    }
    write_csv_union(base.ALL_ROWS_CSV, all_rows)
    write_csv_union(base.SELECTED_ROWS_CSV, selected_rows)
    base.write_csv(base.SUMMARY_CSV, branch_summaries)
    base.write_csv(base.PANEL_SUMMARY_CSV, source_summaries)
    base.write_json(base.REPORT_JSON, report)
    write_report(base, report)
    base.FAIL_CLOSED_MD.write_text(
        "\n".join(
            [
                "# Cross-Run Root Ensemble ict-engine Fail-Closed Summary v1",
                "",
                f"Run id: `{RUN_ID}`.",
                "",
                f"- Branch RC-SPA gate: `{gate_result}`",
                f"- Downstream consumption: `{downstream}`",
                "- Pre-Bayes / BBN / CatBoost / execution-tree were not started unless every required branch hard gate passed.",
                "- The 205047 scoped Manipulation component is recorded as a component pass only, not an aggregate promotion.",
                "- This is fail-closed unless all four price roots and scoped Manipulation pass together.",
                "",
                f"Primary blocker: {primary_blocker}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assertions = [
        f"run_id={RUN_ID}",
        f"variant_trade_rows={len(all_rows)}",
        f"selected_trade_rows={len(selected_rows)}",
        f"branch_paths_evaluated={len(branch_summaries)}",
        f"price_root_paths_passed={len(passed_price_roots)}",
        f"manipulation_component_pass={manip_pass}",
        f"gate_result={gate_result}",
        f"downstream_consumption={downstream}",
        "artifacts_exist=true",
    ]
    if not all_rows:
        assertions.append("ASSERT_FAIL:no_variant_trade_rows")
    if not manip_pass:
        assertions.append("ASSERT_FAIL:manipulation_component_not_available")
    base.ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 1 if any(line.startswith("ASSERT_FAIL") for line in assertions) else 0


if __name__ == "__main__":
    raise SystemExit(main())
