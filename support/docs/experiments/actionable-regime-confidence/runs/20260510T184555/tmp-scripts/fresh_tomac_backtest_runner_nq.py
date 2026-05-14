from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any

from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting
from freqtrade.resolvers import ExchangeResolver

PROJECT_DIR = Path("/Users/thrill3r/Auto-Quant")
USER_DATA = PROJECT_DIR / "user_data"
DEFAULT_STRATEGIES_DIR = USER_DATA / "strategies_external"
DATA_DIR = USER_DATA / "data"
CONFIG = PROJECT_DIR / "config.tomac.json"
SCRATCH_USER_DATA = Path("/tmp/ict-board-a-v2-2-codex-20260510T184555/autoquant-fresh-user-data")
SCRATCH_CONFIG = Path(
    "/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260510T184555/autoquant/config.tomac.nq-15m.json"
)


def synthetic_market(pair: str) -> dict[str, Any]:
    base, quote = pair.split("/", 1)
    return {
        "id": pair.replace("/", ""),
        "symbol": pair,
        "base": base,
        "quote": quote,
        "active": True,
        "type": "spot",
        "spot": True,
        "margin": False,
        "swap": False,
        "future": False,
        "option": False,
        "contract": False,
        "linear": None,
        "inverse": None,
        "settle": None,
        "settleId": None,
        "expiry": None,
        "expiryDatetime": None,
        "strike": None,
        "optionType": None,
        "taker": 0.0,
        "maker": 0.0,
        "percentage": True,
        "tierBased": False,
        "feeSide": "get",
        "precision": {"amount": 1e-8, "price": 0.01, "base": 1e-8, "quote": 0.01},
        "limits": {
            "amount": {"min": 0, "max": None},
            "price": {"min": 0, "max": None},
            "cost": {"min": 0, "max": None},
            "leverage": {"min": 1, "max": 1},
        },
        "info": {},
    }


def build_exchange(config: dict[str, Any]):
    exchange = ExchangeResolver.load_exchange(config, load_leverage_tiers=False)
    for pair in config["exchange"].get("pair_whitelist", []):
        if pair not in exchange._markets:
            exchange._markets[pair] = synthetic_market(pair)
    return exchange


def normalize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): normalize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize(v) for v in obj]
    if hasattr(obj, "total_seconds"):
        return obj.total_seconds()
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    try:
        import numpy as np

        if isinstance(obj, np.generic):
            return obj.item()
    except Exception:
        pass
    return obj


def discover(strategy_dir: Path) -> list[str]:
    return [p.stem for p in sorted(strategy_dir.glob("TomacNQ_*.py")) if not p.stem.startswith("_")]


def write_scratch_config() -> Path:
    return SCRATCH_CONFIG


def run_one(strategy_name: str, timerange: str, strategy_dir: Path) -> dict[str, Any]:
    args = {
        "config": [str(write_scratch_config())],
        "user_data_dir": str(SCRATCH_USER_DATA),
        "datadir": str(DATA_DIR),
        "strategy": strategy_name,
        "strategy_path": str(strategy_dir),
        "timerange": timerange,
        "export": "none",
        "exportfilename": None,
        "cache": "none",
    }
    config = Configuration(args, RunMode.BACKTEST).get_config()
    exchange = build_exchange(config)
    bt = Backtesting(config, exchange=exchange)
    bt.start()
    return bt.results


def strategy_payload(results: dict[str, Any], strategy_name: str, timerange: str) -> dict[str, Any]:
    strat = results.get("strategy", {}).get(strategy_name, {}) or {}
    trades = normalize(strat.get("trades") or [])
    open_dates = [str(t.get("open_date")) for t in trades if t.get("open_date")]
    summary = {
        "strategy": strategy_name,
        "timeframe": strat.get("timeframe", ""),
        "timerange": strat.get("timerange", timerange),
        "total_trades": int(strat.get("total_trades") or len(trades)),
        "wins": int(strat.get("wins") or 0),
        "losses": int(strat.get("losses") or 0),
        "winrate": float(strat.get("winrate") or 0.0),
        "profit_total": float(strat.get("profit_total") or 0.0),
        "profit_factor": float(strat.get("profit_factor") or 0.0),
        "first_open": min(open_dates) if open_dates else "",
        "last_open": max(open_dates) if open_dates else "",
    }
    return {"summary": summary, "trades": trades}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timerange", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--strategy-dir", default=str(DEFAULT_STRATEGIES_DIR))
    parser.add_argument("--strategies", nargs="*", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    SCRATCH_USER_DATA.mkdir(parents=True, exist_ok=True)
    (SCRATCH_USER_DATA / "backtest_results").mkdir(parents=True, exist_ok=True)
    strategy_dir = Path(args.strategy_dir)
    strategies = args.strategies or discover(strategy_dir)
    payload: dict[str, Any] = {
        "schema_version": "fresh-tomac-backtests/v1",
        "timerange": args.timerange,
        "scratch_user_data": str(SCRATCH_USER_DATA),
        "scratch_config": str(write_scratch_config()),
        "strategy_dir": str(strategy_dir),
        "data_dir": str(DATA_DIR),
        "results": {},
        "summaries": [],
        "errors": [],
    }
    for strategy in strategies:
        try:
            results = run_one(strategy, args.timerange, strategy_dir)
            compact = strategy_payload(results, strategy, args.timerange)
            payload["results"][strategy] = compact
            payload["summaries"].append(compact["summary"])
            print(json.dumps(payload["summaries"][-1], sort_keys=True))
        except Exception as exc:
            error = {
                "strategy": strategy,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(limit=12),
            }
            payload["errors"].append(error)
            print(json.dumps(error, sort_keys=True), file=sys.stderr)
    out = Path(args.out)
    out.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")
    print(json.dumps({"out": str(out), "strategies": len(strategies), "errors": len(payload["errors"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
