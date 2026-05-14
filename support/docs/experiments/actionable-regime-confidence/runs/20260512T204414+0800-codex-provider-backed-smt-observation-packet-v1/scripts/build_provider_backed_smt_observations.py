#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MATERIALS = ROOT / "materials"
PROVIDER_DATA = ROOT / "provider-data"


@dataclass(frozen=True)
class Candle:
    time: int
    open: float
    high: float
    low: float
    close: float


FAMILIES = [
    {
        "family": "index_futures",
        "provider": "yahoo_chart",
        "timeframe": "15m",
        "session": "provider_regular_and_extended",
        "symbols": {"NQ": "NQ=F", "ES": "ES=F", "YM": "YM=F"},
        "pairs": [("NQ", "ES", "positive"), ("NQ", "YM", "positive"), ("ES", "YM", "positive")],
    },
    {
        "family": "forex",
        "provider": "yahoo_chart",
        "timeframe": "15m",
        "session": "provider_24h_fx",
        "symbols": {"EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "DXY": "DX-Y.NYB"},
        "pairs": [("EURUSD", "GBPUSD", "positive"), ("EURUSD", "DXY", "negative"), ("GBPUSD", "DXY", "negative")],
    },
    {
        "family": "metals",
        "provider": "yahoo_chart",
        "timeframe": "15m",
        "session": "provider_regular_and_extended",
        "symbols": {"XAUUSD": "GC=F", "XAGUSD": "SI=F", "DXY": "DX-Y.NYB"},
        "pairs": [("XAUUSD", "XAGUSD", "positive"), ("XAUUSD", "DXY", "negative"), ("XAGUSD", "DXY", "negative")],
    },
    {
        "family": "crypto_yahoo",
        "provider": "yahoo_chart",
        "timeframe": "15m",
        "session": "crypto_24x7",
        "symbols": {"BTC": "BTC-USD", "ETH": "ETH-USD"},
        "pairs": [("BTC", "ETH", "positive")],
    },
    {
        "family": "crypto_kraken",
        "provider": "kraken_public_ohlc",
        "timeframe": "15m",
        "session": "crypto_24x7",
        "symbols": {"BTC": "XXBTZUSD", "ETH": "XETHZUSD"},
        "pairs": [("BTC", "ETH", "positive")],
    },
]


def fetch_url_json(url: str, timeout: int = 12) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "ict-engine-smt-preflight/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def yahoo_chart(symbol: str, interval: str = "15m", range_: str = "5d") -> tuple[list[Candle], dict[str, Any]]:
    encoded = urllib.parse.quote(symbol, safe="")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?interval={interval}&range={range_}&includePrePost=true"
    meta = {"source": "yahoo_chart", "symbol": symbol, "url": url, "requested_range": range_, "requested_interval": interval}
    try:
        payload = fetch_url_json(url)
        result = payload.get("chart", {}).get("result") or []
        if not result:
            meta["error"] = payload.get("chart", {}).get("error") or "empty_result"
            return [], meta
        row = result[0]
        ts = row.get("timestamp") or []
        quote = (row.get("indicators", {}).get("quote") or [{}])[0]
        candles = []
        for t, o, h, l, c in zip(ts, quote.get("open", []), quote.get("high", []), quote.get("low", []), quote.get("close", [])):
            if None in (o, h, l, c):
                continue
            candles.append(Candle(int(t), float(o), float(h), float(l), float(c)))
        meta["returned_rows"] = len(candles)
        if candles:
            meta["returned_start"] = candles[0].time
            meta["returned_end"] = candles[-1].time
        return candles, meta
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        meta["error"] = str(exc)
        return [], meta


def kraken_ohlc(pair: str, interval: int = 15) -> tuple[list[Candle], dict[str, Any]]:
    since = int(time.time()) - 5 * 24 * 60 * 60
    url = f"https://api.kraken.com/0/public/OHLC?pair={urllib.parse.quote(pair)}&interval={interval}&since={since}"
    meta = {"source": "kraken_public_ohlc", "symbol": pair, "url": url, "requested_range": "5d", "requested_interval": f"{interval}m"}
    try:
        payload = fetch_url_json(url)
        if payload.get("error"):
            meta["error"] = payload["error"]
            return [], meta
        result = payload.get("result", {})
        key = next((k for k in result if k != "last"), None)
        rows = result.get(key, []) if key else []
        candles = [Candle(int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4])) for r in rows]
        meta["returned_rows"] = len(candles)
        if candles:
            meta["returned_start"] = candles[0].time
            meta["returned_end"] = candles[-1].time
        return candles, meta
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        meta["error"] = str(exc)
        return [], meta


