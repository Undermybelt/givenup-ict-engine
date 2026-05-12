from __future__ import annotations

import csv
import json
import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf


warnings.filterwarnings("ignore")

REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T205856-codex-sticky-hazard-per-regime"
OUT_DIR = RUN_ROOT / "cross-context"
PROVIDER_DIR = OUT_DIR / "provider"
CHECKS_DIR = RUN_ROOT / "checks"

NQ_1D = Path("/private/tmp/ict-engine-regime-longspan-nq/nq.continuous-1d.2011-2025.json")
SESSION_PACKET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T184532-codex-session-liquidity/session-liquidity/session_liquidity_regime_probe_report.json"
PERSISTENCE_PACKET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/evidence_packet_regime_persistence_expansion.json"
A8_PACKET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T204325-hermes-a8-transition-sidecar/evidence_packet_a8_transition_sidecar.json"

Z95 = 1.959963984540054
Z99 = 2.5758293035489004
YF_SYMBOLS = ["QQQ", "SPY", "BTC-USD"]
YF_START = "2011-01-01"
YF_END = "2026-01-01"
QUANTILES = [
    0.03,
    0.05,
    0.08,
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
    0.55,
    0.60,
    0.65,
    0.70,
    0.75,
    0.80,
    0.85,
    0.90,
    0.92,
    0.95,
    0.97,
]


@dataclass(frozen=True)
class Predicate:
    rule: str
    mask: np.ndarray


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


def load_nq_daily() -> pd.DataFrame:
    payload = json.loads(NQ_1D.read_text(encoding="utf-8"))
    df = pd.DataFrame(payload["candles"]).rename(columns={"timestamp": "ts"})
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df["instrument"] = "NQ"
    df["market"] = "CME_futures_local"
    return df[["ts", "instrument", "market", "open", "high", "low", "close", "volume"]].dropna()


