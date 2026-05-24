from __future__ import annotations

from statistics import median
from pathlib import Path
from typing import Mapping, Sequence

try:
    from .mim_cost_window_features import Bar, read_bars
except ImportError:  # pragma: no cover - exercised by direct script execution.
    from mim_cost_window_features import Bar, read_bars


DEFAULT_TIMEFRAMES = ("5m", "15m", "30m", "1h", "4h", "1d")
DEFAULT_MIN_ALIGNED = 3


def build_mtf_trend_resonance(
    context_csvs: Mapping[str, Path],
    *,
    event_ts: str,
    side: int,
    required_timeframes: Sequence[str] = DEFAULT_TIMEFRAMES,
    min_aligned: int = DEFAULT_MIN_ALIGNED,
    lookback: int = 5,
) -> dict[str, object]:
    if not context_csvs:
        return _disabled_summary()

    by_timeframe: dict[str, dict[str, object]] = {}
    aligned: list[str] = []
    rejected: list[str] = []
    missing: list[str] = []
    for timeframe in required_timeframes:
        path = context_csvs.get(timeframe)
        if path is None:
            missing.append(timeframe)
            continue
        verdict = _timeframe_verdict(read_bars(Path(path)), event_ts=event_ts, side=side, lookback=lookback)
        by_timeframe[timeframe] = verdict
        if verdict["aligned"]:
            aligned.append(timeframe)
        else:
            rejected.append(timeframe)

    enabled = bool(by_timeframe)
    score = len(aligned) / len(by_timeframe) if by_timeframe else 0.0
    return {
        "schema_version": "mtf-trend-resonance/v1",
        "enabled": enabled,
        "side": side,
        "required_timeframes": list(required_timeframes),
        "min_aligned": min_aligned,
        "aligned": enabled and len(aligned) >= min_aligned,
        "aligned_timeframes": aligned,
        "rejected_timeframes": rejected,
        "missing_timeframes": missing,
        "resonance_score": score,
        "by_timeframe": by_timeframe,
        "promotion_allowed": False,
        "trade_usable": False,
        "downstream_allowed": False,
    }


def _timeframe_verdict(bars: Sequence[Bar], *, event_ts: str, side: int, lookback: int) -> dict[str, object]:
    cutoff = _parse_event_ts(event_ts)
    eligible = [bar for bar in sorted(bars, key=lambda item: item.ts) if bar.ts <= cutoff]
    if len(eligible) < max(3, lookback):
        return {
            "aligned": False,
            "reason": "insufficient_context_bars",
            "bar_count": len(eligible),
            "slope_return": 0.0,
            "range_expansion": 0.0,
        }

    window = eligible[-lookback:]
    first_close = window[0].close
    last_close = window[-1].close
    slope_return = (last_close - first_close) / first_close if first_close > 0 else 0.0
    ranges = [max(0.0, bar.high - bar.low) for bar in window]
    range_expansion = ranges[-1] / max(1e-12, median(ranges[:-1]) if len(ranges) > 1 else ranges[-1])
    direction_ok = slope_return > 0.0 if side >= 1 else slope_return < 0.0
    last = window[-1]
    structure_ok = last.close >= max(bar.high for bar in window[:-1]) if side >= 1 else last.close <= min(bar.low for bar in window[:-1])
    aligned = bool(direction_ok and (structure_ok or range_expansion >= 1.05))
    return {
        "aligned": aligned,
        "reason": "aligned_trend_context" if aligned else "trend_context_rejected",
        "bar_count": len(eligible),
        "slope_return": slope_return,
        "range_expansion": range_expansion,
        "structure_break": structure_ok,
    }


def _disabled_summary() -> dict[str, object]:
    return {
        "schema_version": "mtf-trend-resonance/v1",
        "enabled": False,
        "side": 0,
        "required_timeframes": list(DEFAULT_TIMEFRAMES),
        "min_aligned": DEFAULT_MIN_ALIGNED,
        "aligned": False,
        "aligned_timeframes": [],
        "rejected_timeframes": [],
        "missing_timeframes": [],
        "resonance_score": 0.0,
        "by_timeframe": {},
        "promotion_allowed": False,
        "trade_usable": False,
        "downstream_allowed": False,
    }


def _parse_event_ts(value: str):
    from datetime import datetime

    clean = value.strip()
    if clean.endswith("Z"):
        clean = clean[:-1] + "+00:00"
    return datetime.fromisoformat(clean)
