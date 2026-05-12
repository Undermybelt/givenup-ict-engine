#!/usr/bin/env python3
"""Strict ICT SMT confirmation-failure material generator.

SMT here is not generic correlation or relative-strength language. A row is an
SMT candidate only when a comparable sibling market fails to confirm the same
liquidity sweep / swing event on the same timeframe and session.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


POSITIVE_SEEDS: dict[str, list[str]] = {
    "NQ": ["ES", "YM", "RTY", "QQQ", "SPY", "DIA", "IWM", "NAS100", "US500", "US30"],
    "ES": ["NQ", "YM", "RTY", "SPY", "QQQ", "DIA"],
    "YM": ["NQ", "ES", "RTY", "DIA", "SPY", "QQQ"],
    "EURUSD": ["GBPUSD", "EURGBP"],
    "XAUUSD": ["XAGUSD", "GDX"],
    "BTC": ["ETH", "SOL", "TOTAL", "QQQ"],
    "ETH": ["BTC", "SOL", "TOTAL"],
}

NEGATIVE_SEEDS: dict[str, list[str]] = {
    "NQ": ["DXY", "VIX"],
    "ES": ["DXY", "VIX"],
    "YM": ["DXY", "VIX"],
    "EURUSD": ["DXY"],
    "GBPUSD": ["DXY"],
    "XAUUSD": ["DXY", "US10Y", "REAL_YIELD"],
    "XAGUSD": ["DXY", "US10Y", "REAL_YIELD"],
    "BTC": ["DXY"],
    "ETH": ["DXY"],
}

ROW_FIELDS = [
    "base_symbol",
    "comparison_symbol",
    "relationship_type",
    "relationship_confidence",
    "timeframe",
    "session",
    "smt_signal",
    "base_swing_type",
    "base_level",
    "comparison_swing_type",
    "comparison_level",
    "swept_side",
    "normalized_for_inverse_correlation",
    "near_pd_array",
    "pd_array_type",
    "mss_or_cisd_confirmed",
    "displacement_confirmed",
    "confidence",
    "fail_closed_reason",
    "actionable",
    "raw_comparison_swing_type",
    "raw_comparison_level",
    "same_event_time_delta_bars",
    "provider_provenance",
]


@dataclass(frozen=True)
class Candle:
    time: str
    open: float
    high: float
    low: float
    close: float


def norm_symbol(symbol: str) -> str:
    return symbol.upper().replace("/", "").replace("-", "").replace("!", "").replace("=F", "")


def synthetic_candle_rows(pattern: str, close_path: str = "positive_zigzag") -> list[dict[str, Any]]:
    positive = [100, 102, 101, 103, 102, 104, 103, 105, 104, 106, 105, 107, 106, 108, 107, 109, 108, 110, 109, 111]
    closes = [300 - value for value in positive] if close_path == "inverse_zigzag" else positive
    rows: list[dict[str, Any]] = []
    for idx, close in enumerate(closes):
        rows.append(
            {
                "time": f"2026-05-12T{9 + idx // 4:02d}:{(idx % 4) * 15:02d}:00Z",
                "open": close,
                "high": close + 2,
                "low": close - 2,
                "close": close,
            }
        )

    if pattern == "base_LL":
        rows[8].update(high=112, low=80)
        rows[17].update(high=113, low=75)
        for idx in [15, 16, 18, 19]:
            rows[idx].update(low=90, high=115)
    elif pattern == "comparison_HL":
        rows[8].update(high=112, low=80)
        rows[17].update(high=113, low=85)
        for idx in [15, 16, 18, 19]:
            rows[idx].update(low=90, high=115)
    elif pattern == "base_HH":
        rows[8].update(high=120, low=90)
        rows[17].update(high=130, low=92)
        for idx in [15, 16, 18, 19]:
            rows[idx].update(low=85, high=115)
    elif pattern == "comparison_LH":
        rows[8].update(high=120, low=90)
        rows[17].update(high=110, low=92)
        for idx in [15, 16, 18, 19]:
            rows[idx].update(low=85, high=105)
    else:
        raise ValueError(f"unknown synthetic candle pattern: {pattern}")
    return rows


def parse_candles(rows: list[dict[str, Any]] | dict[str, Any]) -> list[Candle]:
    if isinstance(rows, dict) and "synthetic_pattern" in rows:
        rows = synthetic_candle_rows(str(rows["synthetic_pattern"]), str(rows.get("close_path", "positive_zigzag")))
    return [
        Candle(
            time=str(row["time"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
        )
        for row in rows
    ]


def returns(candles: list[Candle]) -> list[float]:
    out: list[float] = []
    for prev, cur in zip(candles, candles[1:]):
        out.append(0.0 if prev.close == 0 else (cur.close - prev.close) / prev.close)
    return out


def correlation(left: list[float], right: list[float]) -> float:
    if len(left) < 10 or len(left) != len(right):
        return 0.0
    left_mean = mean(left)
    right_mean = mean(right)
    num = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right))
    den_left = math.sqrt(sum((a - left_mean) ** 2 for a in left))
    den_right = math.sqrt(sum((b - right_mean) ** 2 for b in right))
    if den_left == 0 or den_right == 0:
        return 0.0
    return num / (den_left * den_right)


def resolve_related(base_symbol: str, provider_universe: list[str], metadata: dict[str, Any]) -> list[dict[str, Any]]:
    base = norm_symbol(base_symbol)
    universe = {norm_symbol(symbol): symbol for symbol in provider_universe}
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for relationship_type, seed_map in (("positive", POSITIVE_SEEDS), ("negative", NEGATIVE_SEEDS)):
        for candidate in seed_map.get(base, []):
            normalized = norm_symbol(candidate)
            if normalized in universe and normalized not in seen and normalized != base:
                rows.append(
                    {
                        "comparison_symbol": universe[normalized],
                        "relationship_type": relationship_type,
                        "source": "seed_matched_provider_universe_requires_recent_correlation",
                    }
                )
                seen.add(normalized)
    base_meta = metadata.get(base_symbol) or metadata.get(base) or {}
    for key in ("index_etf", "sector_etf", "top_peers", "options_liquidity_proxies"):
        values = base_meta.get(key, [])
        if isinstance(values, str):
            values = [values]
        for candidate in values:
            normalized = norm_symbol(str(candidate))
            if normalized in universe and normalized not in seen and normalized != base:
                rows.append(
                    {
                        "comparison_symbol": universe[normalized],
                        "relationship_type": "uncertain",
                        "source": "metadata_peer_requires_recent_correlation_and_session_validation",
                    }
                )
                seen.add(normalized)
    return rows


def latest_swing_event(candles: list[Candle], lookback: int = 2) -> dict[str, Any] | None:
    if len(candles) < lookback * 2 + 3:
        return None
    events: list[dict[str, Any]] = []
    for idx in range(lookback, len(candles) - lookback):
        cur = candles[idx]
        peers = candles[idx - lookback : idx] + candles[idx + 1 : idx + 1 + lookback]
        if cur.high > max(row.high for row in peers):
            previous = next((event for event in reversed(events) if event["kind"] == "high"), None)
            swing_type = "HH" if previous and cur.high > previous["level"] else "LH"
            events.append(
                {
                    "kind": "high",
                    "idx": idx,
                    "time": cur.time,
                    "swing_type": swing_type,
                    "level": cur.high,
                    "previous_level": previous["level"] if previous else None,
                    "swept_side": "buy_side_liquidity" if previous and swing_type == "HH" else "none",
                }
            )
        if cur.low < min(row.low for row in peers):
            previous = next((event for event in reversed(events) if event["kind"] == "low"), None)
            swing_type = "LL" if previous and cur.low < previous["level"] else "HL"
            events.append(
                {
                    "kind": "low",
                    "idx": idx,
                    "time": cur.time,
                    "swing_type": swing_type,
                    "level": cur.low,
                    "previous_level": previous["level"] if previous else None,
                    "swept_side": "sell_side_liquidity" if previous and swing_type == "LL" else "none",
                }
            )
    return events[-1] if events else None


def invert_swing(swing_type: str) -> str:
    return {"HH": "LL", "LL": "HH", "HL": "LH", "LH": "HL"}.get(swing_type, swing_type)


def fail_row(
    base_symbol: str,
    comparison_symbol: str,
    relationship_type: str,
    timeframe: str,
    session: str,
    reason: str,
    normalized: bool = False,
) -> dict[str, Any]:
    return {
        "base_symbol": base_symbol,
        "comparison_symbol": comparison_symbol,
        "relationship_type": relationship_type,
        "relationship_confidence": 0.0,
        "timeframe": timeframe,
        "session": session,
        "smt_signal": "none",
        "base_swing_type": "n/a",
        "base_level": None,
        "comparison_swing_type": "n/a",
        "comparison_level": None,
        "swept_side": "none",
        "normalized_for_inverse_correlation": normalized,
        "near_pd_array": False,
        "pd_array_type": "none",
        "mss_or_cisd_confirmed": False,
        "displacement_confirmed": False,
        "confidence": 0.0,
        "fail_closed_reason": reason,
        "actionable": False,
        "raw_comparison_swing_type": None,
        "raw_comparison_level": None,
        "same_event_time_delta_bars": None,
        "provider_provenance": None,
    }


def detect_smt(
    base_symbol: str,
    comparison_symbol: str,
    relationship_type: str,
    timeframe: str,
    session: str,
    base_candles: list[Candle],
    comparison_candles: list[Candle],
    pd_array: dict[str, Any] | None = None,
    confirmations: dict[str, Any] | None = None,
    provider_provenance: str | None = None,
) -> dict[str, Any]:
    normalized = relationship_type == "negative"
    if relationship_type == "uncertain":
        return fail_row(base_symbol, comparison_symbol, relationship_type, timeframe, session, "relationship_uncertain_recent_correlation_required", normalized)
    if len(base_candles) != len(comparison_candles):
        return fail_row(base_symbol, comparison_symbol, relationship_type, timeframe, session, "timeframe_or_bar_alignment_mismatch", normalized)
    if len(base_candles) < 20:
        return fail_row(base_symbol, comparison_symbol, relationship_type, timeframe, session, "insufficient_candles_for_recent_correlation_and_swing_confirmation", normalized)
    corr = correlation(returns(base_candles), returns(comparison_candles))
    if relationship_type == "positive" and corr < 0.35:
        return fail_row(base_symbol, comparison_symbol, relationship_type, timeframe, session, "recent_positive_correlation_unstable", normalized)
    if relationship_type == "negative" and corr > -0.35:
        return fail_row(base_symbol, comparison_symbol, relationship_type, timeframe, session, "recent_negative_correlation_unstable", normalized)

    base_event = latest_swing_event(base_candles)
    comparison_event = latest_swing_event(comparison_candles)
    if not base_event or not comparison_event:
        return fail_row(base_symbol, comparison_symbol, relationship_type, timeframe, session, "missing_confirmed_swing_pair", normalized)

    same_event_delta = abs(int(base_event["idx"]) - int(comparison_event["idx"]))
    if same_event_delta > 2:
        return fail_row(base_symbol, comparison_symbol, relationship_type, timeframe, session, "swing_events_not_near_same_liquidity_event", normalized)

    raw_comparison_type = comparison_event["swing_type"]
    comparison_type = invert_swing(raw_comparison_type) if normalized else raw_comparison_type
    smt_signal = "none"
    if base_event["swing_type"] == "LL" and comparison_type == "HL" and base_event["swept_side"] == "sell_side_liquidity":
        smt_signal = "bullish_smt"
    elif base_event["swing_type"] == "HH" and comparison_type == "LH" and base_event["swept_side"] == "buy_side_liquidity":
        smt_signal = "bearish_smt"
    else:
        return fail_row(base_symbol, comparison_symbol, relationship_type, timeframe, session, "no_sibling_market_swing_confirmation_failure", normalized)

    pd = pd_array or {}
    conf = confirmations or {}
    has_entry_model = bool(conf.get("mss_or_cisd_confirmed")) and bool(conf.get("displacement_confirmed")) and bool(pd.get("near_pd_array"))
    return {
        "base_symbol": base_symbol,
        "comparison_symbol": comparison_symbol,
        "relationship_type": relationship_type,
        "relationship_confidence": round(abs(corr), 4),
        "timeframe": timeframe,
        "session": session,
        "smt_signal": smt_signal,
        "base_swing_type": base_event["swing_type"],
        "base_level": base_event["level"],
        "comparison_swing_type": comparison_type,
        "comparison_level": comparison_event["level"],
        "swept_side": base_event["swept_side"],
        "normalized_for_inverse_correlation": normalized,
        "near_pd_array": bool(pd.get("near_pd_array", False)),
        "pd_array_type": pd.get("pd_array_type", "none"),
        "mss_or_cisd_confirmed": bool(conf.get("mss_or_cisd_confirmed", False)),
        "displacement_confirmed": bool(conf.get("displacement_confirmed", False)),
        "confidence": 0.35 if has_entry_model else 0.2,
        "fail_closed_reason": None if has_entry_model else "confirmation_only_waiting_for_mss_cisd_displacement_and_pda_entry_model",
        "actionable": False,
        "raw_comparison_swing_type": raw_comparison_type,
        "raw_comparison_level": comparison_event["level"],
        "same_event_time_delta_bars": same_event_delta,
        "provider_provenance": provider_provenance,
    }


def empty_regime_stats(coverage: list[str], reason: str) -> dict[str, dict[str, Any]]:
    return {
        regime: {
            "win_rate": None,
            "trade_count": 0,
            "expectancy": None,
            "sample_window": None,
            "instrument_coverage": coverage,
            "confidence": 0.0,
            "fail_closed_reason": reason,
        }
        for regime in ["trend", "range", "transition", "stress", "other"]
    }


def build_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    base_symbol = payload["base_symbol"]
    timeframe = payload["timeframe"]
    session = payload.get("session", "n/a")
    provider_universe = payload.get("provider_universe", [])
    candles = payload.get("candles", {})
    rows = []
    for relation in resolve_related(base_symbol, provider_universe, payload.get("symbol_metadata", {})):
        comparison = relation["comparison_symbol"]
        if base_symbol not in candles or comparison not in candles:
            rows.append(
                fail_row(
                    base_symbol,
                    comparison,
                    relation["relationship_type"],
                    timeframe,
                    session,
                    "missing_base_or_comparison_candles",
                    relation["relationship_type"] == "negative",
                )
            )
            continue
        rows.append(
            detect_smt(
                base_symbol,
                comparison,
                relation["relationship_type"],
                timeframe,
                session,
                parse_candles(candles[base_symbol]),
                parse_candles(candles[comparison]),
                payload.get("pd_array", {}).get(comparison, {}),
                payload.get("confirmations", {}).get(comparison, {}),
                payload.get("provider_provenance", {}).get(comparison),
            )
        )
    return rows


def build_packet(payload: dict[str, Any]) -> dict[str, Any]:
    if "scenarios" in payload:
        scenario_rows: list[dict[str, Any]] = []
        for scenario in payload["scenarios"]:
            scenario_rows.extend(build_rows(scenario))
        rows = scenario_rows
        coverage = payload.get("coverage_target", ["NQ/ES/YM", "EURUSD/GBPUSD/DXY", "XAUUSD/XAGUSD/DXY", "BTC/ETH"])
    else:
        rows = build_rows(payload)
        coverage = payload.get("coverage_target", ["NQ/ES/YM", "EURUSD/GBPUSD/DXY", "XAUUSD/XAGUSD/DXY", "BTC/ETH"])
    return {
        "factor_name": "smt_confirmation_failure_v1",
        "factor_version": "2026-05-12",
        "promotion_allowed": False,
        "trade_usable": False,
        "actionable": False,
        "branch_path_contract": {
            "main_regime": "CrossMarketConfirmation",
            "sub_regime": "LiquiditySweepValidation",
            "sub_sub_regime_or_profit_factor": "SMTConfirmationFailure",
            "profit_factor": "SMTConfirmationOnly",
            "regime_profit_branch_path": "CrossMarketConfirmation -> LiquiditySweepValidation -> SMTConfirmationFailure -> SMTConfirmationOnly",
        },
        "coverage_target": coverage,
        "rows": rows,
        "per_regime_statistics": empty_regime_stats(coverage, "fixture_material_not_provider_backed_no_outcome_labels"),
        "quality_gate": {
            "quality_weight": 0.0,
            "allowed_feedback_targets": ["schema_contract", "factor_material_preflight", "provider_backed_training_next"],
            "downstream_allowed": False,
            "fail_closed_reason": "fixture_material_not_provider_backed_no_regime_conditioned_outcomes",
        },
    }


def write_csv(packet: dict[str, Any], path: Path) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROW_FIELDS)
        writer.writeheader()
        for row in packet["rows"]:
            writer.writerow({field: row.get(field) for field in ROW_FIELDS})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--csv-output", type=Path, required=True)
    args = parser.parse_args()
    packet = build_packet(json.loads(args.input.read_text()))
    args.json_output.write_text(json.dumps(packet, indent=2) + "\n")
    write_csv(packet, args.csv_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
