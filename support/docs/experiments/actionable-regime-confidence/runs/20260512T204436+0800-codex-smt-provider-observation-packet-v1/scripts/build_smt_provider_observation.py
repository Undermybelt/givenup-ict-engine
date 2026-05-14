#!/usr/bin/env python3
"""Build a provider-backed ICT SMT observation packet.

This script is intentionally local-artifact only. It reuses existing candle
JSON files and keeps SMT as confirmation evidence, never as an actionable plan.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[4]
BTC_1H = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T200516+0800-codex-native-crypto-full-chain-retry-v1/data/BOARD_A_NATIVE_BINANCE_BTC_200516/1h.json"
ETH_1H = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T124245+0800-codex-local-nonbtc-mtf-chain-probe-v1/provider-data-json/eth_usdt_crypto_nonbtc_1h_4h_1d/eth_usdt_crypto_nonbtc_1h_4h_1d-1h.json"
REQUIRED_LANES = [
    ("NQ", "ES", "YM"),
    ("EURUSD", "GBPUSD", "DXY"),
    ("XAUUSD", "XAGUSD", "DXY"),
    ("BTC", "ETH"),
]
REGIMES = ["trend", "range", "transition", "stress", "other"]


@dataclass(frozen=True)
class Candle:
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float


def load_json_candles(path: Path) -> list[Candle]:
    data = json.loads(path.read_text())
    rows = []
    for row in data:
        rows.append(
            Candle(
                time=str(row.get("timestamp") or row.get("time")),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row.get("volume", 0.0)),
            )
        )
    return rows


def align(base: list[Candle], comparison: list[Candle]) -> tuple[list[Candle], list[Candle]]:
    comp_by_time = {c.time: c for c in comparison}
    a, b = [], []
    for candle in base:
        other = comp_by_time.get(candle.time)
        if other:
            a.append(candle)
            b.append(other)
    return a, b


def returns(candles: list[Candle]) -> list[float]:
    out = []
    for prev, cur in zip(candles, candles[1:]):
        out.append(0.0 if prev.close == 0 else (cur.close - prev.close) / prev.close)
    return out


def corr(a: list[float], b: list[float]) -> float:
    if len(a) < 20 or len(a) != len(b):
        return 0.0
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return 0.0 if da == 0 or db == 0 else num / (da * db)


def swing_points(candles: list[Candle], lookback: int = 2) -> list[dict[str, Any]]:
    pivots: list[dict[str, Any]] = []
    prior_high = None
    prior_low = None
    for i in range(lookback, len(candles) - lookback):
        left = candles[i - lookback : i]
        right = candles[i + 1 : i + 1 + lookback]
        cur = candles[i]
        if cur.high > max(c.high for c in left + right):
            if prior_high is not None:
                swing_type = "HH" if cur.high > prior_high else "LH"
                pivots.append(
                    {
                        "kind": "high",
                        "index": i,
                        "time": cur.time,
                        "level": cur.high,
                        "swing_type": swing_type,
                        "swept_side": "buy_side_liquidity" if swing_type == "HH" else "none",
                    }
                )
            prior_high = cur.high
        if cur.low < min(c.low for c in left + right):
            if prior_low is not None:
                swing_type = "LL" if cur.low < prior_low else "HL"
                pivots.append(
                    {
                        "kind": "low",
                        "index": i,
                        "time": cur.time,
                        "level": cur.low,
                        "swing_type": swing_type,
                        "swept_side": "sell_side_liquidity" if swing_type == "LL" else "none",
                    }
                )
            prior_low = cur.low
    return sorted(pivots, key=lambda row: row["index"])


def detect_events(
    base_symbol: str,
    comparison_symbol: str,
    base: list[Candle],
    comparison: list[Candle],
    event_window_bars: int = 3,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base_swings = swing_points(base)
    comp_swings = swing_points(comparison)
    comp_by_kind = {"high": [x for x in comp_swings if x["kind"] == "high"], "low": [x for x in comp_swings if x["kind"] == "low"]}
    recent_correlation = corr(returns(base[-720:]), returns(comparison[-720:]))
    stable = recent_correlation >= 0.35
    rows = []
    for base_swing in base_swings:
        candidates = [
            s
            for s in comp_by_kind[base_swing["kind"]]
            if abs(int(s["index"]) - int(base_swing["index"])) <= event_window_bars
        ]
        if not candidates:
            continue
        comp_swing = min(candidates, key=lambda s: abs(int(s["index"]) - int(base_swing["index"])))
        signal = "none"
        if base_swing["swing_type"] == "LL" and comp_swing["swing_type"] == "HL":
            signal = "bullish_smt"
        elif base_swing["swing_type"] == "HH" and comp_swing["swing_type"] == "LH":
            signal = "bearish_smt"
        if signal == "none":
            continue
        fail = None if stable else "recent_positive_correlation_unstable"
        rows.append(
            {
                "base_symbol": base_symbol,
                "comparison_symbol": comparison_symbol,
                "relationship_type": "positive",
                "relationship_confidence": round(abs(recent_correlation), 4) if stable else 0.0,
                "timeframe": "1h",
                "session": "crypto_24x7",
                "comparison_timeframe": "1h",
                "comparison_session": "crypto_24x7",
                "timeframe_aligned": True,
                "session_overlap": True,
                "correlation_window_bars": min(719, len(base) - 1, len(comparison) - 1),
                "recent_correlation": round(recent_correlation, 4),
                "smt_signal": signal if not fail else "none",
                "base_swing_type": base_swing["swing_type"],
                "base_event_time": base_swing["time"],
                "base_level": base_swing["level"],
                "comparison_swing_type": comp_swing["swing_type"],
                "comparison_event_time": comp_swing["time"],
                "comparison_level": comp_swing["level"],
                "event_window_bars": event_window_bars,
                "event_time_delta_bars": abs(int(base_swing["index"]) - int(comp_swing["index"])),
                "same_event_window_confirmed": True,
                "swept_side": base_swing["swept_side"],
                "normalized_for_inverse_correlation": False,
                "raw_comparison_swing_type": comp_swing["swing_type"],
                "raw_comparison_level": comp_swing["level"],
                "near_pd_array": False,
                "pd_array_type": "none",
                "mss_or_cisd_confirmed": False,
                "displacement_confirmed": False,
                "provider_provenance": "BTC:BOARD_A_NATIVE_BINANCE_BTC_200516/1h.json;ETH:eth_usdt_crypto_nonbtc_1h_4h_1d-1h.json",
                "evidence_source": "existing_local_provider_json_same_timeframe_aligned",
                "confidence": 0.0,
                "fail_closed_reason": fail or "confirmation_only_waiting_for_mss_cisd_displacement_pda_and_labeled_outcome",
                "confirmation_role": "confirmation_only",
                "actionable": False,
            }
        )
    summary = {
        "aligned_row_count": len(base),
        "base_swing_count": len(base_swings),
        "comparison_swing_count": len(comp_swings),
        "recent_correlation": round(recent_correlation, 4),
        "recent_correlation_stable": stable,
        "candidate_smt_event_count": len(rows),
        "nonzero_trade_outcome_count": 0,
    }
    return rows, summary


def fail_closed_row(base: str, comparison: str, reason: str) -> dict[str, Any]:
    return {
        "base_symbol": base,
        "comparison_symbol": comparison,
        "relationship_type": "uncertain",
        "relationship_confidence": 0.0,
        "timeframe": "1h",
        "session": "unknown",
        "comparison_timeframe": "1h",
        "comparison_session": "unknown",
        "timeframe_aligned": True,
        "session_overlap": False,
        "correlation_window_bars": 0,
        "recent_correlation": 0.0,
        "smt_signal": "none",
        "base_swing_type": "n/a",
        "base_event_time": None,
        "base_level": None,
        "comparison_swing_type": "n/a",
        "comparison_event_time": None,
        "comparison_level": None,
        "event_window_bars": 3,
        "event_time_delta_bars": None,
        "same_event_window_confirmed": False,
        "swept_side": "none",
        "normalized_for_inverse_correlation": comparison == "DXY",
        "raw_comparison_swing_type": None,
        "raw_comparison_level": None,
        "near_pd_array": False,
        "pd_array_type": "none",
        "mss_or_cisd_confirmed": False,
        "displacement_confirmed": False,
        "provider_provenance": None,
        "evidence_source": "required_lane_missing_local_aligned_provider_candles",
        "confidence": 0.0,
        "fail_closed_reason": reason,
        "confirmation_role": "confirmation_only",
        "actionable": False,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    (ROOT / "materials").mkdir(exist_ok=True)
    (ROOT / "provider-data").mkdir(exist_ok=True)
    btc = load_json_candles(BTC_1H)
    eth = load_json_candles(ETH_1H)
    btc_aligned, eth_aligned = align(btc, eth)
    rows, observation = detect_events("BTC", "ETH", btc_aligned, eth_aligned)
    fail_rows = [
        fail_closed_row("NQ", "ES/YM", "missing_local_same_timeframe_aligned_provider_candles_for_required_lane"),
        fail_closed_row("EURUSD", "GBPUSD/DXY", "missing_local_same_timeframe_aligned_provider_candles_for_required_lane"),
        fail_closed_row("XAUUSD", "XAGUSD/DXY", "missing_local_same_timeframe_aligned_provider_candles_for_required_lane"),
    ]
    if not rows:
        rows = [fail_closed_row("BTC", "ETH", "no_provider_backed_same_event_smt_candidates")]
    all_rows = rows + fail_rows
    per_regime = {
        regime: {
            "win_rate": None,
            "trade_count": 0,
            "expectancy": None,
            "sample_window": {
                "start": btc_aligned[0].time if btc_aligned else None,
                "end": btc_aligned[-1].time if btc_aligned else None,
            },
            "instrument_coverage": ["BTC/ETH"] if btc_aligned else [],
            "confidence": 0.0,
            "fail_closed_reason": "no_mss_cisd_displacement_pda_labeled_outcomes",
        }
        for regime in REGIMES
    }
    packet = {
        "factor_name": "smt_provider_observation_packet",
        "factor_version": "v1",
        "generated_at": "2026-05-12T20:44:36+08:00",
        "branch_path": "Transition -> LiquiditySweepConfirmationFailure -> smt_divergence_confirmation_only -> smt_provider_observation_packet:v1",
        "definition": "ICT SMT divergence is sibling-market confirmation failure around the same liquidity sweep/swing event; it is confirmation only.",
        "coverage_target": REQUIRED_LANES,
        "provider_request_readback": {
            "fetch_performed": False,
            "reused_existing_local_provider_artifacts": True,
            "btc_1h_path": str(BTC_1H.relative_to(REPO)),
            "eth_1h_path": str(ETH_1H.relative_to(REPO)),
            "btc_rows": len(btc),
            "eth_rows": len(eth),
            "aligned_rows": len(btc_aligned),
            "requested_timeframe": "1h",
            "returned_timeframe": "1h",
            "provider_cap_or_error": None,
        },
        "observation_summary": observation,
        "rows": all_rows,
        "per_regime_statistics": per_regime,
        "quality_gate": {
            "smt_confirmation_only": True,
            "standalone_actionable_allowed": False,
            "provider_backed_btc_eth_observed": bool(btc_aligned),
            "all_required_lanes_provider_backed": False,
            "nonzero_per_regime_outcomes": False,
            "quality_weight": 0.0,
            "downstream_allowed": False,
            "pre_bayes_filter_allowed": False,
            "bbn_learning_allowed": False,
            "catboost_learning_allowed": False,
            "execution_tree_branch_weight_update_allowed": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        },
    }
    (ROOT / "provider-data/provider_request_readback.json").write_text(json.dumps(packet["provider_request_readback"], indent=2) + "\n")
    (ROOT / "materials/smt_provider_observation_packet.json").write_text(json.dumps(packet, indent=2) + "\n")
    (ROOT / "materials/smt_provider_observation_summary.json").write_text(json.dumps(observation, indent=2) + "\n")
    write_csv(ROOT / "materials/smt_provider_observation_rows.csv", all_rows)
    print(json.dumps({"rows": len(all_rows), **observation, "downstream_allowed": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
