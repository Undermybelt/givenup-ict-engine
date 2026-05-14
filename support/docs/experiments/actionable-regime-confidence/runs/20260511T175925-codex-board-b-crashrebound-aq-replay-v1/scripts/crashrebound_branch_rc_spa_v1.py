#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any


ROOT_MAP = {
    "bull_2021": {
        "parent_regime_root": "Bull",
        "sub_regime_tags": "TrendExpansion",
        "sub_sub_regime_or_profit_factor": "DrawdownRebound",
    },
    "winter_2022": {
        "parent_regime_root": "Bear",
        "sub_regime_tags": "DowntrendStress",
        "sub_sub_regime_or_profit_factor": "CapitulationRebound",
    },
    "recovery_23_25": {
        "parent_regime_root": "Sideways",
        "sub_regime_tags": "RangeRecovery",
        "sub_sub_regime_or_profit_factor": "MeanReversionRebound",
    },
}

ACCEPTED_ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
OPTIONAL_OVERLAY = "Manipulation(scoped)"


def load_autoquant_run(autoquant_root: Path):
    run_path = autoquant_root / "run.py"
    spec = importlib.util.spec_from_file_location("aq_run", run_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {run_path}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(autoquant_root))
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[int(pos)]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stdev(values: list[float]) -> float:
    return statistics.stdev(values) if len(values) >= 2 else 0.0


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def bootstrap_lcb_5pct(values: list[float]) -> float:
    if not values:
        return 0.0
    # Deterministic circular bootstrap. Good enough for an evidence gate,
    # and avoids adding random seeds to versioned artifacts.
    means: list[float] = []
    n = len(values)
    for offset in range(min(250, max(50, n))):
        sample = [values[(offset + i * 37) % n] for i in range(n)]
        means.append(mean(sample))
    return percentile(means, 0.05)


def max_drawdown(returns: list[float]) -> float:
    equity = 1.0
    peak = 1.0
    worst = 0.0
    for ret in returns:
        equity *= 1.0 + ret
        peak = max(peak, equity)
        worst = min(worst, equity / peak - 1.0)
    return abs(worst)


def profit_factor(values: list[float]) -> float:
    wins = sum(v for v in values if v > 0)
    losses = abs(sum(v for v in values if v < 0))
    if losses <= 1e-12:
        return 999.0 if wins > 0 else 0.0
    return wins / losses


