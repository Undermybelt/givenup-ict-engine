#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT.parents[0]
SRC_ROOT = RUNS / "20260512T205906+0800-codex-smt-full-coverage-provider-observation-v2"
PROVIDER_DATA = SRC_ROOT / "provider-data"

OUT_PACKET = ROOT / "materials/smt_provider_window_event_alignment_expansion_packet.json"
OUT_ROWS = ROOT / "summaries/smt_provider_window_event_alignment_expansion_rows.csv"
OUT_PER_REGIME = ROOT / "summaries/smt_provider_window_event_alignment_expansion_per_regime.csv"
OUT_PAIR_SUMMARY = ROOT / "summaries/smt_provider_window_event_alignment_expansion_pair_summary.csv"

REGIMES = ["trend", "range", "transition", "stress", "other"]
MIN_TRADE_COUNT_FOR_LEARNING = 30


@dataclass(frozen=True)
class PairSpec:
    family: str
    base_symbol: str
    comparison_symbol: str
    relationship_type: str
    timeframe: str
    session: str
    data_file: str


PAIR_SPECS = [
    PairSpec("indices", "NQ", "ES", "positive", "5m", "NY_AM", "NQ_ES_5m.json"),
    PairSpec("indices", "NQ", "YM", "positive", "5m", "NY_AM", "NQ_YM_5m.json"),
    PairSpec("forex", "EURUSD", "GBPUSD", "positive", "15m", "London_NY_overlap", "EURUSD_GBPUSD_15m.json"),
    PairSpec("forex", "EURUSD", "DXY", "negative", "15m", "London_NY_overlap", "EURUSD_DXY_15m.json"),
    PairSpec("metals", "XAUUSD", "XAGUSD", "positive", "15m", "NY_AM", "XAUUSD_XAGUSD_15m.json"),
    PairSpec("metals", "XAUUSD", "DXY", "negative", "15m", "NY_AM", "XAUUSD_DXY_15m.json"),
    PairSpec("crypto", "BTC", "ETH", "positive", "1h", "crypto_24x7", "BTC_ETH_1h.json"),
]


def as_float(value: Any) -> float | None:
    if value in (None, "", "None", "null"):
        return None
    return float(value)


def close_returns(rows: list[dict[str, Any]]) -> list[float]:
    out = []
    for prev, cur in zip(rows, rows[1:]):
        out.append(0.0 if prev["close"] == 0 else (cur["close"] - prev["close"]) / prev["close"])
    return out


def correlation(a: list[float], b: list[float]) -> float:
    if len(a) < 10 or len(a) != len(b):
        return 0.0
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return 0.0 if da == 0.0 or db == 0.0 else num / (da * db)


