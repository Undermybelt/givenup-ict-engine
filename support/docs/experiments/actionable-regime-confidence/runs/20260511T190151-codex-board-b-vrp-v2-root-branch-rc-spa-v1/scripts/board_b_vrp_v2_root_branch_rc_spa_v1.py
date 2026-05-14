#!/usr/bin/env python3
"""Build a root-first Board B RC-SPA packet from the local VRP V2 artifact.

This is an additive experiment script. It consumes the existing Auto-Quant
VRP V2 realized-trades JSONL from /private/tmp, attaches Board A root labels,
scores root-first branch paths, and emits an ict-engine dry-run wire file. It
does not modify ict-engine runtime code or the Auto-Quant checkout.
"""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T190151+0800-codex-board-b-vrp-v2-root-branch-rc-spa-v1"
SCHEMA_VERSION = "board-b-vrp-v2-root-branch-rc-spa/v1"
RECIPE_ID = "VRPCompression_V2_NQ_15m"
SYMBOL = "VRP_NQ_V2_B_190151"
TARGET_EDGE = 0.001
TARGET_DSR = 1.0
DRAWDOWN_BUDGET = 0.25
TAIL_LOSS_BUDGET = 0.03
NQ_INTRADAY_REQUIRED_TRADES = 100
MIN_TEST_FOLDS = 4
MIN_TRADES_PER_TEST_FOLD = 10
FOLD_POSITIVE_RATE_MIN = 0.75
EXTRA_ROUND_TRIP_COST_FOR_2X_COST = 0.0002


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot find repo root from {start}")


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = find_repo_root(Path(__file__).resolve())
OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
ICT_DIR = RUN_ROOT / "ict-engine-fail-closed"

VRP_TRADES = Path("/private/tmp/vrp_v2_realized_trades.jsonl")
VRP_LIBRARY = Path("/private/tmp/vrp_v2_strategy_library.json")
VRP_RUNTIME_CLOSURE = Path("/private/tmp/vrp-v2-runtime-closure")
SOURCE_REGIME_CSV = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
BOARD_A_CONSUMER_MAP = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/"
    "regime_factor_consumer_map_v1.csv"
)

REPORT_JSON = OUT_DIR / "vrp_v2_root_branch_rc_spa_report_v1.json"
REPORT_MD = OUT_DIR / "vrp_v2_root_branch_rc_spa_report_v1.md"
TRADE_ROWS_CSV = OUT_DIR / "vrp_v2_root_branch_trades_v1.csv"
BRANCH_SUMMARY_CSV = OUT_DIR / "vrp_v2_root_branch_rc_spa_summary_v1.csv"
WIRE_JSONL = ICT_DIR / "vrp_v2_real_trades_wire_v1.jsonl"
WIRE_COUNT = ICT_DIR / "vrp_v2_real_trades_wire_v1.count"
ASSERTIONS = CHECK_DIR / "vrp_v2_root_branch_rc_spa_v1_assertions.out"

BRANCH_MAP = {
    "Bull": {
        "sub_regime_tags": "TrendExpansion",
        "sub_sub_regime_or_profit_factor": "VRPCompressionCarry",
        "profit_factor_family": "options_volatility_risk_premium",
        "allowed_action": "long_carry_research_only_until_branch_rc_spa_passes",
        "suppression_rule": "suppress_if_bull_vrp_branch_rc_spa_fails",
    },
    "Bear": {
        "sub_regime_tags": "BearMarketDrawdown",
        "sub_sub_regime_or_profit_factor": "VRPTailRiskSuppression",
        "profit_factor_family": "options_volatility_risk_premium",
        "allowed_action": "suppress_long_carry_until_bear_branch_rc_spa_passes",
        "suppression_rule": "tail_guard_blocks_bear_vrp_if_branch_rc_spa_fails",
    },
    "Sideways": {
        "sub_regime_tags": "RangeConsolidation",
        "sub_sub_regime_or_profit_factor": "VRPCompressionCarry",
        "profit_factor_family": "options_volatility_risk_premium",
        "allowed_action": "long_carry_research_only_until_branch_rc_spa_passes",
        "suppression_rule": "suppress_if_sideways_vrp_branch_rc_spa_fails",
    },
    "Crisis": {
        "sub_regime_tags": "ExtremeStress",
        "sub_sub_regime_or_profit_factor": "VRPTailRiskSuppression",
        "profit_factor_family": "options_volatility_risk_premium",
        "allowed_action": "no_trade_until_crisis_branch_rc_spa_passes",
        "suppression_rule": "tail_guard_blocks_crisis_vrp",
    },
}


