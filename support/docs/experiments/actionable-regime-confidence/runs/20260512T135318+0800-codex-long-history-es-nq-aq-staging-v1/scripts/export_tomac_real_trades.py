from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_TOMAC = RUN_ROOT / "workspace" / "auto-quant" / "run_tomac.py"
STRATEGY = "TomacNQ_KillzoneBreakout"
RUN_ID = "20260512T135318-long-history-es-nq-tomac"
BRANCH_PATH = (
    "TrendExpansion -> LongHistoryTomacBreakout -> "
    "KillzoneContinuation -> TomacNQ_KillzoneBreakout"
)


def load_run_tomac():
    spec = importlib.util.spec_from_file_location("isolated_run_tomac", RUN_TOMAC)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {RUN_TOMAC}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def json_default(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def dt_ms(trade: dict[str, Any], *keys: str) -> int:
    for key in keys:
        if key not in trade or trade[key] is None:
            continue
        value = trade[key]
        if isinstance(value, (int, float)):
            # Freqtrade timestamp fields are milliseconds in current builds.
            return int(value)
        ts = pd.to_datetime(value, utc=True, errors="raise")
        return int(ts.value // 1_000_000)
    raise KeyError(f"missing timestamp keys {keys}; available={sorted(trade)}")


def float_field(trade: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        if key in trade and trade[key] is not None:
            return float(trade[key])
    return default


def trade_pair(trade: dict[str, Any]) -> str:
    pair = str(trade.get("pair") or trade.get("symbol") or "")
    if not pair:
        raise KeyError(f"missing pair in trade keys={sorted(trade)}")
    return pair


def to_real_trade(index: int, trade: dict[str, Any]) -> dict[str, Any]:
    pair = trade_pair(trade)
    symbol = pair.split("/", 1)[0]
    pnl = float_field(trade, "profit_abs", "profit_abs_profit", "profit_ratio")
    ratio = float_field(trade, "profit_ratio", "profit_pct", default=pnl)
    if ratio > 0:
        outcome = "win"
    elif ratio < 0:
        outcome = "loss"
    else:
        outcome = "draw"
    suffix = f"{symbol.lower()}-{index:05d}"
    return {
        "schema_version": "1.0",
        "symbol": symbol,
        "trade_id": f"{RUN_ID}-{suffix}",
        "strategy_name": STRATEGY,
        "strategy_mutation_id": "long-history-es-nq-killzone-breakout-v1",
        "auto_quant_run_id": RUN_ID,
        "open_ts_ms": dt_ms(trade, "open_timestamp", "open_date", "open_date_utc"),
        "close_ts_ms": dt_ms(trade, "close_timestamp", "close_date", "close_date_utc"),
        "direction": "Bear" if trade.get("is_short") else "Bull",
        "pnl": pnl,
        "realized_outcome": outcome,
        "regime_at_entry": "TrendExpansion",
        "entry_signal": "tomac_long_history_killzone_breakout",
        "regime_profit_branch_path": BRANCH_PATH,
        "main_regime": "TrendExpansion",
        "sub_regime": "LongHistoryTomacBreakout",
        "sub_sub_regime_or_profit_factor": "KillzoneContinuation",
        "profit_factor": STRATEGY,
        "factors_used": [
            {
                "factor_name": "long_history_tomac_killzone_breakout",
                "category": "trend_momentum",
                "direction": "Bull",
                "value": ratio,
                "confidence": 0.5,
                "weighted_score": ratio,
                "uncertainty_contribution": 0.5,
            }
        ],
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, default=json_default) + "\n" for row in rows))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_tomac = load_run_tomac()
    results = run_tomac.run_backtest(STRATEGY)
    strategy = results.get("strategy", {}).get(STRATEGY, {}) or {}
    trades = list(strategy.get("trades", []) or [])
    records = [to_real_trade(i + 1, trade) for i, trade in enumerate(trades)]

    raw_path = out_dir / "tomac_raw_trades.json"
    raw_path.write_text(json.dumps(trades, indent=2, default=json_default) + "\n")
    all_path = out_dir / "tomac_real_trades_all.jsonl"
    write_jsonl(all_path, records)

    split_paths = {}
    for symbol in sorted({row["symbol"] for row in records}):
        split = [row for row in records if row["symbol"] == symbol]
        path = out_dir / f"tomac_real_trades_{symbol.lower()}.jsonl"
        write_jsonl(path, split)
        split_paths[symbol] = str(path)

    metrics = run_tomac.extract_metrics(results, STRATEGY)
    summary = {
        "protocol": "tomac-real-trade-export-v1",
        "strategy": STRATEGY,
        "run_id": RUN_ID,
        "records": len(records),
        "raw_trades_path": str(raw_path),
        "all_trades_path": str(all_path),
        "split_paths": split_paths,
        "aggregate_metrics": metrics["aggregate"],
        "per_pair_metrics": metrics["per_pair"],
        "backtest_start": strategy.get("backtest_start"),
        "backtest_end": strategy.get("backtest_end"),
    }
    (out_dir / "tomac_real_trades_summary.json").write_text(
        json.dumps(summary, indent=2, default=json_default) + "\n"
    )
    print(json.dumps(summary, indent=2, default=json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
