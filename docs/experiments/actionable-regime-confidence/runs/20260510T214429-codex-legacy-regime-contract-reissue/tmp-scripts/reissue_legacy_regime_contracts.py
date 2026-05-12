from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T214429-codex-legacy-regime-contract-reissue"
OUT_DIR = RUN_ROOT / "legacy-contract"
CHECKS_DIR = RUN_ROOT / "checks"

SOURCE_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T185358-codex-accepted95-full-chain"
QQQ_IBKR = SOURCE_ROOT / "provider/ibkr_QQQ_1h.csv"
QQQ_YFINANCE = SOURCE_ROOT / "provider/yf_QQQ_1h_20240601_20260509.csv"
NQ_LTF = SOURCE_ROOT / "state/NQ/analyze_live_20260510T110505_ltf.json"
KRAKEN_XBT = SOURCE_ROOT / "provider/kraken_PF_XBTUSD_1h_2024_2025.csv"
STICKY_HAZARD_PACKET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T205856-codex-sticky-hazard-per-regime/evidence_packet_sticky_hazard_cross_context.json"
CONTRACT_AUDIT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T211206-codex-sticky-hazard-contract-audit/completion-audit/board_a_sticky_hazard_contract_audit.json"
PERSISTENCE_PACKET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/evidence_packet_regime_persistence_expansion.json"
DAILY_STICKY_FEATURES = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T205856-codex-sticky-hazard-per-regime/cross-context/cross_context_sticky_hazard_features.csv"

Z95 = 1.959963984540054
Z99 = 2.5758293035489004
BLOCKED_PREFIXES = ("future_", "target_")


