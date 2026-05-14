#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT.parents[0] / "20260512T205906+0800-codex-smt-full-coverage-provider-observation-v2"
SRC_PACKET = SRC_ROOT / "materials/smt_provider_observation_packet.json"
SRC_PROVIDER = SRC_ROOT / "provider-data"
OUT_PACKET = ROOT / "materials/smt_entry_context_outcome_packet.json"
OUT_ROWS = ROOT / "materials/smt_entry_context_outcome_rows.csv"
OUT_REGIME = ROOT / "summaries/smt_entry_context_per_regime.csv"

LOOKBACK = 20
FORWARD_BARS = 12
DISPLACEMENT_BARS = 3
PDA_BARS = 5
MIN_TRADE_COUNT_FOR_LEARNING = 30


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def safe_float(value) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def provider_file(base: str, comparison: str, timeframe: str) -> Path:
    return SRC_PROVIDER / f"{base}_{comparison}_{timeframe}.json"


def index_by_time(rows: list[dict]) -> dict[str, int]:
    return {row["time"]: idx for idx, row in enumerate(rows)}


def true_ranges(rows: list[dict], start: int, end: int) -> list[float]:
    out: list[float] = []
    prev_close = None
    for row in rows[start:end]:
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        if prev_close is None:
            out.append(high - low)
        else:
            out.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
        prev_close = close
    return out


def classify_context(row: dict, base_rows: list[dict], event_idx: int) -> dict:
    signal = row["smt_signal"]
    direction = 1 if signal == "bullish_smt" else -1 if signal == "bearish_smt" else 0
    event = base_rows[event_idx]
    event_close = float(event["close"])
    prior = base_rows[max(0, event_idx - LOOKBACK):event_idx]
    future = base_rows[event_idx + 1:event_idx + 1 + FORWARD_BARS]
    recent = base_rows[max(0, event_idx - LOOKBACK):event_idx + 1]

    if direction == 0 or not prior or not future:
        return {
            "mss_or_cisd_confirmed": False,
            "displacement_confirmed": False,
            "near_pd_array": False,
            "pd_array_type": "none",
            "forward_return": None,
            "outcome_hit": None,
            "entry_context_complete": False,
            "label_fail_closed_reason": "no_smt_signal_or_insufficient_forward_bars",
        }

    prior_high = max(float(r["high"]) for r in prior)
    prior_low = min(float(r["low"]) for r in prior)
    future_high = max(float(r["high"]) for r in future)
    future_low = min(float(r["low"]) for r in future)
    mss = future_high > prior_high if direction > 0 else future_low < prior_low

    atr_window = true_ranges(base_rows, max(0, event_idx - LOOKBACK), event_idx + 1)
    atr = mean(atr_window) if atr_window else 0.0
    displacement = False
    for item in future[:DISPLACEMENT_BARS]:
        body = abs(float(item["close"]) - float(item["open"]))
        signed_body = (float(item["close"]) - float(item["open"])) * direction
        if atr > 0 and signed_body > 0 and body >= 1.25 * atr:
            displacement = True
            break

    pda = "none"
    for idx in range(event_idx + 2, min(len(base_rows), event_idx + 1 + PDA_BARS)):
        cur = base_rows[idx]
        two_back = base_rows[idx - 2]
        if direction > 0 and float(cur["low"]) > float(two_back["high"]):
            pda = "FVG"
            break
        if direction < 0 and float(cur["high"]) < float(two_back["low"]):
            pda = "FVG"
            break
    if pda == "none":
        session_high = max(float(r["high"]) for r in recent)
        session_low = min(float(r["low"]) for r in recent)
        level = safe_float(row["base_level"])
        if level is not None and (abs(level - session_high) <= atr or abs(level - session_low) <= atr):
            pda = "session_high_low"

    horizon_close = float(future[-1]["close"])
    forward_return = direction * ((horizon_close - event_close) / event_close) if event_close else None
    outcome_hit = forward_return is not None and forward_return > 0
    complete = bool(mss and displacement and pda != "none")
    if complete:
        fail_reason = None
    else:
        missing = []
        if not mss:
            missing.append("missing_mss_cisd")
        if not displacement:
            missing.append("missing_displacement")
        if pda == "none":
            missing.append("missing_pda")
        fail_reason = "entry_context_incomplete:" + ",".join(missing)

    return {
        "mss_or_cisd_confirmed": mss,
        "displacement_confirmed": displacement,
        "near_pd_array": pda != "none",
        "pd_array_type": pda,
        "forward_return": forward_return,
        "outcome_hit": outcome_hit,
        "entry_context_complete": complete,
        "label_fail_closed_reason": fail_reason,
    }


