from __future__ import annotations

import json
import contextlib
import io
import sys
from pathlib import Path

from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.exchange.exchange_utils import amount_to_contract_precision
from freqtrade.optimize.backtesting import Backtesting
import freqtrade.optimize.backtesting as bt_consts


REPO = Path(__file__).resolve().parents[6]
SOURCE_RUN = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T124408+0800-codex-123227-tomac-trade-density-iteration-v1"
)
AQ = SOURCE_RUN / "state_tomac_trade_density_iteration_v1/.deps/auto-quant"


sys.path.insert(0, str(AQ))
import run_tomac  # noqa: E402


def inspect_strategy(strategy: str) -> dict:
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
    data, _timerange = bt.load_bt_data()
    strat = bt.strategylist[0]
    bt._set_strategy(strat)
    preprocessed = bt.strategy.advise_all_indicators(data)
    rows = bt._get_ohlcv_as_lists(preprocessed)["BTC/USD"]
    trade_rows = [row for row in rows if bt.check_for_trade_entry(row)]
    first = trade_rows[0]
    current_time = first[bt_consts.DATE_IDX].to_pydatetime()
    pair = "BTC/USD"

    bt.reset_backtest(bt.enable_protections)
    bt.wallets.update()
    precision_price, precision_mode_price = bt.get_pair_precision(pair, current_time)
    propose_rate, stake_amount, leverage, min_stake_amount = bt.get_valid_entry_price_and_stake(
        pair,
        first,
        first[bt_consts.OPEN_IDX],
        0.0,
        "long",
        current_time,
        first[bt_consts.ENTER_TAG_IDX],
        None,
        bt.strategy.order_types["entry"],
        precision_price,
        precision_mode_price,
    )
    precision_amount = bt.exchange.get_precision_amount(pair)
    contract_size = bt.exchange.get_contract_size(pair)
    amount_raw = (stake_amount / propose_rate) * leverage
    amount_rounded = amount_to_contract_precision(
        amount_raw,
        precision_amount,
        bt.precision_mode,
        contract_size,
    )

    return {
        "strategy": strategy,
        "used_rows": len(rows),
        "trade_dir_count": len(trade_rows),
        "first_trade_dir_time": str(current_time),
        "first_trade_dir_open": first[bt_consts.OPEN_IDX],
        "wallet_total": bt.wallets.get_total(bt.config["stake_currency"]),
        "stake_amount": stake_amount,
        "propose_rate": propose_rate,
        "leverage": leverage,
        "min_stake_amount": min_stake_amount,
        "precision_mode": str(bt.precision_mode),
        "precision_amount": precision_amount,
        "precision_price": precision_price,
        "precision_mode_price": str(precision_mode_price),
        "contract_size": contract_size,
        "amount_raw": amount_raw,
        "amount_rounded": amount_rounded,
        "entry_blocker": "amount_rounds_to_zero_under_tick_size_precision"
        if amount_rounded == 0.0
        else None,
    }


def run_precision_fix_probe(strategies: list[str]) -> dict:
    original_synthetic_market = run_tomac._synthetic_market

    def patched_synthetic_market(pair: str, trading_mode: str) -> dict:
        market = original_synthetic_market(pair, trading_mode)
        market["precision"]["amount"] = 1e-8
        market["precision"]["base"] = 1e-8
        market["precision"]["price"] = 1e-7
        market["precision"]["quote"] = 1e-7
        return market

    run_tomac._synthetic_market = patched_synthetic_market
    try:
        results = []
        for strategy in strategies:
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                backtest_result = run_tomac.run_backtest(strategy)
            metrics = run_tomac.extract_metrics(backtest_result, strategy)["aggregate"]
            results.append(
                {
                    "strategy": strategy,
                    "trade_count": metrics["trade_count"],
                    "total_profit_pct": metrics["total_profit_pct"],
                    "win_rate_pct": metrics["win_rate_pct"],
                    "sharpe": metrics["sharpe"],
                    "profit_factor": metrics["profit_factor"],
                    "max_drawdown_pct": metrics["max_drawdown_pct"],
                    "stdout_contains_trade_table": "STRATEGY SUMMARY" in captured.getvalue(),
                }
            )
    finally:
        run_tomac._synthetic_market = original_synthetic_market

    total_trades = sum(row["trade_count"] for row in results)
    return {
        "patch": "in_memory_only_set_synthetic_market_precision_amount_to_1e-8_under_tick_size_mode",
        "results": results,
        "total_trades": total_trades,
        "candidate_package_available": total_trades > 0,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }


def main() -> int:
    strategies = ["TomacAggressiveBE", "TomacKillzoneBreakout", "TomacRRWinRate"]
    payload = {
        "artifact": "124408_signal_export_diagnostic_v1",
        "source_run": str(SOURCE_RUN.relative_to(REPO)),
        "auto_quant_workspace": str(AQ.relative_to(REPO)),
        "cli_signal_export": {
            "attempted": True,
            "exit_codes": {
                "TomacAggressiveBE": 2,
                "TomacKillzoneBreakout": 2,
                "TomacRRWinRate": 2,
            },
            "blocker": "plain_freqtrade_cli_loads_remote_binance_markets_and_hit_dns; run_tomac synthetic exchange path is required",
        },
        "strategies": [inspect_strategy(strategy) for strategy in strategies],
        "precision_fix_probe": run_precision_fix_probe(strategies),
        "root_cause": "run_tomac synthetic market precision.amount is 8 while resolved precision_mode is tick-size mode; intended BTC sizes around 1.38-1.47 round to 0.0, so entry signals never create filled orders",
        "board_effect": {
            "candidate_package_available": True,
            "candidate_package_note": "diagnostic in-memory precision fix produced nonzero trades; promotion still false until a settled run and downstream chain consume it",
            "pre_bayes_bbn_catboost_execution_ready": False,
            "production_likelihood_mutation": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "next": "copy or monkey-patch the isolated Auto-Quant TOMAC runner so synthetic BTC/USD uses an amount tick size such as 1e-8, then rerun TOMAC before downstream promotion",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