def align(a: list[Candle], b: list[Candle]) -> tuple[list[Candle], list[Candle]]:
    by_a = {c.time: c for c in a}
    by_b = {c.time: c for c in b}
    keys = sorted(set(by_a) & set(by_b))
    return [by_a[k] for k in keys], [by_b[k] for k in keys]


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
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def latest_swing(candles: list[Candle], lookback: int = 2) -> dict[str, Any] | None:
    if len(candles) < lookback * 2 + 10:
        return None
    pivots = []
    for i in range(lookback, len(candles) - lookback):
        window = candles[i - lookback : i] + candles[i + 1 : i + 1 + lookback]
        cur = candles[i]
        if cur.high > max(c.high for c in window):
            pivots.append({"kind": "high", "time": cur.time, "level": cur.high})
        if cur.low < min(c.low for c in window):
            pivots.append({"kind": "low", "time": cur.time, "level": cur.low})
    if len(pivots) < 2:
        return None
    cur = pivots[-1]
    prev = next((p for p in reversed(pivots[:-1]) if p["kind"] == cur["kind"]), None)
    if not prev:
        return None
    if cur["kind"] == "high":
        swing_type = "HH" if cur["level"] > prev["level"] else "LH"
        swept_side = "buy_side_liquidity" if swing_type == "HH" else "none"
    else:
        swing_type = "LL" if cur["level"] < prev["level"] else "HL"
        swept_side = "sell_side_liquidity" if swing_type == "LL" else "none"
    return {**cur, "previous_level": prev["level"], "swing_type": swing_type, "swept_side": swept_side}


def invert_swing(swing_type: str | None) -> str:
    return {"HH": "LL", "LL": "HH", "HL": "LH", "LH": "HL"}.get(swing_type or "n/a", swing_type or "n/a")


def smt_row(family: dict[str, Any], base: str, comp: str, relationship_type: str, candles: dict[str, list[Candle]]) -> dict[str, Any]:
    base_raw = candles.get(base, [])
    comp_raw = candles.get(comp, [])
    base_aligned, comp_aligned = align(base_raw, comp_raw)
    c = corr(returns(base_aligned), returns(comp_aligned))
    normalized = relationship_type == "negative"
    fail = None
    if len(base_aligned) < 40:
        fail = "insufficient_aligned_candles"
    elif relationship_type == "positive" and c < 0.25:
        fail = "recent_positive_correlation_unstable"
    elif relationship_type == "negative" and c > -0.25:
        fail = "recent_negative_correlation_unstable"
    base_swing = latest_swing(base_aligned) if not fail else None
    comp_swing = latest_swing(comp_aligned) if not fail else None
    if not fail and (not base_swing or not comp_swing):
        fail = "missing_confirmed_swing_pair"
    base_type = base_swing["swing_type"] if base_swing else "n/a"
    raw_comp_type = comp_swing["swing_type"] if comp_swing else None
    comp_type = invert_swing(raw_comp_type) if normalized else (raw_comp_type or "n/a")
    smt_signal = "none"
    if not fail:
        if base_type == "LL" and comp_type == "HL":
            smt_signal = "bullish_smt"
        elif base_type == "HH" and comp_type == "LH":
            smt_signal = "bearish_smt"
        else:
            fail = "no_swing_confirmation_failure_at_latest_event"
    return {
        "family": family["family"],
        "provider": family["provider"],
        "base_symbol": base,
        "comparison_symbol": comp,
        "relationship_type": relationship_type,
        "relationship_confidence": round(abs(c), 4) if not fail else 0.0,
        "recent_correlation": round(c, 4),
        "timeframe": family["timeframe"],
        "session": family["session"],
        "aligned_kline_rows": len(base_aligned),
        "smt_signal": smt_signal,
        "base_swing_type": base_type,
        "base_level": base_swing["level"] if base_swing else None,
        "comparison_swing_type": comp_type,
        "comparison_level": comp_swing["level"] if comp_swing else None,
        "swept_side": base_swing["swept_side"] if base_swing else "none",
        "normalized_for_inverse_correlation": normalized,
        "raw_comparison_swing_type": raw_comp_type,
        "raw_comparison_level": comp_swing["level"] if comp_swing else None,
        "near_pd_array": False,
        "pd_array_type": "none",
        "mss_or_cisd_confirmed": False,
        "displacement_confirmed": False,
        "confidence": 0.0 if fail else 0.25,
        "fail_closed_reason": fail or "confirmation_only_waiting_for_mss_cisd_displacement_and_pda",
        "actionable": False,
        "regime_profit_branch_path": "Transition -> LiquiditySweepConfirmationFailure -> smt_divergence_confirmation_only -> smt_relationship_resolver:provider_observation_v1",
    }