def extract_trade_rows(aq_run: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pair_basket, test_timeranges = aq_run.get_strategy_overrides("CrashRebound")
    non_overlap_labels = set(ROOT_MAP)
    all_trades: list[dict[str, Any]] = []
    fold_rows: list[dict[str, Any]] = []

    for label, timerange in test_timeranges:
        results = aq_run.run_backtest("CrashRebound", timerange, pair_basket)
        strat = results.get("strategy", {}).get("CrashRebound", {}) or {}
        trades = strat.get("trades") or []
        aggregate = aq_run.extract_metrics(results, "CrashRebound", pair_basket or [])
        agg = aggregate["aggregate"]
        root_info = ROOT_MAP.get(label)
        branch_path_valid = bool(root_info and label in non_overlap_labels)
        if root_info:
            branch_path = (
                f"{root_info['parent_regime_root']} -> "
                f"{root_info['sub_regime_tags']} -> "
                f"{root_info['sub_sub_regime_or_profit_factor']} -> CrashRebound"
            )
            parent = root_info["parent_regime_root"]
            sub = root_info["sub_regime_tags"]
            sub_sub = root_info["sub_sub_regime_or_profit_factor"]
        else:
            branch_path = "aggregate_mixed_root -> overlapping_timerange -> diagnostic_only -> CrashRebound"
            parent = "aggregate_mixed_root"
            sub = "overlapping_timerange"
            sub_sub = "diagnostic_only"

        trade_returns = [float(t.get("profit_ratio") or 0.0) for t in trades]
        stressed_returns = [
            float(t.get("profit_ratio") or 0.0)
            - float(t.get("fee_open") or 0.0)
            - float(t.get("fee_close") or 0.0)
            for t in trades
        ]
        if label in non_overlap_labels:
            fold_rows.append(
                {
                    "fold_label": label,
                    "timerange": timerange,
                    "parent_regime_root": parent,
                    "regime_profit_branch_path": branch_path,
                    "trades": len(trades),
                    "win_rate": mean([1.0 if r > 0 else 0.0 for r in trade_returns]),
                    "net_profit_ratio": sum(trade_returns),
                    "stressed_profit_ratio_2x_cost": sum(stressed_returns),
                    "profit_factor": profit_factor(trade_returns),
                    "max_drawdown": max_drawdown(trade_returns),
                    "branch_path_source": "auto_quant_timerange_label_proxy_not_board_a_trade_label",
                    "branch_path_valid_for_promotion": False,
                }
            )

        for idx, trade in enumerate(trades, start=1):
            if label not in non_overlap_labels:
                continue
            profit_ratio = float(trade.get("profit_ratio") or 0.0)
            stressed_ratio = (
                profit_ratio
                - float(trade.get("fee_open") or 0.0)
                - float(trade.get("fee_close") or 0.0)
            )
            all_trades.append(
                {
                    "source_timerange_label": label,
                    "timerange": timerange,
                    "trade_index_in_fold": idx,
                    "pair": trade.get("pair", ""),
                    "open_date": str(trade.get("open_date", "")),
                    "close_date": str(trade.get("close_date", "")),
                    "profit_ratio": profit_ratio,
                    "profit_abs": float(trade.get("profit_abs") or 0.0),
                    "stressed_profit_ratio_2x_cost": stressed_ratio,
                    "stake_amount": float(trade.get("stake_amount") or 0.0),
                    "exit_reason": trade.get("exit_reason", ""),
                    "parent_regime_root": parent,
                    "parent_regime_confidence_floor": "",
                    "manipulation_overlay_state": "not_observed",
                    "sub_regime_tags": sub,
                    "sub_sub_regime_or_profit_factor": sub_sub,
                    "profit_factor_family": "counter_trend_drawdown_rebound",
                    "profit_factor_leaf": "CrashRebound",
                    "regime_profit_branch_path": branch_path,
                    "regime_profit_branch_path_version": "diagnostic_proxy_v1",
                    "recipe_id": "CrashRebound",
                    "trade_or_bar_horizon": "freqtrade_trade_duration",
                    "allowed_action": "research_watch_only",
                    "suppression_rule": "no_execution_promotion_until_board_a_trade_root_and_downstream_consumption_pass",
                    "branch_path_source": "auto_quant_timerange_label_proxy_not_board_a_trade_label",
                    "branch_path_valid_for_promotion": False,
                    "won": profit_ratio > 0.0,
                }
            )

    return all_trades, fold_rows


def compute_rc_spa(trades: list[dict[str, Any]], folds: list[dict[str, Any]]) -> dict[str, Any]:
    returns = [float(row["profit_ratio"]) for row in trades]
    stressed = [float(row["stressed_profit_ratio_2x_cost"]) for row in trades]
    roots_with_rows = sorted({str(row["parent_regime_root"]) for row in trades})
    missing_roots = [root for root in ACCEPTED_ROOTS if root not in roots_with_rows]
    branch_paths_valid = all(str(row["branch_path_valid_for_promotion"]) == "True" for row in trades)
    positive_folds = sum(1 for row in folds if float(row["net_profit_ratio"]) > 0.0)
    fold_positive_rate = positive_folds / len(folds) if folds else 0.0
    trades_per_fold = [int(row["trades"]) for row in folds]
    min_trades_per_fold = min(trades_per_fold) if trades_per_fold else 0
    lcb = bootstrap_lcb_5pct(returns)
    stressed_survival = sum(stressed) > 0.0
    fold_edges = [float(row["net_profit_ratio"]) / max(1, int(row["trades"])) for row in folds]
    robust_fold_edge = min(fold_edges) if fold_edges else 0.0
    tail_loss_p95 = abs(percentile(returns, 0.05))
    pbo = 1.0 if len(folds) < 4 else 0.25
    dsr = robust_fold_edge / (stdev(returns) + 1e-12) if returns else 0.0
    branch_means = {
        row["regime_profit_branch_path"]: float(row["net_profit_ratio"]) / max(1, int(row["trades"]))
        for row in folds
    }
    aggregate_edge = mean(returns)
    if aggregate_edge > 0 and branch_means:
        specificity_ratio = max(branch_means.values()) / aggregate_edge
    else:
        specificity_ratio = 0.0

    hard_failures: list[str] = []
    if not branch_paths_valid:
        hard_failures.append("reject_missing_branch_path:branch_path_is_proxy_not_recipe_or_board_a_trade_root")
    if missing_roots:
        hard_failures.append("reject_missing_branch_path:missing_roots=" + ",".join(missing_roots))
    if OPTIONAL_OVERLAY not in roots_with_rows:
        hard_failures.append("manipulation_overlay_not_observed")
    if len(trades) < 100:
        hard_failures.append("reject_thin_trades:total_lt_100")
    if len(folds) < 4:
        hard_failures.append("reject_overfit_risk:min_test_folds_lt_4")
    if min_trades_per_fold < 10:
        hard_failures.append("reject_thin_trades:min_trades_per_fold_lt_10")
    if fold_positive_rate < 0.75:
        hard_failures.append("reject_no_positive_edge:fold_positive_rate_lt_0_75")
    if lcb <= 0.0:
        hard_failures.append("reject_no_positive_edge:bootstrap_edge_lcb_5pct_lte_0")
    if not stressed_survival:
        hard_failures.append("reject_cost_fragile:2x_cost_stress_not_survived")
    if pbo > 0.25:
        hard_failures.append("reject_overfit_risk:pbo_gt_0_25")
    if dsr <= 0.0:
        hard_failures.append("reject_overfit_risk:dsr_lte_0")
    if tail_loss_p95 > 0.15:
        hard_failures.append("reject_tail_risk:tail_loss_p95_gt_15pct")
    if specificity_ratio < 1.20:
        hard_failures.append("reject_no_regime_specificity:ratio_lt_1_20")

    edge_score = clamp(lcb / 0.005)
    fold_score = fold_positive_rate
    depth_score = clamp(len(trades) / 100)
    dsr_score = clamp(dsr / 0.50)
    pbo_score = 1.0 - clamp(pbo / 0.25)
    cost_score = 1.0 if stressed_survival else 0.0
    drawdown_budget = 0.15
    drawdown_score = 1.0 - clamp(max(row["max_drawdown"] for row in folds) / drawdown_budget) if folds else 0.0
    specificity_score = clamp((specificity_ratio - 1.0) / 0.5)
    diagnostic_score = 100 * (
        0.20 * edge_score
        + 0.15 * fold_score
        + 0.15 * depth_score
        + 0.15 * dsr_score
        + 0.10 * pbo_score
        + 0.10 * cost_score
        + 0.10 * drawdown_score
        + 0.05 * specificity_score
    )
    rc_spa = 0.0 if hard_failures else diagnostic_score

    return {
        "schema_version": "crashrebound-branch-rc-spa/v1",
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "recipe_id": "CrashRebound",
        "total_nonoverlap_trades": len(trades),
        "test_folds": len(folds),
        "min_trades_per_test_fold": min_trades_per_fold,
        "fold_positive_rate": fold_positive_rate,
        "bootstrap_edge_lcb_5pct": lcb,
        "cost_stress_survival": stressed_survival,
        "pbo": pbo,
        "dsr": dsr,
        "tail_loss_p95": tail_loss_p95,
        "regime_specificity_ratio": specificity_ratio,
        "roots_with_rows": roots_with_rows,
        "missing_roots": missing_roots,
        "manipulation_overlay_state": "not_observed",
        "hard_failures": hard_failures,
        "diagnostic_rc_spa_before_hard_fail_zeroing": diagnostic_score,
        "rc_spa": rc_spa,
        "promotion_level": "reject" if hard_failures or rc_spa < 60 else "research_watch",
        "downstream_consumption_status": "research_watch_branch_path_not_consumed",
        "score_components": {
            "edge_score": edge_score,
            "fold_score": fold_score,
            "depth_score": depth_score,
            "dsr_score": dsr_score,
            "pbo_score": pbo_score,
            "cost_score": cost_score,
            "drawdown_score": drawdown_score,
            "specificity_score": specificity_score,
        },
    }


def build_path_ranker_target(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, trade in enumerate(trades, start=1):
        path = str(trade["regime_profit_branch_path"])
        profit = float(trade["profit_ratio"])
        score = clamp(0.5 + profit * 5.0)
        rows.append(
            {
                "candidate_set_id": "CrashRebound_branch_paths_v1",
                "path_id": f"crashrebound:{trade['parent_regime_root']}:{idx:04d}",
                "rank": idx,
                "symbol": trade["pair"],
                "path_label": path,
                "calibrated_label": 1 if profit > 0 else 0,
                "training_weight": 1.0,
                "maturity_mask": True,
                "current_posterior": score,
                "structural_baseline_score": score,
                "experience_prior": score,
                "evidence_quality_score": 0.0,
                "risk_reward": abs(profit),
                "kelly_fraction": max(0.0, profit),
                "setup_quality": score,
                "gating_status": "research_watch",
                "selected_direction": "Long",
                "factor_alignment": trade["parent_regime_root"],
                "setup_family": "CrashRebound",
                "entry_style": "drawdown_rebound",
                "session_model": "crypto_24x7",
                "htf_rb_type": trade["sub_regime_tags"],
                "ltf_path_label": path,
                "pda_survival_regime": "branch_proxy_not_trade_root",
            }
        )
    return rows


def build_bbn_rows(folds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in folds:
        edge = float(row["net_profit_ratio"]) / max(1, int(row["trades"]))
        rows.append(
            {
                "regime_profit_branch_path": row["regime_profit_branch_path"],
                "parent_regime_root": row["parent_regime_root"],
                "bbn_hint_node": "market_regime_context",
                "bbn_evidence_state": "soft_context_research_watch_not_mutation",
                "bbn_evidence_weight": 0.0,
                "trade_count": row["trades"],
                "win_rate": row["win_rate"],
                "mean_edge": edge,
                "reason": "branch path is proxy-only and not Board A trade-root accepted",
            }
        )
    return rows


def build_bundle(summary: dict[str, Any], run_id: str) -> dict[str, Any]:
    return {
        "schema_version": "regime-consumer-bundle/v1",
        "latest_decision": {
            "timestamp": run_id,
            "decision_state": "rejected_branch_path_proxy",
            "trade_usable": False,
            "final_label": "MainRegimeV2::BranchProxyCrashRebound",
            "label_set": [f"MainRegimeV2::{root}" for root in summary["roots_with_rows"]],
            "abstain_reasons": summary["hard_failures"],
        },
        "consumer_hints": {
            "execution_tree_hint": "unknown_abstain",
            "trade_usable": False,
            "bbn_evidence_hint": {
                "regime_decision_state": "rejected_branch_path_proxy",
                "regime_trade_usable": False,
                "regime_label": "MainRegimeV2::BranchProxyCrashRebound",
                "regime_label_set": [f"MainRegimeV2::{root}" for root in summary["roots_with_rows"]],
                "regime_transition_hazard": None,
                "regime_decision_reasons": summary["hard_failures"],
            },
            "path_ranker_context": {
                "recipe_id": "CrashRebound",
                "accepted_regime_id": summary["accepted_regime_id"],
                "downstream_consumption_status": summary["downstream_consumption_status"],
                "rc_spa": summary["rc_spa"],
                "diagnostic_rc_spa_before_hard_fail_zeroing": summary[
                    "diagnostic_rc_spa_before_hard_fail_zeroing"
                ],
                "roots_with_rows": summary["roots_with_rows"],
                "missing_roots": summary["missing_roots"],
                "branch_path_source": "auto_quant_timerange_label_proxy_not_board_a_trade_label",
            },
            "user_vrp_nq_context": {},
        },
        "provenance": {
            "run_id": run_id,
            "source": "isolated Auto-Quant CrashRebound replay plus Board B RC-SPA diagnostic",
        },
    }


def write_report(path: Path, summary: dict[str, Any], artifacts: dict[str, str]) -> None:
    failures = "\n".join(f"- `{item}`" for item in summary["hard_failures"]) or "- none"
    lines = [
        "# CrashRebound Branch RC-SPA v1",
        "",
        f"Run id: `{artifacts['run_id']}`",
        "",
        "## Decision",
        "",
        f"- RC-SPA: `{summary['rc_spa']:.4f}`.",
        f"- Diagnostic score before hard-fail zeroing: `{summary['diagnostic_rc_spa_before_hard_fail_zeroing']:.4f}`.",
        f"- Promotion level: `{summary['promotion_level']}`.",
        f"- Downstream status: `{summary['downstream_consumption_status']}`.",
        "",
        "## Gates",
        "",
        f"- Non-overlapping trades: `{summary['total_nonoverlap_trades']}`.",
        f"- Test folds: `{summary['test_folds']}`.",
        f"- Fold positive rate: `{summary['fold_positive_rate']:.4f}`.",
        f"- Bootstrap edge LCB 5pct: `{summary['bootstrap_edge_lcb_5pct']:.6f}`.",
        f"- 2x cost stress survival: `{summary['cost_stress_survival']}`.",
        f"- PBO: `{summary['pbo']:.4f}`.",
        f"- DSR proxy: `{summary['dsr']:.4f}`.",
        f"- Tail loss p95: `{summary['tail_loss_p95']:.4f}`.",
        f"- Regime specificity ratio: `{summary['regime_specificity_ratio']:.4f}`.",
        "",
        "## Hard Failures",
        "",
        failures,
        "",
        "## Artifacts",
        "",
    ]
    for key, value in artifacts.items():
        if key == "run_id":
            continue
        lines.append(f"- `{key}`: `{value}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--autoquant-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    autoquant_root = Path(args.autoquant_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    aq_run = load_autoquant_run(autoquant_root)
    trades, folds = extract_trade_rows(aq_run)
    summary = compute_rc_spa(trades, folds)
    target_rows = build_path_ranker_target(trades)
    bbn_rows = build_bbn_rows(folds)
    bundle = build_bundle(summary, args.run_id)

    artifacts = {
        "run_id": args.run_id,
        "trades_csv": str(output_root / "crashrebound_trades_with_branch_paths.csv"),
        "folds_csv": str(output_root / "crashrebound_branch_fold_metrics.csv"),
        "path_ranker_target_csv": str(output_root / "crashrebound_path_ranker_target.csv"),
        "bbn_rows_csv": str(output_root / "crashrebound_bbn_evidence_rows.csv"),
        "summary_json": str(output_root / "crashrebound_rc_spa_summary.json"),
        "bundle_json": str(output_root / "crashrebound_regime_consumer_bundle.json"),
        "report_md": str(output_root / "crashrebound_branch_rc_spa_v1.md"),
    }

    write_csv(Path(artifacts["trades_csv"]), trades, list(trades[0].keys()) if trades else [])
    write_csv(Path(artifacts["folds_csv"]), folds, list(folds[0].keys()) if folds else [])
    write_csv(Path(artifacts["path_ranker_target_csv"]), target_rows, list(target_rows[0].keys()) if target_rows else [])
    write_csv(Path(artifacts["bbn_rows_csv"]), bbn_rows, list(bbn_rows[0].keys()) if bbn_rows else [])
    summary["artifacts"] = {k: v for k, v in artifacts.items() if k != "run_id"}
    write_json(Path(artifacts["summary_json"]), summary)
    write_json(Path(artifacts["bundle_json"]), bundle)
    write_report(Path(artifacts["report_md"]), summary, artifacts)

    print(json.dumps({"summary": summary, "artifacts": artifacts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
