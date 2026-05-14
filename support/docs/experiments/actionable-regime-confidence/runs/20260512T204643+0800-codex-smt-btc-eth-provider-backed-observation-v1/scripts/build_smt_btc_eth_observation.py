#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[4]
BRANCH_PATH = "Transition -> LiquiditySweepConfirmationFailure -> smt_divergence_confirmation_only -> smt_relationship_resolver:btc_eth_1h_v1"

RUN_115500 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1/provider-csv"
RUN_125500 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T125500+0800-codex-eth-six-provider-aq-authority-probe-v1/provider-csv"

PAIRS = [
    ("binance", "Binance BTCUSDT/ETHUSDT 1h", RUN_115500 / "binance_btcusdt_1h.csv", RUN_125500 / "binance_ethusdt_1h.csv"),
    ("bybit", "Bybit linear BTCUSDT/ETHUSDT 1h", RUN_115500 / "bybit_btcusdt_linear_1h.csv", RUN_125500 / "bybit_ethusdt_linear_1h.csv"),
    ("kraken", "Kraken XBTUSD/ETHUSD 1h", RUN_115500 / "kraken_xbtusd_1h.csv", RUN_125500 / "kraken_ethusd_1h.csv"),
    ("tradingviewremix", "TradingViewRemix BTC/ETH 1h", RUN_115500 / "tvr_binance_btcusdt_1h.csv", RUN_125500 / "tvr_eth_usd_1h.csv"),
    ("yfinance", "YF BTC-USD/ETH-USD 1h", RUN_115500 / "yfinance_btc_usd_1h.csv", RUN_125500 / "yfinance_eth_usd_1h.csv"),
    ("ibkr", "IBKR PAXOS BTC/ETH aggtrades 1h", RUN_115500 / "BTC_1h_aggtrades.csv", RUN_125500 / "ibkr_eth_paxos_aggtrades_1h.csv"),
]


@dataclass(frozen=True)
class Candle:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def parse_ts(raw: str) -> datetime:
    text = raw.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.replace(minute=0, second=0, microsecond=0)


def read_csv(path: Path) -> dict[datetime, Candle]:
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    out: dict[datetime, Candle] = {}
    for row in rows:
        raw_ts = row.get("date") or row.get("ts")
        if not raw_ts:
            continue
        try:
            ts = parse_ts(raw_ts)
            out[ts] = Candle(
                ts=ts,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row.get("volume") or 0.0),
            )
        except Exception:
            continue
    return dict(sorted(out.items()))


def returns(candles: list[Candle]) -> list[float]:
    vals = []
    for prev, cur in zip(candles, candles[1:]):
        vals.append(0.0 if prev.close == 0 else (cur.close - prev.close) / prev.close)
    return vals


def correlation(a: list[float], b: list[float]) -> float:
    if len(a) < 30 or len(a) != len(b):
        return 0.0
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return 0.0 if da == 0 or db == 0 else num / (da * db)


def pivots(candles: list[Candle], lookback: int = 2) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i in range(lookback, len(candles) - lookback):
        cur = candles[i]
        left = candles[i - lookback : i]
        right = candles[i + 1 : i + 1 + lookback]
        if cur.high > max(c.high for c in left + right):
            out.append({"idx": i, "ts": cur.ts, "kind": "high", "level": cur.high})
        if cur.low < min(c.low for c in left + right):
            out.append({"idx": i, "ts": cur.ts, "kind": "low", "level": cur.low})
    last_by_kind: dict[str, dict[str, Any]] = {}
    labelled = []
    for p in out:
        prev = last_by_kind.get(p["kind"])
        if p["kind"] == "high":
            swing_type = "HH" if prev and p["level"] > prev["level"] else "LH"
        else:
            swing_type = "LL" if prev and p["level"] < prev["level"] else "HL"
        labelled.append({**p, "swing_type": swing_type, "previous_level": prev["level"] if prev else None})
        last_by_kind[p["kind"]] = p
    return labelled


def find_peer_pivot(peer_pivots: list[dict[str, Any]], idx: int, kind: str, tolerance: int = 3) -> dict[str, Any] | None:
    candidates = [p for p in peer_pivots if p["kind"] == kind and abs(p["idx"] - idx) <= tolerance]
    if not candidates:
        return None
    return min(candidates, key=lambda p: abs(p["idx"] - idx))


def classify_regime(base: list[Candle], idx: int) -> str:
    if idx < 24:
        return "other"
    window = base[idx - 24 : idx]
    start = window[0].close
    end = window[-1].close
    if start == 0:
        return "other"
    move = abs((end - start) / start)
    avg_range = mean((c.high - c.low) / c.close for c in window if c.close)
    if avg_range > 0.018:
        return "stress"
    if move > 0.025:
        return "trend"
    if move < 0.008:
        return "range"
    return "transition"


