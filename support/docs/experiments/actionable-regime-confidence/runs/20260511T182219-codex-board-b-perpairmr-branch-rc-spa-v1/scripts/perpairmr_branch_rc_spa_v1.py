#!/usr/bin/env python3
"""Board B PerPairMR branch-path RC-SPA evidence builder.

This is an additive experiment artifact. It does not modify ict-engine runtime
code or the Auto-Quant checkout.
"""

from __future__ import annotations

import csv
import json
import math
import os
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting


RUN_ID = "20260511T182219+0800-codex-board-b-perpairmr-branch-rc-spa-v1"
SCHEMA_VERSION = "board-b-branch-rc-spa/v1"
RECIPE_ID = "PerPairMR"
PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "AVAX/USDT"]
TIMERANGES = [
    ("bull_2021", "20210101-20211231"),
    ("winter_2022", "20220101-20221231"),
    ("recovery_23_25", "20230101-20251231"),
    ("full_5y", "20210101-20251231"),
]

TARGET_EDGE = 0.005
TARGET_DSR = 1.0
DRAWDOWN_BUDGET = 0.25
TAIL_LOSS_BUDGET = 0.25
CRYPTO_INTRADAY_REQUIRED_TRADES = 100
MIN_TEST_FOLDS = 4
MIN_TRADES_PER_TEST_FOLD = 10
FOLD_POSITIVE_RATE_MIN = 0.75
EXTRA_ROUND_TRIP_COST_FOR_2X_FEE = 0.002


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot find repo root from {start}")


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = find_repo_root(Path(__file__).resolve())
AUTO_QUANT_ROOT = Path(os.environ.get("AUTO_QUANT_ROOT", "/Users/thrill3r/Auto-Quant"))
AUTO_QUANT_CONFIG = AUTO_QUANT_ROOT / "config.json"
AUTO_QUANT_DATA = AUTO_QUANT_ROOT / "user_data" / "data"
AUTO_QUANT_USER_DATA = AUTO_QUANT_ROOT / "user_data"
AUTO_QUANT_STRATEGIES = AUTO_QUANT_ROOT / "versions" / "0.4.1" / "strategies"
BOARD_A_SOURCE_PANEL = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
BOARD_A_CONSUMER_MAP = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/"
    "regime_factor_consumer_map_v1.csv"
)
MEASURED_RECIPE_ARTIFACT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260510T191144-board-b-factor-research-mtf1h/ict-engine/"
    "auto_quant_strategy_library.measured.json"
)

OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"


BRANCH_MAP = {
    "Bull": {
        "sub_regime_tags": "BullTrendContinuationOrPullback",
        "sub_sub_regime_or_profit_factor": "PairConditionalBreakoutOrMeanReversion",
        "profit_factor_family": "per_pair_regime_gated_mr_breakout",
        "profit_factor_leaf": RECIPE_ID,
        "allowed_action": "research_only_until_rc_spa_passes",
        "suppression_rule": "none_after_rc_spa_pass",
    },
    "Bear": {
        "sub_regime_tags": "BearMarketDefensiveReversion",
        "sub_sub_regime_or_profit_factor": "PairConditionalOversoldOrTrendFilter",
        "profit_factor_family": "per_pair_regime_gated_mr_breakout",
        "profit_factor_leaf": RECIPE_ID,
        "allowed_action": "research_only_until_rc_spa_passes",
        "suppression_rule": "suppress_if_cost_stress_or_tail_loss_fails",
    },
    "Sideways": {
        "sub_regime_tags": "RangeMeanReversion",
        "sub_sub_regime_or_profit_factor": "RsiOrBollingerExcursionByPair",
        "profit_factor_family": "per_pair_regime_gated_mr_breakout",
        "profit_factor_leaf": RECIPE_ID,
        "allowed_action": "research_only_until_rc_spa_passes",
        "suppression_rule": "suppress_if_fold_depth_or_specificity_fails",
    },
    "Crisis": {
        "sub_regime_tags": "ExtremeStress",
        "sub_sub_regime_or_profit_factor": "LongOnlyPerPairMRSuppressionReview",
        "profit_factor_family": "per_pair_regime_gated_mr_breakout",
        "profit_factor_leaf": RECIPE_ID,
        "allowed_action": "observe_or_suppress_until_crisis_branch_edge_passes",
        "suppression_rule": "suppress_long_rebound_if_crisis_branch_hard_gates_fail",
    },
}


