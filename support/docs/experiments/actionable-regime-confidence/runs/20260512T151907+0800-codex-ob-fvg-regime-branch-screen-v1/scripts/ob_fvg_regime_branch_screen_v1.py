#!/usr/bin/env python3
"""Lightweight OB/FVG continuation-pullback screen for Board B.

This is an experiment artifact, not runtime code. It reads normalized provider
OHLCV CSVs, emits branch-keyed trade rows, provenance, and walk-forward
summaries for order-block and fair-value-gap pullback factors.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260512T151907+0800-codex-ob-fvg-regime-branch-screen-v1")
DATA_ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260512T150855+0800-codex-145809-aq-material-seed-dispatch-v1/data")


@dataclass(frozen=True)
class ProviderSpec:
    provider: str
    symbol: str
    path: Path | None


PROVIDERS = [
    ProviderSpec("Binance", "BTCUSDT", DATA_ROOT / "binance_btcusdt_1h_20170817_20260512.normalized.csv"),
    ProviderSpec("Bybit", "BTCUSDT", DATA_ROOT / "bybit_linear_btcusdt_1h_20200101_20260512.normalized.csv"),
    ProviderSpec("IBKR", "SPY", DATA_ROOT / "ibkr_spy_1h_5y.normalized.csv"),
    ProviderSpec("Kraken", "XBTUSD", DATA_ROOT / "kraken_futures_pfxbtusd_1h_20200101_20260512.normalized.csv"),
    ProviderSpec("yfinance/YF", "ES", DATA_ROOT / "yahoo_es_1h_20240513_20260512.normalized.csv"),
    ProviderSpec("TradingViewRemix/TVR", "missing", None),
]


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(newline="") as fh:
        for raw in csv.DictReader(fh):
            try:
                rows.append(
                    {
                        "timestamp": raw["timestamp"].strip(),
                        "dt": parse_dt(raw["timestamp"].strip()),
                        "open": float(raw["open"]),
                        "high": float(raw["high"]),
                        "low": float(raw["low"]),
                        "close": float(raw["close"]),
                        "volume": float(raw.get("volume") or 0.0),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    rows.sort(key=lambda r: r["dt"])
    return rows


def ema(values: list[float], span: int) -> list[float]:
    out: list[float] = []
    alpha = 2.0 / (span + 1.0)
    prev = values[0]
    for value in values:
        prev = alpha * value + (1.0 - alpha) * prev
        out.append(prev)
    return out


def rolling_atr(rows: list[dict], span: int = 14) -> list[float]:
    tr: list[float] = []
    for i, row in enumerate(rows):
        prev_close = rows[i - 1]["close"] if i else row["close"]
        tr.append(max(row["high"] - row["low"], abs(row["high"] - prev_close), abs(row["low"] - prev_close)))
    out: list[float] = []
    for i in range(len(tr)):
        window = tr[max(0, i - span + 1) : i + 1]
        out.append(sum(window) / len(window))
    return out


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[int(pos)]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def branch_for(rows: list[dict], i: int, atr_pct_hi: float, direction: str) -> tuple[str, str, str]:
    row = rows[i]
    ema_gap = abs(row["ema20"] - row["ema50"]) / row["close"] if row["close"] else 0.0
    main = "TrendExpansion" if ema_gap >= row["atr_pct"] * 0.45 else "TrendTransition"
    if row["atr_pct"] >= atr_pct_hi:
        sub = "HighVolatility"
    elif row["atr_pct"] <= atr_pct_hi * 0.45:
        sub = "LowVolatility"
    else:
        sub = "NormalVolatility"
    mom = "up_momentum" if direction == "long" else "down_momentum"
    return main, sub, mom


def simulate_exit(rows: list[dict], entry_i: int, side: str, entry: float, stop: float, horizon: int = 12) -> tuple[int, float, str]:
    risk = abs(entry - stop)
    if risk <= 0 or entry <= 0:
        return entry_i, entry, "invalid_risk"
    target = entry + 2.0 * risk if side == "long" else entry - 2.0 * risk
    end_i = min(len(rows) - 1, entry_i + horizon)
    for j in range(entry_i + 1, end_i + 1):
        row = rows[j]
        if side == "long":
            if row["low"] <= stop:
                return j, stop, "stop"
            if row["high"] >= target:
                return j, target, "target"
        else:
            if row["high"] >= stop:
                return j, stop, "stop"
            if row["low"] <= target:
                return j, target, "target"
    return end_i, rows[end_i]["close"], "horizon"


def add_trade(
    trades: list[dict],
    provider: ProviderSpec,
    rows: list[dict],
    signal_i: int,
    entry_i: int,
    factor: str,
    side: str,
    zone_low: float,
    zone_high: float,
    atr_pct_hi: float,
) -> None:
    entry = rows[entry_i]["close"]
    atr = rows[signal_i]["atr"]
    if side == "long":
        stop = zone_low - 0.10 * atr
    else:
        stop = zone_high + 0.10 * atr
    exit_i, exit_price, reason = simulate_exit(rows, entry_i, side, entry, stop)
    gross = (exit_price - entry) / entry if side == "long" else (entry - exit_price) / entry
    net = gross - 0.0008
    main, sub, sub_sub = branch_for(rows, signal_i, atr_pct_hi, side)
    branch = f"{main}->{sub}->{sub_sub}->{factor}"
    fold = "test"
    frac = entry_i / max(1, len(rows) - 1)
    if frac < 0.50:
        fold = "train"
    elif frac < 0.75:
        fold = "validation"
    trades.append(
        {
            "provider": provider.provider,
            "symbol": provider.symbol,
            "factor": factor,
            "side": side,
            "main_regime": main,
            "sub_regime": sub,
            "sub_sub_regime_or_profit_factor": sub_sub,
            "profit_factor": factor,
            "branch_path": branch,
            "signal_time": rows[signal_i]["timestamp"],
            "entry_time": rows[entry_i]["timestamp"],
            "exit_time": rows[exit_i]["timestamp"],
            "entry": f"{entry:.10g}",
            "exit": f"{exit_price:.10g}",
            "stop": f"{stop:.10g}",
            "zone_low": f"{zone_low:.10g}",
            "zone_high": f"{zone_high:.10g}",
            "exit_reason": reason,
            "gross_return": f"{gross:.10g}",
            "net_return": f"{net:.10g}",
            "walk_forward_fold": fold,
        }
    )


def scan_provider(provider: ProviderSpec) -> tuple[list[dict], dict]:
    assert provider.path is not None
    rows = load_rows(provider.path)
    if len(rows) < 80:
        return [], {"provider": provider.provider, "rows": len(rows), "signals": 0}
    closes = [r["close"] for r in rows]
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    atrs = rolling_atr(rows)
    atr_pcts = [a / r["close"] if r["close"] else 0.0 for a, r in zip(atrs, rows)]
    atr_hi = percentile(atr_pcts[50:], 0.75)
    for i, row in enumerate(rows):
        row["ema20"] = ema20[i]
        row["ema50"] = ema50[i]
        row["atr"] = atrs[i]
        row["atr_pct"] = atr_pcts[i]
    trades: list[dict] = []
    cooldown: dict[tuple[str, str], int] = {}
    lookahead = 24
    for i in range(55, len(rows) - lookahead - 13):
        row = rows[i]
        uptrend = row["ema20"] > row["ema50"] and row["close"] > row["ema20"]
        downtrend = row["ema20"] < row["ema50"] and row["close"] < row["ema20"]
        if uptrend and rows[i]["low"] > rows[i - 2]["high"] and rows[i]["close"] > rows[i]["open"]:
            gap_low, gap_high = rows[i - 2]["high"], rows[i]["low"]
            for j in range(i + 1, i + lookahead + 1):
                if rows[j]["low"] <= gap_high and rows[j]["close"] > gap_low and cooldown.get(("fvg_long", provider.provider), -99) < i:
                    add_trade(trades, provider, rows, i, j, "fair_value_gap_pullback_v1", "long", gap_low, gap_high, atr_hi)
                    cooldown[("fvg_long", provider.provider)] = i + 6
                    break
        if downtrend and rows[i]["high"] < rows[i - 2]["low"] and rows[i]["close"] < rows[i]["open"]:
            gap_low, gap_high = rows[i]["high"], rows[i - 2]["low"]
            for j in range(i + 1, i + lookahead + 1):
                if rows[j]["high"] >= gap_low and rows[j]["close"] < gap_high and cooldown.get(("fvg_short", provider.provider), -99) < i:
                    add_trade(trades, provider, rows, i, j, "fair_value_gap_pullback_v1", "short", gap_low, gap_high, atr_hi)
                    cooldown[("fvg_short", provider.provider)] = i + 6
                    break
        prev = rows[i - 1]
        breakout_hi = max(r["high"] for r in rows[i - 8 : i])
        breakout_lo = min(r["low"] for r in rows[i - 8 : i])
        impulse = abs(row["close"] - row["open"]) >= row["atr"] * 0.80
        if uptrend and prev["close"] < prev["open"] and row["close"] > breakout_hi and impulse:
            zone_low, zone_high = prev["low"], prev["high"]
            for j in range(i + 1, i + lookahead + 1):
                if rows[j]["low"] <= zone_high and rows[j]["close"] > zone_low and cooldown.get(("ob_long", provider.provider), -99) < i:
                    add_trade(trades, provider, rows, i, j, "order_block_pullback_v1", "long", zone_low, zone_high, atr_hi)
                    cooldown[("ob_long", provider.provider)] = i + 6
                    break
        if downtrend and prev["close"] > prev["open"] and row["close"] < breakout_lo and impulse:
            zone_low, zone_high = prev["low"], prev["high"]
            for j in range(i + 1, i + lookahead + 1):
                if rows[j]["high"] >= zone_low and rows[j]["close"] < zone_high and cooldown.get(("ob_short", provider.provider), -99) < i:
                    add_trade(trades, provider, rows, i, j, "order_block_pullback_v1", "short", zone_low, zone_high, atr_hi)
                    cooldown[("ob_short", provider.provider)] = i + 6
                    break
    return trades, {"provider": provider.provider, "rows": len(rows), "signals": len(trades), "first": rows[0]["timestamp"], "last": rows[-1]["timestamp"]}


def profit_factor(values: list[float]) -> float:
    wins = sum(v for v in values if v > 0)
    losses = -sum(v for v in values if v < 0)
    if losses == 0:
        return 999.0 if wins > 0 else 0.0
    return wins / losses


def max_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    worst = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        worst = min(worst, equity - peak)
    return worst


def summarize(trades: list[dict], keys: list[str]) -> list[dict]:
    groups: dict[tuple[str, ...], list[dict]] = {}
    for trade in trades:
        groups.setdefault(tuple(trade[k] for k in keys), []).append(trade)
    out: list[dict] = []
    for group_key, rows in sorted(groups.items()):
        vals = [float(r["net_return"]) for r in rows]
        out.append(
            {
                **dict(zip(keys, group_key)),
                "trades": len(rows),
                "win_rate": f"{sum(1 for v in vals if v > 0) / len(vals):.6f}",
                "mean_net_return": f"{statistics.fmean(vals):.10g}",
                "profit_factor": f"{profit_factor(vals):.6f}",
                "max_drawdown_sum_return": f"{max_drawdown(vals):.10g}",
                "folds_present": ",".join(sorted({r["walk_forward_fold"] for r in rows})),
            }
        )
    return out


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    all_trades: list[dict] = []
    provider_stats: list[dict] = []
    provenance: list[dict] = []
    for provider in PROVIDERS:
        acquired = provider.path is not None and provider.path.exists()
        row_count = 0
        if acquired:
            trades, stats = scan_provider(provider)
            all_trades.extend(trades)
            provider_stats.append(stats)
            row_count = stats["rows"]
        provenance.append(
            {
                "provider": provider.provider,
                "symbol": provider.symbol,
                "source_path": str(provider.path) if provider.path else "",
                "aq_provider_invoked": "false",
                "provider_requested": "true" if provider.path else "false",
                "provider_data_acquired": "true" if acquired else "false",
                "provider_unreachable_or_missing": "false" if acquired else "true",
                "local_cache_replay": "true" if acquired else "false",
                "rows": row_count,
            }
        )
    branch_summary = summarize(all_trades, ["factor", "main_regime", "sub_regime", "sub_sub_regime_or_profit_factor", "branch_path"])
    provider_summary = summarize(all_trades, ["provider", "symbol", "factor"])
    walk_summary = summarize(all_trades, ["provider", "factor", "walk_forward_fold"])
    write_csv(ROOT / "summaries" / "ob_fvg_provider_provenance_matrix.csv", provenance)
    write_csv(ROOT / "summaries" / "ob_fvg_branch_trades.csv", all_trades)
    write_csv(ROOT / "summaries" / "ob_fvg_branch_summary.csv", branch_summary)
    write_csv(ROOT / "summaries" / "ob_fvg_provider_summary.csv", provider_summary)
    write_csv(ROOT / "summaries" / "ob_fvg_walk_forward_summary.csv", walk_summary)
    manifest = {
        "run_root": str(ROOT),
        "factor_concepts": ["order_block_pullback_v1", "fair_value_gap_pullback_v1"],
        "branch_shape": "main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor",
        "provider_stats": provider_stats,
        "total_trades": len(all_trades),
        "branch_count": len(branch_summary),
        "provider_rows": len(provenance),
        "same_root_aq_provider_authority": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    (ROOT / "summaries" / "ob_fvg_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    top = sorted(branch_summary, key=lambda r: (float(r["profit_factor"]), int(r["trades"])), reverse=True)[:10]
    lines = [
        "# OB/FVG Regime Branch Screen v1",
        "",
        "This is a lightweight provider-backed screen, not an AQ promotion packet.",
        "",
        f"- total_trades: `{len(all_trades)}`",
        f"- branch_count: `{len(branch_summary)}`",
        f"- provider_rows: `{len(provenance)}`",
        "- same_root_aq_provider_authority: `false`",
        "- promotion_allowed: `false`",
        "- trade_usable: `false`",
        "",
        "## Top Branch Hints",
    ]
    for row in top:
        lines.append(
            f"- `{row['branch_path']}` trades=`{row['trades']}` win_rate=`{row['win_rate']}` "
            f"pf=`{row['profit_factor']}` mean_net=`{row['mean_net_return']}` folds=`{row['folds_present']}`"
        )
    lines.extend(
        [
            "",
            "## Fail-Closed Notes",
            "- TVR is missing in this local provider file set.",
            "- All acquired provider rows are replayed from prior normalized provider artifacts, not same-root AQ/provider acquisition.",
            "- No Auto-Quant backtest, Pre-Bayes, BBN, CatBoost runtime registration, or execution-tree admission is claimed by this root.",
        ]
    )
    (ROOT / "ob_fvg_regime_branch_screen_v1.md").write_text("\n".join(lines) + "\n")
    assertions = [
        f"total_trades={len(all_trades)}",
        f"branch_count={len(branch_summary)}",
        f"provider_rows={len(provenance)}",
        f"tvr_missing={any(r['provider'] == 'TradingViewRemix/TVR' and r['provider_data_acquired'] == 'false' for r in provenance)}",
        "promotion_allowed=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    (ROOT / "checks" / "ob_fvg_regime_branch_screen_assertions.out").write_text("\n".join(assertions) + "\n")
    print(json.dumps(manifest, indent=2))
    return 0 if all_trades else 2


if __name__ == "__main__":
    raise SystemExit(main())
