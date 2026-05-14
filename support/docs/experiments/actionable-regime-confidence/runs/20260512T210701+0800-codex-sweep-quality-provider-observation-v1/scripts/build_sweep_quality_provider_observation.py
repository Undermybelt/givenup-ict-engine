#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[4]
SOURCE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T204436+0800-codex-smt-provider-observation-packet-v1/provider-data"
REGIMES = ["trend", "range", "transition", "stress", "other"]


def symbol_from_path(path: Path) -> tuple[str, str, str]:
    stem = path.stem
    parts = stem.split("_")
    timeframe = parts[-1] if parts and parts[-1].endswith(("h", "m", "d")) else "unknown"
    provider = "unknown"
    if "yahoo" in parts:
        provider = "yahoo"
        symbol = "_".join(parts[:-2]).upper()
    elif "kraken" in parts:
        provider = "kraken"
        symbol = parts[0].upper()
    else:
        symbol = parts[0].upper()
    return symbol, provider, timeframe


def normalize_rows(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, list):
        return []
    rows = []
    for row in data:
        try:
            rows.append(
                {
                    "time": str(row["time"]),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume", 0.0)),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return rows


def load_list(path: Path) -> list[dict[str, Any]]:
    return normalize_rows(json.loads(path.read_text()))


def close_returns(rows: list[dict[str, Any]]) -> list[float]:
    out = []
    for prev, cur in zip(rows, rows[1:]):
        out.append(0.0 if prev["close"] == 0 else (cur["close"] - prev["close"]) / prev["close"])
    return out


def classify_regime(rows: list[dict[str, Any]], index: int, window: int = 48) -> str:
    sample = rows[max(0, index - window) : index + 1]
    rets = close_returns(sample)
    if len(rets) < 10:
        return "other"
    avg = mean(rets)
    vol = math.sqrt(mean((ret - avg) ** 2 for ret in rets))
    drift = 0.0 if sample[0]["close"] == 0 else (sample[-1]["close"] - sample[0]["close"]) / sample[0]["close"]
    if vol > 0.008:
        return "stress"
    if abs(drift) > max(0.008, vol * 2.0):
        return "trend"
    if abs(drift) < max(0.003, vol * 0.8):
        return "range"
    return "transition"


def detect_rows(symbol: str, provider: str, timeframe: str, path: Path, candles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    lookback = 20
    for i in range(lookback, len(candles)):
        prior = candles[i - lookback : i]
        cur = candles[i]
        prior_low = min(item["low"] for item in prior)
        prior_high = max(item["high"] for item in prior)
        body = max(abs(cur["close"] - cur["open"]), 1e-9)
        lower_wick = min(cur["open"], cur["close"]) - cur["low"]
        upper_wick = cur["high"] - max(cur["open"], cur["close"])
        row = None
        if cur["low"] < prior_low and cur["close"] > prior_low:
            row = {
                "sweep_type": "true_sweep",
                "direction": "bullish",
                "swept_side": "sell_side_liquidity",
                "sweep_level": prior_low,
                "reclaim_level": prior_low,
                "invalidation_level": cur["low"],
                "continuation_trigger_level": cur["high"],
                "wick_body_ratio": round(lower_wick / body, 4),
            }
        elif cur["high"] > prior_high and cur["close"] < prior_high:
            row = {
                "sweep_type": "true_sweep",
                "direction": "bearish",
                "swept_side": "buy_side_liquidity",
                "sweep_level": prior_high,
                "reclaim_level": prior_high,
                "invalidation_level": cur["high"],
                "continuation_trigger_level": cur["low"],
                "wick_body_ratio": round(upper_wick / body, 4),
            }
        if not row:
            continue
        rows.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "session": "provider_native",
                "event_time": cur["time"],
                **row,
                "reclaim_speed_bars": 1,
                "continuation_confirmed": False,
                "reversal_confirmed": False,
                "near_pd_array": False,
                "pd_array_type": "none",
                "mss_or_cisd_confirmed": False,
                "displacement_confirmed": False,
                "regime_bucket": classify_regime(candles, i),
                "provider_provenance": f"{provider}:{path.relative_to(REPO)}",
                "evidence_source": "existing_provider_data_json",
                "confidence": 0.2,
                "fail_closed_reason": "confirmation_only_waiting_for_mss_cisd_displacement_pda_and_outcome",
                "confirmation_role": "confirmation_only",
                "actionable": False,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    (ROOT / "materials").mkdir(parents=True, exist_ok=True)
    (ROOT / "checks").mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, Any]] = []
    provider_summary = []
    for path in sorted(SOURCE.glob("*.json")):
        payload = json.loads(path.read_text())
        work_items: list[tuple[str, str, str, list[dict[str, Any]]]] = []
        if isinstance(payload, dict) and {"spec", "base_rows", "comparison_rows"} <= set(payload.keys()):
            spec = payload["spec"]
            timeframe = spec.get("timeframe", spec.get("interval", "unknown"))
            work_items.append((str(spec.get("base_symbol", path.stem)), "paired_provider_packet", timeframe, normalize_rows(payload.get("base_rows", []))))
            work_items.append((str(spec.get("comparison_symbol", path.stem)), "paired_provider_packet", timeframe, normalize_rows(payload.get("comparison_rows", []))))
        else:
            candles = normalize_rows(payload)
            symbol, provider, timeframe = symbol_from_path(path)
            work_items.append((symbol, provider, timeframe, candles))
        for symbol, provider, timeframe, candles in work_items:
            if not candles:
                continue
            rows = detect_rows(symbol, provider, timeframe, path, candles)
            all_rows.extend(rows)
            provider_summary.append(
                {
                    "symbol": symbol,
                    "provider": provider,
                    "timeframe": timeframe,
                    "source_path": str(path.relative_to(REPO)),
                    "candle_rows": len(candles),
                    "sweep_event_count": len(rows),
                    "first_time": candles[0]["time"],
                    "last_time": candles[-1]["time"],
                }
            )
        if not work_items:
            continue
    if not all_rows:
        raise SystemExit("no provider-backed sweep rows emitted")
    per_regime = {}
    for regime in REGIMES:
        event_count = sum(1 for row in all_rows if row["regime_bucket"] == regime)
        per_regime[regime] = {
            "win_rate": None,
            "trade_count": 0,
            "sweep_event_count": event_count,
            "expectancy": None,
            "sample_window": "provider_observation_only_no_entry_model",
            "instrument_coverage": sorted({row["symbol"] for row in all_rows if row["regime_bucket"] == regime}),
            "confidence": 0.0,
            "fail_closed_reason": "no_mss_cisd_displacement_pda_or_realized_trade_outcomes",
        }
    packet = {
        "factor_name": "sweep_quality",
        "factor_version": "2026-05-12.provider-observation.v1",
        "promotion_allowed": False,
        "trade_usable": False,
        "actionable": False,
        "definition": "Sweep quality observes liquidity sweep and reclaim levels; it is confirmation-only until entry model and realized outcomes exist.",
        "branch_path_contract": {
            "main_regime": "Transition",
            "sub_regime": "LiquiditySweep",
            "sub_sub_regime_or_profit_factor": "sweep_quality_confirmation_only",
            "profit_factor": "sweep_quality_provider_observation:v1",
            "regime_profit_branch_path": "Transition -> LiquiditySweep -> sweep_quality_confirmation_only -> sweep_quality_provider_observation:v1",
        },
        "provider_summary": provider_summary,
        "rows": all_rows,
        "per_regime_statistics": per_regime,
        "quality_gate": {
            "quality_weight": 0.0,
            "downstream_allowed": False,
            "pre_bayes_filter_allowed": False,
            "bbn_learning_allowed": False,
            "catboost_learning_allowed": False,
            "execution_tree_branch_weight_update_allowed": False,
            "fail_closed_reason": "provider_observation_only_no_mss_cisd_displacement_pda_or_realized_trade_outcomes",
        },
    }
    (ROOT / "materials/sweep_quality_provider_observation_packet.json").write_text(json.dumps(packet, indent=2) + "\n")
    (ROOT / "materials/sweep_quality_provider_summary.json").write_text(json.dumps(provider_summary, indent=2) + "\n")
    write_csv(ROOT / "materials/sweep_quality_provider_observation_rows.csv", all_rows)
    print(
        json.dumps(
            {
                "provider_files": len(provider_summary),
                "rows": len(all_rows),
                "by_symbol": {item["symbol"]: item["sweep_event_count"] for item in provider_summary},
                "downstream_allowed": False,
                "quality_weight": 0.0,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
