from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import pandas as pd
from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUN = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T124408+0800-codex-123227-tomac-trade-density-iteration-v1"
)
AQ = SOURCE_RUN / "state_tomac_trade_density_iteration_v1/.deps/auto-quant"
TRADE_EXPORTS = RUN_ROOT / "trade-exports"
COMMAND_OUTPUT = RUN_ROOT / "command-output"


sys.path.insert(0, str(AQ))
import run_tomac  # noqa: E402


def patch_synthetic_precision() -> None:
    original = run_tomac._synthetic_market

    def patched(pair: str, trading_mode: str) -> dict:
        market = original(pair, trading_mode)
        market["precision"]["amount"] = 1e-8
        market["precision"]["base"] = 1e-8
        market["precision"]["price"] = 1e-7
        market["precision"]["quote"] = 1e-7
        return market

    run_tomac._synthetic_market = patched


def run_strategy(strategy: str) -> dict:
    args = {
        "config": [str(AQ / "config.tomac.json")],
        "user_data_dir": str(AQ / "user_data"),
        "datadir": str(AQ / "user_data/data"),
        "strategy": strategy,
        "strategy_path": str(AQ / "user_data/strategies_external"),
        "export": "none",
        "exportfilename": None,
        "cache": "none",
    }
    config = Configuration(args, RunMode.BACKTEST).get_config()
    exchange = run_tomac._build_exchange_with_synthetic_pairs(config)
    bt = Backtesting(config, exchange=exchange)

    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        bt.start()
    (COMMAND_OUTPUT / f"{strategy}_table.out").write_text(captured.getvalue())

    metrics = run_tomac.extract_metrics(bt.results, strategy)["aggregate"]
    raw_trades = bt.all_bt_content.get(strategy, {}).get("results")
    trade_csv = TRADE_EXPORTS / f"{strategy}_trades.csv"
    if isinstance(raw_trades, pd.DataFrame):
        raw_trades.to_csv(trade_csv, index=False)
        trade_rows = len(raw_trades)
    else:
        trade_csv.write_text("")
        trade_rows = 0

    return {
        "strategy": strategy,
        "trade_csv": str(trade_csv.relative_to(REPO)),
        "trade_rows": trade_rows,
        "trade_count": metrics["trade_count"],
        "total_profit_pct": metrics["total_profit_pct"],
        "win_rate_pct": metrics["win_rate_pct"],
        "sharpe": metrics["sharpe"],
        "profit_factor": metrics["profit_factor"],
        "max_drawdown_pct": metrics["max_drawdown_pct"],
    }


def main() -> int:
    patch_synthetic_precision()
    strategies = ["TomacAggressiveBE", "TomacKillzoneBreakout", "TomacRRWinRate"]
    results = [run_strategy(strategy) for strategy in strategies]
    metrics_csv = RUN_ROOT / "precision-fix-tomac-rerun-v1/strategy_metrics_v1.csv"
    pd.DataFrame(results).to_csv(metrics_csv, index=False)
    total_trades = sum(row["trade_count"] for row in results)
    best = max(results, key=lambda row: row["total_profit_pct"])
    payload = {
        "artifact": "124408_precision_fix_tomac_rerun_v1",
        "source_run": str(SOURCE_RUN.relative_to(REPO)),
        "diagnostic_parent": "docs/experiments/actionable-regime-confidence/runs/20260512T125232+0800-codex-124408-signal-export-diagnostic-v1",
        "patch_scope": "in_memory_wrapper_only_synthetic_market_precision_amount_1e-8",
        "data_scope": {
            "pair": "BTC/USD",
            "timeframe": "1h",
            "timerange": "20260401-20260512",
            "informative_timeframe": "4h",
        },
        "results": results,
        "strategy_metrics_csv": str(metrics_csv.relative_to(REPO)),
        "total_trades": total_trades,
        "best_strategy": best["strategy"],
        "candidate_package_available": total_trades > 0,
        "board_effect": {
            "measured_candidate": total_trades > 0,
            "accepted_regime_gate": False,
            "pre_bayes_bbn_catboost_execution_ready": False,
            "production_likelihood_mutation": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "next": "Use TomacAggressiveBE trade rows as a BTC-only measured candidate for Pre-Bayes/filter, BBN, CatBoost/path-ranker, and execution-tree validation; do not promote without cross-context and >=95% calibrated regime evidence.",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
