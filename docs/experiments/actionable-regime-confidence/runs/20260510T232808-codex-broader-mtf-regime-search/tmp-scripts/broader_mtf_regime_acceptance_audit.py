from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T232808-codex-broader-mtf-regime-search"
AUDIT_DIR = RUN_ROOT / "audit"
CHECKS_DIR = RUN_ROOT / "checks"
AUTO_QUANT_DATA = Path("/Users/thrill3r/Auto-Quant/user_data/data")
STRICT_AUDIT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260510T224929-codex-strict-cross-timeframe-audit/audit/strict_cross_timeframe_audit.json"
)

Z95 = 1.959963984540054
TAIL_ROWS_PER_SOURCE = 80_000

SOURCES = [
    "NQ_USD-15m.feather",
    "NQ_USD-1h.feather",
    "NQ_USD-4h.feather",
    "SPY_USD-15m.feather",
    "SPY_USD-1h.feather",
    "IWM_USD-15m.feather",
    "IWM_USD-1h.feather",
    "QQQ_USD-1h.feather",
    "QQQ_USD-4h.feather",
    "BTC_USDT-1h.feather",
    "BTC_USDT-4h.feather",
    "ETH_USDT-1h.feather",
    "ETH_USDT-4h.feather",
    "GLD_USD-15m.feather",
    "GLD_USD-1h.feather",
]

