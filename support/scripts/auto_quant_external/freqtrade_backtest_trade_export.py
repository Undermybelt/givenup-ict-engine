from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any


def _load_backtest_payload(backtest_zip: Path) -> dict[str, Any]:
    with zipfile.ZipFile(backtest_zip) as archive:
        candidates = [
            name
            for name in archive.namelist()
            if name.endswith(".json") and "_config" not in name and "market_change" not in name
        ]
        if not candidates:
            raise ValueError(f"no backtest json found in {backtest_zip}")
        return json.loads(archive.read(candidates[0]))


def _branch_segments(branch_path: str) -> list[str]:
    return [part.strip() for part in branch_path.split(" -> ") if part.strip()]


def _realized_outcome(profit_abs: float) -> str:
    if profit_abs > 0.0:
        return "win"
    if profit_abs < 0.0:
        return "loss"
    return "breakeven"


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=False) + "\n")


def export_backtest_trades(
    *,
    backtest_zip: Path,
    strategy_name: str,
    output_jsonl: Path,
    strategy_mutation_id: str,
    auto_quant_run_id: str,
    symbol: str,
    provider: str,
    instrument: str,
    timeframe: str,
    branch_path: str,
) -> dict[str, Any]:
    payload = _load_backtest_payload(backtest_zip)
    strategy_block = payload.get("strategy", {}).get(strategy_name)
    if not isinstance(strategy_block, dict):
        raise ValueError(f"strategy {strategy_name!r} not found in {backtest_zip}")
    trades = strategy_block.get("trades", [])
    if not isinstance(trades, list):
        raise ValueError(f"strategy {strategy_name!r} missing trades list")

    parts = _branch_segments(branch_path)
    main_regime = parts[0] if len(parts) > 0 else ""
    sub_regime = parts[1] if len(parts) > 1 else ""
    sub_sub_regime = parts[2] if len(parts) > 2 else ""
    profit_factor = " -> ".join(parts[3:]) if len(parts) > 3 else ""

    rows: list[dict[str, Any]] = []
    wins = losses = breakevens = 0
    profit_abs_sum = 0.0

    for index, trade in enumerate(trades, start=1):
        profit_abs = float(trade.get("profit_abs", 0.0))
        realized_outcome = _realized_outcome(profit_abs)
        if realized_outcome == "win":
            wins += 1
        elif realized_outcome == "loss":
            losses += 1
        else:
            breakevens += 1
        profit_abs_sum += profit_abs

        rows.append(
            {
                "schema_version": "1.0",
                "symbol": symbol,
                "trade_id": f"{strategy_mutation_id}:{index}",
                "strategy_name": strategy_name,
                "strategy_mutation_id": strategy_mutation_id,
                "auto_quant_run_id": auto_quant_run_id,
                "open_ts_ms": int(trade["open_timestamp"]),
                "close_ts_ms": int(trade["close_timestamp"]),
                "direction": "Bear" if bool(trade.get("is_short", False)) else "Bull",
                "pnl": profit_abs,
                "realized_outcome": realized_outcome,
                "regime_at_entry": main_regime,
                "entry_signal": str(trade.get("enter_tag", "")),
                "exit_reason": str(trade.get("exit_reason", "")),
                "provider": provider,
                "instrument": instrument,
                "timeframe": timeframe,
                "pair": str(trade.get("pair", "")),
                "open_date": str(trade.get("open_date", "")),
                "close_date": str(trade.get("close_date", "")),
                "open_rate": float(trade.get("open_rate", 0.0)),
                "close_rate": float(trade.get("close_rate", 0.0)),
                "profit_ratio": float(trade.get("profit_ratio", 0.0)),
                "profit_abs": profit_abs,
                "min_rate": float(trade.get("min_rate", trade.get("open_rate", 0.0))),
                "max_rate": float(trade.get("max_rate", trade.get("close_rate", 0.0))),
                "stake_amount": float(trade.get("stake_amount", 0.0)),
                "amount": float(trade.get("amount", 0.0)),
                "leverage": float(trade.get("leverage", 1.0)),
                "trade_duration": int(trade.get("trade_duration", 0)),
                "regime_profit_branch_path": branch_path,
                "main_regime": main_regime,
                "sub_regime": sub_regime,
                "sub_sub_regime_or_profit_factor": sub_sub_regime,
                "profit_factor": profit_factor,
            }
        )

    _write_jsonl(output_jsonl, rows)
    return {
        "rows": len(rows),
        "wins": wins,
        "losses": losses,
        "breakevens": breakevens,
        "profit_abs_sum": profit_abs_sum,
        "output_jsonl": str(output_jsonl),
        "branch_path": branch_path,
        "provider": provider,
        "instrument": instrument,
        "timeframe": timeframe,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export normalized real trades from a Freqtrade backtest zip.")
    parser.add_argument("--backtest-zip", required=True)
    parser.add_argument("--strategy-name", required=True)
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--strategy-mutation-id", required=True)
    parser.add_argument("--auto-quant-run-id", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--instrument", required=True)
    parser.add_argument("--timeframe", required=True)
    parser.add_argument("--branch-path", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = export_backtest_trades(
        backtest_zip=Path(args.backtest_zip),
        strategy_name=args.strategy_name,
        output_jsonl=Path(args.output_jsonl),
        strategy_mutation_id=args.strategy_mutation_id,
        auto_quant_run_id=args.auto_quant_run_id,
        symbol=args.symbol,
        provider=args.provider,
        instrument=args.instrument,
        timeframe=args.timeframe,
        branch_path=args.branch_path,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
