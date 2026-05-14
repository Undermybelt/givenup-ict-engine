#!/usr/bin/env python3
"""SMT divergence factor preflight for Board B.

This is a lightweight runtime-evidence contract generator. It does not fetch
provider data, dispatch Auto-Quant, or mutate ict-engine runtime state.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[4]
SOURCE_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T201300+0800-codex-provider-density-redesign-six-provider-aq-v1"
)
NORMALIZED_DATA = SOURCE_ROOT / "data/normalized"


REQUIRED_SCHEMA_FIELDS = [
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
]

REGIME_BUCKETS = ["trend", "range", "transition", "stress", "other"]

RELATIONSHIP_SEEDS = {
    "NQ": {
        "positive": ["ES", "YM", "RTY", "QQQ", "SPY", "DIA", "IWM", "NAS100", "US500", "US30"],
        "negative": ["DXY", "VIX"],
    },
    "ES": {
        "positive": ["NQ", "YM", "RTY", "SPY", "QQQ", "DIA"],
        "negative": ["VIX", "DXY"],
    },
    "EURUSD": {
        "positive": ["GBPUSD"],
        "negative": ["DXY", "EURGBP"],
    },
    "XAUUSD": {
        "positive": ["XAGUSD", "GDX"],
        "negative": ["DXY", "US10Y", "REAL_YIELD"],
    },
    "BTC": {
        "positive": ["ETH", "SOL", "TOTAL", "QQQ"],
        "negative": ["DXY"],
    },
    "BTCUSDT": {
        "positive": ["ETHUSDT", "SOLUSDT", "TOTAL", "QQQ"],
        "negative": ["DXY"],
    },
}

LOCAL_SYMBOL_ALIASES = {
    "binance_btcusdt_1h.normalized.csv": "BTCUSDT",
    "bybit_linear_btcusdt_1h.normalized.csv": "BTCUSDT",
    "kraken_futures_pfxbtusd_1h.normalized.csv": "BTCUSD",
    "tvr_btc_usd_1h.normalized.csv": "BTCUSD",
    "yahoo_spy_1h.normalized.csv": "SPY",
    "ibkr_spy_1h_90d.normalized.csv": "SPY",
}


@dataclass
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_candles(path: Path) -> list[Candle]:
    candles: list[Candle] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            try:
                candles.append(
                    Candle(
                        timestamp=row["timestamp"],
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row.get("volume") or 0.0),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
    return candles


def pct_returns(values: list[float]) -> list[float]:
    out: list[float] = []
    for prev, cur in zip(values, values[1:]):
        if prev == 0:
            continue
        out.append((cur - prev) / prev)
    return out


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = min(len(xs), len(ys))
    if n < 20:
        return None
    xs = xs[-n:]
    ys = ys[-n:]
    mx = mean(xs)
    my = mean(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(vx * vy)


def swing_type(candles: list[Candle], idx: int, lookback: int = 5, tolerance: float = 0.0005) -> tuple[str, float]:
    if idx < lookback:
        return ("n/a", candles[idx].close)
    window = candles[idx - lookback : idx]
    prev_high = max(c.high for c in window)
    prev_low = min(c.low for c in window)
    cur = candles[idx]
    if cur.high > prev_high * (1 + tolerance):
        return ("HH", cur.high)
    if cur.high >= prev_high * (1 - tolerance):
        return ("equal_high", cur.high)
    if cur.low < prev_low * (1 - tolerance):
        return ("LL", cur.low)
    if cur.low <= prev_low * (1 + tolerance):
        return ("equal_low", cur.low)
    if cur.close > window[-1].close:
        return ("HL", cur.low)
    return ("LH", cur.high)


def align_by_timestamp(base: list[Candle], comp: list[Candle]) -> tuple[list[Candle], list[Candle]]:
    comp_by_time = {c.timestamp: c for c in comp}
    left: list[Candle] = []
    right: list[Candle] = []
    for candle in base:
        other = comp_by_time.get(candle.timestamp)
        if other is not None:
            left.append(candle)
            right.append(other)
    return left, right


def detect_smt(base: list[Candle], comp: list[Candle], relationship_type: str) -> dict[str, object]:
    aligned_base, aligned_comp = align_by_timestamp(base, comp)
    min_len = min(len(base), len(comp))
    overlap_ratio = len(aligned_base) / min_len if min_len else 0.0
    if len(aligned_base) < 50 or overlap_ratio < 0.60:
        return fail_closed_signal("session_or_timeframe_overlap_insufficient", aligned_base, aligned_comp, relationship_type)

    base_rets = pct_returns([c.close for c in aligned_base])
    comp_rets = pct_returns([c.close for c in aligned_comp])
    recent_corr = pearson(base_rets[-80:], comp_rets[-80:])
    full_corr = pearson(base_rets, comp_rets)
    if recent_corr is None or full_corr is None:
        return fail_closed_signal("recent_correlation_unavailable_or_flat", aligned_base, aligned_comp, relationship_type)
    if abs(recent_corr) < 0.25 or abs(recent_corr - full_corr) > 0.55:
        return fail_closed_signal("recent_correlation_unstable", aligned_base, aligned_comp, relationship_type, recent_corr, full_corr)

    normalized_for_inverse = relationship_type == "negative" or recent_corr < -0.25
    scan_start = max(5, len(aligned_base) - 160)
    for idx in range(len(aligned_base) - 1, scan_start, -1):
        base_swing, base_level = swing_type(aligned_base, idx)
        comp_swing, comp_level = swing_type(aligned_comp, idx)
        raw_comp_swing = comp_swing
        if normalized_for_inverse:
            comp_swing = {"HH": "LL", "LL": "HH", "HL": "LH", "LH": "HL"}.get(comp_swing, comp_swing)
        if base_swing in {"LL", "equal_low"} and comp_swing in {"HL", "equal_low"}:
            return build_signal(
                "bullish_smt",
                "sell_side_liquidity",
                aligned_base[idx],
                base_swing,
                base_level,
                raw_comp_swing,
                comp_level,
                normalized_for_inverse,
                recent_corr,
                full_corr,
            )
        if base_swing in {"HH", "equal_high"} and comp_swing in {"LH", "equal_high"}:
            return build_signal(
                "bearish_smt",
                "buy_side_liquidity",
                aligned_base[idx],
                base_swing,
                base_level,
                raw_comp_swing,
                comp_level,
                normalized_for_inverse,
                recent_corr,
                full_corr,
            )

    return fail_closed_signal("no_same_event_swing_confirmation_failure_detected", aligned_base, aligned_comp, relationship_type, recent_corr, full_corr)


def fail_closed_signal(
    reason: str,
    base: list[Candle],
    comp: list[Candle],
    relationship_type: str,
    recent_corr: float | None = None,
    full_corr: float | None = None,
) -> dict[str, object]:
    base_level = base[-1].close if base else None
    comp_level = comp[-1].close if comp else None
    return {
        "base_symbol": "n/a",
        "comparison_symbol": "n/a",
        "relationship_type": relationship_type,
        "relationship_confidence": 0.0,
        "timeframe": "1h",
        "session": "n/a",
        "smt_signal": "none",
        "base_swing_type": "n/a",
        "base_level": base_level,
        "comparison_swing_type": "n/a",
        "comparison_level": comp_level,
        "swept_side": "none",
        "normalized_for_inverse_correlation": relationship_type == "negative",
        "near_pd_array": False,
        "pd_array_type": "none",
        "mss_or_cisd_confirmed": False,
        "displacement_confirmed": False,
        "confidence": 0.0,
        "fail_closed_reason": reason,
        "recent_correlation": recent_corr,
        "full_window_correlation": full_corr,
        "actionable": False,
        "confirmation_only": True,
    }


def build_signal(
    signal: str,
    swept_side: str,
    candle: Candle,
    base_swing: str,
    base_level: float,
    comp_swing: str,
    comp_level: float,
    normalized: bool,
    recent_corr: float,
    full_corr: float,
) -> dict[str, object]:
    return {
        "base_symbol": "n/a",
        "comparison_symbol": "n/a",
        "relationship_type": "negative" if normalized and recent_corr < 0 else "positive",
        "relationship_confidence": min(1.0, abs(recent_corr)),
        "timeframe": "1h",
        "session": "overlap_from_timestamps",
        "smt_signal": signal,
        "base_swing_type": base_swing,
        "base_level": round(base_level, 8),
        "comparison_swing_type": comp_swing,
        "comparison_level": round(comp_level, 8),
        "swept_side": swept_side,
        "normalized_for_inverse_correlation": normalized,
        "near_pd_array": False,
        "pd_array_type": "none",
        "mss_or_cisd_confirmed": False,
        "displacement_confirmed": False,
        "confidence": 0.25,
        "fail_closed_reason": "confirmation_only_waiting_for_mss_cisd_displacement_and_pda",
        "event_time": candle.timestamp,
        "recent_correlation": recent_corr,
        "full_window_correlation": full_corr,
        "actionable": False,
        "confirmation_only": True,
    }


def discover_local_universe() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for path in sorted(NORMALIZED_DATA.glob("*.csv")):
        symbol = LOCAL_SYMBOL_ALIASES.get(path.name)
        if symbol:
            out[f"{symbol}:{path.stem}"] = path
    return out


def relationship_candidates(base_symbol: str, available_symbols: set[str]) -> list[dict[str, object]]:
    seed = RELATIONSHIP_SEEDS.get(base_symbol.upper(), {"positive": [], "negative": []})
    rows: list[dict[str, object]] = []
    for rel_type, symbols in seed.items():
        for symbol in symbols:
            rows.append(
                {
                    "base_symbol": base_symbol,
                    "comparison_symbol": symbol,
                    "relationship_type": rel_type,
                    "available_in_local_universe": symbol in available_symbols,
                    "relationship_confidence": 0.0 if symbol not in available_symbols else 0.25,
                    "evidence_source": "seed_resolver_plus_available_universe_filter",
                    "fail_closed_reason": "" if symbol in available_symbols else "comparison_symbol_not_available_locally",
                }
            )
    if not rows:
        rows.append(
            {
                "base_symbol": base_symbol,
                "comparison_symbol": "n/a",
                "relationship_type": "uncertain",
                "available_in_local_universe": False,
                "relationship_confidence": 0.0,
                "evidence_source": "no_seed_or_profile_resolution",
                "fail_closed_reason": "no_dynamic_relationship_candidate",
            }
        )
    return rows


def main() -> int:
    for sub in ["schemas", "materials", "mappings", "checks"]:
        (ROOT / sub).mkdir(parents=True, exist_ok=True)

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ict-engine Board B SMT divergence factor evidence v1",
        "type": "object",
        "required": REQUIRED_SCHEMA_FIELDS,
        "additionalProperties": True,
        "properties": {
            "base_symbol": {"type": "string"},
            "comparison_symbol": {"type": "string"},
            "relationship_type": {"enum": ["positive", "negative", "uncertain"]},
            "relationship_confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "timeframe": {"type": "string"},
            "session": {"type": "string"},
            "smt_signal": {"enum": ["bullish_smt", "bearish_smt", "none"]},
            "base_swing_type": {"enum": ["HH", "LH", "LL", "HL", "equal_high", "equal_low", "n/a"]},
            "base_level": {"type": ["number", "null"]},
            "comparison_swing_type": {"enum": ["HH", "LH", "LL", "HL", "equal_high", "equal_low", "n/a"]},
            "comparison_level": {"type": ["number", "null"]},
            "swept_side": {"enum": ["buy_side_liquidity", "sell_side_liquidity", "none"]},
            "normalized_for_inverse_correlation": {"type": "boolean"},
            "near_pd_array": {"type": "boolean"},
            "pd_array_type": {
                "enum": [
                    "FVG",
                    "IFVG",
                    "OB",
                    "breaker",
                    "mitigation",
                    "rejection",
                    "session_high_low",
                    "previous_day_high_low",
                    "none",
                ]
            },
            "mss_or_cisd_confirmed": {"type": "boolean"},
            "displacement_confirmed": {"type": "boolean"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "fail_closed_reason": {"type": "string"},
            "actionable": {"const": False},
            "confirmation_only": {"const": True},
        },
    }
    write_json(ROOT / "schemas/smt_divergence_factor_schema_v1.json", schema)

    local_universe = discover_local_universe()
    available_symbols = {key.split(":", 1)[0] for key in local_universe}

    candidate_rows: list[dict[str, object]] = []
    for base_symbol in ["NQ", "ES", "EURUSD", "XAUUSD", "BTC", "BTCUSDT"]:
        candidate_rows.extend(relationship_candidates(base_symbol, available_symbols))
    write_csv(
        ROOT / "materials/smt_dynamic_relationship_candidates_v1.csv",
        candidate_rows,
        [
            "base_symbol",
            "comparison_symbol",
            "relationship_type",
            "available_in_local_universe",
            "relationship_confidence",
            "evidence_source",
            "fail_closed_reason",
        ],
    )

    coverage_pairs = [
        ("NQ", "ES", "indices"),
        ("NQ", "YM", "indices"),
        ("EURUSD", "GBPUSD", "forex"),
        ("EURUSD", "DXY", "forex_inverse"),
        ("XAUUSD", "XAGUSD", "metals"),
        ("XAUUSD", "DXY", "metals_inverse"),
        ("BTC", "ETH", "crypto"),
    ]
    coverage_rows = []
    for base, comp, family in coverage_pairs:
        coverage_rows.append(
            {
                "family": family,
                "base_symbol": base,
                "comparison_symbol": comp,
                "timeframe": "1h",
                "local_base_available": base in available_symbols or f"{base}USDT" in available_symbols,
                "local_comparison_available": comp in available_symbols or f"{comp}USDT" in available_symbols,
                "status": "fail_closed",
                "fail_closed_reason": "required_pair_not_fully_available_in_local_preflight_universe",
            }
        )
    write_csv(
        ROOT / "materials/smt_required_coverage_matrix_v1.csv",
        coverage_rows,
        [
            "family",
            "base_symbol",
            "comparison_symbol",
            "timeframe",
            "local_base_available",
            "local_comparison_available",
            "status",
            "fail_closed_reason",
        ],
    )

    sample_signal = fail_closed_signal("no_provider_backed_same_event_pair_in_required_coverage", [], [], "uncertain")
    sample_signal.update(
        {
            "base_symbol": "NQ",
            "comparison_symbol": "ES",
            "main_regime": "Transition",
            "sub_regime": "CrossMarketConfirmation",
            "sub_sub_regime_or_profit_factor": "smt_divergence_confirmation_failure",
            "profit_factor": "ict_smt_divergence_confirmation_v1",
            "branch_path": "Transition -> CrossMarketConfirmation -> smt_divergence_confirmation_failure -> ict_smt_divergence_confirmation_v1",
            "regime_profit_branch_path": "Transition -> CrossMarketConfirmation -> smt_divergence_confirmation_failure -> ict_smt_divergence_confirmation_v1",
            "quality_weight": "0_for_bbn_catboost_execution_tree_learning",
        }
    )
    sample_signal["per_regime_stats"] = {
        bucket: {"win_rate": None, "trade_count": 0, "expectancy": None, "sample_window": "n/a"}
        for bucket in REGIME_BUCKETS
    }
    write_json(ROOT / "materials/smt_divergence_factor_sample_null_v1.json", sample_signal)

    detected_rows = []
    provider_paths = list(local_universe.items())
    if len(provider_paths) >= 2:
        (_, left_path), (_, right_path) = provider_paths[0], provider_paths[1]
        left_symbol = provider_paths[0][0].split(":", 1)[0]
        right_symbol = provider_paths[1][0].split(":", 1)[0]
        if left_symbol == right_symbol:
            detection = fail_closed_signal(
                "same_symbol_provider_reproduction_is_not_smt_divergence",
                load_candles(left_path),
                load_candles(right_path),
                "uncertain",
            )
        else:
            detection = detect_smt(load_candles(left_path), load_candles(right_path), "uncertain")
        detection.update(
            {
                "base_symbol": left_symbol,
                "comparison_symbol": right_symbol,
                "provider_pair": f"{left_path.name}__vs__{right_path.name}",
                "promotion_allowed": False,
                "trade_usable": False,
                "quality_weight": "0_for_bbn_catboost_execution_tree_learning",
            }
        )
        detected_rows.append(detection)
    with (ROOT / "materials/smt_detected_local_provider_pair_signals_v1.jsonl").open("w", encoding="utf-8") as handle:
        for row in detected_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    mapping = {
        "factor": "smt_divergence_confirmation_failure",
        "branch_path_contract": [
            "main_regime",
            "sub_regime",
            "sub_sub_regime_or_profit_factor",
            "profit_factor",
        ],
        "consumer_mapping": {
            "Structure": ["base_swing_type", "comparison_swing_type", "base_level", "comparison_level", "swept_side"],
            "Technicals": ["timeframe", "session", "near_pd_array", "pd_array_type"],
            "SMT": [
                "relationship_type",
                "relationship_confidence",
                "smt_signal",
                "normalized_for_inverse_correlation",
                "fail_closed_reason",
            ],
            "Regime posterior evidence": ["per_regime_stats", "confidence", "quality_weight"],
            "Execution tree features": [
                "smt_signal",
                "mss_or_cisd_confirmed",
                "displacement_confirmed",
                "near_pd_array",
                "pd_array_type",
            ],
            "Feedback/update learning fields": [
                "base_symbol",
                "comparison_symbol",
                "base_level",
                "comparison_level",
                "swept_side",
                "per_regime_stats",
                "fail_closed_reason",
            ],
        },
        "gates": {
            "smt_confirmation_only": True,
            "standalone_actionable_allowed": False,
            "requires_same_timeframe": True,
            "requires_session_overlap": True,
            "requires_stable_recent_correlation": True,
            "requires_base_and_comparison_levels": True,
            "requires_mss_or_cisd_or_displacement_for_trade_plan": True,
            "requires_pda_entry_model_for_trade_plan": True,
            "low_sample_fail_closed": True,
        },
    }
    write_json(ROOT / "mappings/smt_divergence_factor_field_mapping_v1.json", mapping)

    assertions = []
    assertions.append(("schema_has_required_user_fields", all(field in schema["required"] for field in REQUIRED_SCHEMA_FIELDS)))
    assertions.append(("schema_forces_actionable_false", schema["properties"]["actionable"]["const"] is False))
    assertions.append(("sample_has_branch_path", bool(sample_signal["branch_path"])))
    assertions.append(("sample_fail_closed", sample_signal["confidence"] == 0.0 and sample_signal["smt_signal"] == "none"))
    assertions.append(("coverage_matrix_fail_closed_until_required_pairs_exist", all(row["status"] == "fail_closed" for row in coverage_rows)))
    assertions.append(("mapping_keeps_smt_confirmation_only", mapping["gates"]["smt_confirmation_only"] is True))
    assertions.append(("no_downstream_learning_allowed", sample_signal["quality_weight"] == "0_for_bbn_catboost_execution_tree_learning"))
    ok = all(value for _, value in assertions)
    lines = [f"{name}={str(value).lower()}" for name, value in assertions]
    lines.extend(
        [
            f"local_universe_count={len(local_universe)}",
            f"candidate_rows={len(candidate_rows)}",
            f"coverage_rows={len(coverage_rows)}",
            f"detected_local_provider_pair_rows={len(detected_rows)}",
            "provider_fetch_allowed=false",
            "auto_quant_dispatch_allowed=false",
            "downstream_allowed=false",
            f"overall={'pass' if ok else 'fail'}",
        ]
    )
    (ROOT / "checks/smt_divergence_preflight_assertions.out").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