def branch_path_for_root(root: str) -> str:
    branch = BRANCH_MAP[root]
    return (
        f"{root} -> {branch['sub_regime_tags']} -> "
        f"{branch['sub_sub_regime_or_profit_factor']} -> {RECIPE_ID}"
    )


REQUIRED_ROOT_PATHS = [branch_path_for_root(root) for root in ["Bull", "Bear", "Sideways", "Crisis"]]
MANIPULATION_PATH = (
    "Manipulation(scoped) -> DirectEventOverlayMissing -> "
    "no_direct_event_rows -> suppress_or_abstain"
)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def load_root_floors() -> dict[str, float]:
    floors: dict[str, float] = {}
    with BOARD_A_CONSUMER_MAP.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            regime = row["regime"]
            if regime in {"Bull", "Bear", "Sideways", "Crisis", "Manipulation"}:
                floors[regime] = float(row["confidence_floor"])
    return floors


def load_source_schedule() -> pd.DataFrame:
    df = pd.read_csv(
        SOURCE_REGIME_CSV,
        usecols=["date", "ticker", "regime_label", "regime_confidence", "vix"],
    )
    df = df[df["ticker"] == "^IXIC"].copy()
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.normalize()
    df = df.sort_values("date").reset_index(drop=True)
    df = df.rename(
        columns={
            "regime_label": "parent_regime_root",
            "regime_confidence": "source_anchor_confidence",
        }
    )
    return df[["date", "parent_regime_root", "source_anchor_confidence", "vix"]]