def align_by_time(base: list[dict[str, Any]], comp: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    comp_by_time = {row["time"]: row for row in comp}
    aligned = [(row, comp_by_time[row["time"]]) for row in base if row["time"] in comp_by_time]
    return [item[0] for item in aligned], [item[1] for item in aligned]


def classify_regime(rows: list[dict[str, Any]], index: int, window: int = 48) -> str:
    sample = rows[max(0, index - window) : index + 1]
    returns = close_returns(sample)
    if len(returns) < 10:
        return "other"
    avg = mean(returns)
    vol = math.sqrt(mean((ret - avg) ** 2 for ret in returns))
    drift = (sample[-1]["close"] - sample[0]["close"]) / sample[0]["close"] if sample[0]["close"] else 0.0
    if vol > 0.008:
        return "stress"
    if abs(drift) > max(0.008, vol * 2.0):
        return "trend"
    if abs(drift) < max(0.003, vol * 0.8):
        return "range"
    return "transition"


def atr(rows: list[dict[str, Any]], index: int, period: int = 14) -> float:
    start = max(1, index - period + 1)
    ranges = []
    for i in range(start, index + 1):
        cur = rows[i]
        prev = rows[i - 1]
        ranges.append(max(cur["high"] - cur["low"], abs(cur["high"] - prev["close"]), abs(cur["low"] - prev["close"])))
    return mean(ranges) if ranges else 0.0


def pivots(rows: list[dict[str, Any]], lookback: int) -> list[dict[str, Any]]:
    raw = []
    for index in range(lookback, len(rows) - lookback):
        cur = rows[index]
        around = rows[index - lookback : index] + rows[index + 1 : index + 1 + lookback]
        if cur["high"] > max(row["high"] for row in around):
            raw.append({"index": index, "time": cur["time"], "kind": "high", "level": cur["high"]})
        if cur["low"] < min(row["low"] for row in around):
            raw.append({"index": index, "time": cur["time"], "kind": "low", "level": cur["low"]})
    last_by_kind: dict[str, dict[str, Any]] = {}
    out = []
    for pivot in raw:
        previous = last_by_kind.get(pivot["kind"])
        if previous is None:
            last_by_kind[pivot["kind"]] = pivot
            continue
        if pivot["kind"] == "high":
            swing_type = "equal_high" if abs(pivot["level"] - previous["level"]) <= abs(previous["level"]) * 0.0002 else ("HH" if pivot["level"] > previous["level"] else "LH")
        else:
            swing_type = "equal_low" if abs(pivot["level"] - previous["level"]) <= abs(previous["level"]) * 0.0002 else ("LL" if pivot["level"] < previous["level"] else "HL")
        out.append({**pivot, "swing_type": swing_type, "previous_level": previous["level"], "lookback": lookback})
        last_by_kind[pivot["kind"]] = pivot
    return out


def invert_kind(kind: str) -> str:
    return "low" if kind == "high" else "high"


def invert_swing(swing: str) -> str:
    return {
        "HH": "LL",
        "LL": "HH",
        "HL": "LH",
        "LH": "HL",
        "equal_high": "equal_low",
        "equal_low": "equal_high",
    }.get(swing, swing)


def near_pd_array(rows: list[dict[str, Any]], index: int, kind: str, level: float) -> tuple[bool, str]:
    window = rows[max(0, index - 24) : index + 1]
    if not window:
        return False, "none"
    if kind == "high" and level >= max(row["high"] for row in window[:-1] or window):
        return True, "session_high_low"
    if kind == "low" and level <= min(row["low"] for row in window[:-1] or window):
        return True, "session_high_low"
    for i in range(max(2, index - 3), min(len(rows), index + 4)):
        if rows[i]["low"] > rows[i - 2]["high"] or rows[i]["high"] < rows[i - 2]["low"]:
            return True, "FVG"
    return False, "none"


def entry_context(rows: list[dict[str, Any]], pivot: dict[str, Any], smt_signal: str) -> tuple[bool, bool, bool, str]:
    index = pivot["index"]
    a = atr(rows, index)
    if a <= 0:
        return False, False, False, "none"
    after = rows[index + 1 : min(len(rows), index + 7)]
    if not after:
        near, pd_type = near_pd_array(rows, index, pivot["kind"], pivot["level"])
        return False, False, near, pd_type
    if smt_signal == "bullish_smt":
        break_level = max(row["high"] for row in rows[max(0, index - 8) : index + 1])
        mss = any(row["close"] > break_level for row in after)
        displacement = any((row["close"] - rows[index]["close"]) > a * 0.75 for row in after)
    else:
        break_level = min(row["low"] for row in rows[max(0, index - 8) : index + 1])
        mss = any(row["close"] < break_level for row in after)
        displacement = any((rows[index]["close"] - row["close"]) > a * 0.75 for row in after)
    near, pd_type = near_pd_array(rows, index, pivot["kind"], pivot["level"])
    return mss, displacement, near, pd_type


def find_near(pivot: dict[str, Any], comp_pivots: list[dict[str, Any]], spec: PairSpec, bars: int) -> dict[str, Any] | None:
    wanted_kind = invert_kind(pivot["kind"]) if spec.relationship_type == "negative" else pivot["kind"]
    candidates = [item for item in comp_pivots if item["kind"] == wanted_kind]
    if not candidates:
        return None
    near = min(candidates, key=lambda item: abs(item["index"] - pivot["index"]))
    return near if abs(near["index"] - pivot["index"]) <= bars else None


def forward_outcome(rows: list[dict[str, Any]], index: int, smt_signal: str, bars: int = 12) -> tuple[float | None, bool | None]:
    if index + bars >= len(rows):
        return None, None
    ret = (rows[index + bars]["close"] - rows[index]["close"]) / rows[index]["close"] if rows[index]["close"] else None
    if ret is None:
        return None, None
    directional = ret if smt_signal == "bullish_smt" else -ret
    return ret, directional > 0


def stable_relationship(spec: PairSpec, corr: float) -> tuple[bool, float, str]:
    if spec.relationship_type == "positive":
        return corr >= 0.35, max(0.0, corr), "recent_positive_correlation_unstable"
    if spec.relationship_type == "negative":
        return corr <= -0.35, max(0.0, -corr), "recent_negative_correlation_unstable"
    return False, 0.0, "relationship_uncertain"


def build_pair_rows(spec: PairSpec) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = json.loads((PROVIDER_DATA / spec.data_file).read_text())
    base, comp = align_by_time(payload["base_rows"], payload["comparison_rows"])
    if len(base) < 40:
        return [], {"fail_closed_reason": "insufficient_same_timeframe_aligned_candles", "aligned_rows": len(base), "correlation": 0.0}
    corr = correlation(close_returns(base), close_returns(comp))
    stable, rel_conf, unstable_reason = stable_relationship(spec, corr)
    if not stable:
        return [], {"fail_closed_reason": unstable_reason, "aligned_rows": len(base), "correlation": corr}
    rows_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for lookback in (2, 3):
        base_pivots = pivots(base, lookback)
        comp_pivots = pivots(comp, lookback)
        for base_pivot in base_pivots:
            comp_pivot = find_near(base_pivot, comp_pivots, spec, bars=5)
            if comp_pivot is None:
                continue
            base_type = base_pivot["swing_type"]
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
            mss, displacement, pda, pda_type = entry_context(base, base_pivot, smt_signal)
            fwd_ret, hit = forward_outcome(base, base_pivot["index"], smt_signal)
            strict = all([mss, displacement, pda]) and fwd_ret is not None
            fail_reasons = []
            if not mss:
                fail_reasons.append("missing_mss_cisd")
            if not displacement:
                fail_reasons.append("missing_displacement")
            if not pda:
                fail_reasons.append("missing_pda")
            if fwd_ret is None:
                fail_reasons.append("missing_forward_outcome")
            key = (spec.base_symbol, spec.comparison_symbol, base_pivot["time"])
            row = {
                "base_symbol": spec.base_symbol,
                "comparison_symbol": spec.comparison_symbol,
                "relationship_type": spec.relationship_type,
                "relationship_confidence": round(rel_conf, 4),
                "timeframe": spec.timeframe,
                "session": spec.session,
                "comparison_timeframe": spec.timeframe,
                "comparison_session": spec.session,
                "timeframe_aligned": True,
                "session_overlap": True,
                "correlation_window_bars": len(base) - 1,
                "recent_correlation": round(corr, 4),
                "event_time": base_pivot["time"],
                "smt_signal": smt_signal,
                "base_swing_type": base_type,
                "base_level": base_pivot["level"],
                "comparison_swing_type": comp_type,
                "comparison_level": comp_pivot["level"],
                "swept_side": swept_side,
                "normalized_for_inverse_correlation": spec.relationship_type == "negative",
                "raw_comparison_swing_type": raw_comp_type,
                "raw_comparison_level": comp_pivot["level"],
                "event_window_bars": 5,
                "event_time_delta_bars": abs(comp_pivot["index"] - base_pivot["index"]),
                "same_event_window_confirmed": True,
                "near_pd_array": pda,
                "pd_array_type": pda_type,
                "mss_or_cisd_confirmed": mss,
                "displacement_confirmed": displacement,
                "regime_bucket": classify_regime(base, base_pivot["index"]),
                "provider_provenance": "yfinance_cached_provider_window",
                "evidence_source": "closed_provider_data_event_alignment_expansion",
                "confidence": 0.35 if strict else 0.20,
                "forward_return": fwd_ret,
                "outcome_hit": hit,
                "strict_entry_context_complete": strict,
                "confirmation_role": "confirmation_only",
                "actionable": False,
                "fail_closed_reason": "none" if strict else "entry_context_incomplete:" + ",".join(fail_reasons),
                "branch_path": "Transition -> LiquiditySweepConfirmationFailure -> smt_divergence_confirmation_only -> smt_provider_window_event_alignment_expansion_v1",
            }
            previous = rows_by_key.get(key)
            if previous is None or (row["strict_entry_context_complete"] and not previous["strict_entry_context_complete"]):
                rows_by_key[key] = row
    return list(rows_by_key.values()), {"fail_closed_reason": None, "aligned_rows": len(base), "correlation": corr}


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    returns = [as_float(row["forward_return"]) for row in rows]
    returns = [value for value in returns if value is not None]
    hits = [row["outcome_hit"] for row in rows if row["outcome_hit"] is not None]
    return {
        "trade_count": len(rows),
        "win_rate": (sum(1 for hit in hits if hit) / len(hits)) if hits else None,
        "expectancy": mean(returns) if returns else None,
    }


def main() -> int:
    all_rows: list[dict[str, Any]] = []
    pair_summary = []
    for spec in PAIR_SPECS:
        rows, meta = build_pair_rows(spec)
        all_rows.extend(rows)
        strict_rows = [row for row in rows if row["strict_entry_context_complete"]]
        stats = summarize(strict_rows)
        pair_summary.append({
            "base_symbol": spec.base_symbol,
            "comparison_symbol": spec.comparison_symbol,
            "relationship_type": spec.relationship_type,
            "aligned_rows": meta["aligned_rows"],
            "recent_correlation": round(meta["correlation"], 4),
            "event_count": len(rows),
            "strict_trade_count": stats["trade_count"],
            "win_rate": stats["win_rate"],
            "expectancy": stats["expectancy"],
            "fail_closed_reason": "insufficient_strict_entry_context_trade_count" if stats["trade_count"] < MIN_TRADE_COUNT_FOR_LEARNING else "none",
        })

    strict_rows = [row for row in all_rows if row["strict_entry_context_complete"]]
    per_regime_rows = []
    per_regime: dict[str, dict[str, Any]] = {}
    for regime in REGIMES:
        selected = [row for row in strict_rows if row["regime_bucket"] == regime]
        stats = summarize(selected)
        stats["fail_closed_reason"] = "insufficient_per_regime_trade_count" if stats["trade_count"] < MIN_TRADE_COUNT_FOR_LEARNING else "none"
        per_regime[regime] = stats
        per_regime_rows.append({"regime": regime, **stats})

    fieldnames = [
        "base_symbol", "comparison_symbol", "relationship_type", "relationship_confidence", "timeframe", "session",
        "comparison_timeframe", "comparison_session", "timeframe_aligned", "session_overlap", "correlation_window_bars",
        "recent_correlation", "event_time", "smt_signal", "base_swing_type", "base_level", "comparison_swing_type",
        "comparison_level", "swept_side", "normalized_for_inverse_correlation", "raw_comparison_swing_type",
        "raw_comparison_level", "event_window_bars", "event_time_delta_bars", "same_event_window_confirmed",
        "near_pd_array", "pd_array_type", "mss_or_cisd_confirmed", "displacement_confirmed", "regime_bucket",
        "provider_provenance", "evidence_source", "confidence", "forward_return", "outcome_hit",
        "strict_entry_context_complete", "confirmation_role", "actionable", "fail_closed_reason", "branch_path",
    ]
    with OUT_ROWS.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    with OUT_PER_REGIME.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["regime", "trade_count", "win_rate", "expectancy", "fail_closed_reason"])
        writer.writeheader()
        writer.writerows(per_regime_rows)
    with OUT_PAIR_SUMMARY.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(pair_summary[0].keys()))
        writer.writeheader()
        writer.writerows(pair_summary)

    aggregate = summarize(strict_rows)
    pair_coverage_met = all(row["event_count"] > 0 for row in pair_summary)
    packet = {
        "factor_name": "smt_provider_window_event_alignment_expansion_v1",
        "source_root": str(SRC_ROOT.relative_to(Path.cwd())),
        "branch_path": "Transition -> LiquiditySweepConfirmationFailure -> smt_divergence_confirmation_only -> smt_provider_window_event_alignment_expansion_v1",
        "definition": "SMT is sibling-market liquidity-sweep swing confirmation failure at the same timeframe/session event window, not ordinary correlation or relative strength.",
        "counts": {
            "rows": len(all_rows),
            "smt_signal_rows": len(all_rows),
            "strict_trade_count": aggregate["trade_count"],
            "inverse_normalized_signal_rows": sum(1 for row in all_rows if row["normalized_for_inverse_correlation"]),
            "actionable_true_count": sum(1 for row in all_rows if row["actionable"]),
        },
        "pair_summary": pair_summary,
        "per_regime_statistics": per_regime,
        "aggregate_strict_statistics": aggregate,
        "quality_gate": {
            "min_trade_count_for_learning": MIN_TRADE_COUNT_FOR_LEARNING,
            "pair_coverage_met": pair_coverage_met,
            "aggregate_learning_floor_met": aggregate["trade_count"] >= MIN_TRADE_COUNT_FOR_LEARNING,
            "per_regime_learning_floor_met": all(item["trade_count"] >= MIN_TRADE_COUNT_FOR_LEARNING for item in per_regime.values()),
            "smt_confirmation_only": True,
            "standalone_actionable_allowed": False,
            "actionable": False,
            "auto_quant_dispatch_allowed": False,
            "pre_bayes_filter_allowed": False,
            "bbn_learning_allowed": False,
            "catboost_path_ranker_allowed": False,
            "execution_tree_branch_weight_update_allowed": False,
            "feedback_update_learning_allowed": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "fail_closed_reason": "insufficient_strict_entry_context_trade_count_or_per_regime_coverage",
        },
    }
    OUT_PACKET.write_text(json.dumps(packet, indent=2) + "\n")
    print(json.dumps({
        "smt_provider_window_event_alignment_expansion": "pass",
        "rows": len(all_rows),
        "strict_trade_count": aggregate["trade_count"],
        "pair_coverage_met": pair_coverage_met,
        "downstream_allowed": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
