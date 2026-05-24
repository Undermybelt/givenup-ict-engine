from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Bar:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class MimCostWindowFeatures:
    first_window_return: float
    late_window_return: float
    first_window_realized_variance: float
    first_window_amihud: float
    corwin_schultz_spread: float
    basic_high_low_spread: float
    rvol: float
    momentum_state_prob: float
    posterior_entropy_proxy: float
    eligible_long: bool


def read_bars(path: Path) -> list[Bar]:
    rows: list[Bar] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            timestamp = row.get("timestamp") or row.get("datetime") or row.get("date") or row.get("ts")
            if not timestamp:
                raise ValueError("missing timestamp-like column")
            rows.append(
                Bar(
                    ts=_parse_timestamp(timestamp),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row.get("volume") or 0.0),
                )
            )
    return sorted(rows, key=lambda item: item.ts)


def mim_cost_window_features(
    bars: Iterable[Bar],
    *,
    open_minutes: int = 30,
    late_minutes: int = 30,
    spread_max: float = 0.0065,
    first_abs_return_min: float = 0.0015,
    rvol_min: float = 0.60,
    momentum_prob_min: float = 0.58,
    entropy_max: float = 0.92,
) -> MimCostWindowFeatures:
    ordered = sorted(bars, key=lambda item: item.ts)
    if len(ordered) < max(open_minutes, late_minutes) + 2:
        raise ValueError("not enough bars for MIM cost-window features")

    first = ordered[:open_minutes]
    late = ordered[-late_minutes:]
    first_ret = _safe_log_return(first[0].open, first[-1].close)
    late_ret = _safe_log_return(late[0].open, late[-1].close)
    rv = realized_variance(first)
    amihud = amihud_illiquidity(first)
    cs_spread = corwin_schultz_spread(first)
    hl_spread = basic_high_low_spread(first)
    rvol = relative_volume(first, ordered)
    momentum_prob = momentum_state_probability(first_ret, late_ret, rv, rvol, cs_spread)
    entropy = posterior_entropy_proxy(momentum_prob)
    eligible = (
        first_ret >= first_abs_return_min
        and cs_spread <= spread_max
        and hl_spread <= spread_max * 1.35
        and rvol >= rvol_min
        and momentum_prob >= momentum_prob_min
        and entropy <= entropy_max
    )
    return MimCostWindowFeatures(
        first_window_return=first_ret,
        late_window_return=late_ret,
        first_window_realized_variance=rv,
        first_window_amihud=amihud,
        corwin_schultz_spread=cs_spread,
        basic_high_low_spread=hl_spread,
        rvol=rvol,
        momentum_state_prob=momentum_prob,
        posterior_entropy_proxy=entropy,
        eligible_long=eligible,
    )


def realized_variance(bars: Iterable[Bar]) -> float:
    closes = [bar.close for bar in bars if bar.close > 0]
    if len(closes) < 2:
        return 0.0
    returns = [_safe_log_return(prev, cur) for prev, cur in zip(closes, closes[1:])]
    return sum(ret * ret for ret in returns)


def amihud_illiquidity(bars: Iterable[Bar]) -> float:
    values: list[float] = []
    prev_close: float | None = None
    for bar in bars:
        if prev_close is not None and bar.volume > 0 and bar.close > 0:
            dollar_volume = max(1.0, bar.volume * bar.close)
            values.append(abs(_safe_log_return(prev_close, bar.close)) / dollar_volume)
        prev_close = bar.close
    return sum(values) / len(values) if values else 0.0


def corwin_schultz_spread(bars: Iterable[Bar]) -> float:
    ordered = [bar for bar in bars if bar.high > 0 and bar.low > 0 and bar.high >= bar.low]
    if len(ordered) < 2:
        return 0.0
    denom = 3.0 - 2.0 * math.sqrt(2.0)
    values: list[float] = []
    for left, right in zip(ordered, ordered[1:]):
        beta = math.log(left.high / left.low) ** 2 + math.log(right.high / right.low) ** 2
        two_bar_high = max(left.high, right.high)
        two_bar_low = min(left.low, right.low)
        gamma = math.log(two_bar_high / two_bar_low) ** 2
        alpha = (math.sqrt(2.0 * beta) - math.sqrt(beta)) / denom - math.sqrt(max(0.0, gamma / denom))
        spread = 2.0 * (math.exp(alpha) - 1.0) / (1.0 + math.exp(alpha))
        values.append(max(0.0, spread))
    return sum(values) / len(values)


def basic_high_low_spread(bars: Iterable[Bar]) -> float:
    values = [
        max(0.0, 2.0 * (bar.high - bar.low) / max(1e-12, bar.high + bar.low))
        for bar in bars
        if bar.high > 0 and bar.low > 0 and bar.high >= bar.low
    ]
    return sum(values) / len(values) if values else 0.0


def relative_volume(window: Iterable[Bar], session: Iterable[Bar]) -> float:
    window_rows = list(window)
    session_rows = list(session)
    if not window_rows or not session_rows:
        return 0.0
    window_volume = sum(max(0.0, bar.volume) for bar in window_rows)
    session_avg = sum(max(0.0, bar.volume) for bar in session_rows) / len(session_rows)
    return window_volume / max(1.0, session_avg * len(window_rows))


def momentum_state_probability(first_ret: float, late_ret: float, rv: float, rvol: float, spread: float) -> float:
    directional = 1.0 / (1.0 + math.exp(-650.0 * first_ret))
    confirmation = 1.0 / (1.0 + math.exp(-650.0 * late_ret))
    vol_ok = 1.0 / (1.0 + math.exp(-45_000.0 * (rv - 0.000015)))
    volume_ok = min(1.0, max(0.0, rvol / 1.5))
    cost_ok = 1.0 - min(1.0, max(0.0, spread / 0.012))
    return min(
        1.0,
        max(
            0.0,
            0.42 * directional + 0.18 * confirmation + 0.16 * vol_ok + 0.14 * volume_ok + 0.10 * cost_ok,
        ),
    )


def posterior_entropy_proxy(probability: float) -> float:
    return 1.0 - abs(min(1.0, max(0.0, probability)) - 0.5) * 2.0


def triple_barrier_label(
    bars: Iterable[Bar],
    entry_index: int,
    *,
    profit_take: float = 0.006,
    stop_loss: float = 0.004,
    horizon: int = 30,
) -> int:
    ordered = sorted(bars, key=lambda item: item.ts)
    if entry_index < 0 or entry_index >= len(ordered):
        raise IndexError("entry_index out of range")
    entry = ordered[entry_index].close
    end = min(len(ordered), entry_index + horizon + 1)
    for bar in ordered[entry_index + 1 : end]:
        high_ret = (bar.high - entry) / entry
        low_ret = (bar.low - entry) / entry
        if high_ret >= profit_take:
            return 1
        if low_ret <= -abs(stop_loss):
            return -1
    return 0


def _safe_log_return(start: float, end: float) -> float:
    if start <= 0 or end <= 0:
        return 0.0
    return math.log(end / start)


def _parse_timestamp(value: str) -> datetime:
    clean = value.strip()
    if clean.endswith("Z"):
        clean = clean[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(clean)
    except ValueError:
        return datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
