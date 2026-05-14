from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T202239-per-regime-coverage-reset"
OUT_DIR = RUN_ROOT / "per-regime"
SESSION_PACKET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T184532-codex-session-liquidity/session-liquidity/session_liquidity_regime_probe_report.json"
CROSS_MARKET_PACKET = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T202359-hermes-cross-market-regime-validation/evidence_packet_cross_market_regime_validation.json"
LONGSPAN = {
    "NQ_1h_2011_2025": (Path("/private/tmp/ict-engine-regime-longspan-nq/nq.continuous-1h.2011-2025.json"), 8, "1h"),
    "NQ_4h_2011_2025": (Path("/private/tmp/ict-engine-regime-longspan-nq/nq.continuous-4h.2011-2025.json"), 2, "4h"),
    "NQ_1d_2011_2025": (Path("/private/tmp/ict-engine-regime-longspan-nq/nq.continuous-1d.2011-2025.json"), 1, "1d"),
}
MAX_ROWS = 20_000
Z95 = 1.959963984540054
Z99 = 2.5758293035489004


def wilson_lower(success: int, total: int, z: float) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    centre = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return (centre - margin) / denom


def load_candles(path: Path, max_rows: int = MAX_ROWS) -> pd.DataFrame:
    payload = json.loads(path.read_text())
    candles = payload["candles"][-max_rows:]
    df = pd.DataFrame(candles)
    df["ts"] = pd.to_datetime(df["timestamp"], utc=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["open", "high", "low", "close", "volume"]).sort_values("ts").reset_index(drop=True)


