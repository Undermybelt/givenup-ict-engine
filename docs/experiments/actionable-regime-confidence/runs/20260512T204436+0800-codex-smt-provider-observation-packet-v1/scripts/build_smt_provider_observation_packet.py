#!/usr/bin/env python3
"""Build a provider-backed SMT observation packet.

This script is intentionally observation-only. SMT is treated as a sibling-market
swing/liquidity confirmation failure, not as a standalone trade signal.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

import yfinance as yf


ROOT = Path(__file__).resolve().parents[1]
PROVIDER_DATA = ROOT / "provider-data"
MATERIALS = ROOT / "materials"


@dataclass(frozen=True)
class PairSpec:
    family: str
    base_symbol: str
    base_provider_symbol: str
    comparison_symbol: str
    comparison_provider_symbol: str
    relationship_type: str
    timeframe: str
    session: str
    interval: str
    period: str


PAIR_SPECS = [
    PairSpec("indices", "NQ", "NQ=F", "ES", "ES=F", "positive", "5m", "NY_AM", "5m", "5d"),
    PairSpec("indices", "NQ", "NQ=F", "YM", "YM=F", "positive", "5m", "NY_AM", "5m", "5d"),
    PairSpec("forex", "EURUSD", "EURUSD=X", "GBPUSD", "GBPUSD=X", "positive", "15m", "London_NY_overlap", "15m", "5d"),
    PairSpec("forex", "EURUSD", "EURUSD=X", "DXY", "DX-Y.NYB", "negative", "15m", "London_NY_overlap", "15m", "5d"),
    PairSpec("metals", "XAUUSD", "GC=F", "XAGUSD", "SI=F", "positive", "15m", "NY_AM", "15m", "5d"),
    PairSpec("metals", "XAUUSD", "GC=F", "DXY", "DX-Y.NYB", "negative", "15m", "NY_AM", "15m", "5d"),
    PairSpec("crypto", "BTC", "BTC-USD", "ETH", "ETH-USD", "positive", "1h", "crypto_24x7", "1h", "60d"),
]


def fetch_candles(provider_symbol: str, interval: str, period: str) -> tuple[list[dict[str, Any]], str | None]:
    try:
        frame = yf.download(
            provider_symbol,
            interval=interval,
            period=period,
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except Exception as exc:  # provider/network fault, not factor failure
        return [], f"provider_error:{type(exc).__name__}:{exc}"
    if frame.empty:
        return [], "provider_empty"
    if isinstance(frame.columns, type(frame.index)):
        pass
    if hasattr(frame.columns, "nlevels") and frame.columns.nlevels > 1:
        frame.columns = [str(col[0]) for col in frame.columns]
    rows: list[dict[str, Any]] = []
    for timestamp, row in frame.dropna().iterrows():
        try:
            rows.append(
                {
                    "time": timestamp.isoformat(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row.get("Volume", 0.0)),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return rows, None if rows else "provider_no_usable_ohlcv"


def align_by_time(base: list[dict[str, Any]], comp: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    comp_by_time = {row["time"]: row for row in comp}
    return [(row, comp_by_time[row["time"]]) for row in base if row["time"] in comp_by_time]


def close_returns(rows: list[dict[str, Any]]) -> list[float]:
    out = []
    for prev, cur in zip(rows, rows[1:]):
        if prev["close"] == 0:
            out.append(0.0)
        else:
            out.append((cur["close"] - prev["close"]) / prev["close"])
    return out


def correlation(a: list[float], b: list[float]) -> float:
    if len(a) < 10 or len(a) != len(b):
        return 0.0
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return 0.0 if da == 0 or db == 0 else num / (da * db)


def classify_regime(rows: list[dict[str, Any]], index: int, window: int = 48) -> str:
    start = max(0, index - window)
    sample = rows[start : index + 1]
    rets = close_returns(sample)
    if len(rets) < 10:
        return "other"
    avg = mean(rets)
    variance = mean((ret - avg) ** 2 for ret in rets)
    vol = math.sqrt(variance)
    drift = (sample[-1]["close"] - sample[0]["close"]) / sample[0]["close"] if sample[0]["close"] else 0.0
    if vol > 0.008:
        return "stress"
    if abs(drift) > max(0.008, vol * 2.0):
        return "trend"
    if abs(drift) < max(0.003, vol * 0.8):
        return "range"
    return "transition"


def pivots(rows: list[dict[str, Any]], lookback: int = 2) -> list[dict[str, Any]]:
    out = []
    for index in range(lookback, len(rows) - lookback):
        left = rows[index - lookback : index]
        right = rows[index + 1 : index + 1 + lookback]
        cur = rows[index]
        if cur["high"] > max(item["high"] for item in left + right):
            out.append({"index": index, "time": cur["time"], "kind": "high", "level": cur["high"]})
        if cur["low"] < min(item["low"] for item in left + right):
            out.append({"index": index, "time": cur["time"], "kind": "low", "level": cur["low"]})
    last_by_kind: dict[str, dict[str, Any]] = {}
    classified = []
    for pivot in out:
        previous = last_by_kind.get(pivot["kind"])
        if previous is None:
            last_by_kind[pivot["kind"]] = pivot
            continue
        if pivot["kind"] == "high":
            if abs(pivot["level"] - previous["level"]) <= max(1e-9, abs(previous["level"]) * 0.0002):
                swing_type = "equal_high"
            else:
                swing_type = "HH" if pivot["level"] > previous["level"] else "LH"
        else:
            if abs(pivot["level"] - previous["level"]) <= max(1e-9, abs(previous["level"]) * 0.0002):
                swing_type = "equal_low"
            else:
                swing_type = "LL" if pivot["level"] < previous["level"] else "HL"
        classified.append({**pivot, "swing_type": swing_type, "previous_level": previous["level"]})
        last_by_kind[pivot["kind"]] = pivot
    return classified


def invert_swing(swing_type: str) -> str:
    return {
        "HH": "LL",
        "LL": "HH",
        "HL": "LH",
        "LH": "HL",
        "equal_high": "equal_low",
        "equal_low": "equal_high",
    }.get(swing_type, swing_type)


def find_near(pivot: dict[str, Any], comparison_pivots: list[dict[str, Any]], bars: int = 3) -> dict[str, Any] | None:
    same_kind = [item for item in comparison_pivots if item["kind"] == pivot["kind"]]
    if not same_kind:
        return None
    near = sorted(same_kind, key=lambda item: abs(item["index"] - pivot["index"]))
    return near[0] if abs(near[0]["index"] - pivot["index"]) <= bars else None


def stable_relationship(relationship_type: str, corr: float) -> tuple[bool, str | None]:
    if relationship_type == "positive" and corr < 0.25:
        return False, "recent_positive_correlation_unstable"
    if relationship_type == "negative" and corr > -0.25:
        return False, "recent_negative_correlation_unstable"
    return True, None


def observation_rows(spec: PairSpec, base: list[dict[str, Any]], comp: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    aligned_pairs = align_by_time(base, comp)
    aligned_base = [pair[0] for pair in aligned_pairs]
    aligned_comp = [pair[1] for pair in aligned_pairs]
    if len(aligned_pairs) < 40:
        return [], {"fail_closed_reason": "insufficient_same_timeframe_aligned_candles", "aligned_rows": len(aligned_pairs), "correlation": 0.0}
    corr = correlation(close_returns(aligned_base), close_returns(aligned_comp))
    stable, fail = stable_relationship(spec.relationship_type, corr)
    if not stable:
        return [], {"fail_closed_reason": fail, "aligned_rows": len(aligned_pairs), "correlation": corr}

    base_pivots = pivots(aligned_base)
    comp_pivots = pivots(aligned_comp)
    rows = []
    for pivot in base_pivots:
        comp_pivot = find_near(pivot, comp_pivots)
        if comp_pivot is None:
            continue
        base_type = pivot["swing_type"]
        raw_comp_type = comp_pivot["swing_type"]
        comp_type = invert_swing(raw_comp_type) if spec.relationship_type == "negative" else raw_comp_type
        smt_signal = "none"
        swept_side = "none"
        if base_type == "LL":
            swept_side = "sell_side_liquidity"
            if comp_type == "HL":
                smt_signal = "bullish_smt"
        elif base_type == "HH":
            swept_side = "buy_side_liquidity"
            if comp_type == "LH":
                smt_signal = "bearish_smt"
        if smt_signal == "none":
            continue
        regime = classify_regime(aligned_base, pivot["index"])
        rows.append(
            {
                "base_symbol": spec.base_symbol,
                "comparison_symbol": spec.comparison_symbol,
                "relationship_type": spec.relationship_type,
                "relationship_confidence": round(abs(corr), 4),
                "timeframe": spec.timeframe,
                "session": spec.session,
                "comparison_timeframe": spec.timeframe,
                "comparison_session": spec.session,
                "timeframe_aligned": True,
                "session_overlap": True,
                "correlation_window_bars": max(0, len(aligned_pairs) - 1),
                "recent_correlation": round(corr, 4),
                "event_time": pivot["time"],
                "smt_signal": smt_signal,
                "base_swing_type": base_type,
                "base_event_time": pivot["time"],
                "base_level": pivot["level"],
                "comparison_swing_type": comp_type,
                "comparison_event_time": comp_pivot["time"],
                "comparison_level": comp_pivot["level"],
                "event_window_bars": 3,
                "event_time_delta_bars": abs(comp_pivot["index"] - pivot["index"]),
                "same_event_window_confirmed": True,
                "swept_side": swept_side,
                "normalized_for_inverse_correlation": spec.relationship_type == "negative",
                "raw_comparison_swing_type": raw_comp_type,
                "raw_comparison_level": comp_pivot["level"],
                "near_pd_array": False,
                "pd_array_type": "none",
                "mss_or_cisd_confirmed": False,
                "displacement_confirmed": False,
                "regime_bucket": regime,
                "provider_provenance": "yfinance",
                "evidence_source": "provider_backed_same_timeframe_aligned_candles",
                "confidence": 0.25,
                "fail_closed_reason": "confirmation_only_waiting_for_mss_cisd_displacement_and_pda",
                "confirmation_role": "confirmation_only",
                "actionable": False,
            }
        )
    return rows, {"fail_closed_reason": None, "aligned_rows": len(aligned_pairs), "correlation": corr}


def main() -> int:
    MATERIALS.mkdir(parents=True, exist_ok=True)
    PROVIDER_DATA.mkdir(parents=True, exist_ok=True)
    provider_readbacks = []
    all_rows = []
    for spec in PAIR_SPECS:
        base_rows, base_error = fetch_candles(spec.base_provider_symbol, spec.interval, spec.period)
        comp_rows, comp_error = fetch_candles(spec.comparison_provider_symbol, spec.interval, spec.period)
        (PROVIDER_DATA / f"{spec.base_symbol}_{spec.comparison_symbol}_{spec.interval}.json").write_text(
            json.dumps(
                {
                    "spec": asdict(spec),
                    "base_rows": base_rows,
                    "comparison_rows": comp_rows,
                    "base_error": base_error,
                    "comparison_error": comp_error,
                },
                indent=2,
            )
        )
        pair_rows, summary = observation_rows(spec, base_rows, comp_rows) if not base_error and not comp_error else (
            [],
            {"fail_closed_reason": base_error or comp_error, "aligned_rows": 0, "correlation": 0.0},
        )
        all_rows.extend(pair_rows)
        provider_readbacks.append(
            {
                **asdict(spec),
                "provider": "yfinance",
                "provider_requested": True,
                "provider_data_acquired": bool(base_rows and comp_rows),
                "base_rows": len(base_rows),
                "comparison_rows": len(comp_rows),
                "aligned_rows": summary["aligned_rows"],
                "recent_correlation": round(summary["correlation"], 4),
                "smt_event_count": len(pair_rows),
                "provider_unreachable": base_error or comp_error,
                "fail_closed_reason": summary["fail_closed_reason"],
            }
        )

    stats = {}
    for regime in ["trend", "range", "transition", "stress", "other"]:
        event_count = sum(1 for row in all_rows if row["regime_bucket"] == regime)
        stats[regime] = {
            "win_rate": None,
            "trade_count": 0,
            "smt_event_count": event_count,
            "expectancy": None,
            "sample_window": "provider_observation_only_no_entry_model",
            "instrument_coverage": sorted({row["base_symbol"] for row in all_rows if row["regime_bucket"] == regime}),
            "confidence": 0.0,
            "fail_closed_reason": "no_mss_cisd_displacement_pda_or_realized_trade_outcomes",
        }

    packet = {
        "factor_name": "smt_relationship_resolver",
        "factor_version": "2026-05-12.provider-observation.v1",
        "promotion_allowed": False,
        "trade_usable": False,
        "actionable": False,
        "definition": "ICT SMT divergence is a sibling-market swing confirmation failure around the same liquidity/swing event, not a generic correlation label.",
        "branch_path_contract": {
            "main_regime": "Transition",
            "sub_regime": "LiquiditySweepConfirmationFailure",
            "sub_sub_regime_or_profit_factor": "smt_divergence_confirmation_only",
            "profit_factor": "smt_provider_observation_packet:v1",
            "regime_profit_branch_path": "Transition -> LiquiditySweepConfirmationFailure -> smt_divergence_confirmation_only -> smt_provider_observation_packet:v1",
        },
        "coverage_target": ["NQ/ES/YM", "EURUSD/GBPUSD/DXY", "XAUUSD/XAGUSD/DXY", "BTC/ETH"],
        "provider_readbacks": provider_readbacks,
        "rows": all_rows,
        "per_regime_statistics": stats,
        "quality_gate": {
            "quality_weight": 0.0,
            "allowed_feedback_targets": ["smt_event_detector_observation", "provider_relationship_stability"],
            "downstream_allowed": False,
            "fail_closed_reason": "provider_observation_only_no_mss_cisd_displacement_pda_or_realized_trade_outcomes",
        },
    }
    (MATERIALS / "smt_provider_observation_packet.json").write_text(json.dumps(packet, indent=2))
    with (MATERIALS / "smt_provider_observation_rows.csv").open("w", newline="") as handle:
        fieldnames = list(all_rows[0].keys()) if all_rows else [
            "base_symbol",
            "comparison_symbol",
            "relationship_type",
            "relationship_confidence",
            "timeframe",
            "session",
            "event_time",
            "smt_signal",
            "base_level",
            "comparison_level",
            "fail_closed_reason",
            "actionable",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(
        "smt_provider_observation_packet=pass "
        f"provider_pairs={len(provider_readbacks)} rows={len(all_rows)} "
        f"downstream_allowed={packet['quality_gate']['downstream_allowed']} "
        f"quality_weight={packet['quality_gate']['quality_weight']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