def branch_path_for_root(root: str) -> str:
    branch = BRANCH_MAP[root]
    return (
        f"{root} -> {branch['sub_regime_tags']} -> "
        f"{branch['sub_sub_regime_or_profit_factor']} -> "
        f"{branch['profit_factor_leaf']}"
    )


REQUIRED_BRANCH_PATHS = [
    branch_path_for_root("Bull"),
    branch_path_for_root("Bear"),
    branch_path_for_root("Sideways"),
    branch_path_for_root("Crisis"),
    "Manipulation(scoped) -> DirectEventOverlayMissing -> no_direct_event_rows -> suppress_or_abstain",
]


def run_backtest(timerange: str) -> dict[str, Any]:
    args = {
        "config": [str(AUTO_QUANT_CONFIG)],
        "user_data_dir": str(AUTO_QUANT_USER_DATA),
        "datadir": str(AUTO_QUANT_DATA),
        "strategy": RECIPE_ID,
        "strategy_path": str(AUTO_QUANT_STRATEGIES),
        "timerange": timerange,
        "export": "none",
        "exportfilename": None,
        "cache": "none",
    }
    config = Configuration(args, RunMode.BACKTEST).get_config()
    config["exchange"]["pair_whitelist"] = list(PAIRS)
    bt = Backtesting(config)
    bt.start()
    return bt.results


def to_jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except TypeError:
            pass
    return str(value)


def extract_strategy_result(results: dict[str, Any]) -> dict[str, Any]:
    return results.get("strategy", {}).get(RECIPE_ID, {}) or {}


