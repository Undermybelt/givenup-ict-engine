from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T202359-hermes-cross-market-regime-validation"
OUT_DIR = RUN_ROOT / "cross-market"

SOURCE_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T185358-codex-accepted95-full-chain"
QQQ_IBKR = SOURCE_ROOT / "provider/ibkr_QQQ_1h.csv"
QQQ_YFINANCE = SOURCE_ROOT / "provider/yf_QQQ_1h_20240601_20260509.csv"
NQ_LTF = SOURCE_ROOT / "state/NQ/analyze_live_20260510T110505_ltf.json"
KRAKEN_XBT = SOURCE_ROOT / "provider/kraken_PF_XBTUSD_1h_2024_2025.csv"
SESSION_LIQUIDITY = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T184532-codex-session-liquidity/session-liquidity/session_liquidity_regime_probe_report.json"
FULL_CHAIN_REAUDIT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T200154-hermes-loop-full-chain-reaudit/evidence_packet_full_chain_reaudit.json"

Z95 = 1.959963984540054
Z99 = 2.5758293035489004


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lower(success: int, total: int, z: float = Z95) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    centre = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def split_indices(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    train_end = n // 2
    cal_end = (n * 3) // 4
    return np.arange(0, train_end), np.arange(train_end, cal_end), np.arange(cal_end, n)


def pct_rank(series: pd.Series, window: int, min_periods: int | None = None) -> pd.Series:
    minp = min_periods if min_periods is not None else max(20, window // 4)

    def last_rank(values: np.ndarray) -> float:
        s = pd.Series(values)
        return float(s.rank(pct=True).iloc[-1])

    return series.rolling(window, min_periods=minp).apply(last_rank, raw=True)


def load_csv_ohlcv(path: Path, ts_col: str, instrument: str, market: str, timeframe: str, timeframe_minutes: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["ts"] = pd.to_datetime(df[ts_col], utc=True).dt.floor(f"{timeframe_minutes}min")
    df = df.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if "count" in df.columns:
        df["count"] = pd.to_numeric(df["count"], errors="coerce")
    else:
        df["count"] = np.nan
    df["instrument"] = instrument
    df["market"] = market
    df["timeframe"] = timeframe
    df["timeframe_minutes"] = timeframe_minutes
    return df[["ts", "instrument", "market", "timeframe", "timeframe_minutes", "open", "high", "low", "close", "volume", "count"]].dropna(subset=["open", "high", "low", "close"])


def load_nq_15m() -> pd.DataFrame:
    payload = json.loads(NQ_LTF.read_text())
    df = pd.DataFrame(payload["candles"])
    df["ts"] = pd.to_datetime(df["timestamp"], utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["count"] = np.nan
    df["instrument"] = "NQ"
    df["market"] = "CME futures"
    df["timeframe"] = "15m"
    df["timeframe_minutes"] = 15
    return df[["ts", "instrument", "market", "timeframe", "timeframe_minutes", "open", "high", "low", "close", "volume", "count"]].dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)


def load_universe() -> list[dict[str, Any]]:
    return [
        {
            "instrument": "QQQ",
            "market": "US ETF / IBKR",
            "timeframe": "1h",
            "path": QQQ_IBKR,
            "rows": load_csv_ohlcv(QQQ_IBKR, "ts", "QQQ", "US ETF / IBKR", "1h", 60),
        },
        {
            "instrument": "QQQ",
            "market": "US ETF / yfinance",
            "timeframe": "1h",
            "path": QQQ_YFINANCE,
            "rows": load_csv_ohlcv(QQQ_YFINANCE, "date", "QQQ", "US ETF / yfinance", "1h", 60),
        },
        {
            "instrument": "NQ",
            "market": "CME futures",
            "timeframe": "15m",
            "path": NQ_LTF,
            "rows": load_nq_15m(),
        },
        {
            "instrument": "PF_XBTUSD",
            "market": "Kraken crypto",
            "timeframe": "1h",
            "path": KRAKEN_XBT,
            "rows": load_csv_ohlcv(KRAKEN_XBT, "date", "PF_XBTUSD", "Kraken crypto", "1h", 60),
        },
    ]


def feature_frame(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    df = raw.sort_values("ts").reset_index(drop=True).copy()
    horizon_bars = max(4, int(round(480 / int(df["timeframe_minutes"].iloc[0]))))
    volume_horizon_bars = max(4, int(round(240 / int(df["timeframe_minutes"].iloc[0]))))
    df["ret_1"] = np.log(df["close"]).diff()
    df["ret_4"] = np.log(df["close"] / df["close"].shift(4))
    df["ma_32"] = df["close"].rolling(32, min_periods=12).mean()
    df["stretch_32"] = df["close"] / df["ma_32"] - 1.0
    df["range_pct"] = (df["high"] - df["low"]) / df["close"]
    df["realized_vol_16"] = df["ret_1"].rolling(16, min_periods=8).std()
    df["realized_vol_rank_252"] = pct_rank(df["realized_vol_16"], 252, min_periods=64)
    df["range_rank_252"] = pct_rank(df["range_pct"], 252, min_periods=64)
    df["volume_rank_252"] = pct_rank(df["volume"], 252, min_periods=64)
    df["stretch_abs_rank_252"] = pct_rank(df["stretch_32"].abs(), 252, min_periods=64)

    future_close = df["close"].shift(-horizon_bars)
    future_high = pd.concat([df["high"].shift(-i) for i in range(1, horizon_bars + 1)], axis=1).max(axis=1)
    future_low = pd.concat([df["low"].shift(-i) for i in range(1, horizon_bars + 1)], axis=1).min(axis=1)
    future_volume = pd.concat([df["volume"].shift(-i) for i in range(1, volume_horizon_bars + 1)], axis=1).median(axis=1)
    future_count = pd.concat([df["count"].shift(-i) for i in range(1, volume_horizon_bars + 1)], axis=1).median(axis=1)
    df["future_ret_h8h"] = future_close / df["close"] - 1.0
    df["future_absret_h8h"] = df["future_ret_h8h"].abs()
    df["future_max_up_h8h"] = future_high / df["close"] - 1.0
    df["future_max_down_h8h"] = future_low / df["close"] - 1.0
    df["future_range_h8h"] = (future_high - future_low) / df["close"]
    df["future_median_volume_h4h"] = future_volume
    df["future_median_count_h4h"] = future_count

    train_idx, _, _ = split_indices(len(df))
    train = df.iloc[train_idx]
    thresholds = {
        "horizon_bars_8h": float(horizon_bars),
        "volume_horizon_bars_4h": float(volume_horizon_bars),
        "trend_ret_q70": float(train["future_ret_h8h"].quantile(0.70)),
        "absret_low_q35": float(train["future_absret_h8h"].quantile(0.35)),
        "range_low_q35": float(train["future_range_h8h"].quantile(0.35)),
        "absret_high_q90": float(train["future_absret_h8h"].quantile(0.90)),
        "drawdown_bad_q10": float(train["future_max_down_h8h"].quantile(0.10)),
        "reversal_move_q65": float(train["future_absret_h8h"].quantile(0.65)),
        "ret4_pos_q60": float(train["ret_4"].quantile(0.60)),
        "ret4_abs_low_q40": float(train["ret_4"].abs().quantile(0.40)),
        "stretch_abs_q80": float(train["stretch_32"].abs().quantile(0.80)),
        "volume_low_q30": float(train["volume"].quantile(0.30)),
        "count_low_q30": float(train["count"].quantile(0.30)) if train["count"].notna().any() else float("nan"),
    }

    df["condition_trend_expansion"] = (
        (df["ret_4"] > thresholds["ret4_pos_q60"])
        & (df["close"] > df["ma_32"])
        & (df["volume_rank_252"].fillna(0.5) >= 0.35)
    )
    df["target_trend_expansion"] = (
        (df["future_ret_h8h"] >= thresholds["trend_ret_q70"])
        & (df["future_max_down_h8h"] > -max(0.004, thresholds["absret_high_q90"] * 0.45))
    )

    df["condition_range_consolidation"] = (
        (df["ret_4"].abs() <= thresholds["ret4_abs_low_q40"])
        & (df["realized_vol_rank_252"].fillna(0.5) <= 0.45)
        & (df["range_rank_252"].fillna(0.5) <= 0.55)
    )
    df["target_range_consolidation"] = (
        (df["future_absret_h8h"] <= thresholds["absret_low_q35"])
        & (df["future_range_h8h"] <= thresholds["range_low_q35"])
    )

    df["condition_extreme_stress"] = (
        (df["realized_vol_rank_252"].fillna(0.0) >= 0.85)
        | (df["range_rank_252"].fillna(0.0) >= 0.85)
        | (df["ret_4"] <= train["ret_4"].quantile(0.10))
    )
    df["target_extreme_stress"] = (
        (df["future_absret_h8h"] >= thresholds["absret_high_q90"])
        | (df["future_max_down_h8h"] <= thresholds["drawdown_bad_q10"])
    )

    stretch_sign = np.sign(df["stretch_32"].fillna(0.0))
    future_sign = np.sign(df["future_ret_h8h"].fillna(0.0))
    df["condition_reversal_brewing"] = (
        (df["stretch_32"].abs() >= thresholds["stretch_abs_q80"])
        & (df["volume_rank_252"].fillna(0.5) >= 0.25)
    )
    df["target_reversal_brewing"] = (
        (stretch_sign != 0)
        & (future_sign != 0)
        & (stretch_sign != future_sign)
        & (df["future_absret_h8h"] >= thresholds["reversal_move_q65"])
    )

    count_thin = df["future_median_count_h4h"] <= thresholds["count_low_q30"] if math.isfinite(thresholds["count_low_q30"]) else False
    df["condition_thin_liquidity"] = (
        (df["volume_rank_252"].fillna(0.5) <= 0.30)
        | (df["volume"] <= thresholds["volume_low_q30"])
        | ((df["count"] <= thresholds["count_low_q30"]) if math.isfinite(thresholds["count_low_q30"]) else False)
    )
    df["target_thin_liquidity"] = (
        (df["future_median_volume_h4h"] <= thresholds["volume_low_q30"])
        | count_thin
    )

    target_cols = [c for c in df.columns if c.startswith("target_")]
    for col in target_cols:
        df[col] = df[col].astype(float)
    df.loc[df["future_ret_h8h"].isna(), target_cols] = np.nan
    df.loc[df["future_median_volume_h4h"].isna(), "target_thin_liquidity"] = np.nan
    return df, thresholds


REGIMES = [
    {
        "regime_id": "TrendExpansion",
        "condition": "condition_trend_expansion",
        "target": "target_trend_expansion",
        "condition_definition": "ret_4 > train q60, close > rolling MA32, and volume rank >= 0.35",
        "target_definition": "future 8h return >= train q70 and interim drawdown not worse than stress-scaled drawdown floor",
        "allowed_action": "release_candidate_only_when_other_gates_pass",
    },
    {
        "regime_id": "RangeConsolidation",
        "condition": "condition_range_consolidation",
        "target": "target_range_consolidation",
        "condition_definition": "|ret_4| <= train q40, realized-vol rank <= 0.45, and range rank <= 0.55",
        "target_definition": "future 8h absolute return and future 8h range both below train q35",
        "allowed_action": "observe_or_mean_reversion_candidate_only_when_other_gates_pass",
    },
    {
        "regime_id": "ExtremeStress",
        "condition": "condition_extreme_stress",
        "target": "target_extreme_stress",
        "condition_definition": "realized-vol rank >= 0.85, range rank >= 0.85, or ret_4 <= train q10",
        "target_definition": "future 8h absolute return >= train q90 or future max drawdown <= train q10 drawdown",
        "allowed_action": "guardrail_only_reduce_or_block_release",
    },
    {
        "regime_id": "ReversalBrewing",
        "condition": "condition_reversal_brewing",
        "target": "target_reversal_brewing",
        "condition_definition": "|stretch from MA32| >= train q80 and volume rank >= 0.25",
        "target_definition": "future 8h move reverses current MA32 stretch sign with magnitude >= train q65",
        "allowed_action": "observe_or_reversal_candidate_only_when_other_gates_pass",
    },
    {
        "regime_id": "ThinLiquidity",
        "condition": "condition_thin_liquidity",
        "target": "target_thin_liquidity",
        "condition_definition": "volume rank <= 0.30, raw volume <= train q30, or IBKR count <= train q30 when count is available",
        "target_definition": "future 4h median volume <= train q30, or future IBKR count <= train q30 when count is available",
        "allowed_action": "guardrail_only_liquidity_context",
    },
]


def metric_for_split(df: pd.DataFrame, idx: np.ndarray, condition: str, target: str, calibrated_probability: float | None = None) -> dict[str, Any]:
    rows = df.iloc[idx]
    valid = rows[target].notna() & rows[condition].notna()
    rows = rows[valid]
    selected = rows[condition].astype(bool)
    selected_rows = rows[selected]
    support = int(len(selected_rows))
    success = int(selected_rows[target].fillna(False).astype(bool).sum()) if support else 0
    precision = success / support if support else 0.0
    prob = precision if calibrated_probability is None else calibrated_probability
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lower(success, support, Z95),
        "precision_wilson_lcb_99": wilson_lower(success, support, Z99),
        "coverage": support / len(rows) if len(rows) else 0.0,
        "ece": abs(prob - precision) if support else None,
        "calibrated_probability": prob,
    }


def time_range(df: pd.DataFrame, idx: np.ndarray) -> dict[str, str]:
    if len(idx) == 0:
        return {"start": "", "end": ""}
    rows = df.iloc[idx]
    return {"start": str(rows["ts"].min()), "end": str(rows["ts"].max())}


def evaluate_dataset(dataset: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    df, thresholds = feature_frame(dataset["rows"])
    train_idx, cal_idx, test_idx = split_indices(len(df))
    results = []
    for spec in REGIMES:
        cal = metric_for_split(df, cal_idx, spec["condition"], spec["target"])
        test = metric_for_split(df, test_idx, spec["condition"], spec["target"], cal["precision"])
        pass95 = (
            cal["support"] >= 120
            and test["support"] >= 60
            and cal["precision_wilson_lcb_95"] >= 0.95
            and test["precision_wilson_lcb_95"] >= 0.95
            and test["ece"] is not None
            and test["ece"] <= 0.05
            and test["coverage"] >= 0.03
        )
        pass99 = (
            cal["support"] >= 300
            and test["support"] >= 120
            and cal["precision_wilson_lcb_99"] >= 0.99
            and test["precision_wilson_lcb_99"] >= 0.99
            and test["ece"] is not None
            and test["ece"] <= 0.02
            and test["coverage"] >= 0.02
        )
        blockers = []
        if cal["support"] < 120:
            blockers.append("calibration_support_below_120")
        if test["support"] < 60:
            blockers.append("test_support_below_60")
        if cal["precision_wilson_lcb_95"] < 0.95 or test["precision_wilson_lcb_95"] < 0.95:
            blockers.append("wilson95_below_0_95")
        if test["ece"] is None or test["ece"] > 0.05:
            blockers.append("ece_above_0_05")
        if test["coverage"] < 0.03:
            blockers.append("coverage_below_0_03")
        results.append(
            {
                "regime_id": spec["regime_id"],
                "instrument": dataset["instrument"],
                "market": dataset["market"],
                "timeframe": dataset["timeframe"],
                "allowed_action": spec["allowed_action"],
                "condition": spec["condition"],
                "target": spec["target"],
                "condition_definition": spec["condition_definition"],
                "target_definition": spec["target_definition"],
                "calibration": cal,
                "test": test,
                "passes_95": pass95,
                "passes_99": pass99,
                "blocker": "none" if pass95 else ";".join(blockers),
            }
        )
    summary = {
        "instrument": dataset["instrument"],
        "market": dataset["market"],
        "timeframe": dataset["timeframe"],
        "source_path": repo_rel(dataset["path"]),
        "rows": int(len(df)),
        "split": {
            "train": int(len(train_idx)),
            "calibration": int(len(cal_idx)),
            "test": int(len(test_idx)),
            "train_time_range": time_range(df, train_idx),
            "calibration_time_range": time_range(df, cal_idx),
            "test_time_range": time_range(df, test_idx),
        },
        "thresholds_from_train_split": thresholds,
        "regime_results": results,
    }
    return df, summary


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    datasets = load_universe()
    feature_tables = []
    dataset_summaries = []
    for dataset in datasets:
        df, summary = evaluate_dataset(dataset)
        feature_cols = [
            "ts",
            "instrument",
            "market",
            "timeframe",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "count",
            "ret_1",
            "ret_4",
            "stretch_32",
            "range_pct",
            "realized_vol_rank_252",
            "range_rank_252",
            "volume_rank_252",
            "stretch_abs_rank_252",
            "future_ret_h8h",
            "future_absret_h8h",
            "future_range_h8h",
            "future_median_volume_h4h",
        ]
        for spec in REGIMES:
            feature_cols.extend([spec["condition"], spec["target"]])
        feature_tables.append(df[[c for c in feature_cols if c in df.columns]])
        dataset_summaries.append(summary)

    features_path = OUT_DIR / "cross_market_regime_features_and_labels.csv"
    pd.concat(feature_tables, ignore_index=True).to_csv(features_path, index=False)

    by_regime = []
    for spec in REGIMES:
        rows = []
        for dataset in dataset_summaries:
            match = next(r for r in dataset["regime_results"] if r["regime_id"] == spec["regime_id"])
            rows.append(match)
        validation_contexts = [
            f"{row['instrument']}:{row['market']}:{row['timeframe']}"
            for row in rows
            if row["calibration"]["support"] > 0 and row["test"]["support"] > 0
        ]
        markets = sorted({row["market"] for row in rows if row["calibration"]["support"] > 0 and row["test"]["support"] > 0})
        timeframes = sorted({row["timeframe"] for row in rows if row["calibration"]["support"] > 0 and row["test"]["support"] > 0})
        by_regime.append(
            {
                "regime_id": spec["regime_id"],
                "condition_definition": spec["condition_definition"],
                "target_definition": spec["target_definition"],
                "allowed_action": spec["allowed_action"],
                "validation_contexts": validation_contexts,
                "market_count": len(markets),
                "timeframe_count": len(timeframes),
                "instrument_result_count": len(validation_contexts),
                "passes_cross_market_coverage_floor": len(validation_contexts) >= 3 and len(markets) >= 3 and len(timeframes) >= 2,
                "passes_95_anywhere": any(row["passes_95"] for row in rows),
                "passes_99_anywhere": any(row["passes_99"] for row in rows),
                "instrument_results": rows,
            }
        )

    session = json.loads(SESSION_LIQUIDITY.read_text())
    full_chain = json.loads(FULL_CHAIN_REAUDIT.read_text())
    evidence = {
        "schema_version": "board-a-cross-market-regime-condition-validation/v1",
        "loop_id": "20260510T202359+0800-cross-market-regime-condition-validation",
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Every regime must have explicit qualifying conditions and validation across different instruments, times, and markets.",
        "feature_table": repo_rel(features_path),
        "input_sources": {
            "QQQ_IBKR_1h": repo_rel(QQQ_IBKR),
            "QQQ_yfinance_1h": repo_rel(QQQ_YFINANCE),
            "NQ_15m_cache": repo_rel(NQ_LTF),
            "Kraken_PF_XBTUSD_1h": repo_rel(KRAKEN_XBT),
            "existing_accepted_session_liquidity": repo_rel(SESSION_LIQUIDITY),
            "full_chain_reaudit": repo_rel(FULL_CHAIN_REAUDIT),
        },
        "validation_universe": [
            {k: dataset[k] for k in ["instrument", "market", "timeframe"]}
            | {"source_path": repo_rel(dataset["path"]), "rows": int(len(dataset["rows"]))}
            for dataset in datasets
        ],
        "threshold_policy": {
            "thresholds_relaxed": False,
            "thresholds_are_train_split_local": True,
            "precision_wilson_lcb_95": 0.95,
            "precision_wilson_lcb_99": 0.99,
            "calibration_support_min_95": 120,
            "test_support_min_95": 60,
            "ece_max_95": 0.05,
            "coverage_min_95": 0.03,
            "cross_market_coverage_floor": ">=3 instrument/market/timeframe contexts, >=3 market labels, >=2 timeframes",
        },
        "dataset_summaries": dataset_summaries,
        "regime_condition_matrix": by_regime,
        "existing_accepted_context": {
            "accepted_regime_id": session["accepted_packet"]["accepted_regime_id"],
            "confidence_lane": session["accepted_packet"]["confidence_lane"],
            "precision_wilson_lcb": session["accepted_packet"]["precision_wilson_lcb"],
            "artifact_path": session["accepted_packet"]["artifact_path"],
            "kept_as_primary_gate": True,
        },
        "full_chain_context": {
            "source_artifact": repo_rel(FULL_CHAIN_REAUDIT),
            "provider_key_readiness": full_chain["provider_status"]["key_readiness"],
            "bbn_apply": full_chain["bbn_apply"],
            "catboost_path_ranker": {
                "score_model_family": full_chain["catboost_path_ranker"]["score_model_family"],
                "raw_scored_mature_rows": full_chain["catboost_path_ranker"]["raw_scored_mature_rows"],
                "production_validation_rows": full_chain["catboost_path_ranker"]["production_validation_rows"],
                "current_path_ranker_gate": full_chain["catboost_path_ranker"]["current_path_ranker_gate"],
            },
            "execution_tree": {
                "status": full_chain["workflow_and_execution"]["execution_tree_status"],
                "promote_candidate": full_chain["workflow_and_execution"]["execution_tree_promote_candidate"],
                "branch": full_chain["workflow_and_execution"]["execution_tree_branch"],
            },
        },
        "decision": {
            "condition_matrix_complete": all(item["passes_cross_market_coverage_floor"] for item in by_regime),
            "accepted_gate": "accepted_95_existing_SessionLiquidityCoreViable_only",
            "accepted_new_regime_count_95": sum(1 for item in by_regime if item["passes_95_anywhere"]),
            "accepted_new_regime_count_99": sum(1 for item in by_regime if item["passes_99_anywhere"]),
            "trade_usable": False,
            "not_promoted_reason": "This run validates condition coverage breadth; it does not create a non-observe release candidate with path-specific edge.",
            "next_action": "Use the cross-market condition matrix to target missing support/Wilson/ECE blockers; do not promote any regime until it passes unchanged thresholds across the required market contexts.",
        },
    }

    report_path = OUT_DIR / "cross_market_regime_condition_matrix.json"
    evidence_path = RUN_ROOT / "evidence_packet_cross_market_regime_validation.json"
    report_path.write_text(json.dumps(evidence, indent=2) + "\n")
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n")
    (RUN_ROOT / "README.md").write_text(
        "# Board A Cross-Market Regime Condition Validation\n\n"
        "This run adds explicit qualifying conditions for every Board A regime and validates each condition across QQQ, NQ, and Kraken XBTUSD contexts.\n\n"
        f"- Evidence packet: `{repo_rel(evidence_path)}`\n"
        f"- Condition matrix: `{repo_rel(report_path)}`\n"
        f"- Feature/label table: `{repo_rel(features_path)}`\n"
        f"- Full-chain context: `{repo_rel(FULL_CHAIN_REAUDIT)}`\n\n"
        "The existing `SessionLiquidityCoreViable` 95% packet remains the only accepted Board A gate. This run does not claim 99% confidence or trade/execute readiness.\n"
    )
    print(
        json.dumps(
            {
                "evidence": repo_rel(evidence_path),
                "condition_matrix": repo_rel(report_path),
                "condition_matrix_complete": evidence["decision"]["condition_matrix_complete"],
                "regimes": [
                    {
                        "regime_id": item["regime_id"],
                        "contexts": len(item["validation_contexts"]),
                        "markets": item["market_count"],
                        "timeframes": item["timeframe_count"],
                        "passes_95_anywhere": item["passes_95_anywhere"],
                    }
                    for item in by_regime
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
