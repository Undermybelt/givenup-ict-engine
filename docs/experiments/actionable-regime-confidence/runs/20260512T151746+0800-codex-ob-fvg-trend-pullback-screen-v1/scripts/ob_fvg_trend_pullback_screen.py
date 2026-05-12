#!/usr/bin/env python3
"""Lightweight OHLCV-only Order Block / FVG continuation screen.

This script is intentionally self-contained and dependency-free. It is a
screening artifact, not a production factor implementation.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable


@dataclass(frozen=True)
class DataSource:
    provider: str
    symbol: str
    path: Path
    roundtrip_cost: float


@dataclass(frozen=True)
class Bar:
    index: int
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    provider: str
    symbol: str
    family: str
    direction: int
    entry_index: int
    entry_time: str
    entry_price: float
    exit_index: int
    exit_time: str
    exit_price: float
    net_return: float
    main_regime: str
    volatility_bucket: str
    momentum_bucket: str
    branch_path: str
    source_detail: str


def parse_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    value = row.get(key, "")
    if value == "":
        return default
    return float(value)


def load_bars(path: Path) -> list[Bar]:
    bars: list[Bar] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for i, row in enumerate(reader):
            bars.append(
                Bar(
                    index=i,
                    timestamp=row["timestamp"],
                    open=parse_float(row, "open"),
                    high=parse_float(row, "high"),
                    low=parse_float(row, "low"),
                    close=parse_float(row, "close"),
                    volume=parse_float(row, "volume"),
                )
            )
    return bars


def rolling_mean(values: list[float], window: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    acc = 0.0
    for i, value in enumerate(values):
        acc += value
        if i >= window:
            acc -= values[i - window]
        if i >= window - 1:
            out[i] = acc / window
    return out


def true_ranges(bars: list[Bar]) -> list[float]:
    ranges: list[float] = []
    prev_close = bars[0].close if bars else 0.0
    for bar in bars:
        ranges.append(max(bar.high - bar.low, abs(bar.high - prev_close), abs(bar.low - prev_close)))
        prev_close = bar.close
    return ranges


def classify_context(
    bars: list[Bar],
    atr: list[float | None],
    atr_base: list[float | None],
    i: int,
) -> tuple[str, str, str]:
    if i < 48 or atr[i] is None or atr_base[i] in (None, 0):
        return "insufficient_context", "unknown_volatility", "unknown_momentum"
    close_now = bars[i].close
    close_24 = bars[i - 24].close
    ret_24 = close_now / close_24 - 1.0 if close_24 else 0.0
    atr_pct = atr[i] / close_now if close_now else 0.0
    trend_cutoff = max(0.003, 1.25 * atr_pct)
    main_regime = "trend_expansion" if abs(ret_24) >= trend_cutoff else "range_or_de_risk"
    volatility_bucket = "high_volatility" if atr[i] > 1.2 * atr_base[i] else "normal_volatility"
    momentum_bucket = "up_momentum" if ret_24 > 0 else "down_or_flat_momentum"
    return main_regime, volatility_bucket, momentum_bucket


def outcome_return(direction: int, entry: float, exit_price: float, roundtrip_cost: float) -> float:
    if entry <= 0:
        return 0.0
    gross = (exit_price / entry - 1.0) * direction
    return gross - roundtrip_cost


def branch_path(main_regime: str, volatility_bucket: str, momentum_bucket: str, family: str) -> str:
    leaf = family.removesuffix("_v1")
    return "->".join([main_regime, volatility_bucket, momentum_bucket, leaf])


def build_signal(
    source: DataSource,
    bars: list[Bar],
    atr: list[float | None],
    atr_base: list[float | None],
    family: str,
    direction: int,
    entry_index: int,
    exit_horizon: int,
    detail: str,
) -> Signal | None:
    exit_index = min(entry_index + exit_horizon, len(bars) - 1)
    if exit_index <= entry_index:
        return None
    entry = bars[entry_index].close
    exit_price = bars[exit_index].close
    main_regime, vol_bucket, mom_bucket = classify_context(bars, atr, atr_base, entry_index)
    path = branch_path(main_regime, vol_bucket, mom_bucket, family)
    return Signal(
        provider=source.provider,
        symbol=source.symbol,
        family=family,
        direction=direction,
        entry_index=entry_index,
        entry_time=bars[entry_index].timestamp,
        entry_price=entry,
        exit_index=exit_index,
        exit_time=bars[exit_index].timestamp,
        exit_price=exit_price,
        net_return=outcome_return(direction, entry, exit_price, source.roundtrip_cost),
        main_regime=main_regime,
        volatility_bucket=vol_bucket,
        momentum_bucket=mom_bucket,
        branch_path=path,
        source_detail=detail,
    )


def scan_order_blocks(
    source: DataSource,
    bars: list[Bar],
    atr: list[float | None],
    atr_base: list[float | None],
    max_wait: int,
    exit_horizon: int,
) -> list[Signal]:
    signals: list[Signal] = []
    for i in range(3, len(bars) - exit_horizon - 1):
        if atr[i] in (None, 0):
            continue
        impulse = bars[i]
        prev = bars[i - 1]
        body = abs(impulse.close - impulse.open)
        range_size = impulse.high - impulse.low
        bullish_impulse = (
            impulse.close > impulse.open
            and prev.close < prev.open
            and impulse.close > max(b.high for b in bars[i - 3 : i])
            and body >= 0.55 * atr[i]
            and range_size >= 0.9 * atr[i]
        )
        bearish_impulse = (
            impulse.close < impulse.open
            and prev.close > prev.open
            and impulse.close < min(b.low for b in bars[i - 3 : i])
            and body >= 0.55 * atr[i]
            and range_size >= 0.9 * atr[i]
        )
        if not (bullish_impulse or bearish_impulse):
            continue
        direction = 1 if bullish_impulse else -1
        if direction == 1:
            zone_low, zone_high = prev.low, max(prev.open, prev.close)
        else:
            zone_low, zone_high = min(prev.open, prev.close), prev.high
        zone_mid = (zone_low + zone_high) / 2.0
        for j in range(i + 1, min(i + max_wait + 1, len(bars) - exit_horizon)):
            retested = bars[j].low <= zone_high and bars[j].high >= zone_low
            continued = bars[j].close >= zone_mid if direction == 1 else bars[j].close <= zone_mid
            if retested and continued:
                signal = build_signal(
                    source,
                    bars,
                    atr,
                    atr_base,
                    "order_block_retest_continuation_v1",
                    direction,
                    j,
                    exit_horizon,
                    f"impulse_index={i};block_index={i - 1};zone={zone_low:.8f}:{zone_high:.8f}",
                )
                if signal:
                    signals.append(signal)
                break
    return signals


def scan_fvg(
    source: DataSource,
    bars: list[Bar],
    atr: list[float | None],
    atr_base: list[float | None],
    max_wait: int,
    exit_horizon: int,
) -> list[Signal]:
    signals: list[Signal] = []
    for i in range(2, len(bars) - exit_horizon - 1):
        if atr[i] in (None, 0):
            continue
        bullish_gap = bars[i].low > bars[i - 2].high and (bars[i].low - bars[i - 2].high) >= 0.10 * atr[i]
        bearish_gap = bars[i].high < bars[i - 2].low and (bars[i - 2].low - bars[i].high) >= 0.10 * atr[i]
        if not (bullish_gap or bearish_gap):
            continue
        direction = 1 if bullish_gap else -1
        if direction == 1:
            zone_low, zone_high = bars[i - 2].high, bars[i].low
        else:
            zone_low, zone_high = bars[i].high, bars[i - 2].low
        zone_mid = (zone_low + zone_high) / 2.0
        for j in range(i + 1, min(i + max_wait + 1, len(bars) - exit_horizon)):
            retested = bars[j].low <= zone_high and bars[j].high >= zone_low
            continued = bars[j].close >= zone_mid if direction == 1 else bars[j].close <= zone_mid
            if retested and continued:
                signal = build_signal(
                    source,
                    bars,
                    atr,
                    atr_base,
                    "fvg_retrace_continuation_v1",
                    direction,
                    j,
                    exit_horizon,
                    f"gap_index={i};gap_base_index={i - 2};zone={zone_low:.8f}:{zone_high:.8f}",
                )
                if signal:
                    signals.append(signal)
                break
    return signals


def confluence_signals(
    source: DataSource,
    bars: list[Bar],
    atr: list[float | None],
    atr_base: list[float | None],
    ob_signals: list[Signal],
    fvg_signals: list[Signal],
    exit_horizon: int,
    window: int,
) -> list[Signal]:
    signals: list[Signal] = []
    fvg_by_direction: dict[int, list[Signal]] = defaultdict(list)
    for signal in fvg_signals:
        fvg_by_direction[signal.direction].append(signal)

    for ob in ob_signals:
        matches = [
            fvg
            for fvg in fvg_by_direction.get(ob.direction, [])
            if abs(fvg.entry_index - ob.entry_index) <= window
        ]
        if not matches:
            continue
        match = min(matches, key=lambda fvg: abs(fvg.entry_index - ob.entry_index))
        entry_index = max(ob.entry_index, match.entry_index)
        signal = build_signal(
            source,
            bars,
            atr,
            atr_base,
            "ob_fvg_confluence_continuation_v1",
            ob.direction,
            entry_index,
            exit_horizon,
            f"ob_entry={ob.entry_index};fvg_entry={match.entry_index}",
        )
        if signal:
            signals.append(signal)

    ob_by_direction: dict[int, list[Signal]] = defaultdict(list)
    for signal in ob_signals:
        ob_by_direction[signal.direction].append(signal)
    for fvg in fvg_signals:
        matches = [
            ob
            for ob in ob_by_direction.get(fvg.direction, [])
            if 0 <= fvg.entry_index - ob.entry_index <= window
        ]
        if not matches:
            continue
        match = min(matches, key=lambda ob: fvg.entry_index - ob.entry_index)
        signal = build_signal(
            source,
            bars,
            atr,
            atr_base,
            "fvg_ob_pullback_resume_v1",
            fvg.direction,
            fvg.entry_index,
            exit_horizon,
            f"ob_entry={match.entry_index};fvg_entry={fvg.entry_index}",
        )
        if signal:
            signals.append(signal)
    return signals


def profit_factor(returns: Iterable[float]) -> float:
    gains = 0.0
    losses = 0.0
    for value in returns:
        if value > 0:
            gains += value
        elif value < 0:
            losses += abs(value)
    if losses == 0:
        return math.inf if gains > 0 else 0.0
    return gains / losses


def summarize(signals: list[Signal]) -> list[dict[str, object]]:
    groups: dict[tuple[str, ...], list[Signal]] = defaultdict(list)
    for signal in signals:
        key = (
            signal.family,
            signal.provider,
            signal.symbol,
            signal.branch_path,
            signal.main_regime,
            signal.volatility_bucket,
            signal.momentum_bucket,
        )
        groups[key].append(signal)

    rows: list[dict[str, object]] = []
    for key, items in sorted(groups.items()):
        returns = [item.net_return for item in items]
        rows.append(
            {
                "family": key[0],
                "provider": key[1],
                "symbol": key[2],
                "branch_path": key[3],
                "main_regime": key[4],
                "volatility_bucket": key[5],
                "momentum_bucket": key[6],
                "trade_count": len(items),
                "win_rate": sum(1 for value in returns if value > 0) / len(returns),
                "avg_net_return": mean(returns),
                "total_net_return": sum(returns),
                "profit_factor": profit_factor(returns),
            }
        )
    return rows


def aggregate_by_branch(signals: list[Signal]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, str, str, str], list[Signal]] = defaultdict(list)
    for signal in signals:
        groups[
            (
                signal.family,
                signal.branch_path,
                signal.main_regime,
                signal.volatility_bucket,
                signal.momentum_bucket,
            )
        ].append(signal)

    rows: list[dict[str, object]] = []
    for key, items in sorted(groups.items()):
        returns = [item.net_return for item in items]
        providers = sorted({item.provider for item in items})
        symbols = sorted({item.symbol for item in items})
        rows.append(
            {
                "family": key[0],
                "branch_path": key[1],
                "main_regime": key[2],
                "volatility_bucket": key[3],
                "momentum_bucket": key[4],
                "provider_count": len(providers),
                "providers": "|".join(providers),
                "symbol_count": len(symbols),
                "symbols": "|".join(symbols),
                "trade_count": len(items),
                "win_rate": sum(1 for value in returns if value > 0) / len(returns),
                "avg_net_return": mean(returns),
                "total_net_return": sum(returns),
                "profit_factor": profit_factor(returns),
            }
        )
    rows.sort(
        key=lambda row: (
            int(row["provider_count"]),
            int(row["trade_count"]),
            float(row["profit_factor"]) if math.isfinite(float(row["profit_factor"])) else 999.0,
            float(row["avg_net_return"]),
        ),
        reverse=True,
    )
    return rows


def fold_summary(signals: list[Signal], folds: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    groups: dict[tuple[str, str, str, str], list[Signal]] = defaultdict(list)
    for signal in signals:
        groups[(signal.family, signal.provider, signal.symbol, signal.branch_path)].append(signal)
    for key, items in sorted(groups.items()):
        items = sorted(items, key=lambda signal: signal.entry_index)
        if len(items) < folds:
            continue
        chunk_size = math.ceil(len(items) / folds)
        for fold_index in range(folds):
            chunk = items[fold_index * chunk_size : (fold_index + 1) * chunk_size]
            if not chunk:
                continue
            returns = [signal.net_return for signal in chunk]
            rows.append(
                {
                    "family": key[0],
                    "provider": key[1],
                    "symbol": key[2],
                    "branch_path": key[3],
                    "fold": fold_index + 1,
                    "trade_count": len(chunk),
                    "win_rate": sum(1 for value in returns if value > 0) / len(returns),
                    "avg_net_return": mean(returns),
                    "profit_factor": profit_factor(returns),
                    "start_time": chunk[0].entry_time,
                    "end_time": chunk[-1].entry_time,
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def top_rows(summary_rows: list[dict[str, object]], min_trades: int) -> list[dict[str, object]]:
    candidates = [row for row in summary_rows if int(row["trade_count"]) >= min_trades]
    candidates.sort(
        key=lambda row: (
            float(row["profit_factor"]) if math.isfinite(float(row["profit_factor"])) else 999.0,
            float(row["avg_net_return"]),
            int(row["trade_count"]),
        ),
        reverse=True,
    )
    return candidates[:12]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--exit-horizon", type=int, default=12)
    parser.add_argument("--max-wait", type=int, default=24)
    parser.add_argument("--confluence-window", type=int, default=24)
    parser.add_argument("--min-trades", type=int, default=50)
    parser.add_argument("--source", action="append", nargs=4, metavar=("PROVIDER", "SYMBOL", "CSV", "COST"))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sources = [
        DataSource(provider=provider, symbol=symbol, path=Path(path), roundtrip_cost=float(cost))
        for provider, symbol, path, cost in (args.source or [])
    ]
    if not sources:
        raise SystemExit("--source is required")

    all_signals: list[Signal] = []
    source_counts: list[dict[str, object]] = []
    for source in sources:
        bars = load_bars(source.path)
        trs = true_ranges(bars)
        atr = rolling_mean(trs, 14)
        atr_base = rolling_mean([value if value is not None else 0.0 for value in atr], 120)
        ob = scan_order_blocks(source, bars, atr, atr_base, args.max_wait, args.exit_horizon)
        fvg = scan_fvg(source, bars, atr, atr_base, args.max_wait, args.exit_horizon)
        confluence = confluence_signals(
            source,
            bars,
            atr,
            atr_base,
            ob,
            fvg,
            args.exit_horizon,
            args.confluence_window,
        )
        all_signals.extend(ob)
        all_signals.extend(fvg)
        all_signals.extend(confluence)
        source_counts.append(
            {
                "provider": source.provider,
                "symbol": source.symbol,
                "bars": len(bars),
                "ob_signals": len(ob),
                "fvg_signals": len(fvg),
                "confluence_signals": len(confluence),
            }
        )

    signal_rows = [signal.__dict__ for signal in all_signals]
    summary_rows = summarize(all_signals)
    aggregate_rows = aggregate_by_branch(all_signals)
    fold_rows = fold_summary(all_signals, 4)
    top = top_rows(summary_rows, args.min_trades)

    write_csv(
        output_dir / "ob_fvg_signal_rows.csv",
        signal_rows,
        [
            "provider",
            "symbol",
            "family",
            "direction",
            "entry_index",
            "entry_time",
            "entry_price",
            "exit_index",
            "exit_time",
            "exit_price",
            "net_return",
            "main_regime",
            "volatility_bucket",
            "momentum_bucket",
            "branch_path",
            "source_detail",
        ],
    )
    write_csv(
        output_dir / "ob_fvg_summary.csv",
        summary_rows,
        [
            "family",
            "provider",
            "symbol",
            "branch_path",
            "main_regime",
            "volatility_bucket",
            "momentum_bucket",
            "trade_count",
            "win_rate",
            "avg_net_return",
            "total_net_return",
            "profit_factor",
        ],
    )
    write_csv(
        output_dir / "ob_fvg_aggregate_by_branch.csv",
        aggregate_rows,
        [
            "family",
            "branch_path",
            "main_regime",
            "volatility_bucket",
            "momentum_bucket",
            "provider_count",
            "providers",
            "symbol_count",
            "symbols",
            "trade_count",
            "win_rate",
            "avg_net_return",
            "total_net_return",
            "profit_factor",
        ],
    )
    write_csv(
        output_dir / "ob_fvg_fold_summary.csv",
        fold_rows,
        [
            "family",
            "provider",
            "symbol",
            "branch_path",
            "fold",
            "trade_count",
            "win_rate",
            "avg_net_return",
            "profit_factor",
            "start_time",
            "end_time",
        ],
    )
    write_csv(
        output_dir / "ob_fvg_top_candidates.csv",
        top,
        [
            "family",
            "provider",
            "symbol",
            "branch_path",
            "main_regime",
            "volatility_bucket",
            "momentum_bucket",
            "trade_count",
            "win_rate",
            "avg_net_return",
            "total_net_return",
            "profit_factor",
        ],
    )

    manifest = {
        "protocol": "ob-fvg-trend-pullback-screen-v1",
        "evidence_class": "screen_only_ohlcv_proxy",
        "promotion_allowed": False,
        "exit_horizon_bars": args.exit_horizon,
        "max_wait_bars": args.max_wait,
        "confluence_window_bars": args.confluence_window,
        "min_trades_for_top_table": args.min_trades,
        "sources": [source.__dict__ | {"path": str(source.path)} for source in sources],
        "source_counts": source_counts,
        "total_signals": len(all_signals),
        "summary_rows": len(summary_rows),
        "aggregate_rows": len(aggregate_rows),
        "fold_rows": len(fold_rows),
        "top_candidate_rows": len(top),
        "outputs": {
            "signals": str(output_dir / "ob_fvg_signal_rows.csv"),
            "summary": str(output_dir / "ob_fvg_summary.csv"),
            "aggregate_by_branch": str(output_dir / "ob_fvg_aggregate_by_branch.csv"),
            "fold_summary": str(output_dir / "ob_fvg_fold_summary.csv"),
            "top_candidates": str(output_dir / "ob_fvg_top_candidates.csv"),
        },
    }
    (output_dir / "ob_fvg_screen_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