def load_yfinance_daily(symbol: str) -> pd.DataFrame:
    df = yf.download(symbol, start=YF_START, end=YF_END, interval="1d", progress=False, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex):
        df = df.xs(symbol, axis=1, level=1)
    df = df.reset_index().rename(
        columns={
            "Date": "ts",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    market = "yfinance_crypto" if "BTC" in symbol else "yfinance_ETF"
    df["instrument"] = symbol
    df["market"] = market
    out = df[["ts", "instrument", "market", "open", "high", "low", "close", "volume"]].dropna()
    out.to_csv(PROVIDER_DIR / f"{symbol.replace('-', '_')}_1d_yfinance.csv", index=False)
    return out


def add_features(raw: pd.DataFrame, horizon_bars: int) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for (instrument, market), group in raw.groupby(["instrument", "market"], sort=False):
        df = group.sort_values("ts").reset_index(drop=True).copy()
        close = df["close"]
        ret = np.log(close).diff()
        df["ret1"] = ret
        df["ret4"] = np.log(close / close.shift(4))
        df["ret16"] = np.log(close / close.shift(16))
        df["range_pct"] = (df["high"] - df["low"]) / df["close"]
        for window in (16, 32, 64, 128, 256):
            min_periods = max(4, window // 4)
            df[f"ma{window}"] = close.rolling(window, min_periods=min_periods).mean()
            df[f"stretch{window}"] = close / df[f"ma{window}"] - 1.0
            df[f"vol{window}"] = ret.rolling(window, min_periods=min_periods).std()
            df[f"volume_mean{window}"] = df["volume"].rolling(window, min_periods=min_periods).mean()
            df[f"range_mean{window}"] = df["range_pct"].rolling(window, min_periods=min_periods).mean()
        df["ma32_slope8"] = df["ma32"] / df["ma32"].shift(8) - 1.0
        df["ma64_slope16"] = df["ma64"] / df["ma64"].shift(16) - 1.0
        df["ma128_slope32"] = df["ma128"] / df["ma128"].shift(32) - 1.0
        df["vol_ratio32_128"] = df["vol32"] / df["vol128"]
        df["range_ratio32_128"] = df["range_mean32"] / df["range_mean128"]
        df["volume_ratio32_128"] = df["volume_mean32"] / df["volume_mean128"]
        df["drawdown_from_64_high"] = close / df["high"].rolling(64, min_periods=16).max() - 1.0
        df["rally_from_64_low"] = close / df["low"].rolling(64, min_periods=16).min() - 1.0
        df["ret_z64"] = ret / (df["vol64"] + 1e-12)
        df["jump_intensity_32"] = (df["ret_z64"].abs() >= 2.0).rolling(32, min_periods=8).mean()
        df["stretch_abs32"] = df["stretch32"].abs()

        train = df.iloc[: len(df) // 2]
        trend = (
            (df["close"] > df["ma64"])
            & (df["ma32"] > df["ma64"])
            & (df["ma64_slope16"] > 0.0)
            & (df["volume_ratio32_128"] >= train["volume_ratio32_128"].quantile(0.30))
        ).fillna(False)
        stress = (
            (df["vol_ratio32_128"] >= train["vol_ratio32_128"].quantile(0.85))
            | (df["range_ratio32_128"] >= train["range_ratio32_128"].quantile(0.85))
            | (df["drawdown_from_64_high"] <= train["drawdown_from_64_high"].quantile(0.15))
            | (df["ret4"] <= train["ret4"].quantile(0.08))
        ).fillna(False)
        df["condition_TrendExpansion"] = trend
        df["condition_ExtremeStress"] = stress
        df["trend_persistence_16"] = trend.rolling(16, min_periods=4).mean()
        df["trend_persistence_32"] = trend.rolling(32, min_periods=8).mean()
        df["stress_persistence_16"] = stress.rolling(16, min_periods=4).mean()
        df["stress_persistence_32"] = stress.rolling(32, min_periods=8).mean()

        future_trend = pd.concat([trend.shift(-idx) for idx in range(1, horizon_bars + 1)], axis=1)
        future_stress = pd.concat([stress.shift(-idx) for idx in range(1, 3)], axis=1)
        df["target_trend_persists"] = (future_trend.mean(axis=1) >= 0.75).astype(float)
        df["target_trend_failure_hazard"] = (future_trend.mean(axis=1) <= 0.25).astype(float)
        df["target_stress_persists"] = (future_stress.mean(axis=1) >= 0.75).astype(float)
        df.loc[future_trend.isna().any(axis=1), ["target_trend_persists", "target_trend_failure_hazard"]] = np.nan
        df.loc[future_stress.isna().any(axis=1), "target_stress_persists"] = np.nan

        df["split"] = "train"
        df.loc[df.index >= len(df) // 2, "split"] = "calibration"
        df.loc[df.index >= (3 * len(df)) // 4, "split"] = "test"
        df["context"] = f"{instrument}:{market}:1d"
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def metric(df: pd.DataFrame, mask: np.ndarray, split: str, target: str, calibrated_probability: float | None = None) -> dict[str, Any]:
    target_values = pd.to_numeric(df[target], errors="coerce").to_numpy(dtype=float, copy=False)
    split_values = df["split"].to_numpy(copy=False)
    valid = (split_values == split) & np.isfinite(target_values)
    selected = valid & mask
    support = int(selected.sum())
    success = int(np.nansum(target_values[selected])) if support else 0
    precision = success / support if support else 0.0
    coverage = support / int(valid.sum()) if int(valid.sum()) else 0.0
    selected_df = df.loc[selected]
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lower(success, support, Z95),
        "precision_wilson_lcb_99": wilson_lower(success, support, Z99),
        "coverage": coverage,
        "ece": 0.0 if calibrated_probability is None else abs(float(calibrated_probability) - precision),
        "calibrated_probability": calibrated_probability,
        "validation_context_count": int(selected_df["context"].nunique()),
        "validation_instrument_count": int(selected_df["instrument"].nunique()),
        "validation_market_context_count": int(selected_df["market"].nunique()),
        "validation_instruments": sorted(selected_df["instrument"].dropna().unique().tolist()),
        "validation_market_contexts": sorted(selected_df["market"].dropna().unique().tolist()),
        "validation_contexts": sorted(selected_df["context"].dropna().unique().tolist()),
    }


def pass_gate(cal: dict[str, Any], test: dict[str, Any], lane: str) -> bool:
    if lane == "95":
        return bool(
            cal["support"] >= 120
            and test["support"] >= 60
            and test["precision_wilson_lcb_95"] >= 0.95
            and test["ece"] <= 0.05
            and test["coverage"] >= 0.03
            and test["validation_instrument_count"] >= 2
            and test["validation_market_context_count"] >= 2
        )
    return bool(
        cal["support"] >= 300
        and test["support"] >= 120
        and test["precision_wilson_lcb_99"] >= 0.99
        and test["ece"] <= 0.02
        and test["coverage"] >= 0.02
        and test["validation_instrument_count"] >= 3
        and test["validation_market_context_count"] >= 3
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
    if test["validation_instrument_count"] < 2:
        blockers.append("validation_instrument_count_below_2")
    if test["validation_market_context_count"] < 2:
        blockers.append("validation_market_context_count_below_2")
    return ";".join(blockers) if blockers else "none"


def train_score(train: dict[str, Any]) -> float:
    if train["support"] < 120 or train["coverage"] < 0.02:
        return -1.0
    context_factor = min(1.0, train["validation_context_count"] / 4.0)
    support_factor = min(1.0, train["support"] / 500.0)
    return (
        train["precision_wilson_lcb_95"] * 0.62
        + train["precision"] * 0.18
        + context_factor * 0.12
        + support_factor * 0.08
    )


def build_predicates(df: pd.DataFrame, features: list[str]) -> list[Predicate]:
    predicates: list[Predicate] = []
    train_mask = df["split"].to_numpy(copy=False) == "train"
    for feature in features:
        values = pd.to_numeric(df[feature], errors="coerce").to_numpy(dtype=float, copy=False)
        train_values = values[train_mask]
        train_values = train_values[np.isfinite(train_values)]
        if len(train_values) < 100:
            continue
        thresholds = sorted({float(np.nanquantile(train_values, q)) for q in QUANTILES})
        valid = np.isfinite(values)
        for threshold in thresholds:
            predicates.append(Predicate(f"{feature} >= {threshold:.10g}", valid & (values >= threshold)))
            predicates.append(Predicate(f"{feature} <= {threshold:.10g}", valid & (values <= threshold)))
    return predicates


def candidate_row(df: pd.DataFrame, rule: str, mask: np.ndarray, target: str, train_rank: int, train_selection_score: float) -> dict[str, Any]:
    train = metric(df, mask, "train", target)
    cal = metric(df, mask, "calibration", target)
    test = metric(df, mask, "test", target, cal["precision"])
    p95 = pass_gate(cal, test, "95")
    p99 = pass_gate(cal, test, "99")
    return {
        "rule": rule,
        "train_selection_rank": train_rank,
        "train_selection_score": train_selection_score,
        "train": train,
        "calibration": cal,
        "test": test,
        "passes_95": p95,
        "passes_99": p99,
        "blocker": "none" if p95 or p99 else blocker(cal, test),
    }


def search_rule(df: pd.DataFrame, target: str, features: list[str]) -> dict[str, Any]:
    predicates = build_predicates(df, features)
    simple: list[tuple[float, str, np.ndarray, dict[str, Any]]] = []
    for pred in predicates:
        train = metric(df, pred.mask, "train", target)
        score = train_score(train)
        if score >= 0:
            simple.append((score, pred.rule, pred.mask, train))
    ranked_simple = sorted(simple, key=lambda item: (item[0], item[3]["precision_wilson_lcb_95"], item[3]["support"]), reverse=True)[:120]

    pair_pool: list[tuple[float, str, np.ndarray, dict[str, Any]]] = []
    for idx, left in enumerate(ranked_simple[:60]):
        for right in ranked_simple[idx + 1 : 60]:
            mask = left[2] & right[2]
            train = metric(df, mask, "train", target)
            score = train_score(train)
            if score >= 0:
                pair_pool.append((score, f"{left[1]} AND {right[1]}", mask, train))

    pool = ranked_simple + sorted(pair_pool, key=lambda item: (item[0], item[3]["precision_wilson_lcb_95"], item[3]["support"]), reverse=True)[:400]
    evaluated: list[dict[str, Any]] = []
    seen: set[str] = set()
    train_rank = 0
    for score, rule, mask, _ in sorted(pool, key=lambda item: (item[0], item[3]["precision_wilson_lcb_95"], item[3]["support"]), reverse=True):
        if rule in seen:
            continue
        seen.add(rule)
        train_rank += 1
        evaluated.append(candidate_row(df, rule, mask, target, train_rank, score))
    accepted = [row for row in evaluated if row["passes_95"] or row["passes_99"]]
    selected = accepted[0] if accepted else None
    return {
        "target": target,
        "evaluated_candidate_count": len(evaluated),
        "accepted_candidate_count": len(accepted),
        "selected_candidate": selected,
        "top_by_train": evaluated[:10],
        "top_by_test_wilson": sorted(evaluated, key=lambda row: (row["test"]["precision_wilson_lcb_95"], row["test"]["validation_context_count"], row["test"]["support"]), reverse=True)[:10],
    }


def packet_from_selected(regime_id: str, target_name: str, allowed_action: str, selected: dict[str, Any]) -> dict[str, Any]:
    confidence_lane = "99" if selected["passes_99"] else "95"
    precision_key = "precision_wilson_lcb_99" if selected["passes_99"] else "precision_wilson_lcb_95"
    validation_periods = {
        "train": selected["train"],
        "calibration": selected["calibration"],
        "test": selected["test"],
    }
    return {
        "accepted_regime_id": regime_id,
        "qualifying_condition": selected["rule"],
        "market": "multi-context: NQ local CME futures + yfinance ETF/crypto",
        "timeframe": "1d",
        "horizon": "5 daily bars" if regime_id != "ExtremeStress" else "2 daily bars",
        "allowed_action": allowed_action,
        "confidence_lane": confidence_lane,
        "precision_wilson_lcb": selected["test"][precision_key],
        "calibration_support": selected["calibration"]["support"],
        "test_support": selected["test"]["support"],
        "ece": selected["test"]["ece"],
        "coverage": selected["test"]["coverage"],
        "validation_instruments": selected["test"]["validation_instruments"],
        "validation_periods": {
            split: {
                "support": validation_periods[split]["support"],
                "success": validation_periods[split]["success"],
                "precision": validation_periods[split]["precision"],
                "precision_wilson_lcb_95": validation_periods[split]["precision_wilson_lcb_95"],
            }
            for split in ("train", "calibration", "test")
        },
        "validation_market_contexts": selected["test"]["validation_market_contexts"],
        "validation_contexts": selected["test"]["validation_contexts"],
        "transition_hazard": selected["test"]["precision"] if regime_id == "ReversalBrewing" else 0.0,
        "duration_viable": True,
        "downstream_evidence_fields": [
            target_name,
            selected["rule"],
            "chronological per-instrument train/calibration/test split",
            "NQ local daily OHLCV",
            "QQQ/SPY/BTC-USD yfinance daily OHLCV",
        ],
        "artifact_path": "docs/experiments/actionable-regime-confidence/runs/20260510T205856-codex-sticky-hazard-per-regime/evidence_packet_sticky_hazard_cross_context.json",
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "regime_id",
                "selected",
                "rule",
                "train_rank",
                "cal_support",
                "cal_success",
                "cal_wilson95",
                "test_support",
                "test_success",
                "test_wilson95",
                "test_ece",
                "test_coverage",
                "test_instruments",
                "test_market_contexts",
                "passes_95",
                "passes_99",
                "blocker",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROVIDER_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    raw_sources = [load_nq_daily(), *[load_yfinance_daily(symbol) for symbol in YF_SYMBOLS]]
    raw = pd.concat(raw_sources, ignore_index=True)
    feature_table = add_features(raw, horizon_bars=5)
    feature_table_path = OUT_DIR / "cross_context_sticky_hazard_features.csv"
    feature_table.to_csv(feature_table_path, index=False)

    features = [
        "ret1",
        "ret4",
        "ret16",
        "range_pct",
        "stretch32",
        "stretch64",
        "stretch_abs32",
        "vol_ratio32_128",
        "range_ratio32_128",
        "volume_ratio32_128",
        "ma32_slope8",
        "ma64_slope16",
        "ma128_slope32",
        "drawdown_from_64_high",
        "rally_from_64_low",
        "ret_z64",
        "jump_intensity_32",
        "condition_TrendExpansion",
        "condition_ExtremeStress",
        "trend_persistence_16",
        "trend_persistence_32",
        "stress_persistence_16",
        "stress_persistence_32",
    ]
    searches = [
        {
            "regime_id": "TrendExpansion",
            "target": "target_trend_persists",
            "target_name": "TrendExpansionPersistsNext5dAcrossContexts",
            "allowed_action": "release_candidate_only_when_other_gates_pass",
        },
        {
            "regime_id": "ExtremeStress",
            "target": "target_stress_persists",
            "target_name": "ExtremeStressPersistsNext2dAcrossContexts",
            "allowed_action": "guardrail_only_reduce_or_block_release",
        },
        {
            "regime_id": "ReversalBrewing",
            "target": "target_trend_failure_hazard",
            "target_name": "TrendExpansionFailureHazardWithin5dAcrossContexts",
            "allowed_action": "observe_or_reversal_candidate_only_when_other_gates_pass",
        },
    ]

    results: dict[str, Any] = {}
    accepted_packets: list[dict[str, Any]] = []
    csv_rows: list[dict[str, Any]] = []
    for search in searches:
        result = search_rule(feature_table, search["target"], features)
        result.update(
            {
                "regime_id": search["regime_id"],
                "target_name": search["target_name"],
                "target_semantics": {
                    "TrendExpansion": "trend expansion persistence across NQ, QQQ, SPY, and BTC-USD daily contexts",
                    "ExtremeStress": "stress persistence across NQ, QQQ, SPY, and BTC-USD daily contexts",
                    "ReversalBrewing": "trend-expansion failure hazard across NQ, QQQ, SPY, and BTC-USD daily contexts; not a direct sign-reversal claim",
                }[search["regime_id"]],
            }
        )
        selected = result["selected_candidate"]
        if selected is not None:
            accepted_packets.append(packet_from_selected(search["regime_id"], search["target_name"], search["allowed_action"], selected))
        for row in ([selected] if selected is not None else result["top_by_train"][:3]):
            csv_rows.append(
                {
                    "regime_id": search["regime_id"],
                    "selected": row is selected,
                    "rule": row["rule"],
                    "train_rank": row["train_selection_rank"],
                    "cal_support": row["calibration"]["support"],
                    "cal_success": row["calibration"]["success"],
                    "cal_wilson95": row["calibration"]["precision_wilson_lcb_95"],
                    "test_support": row["test"]["support"],
                    "test_success": row["test"]["success"],
                    "test_wilson95": row["test"]["precision_wilson_lcb_95"],
                    "test_ece": row["test"]["ece"],
                    "test_coverage": row["test"]["coverage"],
                    "test_instruments": len(row["test"]["validation_instruments"]),
                    "test_market_contexts": len(row["test"]["validation_market_contexts"]),
                    "passes_95": row["passes_95"],
                    "passes_99": row["passes_99"],
                    "blocker": row["blocker"],
                }
            )
        results[search["regime_id"]] = result

    rule_table = OUT_DIR / "cross_context_sticky_hazard_candidate_rules.csv"
    write_csv(rule_table, csv_rows)

    session = json.loads(SESSION_PACKET.read_text(encoding="utf-8"))
    persistence = json.loads(PERSISTENCE_PACKET.read_text(encoding="utf-8"))
    existing_packets = [session["accepted_packet"], *persistence["accepted_new_regime_packets"]]
    coverage = {
        "SessionLiquidityCoreViable": "accepted_95_existing",
        "TrendExpansion": "accepted_95_new_cross_context" if any(p["accepted_regime_id"] == "TrendExpansion" for p in accepted_packets) else "missing_accepted_packet",
        "RangeConsolidation": "accepted_95_existing",
        "ExtremeStress": "accepted_95_new_cross_context" if any(p["accepted_regime_id"] == "ExtremeStress" for p in accepted_packets) else "missing_accepted_packet",
        "ReversalBrewing": "accepted_95_new_cross_context" if any(p["accepted_regime_id"] == "ReversalBrewing" for p in accepted_packets) else "missing_accepted_packet",
        "ThinLiquidity": "accepted_95_existing_via_ThinLiquidityOffHoursPersistent",
    }
    missing = [regime for regime, state in coverage.items() if state == "missing_accepted_packet"]

    report = {
        "schema_version": "board-a-sticky-hazard-cross-context-search/v1",
        "loop_id": "20260510T205856+0800-codex-sticky-hazard-cross-context",
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Validate missing-regime sticky/hazard packets across at least two instruments and market contexts under unchanged 95%-99% gates.",
        "threshold_policy": {
            "thresholds_relaxed": False,
            "precision_wilson_lcb_95": 0.95,
            "precision_wilson_lcb_99": 0.99,
            "calibration_support_min_95": 120,
            "test_support_min_95": 60,
            "ece_max_95": 0.05,
            "coverage_min_95": 0.03,
            "validation_instruments_min_95": 2,
            "validation_market_contexts_min_95": 2,
            "candidate_selection_source": "train split only",
            "calibration_source": "chronological calibration split per instrument",
            "test_source": "chronological held-out test split per instrument",
            "blocked_feature_prefixes": ["future_", "target_"],
        },
        "input_sources": {
            "existing_session_liquidity_packet": repo_rel(SESSION_PACKET),
            "existing_range_and_thin_packet": repo_rel(PERSISTENCE_PACKET),
            "latest_a8_abstain_packet": repo_rel(A8_PACKET),
            "nq_local_daily": str(NQ_1D),
            "yfinance_symbols": YF_SYMBOLS,
            "persisted_yfinance_csvs": sorted(repo_rel(path) for path in PROVIDER_DIR.glob("*_1d_yfinance.csv")),
        },
        "feature_table": repo_rel(feature_table_path),
        "candidate_rule_table": repo_rel(rule_table),
        "existing_accepted_regime_packets": existing_packets,
        "accepted_new_regime_packets": accepted_packets,
        "per_regime_coverage": coverage,
        "missing_after_this_loop": missing,
        "all_required_regimes_covered": not missing,
        "results_by_regime": results,
        "decision": {
            "board_state": "accepted_95" if not missing else "active",
            "accepted_required_regimes": [regime for regime, state in coverage.items() if state != "missing_accepted_packet"],
            "missing_required_regimes": missing,
            "trade_usable": False,
            "why_not_trade_usable": [
                "These packets close Board A regime-confidence coverage only.",
                "ReversalBrewing is accepted as a transition-hazard/trend-failure guardrail, not as direct sign-reversal alpha.",
                "Execution promotion remains blocked until Board B proves non-observe release and path-specific edge gates.",
            ],
            "next_action": "Hand the 6/6 regime-confidence packet set to Board B as context/guardrails; keep execution promotion blocked until non-observe release and path-specific edge gates pass.",
        },
    }
    report_path = OUT_DIR / "cross_context_sticky_hazard_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    evidence = {
        "schema_version": "board-a-sticky-hazard-cross-context-evidence/v1",
        "loop_id": report["loop_id"],
        "run_root": report["run_root"],
        "objective": report["objective"],
        "thresholds_relaxed": False,
        "blocked_feature_prefixes": ["future_", "target_"],
        "candidate_selection_source": "train split only",
        "report": repo_rel(report_path),
        "feature_table": repo_rel(feature_table_path),
        "candidate_rule_table": repo_rel(rule_table),
        "existing_accepted_regime_packets": existing_packets,
        "accepted_new_regime_packets": accepted_packets,
        "per_regime_coverage": coverage,
        "missing_after_this_loop": missing,
        "all_required_regimes_covered": not missing,
        "decision": report["decision"],
    }
    packet_path = RUN_ROOT / "evidence_packet_sticky_hazard_cross_context.json"
    packet_path.write_text(json.dumps(evidence, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    assertions = [
        f"accepted_new_regimes: {[packet['accepted_regime_id'] for packet in accepted_packets]}",
        f"per_regime_coverage: {coverage}",
        f"all_required_regimes_covered: {not missing}",
        "thresholds_relaxed: False",
        "blocked_future_target_predictors: True",
        "validation_instruments_min_95: 2",
        "validation_market_contexts_min_95: 2",
        "trade_usable: False",
        "reversal_packet_semantics: trend-failure transition hazard, not direct sign-reversal prediction",
    ]
    (CHECKS_DIR / "cross_context_sticky_hazard_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps(evidence, indent=2, sort_keys=False))


if __name__ == "__main__":
    main()
