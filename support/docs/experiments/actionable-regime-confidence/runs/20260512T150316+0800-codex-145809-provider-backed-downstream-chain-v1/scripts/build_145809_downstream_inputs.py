#!/usr/bin/env python3
"""Build ict-engine downstream inputs from the 145809 provider-backed screen."""

from __future__ import annotations

import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T150316+0800-codex-145809-provider-backed-downstream-chain-v1"
)
SOURCE_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T145809+0800-codex-provider-backed-high-density-factor-screen-v1"
)
SOURCE_TRADES = SOURCE_ROOT / "summaries/provider_backed_high_density_factor_trades.csv"
SOURCE_SUMMARY = SOURCE_ROOT / "summaries/provider_backed_high_density_factor_summary.csv"
SOURCE_MANIFEST = SOURCE_ROOT / "summaries/provider_backed_high_density_factor_manifest.json"


def parse_ts_ms(value: str) -> int:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def safe_float(value: str, default: float = 0.0) -> float:
    try:
        val = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(val):
        return default
    return val


def load_summary_rows() -> dict[str, dict[str, str]]:
    by_strategy: dict[str, dict[str, str]] = {}
    with SOURCE_SUMMARY.open(newline="") as fh:
        for row in csv.DictReader(fh):
            if row["provider"] == "ALL" and row["symbol"] == "ALL" and row["branch_path"] == "ALL":
                by_strategy[row["strategy"]] = row
    return by_strategy


def build_manifest() -> dict:
    source_manifest = json.loads(SOURCE_MANIFEST.read_text())
    summaries = load_summary_rows()
    strategies = []
    for strategy_name, row in sorted(summaries.items()):
        trades = int(row["trades"])
        win_rate = safe_float(row["win_rate"]) * 100.0
        total_return = safe_float(row["total_return_units"])
        avg_return = safe_float(row["avg_return"])
        profit_factor = safe_float(row["profit_factor"])
        strategies.append(
            {
                "name": strategy_name,
                "file_path": str(SOURCE_TRADES),
                "metadata": {
                    "strategy": strategy_name,
                    "mutation_id": f"145809_provider_backed_{strategy_name}",
                    "base_factor": strategy_name,
                    "hypothesis": (
                        "Provider-backed high-density branch-keyed factor screen "
                        "from Binance BTCUSDT, IBKR SPY, and Yahoo ES 1h data."
                    ),
                    "paradigm": "provider_backed_branch_factor_screen",
                    "expected_regime": "mixed_branch_keyed",
                    "factors_used": [strategy_name],
                    "parent": "provider_backed_high_density_factor_screen_v1",
                    "asset_class": "multi_asset_provider_backed",
                    "status": "support_only_provider_backed_screen_not_auto_quant_backtest",
                },
                "status": "ok",
                "validation_metrics": {
                    "sharpe": 0.0,
                    "sortino": 0.0,
                    "calmar": 0.0,
                    "total_profit_pct": total_return * 100.0,
                    "max_drawdown_pct": 0.0,
                    "trade_count": trades,
                    "win_rate_pct": win_rate,
                    "profit_factor": profit_factor,
                    "avg_return": avg_return,
                },
                "per_pair_metrics": {
                    "PROVIDER_BACKED/ALL": {
                        "trade_count": trades,
                        "win_rate_pct": win_rate,
                        "profit_factor": profit_factor,
                        "total_profit_pct": total_return * 100.0,
                    }
                },
                "pairs": ["PROVIDER_BACKED/ALL"],
                "timerange": "2017-08-17 -> 2026-05-12",
                "commit": "provider-backed-screen-145809",
            }
        )

    return {
        "manifest_version": "1.0",
        "exported_at": "2026-05-12T15:03:16+08:00",
        "auto_quant_repo_url": (
            "provider-backed high-density screen derived from settled 145809 artifacts; "
            "not an Auto-Quant backtest"
        ),
        "auto_quant_pinned_ref": "screen-145809",
        "config_path": str(SOURCE_MANIFEST),
        "timeframe": "1h_provider_backed",
        "log_path": str(SOURCE_ROOT / "checks/provider_backed_high_density_factor_screen_v1_assertions.out"),
        "validation_errors": [
            "not_auto_quant_backtest",
            "missing_required_provider_acquisition_rows_for_tvr_kraken_bybit",
        ],
        "source_manifest": source_manifest,
        "strategies": strategies,
    }


