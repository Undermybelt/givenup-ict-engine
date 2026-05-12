from __future__ import annotations

import json
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any

from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting
from freqtrade.resolvers import ExchangeResolver


PROJECT_DIR = Path(__file__).parent.resolve()
USER_DATA = PROJECT_DIR / "user_data"
STRATEGIES_DIR = USER_DATA / "strategies_external"
DATA_DIR = USER_DATA / "data"
CONFIG = PROJECT_DIR / "config.tomac.json"


def synthetic_market(pair: str, trading_mode: str) -> dict[str, Any]:
    base, quote = pair.split("/", 1)
    is_futures = trading_mode == "futures"
    return {
        "id": pair.replace("/", ""),
        "symbol": pair,
        "base": base,
        "quote": quote,
        "active": True,
        "type": "swap" if is_futures else "spot",
        "spot": not is_futures,
        "margin": is_futures,
        "swap": is_futures,
        "future": False,
        "option": False,
        "contract": is_futures,
        "linear": True if is_futures else None,
        "inverse": False if is_futures else None,
        "settle": quote if is_futures else None,
        "settleId": quote if is_futures else None,
        "expiry": None,
        "expiryDatetime": None,
        "strike": None,
        "optionType": None,
        "taker": 0.0,
        "maker": 0.0,
        "percentage": True,
        "tierBased": False,
        "feeSide": "get",
        "precision": {"amount": 8, "price": 8, "base": 8, "quote": 8},
        "limits": {
            "amount": {"min": 0, "max": None},
            "price": {"min": 0, "max": None},
            "cost": {"min": 0, "max": None},
            "leverage": {"min": 1, "max": 20 if is_futures else 1},
        },
        "info": {},
    }


def build_exchange_with_synthetic_pairs(config: dict[str, Any]):
    exchange = ExchangeResolver.load_exchange(config, validate=False, load_leverage_tiers=False)
    trading_mode = config.get("trading_mode", "spot")
    if exchange._api.markets is None:
        exchange._api.markets = {}
    if exchange._api_async.markets is None:
        exchange._api_async.markets = {}
    for pair in config["exchange"].get("pair_whitelist", []):
        market = synthetic_market(pair, trading_mode)
        exchange._markets[pair] = market
        exchange._api.markets[pair] = market
        exchange._api_async.markets[pair] = market
    return exchange


def get_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd="/Users/thrill3r/Auto-Quant",
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def discover_strategies() -> list[str]:
    if not STRATEGIES_DIR.exists():
        return []
    return sorted(path.stem for path in STRATEGIES_DIR.glob("*.py") if not path.stem.startswith("_"))


def number(entry: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        if key in entry and entry[key] is not None:
            try:
                return float(entry[key])
            except (TypeError, ValueError):
                pass
    return default


def entry_metrics(entry: dict[str, Any]) -> dict[str, float]:
    return {
        "sharpe": number(entry, "sharpe", "sharpe_ratio"),
        "sortino": number(entry, "sortino", "sortino_ratio"),
        "calmar": number(entry, "calmar", "calmar_ratio"),
        "total_profit_pct": number(entry, "profit_total_pct"),
        "max_drawdown_pct": -abs(number(entry, "max_drawdown_account")) * 100,
        "trade_count": int(number(entry, "trades", "total_trades")),
        "win_rate_pct": number(entry, "winrate") * 100,
        "profit_factor": number(entry, "profit_factor"),
    }


def run_backtest(strategy_name: str) -> dict[str, Any]:
    args = {
        "config": [str(CONFIG)],
        "user_data_dir": str(USER_DATA),
        "datadir": str(DATA_DIR),
        "strategy": strategy_name,
        "strategy_path": str(STRATEGIES_DIR),
        "export": "none",
        "exportfilename": None,
        "cache": "none",
    }
    config = Configuration(args, RunMode.BACKTEST).get_config()
    exchange = build_exchange_with_synthetic_pairs(config)
    bt = Backtesting(config, exchange=exchange)
    bt.start()
    return bt.results


def extract_metrics(results: dict[str, Any], strategy_name: str) -> dict[str, Any]:
    strat = results.get("strategy", {}).get(strategy_name, {}) or {}
    per_pair_list = strat.get("results_per_pair", []) or []
    aggregate: dict[str, float] = {}
    per_pair: dict[str, dict[str, float]] = {}
    for entry in per_pair_list:
        key = entry.get("key", "")
        metrics = entry_metrics(entry)
        if key == "TOTAL":
            aggregate = metrics
        elif key:
            per_pair[key] = metrics
    if not aggregate:
        aggregate = entry_metrics(strat)
    return {"aggregate": aggregate, "per_pair": per_pair}


def emit_block(strategy_name: str, commit: str, config_pairs: list[str], metrics: dict[str, Any]) -> None:
    agg = metrics["aggregate"]
    print("---")
    print(f"strategy:         {strategy_name}")
    print(f"commit:           {commit}")
    print(f"config:           {CONFIG.name}")
    print(f"pairs:            {','.join(config_pairs)}")
    print(f"sharpe:           {agg['sharpe']:.4f}")
    print(f"sortino:          {agg['sortino']:.4f}")
    print(f"calmar:           {agg['calmar']:.4f}")
    print(f"total_profit_pct: {agg['total_profit_pct']:.4f}")
    print(f"max_drawdown_pct: {agg['max_drawdown_pct']:.4f}")
    print(f"trade_count:      {agg['trade_count']}")
    print(f"win_rate_pct:     {agg['win_rate_pct']:.4f}")
    print(f"profit_factor:    {agg['profit_factor']:.4f}")
    if metrics["per_pair"]:
        print("per_pair:")
        for pair, pair_metrics in metrics["per_pair"].items():
            print(
                f"  {pair}: sharpe={pair_metrics['sharpe']:.4f} "
                f"trades={pair_metrics['trade_count']} "
                f"profit_pct={pair_metrics['total_profit_pct']:.2f} "
                f"dd_pct={pair_metrics['max_drawdown_pct']:.2f} "
                f"wr={pair_metrics['win_rate_pct']:.1f} "
                f"pf={pair_metrics['profit_factor']:.2f}"
            )
    print()


def main() -> int:
    config_pairs = json.loads(CONFIG.read_text(encoding="utf-8"))["exchange"]["pair_whitelist"]
    commit = get_commit()
    strategies = discover_strategies()
    if not strategies:
        print(f"ERROR: no strategies discovered in {STRATEGIES_DIR}", file=sys.stderr)
        return 2
    succeeded = failed = 0
    for strategy_name in strategies:
        try:
            results = run_backtest(strategy_name)
            emit_block(strategy_name, commit, config_pairs, extract_metrics(results, strategy_name))
            succeeded += 1
        except Exception as exc:
            failed += 1
            print("---")
            print(f"strategy:         {strategy_name}")
            print(f"commit:           {commit}")
            print("status:           ERROR")
            print(f"error_type:       {type(exc).__name__}")
            print(f"error_msg:        {exc}")
            print("traceback:")
            traceback.print_exc()
            print()
    print(f"Done: {succeeded} succeeded, {failed} failed.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
