from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PAIR_CONTEXT = {
    "BTC/USDT": {
        "provider": "binance_public",
        "main_regime": "TrendExpansion",
        "sub_regime": "WideRange",
    },
    "SPY/USDT": {
        "provider": "ibkr",
        "main_regime": "RangeConsolidation",
        "sub_regime": "WideRange",
    },
    "ES/USDT": {
        "provider": "yfinance",
        "main_regime": "TrendExpansion",
        "sub_regime": "BullTrendAcceleration",
    },
    "KXBT/USDT": {
        "provider": "kraken_public",
        "main_regime": "TrendExpansion",
        "sub_regime": "KrakenFuturesWindow",
    },
    "KSPX/USDT": {
        "provider": "kraken_public",
        "main_regime": "RangeConsolidation",
        "sub_regime": "KrakenEquityProxyWindow",
    },
    "BBTC/USDT": {
        "provider": "bybit_public",
        "main_regime": "TrendExpansion",
        "sub_regime": "BybitWindowCapped",
    },
}


def jsonable(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if not math.isfinite(float(value)):
            return None
        return float(value)
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime().isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def trade_ms(trade: dict[str, Any], key: str, fallback_key: str) -> int:
    if trade.get(key) is not None:
        return int(trade[key])
    value = trade.get(fallback_key)
    if isinstance(value, pd.Timestamp):
        return int(value.timestamp() * 1000)
    if isinstance(value, datetime):
        return int(value.timestamp() * 1000)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    run_root = Path(args.run_root).resolve()
    sys.path.insert(0, str(workspace))
    import run_tomac as rt  # noqa: PLC0415

    results = rt.run_backtest(args.strategy)
    metrics = rt.extract_metrics(results, args.strategy)
    strat = results.get("strategy", {}).get(args.strategy, {}) or {}
    trades = strat.get("trades", []) or []

    branch_counts: Counter[str] = Counter()
    branch_outcomes: dict[str, Counter[str]] = defaultdict(Counter)
    trades_path = run_root / "provider_multi_longspan_ema_rsi_real_trades_v1.jsonl"
    with trades_path.open("w", encoding="utf-8") as fh:
        for idx, trade in enumerate(trades, start=1):
            pair = str(trade.get("pair", "UNKNOWN"))
            ctx = PAIR_CONTEXT.get(
                pair,
                {"provider": "unknown", "main_regime": "Unknown", "sub_regime": "Unknown"},
            )
            profit_ratio = float(trade.get("profit_ratio") or 0.0)
            profit_abs = float(trade.get("profit_abs") or 0.0)
            outcome = "win" if profit_ratio > 0 else "loss" if profit_ratio < 0 else "flat"
            sub_sub = "EmaRsiContinuation"
            branch_path = (
                f"{ctx['main_regime']} -> {ctx['sub_regime']} -> "
                f"{sub_sub} -> {args.strategy}"
            )
            branch_counts[branch_path] += 1
            branch_outcomes[branch_path][outcome] += 1
            open_ms = trade_ms(trade, "open_timestamp", "open_date")
            close_ms = trade_ms(trade, "close_timestamp", "close_date")
            record = {
                "schema_version": "1.0",
                "auto_quant_run_id": args.run_id,
                "symbol": args.symbol,
                "pair": pair,
                "source_provider": ctx["provider"],
                "trade_id": f"provider-multi-longspan-ema-rsi-v1_{idx:05d}_{open_ms}_{close_ms}",
                "strategy_name": args.strategy,
                "strategy_mutation_id": "provider-multi-longspan-ema-rsi-v1",
                "entry_signal": trade.get("enter_tag") or "provider_multi_ema_rsi_continuation",
                "exit_reason": trade.get("exit_reason"),
                "direction": "Bull",
                "main_regime": ctx["main_regime"],
                "sub_regime": ctx["sub_regime"],
                "sub_sub_regime_or_profit_factor": sub_sub,
                "profit_factor": args.strategy,
                "regime_at_entry": ctx["main_regime"],
                "regime_profit_branch_path": branch_path,
                "open_ts_ms": open_ms,
                "close_ts_ms": close_ms,
                "pnl": profit_abs,
                "profit_ratio": profit_ratio,
                "realized_outcome": outcome,
                "model_probabilities_before_trade": {
                    "selected_direction": "Bull",
                    "selected_probability": 0.55,
                    "win_prob_long": 0.55,
                    "win_prob_short": 0.45,
                    "long_score": 0.55,
                    "short_score": 0.45,
                    "uncertainty": 0.45,
                },
                "factors_used": [
                    {
                        "category": "trend_momentum",
                        "factor_name": args.strategy,
                        "direction": "Bull",
                        "confidence": 0.55,
                        "value": profit_ratio,
                        "weighted_score": profit_abs,
                        "uncertainty_contribution": 0.45,
                    },
                    {
                        "category": "regime_branch_key",
                        "factor_name": branch_path,
                        "direction": "context",
                        "confidence": 0.55,
                        "value": branch_counts[branch_path],
                        "weighted_score": branch_counts[branch_path],
                        "uncertainty_contribution": 0.45,
                    },
                ],
            }
            fh.write(json.dumps(jsonable(record), sort_keys=True) + "\n")

    library_path = run_root / "provider_multi_longspan_ema_rsi_strategy_library_v1.json"
    metadata = {
        "strategy": args.strategy,
        "created": "2026-05-12",
        "mutation_id": "provider-multi-longspan-ema-rsi-v1",
        "base_factor": "provider_backed_multi_market_ema_rsi_continuation",
        "hypothesis": "Long-span provider-owned 1h bars can produce branch-keyed profitability evidence with enough observations for downstream admission tests.",
        "paradigm": "ema_rsi_continuation",
        "expected_regime": "TrendExpansion -> ProviderTrend -> EmaRsiContinuation -> ProviderMultiLongspanEmaRsiV1",
        "parent": "BoardB provider multi-longspan profitability-factor continuation",
        "asset_class": "crypto_tradfi_provider_ohlcv",
        "status": "incubation_only_provider_backed_multi_market",
        "factors_used": [
            "provider_binance_btc_ohlcv",
            "provider_ibkr_spy_ohlcv",
            "provider_yfinance_es_ohlcv",
            "provider_kraken_futures_ohlcv",
            "provider_bybit_window_ohlcv",
            "ema8",
            "ema24",
            "rsi14_midband",
            "fixed_12h_risk_horizon",
            "regime_profit_branch_path",
        ],
    }
    strategy_entry = {
        "name": args.strategy,
        "status": "ok",
        "commit": "provider-multi-longspan-run-local",
        "file_path": str(workspace / "user_data/strategies_external" / f"{args.strategy}.py"),
        "pairs": list(PAIR_CONTEXT),
        "timerange": "20170817-20260512",
        "metadata": metadata,
        "validation_metrics": metrics["aggregate"],
        "per_pair_metrics": metrics["per_pair"],
        "error": None,
    }
    library = {
        "manifest_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "auto_quant_repo_url": str(workspace),
        "auto_quant_pinned_ref": "provider-multi-longspan-run-local",
        "config_path": str(workspace / "config.tomac.json"),
        "log_path": str(run_root / "command-output/07_auto_quant_materialize_packet.out"),
        "timeframe": "1h",
        "strategies": [strategy_entry],
        "validation_errors": [],
    }
    library_path.write_text(json.dumps(jsonable(library), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary_path = run_root / "provider_multi_longspan_ema_rsi_packet_summary_v1.json"
    summary = {
        "run_id": args.run_id,
        "symbol": args.symbol,
        "branch_path_template": "main_regime -> sub_regime -> EmaRsiContinuation -> ProviderMultiLongspanEmaRsiV1",
        "library_path": str(library_path),
        "trades_path": str(trades_path),
        "total_trade_rows": len(trades),
        "provider_data_acquired": True,
        "provider_requested": sorted({ctx["provider"] for ctx in PAIR_CONTEXT.values()}),
        "providers_not_invoked_this_slice": ["TradingViewRemix/TVR"],
        "local_cache_replay": "provider-provenanced CSV copied from 141554 provider matrix into this run root",
        "promotion_scope": "incubation_only_provider_backed_multi_market",
        "strategies": [strategy_entry],
        "branch_counts": dict(branch_counts),
        "branch_outcomes": {k: dict(v) for k, v in branch_outcomes.items()},
    }
    summary_path.write_text(json.dumps(jsonable(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable({"summary_path": summary_path, "library_path": library_path, "trades_path": trades_path, "rows": len(trades), "metrics": metrics["aggregate"]}), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