def build_real_trades() -> tuple[int, dict[str, int]]:
    out_path = ROOT / "derived/provider_backed_high_density_real_trades.jsonl"
    counts: dict[str, int] = {}
    total = 0
    with SOURCE_TRADES.open(newline="") as src, out_path.open("w") as out:
        for idx, row in enumerate(csv.DictReader(src), start=1):
            ret = safe_float(row["return"])
            strategy = row["strategy"]
            counts[strategy] = counts.get(strategy, 0) + 1
            total += 1
            direction = "Bull" if row["direction"].lower() == "long" else "Bear"
            branch_path = row["branch_path"]
            record = {
                "schema_version": "1.0",
                "symbol": row["symbol"],
                "provider": row["provider"],
                "trade_id": f"145809-provider-backed-{idx:06d}",
                "strategy_name": strategy,
                "strategy_mutation_id": f"145809_provider_backed_{strategy}",
                "auto_quant_run_id": "20260512T145809-provider-backed-high-density-factor-screen-v1",
                "open_ts_ms": parse_ts_ms(row["entry_time"]),
                "close_ts_ms": parse_ts_ms(row["exit_time"]),
                "direction": direction,
                "pnl": ret,
                "realized_outcome": "win" if ret > 0.0 else "loss",
                "regime_at_entry": row["main_regime"],
                "entry_signal": strategy,
                "regime_profit_branch_path": branch_path,
                "main_regime": row["main_regime"],
                "sub_regime": row["sub_regime"],
                "sub_sub_regime_or_profit_factor": row["sub_sub_regime_or_profit_factor"],
                "profit_factor": row["profit_factor"],
                "factors_used": [
                    {
                        "factor_name": strategy,
                        "category": "provider_backed_profitability_screen",
                        "direction": direction,
                        "value": ret,
                        "confidence": 0.5,
                        "weighted_score": ret,
                        "uncertainty_contribution": 0.5,
                    }
                ],
            }
            out.write(json.dumps(record, separators=(",", ":")) + "\n")
    return total, counts


def write_provider_provenance() -> None:
    rows = [
        ["IBKR", True, True, True, False, False, "143900", "SPY 1h 5Y provider-backed rows consumed by 145809"],
        ["TradingViewRemix/TVR", False, False, False, True, False, "141554", "TVR QQQ 1h fetch failed; no 145809 trades"],
        ["yfinance/YF", True, True, True, False, False, "143900", "Yahoo ES 1h provider-backed rows consumed by 145809"],
        ["Kraken", False, False, False, False, False, "141554", "Windowed rows existed in 141554 but were not consumed by 145809"],
        ["Binance", True, True, True, False, False, "143900", "BTCUSDT 1h full-listing provider-backed rows consumed by 145809"],
        ["Bybit", False, False, False, False, False, "141554", "Capped rows existed in 141554 but were not consumed by 145809"],
    ]
    path = ROOT / "derived/aq_provider_provenance_145809_downstream.csv"
    with path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "provider",
                "aq_provider_invoked",
                "provider_requested",
                "provider_data_acquired",
                "provider_unreachable",
                "local_cache_replay",
                "context_source",
                "note",
            ]
        )
        writer.writerows(rows)


def main() -> int:
    ROOT.joinpath("derived").mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    manifest_path = ROOT / "derived/strategy_library_145809_provider_backed_v1.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    total, counts = build_real_trades()
    write_provider_provenance()
    summary = {
        "protocol": "145809-provider-backed-downstream-inputs-v1",
        "source_root": str(SOURCE_ROOT),
        "manifest_path": str(manifest_path),
        "real_trades_path": str(ROOT / "derived/provider_backed_high_density_real_trades.jsonl"),
        "provider_provenance_path": str(ROOT / "derived/aq_provider_provenance_145809_downstream.csv"),
        "trade_count_total": total,
        "trade_count_by_strategy": counts,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    (ROOT / "derived/input_build_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