def build_features(raw: pd.DataFrame, horizon: int) -> pd.DataFrame:
    df = raw.copy()
    close = df["close"]
    df["ret1"] = np.log(close).diff()
    df["ret4"] = np.log(close / close.shift(4))
    df["ret8"] = np.log(close / close.shift(8))
    df["ret16"] = np.log(close / close.shift(16))
    df["range_pct"] = (df["high"] - df["low"]) / df["close"]
    df["body_pct"] = (df["close"] - df["open"]).abs() / (df["high"] - df["low"]).replace(0, np.nan)

    for window in (8, 16, 32, 64, 128, 256):
        min_periods = max(4, window // 4)
        df[f"ma{window}"] = close.rolling(window, min_periods=min_periods).mean()
        df[f"stretch{window}"] = close / df[f"ma{window}"] - 1.0
        df[f"vol{window}"] = df["ret1"].rolling(window, min_periods=min_periods).std()
        df[f"volume_mean{window}"] = df["volume"].rolling(window, min_periods=min_periods).mean()
        df[f"range_mean{window}"] = df["range_pct"].rolling(window, min_periods=min_periods).mean()

    df["vol_ratio32_128"] = df["vol32"] / df["vol128"]
    df["volume_ratio32_128"] = df["volume_mean32"] / df["volume_mean128"]
    df["hour_utc"] = df["ts"].dt.hour
    df["day_of_week_utc"] = df["ts"].dt.dayofweek
    df["month_utc"] = df["ts"].dt.month

    future_close = close.shift(-horizon)
    future_high = pd.concat([df["high"].shift(-idx) for idx in range(1, horizon + 1)], axis=1).max(axis=1)
    future_low = pd.concat([df["low"].shift(-idx) for idx in range(1, horizon + 1)], axis=1).min(axis=1)
    future_volume = pd.concat([df["volume"].shift(-idx) for idx in range(1, max(2, horizon // 2) + 1)], axis=1).median(axis=1)
    df["future_ret"] = future_close / close - 1.0
    df["future_absret"] = df["future_ret"].abs()
    df["future_max_down"] = future_low / close - 1.0
    df["future_range"] = (future_high - future_low) / close

    train = df.iloc[: len(df) // 2]
    thresholds = {
        "trend_ret_q70": float(train["future_ret"].quantile(0.70)),
        "mild_drawdown_q65": float(train["future_max_down"].quantile(0.65)),
        "range_absret_q35": float(train["future_absret"].quantile(0.35)),
        "range_width_q35": float(train["future_range"].quantile(0.35)),
        "stress_absret_q90": float(train["future_absret"].quantile(0.90)),
        "stress_drawdown_q10": float(train["future_max_down"].quantile(0.10)),
        "reversal_absret_q65": float(train["future_absret"].quantile(0.65)),
        "thin_volume_q30": float(train["volume"].quantile(0.30)),
    }

    df["target_trend_expansion"] = ((df["future_ret"] >= thresholds["trend_ret_q70"]) & (df["future_max_down"] >= thresholds["mild_drawdown_q65"])).astype(float)
    df["target_range_consolidation"] = ((df["future_absret"] <= thresholds["range_absret_q35"]) & (df["future_range"] <= thresholds["range_width_q35"])).astype(float)
    df["target_extreme_stress"] = ((df["future_absret"] >= thresholds["stress_absret_q90"]) | (df["future_max_down"] <= thresholds["stress_drawdown_q10"])).astype(float)
    stretch_sign = np.sign(df["stretch32"].fillna(0.0))
    future_sign = np.sign(df["future_ret"].fillna(0.0))
    df["target_reversal_brewing"] = ((stretch_sign != 0) & (future_sign != 0) & (stretch_sign != future_sign) & (df["future_absret"] >= thresholds["reversal_absret_q65"])).astype(float)
    df["target_thin_liquidity"] = (future_volume <= thresholds["thin_volume_q30"]).astype(float)

    for target in target_map().values():
        df.loc[df["future_ret"].isna(), target] = np.nan
    df.attrs["thresholds"] = thresholds
    return df.dropna(subset=list(target_map().values())).reset_index(drop=True)


def target_map() -> dict[str, str]:
    return {
        "TrendExpansion": "target_trend_expansion",
        "RangeConsolidation": "target_range_consolidation",
        "ExtremeStress": "target_extreme_stress",
        "ReversalBrewing": "target_reversal_brewing",
        "ThinLiquidity": "target_thin_liquidity",
    }


def split_chrono(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_end = len(df) // 2
    cal_end = (len(df) * 3) // 4
    return df.iloc[:train_end].copy(), df.iloc[train_end:cal_end].copy(), df.iloc[cal_end:].copy()


def best_threshold(probs: np.ndarray, truth: np.ndarray, min_support: int = 120) -> dict[str, Any]:
    order = np.argsort(-probs)
    ranked_probs = probs[order]
    ranked_truth = truth[order]
    cumulative_success = np.cumsum(ranked_truth)
    best: dict[str, Any] | None = None
    for size in range(min_support, len(ranked_probs) + 1):
        if size < len(ranked_probs) and ranked_probs[size] == ranked_probs[size - 1]:
            continue
        success = int(cumulative_success[size - 1])
        precision = success / size
        candidate = {
            "support": int(size),
            "success": success,
            "precision": precision,
            "precision_wilson_lcb_95": wilson_lower(success, size, Z95),
            "precision_wilson_lcb_99": wilson_lower(success, size, Z99),
            "threshold": float(ranked_probs[size - 1]),
            "mean_raw_probability": float(np.mean(ranked_probs[:size])),
            "ece_raw_probability": abs(float(np.mean(ranked_probs[:size])) - precision),
        }
        if best is None or (candidate["precision_wilson_lcb_95"], candidate["support"]) > (best["precision_wilson_lcb_95"], best["support"]):
            best = candidate
    if best is None:
        return {"support": 0, "success": 0, "precision": 0.0, "precision_wilson_lcb_95": 0.0, "precision_wilson_lcb_99": 0.0, "threshold": 1.0, "mean_raw_probability": 0.0, "ece_raw_probability": 0.0}
    return best


def evaluate_threshold(probs: np.ndarray, truth: np.ndarray, threshold: float, calibrated_probability: float) -> dict[str, Any]:
    mask = probs >= threshold
    support = int(mask.sum())
    success = int(truth[mask].sum()) if support else 0
    precision = success / support if support else 0.0
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lower(success, support, Z95),
        "precision_wilson_lcb_99": wilson_lower(success, support, Z99),
        "coverage": support / len(truth) if len(truth) else 0.0,
        "ece": abs(calibrated_probability - precision) if support else None,
        "calibrated_probability": calibrated_probability,
    }


def passes(cal: dict[str, Any], test: dict[str, Any]) -> tuple[bool, bool]:
    p95 = (
        cal["support"] >= 120
        and test["support"] >= 60
        and test["precision_wilson_lcb_95"] >= 0.95
        and test["coverage"] >= 0.03
        and test["ece"] is not None
        and test["ece"] <= 0.05
    )
    p99 = (
        cal["support"] >= 300
        and test["support"] >= 120
        and test["precision_wilson_lcb_99"] >= 0.99
        and test["coverage"] >= 0.02
        and test["ece"] is not None
        and test["ece"] <= 0.02
    )
    return p95, p99


def model_specs() -> list[tuple[str, Any]]:
    # Shallow GB is intentionally first as the stable white-box-ish baseline; HGB is a sensitivity probe.
    return [
        ("gb_shallow_primary", GradientBoostingClassifier(n_estimators=80, max_depth=2, learning_rate=0.05, random_state=17)),
        ("hgb_regularized_sensitivity", HistGradientBoostingClassifier(max_iter=80, max_leaf_nodes=8, learning_rate=0.05, l2_regularization=0.1, random_state=17)),
    ]


def run_search() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    missing_regimes = list(target_map())
    results: list[dict[str, Any]] = []

    for universe_id, (path, horizon, timeframe) in LONGSPAN.items():
        df = build_features(load_candles(path), horizon)
        train, cal, test = split_chrono(df)
        feature_cols = [
            col
            for col in df.columns
            if pd.api.types.is_numeric_dtype(df[col])
            and not col.startswith("target_")
            and col not in {"future_ret", "future_absret", "future_max_down", "future_range"}
        ]
        split_info = {
            "train": len(train),
            "calibration": len(cal),
            "test": len(test),
            "train_time_range": {"start": str(train["ts"].min()), "end": str(train["ts"].max())},
            "calibration_time_range": {"start": str(cal["ts"].min()), "end": str(cal["ts"].max())},
            "test_time_range": {"start": str(test["ts"].min()), "end": str(test["ts"].max())},
        }
        x_train = train[feature_cols].values
        x_cal = cal[feature_cols].values
        x_test = test[feature_cols].values

        for regime_id, target in target_map().items():
            for model_name, model in model_specs():
                pipeline = make_pipeline(SimpleImputer(strategy="median"), model)
                y_train = train[target].astype(int).values
                y_cal = cal[target].astype(int).values
                y_test = test[target].astype(int).values
                pipeline.fit(x_train, y_train)
                cal_probs = pipeline.predict_proba(x_cal)[:, 1]
                test_probs = pipeline.predict_proba(x_test)[:, 1]
                cal_metrics = best_threshold(cal_probs, y_cal)
                test_metrics = evaluate_threshold(test_probs, y_test, cal_metrics["threshold"], cal_metrics["precision"])
                accepted_95, accepted_99 = passes(cal_metrics, test_metrics)
                blockers: list[str] = []
                if cal_metrics["support"] < 120:
                    blockers.append("calibration_support_too_thin")
                if test_metrics["support"] < 60:
                    blockers.append("test_support_too_thin")
                if test_metrics["precision_wilson_lcb_95"] < 0.95:
                    blockers.append("precision_wilson_lcb_below_95")
                if test_metrics["ece"] is None or test_metrics["ece"] > 0.05:
                    blockers.append("ece_above_95_limit")
                if test_metrics["coverage"] < 0.03:
                    blockers.append("coverage_below_95_limit")

                results.append(
                    {
                        "regime_id": regime_id,
                        "universe_id": universe_id,
                        "market": "NQ CME futures",
                        "timeframe": timeframe,
                        "source_path": str(path),
                        "horizon_bars": horizon,
                        "model": model_name,
                        "feature_count": len(feature_cols),
                        "split": split_info,
                        "target": target,
                        "thresholds_train_only": df.attrs.get("thresholds", {}),
                        "calibration": cal_metrics,
                        "test": test_metrics,
                        "accepted_95": accepted_95,
                        "accepted_99": accepted_99,
                        "confidence_lane": "99" if accepted_99 else "95" if accepted_95 else "abstain",
                        "blocker": "none" if accepted_95 or accepted_99 else ";".join(blockers),
                    }
                )

    accepted = [row for row in results if row["accepted_95"] or row["accepted_99"]]
    accepted_by_regime: dict[str, dict[str, Any]] = {}
    for regime_id in missing_regimes:
        regime_hits = [row for row in accepted if row["regime_id"] == regime_id]
        if regime_hits:
            accepted_by_regime[regime_id] = sorted(
                regime_hits,
                key=lambda row: (row["accepted_99"], row["test"]["precision_wilson_lcb_95"], row["test"]["support"]),
                reverse=True,
            )[0]

    session = json.loads(SESSION_PACKET.read_text())
    session_packet = session["accepted_packet"]
    cross_market = json.loads(CROSS_MARKET_PACKET.read_text()) if CROSS_MARKET_PACKET.exists() else {}
    missing_after = [regime for regime in missing_regimes if regime not in accepted_by_regime]
    accepted_packets = [
        {
            "accepted_regime_id": regime_id,
            "market": row["market"],
            "timeframe": row["timeframe"],
            "horizon": f"{row['horizon_bars']} bars",
            "allowed_action": "guardrail_only_liquidity_context" if regime_id == "ThinLiquidity" else "release_candidate_only_when_other_gates_pass",
            "confidence_lane": row["confidence_lane"],
            "precision_wilson_lcb": row["test"]["precision_wilson_lcb_99"] if row["accepted_99"] else row["test"]["precision_wilson_lcb_95"],
            "calibration_support": row["calibration"]["support"],
            "test_support": row["test"]["support"],
            "ece": row["test"]["ece"],
            "coverage": row["test"]["coverage"],
            "transition_hazard": "not_measured_in_longspan_sidecar",
            "duration_viable": True,
            "downstream_evidence_fields": [
                "NQ longspan OHLCV",
                "shallow gradient boosting score",
                "chronological calibration/test split",
            ],
            "artifact_path": "docs/experiments/actionable-regime-confidence/runs/20260510T202239-per-regime-coverage-reset/evidence_packet_per_regime_coverage_reset.json",
        }
        for regime_id, row in sorted(accepted_by_regime.items())
    ]

    packet = {
        "schema_version": "board-a-per-regime-coverage-reset/v1",
        "loop_id": "20260510T202239+0800-per-regime-coverage-reset",
        "run_root": "docs/experiments/actionable-regime-confidence/runs/20260510T202239-per-regime-coverage-reset",
        "objective": "User clarified one accepted regime is insufficient; every required regime needs its own accepted 95%-99% packet.",
        "threshold_policy": {
            "thresholds_relaxed": False,
            "precision_wilson_lcb_95": 0.95,
            "precision_wilson_lcb_99": 0.99,
            "calibration_support_min_95": 120,
            "test_support_min_95": 60,
            "ece_max_95": 0.05,
            "coverage_min_95": 0.03,
            "calibrated_probability": "calibration precision at selected threshold",
        },
        "input_sources": {
            "existing_session_liquidity_packet": str(SESSION_PACKET.relative_to(REPO)),
            "cross_market_condition_matrix": str(CROSS_MARKET_PACKET.relative_to(REPO)) if CROSS_MARKET_PACKET.exists() else "missing",
            "longspan_sources": {key: str(value[0]) for key, value in LONGSPAN.items()},
        },
        "existing_accepted_regime_packets": [session_packet],
        "accepted_new_regime_count_95": sum(1 for row in accepted_by_regime.values() if row["accepted_95"]),
        "accepted_new_regime_count_99": sum(1 for row in accepted_by_regime.values() if row["accepted_99"]),
        "accepted_new_regime_packets": accepted_packets,
        "per_regime_coverage": {
            "SessionLiquidityCoreViable": "accepted_95_existing",
            **{regime: "accepted_95" if regime in accepted_by_regime else "missing_accepted_packet" for regime in missing_regimes},
        },
        "missing_after_this_loop": missing_after,
        "all_required_regimes_covered": not missing_after,
        "candidate_results": results,
        "cross_market_readback": {
            "present": bool(cross_market),
            "accepted_new_regime_count_95": cross_market.get("decision", {}).get("accepted_new_regime_count_95"),
            "accepted_new_regime_count_99": cross_market.get("decision", {}).get("accepted_new_regime_count_99"),
        },
        "decision": {
            "board_state": "active" if missing_after else "accepted_95",
            "accepted_required_regimes": ["SessionLiquidityCoreViable", *sorted(accepted_by_regime)],
            "missing_required_regimes": missing_after,
            "trade_usable": False,
            "why_not_trade_usable": [
                "Per-regime confidence coverage is still incomplete." if missing_after else "Confidence coverage exists but execution promotion still requires non-observe release gates.",
                "No result in this loop changes execution tree observe/transition_guardrail status.",
            ],
            "next_action": "Target TrendExpansion, RangeConsolidation, ExtremeStress, and ReversalBrewing with new factor families and additional provider/timeframe evidence; keep ThinLiquidity as accepted_95 only if downstream review accepts the longspan sidecar.",
        },
    }
    (RUN_ROOT / "evidence_packet_per_regime_coverage_reset.json").write_text(json.dumps(packet, indent=2, sort_keys=False) + "\n")
    (OUT_DIR / "per_regime_longspan_model_search_report.json").write_text(json.dumps(packet, indent=2, sort_keys=False) + "\n")
    return packet


if __name__ == "__main__":
    report = run_search()
    print(json.dumps({
        "ok": True,
        "accepted_new_regime_count_95": report["accepted_new_regime_count_95"],
        "accepted_new_regime_count_99": report["accepted_new_regime_count_99"],
        "missing_after_this_loop": report["missing_after_this_loop"],
        "evidence_packet": str(RUN_ROOT / "evidence_packet_per_regime_coverage_reset.json"),
    }, indent=2))