def load_vrp_trades() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with VRP_TRADES.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def attach_root_context(
    trades: list[dict[str, Any]],
    schedule: pd.DataFrame,
    floors: dict[str, float],
) -> list[dict[str, Any]]:
    context_dates = schedule["date"].values.astype("datetime64[ns]")
    roots = schedule["parent_regime_root"].to_numpy()
    confidences = schedule["source_anchor_confidence"].to_numpy(dtype=float)
    vix_values = schedule["vix"].to_numpy(dtype=float)
    attached: list[dict[str, Any]] = []
    for idx, trade in enumerate(trades, start=1):
        opened = pd.to_datetime(int(trade["open_ts_ms"]), unit="ms", utc=True)
        closed = pd.to_datetime(int(trade["close_ts_ms"]), unit="ms", utc=True)
        trade_date = opened.normalize().to_datetime64()
        pos = int(np.searchsorted(context_dates, trade_date, side="right") - 1)
        if pos < 0:
            root = "Unlabeled"
            source_date = ""
            source_confidence = 0.0
            source_vix = 0.0
        else:
            root = str(roots[pos])
            source_date = pd.Timestamp(context_dates[pos]).date().isoformat()
            source_confidence = float(confidences[pos])
            source_vix = float(vix_values[pos])
        branch = BRANCH_MAP.get(root, {})
        branch_path = (
            f"{root} -> {branch.get('sub_regime_tags', 'Unlabeled')} -> "
            f"{branch.get('sub_sub_regime_or_profit_factor', 'Unlabeled')} -> {RECIPE_ID}"
        )
        pnl = float(trade.get("pnl") or 0.0)
        attached.append(
            {
                "row_id": idx,
                "schema_version": SCHEMA_VERSION,
                "recipe_id": RECIPE_ID,
                "strategy_name": trade.get("strategy_name", RECIPE_ID),
                "strategy_mutation_id": trade.get("strategy_mutation_id", "pandas-vrp-v2-nq-15m"),
                "auto_quant_run_id": trade.get("auto_quant_run_id", "vrp-v2-8y-2019-2025"),
                "symbol": trade.get("symbol", "NQ"),
                "trade_id": trade.get("trade_id", f"{RECIPE_ID}:{idx}"),
                "open_ts_ms": int(trade["open_ts_ms"]),
                "close_ts_ms": int(trade["close_ts_ms"]),
                "open_date": opened.isoformat(),
                "close_date": closed.isoformat(),
                "open_session_date": opened.date().isoformat(),
                "source_regime_session_date": source_date,
                "source_context_attachment_policy": "^IXIC_source_anchor_previous_session_context",
                "source_anchor": "^IXIC",
                "target_market": "NQ=F/NQ_USD",
                "parent_regime_root": root,
                "parent_regime_confidence_floor": floors.get(root, 0.0),
                "source_anchor_confidence": source_confidence,
                "source_anchor_vix": source_vix,
                "manipulation_overlay_state": "not_consumed_no_direct_event_rows",
                "sub_regime_tags": branch.get("sub_regime_tags", "Unlabeled"),
                "sub_sub_regime_or_profit_factor": branch.get(
                    "sub_sub_regime_or_profit_factor", "Unlabeled"
                ),
                "profit_factor_family": branch.get(
                    "profit_factor_family", "options_volatility_risk_premium"
                ),
                "profit_factor_leaf": RECIPE_ID,
                "regime_profit_branch_path": branch_path,
                "regime_profit_branch_path_version": SCHEMA_VERSION,
                "trade_or_bar_horizon": "15m_trade",
                "allowed_action": branch.get("allowed_action", "research_only"),
                "suppression_rule": branch.get("suppression_rule", "suppress_until_labeled"),
                "year_fold": int(opened.year),
                "profit_ratio_net": pnl,
                "pnl": pnl,
                "realized_outcome": trade.get("realized_outcome", "win" if pnl > 0 else "loss"),
                "regime_at_entry": trade.get("regime_at_entry", "vol_compression"),
            }
        )
    return attached


def bootstrap_lcb(values: np.ndarray, seed: int = 42) -> float:
    if len(values) == 0:
        return 0.0
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(5000, len(values)), replace=True)
    return float(np.quantile(draws.mean(axis=1), 0.05))