def main() -> int:
    packet = json.loads(SRC_PACKET.read_text())
    provider_cache: dict[tuple[str, str, str], tuple[list[dict], dict[str, int]]] = {}
    labeled: list[dict] = []

    for row in packet["rows"]:
        out = dict(row)
        key = (row["base_symbol"], row["comparison_symbol"], row["timeframe"])
        if key not in provider_cache:
            data = json.loads(provider_file(*key).read_text())
            provider_cache[key] = (data["base_rows"], index_by_time(data["base_rows"]))
        base_rows, time_index = provider_cache[key]
        event_idx = time_index.get(row["event_time"])
        if event_idx is None:
            context = {
                "mss_or_cisd_confirmed": False,
                "displacement_confirmed": False,
                "near_pd_array": False,
                "pd_array_type": "none",
                "forward_return": None,
                "outcome_hit": None,
                "entry_context_complete": False,
                "label_fail_closed_reason": "event_time_missing_from_provider_candles",
            }
        else:
            context = classify_context(row, base_rows, event_idx)
        out.update(context)
        out["actionable"] = False
        out["confirmation_role"] = "confirmation_only"
        out["branch_path"] = "Transition -> LiquiditySweepConfirmationFailure -> smt_divergence_confirmation_only -> smt_entry_context_outcome_labeling_v1"
        labeled.append(out)

    stats = {}
    for regime in ["trend", "range", "transition", "stress", "other"]:
        rows = [r for r in labeled if r.get("regime_bucket") == regime]
        trades = [r for r in rows if r["entry_context_complete"] and r["outcome_hit"] is not None]
        returns = [float(r["forward_return"]) for r in trades if r["forward_return"] is not None]
        stats[regime] = {
            "event_count": len(rows),
            "trade_count": len(trades),
            "win_rate": (sum(1 for r in trades if r["outcome_hit"]) / len(trades)) if trades else None,
            "expectancy": mean(returns) if returns else None,
            "sample_window": f"forward_{FORWARD_BARS}_bars",
            "instrument_coverage": sorted({r["base_symbol"] for r in rows}),
            "confidence": min(0.5, len(trades) / MIN_TRADE_COUNT_FOR_LEARNING) if trades else 0.0,
            "fail_closed_reason": None if len(trades) >= MIN_TRADE_COUNT_FOR_LEARNING else "insufficient_entry_context_trade_count",
        }

    total_trades = sum(item["trade_count"] for item in stats.values())
    quality_weight = 0.0 if total_trades < MIN_TRADE_COUNT_FOR_LEARNING else 0.25
    downstream_allowed = total_trades >= MIN_TRADE_COUNT_FOR_LEARNING
    out_packet = {
        "source_root": str(SRC_ROOT),
        "branch_path": "Transition -> LiquiditySweepConfirmationFailure -> smt_divergence_confirmation_only -> smt_entry_context_outcome_labeling_v1",
        "rows": labeled,
        "per_regime_statistics": stats,
        "quality_gate": {
            "quality_weight": quality_weight,
            "downstream_allowed": downstream_allowed,
            "fail_closed_reason": None if downstream_allowed else "insufficient_entry_context_trade_count_for_learning",
            "min_trade_count_for_learning": MIN_TRADE_COUNT_FOR_LEARNING,
        },
        "promotion_allowed": False,
        "trade_usable": False,
        "actionable": False,
        "allowed_feedback_targets": ["entry_context_label_quality", "smt_event_outcome_observation"] if total_trades else ["entry_context_missingness"],
    }

    OUT_PACKET.write_text(json.dumps(out_packet, indent=2) + "\n")
    fields = list(labeled[0].keys()) if labeled else []
    with OUT_ROWS.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(labeled)
    with OUT_REGIME.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["regime", "event_count", "trade_count", "win_rate", "expectancy", "sample_window", "instrument_coverage", "confidence", "fail_closed_reason"])
        writer.writeheader()
        for regime, item in stats.items():
            writer.writerow({"regime": regime, **item, "instrument_coverage": ",".join(item["instrument_coverage"])})

    print(json.dumps({
        "smt_entry_context_outcome_packet": "pass",
        "rows": len(labeled),
        "entry_context_trade_count": total_trades,
        "downstream_allowed": downstream_allowed,
        "quality_weight": quality_weight,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