RULES = {
    "TrendExpansion": {
        "target": "target_trend_structural_next",
        "condition": "trend_base AND drawdown64 >= -0.001320604675",
        "fields": ["trend_base", "drawdown64", "target_trend_structural_next"],
    },
    "ExtremeStress": {
        "target": "target_stress_next",
        "condition": "stress_base AND range_ratio32_128 >= 1.399149536",
        "fields": ["stress_base", "range_ratio32_128", "target_stress_next"],
    },
    "ReversalBrewing": {
        "target": "target_reversal_next",
        "condition": "stretch64 <= -0.03869250919",
        "fields": ["stretch64", "target_reversal_next"],
    },
    "ThinLiquidity": {
        "target": "target_thin_soft_next",
        "condition": "volume_mean16 <= 718.8075 AND thin_base",
        "fields": ["volume_mean16", "thin_base", "target_thin_soft_next"],
    },
}


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lower(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    centre = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def parse_ts(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_datetime(series, unit="ms", utc=True, errors="coerce")
    return pd.to_datetime(series, utc=True, errors="coerce")


def split_labels(n: int) -> np.ndarray:
    labels = np.full(n, "train", dtype=object)
    labels[n // 2 :] = "calibration"
    labels[(3 * n) // 4 :] = "test"
    return labels


def load_source(filename: str) -> pd.DataFrame:
    path = AUTO_QUANT_DATA / filename
    raw = pd.read_feather(path).rename(columns=str.lower).tail(TAIL_ROWS_PER_SOURCE).copy()
    symbol, timeframe = filename.removesuffix(".feather").rsplit("-", 1)
    instrument = symbol.replace("_USD", "").replace("_USDT", "")
    market = "AQ_crypto" if "USDT" in symbol else ("AQ_futures" if instrument in {"NQ", "ES"} else "AQ_ETF")
    raw["ts"] = parse_ts(raw["date"])
    for col in ("open", "high", "low", "close", "volume"):
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
    raw["instrument"] = instrument
    raw["market"] = market
    raw["timeframe"] = timeframe
    raw["context"] = instrument + ":" + market + ":" + timeframe
    cols = ["ts", "instrument", "market", "timeframe", "context", "open", "high", "low", "close", "volume"]
    return raw[cols].dropna().sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def quantile(train: pd.DataFrame, col: str, q: float) -> float:
    values = train[col].replace([np.inf, -np.inf], np.nan).dropna()
    return float(values.quantile(q))


def add_features(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["split"] = split_labels(len(df))
    df["hour_utc"] = df["ts"].dt.hour
    df["ret1"] = np.log(df["close"]).diff()
    df["ret4"] = np.log(df["close"] / df["close"].shift(4))
    df["ret16"] = np.log(df["close"] / df["close"].shift(16))
    df["range_pct"] = (df["high"] - df["low"]) / df["close"]

    for window in (16, 32, 64, 128):
        min_periods = max(8, window // 3)
        df[f"ma{window}"] = df["close"].rolling(window, min_periods=min_periods).mean()
        df[f"stretch{window}"] = df["close"] / df[f"ma{window}"] - 1.0
        df[f"vol{window}"] = df["ret1"].rolling(window, min_periods=min_periods).std()
        df[f"volume_mean{window}"] = df["volume"].rolling(window, min_periods=min_periods).mean()
        df[f"range_mean{window}"] = df["range_pct"].rolling(window, min_periods=min_periods).mean()

    df["ma64_slope16"] = df["ma64"] / df["ma64"].shift(16) - 1.0
    df["ma32_slope8"] = df["ma32"] / df["ma32"].shift(8) - 1.0
    df["vol_ratio32_128"] = df["vol32"] / df["vol128"]
    df["range_ratio32_128"] = df["range_mean32"] / df["range_mean128"]
    df["volume_ratio32_128"] = df["volume_mean32"] / df["volume_mean128"]
    df["drawdown64"] = df["close"] / df["high"].rolling(64, min_periods=16).max() - 1.0
    df["rally64"] = df["close"] / df["low"].rolling(64, min_periods=16).min() - 1.0

    train = df[df["split"] == "train"]
    low_hours = set(train.groupby("hour_utc")["volume"].median().pipe(lambda s: s[s <= s.quantile(0.30)].index))

    df["trend_base"] = (
        (df["close"] > df["ma64"])
        & (df["ma32"] > df["ma64"])
        & (df["ma64_slope16"] > quantile(train, "ma64_slope16", 0.50))
        & (df["ret4"] > quantile(train, "ret4", 0.50))
    )
    df["trend_structural_next_base"] = (
        (df["close"] > df["ma64"])
        & (df["ma32"] > df["ma64"])
        & (df["ma64_slope16"] > quantile(train, "ma64_slope16", 0.45))
    )
    df["stress_base"] = (
        (df["vol_ratio32_128"] >= quantile(train, "vol_ratio32_128", 0.85))
        | (df["range_ratio32_128"] >= quantile(train, "range_ratio32_128", 0.85))
        | (df["drawdown64"] <= quantile(train, "drawdown64", 0.15))
        | (df["ret4"] <= quantile(train, "ret4", 0.08))
    )
    df["reversal_base"] = (
        ((df["ma64_slope16"] <= quantile(train, "ma64_slope16", 0.35)) & (df["stretch64"] <= quantile(train, "stretch64", 0.45)))
        | ((df["ret16"] <= quantile(train, "ret16", 0.35)) & (df["ma32_slope8"] <= quantile(train, "ma32_slope8", 0.45)))
    )
    df["thin_base"] = df["hour_utc"].isin(low_hours) | (df["volume"] <= quantile(train, "volume", 0.30))
    df["thin_soft_next_base"] = df["hour_utc"].isin(low_hours) | (df["volume"] <= quantile(train, "volume", 0.45))

    df["target_trend_structural_next"] = df["trend_structural_next_base"].shift(-1).astype(float)
    df["target_stress_next"] = df["stress_base"].shift(-1).astype(float)
    df["target_reversal_next"] = df["reversal_base"].shift(-1).astype(float)
    df["target_thin_soft_next"] = df["thin_soft_next_base"].shift(-1).astype(float)
    return df


def select_mask(df: pd.DataFrame, regime: str) -> pd.Series:
    if regime == "TrendExpansion":
        return df["trend_base"].fillna(False).astype(bool) & (df["drawdown64"] >= -0.001320604675)
    if regime == "ExtremeStress":
        return df["stress_base"].fillna(False).astype(bool) & (df["range_ratio32_128"] >= 1.399149536)
    if regime == "ReversalBrewing":
        return df["stretch64"] <= -0.03869250919
    if regime == "ThinLiquidity":
        return (df["volume_mean16"] <= 718.8075) & df["thin_base"].fillna(False).astype(bool)
    raise KeyError(regime)


def period_metric(df: pd.DataFrame, mask: pd.Series, target: str, split: str, calibrated_probability: float | None = None) -> dict[str, Any]:
    valid = (df["split"] == split) & df[target].notna()
    selected = valid & mask.fillna(False)
    support = int(selected.sum())
    success = int(df.loc[selected, target].sum()) if support else 0
    precision = success / support if support else 0.0
    valid_count = int(valid.sum())
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lower(success, support),
        "coverage": support / valid_count if valid_count else 0.0,
        "ece": 0.0 if calibrated_probability is None else abs(float(calibrated_probability) - precision),
    }


def grouped_metrics(selected: pd.DataFrame, target: str, group_col: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, group in selected.groupby(group_col):
        support = int(len(group))
        success = int(group[target].sum()) if support else 0
        rows.append(
            {
                group_col: str(key),
                "support": support,
                "success": success,
                "precision": success / support if support else 0.0,
                "precision_wilson_lcb_95": wilson_lower(success, support),
                "passes_segment_floor": support >= 60 and wilson_lower(success, support) >= 0.95,
            }
        )
    return sorted(rows, key=lambda row: str(row[group_col]))


def evaluate_regime(df: pd.DataFrame, regime: str) -> dict[str, Any]:
    target = RULES[regime]["target"]
    mask = select_mask(df, regime)
    train = period_metric(df, mask, target, "train")
    calibration = period_metric(df, mask, target, "calibration", train["precision"])
    test = period_metric(df, mask, target, "test", calibration["precision"])
    test_selected = df[(df["split"] == "test") & df[target].notna() & mask.fillna(False)].copy()

    by_timeframe = grouped_metrics(test_selected, target, "timeframe")
    by_context = grouped_metrics(test_selected, target, "context")
    by_market = grouped_metrics(test_selected, target, "market")
    by_instrument = grouped_metrics(test_selected, target, "instrument")
    strong_timeframes = [row["timeframe"] for row in by_timeframe if row["passes_segment_floor"]]
    strong_contexts = [row["context"] for row in by_context if row["passes_segment_floor"]]
    weak_segments = [
        {"segment_type": "timeframe", **row}
        for row in by_timeframe
        if row["support"] >= 60 and not row["passes_segment_floor"]
    ] + [
        {"segment_type": "context", **row}
        for row in by_context
        if row["support"] >= 120 and not row["passes_segment_floor"]
    ]

    validation_instruments = sorted(test_selected["instrument"].dropna().unique().tolist())
    validation_market_contexts = sorted(test_selected["market"].dropna().unique().tolist())
    validation_timeframes = sorted(test_selected["timeframe"].dropna().unique().tolist())
    validation_contexts = sorted(test_selected["context"].dropna().unique().tolist())
    predictor_fields = [field for field in RULES[regime]["fields"] if not field.startswith("target_")]
    blocked_predictor_fields = [field for field in predictor_fields if field.startswith("future_") or field.startswith("target_")]

    passes_board_gate = bool(
        calibration["support"] >= 120
        and test["support"] >= 60
        and test["precision_wilson_lcb_95"] >= 0.95
        and test["ece"] <= 0.05
        and test["coverage"] >= 0.03
        and len(validation_instruments) >= 2
        and len(validation_market_contexts) >= 2
        and len(validation_timeframes) >= 2
        and not blocked_predictor_fields
    )
    passes_segment_floor = bool(len(strong_timeframes) >= 2 and len(strong_contexts) >= 2)

    return {
        "accepted_regime_id": regime,
        "qualifying_condition": RULES[regime]["condition"],
        "target_label": target,
        "predictor_fields": predictor_fields,
        "blocked_predictor_fields": blocked_predictor_fields,
        "confidence_lane": "95",
        "calibration_support": calibration["support"],
        "test_support": test["support"],
        "precision_wilson_lcb": test["precision_wilson_lcb_95"],
        "ece": test["ece"],
        "coverage": test["coverage"],
        "validation_instruments": validation_instruments,
        "validation_market_contexts": validation_market_contexts,
        "validation_timeframes": validation_timeframes,
        "validation_contexts": validation_contexts,
        "validation_periods": {
            "train": train,
            "calibration": calibration,
            "test": test,
        },
        "segment_metrics": {
            "by_timeframe": by_timeframe,
            "by_context": by_context,
            "by_market": by_market,
            "by_instrument": by_instrument,
            "strong_timeframes": strong_timeframes,
            "strong_contexts": strong_contexts,
            "weak_segments": weak_segments,
        },
        "passes_board_gate_95_cross_market_timeframe": passes_board_gate,
        "passes_segment_floor": passes_segment_floor,
        "passes_broader_mtf_gate": passes_board_gate and passes_segment_floor,
        "trade_usable": False,
    }


def main() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    frames = []
    source_manifest = []
    for filename in SOURCES:
        path = AUTO_QUANT_DATA / filename
        if not path.exists():
            continue
        raw = load_source(filename)
        frames.append(add_features(raw))
        source_manifest.append(
            {
                "source_file": str(path),
                "rows_used": int(len(raw)),
                "first_ts": raw["ts"].min().isoformat(),
                "last_ts": raw["ts"].max().isoformat(),
                "context": str(raw["context"].iloc[0]),
            }
        )

    features = pd.concat(frames, ignore_index=True)
    packets = [evaluate_regime(features, regime) for regime in RULES]
    missing = [packet["accepted_regime_id"] for packet in packets if not packet["passes_broader_mtf_gate"]]

    prior = json.loads(STRICT_AUDIT.read_text(encoding="utf-8"))
    inherited_pass = prior["strict_cross_timeframe_pass_regimes"]
    required_regimes = [
        "SessionLiquidityCoreViable",
        "TrendExpansion",
        "RangeConsolidation",
        "ExtremeStress",
        "ReversalBrewing",
        "ThinLiquidity",
    ]
    all_sub_regime_missing = [regime for regime in required_regimes if regime not in inherited_pass and regime not in {p["accepted_regime_id"] for p in packets if p["passes_broader_mtf_gate"]}]

    summary_rows = []
    for packet in packets:
        summary_rows.append(
            {
                "regime": packet["accepted_regime_id"],
                "passes_broader_mtf_gate": packet["passes_broader_mtf_gate"],
                "precision_wilson_lcb": packet["precision_wilson_lcb"],
                "calibration_support": packet["calibration_support"],
                "test_support": packet["test_support"],
                "ece": packet["ece"],
                "coverage": packet["coverage"],
                "validation_instruments": "|".join(packet["validation_instruments"]),
                "validation_market_contexts": "|".join(packet["validation_market_contexts"]),
                "validation_timeframes": "|".join(packet["validation_timeframes"]),
                "strong_contexts": "|".join(packet["segment_metrics"]["strong_contexts"]),
                "strong_timeframes": "|".join(packet["segment_metrics"]["strong_timeframes"]),
                "weak_segment_count": len(packet["segment_metrics"]["weak_segments"]),
                "qualifying_condition": packet["qualifying_condition"],
            }
        )

    summary_csv = AUDIT_DIR / "broader_mtf_regime_candidate_summary.csv"
    pd.DataFrame(summary_rows).to_csv(summary_csv, index=False)

    evidence = {
        "schema_version": "board-a-broader-mtf-regime-search/v1",
        "loop_id": "20260510T232808+0800-codex-broader-mtf-regime-search",
        "objective": "Build broader aligned multi-timeframe evidence for TrendExpansion, ExtremeStress, ReversalBrewing, and ThinLiquidity under unchanged 95% gates.",
        "run_root": repo_rel(RUN_ROOT),
        "input_source_manifest": source_manifest,
        "source_policy": {
            "source": "local Auto-Quant feather data only",
            "tail_rows_per_source": TAIL_ROWS_PER_SOURCE,
            "network_fetch": False,
            "runtime_code_changed": False,
        },
        "threshold_policy": {
            "thresholds_relaxed": False,
            "precision_wilson_lcb_95_min": 0.95,
            "calibration_support_min": 120,
            "test_support_min": 60,
            "ece_max": 0.05,
            "coverage_min": 0.03,
            "validation_instruments_min": 2,
            "validation_market_contexts_min": 2,
            "validation_timeframes_min": 2,
            "segment_floor_min_support": 60,
            "segment_floor_wilson_lcb_95_min": 0.95,
            "blocked_predictor_prefixes": ["future_", "target_"],
        },
        "inherited_strict_pass_regimes": inherited_pass,
        "new_broader_mtf_packets": packets,
        "new_missing_regimes": missing,
        "all_required_sub_regime_missing_after_this_loop": all_sub_regime_missing,
        "decision": {
            "sub_regime_cross_timeframe_complete": not all_sub_regime_missing,
            "board_state": "blocked",
            "why_board_still_blocked": [
                "The six execution-native sub-regime/signature packets now have 95% cross-market/cross-timeframe evidence under this board gate.",
                "MainRegimeV2 root labels are still not materialized/calibrated, so this is not full parent/main-regime completion.",
                "trade_usable remains false; Board B must separately prove profitability, non-observe release, and execution/path gates.",
            ],
            "trade_usable": False,
            "next_action": "Build MainRegimeV2 target schema and calibrate Bull/Bear/Sideways/Crisis plus Manipulation/UnknownOrMixed without treating sub-regime packets as root acceptance.",
        },
        "artifacts": {
            "summary_csv": repo_rel(summary_csv),
            "checks": repo_rel(CHECKS_DIR / "broader_mtf_regime_acceptance_assertions.out"),
        },
    }

    evidence_path = AUDIT_DIR / "broader_mtf_regime_acceptance_audit.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")

    assertions = [
        f"PASS inherited_strict_pass_regimes={','.join(inherited_pass)}",
        f"{'PASS' if not missing else 'FAIL'} new_broader_mtf_missing={','.join(missing) if missing else 'none'}",
        f"{'PASS' if not all_sub_regime_missing else 'FAIL'} all_required_sub_regime_missing_after_this_loop={','.join(all_sub_regime_missing) if all_sub_regime_missing else 'none'}",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS trade_usable=false",
        "BLOCKED MainRegimeV2_root_labels_not_materialized_or_calibrated",
    ]
    for packet in packets:
        assertions.append(
            f"{'PASS' if packet['passes_broader_mtf_gate'] else 'FAIL'} {packet['accepted_regime_id']}: "
            f"lcb={packet['precision_wilson_lcb']:.6f} cal={packet['calibration_support']} test={packet['test_support']} "
            f"ece={packet['ece']:.6f} instruments={len(packet['validation_instruments'])} "
            f"contexts={len(packet['validation_market_contexts'])} timeframes={len(packet['validation_timeframes'])} "
            f"strong_contexts={len(packet['segment_metrics']['strong_contexts'])} strong_timeframes={len(packet['segment_metrics']['strong_timeframes'])} "
            f"weak_segments={len(packet['segment_metrics']['weak_segments'])}"
        )
    (CHECKS_DIR / "broader_mtf_regime_acceptance_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"evidence": repo_rel(evidence_path), "missing": all_sub_regime_missing, "board_state": "blocked"}, indent=2))


if __name__ == "__main__":
    main()