def max_drawdown_from_returns(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    equity = np.cumprod(1.0 + values)
    peak = np.maximum.accumulate(equity)
    return float(abs((equity / peak - 1.0).min()))


def estimate_pbo(path: str, all_rows: list[dict[str, Any]]) -> tuple[float, str]:
    rows = [r for r in all_rows if r["regime_profit_branch_path"] == path]
    folds = sorted({int(r["year_fold"]) for r in rows})
    if len(folds) < MIN_TEST_FOLDS:
        return 1.0, "not_identifiable_lt4_folds"
    fold_returns = [
        sum(float(r["profit_ratio_net"]) for r in rows if int(r["year_fold"]) == fold)
        for fold in folds
    ]
    # With one realized VRP recipe rather than a parameter grid, use a conservative
    # fold-instability proxy: negative out-of-sample fold share.
    negative = sum(1 for value in fold_returns if value <= 0.0)
    return float(negative / len(fold_returns)), "single_recipe_negative_fold_share_proxy"


def summarize_branch(path: str, rows: list[dict[str, Any]], all_rows: list[dict[str, Any]]) -> dict[str, Any]:
    returns = np.array([float(r["profit_ratio_net"]) for r in rows], dtype=float)
    outside = np.array(
        [float(r["profit_ratio_net"]) for r in all_rows if r["regime_profit_branch_path"] != path],
        dtype=float,
    )
    n = int(len(returns))
    folds = sorted({int(r["year_fold"]) for r in rows})
    fold_sums: list[float] = []
    fold_counts: list[int] = []
    for fold in folds:
        vals = np.array(
            [float(r["profit_ratio_net"]) for r in rows if int(r["year_fold"]) == fold],
            dtype=float,
        )
        fold_sums.append(float(vals.sum()))
        fold_counts.append(int(len(vals)))
    mean_return = float(returns.mean()) if n else 0.0
    win_rate = float((returns > 0).mean()) if n else 0.0
    edge_lcb = bootstrap_lcb(returns)
    stressed = returns - EXTRA_ROUND_TRIP_COST_FOR_2X_COST
    stressed_lcb = bootstrap_lcb(stressed)
    cost_stress_survival = bool(n and stressed.sum() > 0.0 and stressed_lcb > 0.0)
    std = float(returns.std(ddof=1)) if n > 1 else 0.0
    dsr_proxy = float(mean_return / std * math.sqrt(n)) if std > 0.0 else 0.0
    tail_loss_p95 = float(max(0.0, -np.quantile(returns, 0.05))) if n else 0.0
    branch_mdd = max_drawdown_from_returns(returns)
    outside_mean = float(outside.mean()) if len(outside) else 0.0
    if mean_return > 0.0 and outside_mean <= 0.0:
        specificity_ratio = 999.0
    elif outside_mean > 0.0:
        specificity_ratio = float(mean_return / outside_mean)
    else:
        specificity_ratio = 0.0
    fold_positive_rate = (
        float(sum(1 for value in fold_sums if value > 0.0) / len(fold_sums))
        if fold_sums
        else 0.0
    )
    min_trades_per_fold = int(min(fold_counts)) if fold_counts else 0
    pbo, pbo_method = estimate_pbo(path, all_rows)

    edge_score = min(max(edge_lcb / TARGET_EDGE, 0.0), 1.0)
    fold_score = fold_positive_rate
    depth_score = min(max(n / NQ_INTRADAY_REQUIRED_TRADES, 0.0), 1.0)
    dsr_score = min(max(dsr_proxy / TARGET_DSR, 0.0), 1.0)
    pbo_score = 1.0 - min(max(pbo / 0.25, 0.0), 1.0)
    cost_score = 1.0 if cost_stress_survival else 0.0
    drawdown_score = 1.0 - min(max(branch_mdd / DRAWDOWN_BUDGET, 0.0), 1.0)
    specificity_score = min(max((specificity_ratio - 1.0) / 0.5, 0.0), 1.0)
    rc_spa = 100.0 * (
        0.20 * edge_score
        + 0.15 * fold_score
        + 0.15 * depth_score
        + 0.15 * dsr_score
        + 0.10 * pbo_score
        + 0.10 * cost_score
        + 0.10 * drawdown_score
        + 0.05 * specificity_score
    )

    failures: list[str] = []
    if n < NQ_INTRADAY_REQUIRED_TRADES:
        failures.append("reject_thin_trades")
    if len(folds) < MIN_TEST_FOLDS:
        failures.append("reject_insufficient_test_folds")
    if min_trades_per_fold < MIN_TRADES_PER_TEST_FOLD:
        failures.append("reject_fold_trade_depth")
    if fold_positive_rate < FOLD_POSITIVE_RATE_MIN:
        failures.append("reject_fold_inconsistency")
    if edge_lcb <= 0.0:
        failures.append("reject_no_positive_edge")
    if not cost_stress_survival:
        failures.append("reject_cost_fragile")
    if pbo > 0.25:
        failures.append("reject_overfit_risk")
    if dsr_proxy <= 0.0:
        failures.append("reject_dsr_nonpositive")
    if tail_loss_p95 > TAIL_LOSS_BUDGET:
        failures.append("reject_tail_risk")
    if specificity_ratio < 1.20:
        failures.append("reject_no_regime_specificity")
    if rc_spa < 60.0:
        failures.append("reject_rc_spa_below_60")

    parent_root = rows[0]["parent_regime_root"] if rows else path.split(" -> ", 1)[0]
    return {
        "recipe_id": RECIPE_ID,
        "regime_profit_branch_path": path,
        "parent_regime_root": parent_root,
        "total_trades": n,
        "test_folds": len(folds),
        "min_trades_per_test_fold": min_trades_per_fold,
        "fold_positive_rate": fold_positive_rate,
        "win_rate": win_rate,
        "mean_profit_ratio_net": mean_return,
        "bootstrap_edge_lcb_5pct": edge_lcb,
        "bootstrap_edge_lcb_5pct_stressed_2x_cost": stressed_lcb,
        "pbo": pbo,
        "pbo_method": pbo_method,
        "dsr": dsr_proxy,
        "cost_stress_result": "pass" if cost_stress_survival else "fail",
        "tail_loss_p95": tail_loss_p95,
        "max_drawdown_trade_equity_proxy": branch_mdd,
        "regime_specificity_ratio": specificity_ratio,
        "outside_mean_profit_ratio_net": outside_mean,
        "rc_spa": rc_spa,
        "hard_gate_result": "pass" if not failures else "fail:" + "|".join(dict.fromkeys(failures)),
    }


def write_wire(rows: list[dict[str, Any]]) -> None:
    ICT_DIR.mkdir(parents=True, exist_ok=True)
    with WIRE_JSONL.open("w", encoding="utf-8") as fh:
        for row in rows:
            root = row["parent_regime_root"]
            pnl = float(row["pnl"])
            feedback = {
                "protocol_version": SCHEMA_VERSION,
                "recommendation_id": row["trade_id"],
                "recommended_at": row["open_date"],
                "symbol": SYMBOL,
                "node_id": root,
                "branch_id": row["regime_profit_branch_path"],
                "scenario_id": row["sub_regime_tags"],
                "path_id": row["regime_profit_branch_path"],
                "direction": "long",
                "entry_style": "vrp_compression",
                "candidate_set_id": RUN_ID,
                "candidate_set_size": len(rows),
                "followed_path": True,
                "realized_outcome": row["realized_outcome"],
                "realized_pnl": pnl,
                "exit_reason": "vrp_exit_or_regime_break",
                "notes": "diagnostic_dry_run_only_vrp_v2_root_branch_rc_spa",
            }
            factors = [
                {
                    "factor_name": "market_regime_context.root",
                    "category": "regime_context",
                    "direction": root,
                    "value": row["source_anchor_confidence"],
                    "confidence": row["source_anchor_confidence"],
                    "weighted_score": row["source_anchor_confidence"],
                    "uncertainty_contribution": max(0.0, 1.0 - row["source_anchor_confidence"]),
                },
                {
                    "factor_name": "regime_profit_branch_path",
                    "category": "branch_path",
                    "direction": "Bull" if pnl >= 0 else "Bear",
                    "value": pnl,
                    "confidence": row["source_anchor_confidence"],
                    "weighted_score": pnl,
                    "uncertainty_contribution": max(0.0, 1.0 - row["source_anchor_confidence"]),
                },
                {
                    "factor_name": "iv_hv_compression",
                    "category": "options_volatility",
                    "direction": "Bull",
                    "value": pnl,
                    "confidence": 0.65,
                    "weighted_score": pnl,
                    "uncertainty_contribution": 0.35,
                },
            ]
            payload = {
                "schema_version": "1.0",
                "symbol": SYMBOL,
                "trade_id": row["trade_id"],
                "strategy_name": RECIPE_ID,
                "strategy_mutation_id": row["strategy_mutation_id"],
                "auto_quant_run_id": RUN_ID,
                "open_ts_ms": row["open_ts_ms"],
                "close_ts_ms": row["close_ts_ms"],
                "direction": "long",
                "pnl": pnl,
                "realized_outcome": row["realized_outcome"],
                "regime_at_entry": root,
                "entry_signal": "vrp_compression",
                "factors_used": factors,
                "structural_feedback": feedback,
            }
            fh.write(json.dumps(payload, sort_keys=True) + "\n")
    WIRE_COUNT.write_text(f"{len(rows)}\n", encoding="utf-8")


def write_report(report: dict[str, Any]) -> None:
    decision = report["decision"]
    lines = [
        "# VRP V2 Root Branch RC-SPA v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Stable profit score: `{decision['stable_profit_score']:.4f}`",
        f"- Branch paths evaluated: `{decision['branch_paths_evaluated']}`",
        f"- Branch paths passed: `{decision['branch_paths_passed']}`",
        f"- Root trade counts: `{decision['root_trade_counts']}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        f"- Primary blocker: {decision['primary_blocker']}",
        "",
        "## Inputs",
        "",
        f"- VRP realized trades: `{VRP_TRADES}`",
        f"- VRP strategy library: `{VRP_LIBRARY}`",
        f"- Prior runtime closure: `{VRP_RUNTIME_CLOSURE}`",
        f"- Board A consumer map: `{rel(BOARD_A_CONSUMER_MAP)}`",
        f"- Source anchor: `^IXIC`; target: `NQ`; source artifact is existing Auto-Quant/Pandas VRP V2.",
        "",
        "## Branch Summary",
        "",
        "| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["branch_summaries"]:
        lines.append(
            f"| {row['parent_regime_root']} | {row['total_trades']} | {row['test_folds']} | "
            f"{row['min_trades_per_test_fold']} | {row['fold_positive_rate']:.4f} | "
            f"{row['bootstrap_edge_lcb_5pct']:.6f} | {row['pbo']:.2f} | "
            f"{row['dsr']:.4f} | {row['rc_spa']:.4f} | `{row['hard_gate_result']}` |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Report JSON: `{rel(REPORT_JSON)}`",
            f"- Trade rows: `{rel(TRADE_ROWS_CSV)}`",
            f"- Branch summary: `{rel(BRANCH_SUMMARY_CSV)}`",
            f"- ict-engine wire JSONL: `{rel(WIRE_JSONL)}`",
            f"- Assertions: `{rel(ASSERTIONS)}`",
            "",
            "## Next",
            "",
            f"- {decision['next_action']}",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, ICT_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    for path in [VRP_TRADES, VRP_LIBRARY, SOURCE_REGIME_CSV, BOARD_A_CONSUMER_MAP]:
        if not path.exists():
            raise FileNotFoundError(path)
    floors = load_root_floors()
    schedule = load_source_schedule()
    trades = load_vrp_trades()
    rows = attach_root_context(trades, schedule, floors)
    paths_to_score = [*REQUIRED_ROOT_PATHS, MANIPULATION_PATH]
    for path in sorted({row["regime_profit_branch_path"] for row in rows}):
        if path not in paths_to_score:
            paths_to_score.append(path)
    branch_summaries = [
        summarize_branch(path, [row for row in rows if row["regime_profit_branch_path"] == path], rows)
        for path in paths_to_score
    ]
    branch_passes = [row for row in branch_summaries if row["hard_gate_result"] == "pass"]
    required_failures = [
        row for row in branch_summaries
        if row["regime_profit_branch_path"] in REQUIRED_ROOT_PATHS
        and row["hard_gate_result"] != "pass"
    ]
    max_rc_spa = max([float(row["rc_spa"]) for row in branch_summaries] or [0.0])
    root_counts = {
        root: sum(1 for row in rows if row["parent_regime_root"] == root)
        for root in ["Bull", "Bear", "Sideways", "Crisis"]
    }
    if not branch_passes:
        gate_result = "fail:all_branch_paths_failed_rc_spa_hard_gates"
    elif required_failures:
        gate_result = "fail:required_root_branch_hard_gates_failed"
    else:
        gate_result = "pass:all_required_root_branch_paths_passed"
    downstream = (
        "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
        if gate_result.startswith("pass:")
        else "not_started:blocked_by_branch_rc_spa_hard_gates"
    )
    decision = {
        "board_state": "research_watch" if gate_result.startswith("pass:") else "rejected",
        "gate_result": gate_result,
        "stable_profit_score": max_rc_spa,
        "branch_paths_evaluated": len(branch_summaries),
        "branch_paths_passed": len(branch_passes),
        "required_root_failures": [row["parent_regime_root"] for row in required_failures],
        "total_trade_rows": len(rows),
        "root_trade_counts": root_counts,
        "downstream_consumption": downstream,
        "primary_blocker": (
            "VRP V2 is a different Auto-Quant artifact family and carries root-first branch paths, "
            "but downstream promotion is blocked unless every required root branch clears RC-SPA; "
            "scoped Manipulation still has no direct rows."
        ),
        "next_action": (
            "If VRP is reused, convert it into a true multi-root parameter matrix or add direct "
            "Manipulation rows before downstream promotion; do not treat aggregate Sharpe as enough."
        ),
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_root": rel(RUN_ROOT),
        "recipe_id": RECIPE_ID,
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": rel(BOARD_A_CONSUMER_MAP),
        "auto_quant": {
            "realized_trades": str(VRP_TRADES),
            "strategy_library": str(VRP_LIBRARY),
            "prior_runtime_closure": str(VRP_RUNTIME_CLOSURE),
        },
        "rc_spa_parameters": {
            "target_edge": TARGET_EDGE,
            "target_dsr": TARGET_DSR,
            "drawdown_budget": DRAWDOWN_BUDGET,
            "tail_loss_budget": TAIL_LOSS_BUDGET,
            "required_trades": NQ_INTRADAY_REQUIRED_TRADES,
            "min_test_folds": MIN_TEST_FOLDS,
            "min_trades_per_test_fold": MIN_TRADES_PER_TEST_FOLD,
            "fold_positive_rate_min": FOLD_POSITIVE_RATE_MIN,
            "extra_round_trip_cost_for_2x_cost": EXTRA_ROUND_TRIP_COST_FOR_2X_COST,
        },
        "artifacts": {
            "report_md": rel(REPORT_MD),
            "report_json": rel(REPORT_JSON),
            "trade_rows_csv": rel(TRADE_ROWS_CSV),
            "branch_summary_csv": rel(BRANCH_SUMMARY_CSV),
            "ict_engine_wire_jsonl": rel(WIRE_JSONL),
        },
        "branch_summaries": branch_summaries,
        "decision": decision,
        "completion": {
            "runtime_code_changed": False,
            "auto_quant_checkout_changed": False,
            "raw_auto_quant_data_committed": False,
            "thresholds_relaxed_after_scoring": False,
            "downstream_runtime_consumed_branch_path": gate_result.startswith("pass:"),
        },
    }
    write_csv(TRADE_ROWS_CSV, rows)
    write_csv(BRANCH_SUMMARY_CSV, branch_summaries)
    write_wire(rows)
    write_json(REPORT_JSON, report)
    write_report(report)
    assertions = [
        f"run_id={RUN_ID}",
        f"recipe_id={RECIPE_ID}",
        f"trade_rows={len(rows)}",
        f"root_counts={root_counts}",
        f"branch_paths_evaluated={len(branch_summaries)}",
        f"branch_paths_passed={len(branch_passes)}",
        f"gate_result={gate_result}",
        f"downstream_consumption={downstream}",
        f"report_json={rel(REPORT_JSON)}",
        f"wire_jsonl={rel(WIRE_JSONL)}",
    ]
    if len(rows) <= 0:
        assertions.append("ASSERT_FAIL:no_trade_rows")
    if root_counts["Bull"] <= 0:
        assertions.append("ASSERT_FAIL:no_bull_rows")
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"ok": not any(a.startswith("ASSERT_FAIL") for a in assertions), **decision}, indent=2, sort_keys=True))
    return 1 if any(a.startswith("ASSERT_FAIL") for a in assertions) else 0


if __name__ == "__main__":
    raise SystemExit(main())