def provider_packet(provider_id: str, label: str, btc_path: Path, eth_path: Path) -> dict[str, Any]:
    btc_map = read_csv(btc_path)
    eth_map = read_csv(eth_path)
    aligned_ts = sorted(set(btc_map) & set(eth_map))
    btc = [btc_map[t] for t in aligned_ts]
    eth = [eth_map[t] for t in aligned_ts]
    corr = correlation(returns(btc), returns(eth))
    btc_pivots = pivots(btc)
    eth_pivots = pivots(eth)
    events: list[dict[str, Any]] = []
    for p in btc_pivots:
        peer = find_peer_pivot(eth_pivots, p["idx"], p["kind"])
        if not peer:
            continue
        signal = "none"
        if p["swing_type"] == "LL" and peer["swing_type"] == "HL":
            signal = "bullish_smt"
        elif p["swing_type"] == "HH" and peer["swing_type"] == "LH":
            signal = "bearish_smt"
        if signal == "none":
            continue
        events.append(
            {
                "provider_id": provider_id,
                "provider_provenance": label,
                "event_time": p["ts"].isoformat(),
                "base_symbol": "BTC",
                "comparison_symbol": "ETH",
                "relationship_type": "positive",
                "relationship_confidence": round(max(0.0, corr), 4),
                "timeframe": "1h",
                "session": "crypto_24x7",
                "smt_signal": signal,
                "base_swing_type": p["swing_type"],
                "base_level": round(float(p["level"]), 8),
                "comparison_swing_type": peer["swing_type"],
                "comparison_level": round(float(peer["level"]), 8),
                "swept_side": "sell_side_liquidity" if signal == "bullish_smt" else "buy_side_liquidity",
                "normalized_for_inverse_correlation": False,
                "near_pd_array": False,
                "pd_array_type": "none",
                "mss_or_cisd_confirmed": False,
                "displacement_confirmed": False,
                "regime_label": classify_regime(btc, p["idx"]),
                "regime_profit_branch_path": BRANCH_PATH,
                "confidence": 0.15 if corr >= 0.55 else 0.0,
                "actionable": False,
                "fail_closed_reason": "confirmation_only_missing_mss_cisd_displacement_pda_and_outcome_labels",
            }
        )
    return {
        "provider_id": provider_id,
        "provider_provenance": label,
        "btc_path": str(btc_path.relative_to(REPO)),
        "eth_path": str(eth_path.relative_to(REPO)),
        "btc_rows": len(btc_map),
        "eth_rows": len(eth_map),
        "aligned_rows": len(aligned_ts),
        "returned_span": {
            "start": aligned_ts[0].isoformat() if aligned_ts else None,
            "end": aligned_ts[-1].isoformat() if aligned_ts else None,
        },
        "relationship_type": "positive",
        "relationship_confidence": round(max(0.0, corr), 4),
        "correlation": round(corr, 6),
        "correlation_stable": corr >= 0.55,
        "smt_event_count": len(events),
        "provider_cap_or_error": None if aligned_ts else "no_overlap",
        "events": events,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    provider_packets = [provider_packet(*pair) for pair in PAIRS]
    events = [event for packet in provider_packets for event in packet["events"]]
    regimes = {name: {"event_count": 0, "trade_count": 0, "confidence": 0.0} for name in ["trend", "range", "transition", "stress", "other"]}
    for event in events:
        regimes[event["regime_label"]]["event_count"] += 1
    fold_keys = sorted({event["event_time"][:7] for event in events})
    summary = {
        "factor_name": "smt_relationship_resolver",
        "factor_version": "2026-05-12.provider-backed-observation.v1",
        "branch_path_contract": {
            "main_regime": "Transition",
            "sub_regime": "LiquiditySweepConfirmationFailure",
            "sub_sub_regime_or_profit_factor": "smt_divergence_confirmation_only",
            "profit_factor": "smt_relationship_resolver:btc_eth_1h_v1",
            "regime_profit_branch_path": BRANCH_PATH,
        },
        "input_policy": "reuse_existing_provider_csv_only_no_new_fetch",
        "provider_packets": [{k: v for k, v in p.items() if k != "events"} for p in provider_packets],
        "aggregate": {
            "provider_count": len(provider_packets),
            "providers_with_overlap": sum(1 for p in provider_packets if p["aligned_rows"] > 0),
            "providers_with_stable_relationship": sum(1 for p in provider_packets if p["correlation_stable"]),
            "total_aligned_rows": sum(p["aligned_rows"] for p in provider_packets),
            "smt_event_count": len(events),
            "branch_keyed_trade_count": 0,
            "fold_count": len(fold_keys),
            "fold_keys": fold_keys,
        },
        "per_regime_statistics": regimes,
        "quality_gate": {
            "runtime_provider_observations_present": len(events) > 0,
            "per_regime_profitability_statistics_present": False,
            "observation_quality_weight": 0.2 if events else 0.0,
            "learning_quality_weight": 0.0,
            "auto_quant_dispatch_allowed": False,
            "pre_bayes_filter_allowed": False,
            "bbn_learning_allowed": False,
            "catboost_learning_allowed": False,
            "execution_tree_branch_weight_update_allowed": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "fail_closed_reason": "provider_backed_smt_events_are_confirmation_only_without_mss_cisd_displacement_pda_or_outcome_labels",
        },
    }
    manifest_rows = [
        {
            "provider_id": p["provider_id"],
            "provider_provenance": p["provider_provenance"],
            "btc_path": p["btc_path"],
            "eth_path": p["eth_path"],
            "btc_rows": p["btc_rows"],
            "eth_rows": p["eth_rows"],
            "aligned_rows": p["aligned_rows"],
            "span_start": p["returned_span"]["start"],
            "span_end": p["returned_span"]["end"],
            "correlation": p["correlation"],
            "smt_event_count": p["smt_event_count"],
        }
        for p in provider_packets
    ]
    write_csv(ROOT / "inputs/provider_file_manifest.csv", manifest_rows)
    write_csv(ROOT / "summaries/smt_btc_eth_provider_observation_events.csv", events)
    (ROOT / "summaries/smt_btc_eth_provider_observation_v1.json").write_text(json.dumps(summary, indent=2) + "\n")
    assert summary["aggregate"]["provider_count"] == 6
    assert summary["aggregate"]["providers_with_overlap"] >= 4
    assert summary["aggregate"]["smt_event_count"] > 0
    assert summary["quality_gate"]["learning_quality_weight"] == 0.0
    assert summary["quality_gate"]["promotion_allowed"] is False
    print(json.dumps(summary["aggregate"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