def main() -> int:
    MATERIALS.mkdir(parents=True, exist_ok=True)
    PROVIDER_DATA.mkdir(parents=True, exist_ok=True)
    provider_meta = []
    observation_rows = []
    for family in FAMILIES:
        candles: dict[str, list[Candle]] = {}
        for logical, provider_symbol in family["symbols"].items():
            if family["provider"] == "yahoo_chart":
                rows, meta = yahoo_chart(provider_symbol)
            else:
                rows, meta = kraken_ohlc(provider_symbol)
            meta = {**meta, "logical_symbol": logical, "family": family["family"], "provider": family["provider"]}
            provider_meta.append(meta)
            candles[logical] = rows
            safe = f"{family['family']}.{logical}.{provider_symbol}".replace("/", "_").replace("=", "_")
            (PROVIDER_DATA / f"{safe}.json").write_text(json.dumps({"meta": meta, "rows": [c.__dict__ for c in rows]}, indent=2) + "\n")
        for base, comp, relationship in family["pairs"]:
            observation_rows.append(smt_row(family, base, comp, relationship, candles))
    per_regime = {
        regime: {
            "win_rate": None,
            "trade_count": 0,
            "expectancy": None,
            "sample_window": "provider_observation_only_5d_15m_requested",
            "instrument_coverage": sorted({r["base_symbol"] for r in observation_rows} | {r["comparison_symbol"] for r in observation_rows}),
            "confidence": 0.0,
            "fail_closed_reason": "no_realized_trade_outcomes_smt_confirmation_only",
        }
        for regime in ["trend", "range", "transition", "stress", "other"]
    }
    packet = {
        "factor_name": "smt_relationship_resolver",
        "factor_version": "2026-05-12.provider-observation.v1",
        "promotion_allowed": False,
        "trade_usable": False,
        "actionable": False,
        "branch_path_contract": {
            "main_regime": "Transition",
            "sub_regime": "LiquiditySweepConfirmationFailure",
            "sub_sub_regime_or_profit_factor": "smt_divergence_confirmation_only",
            "profit_factor": "smt_relationship_resolver:provider_observation_v1",
            "regime_profit_branch_path": "Transition -> LiquiditySweepConfirmationFailure -> smt_divergence_confirmation_only -> smt_relationship_resolver:provider_observation_v1",
        },
        "provider_summary": {
            "attempted_provider_symbols": len(provider_meta),
            "successful_provider_symbols": sum(1 for m in provider_meta if m.get("returned_rows", 0) > 0),
            "failed_provider_symbols": sum(1 for m in provider_meta if m.get("returned_rows", 0) == 0),
            "provider_meta_path": "materials/provider_fetch_summary.json",
        },
        "rows": observation_rows,
        "per_regime_statistics": per_regime,
        "quality_gate": {
            "quality_weight": 0.0,
            "allowed_feedback_targets": ["provider_observation_diagnostics", "smt_event_detection_preflight"],
            "downstream_allowed": False,
            "fail_closed_reason": "no_realized_trade_outcomes_no_mss_cisd_no_displacement_no_pda_entry_model",
        },
    }
    (MATERIALS / "provider_fetch_summary.json").write_text(json.dumps(provider_meta, indent=2) + "\n")
    (MATERIALS / "smt_provider_observation_packet.json").write_text(json.dumps(packet, indent=2) + "\n")
    with (MATERIALS / "smt_provider_observation_rows.csv").open("w", newline="") as f:
        fieldnames = list(observation_rows[0].keys()) if observation_rows else []
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(observation_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