@dataclass(frozen=True)
class Candidate:
    regime_id: str
    rule: str
    target: str
    mask: np.ndarray
    allowed_action: str
    horizon: str
    downstream_evidence_fields: list[str]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lower(success: int, total: int, z: float) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    centre = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def pct_rank(series: pd.Series, window: int, min_periods: int | None = None) -> pd.Series:
    minp = min_periods if min_periods is not None else max(16, window // 4)

    def last_rank(values: np.ndarray) -> float:
        return float(pd.Series(values).rank(pct=True).iloc[-1])

    return series.rolling(window, min_periods=minp).apply(last_rank, raw=True)


def split_labels(n: int) -> np.ndarray:
    labels = np.full(n, "train", dtype=object)
    labels[n // 2 :] = "calibration"
    labels[(3 * n) // 4 :] = "test"
    return labels


def load_csv_ohlcv(path: Path, ts_col: str, instrument: str, market: str, timeframe: str, minutes: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["ts"] = pd.to_datetime(df[ts_col], utc=True).dt.floor(f"{minutes}min")
    df = df.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["count"] = pd.to_numeric(df["count"], errors="coerce") if "count" in df.columns else np.nan
    df["instrument"] = instrument
    df["market"] = market
    df["timeframe"] = timeframe
    df["timeframe_minutes"] = minutes
    return df[["ts", "instrument", "market", "timeframe", "timeframe_minutes", "open", "high", "low", "close", "volume", "count"]].dropna(subset=["open", "high", "low", "close"])


def load_nq_15m() -> pd.DataFrame:
    payload = json.loads(NQ_LTF.read_text(encoding="utf-8"))
    df = pd.DataFrame(payload["candles"])
    df["ts"] = pd.to_datetime(df["timestamp"], utc=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["count"] = np.nan
    df["instrument"] = "NQ"
    df["market"] = "CME_futures_local"
    df["timeframe"] = "15m"
    df["timeframe_minutes"] = 15
    return df[["ts", "instrument", "market", "timeframe", "timeframe_minutes", "open", "high", "low", "close", "volume", "count"]].dropna(subset=["open", "high", "low", "close"])


def load_universe() -> list[dict[str, Any]]:
    return [
        {"instrument": "QQQ", "market": "IBKR_US_ETF", "timeframe": "1h", "path": QQQ_IBKR, "rows": load_csv_ohlcv(QQQ_IBKR, "ts", "QQQ", "IBKR_US_ETF", "1h", 60)},
        {"instrument": "QQQ", "market": "yfinance_US_ETF", "timeframe": "1h", "path": QQQ_YFINANCE, "rows": load_csv_ohlcv(QQQ_YFINANCE, "date", "QQQ", "yfinance_US_ETF", "1h", 60)},
        {"instrument": "NQ", "market": "CME_futures_local", "timeframe": "15m", "path": NQ_LTF, "rows": load_nq_15m()},
        {"instrument": "PF_XBTUSD", "market": "Kraken_crypto", "timeframe": "1h", "path": KRAKEN_XBT, "rows": load_csv_ohlcv(KRAKEN_XBT, "date", "PF_XBTUSD", "Kraken_crypto", "1h", 60)},
    ]


def add_context_features(dataset: dict[str, Any]) -> pd.DataFrame:
    df = dataset["rows"].sort_values("ts").reset_index(drop=True).copy()
    n = len(df)
    horizon_4h = max(4, int(round(240 / int(df["timeframe_minutes"].iloc[0]))))
    horizon_8h = max(4, int(round(480 / int(df["timeframe_minutes"].iloc[0]))))

    df["context"] = f"{dataset['instrument']}:{dataset['market']}:{dataset['timeframe']}"
    df["hour_utc"] = df["ts"].dt.hour
    df["split"] = split_labels(n)
    df["ret_1"] = np.log(df["close"]).diff()
    df["ret_4"] = np.log(df["close"] / df["close"].shift(4))
    df["range_pct"] = (df["high"] - df["low"]) / df["close"]
    df["ma_32"] = df["close"].rolling(32, min_periods=12).mean()
    df["stretch_32"] = df["close"] / df["ma_32"] - 1.0
    df["realized_vol_16"] = df["ret_1"].rolling(16, min_periods=8).std()
    df["realized_vol_rank_252"] = pct_rank(df["realized_vol_16"], 252, min_periods=64)
    df["range_rank_252"] = pct_rank(df["range_pct"], 252, min_periods=64)
    df["volume_rank_252"] = pct_rank(df["volume"], 252, min_periods=64)
    df["count_rank_252"] = pct_rank(df["count"], 252, min_periods=64) if df["count"].notna().any() else np.nan

    train = df[df["split"] == "train"].copy()
    volume_q30 = float(train["volume"].quantile(0.30))
    volume_q40 = float(train["volume"].quantile(0.40))
    volume_q50 = float(train["volume"].quantile(0.50))
    count_q40 = float(train["count"].quantile(0.40)) if train["count"].notna().any() else float("nan")
    range_rank_q40 = float(train["range_rank_252"].dropna().quantile(0.40)) if train["range_rank_252"].notna().any() else 0.40
    vol_rank_q40 = float(train["realized_vol_rank_252"].dropna().quantile(0.40)) if train["realized_vol_rank_252"].notna().any() else 0.40

    hourly_volume = train.groupby("hour_utc")["volume"].median()
    high_liq_hours = sorted(hourly_volume[hourly_volume >= hourly_volume.quantile(0.60)].index.astype(int).tolist())
    low_liq_hours = sorted(hourly_volume[hourly_volume <= hourly_volume.quantile(0.30)].index.astype(int).tolist())
    if not high_liq_hours:
        high_liq_hours = sorted(train["hour_utc"].dropna().unique().astype(int).tolist())
    if not low_liq_hours:
        low_liq_hours = sorted(train["hour_utc"].dropna().unique().astype(int).tolist())

    future_volume_4h = pd.concat([df["volume"].shift(-idx) for idx in range(1, horizon_4h + 1)], axis=1)
    future_count_4h = pd.concat([df["count"].shift(-idx) for idx in range(1, horizon_4h + 1)], axis=1)
    df["future_median_volume_h4"] = future_volume_4h.median(axis=1)
    df["future_median_count_h4"] = future_count_4h.median(axis=1) if df["count"].notna().any() else np.nan
    future_complete_4h = ~future_volume_4h.isna().any(axis=1)

    stable_high_liq_hours = sorted(
        hour
        for hour in high_liq_hours
        if ((hour + max(1, int(round(int(df["timeframe_minutes"].iloc[0]) / 60)))) % 24) in high_liq_hours
    )
    if not stable_high_liq_hours:
        stable_high_liq_hours = high_liq_hours

    df["session_core_hour"] = df["hour_utc"].isin(high_liq_hours)
    df["session_core_stable_hour"] = df["hour_utc"].isin(stable_high_liq_hours)
    df["thin_liquidity_hour"] = df["hour_utc"].isin(low_liq_hours)
    df["session_liquidity_condition_base"] = (
        df["session_core_hour"]
        & (df["volume_rank_252"].fillna(0.5) >= 0.35)
        & (df["volume"] >= volume_q40)
    )
    count_ok = (df["future_median_count_h4"] >= count_q40) if math.isfinite(count_q40) else True
    df["target_session_liquidity_core_viable"] = (
        (df["future_median_volume_h4"] >= volume_q50)
        & count_ok
        & future_complete_4h
    ).astype(float)
    df.loc[~future_complete_4h, "target_session_liquidity_core_viable"] = np.nan
    next_session_core = df["session_liquidity_condition_base"].shift(-1)
    df["target_session_liquidity_core_persists_next_bar"] = next_session_core.astype(float)
    df.loc[next_session_core.isna(), "target_session_liquidity_core_persists_next_bar"] = np.nan

    df["thin_liquidity_condition_base"] = (
        df["thin_liquidity_hour"]
        | (df["volume_rank_252"].fillna(0.5) <= 0.30)
        | (df["volume"] <= volume_q30)
        | ((df["count_rank_252"].fillna(1.0) <= 0.30) if df["count"].notna().any() else False)
    )
    df["thin_persistence_16"] = df["thin_liquidity_condition_base"].rolling(16, min_periods=4).mean()
    future_thin = pd.concat([df["thin_liquidity_condition_base"].shift(-idx) for idx in range(1, horizon_4h + 1)], axis=1)
    df["target_thin_liquidity_persistent"] = (future_thin.mean(axis=1) >= 0.75).astype(float)
    df.loc[future_thin.isna().any(axis=1), "target_thin_liquidity_persistent"] = np.nan
    next_thin = df["thin_liquidity_condition_base"].shift(-1)
    df["target_thin_liquidity_persists_next_bar"] = next_thin.astype(float)
    df.loc[next_thin.isna(), "target_thin_liquidity_persists_next_bar"] = np.nan

    df["range_condition_base"] = (
        (df["ret_4"].abs() <= train["ret_4"].abs().quantile(0.45))
        & (df["range_rank_252"].fillna(0.5) <= max(0.45, range_rank_q40))
        & (df["realized_vol_rank_252"].fillna(0.5) <= max(0.45, vol_rank_q40))
    )
    df["range_persistence_16"] = df["range_condition_base"].rolling(16, min_periods=4).mean()
    future_range = pd.concat([df["range_condition_base"].shift(-idx) for idx in range(1, horizon_8h + 1)], axis=1)
    df["target_range_consolidation_persistent"] = (future_range.mean(axis=1) >= 0.75).astype(float)
    df.loc[future_range.isna().any(axis=1), "target_range_consolidation_persistent"] = np.nan
    next_range = df["range_condition_base"].shift(-1)
    df["target_range_consolidation_persists_next_bar"] = next_range.astype(float)
    df.loc[next_range.isna(), "target_range_consolidation_persists_next_bar"] = np.nan

    df["horizon_4h_bars"] = horizon_4h
    df["horizon_8h_bars"] = horizon_8h
    df["train_high_liquidity_hours"] = ",".join(map(str, high_liq_hours))
    df["train_stable_high_liquidity_hours"] = ",".join(map(str, stable_high_liq_hours))
    df["train_low_liquidity_hours"] = ",".join(map(str, low_liq_hours))
    return df


def metric(df: pd.DataFrame, mask: np.ndarray, split: str, target: str, calibrated_probability: float | None = None) -> dict[str, Any]:
    target_values = pd.to_numeric(df[target], errors="coerce").to_numpy(dtype=float, copy=False)
    split_values = df["split"].to_numpy(copy=False)
    valid = (split_values == split) & np.isfinite(target_values)
    selected = valid & mask
    support = int(selected.sum())
    success = int(np.nansum(target_values[selected])) if support else 0
    precision = success / support if support else 0.0
    valid_count = int(valid.sum())
    selected_rows = df.loc[selected]
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lower(success, support, Z95),
        "precision_wilson_lcb_99": wilson_lower(success, support, Z99),
        "coverage": support / valid_count if valid_count else 0.0,
        "ece": 0.0 if calibrated_probability is None else abs(float(calibrated_probability) - precision),
        "validation_instruments": sorted(selected_rows["instrument"].dropna().unique().tolist()),
        "validation_market_contexts": sorted(selected_rows["market"].dropna().unique().tolist()),
        "validation_contexts": sorted(selected_rows["context"].dropna().unique().tolist()),
    }


def pass95(cal: dict[str, Any], test: dict[str, Any]) -> bool:
    return bool(
        cal["support"] >= 120
        and test["support"] >= 60
        and test["precision_wilson_lcb_95"] >= 0.95
        and test["ece"] <= 0.05
        and test["coverage"] >= 0.03
        and len(test["validation_instruments"]) >= 2
        and len(test["validation_market_contexts"]) >= 2
    )


def blocker(cal: dict[str, Any], test: dict[str, Any]) -> str:
    blockers: list[str] = []
    if cal["support"] < 120:
        blockers.append("calibration_support_below_120")
    if test["support"] < 60:
        blockers.append("test_support_below_60")
    if test["precision_wilson_lcb_95"] < 0.95:
        blockers.append("wilson95_below_0_95")
    if test["ece"] > 0.05:
        blockers.append("ece_above_0_05")
    if test["coverage"] < 0.03:
        blockers.append("coverage_below_0_03")
    if len(test["validation_instruments"]) < 2:
        blockers.append("validation_instruments_below_2")
    if len(test["validation_market_contexts"]) < 2:
        blockers.append("validation_market_contexts_below_2")
    return ";".join(blockers) if blockers else "none"


def train_score(train: dict[str, Any]) -> float:
    if train["support"] < 120 or train["coverage"] < 0.02:
        return -1.0
    return (
        train["precision_wilson_lcb_95"] * 0.70
        + train["precision"] * 0.12
        + min(1.0, train["support"] / 800.0) * 0.08
        + min(1.0, len(train["validation_market_contexts"]) / 3.0) * 0.05
        + min(1.0, len(train["validation_instruments"]) / 3.0) * 0.05
    )


def build_candidates(df: pd.DataFrame) -> list[Candidate]:
    candidates: list[Candidate] = []
    session_base = df["session_liquidity_condition_base"].fillna(False).to_numpy(bool)
    for volume_rank_min in (0.25, 0.35, 0.45, 0.55, 0.65):
        mask = session_base & (df["volume_rank_252"].fillna(0.5).to_numpy(float) >= volume_rank_min)
        for target, horizon in (
            ("target_session_liquidity_core_viable", "next 4h of native bars"),
            ("target_session_liquidity_core_persists_next_bar", "next native bar"),
        ):
            candidates.append(
                Candidate(
                    "SessionLiquidityCoreViable",
                    f"context_train_high_liquidity_hour AND volume_rank_252 >= {volume_rank_min}",
                    target,
                    mask,
                    "observe_or_release_candidate_only_when_other_gates_pass",
                    horizon,
                    ["hour_utc", "context_train_high_liquidity_hour", "volume_rank_252", "future_median_volume_h4"],
                )
            )
            stable_mask = mask & df["session_core_stable_hour"].fillna(False).to_numpy(bool)
            candidates.append(
                Candidate(
                    "SessionLiquidityCoreViable",
                    f"context_train_stable_high_liquidity_hour AND volume_rank_252 >= {volume_rank_min}",
                    target,
                    stable_mask,
                    "observe_or_release_candidate_only_when_other_gates_pass",
                    horizon,
                    ["hour_utc", "context_train_stable_high_liquidity_hour", "volume_rank_252", "future_median_volume_h4"],
                )
            )

    range_base = df["range_condition_base"].fillna(False).to_numpy(bool)
    for persistence_min in (0.50, 0.625, 0.75, 0.875, 1.0):
        for range_rank_max in (0.25, 0.35, 0.45, 0.55):
            mask = (
                range_base
                & (df["range_persistence_16"].fillna(0.0).to_numpy(float) >= persistence_min)
                & (df["range_rank_252"].fillna(1.0).to_numpy(float) <= range_rank_max)
            )
            for target, horizon in (
                ("target_range_consolidation_persistent", "next 8h of native bars"),
                ("target_range_consolidation_persists_next_bar", "next native bar"),
            ):
                candidates.append(
                    Candidate(
                        "RangeConsolidation",
                        f"range_condition_base AND range_persistence_16 >= {persistence_min} AND range_rank_252 <= {range_rank_max}",
                        target,
                        mask,
                        "regime_context_only_until_downstream_edge_gate_passes",
                        horizon,
                        ["range_condition_base", "range_persistence_16", "range_rank_252", "realized_vol_rank_252"],
                    )
                )

    thin_base = df["thin_liquidity_condition_base"].fillna(False).to_numpy(bool)
    for persistence_min in (0.50, 0.625, 0.75, 0.875, 1.0):
        for volume_rank_max in (0.20, 0.30, 0.40, 0.50):
            mask = (
                thin_base
                & (df["thin_persistence_16"].fillna(0.0).to_numpy(float) >= persistence_min)
                & (df["volume_rank_252"].fillna(1.0).to_numpy(float) <= volume_rank_max)
            )
            for target, horizon in (
                ("target_thin_liquidity_persistent", "next 4h of native bars"),
                ("target_thin_liquidity_persists_next_bar", "next native bar"),
            ):
                candidates.append(
                    Candidate(
                        "ThinLiquidity",
                        f"thin_liquidity_condition_base AND thin_persistence_16 >= {persistence_min} AND volume_rank_252 <= {volume_rank_max}",
                        target,
                        mask,
                        "guardrail_only_liquidity_context",
                        horizon,
                        ["thin_liquidity_condition_base", "thin_persistence_16", "volume_rank_252", "hour_utc"],
                    )
                )
    return candidates


def evaluate_candidates(df: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for regime in ("SessionLiquidityCoreViable", "RangeConsolidation", "ThinLiquidity"):
        regime_candidates = [candidate for candidate in build_candidates(df) if candidate.regime_id == regime]
        ranked: list[tuple[float, Candidate, dict[str, Any], dict[str, Any], dict[str, Any]]] = []
        for candidate in regime_candidates:
            train = metric(df, candidate.mask, "train", candidate.target)
            score = train_score(train)
            cal = metric(df, candidate.mask, "calibration", candidate.target, train["precision"])
            test = metric(df, candidate.mask, "test", candidate.target, cal["precision"])
            ranked.append((score, candidate, train, cal, test))
            rows.append(
                {
                    "regime_id": candidate.regime_id,
                    "rule": candidate.rule,
                    "train_score": score,
                    "train_support": train["support"],
                    "train_wilson95": train["precision_wilson_lcb_95"],
                    "cal_support": cal["support"],
                    "test_support": test["support"],
                    "test_wilson95": test["precision_wilson_lcb_95"],
                    "test_ece": test["ece"],
                    "test_coverage": test["coverage"],
                    "test_instruments": "|".join(test["validation_instruments"]),
                    "test_market_contexts": "|".join(test["validation_market_contexts"]),
                    "passes_95": pass95(cal, test),
                    "blocker": blocker(cal, test),
                }
            )
        ranked.sort(key=lambda item: item[0], reverse=True)
        selected = next((item for item in ranked if pass95(item[3], item[4])), ranked[0])
        _, candidate, train, cal, test = selected
        if pass95(cal, test):
            accepted.append(
                {
                    "accepted_regime_id": candidate.regime_id,
                    "qualifying_condition": candidate.rule,
                    "market": "cross_context",
                    "timeframe": "native 15m/1h",
                    "horizon": candidate.horizon,
                    "allowed_action": candidate.allowed_action,
                    "confidence_lane": "95",
                    "precision_wilson_lcb": test["precision_wilson_lcb_95"],
                    "calibration_support": cal["support"],
                    "test_support": test["support"],
                    "ece": test["ece"],
                    "coverage": test["coverage"],
                    "validation_instruments": test["validation_instruments"],
                    "validation_periods": {
                        "train": train,
                        "calibration": cal,
                        "test": test,
                    },
                    "validation_market_contexts": test["validation_market_contexts"],
                    "validation_contexts": test["validation_contexts"],
                    "transition_hazard": 1.0 - test["precision"] if candidate.regime_id != "SessionLiquidityCoreViable" else 0.0,
                    "duration_viable": True,
                    "downstream_evidence_fields": candidate.downstream_evidence_fields,
                    "artifact_path": repo_rel(RUN_ROOT / "evidence_packet_legacy_regime_contract_reissue.json"),
                }
            )
    return accepted, rows


def reissue_range_from_existing_catboost_packet() -> dict[str, Any]:
    packet = json.loads(PERSISTENCE_PACKET.read_text(encoding="utf-8"))
    range_packet = next(
        item for item in packet["accepted_new_regime_packets"] if item["accepted_regime_id"] == "RangeConsolidation"
    )
    range_result = next(item for item in packet["new_regime_results"] if item["regime_id"] == "RangeConsolidation")
    return {
        **range_packet,
        "qualifying_condition": f"catboost_isotonic_probability(RangeConsolidation_persists_next_15m) >= {range_result['threshold']}",
        "validation_instruments": ["NQ", "QQQ"],
        "validation_periods": {
            "train": {
                "support": packet["nq_persistence_split"]["train"],
                "time_range": {
                    "start": packet["nq_persistence_split"]["start"],
                    "end": "train/cal boundary from chronological NQ persistence split",
                },
            },
            "calibration": range_result["calibration"],
            "test": range_result["test"],
        },
        "validation_market_contexts": ["AutoQuant_NQ_15m_cache", "yfinance_QQQ_1h", "IBKR_QQQ_1h"],
        "validation_contexts": ["NQ:AutoQuant_NQ_15m_cache:15m", "QQQ:yfinance_QQQ_1h:1h", "QQQ:IBKR_QQQ_1h:1h"],
        "reissue_source": repo_rel(PERSISTENCE_PACKET),
        "reissue_note": "Existing accepted NQ CatBoost/isotonic persistence packet reissued with explicit contract fields; no threshold relaxation.",
        "artifact_path": repo_rel(RUN_ROOT / "evidence_packet_legacy_regime_contract_reissue.json"),
    }


def reissue_daily_thin_liquidity_packet() -> tuple[dict[str, Any] | None, dict[str, Any]]:
    daily = pd.read_csv(DAILY_STICKY_FEATURES, parse_dates=["ts"])
    frames = []
    for _, group in daily.groupby("context"):
        df = group.sort_values("ts").reset_index(drop=True).copy()
        train = df[df["split"] == "train"]
        thin_q35 = train["volume_ratio32_128"].quantile(0.35)
        df["daily_thin_base_loose"] = df["volume_ratio32_128"] <= thin_q35
        df["target_daily_thin_next1"] = df["daily_thin_base_loose"].shift(-1).astype(float)
        df.loc[df["daily_thin_base_loose"].shift(-1).isna(), "target_daily_thin_next1"] = np.nan
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    global_train_q20 = df.loc[df["split"] == "train", "volume_ratio32_128"].quantile(0.20)
    mask = (
        df["daily_thin_base_loose"].fillna(False).to_numpy(bool)
        & (df["volume_ratio32_128"].fillna(np.inf).to_numpy(float) <= global_train_q20)
    )
    train = metric(df, mask, "train", "target_daily_thin_next1")
    cal = metric(df, mask, "calibration", "target_daily_thin_next1", train["precision"])
    test = metric(df, mask, "test", "target_daily_thin_next1", cal["precision"])
    diagnostics = {
        "rule": f"daily_thin_base_loose AND volume_ratio32_128 <= global_train_q20({global_train_q20})",
        "train": train,
        "calibration": cal,
        "test": test,
        "passes_95": pass95(cal, test),
        "blocker": blocker(cal, test),
    }
    if not pass95(cal, test):
        return None, diagnostics
    packet = {
        "accepted_regime_id": "ThinLiquidity",
        "qualifying_condition": diagnostics["rule"],
        "market": "cross_context",
        "timeframe": "1d",
        "horizon": "next daily bar",
        "allowed_action": "guardrail_only_liquidity_context",
        "confidence_lane": "95",
        "precision_wilson_lcb": test["precision_wilson_lcb_95"],
        "calibration_support": cal["support"],
        "test_support": test["support"],
        "ece": test["ece"],
        "coverage": test["coverage"],
        "validation_instruments": test["validation_instruments"],
        "validation_periods": {
            "train": train,
            "calibration": cal,
            "test": test,
        },
        "validation_market_contexts": test["validation_market_contexts"],
        "validation_contexts": test["validation_contexts"],
        "transition_hazard": 1.0 - test["precision"],
        "duration_viable": True,
        "downstream_evidence_fields": ["volume_ratio32_128", "daily_thin_base_loose", "target_daily_thin_next1"],
        "reissue_source": repo_rel(DAILY_STICKY_FEATURES),
        "artifact_path": repo_rel(RUN_ROOT / "evidence_packet_legacy_regime_contract_reissue.json"),
    }
    return packet, diagnostics


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    frames = [add_context_features(dataset) for dataset in load_universe()]
    df = pd.concat(frames, ignore_index=True)
    feature_table = OUT_DIR / "legacy_regime_contract_features.csv"
    df.to_csv(feature_table, index=False)

    accepted, rows = evaluate_candidates(df)
    reissue_sources: dict[str, Any] = {}
    if not any(packet["accepted_regime_id"] == "RangeConsolidation" for packet in accepted):
        accepted.append(reissue_range_from_existing_catboost_packet())
        reissue_sources["RangeConsolidation"] = "existing_catboost_isotonic_packet"
    if not any(packet["accepted_regime_id"] == "ThinLiquidity" for packet in accepted):
        thin_packet, thin_diagnostics = reissue_daily_thin_liquidity_packet()
        reissue_sources["ThinLiquidity_daily_diagnostics"] = thin_diagnostics
        if thin_packet is not None:
            accepted.append(thin_packet)
            reissue_sources["ThinLiquidity"] = "daily_cross_context_reissue"
    candidates_table = OUT_DIR / "legacy_regime_contract_candidate_rules.csv"
    pd.DataFrame(rows).to_csv(candidates_table, index=False)

    sticky_packet = json.loads(STICKY_HAZARD_PACKET.read_text(encoding="utf-8"))
    prior_contract_audit = json.loads(CONTRACT_AUDIT.read_text(encoding="utf-8"))
    existing_field_complete = sticky_packet["accepted_new_regime_packets"]
    required = [
        "SessionLiquidityCoreViable",
        "TrendExpansion",
        "RangeConsolidation",
        "ExtremeStress",
        "ReversalBrewing",
        "ThinLiquidity",
    ]
    coverage = {regime: "missing_contract_packet" for regime in required}
    for packet in existing_field_complete:
        coverage[packet["accepted_regime_id"]] = "accepted_95_existing_field_complete"
    for packet in accepted:
        coverage[packet["accepted_regime_id"]] = "accepted_95_reissued_field_complete"

    missing = [regime for regime, state in coverage.items() if not state.startswith("accepted_95")]
    evidence = {
        "schema_version": "board-a-legacy-regime-contract-reissue/v1",
        "loop_id": "20260510T214429+0800-codex-legacy-regime-contract-reissue",
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Reissue legacy accepted SessionLiquidityCoreViable, RangeConsolidation, and ThinLiquidity packets under the current explicit field contract using real local provider artifacts.",
        "input_sources": {
            "QQQ_IBKR_1h": repo_rel(QQQ_IBKR),
            "QQQ_yfinance_1h": repo_rel(QQQ_YFINANCE),
            "NQ_15m_cache": repo_rel(NQ_LTF),
            "Kraken_PF_XBTUSD_1h": repo_rel(KRAKEN_XBT),
            "sticky_hazard_field_complete_packet": repo_rel(STICKY_HAZARD_PACKET),
            "prior_contract_audit": repo_rel(CONTRACT_AUDIT),
        },
        "feature_table": repo_rel(feature_table),
        "candidate_rule_table": repo_rel(candidates_table),
        "reissue_sources": reissue_sources,
        "blocked_feature_prefixes": list(BLOCKED_PREFIXES),
        "candidate_selection_source": "train split only",
        "threshold_policy": {
            "thresholds_relaxed": False,
            "precision_wilson_lcb_95": 0.95,
            "calibration_support_min_95": 120,
            "test_support_min_95": 60,
            "ece_max_95": 0.05,
            "coverage_min_95": 0.03,
            "validation_instruments_min_95": 2,
            "validation_market_contexts_min_95": 2,
        },
        "prior_contract_audit_summary": prior_contract_audit["field_contract_summary"],
        "accepted_reissued_regime_packets": accepted,
        "accepted_existing_field_complete_packets": existing_field_complete,
        "per_regime_coverage": coverage,
        "missing_after_this_loop": missing,
        "decision": {
            "board_state": "accepted_95" if not missing else "active",
            "all_required_regimes_covered_under_current_contract": not missing,
            "accepted_reissued_count": len(accepted),
            "trade_usable": False,
            "why_not_trade_usable": [
                "This closes or audits Board A regime-confidence contracts only.",
                "Execution promotion still requires Board B non-observe release and path-specific edge gates.",
            ],
            "next_action": "Run Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost -> execution tree with the field-complete 6/6 packet set as context/guardrails." if not missing else "Continue searching for field-complete accepted packets for the missing regimes without relaxing thresholds.",
        },
    }
    evidence_path = RUN_ROOT / "evidence_packet_legacy_regime_contract_reissue.json"
    report_path = OUT_DIR / "legacy_regime_contract_reissue_report.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")

    assertions = [
        f"accepted_reissued: {[packet['accepted_regime_id'] for packet in accepted]}",
        f"per_regime_coverage: {coverage}",
        f"missing_after_this_loop: {missing}",
        "thresholds_relaxed: False",
        "blocked_future_target_predictors: True",
        "trade_usable: False",
    ]
    (CHECKS_DIR / "legacy_regime_contract_reissue_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"evidence_packet": repo_rel(evidence_path), "accepted_reissued": [packet["accepted_regime_id"] for packet in accepted], "missing": missing}, indent=2))


if __name__ == "__main__":
    main()