def extract_trades(strategy_result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for trade in strategy_result.get("trades", []) or []:
        rows.append({k: to_jsonable(v) for k, v in trade.items() if k != "orders"})
    return rows


def metric(strategy_result: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = strategy_result.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_root_floors() -> dict[str, float]:
    floors: dict[str, float] = {}
    with BOARD_A_CONSUMER_MAP.open(newline="") as fh:
        for row in csv.DictReader(fh):
            regime = row["regime"]
            if regime in {"Bull", "Bear", "Sideways", "Crisis", "Manipulation"}:
                floors[regime] = float(row["confidence_floor"])
    return floors


def build_daily_root_context() -> pd.DataFrame:
    df = pd.read_csv(
        BOARD_A_SOURCE_PANEL,
        usecols=["date", "ticker", "regime_label", "regime_confidence"],
    )
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.normalize()
    counts = (
        df.groupby(["date", "regime_label"], as_index=False)
        .agg(
            ticker_count=("ticker", "nunique"),
            row_count=("ticker", "size"),
            mean_source_confidence=("regime_confidence", "mean"),
        )
        .sort_values(
            ["date", "row_count", "mean_source_confidence", "regime_label"],
            ascending=[True, False, False, True],
        )
    )
    daily = counts.groupby("date", as_index=False).first()
    daily = daily.rename(columns={"regime_label": "parent_regime_root"})
    return daily.sort_values("date").reset_index(drop=True)


def attach_root_context(
    trades: list[dict[str, Any]],
    daily_context: pd.DataFrame,
    root_floors: dict[str, float],
) -> list[dict[str, Any]]:
    context_dates = list(daily_context["date"])
    attached = []
    for idx, trade in enumerate(trades, start=1):
        opened = pd.to_datetime(trade["open_date"], utc=True)
        trade_date = opened.normalize()
        pos = np.searchsorted(context_dates, trade_date, side="right") - 1
        if pos < 0:
            root = "Unlabeled"
            source_date = ""
            source_confidence = 0.0
            source_ticker_count = 0
            attachment_policy = "missing_source_context"
        else:
            ctx = daily_context.iloc[int(pos)]
            root = str(ctx["parent_regime_root"])
            source_date = pd.Timestamp(ctx["date"]).date().isoformat()
            source_confidence = float(ctx["mean_source_confidence"])
            source_ticker_count = int(ctx["ticker_count"])
            attachment_policy = "source_panel_previous_session_context_asof"
        branch = BRANCH_MAP.get(root, {})
        path = (
            f"{root} -> {branch.get('sub_regime_tags', 'Unlabeled')} -> "
            f"{branch.get('sub_sub_regime_or_profit_factor', 'Unlabeled')} -> "
            f"{branch.get('profit_factor_leaf', RECIPE_ID)}"
        )
        profit_ratio = float(trade.get("profit_ratio") or 0.0)
        attached.append(
            {
                "row_id": idx,
                "recipe_id": RECIPE_ID,
                "pair": trade.get("pair", ""),
                "open_date": pd.Timestamp(opened).isoformat(),
                "close_date": to_jsonable(trade.get("close_date", "")),
                "open_session_date": trade_date.date().isoformat(),
                "source_regime_session_date": source_date,
                "source_context_attachment_policy": attachment_policy,
                "parent_regime_root": root,
                "parent_regime_confidence_floor": root_floors.get(root, 0.0),
                "source_panel_mean_confidence": source_confidence,
                "source_panel_ticker_count": source_ticker_count,
                "manipulation_overlay_state": "not_consumed_no_direct_event_rows",
                "sub_regime_tags": branch.get("sub_regime_tags", "Unlabeled"),
                "sub_sub_regime_or_profit_factor": branch.get(
                    "sub_sub_regime_or_profit_factor", "Unlabeled"
                ),
                "profit_factor_family": branch.get(
                    "profit_factor_family", "per_pair_regime_gated_mr_breakout"
                ),
                "profit_factor_leaf": branch.get("profit_factor_leaf", RECIPE_ID),
                "regime_profit_branch_path": path,
                "regime_profit_branch_path_version": SCHEMA_VERSION,
                "trade_or_bar_horizon": "1h_trade",
                "allowed_action": branch.get("allowed_action", "research_only"),
                "suppression_rule": branch.get("suppression_rule", "suppress_until_labeled"),
                "year_fold": int(pd.Timestamp(opened).year),
                "profit_ratio_net": profit_ratio,
                "profit_abs": float(trade.get("profit_abs") or 0.0),
                "stake_amount": float(trade.get("stake_amount") or 0.0),
                "fee_open": float(trade.get("fee_open") or 0.0),
                "fee_close": float(trade.get("fee_close") or 0.0),
                "exit_reason": trade.get("exit_reason", ""),
                "is_open": bool(trade.get("is_open", False)),
            }
        )
    return attached


def bootstrap_lcb(values: np.ndarray, *, seed: int = 42) -> float:
    if len(values) == 0:
        return 0.0
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(5000, len(values)), replace=True)
    means = draws.mean(axis=1)
    return float(np.quantile(means, 0.05))


def max_drawdown_from_returns(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    equity = np.cumprod(1.0 + values)
    peak = np.maximum.accumulate(equity)
    drawdown = equity / peak - 1.0
    return float(abs(drawdown.min()))


def summarize_branch(path: str, rows: list[dict[str, Any]], all_rows: list[dict[str, Any]]) -> dict[str, Any]:
    returns = np.array([float(r["profit_ratio_net"]) for r in rows], dtype=float)
    all_returns = np.array([float(r["profit_ratio_net"]) for r in all_rows], dtype=float)
    outside = np.array(
        [float(r["profit_ratio_net"]) for r in all_rows if r["regime_profit_branch_path"] != path],
        dtype=float,
    )
    n = int(len(returns))
    folds = sorted({int(r["year_fold"]) for r in rows})
    fold_sums = []
    fold_counts = []
    for fold in folds:
        vals = np.array(
            [float(r["profit_ratio_net"]) for r in rows if int(r["year_fold"]) == fold],
            dtype=float,
        )
        fold_sums.append(float(vals.sum()))
        fold_counts.append(int(len(vals)))

    mean_return = float(returns.mean()) if n else 0.0
    win_rate = float((returns > 0).mean()) if n else 0.0
    bootstrap_edge_lcb = bootstrap_lcb(returns)
    stressed_returns = returns - EXTRA_ROUND_TRIP_COST_FOR_2X_FEE
    stressed_lcb = bootstrap_lcb(stressed_returns)
    cost_stress_survival = bool(n and stressed_returns.sum() > 0.0 and stressed_lcb > 0.0)
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
    pbo = 1.0
    pbo_method = "not_identifiable_single_selected_recipe_no_param_grid"

    edge_score = min(max(bootstrap_edge_lcb / TARGET_EDGE, 0.0), 1.0)
    fold_score = fold_positive_rate
    depth_score = min(max(n / CRYPTO_INTRADAY_REQUIRED_TRADES, 0.0), 1.0)
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

    failures = []
    if n < CRYPTO_INTRADAY_REQUIRED_TRADES:
        failures.append("reject_thin_trades")
    if len(folds) < MIN_TEST_FOLDS:
        failures.append("reject_insufficient_test_folds")
    if min_trades_per_fold < MIN_TRADES_PER_TEST_FOLD:
        failures.append("reject_fold_trade_depth")
    if fold_positive_rate < FOLD_POSITIVE_RATE_MIN:
        failures.append("reject_fold_inconsistency")
    if bootstrap_edge_lcb <= 0.0:
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
        "folds": ",".join(str(f) for f in folds),
        "min_trades_per_test_fold": min_trades_per_fold,
        "fold_positive_rate": fold_positive_rate,
        "win_rate": win_rate,
        "mean_profit_ratio_net": mean_return,
        "bootstrap_edge_lcb_5pct": bootstrap_edge_lcb,
        "bootstrap_edge_lcb_5pct_stressed_2x_cost": stressed_lcb,
        "pbo": pbo,
        "pbo_method": pbo_method,
        "dsr": dsr_proxy,
        "dsr_method": "trade_return_sharpe_proxy_not_full_deflated_sharpe",
        "cost_stress_result": "pass" if cost_stress_survival else "fail",
        "tail_loss_p95": tail_loss_p95,
        "max_drawdown_trade_equity_proxy": branch_mdd,
        "regime_specificity_ratio": specificity_ratio,
        "outside_mean_profit_ratio_net": outside_mean,
        "rc_spa": rc_spa,
        "promotion_level": "reject" if failures else ("research_watch" if rc_spa < 75 else "stable_candidate"),
        "hard_gate_result": "pass" if not failures else "fail:" + "|".join(dict.fromkeys(failures)),
        "downstream_consumption_status": (
            "not_started:blocked_by_branch_rc_spa_hard_gates"
            if failures
            else "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
        ),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    root_floors = load_root_floors()
    daily_context = build_daily_root_context()

    backtest_log = CHECK_DIR / "perpairmr_freqtrade_backtests.out"
    backtest_err = CHECK_DIR / "perpairmr_freqtrade_backtests.err"
    timerange_summaries = []
    full_trades: list[dict[str, Any]] = []
    with backtest_log.open("w", encoding="utf-8") as out, backtest_err.open("w", encoding="utf-8") as err:
        with redirect_stdout(out), redirect_stderr(err):
            for label, timerange in TIMERANGES:
                results = run_backtest(timerange)
                strategy_result = extract_strategy_result(results)
                trades = extract_trades(strategy_result)
                timerange_summaries.append(
                    {
                        "timerange_label": label,
                        "timerange": timerange,
                        "trade_count": int(metric(strategy_result, "total_trades")),
                        "win_rate": metric(strategy_result, "winrate"),
                        "total_profit_pct": metric(strategy_result, "profit_total") * 100.0,
                        "profit_factor": metric(strategy_result, "profit_factor"),
                        "sharpe": metric(strategy_result, "sharpe"),
                        "max_drawdown_pct": -abs(metric(strategy_result, "max_drawdown_account")) * 100.0,
                        "extracted_trade_rows": len(trades),
                    }
                )
                if label == "full_5y":
                    full_trades = trades

    branch_rows = attach_root_context(full_trades, daily_context, root_floors)
    write_csv(OUT_DIR / "perpairmr_branch_path_trades_v1.csv", branch_rows)
    write_csv(OUT_DIR / "perpairmr_timerange_backtest_summaries_v1.csv", timerange_summaries)

    branch_summaries = []
    observed_paths = sorted({r["regime_profit_branch_path"] for r in branch_rows})
    paths_to_score = list(dict.fromkeys([*REQUIRED_BRANCH_PATHS, *observed_paths]))
    for path in paths_to_score:
        rows = [r for r in branch_rows if r["regime_profit_branch_path"] == path]
        branch_summaries.append(summarize_branch(path, rows, branch_rows))
    write_csv(OUT_DIR / "perpairmr_branch_rc_spa_summary_v1.csv", branch_summaries)

    all_failures = [
        item["hard_gate_result"]
        for item in branch_summaries
        if str(item["hard_gate_result"]).startswith("fail:")
    ]
    branch_passes = [
        item for item in branch_summaries if item["hard_gate_result"] == "pass"
    ]
    max_rc_spa = max([float(item["rc_spa"]) for item in branch_summaries] or [0.0])
    total_trades = len(branch_rows)
    decision = {
        "board_state": "rejected" if not branch_passes else "research_watch",
        "gate_result": (
            "fail:all_branch_paths_failed_rc_spa_hard_gates"
            if not branch_passes
            else "pass:at_least_one_branch_path_eligible_for_downstream_probe"
        ),
        "stable_profit_score": max_rc_spa,
        "branch_paths_evaluated": len(branch_summaries),
        "branch_paths_passed": len(branch_passes),
        "total_trade_rows": total_trades,
        "downstream_consumption": (
            "not_started:blocked_by_branch_rc_spa_hard_gates"
            if not branch_passes
            else "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
        ),
        "primary_blocker": (
            "PerPairMR has real trade rows and root-first branch paths, but downstream "
            "runtime promotion remains blocked unless at least one branch path passes all "
            "RC-SPA hard gates, including fail-closed PBO for the selected recipe."
        ),
        "next_action": (
            "B3-repeat: if PerPairMR fails, synthesize a parameter/candidate matrix for the "
            "strongest root branch or choose a denser branch-specific recipe before attempting "
            "Pre-Bayes -> BBN -> CatBoost -> execution-tree branch consumption."
        ),
    }

    provider_snapshot = {
        "provider_status_artifacts": {
            "all": str(RUN_ROOT / "provider-snapshot/provider_status_agent.json"),
            "ibkr": str(RUN_ROOT / "provider-snapshot/provider_status_ibkr_agent.json"),
            "tradingview_mcp": str(
                RUN_ROOT / "provider-snapshot/provider_status_tradingview_mcp_agent.json"
            ),
            "yfinance": str(RUN_ROOT / "provider-snapshot/provider_status_yfinance_agent.json"),
            "kraken_public": str(
                RUN_ROOT / "provider-snapshot/provider_status_kraken_public_agent.json"
            ),
            "kraken_cli": str(
                RUN_ROOT / "provider-snapshot/provider_status_kraken_cli_agent.json"
            ),
            "tvremix_config_presence": str(
                RUN_ROOT / "provider-snapshot/tvremix_config_presence.txt"
            ),
        },
        "actual_recipe_data_source": "Auto-Quant/Freqtrade local OHLCV cache with exchange=binance in config.json",
        "provider_use_note": (
            "This loop consumed the existing PerPairMR Auto-Quant cache. Provider snapshots "
            "were captured so the next density run can prefer ready yfinance/tradingview_mcp/"
            "kraken_cli paths and handle ibkr/kraken_public dependency blockers explicitly."
        ),
    }

    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_root": str(RUN_ROOT.relative_to(REPO_ROOT)),
        "recipe_id": RECIPE_ID,
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": str(BOARD_A_CONSUMER_MAP.relative_to(REPO_ROOT)),
        "recipe_artifact": str(MEASURED_RECIPE_ARTIFACT.relative_to(REPO_ROOT)),
        "auto_quant": {
            "root": str(AUTO_QUANT_ROOT),
            "strategy_path": str(AUTO_QUANT_STRATEGIES / f"{RECIPE_ID}.py"),
            "config": str(AUTO_QUANT_CONFIG),
            "pairs": PAIRS,
            "timeranges": TIMERANGES,
        },
        "rc_spa_parameters": {
            "target_edge": TARGET_EDGE,
            "target_dsr": TARGET_DSR,
            "drawdown_budget": DRAWDOWN_BUDGET,
            "tail_loss_budget": TAIL_LOSS_BUDGET,
            "required_trades": CRYPTO_INTRADAY_REQUIRED_TRADES,
            "min_test_folds": MIN_TEST_FOLDS,
            "min_trades_per_test_fold": MIN_TRADES_PER_TEST_FOLD,
            "fold_positive_rate_min": FOLD_POSITIVE_RATE_MIN,
            "extra_round_trip_cost_for_2x_fee": EXTRA_ROUND_TRIP_COST_FOR_2X_FEE,
            "pbo_policy": "fail_closed_when_only_one_selected_recipe_has_no_parameter_or_candidate_matrix",
        },
        "artifacts": {
            "trade_rows_csv": str(
                (OUT_DIR / "perpairmr_branch_path_trades_v1.csv").relative_to(REPO_ROOT)
            ),
            "branch_summary_csv": str(
                (OUT_DIR / "perpairmr_branch_rc_spa_summary_v1.csv").relative_to(REPO_ROOT)
            ),
            "timerange_summary_csv": str(
                (OUT_DIR / "perpairmr_timerange_backtest_summaries_v1.csv").relative_to(
                    REPO_ROOT
                )
            ),
            "backtest_stdout": str(backtest_log.relative_to(REPO_ROOT)),
            "backtest_stderr": str(backtest_err.relative_to(REPO_ROOT)),
        },
        "provider_snapshot": provider_snapshot,
        "timerange_summaries": timerange_summaries,
        "branch_summaries": branch_summaries,
        "decision": decision,
        "all_branch_gate_failures": all_failures,
        "completion": {
            "runtime_code_changed": False,
            "raw_auto_quant_data_committed": False,
            "thresholds_relaxed": False,
            "downstream_runtime_consumed_branch_path": bool(branch_passes),
        },
    }

    report_path = OUT_DIR / "perpairmr_branch_rc_spa_report_v1.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = OUT_DIR / "perpairmr_branch_rc_spa_report_v1.md"
    lines = [
        "# PerPairMR Branch RC-SPA v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Stable profit score: `{decision['stable_profit_score']:.4f}`",
        f"- Branch paths evaluated: `{decision['branch_paths_evaluated']}`",
        f"- Branch paths passed: `{decision['branch_paths_passed']}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        f"- Primary blocker: {decision['primary_blocker']}",
        "",
        "## Branch Summary",
        "",
        "| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in branch_summaries:
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
            f"- Report JSON: `{report_path.relative_to(REPO_ROOT)}`",
            f"- Trade rows: `{(OUT_DIR / 'perpairmr_branch_path_trades_v1.csv').relative_to(REPO_ROOT)}`",
            f"- Branch summary: `{(OUT_DIR / 'perpairmr_branch_rc_spa_summary_v1.csv').relative_to(REPO_ROOT)}`",
            f"- Timerange summary: `{(OUT_DIR / 'perpairmr_timerange_backtest_summaries_v1.csv').relative_to(REPO_ROOT)}`",
            f"- Backtest stdout: `{backtest_log.relative_to(REPO_ROOT)}`",
            f"- Backtest stderr: `{backtest_err.relative_to(REPO_ROOT)}`",
            "",
            "## Next",
            "",
            f"- {decision['next_action']}",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"trade_rows={total_trades}",
        f"branch_paths_evaluated={len(branch_summaries)}",
        f"branch_paths_passed={len(branch_passes)}",
        f"gate_result={decision['gate_result']}",
        f"downstream_consumption={decision['downstream_consumption']}",
        f"report_json={report_path.relative_to(REPO_ROOT)}",
    ]
    if total_trades < CRYPTO_INTRADAY_REQUIRED_TRADES:
        assertions.append("ASSERT_FAIL:expected_at_least_100_full_5y_trades")
    if len(branch_summaries) < len(REQUIRED_BRANCH_PATHS):
        assertions.append("ASSERT_FAIL:missing_required_branch_summaries")
    (CHECK_DIR / "perpairmr_branch_rc_spa_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    if any(line.startswith("ASSERT_FAIL") for line in assertions):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
