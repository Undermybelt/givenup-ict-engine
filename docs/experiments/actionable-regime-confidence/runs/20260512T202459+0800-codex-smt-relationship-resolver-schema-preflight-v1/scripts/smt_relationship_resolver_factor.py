#!/usr/bin/env python3
"""SMT relationship resolver and SMT confirmation-failure detector.

This is a lightweight factor/training file for preflight material generation.
It deliberately emits confirmation-only rows. It never marks SMT actionable by
itself; downstream admission requires MSS/CISD, displacement, and PDA context.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


POSITIVE_SEEDS = {
    "NQ": ["ES", "YM", "RTY", "QQQ", "SPY", "DIA", "IWM", "NAS100", "US500", "US30"],
    "ES": ["NQ", "YM", "RTY", "SPY", "QQQ", "DIA"],
    "EURUSD": ["GBPUSD", "EURGBP"],
    "XAUUSD": ["XAGUSD", "GC", "SI", "GDX"],
    "BTC": ["ETH", "SOL", "TOTAL", "QQQ"],
    "ETH": ["BTC", "SOL", "TOTAL"],
}

NEGATIVE_SEEDS = {
    "NQ": ["DXY", "VIX"],
    "ES": ["DXY", "VIX"],
    "EURUSD": ["DXY", "USDX"],
    "XAUUSD": ["DXY", "US10Y", "REAL_YIELD"],
    "BTC": ["DXY"],
    "ETH": ["DXY"],
}


@dataclass(frozen=True)
class Candle:
    time: str
    open: float
    high: float
    low: float
    close: float


def norm_symbol(symbol: str) -> str:
    return symbol.upper().replace("/", "").replace("-", "").replace("!", "")


def resolve_related(
    base_symbol: str,
    provider_universe: list[str],
    symbol_metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    base = norm_symbol(base_symbol)
    universe = {norm_symbol(s): s for s in provider_universe}
    candidates: list[dict[str, Any]] = []
    for relationship_type, seed_map in (("positive", POSITIVE_SEEDS), ("negative", NEGATIVE_SEEDS)):
        for candidate in seed_map.get(base, []):
            normalized = norm_symbol(candidate)
            if normalized in universe:
                candidates.append(
                    {
                        "comparison_symbol": universe[normalized],
                        "relationship_type": relationship_type,
                        "relationship_confidence": 0.35,
                        "evidence_source": "seed_matched_provider_universe_requires_recent_correlation_validation",
                    }
                )
    metadata = symbol_metadata or {}
    base_meta = metadata.get(base_symbol) or metadata.get(base) or {}
    stock_related = []
    for key in ("index_etf", "sector_etf", "top_peers", "options_liquidity_proxies"):
        value = base_meta.get(key, [])
        if isinstance(value, str):
            stock_related.append(value)
        else:
            stock_related.extend(value)
    seen = {norm_symbol(row["comparison_symbol"]) for row in candidates}
    for candidate in stock_related:
        normalized = norm_symbol(str(candidate))
        if normalized in universe and normalized not in seen and normalized != base:
            candidates.append(
                {
                    "comparison_symbol": universe[normalized],
                    "relationship_type": "uncertain",
                    "relationship_confidence": 0.0,
                    "evidence_source": "stock_metadata_matched_provider_universe_requires_sector_peer_and_recent_correlation_validation",
                }
            )
            seen.add(normalized)
    return candidates


def parse_candles(rows: list[dict[str, Any]]) -> list[Candle]:
    candles = []
    for row in rows:
        candles.append(
            Candle(
                time=str(row["time"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
            )
        )
    return candles


def returns(candles: list[Candle]) -> list[float]:
    out = []
    for prev, cur in zip(candles, candles[1:]):
        if prev.close == 0:
            out.append(0.0)
        else:
            out.append((cur.close - prev.close) / prev.close)
    return out


def correlation(a: list[float], b: list[float]) -> float:
    if len(a) < 10 or len(a) != len(b):
        return 0.0
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def latest_confirmed_swing(candles: list[Candle], lookback: int = 2) -> dict[str, Any] | None:
    if len(candles) < lookback * 2 + 3:
        return None
    pivots = []
    for i in range(lookback, len(candles) - lookback):
        left = candles[i - lookback : i]
        right = candles[i + 1 : i + 1 + lookback]
        cur = candles[i]
        if cur.high > max(c.high for c in left + right):
            pivots.append({"kind": "high", "index": i, "time": cur.time, "level": cur.high})
        if cur.low < min(c.low for c in left + right):
            pivots.append({"kind": "low", "index": i, "time": cur.time, "level": cur.low})
    if len(pivots) < 2:
        return None
    current = pivots[-1]
    previous_same = next((p for p in reversed(pivots[:-1]) if p["kind"] == current["kind"]), None)
    if not previous_same:
        return None
    if current["kind"] == "high":
        swing_type = "HH" if current["level"] > previous_same["level"] else "LH"
        swept_side = "buy_side_liquidity" if swing_type == "HH" else "none"
    else:
        swing_type = "LL" if current["level"] < previous_same["level"] else "HL"
        swept_side = "sell_side_liquidity" if swing_type == "LL" else "none"
    return {**current, "swing_type": swing_type, "previous_level": previous_same["level"], "swept_side": swept_side}


def invert_swing(swing_type: str) -> str:
    return {"HH": "LL", "LL": "HH", "HL": "LH", "LH": "HL"}.get(swing_type, swing_type)


def sessions_overlap(base_session: str, comparison_session: str, session_calendar: dict[str, Any] | None) -> bool:
    if base_session == comparison_session:
        return True
    overlaps = (session_calendar or {}).get("overlaps", {})
    base_overlaps = set(overlaps.get(base_session, []))
    comparison_overlaps = set(overlaps.get(comparison_session, []))
    return comparison_session in base_overlaps or base_session in comparison_overlaps


def detect_smt(
    base_symbol: str,
    comparison_symbol: str,
    relationship_type: str,
    timeframe: str,
    session: str,
    base_candles: list[Candle],
    comparison_candles: list[Candle],
    comparison_timeframe: str | None = None,
    comparison_session: str | None = None,
    session_calendar: dict[str, Any] | None = None,
    event_window_bars: int = 3,
) -> dict[str, Any]:
    comparison_timeframe = comparison_timeframe or timeframe
    comparison_session = comparison_session or session
    timeframe_aligned = timeframe == comparison_timeframe
    session_overlap = sessions_overlap(session, comparison_session, session_calendar)
    fail = None
    if not timeframe_aligned:
        fail = "timeframe_mismatch"
    elif not session_overlap:
        fail = "session_not_overlapping"
    elif len(base_candles) != len(comparison_candles):
        fail = "timeframe_or_bar_alignment_mismatch"
    elif len(base_candles) < 20:
        fail = "insufficient_candles_for_swing_and_recent_correlation"

    corr = correlation(returns(base_candles), returns(comparison_candles)) if not fail else 0.0
    if not fail:
        if relationship_type == "positive" and corr < 0.35:
            fail = "recent_positive_correlation_unstable"
        if relationship_type == "negative" and corr > -0.35:
            fail = "recent_negative_correlation_unstable"

    base_swing = latest_confirmed_swing(base_candles) if not fail else None
    comparison_swing = latest_confirmed_swing(comparison_candles) if not fail else None
    if not fail and (base_swing is None or comparison_swing is None):
        fail = "missing_confirmed_swing_pair"

    normalized = relationship_type == "negative"
    base_type = base_swing["swing_type"] if base_swing else "n/a"
    comparison_raw_type = comparison_swing["swing_type"] if comparison_swing else None
    comparison_type = invert_swing(comparison_raw_type) if normalized and comparison_raw_type else (comparison_raw_type or "n/a")
    event_time_delta_bars = (
        abs(int(base_swing["index"]) - int(comparison_swing["index"]))
        if base_swing and comparison_swing
        else None
    )
    same_event_window_confirmed = event_time_delta_bars is not None and event_time_delta_bars <= event_window_bars
    if not fail and not same_event_window_confirmed:
        fail = "swing_confirmation_failure_not_near_same_event_window"
    smt_signal = "none"
    if not fail:
        if base_type == "LL" and comparison_type == "HL":
            smt_signal = "bullish_smt"
        elif base_type == "HH" and comparison_type == "LH":
            smt_signal = "bearish_smt"
        else:
            fail = "no_swing_confirmation_failure_at_latest_event"

    return {
        "base_symbol": base_symbol,
        "comparison_symbol": comparison_symbol,
        "relationship_type": relationship_type if relationship_type in {"positive", "negative"} else "uncertain",
        "relationship_confidence": round(abs(corr), 4) if not fail else 0.0,
        "timeframe": timeframe,
        "session": session,
        "comparison_timeframe": comparison_timeframe,
        "comparison_session": comparison_session,
        "timeframe_aligned": timeframe_aligned,
        "session_overlap": session_overlap,
        "correlation_window_bars": max(0, min(len(base_candles), len(comparison_candles)) - 1),
        "recent_correlation": round(corr, 4) if not fail else 0.0,
        "smt_signal": smt_signal,
        "base_swing_type": base_type,
        "base_event_time": base_swing["time"] if base_swing else None,
        "base_level": base_swing["level"] if base_swing else None,
        "comparison_swing_type": comparison_type,
        "comparison_event_time": comparison_swing["time"] if comparison_swing else None,
        "comparison_level": comparison_swing["level"] if comparison_swing else None,
        "event_window_bars": event_window_bars,
        "event_time_delta_bars": event_time_delta_bars,
        "same_event_window_confirmed": same_event_window_confirmed,
        "swept_side": base_swing["swept_side"] if base_swing else "none",
        "normalized_for_inverse_correlation": normalized,
        "raw_comparison_swing_type": comparison_raw_type,
        "raw_comparison_level": comparison_swing["level"] if comparison_swing else None,
        "near_pd_array": False,
        "pd_array_type": "none",
        "mss_or_cisd_confirmed": False,
        "displacement_confirmed": False,
        "provider_provenance": None,
        "evidence_source": "local_input_candles" if not fail else "factor_fail_closed",
        "confidence": 0.0 if fail else 0.25,
        "fail_closed_reason": fail or "confirmation_only_waiting_for_mss_cisd_displacement_and_pda",
        "confirmation_role": "confirmation_only",
        "actionable": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text())
    rows = []
    base_symbol = payload["base_symbol"]
    provider_universe = payload.get("provider_universe", [])
    candles = payload.get("candles", {})
    comparison_timeframes = payload.get("comparison_timeframes", {})
    comparison_sessions = payload.get("comparison_sessions", {})
    session_calendar = payload.get("session_calendar", {})
    for relation in resolve_related(base_symbol, provider_universe, payload.get("symbol_metadata", {})):
        comparison = relation["comparison_symbol"]
        if base_symbol not in candles or comparison not in candles:
            rows.append(
                {
                    "base_symbol": base_symbol,
                    "comparison_symbol": comparison,
                    "relationship_type": relation["relationship_type"],
                    "relationship_confidence": 0.0,
                    "timeframe": payload.get("timeframe", "n/a"),
                    "session": payload.get("session", "n/a"),
                    "comparison_timeframe": comparison_timeframes.get(comparison, payload.get("timeframe", "n/a")),
                    "comparison_session": comparison_sessions.get(comparison, payload.get("session", "n/a")),
                    "timeframe_aligned": payload.get("timeframe", "n/a") == comparison_timeframes.get(comparison, payload.get("timeframe", "n/a")),
                    "session_overlap": sessions_overlap(
                        payload.get("session", "n/a"),
                        comparison_sessions.get(comparison, payload.get("session", "n/a")),
                        session_calendar,
                    ),
                    "correlation_window_bars": 0,
                    "recent_correlation": 0.0,
                    "smt_signal": "none",
                    "base_swing_type": "n/a",
                    "base_event_time": None,
                    "base_level": None,
                    "comparison_swing_type": "n/a",
                    "comparison_event_time": None,
                    "comparison_level": None,
                    "event_window_bars": int(payload.get("event_window_bars", 3)),
                    "event_time_delta_bars": None,
                    "same_event_window_confirmed": False,
                    "swept_side": "none",
                    "normalized_for_inverse_correlation": relation["relationship_type"] == "negative",
                    "raw_comparison_swing_type": None,
                    "raw_comparison_level": None,
                    "near_pd_array": False,
                    "pd_array_type": "none",
                    "mss_or_cisd_confirmed": False,
                    "displacement_confirmed": False,
                    "provider_provenance": None,
                    "evidence_source": relation["evidence_source"],
                    "confidence": 0.0,
                    "fail_closed_reason": "missing_base_or_comparison_candles",
                    "confirmation_role": "confirmation_only",
                    "actionable": False,
                }
            )
            continue
        rows.append(
            detect_smt(
                base_symbol,
                comparison,
                relation["relationship_type"],
                payload.get("timeframe", "n/a"),
                payload.get("session", "n/a"),
                parse_candles(candles[base_symbol]),
                parse_candles(candles[comparison]),
                comparison_timeframes.get(comparison, payload.get("timeframe", "n/a")),
                comparison_sessions.get(comparison, payload.get("session", "n/a")),
                session_calendar,
                int(payload.get("event_window_bars", 3)),
            )
        )
    output = json.dumps({"rows": rows}, indent=2) + "\n"
    if args.output == "-":
        print(output, end="")
    else:
        Path(args.output).write_text(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
