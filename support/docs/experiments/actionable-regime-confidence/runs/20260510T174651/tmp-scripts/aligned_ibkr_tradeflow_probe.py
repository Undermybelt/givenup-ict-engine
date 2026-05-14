from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier


ROOT = Path("/tmp/ict-regime-chain-20260509T231052")
BASE_SCORES = ROOT / "execution-native-release-512" / "execution_native_release_provider_ofi_scores_512.csv"
WINDOWS_DIR = ROOT / "structural-replay-cont-windows-512"
TRADEFLOW = ROOT / "provider-probes" / "aligned_ibkr_nq_contract_roll_15m_trades_combined.csv"
OUT_DIR = ROOT / "execution-native-release-512-aligned-ibkr-tradeflow"
TARGETS = [
    "ReleaseAllowed",
    "LowTransitionHazard",
    "ReadinessObserveOrReady",
    "DurationViable",
    "PathEdgePositive",
]
EXCLUDE_FEATURES = set(TARGETS) | {
    "safe_forward",
    "score_ReleaseAllowed",
    "score_LowTransitionHazard",
    "score_ReadinessObserveOrReady",
    "score_DurationViable",
    "score_PathEdgePositive",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        out = float(value)
        if not math.isfinite(out):
            return default
        return out
    except (TypeError, ValueError):
        return default


def _wilson_lower(success: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    phat = success / total
    denom = 1.0 + z * z / total
    centre = phat + z * z / (2.0 * total)
    margin = z * math.sqrt((phat * (1.0 - phat) + z * z / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def _window_final_ts() -> dict[str, int]:
    out = {}
    for path in sorted(WINDOWS_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        out[path.stem[-3:]] = int(payload["candles"][-1]["timestamp"])
    return out


def _tradeflow_features(base: pd.DataFrame) -> pd.DataFrame:
    final_ts = _window_final_ts()
    trades = pd.read_csv(TRADEFLOW)
    trades["ts_ms"] = pd.to_datetime(trades["ts"], utc=True).astype("int64") // 1_000_000
    if trades["ts_ms"].max() < 10_000_000_000:
        trades["ts_ms"] = trades["ts_ms"] * 1000
    for col in ["open", "high", "low", "close", "volume", "count"]:
        trades[col] = pd.to_numeric(trades[col], errors="coerce")
    trades = trades.sort_values("ts_ms").reset_index(drop=True)
    ts_values = trades["ts_ms"].to_numpy()
    rows = []
    for window in base["window"].astype(str).str.zfill(3):
        ts = final_ts[window]
        idx = int(np.searchsorted(ts_values, ts, side="right") - 1)
        row: dict[str, Any] = {"window": window}
        matched = idx >= 0 and int(ts_values[idx]) == ts
        row["ibkr_nq_tradeflow_matched"] = 1.0 if matched else 0.0
        row["ibkr_nq_tradeflow_missing"] = 0.0 if matched else 1.0
        if idx < 0:
            rows.append(row)
            continue

        current = trades.iloc[idx]
        row["ibkr_nq_trade_count"] = _safe_float(current.get("count"))
        row["ibkr_nq_trade_volume"] = _safe_float(current.get("volume"))
        row["ibkr_nq_trade_range"] = _safe_float(current.get("high")) - _safe_float(current.get("low"))
        row["ibkr_nq_trade_body"] = abs(_safe_float(current.get("close")) - _safe_float(current.get("open")))
        row["ibkr_nq_trade_contract_code"] = hash(str(current.get("contract", ""))) % 1000
        for horizon in (16, 64, 192):
            start = max(0, idx - horizon + 1)
            sample = trades.iloc[start : idx + 1]
            count = pd.to_numeric(sample["count"], errors="coerce").fillna(0.0)
            volume = pd.to_numeric(sample["volume"], errors="coerce").fillna(0.0)
            high = pd.to_numeric(sample["high"], errors="coerce")
            low = pd.to_numeric(sample["low"], errors="coerce")
            close = pd.to_numeric(sample["close"], errors="coerce")
            ret = np.log(np.maximum(close.to_numpy(dtype=float), 1e-9))
            ret = np.diff(ret) if len(ret) > 1 else np.array([0.0])

            row[f"ibkr_nq_count_mean_{horizon}"] = float(count.mean())
            row[f"ibkr_nq_count_sum_{horizon}"] = float(count.sum())
            row[f"ibkr_nq_volume_mean_{horizon}"] = float(volume.mean())
            row[f"ibkr_nq_volume_sum_{horizon}"] = float(volume.sum())
            row[f"ibkr_nq_range_mean_{horizon}"] = float((high - low).mean())
            row[f"ibkr_nq_absret_sum_{horizon}"] = float(np.abs(ret).sum())
            row[f"ibkr_nq_realized_vol_{horizon}"] = float(np.std(ret)) if len(ret) else 0.0
            if len(sample) >= horizon:
                prev_start = max(0, start - horizon)
                prev = trades.iloc[prev_start:start]
                prev_count = pd.to_numeric(prev["count"], errors="coerce").fillna(0.0)
                prev_volume = pd.to_numeric(prev["volume"], errors="coerce").fillna(0.0)
                row[f"ibkr_nq_count_z_{horizon}"] = (
                    (float(count.iloc[-1]) - float(prev_count.mean())) / ((float(prev_count.std()) or 1e-9) + 1e-9)
                    if len(prev_count)
                    else 0.0
                )
                row[f"ibkr_nq_volume_z_{horizon}"] = (
                    (float(volume.iloc[-1]) - float(prev_volume.mean())) / ((float(prev_volume.std()) or 1e-9) + 1e-9)
                    if len(prev_volume)
                    else 0.0
                )
        rows.append(row)
    return pd.DataFrame(rows)


def _candidate_thresholds(scores: np.ndarray) -> list[float]:
    if len(scores) == 0:
        return []
    quantiles = np.unique(np.quantile(scores, np.linspace(0.50, 0.98, 25)))
    return sorted((float(x) for x in quantiles), reverse=True)


def _run_target(df: pd.DataFrame, features: list[str], target: str) -> tuple[dict[str, Any], np.ndarray]:
    y = df[target].astype(int).to_numpy()
    train_idx = np.arange(0, 256)
    cal_idx = np.arange(256, 384)
    final_idx = np.arange(384, len(df))
    report: dict[str, Any] = {
        "target": target,
        "positive_count": int(y.sum()),
        "negative_count": int(len(y) - y.sum()),
        "split": {"train": len(train_idx), "calibration": len(cal_idx), "final_holdout": len(final_idx)},
    }
    if len(set(y[train_idx].tolist())) < 2:
        report.update({"status": "skipped_single_class_train", "accepted_rules": [], "selected_rule": None, "decision": "no_95_candidate"})
        return report, np.zeros(len(df), dtype=float)

    model = CatBoostClassifier(
        iterations=180,
        depth=4,
        learning_rate=0.045,
        loss_function="Logloss",
        verbose=False,
        random_seed=43,
        allow_writing_files=False,
        thread_count=1,
    )
    x = df[features].fillna(-999.0)
    model.fit(x.iloc[train_idx], y[train_idx])
    scores = model.predict_proba(x)[:, 1]
    accepted_rules = []
    for threshold in _candidate_thresholds(scores[cal_idx]):
        cal_mask = scores[cal_idx] >= threshold
        final_mask = scores[final_idx] >= threshold
        cal_n = int(cal_mask.sum())
        final_n = int(final_mask.sum())
        if cal_n < 20 or final_n < 20:
            continue
        cal_success = int(y[cal_idx][cal_mask].sum())
        final_success = int(y[final_idx][final_mask].sum())
        cal_lower = _wilson_lower(cal_success, cal_n)
        final_lower = _wilson_lower(final_success, final_n)
        rule = {
            "threshold": threshold,
            "calibration": {"n": cal_n, "success": cal_success, "precision": cal_success / cal_n, "wilson95_lower": cal_lower},
            "final_holdout": {"n": final_n, "success": final_success, "precision": final_success / final_n, "wilson95_lower": final_lower},
        }
        if cal_lower >= 0.95 and final_lower >= 0.95:
            accepted_rules.append(rule)

    top = sorted(zip(features, model.get_feature_importance()), key=lambda item: item[1], reverse=True)[:20]
    report.update(
        {
            "status": "ran_catboost",
            "feature_count": len(features),
            "ibkr_tradeflow_features": len([name for name in features if name.startswith("ibkr_nq_")]),
            "accepted_rules": accepted_rules,
            "selected_rule": accepted_rules[0] if accepted_rules else None,
            "decision": "accepted_95_candidate" if accepted_rules else "no_95_candidate",
            "top_importances": [{"feature": name, "importance": float(value)} for name, value in top],
        }
    )
    return report, scores


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = pd.read_csv(BASE_SCORES, dtype={"window": str})
    base["window"] = base["window"].astype(str).str.zfill(3)
    trade_features = _tradeflow_features(base)
    df = base.merge(trade_features, on="window", how="left")
    numeric_features = []
    for col in df.columns:
        if col in EXCLUDE_FEATURES or col == "window" or col.startswith("score_"):
            continue
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().any():
            df[col] = converted
            numeric_features.append(col)

    reports = []
    score_rows = [{"window": str(window).zfill(3)} for window in df["window"]]
    for target in TARGETS:
        report, scores = _run_target(df, numeric_features, target)
        reports.append(report)
        for row, score in zip(score_rows, scores):
            row[f"aligned_ibkr_score_{target}"] = float(score)

    feature_path = OUT_DIR / "execution_native_aligned_ibkr_tradeflow_features_512.csv"
    score_path = OUT_DIR / "execution_native_aligned_ibkr_tradeflow_scores_512.csv"
    report_path = OUT_DIR / "execution_native_aligned_ibkr_tradeflow_catboost_probe_512.json"
    df.to_csv(feature_path, index=False)
    with score_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(score_rows[0].keys()))
        writer.writeheader()
        writer.writerows(score_rows)
    accepted_count = sum(len(report.get("accepted_rules", [])) for report in reports)
    payload = {
        "schema_version": "execution-native-aligned-ibkr-tradeflow/v1",
        "input_feature_table": str(BASE_SCORES),
        "tradeflow_input": str(TRADEFLOW),
        "feature_table": str(feature_path),
        "score_table": str(score_path),
        "row_count": int(len(df)),
        "feature_count": len(numeric_features),
        "ibkr_tradeflow_feature_count": len([name for name in numeric_features if name.startswith("ibkr_nq_")]),
        "ibkr_tradeflow_matched_windows": int(df["ibkr_nq_tradeflow_matched"].sum()),
        "ibkr_tradeflow_missing_windows": int(df["ibkr_nq_tradeflow_missing"].sum()),
        "training_policy": {
            "chronological_split": {"train": 256, "calibration": 128, "final_holdout": 128},
            "excluded_features": sorted(EXCLUDE_FEATURES | {name for name in df.columns if name.startswith("score_")}),
            "leakage_policy": "IBKR trade-flow features use only bars at or before each execution scan-window final timestamp; outcome and previous score columns are excluded",
        },
        "catboost_reports": reports,
        "accepted_candidate_count": accepted_count,
        "overall_decision": "accepted_95_candidate" if accepted_count else "no_95_candidate",
    }
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"report": str(report_path), "overall_decision": payload["overall_decision"], "accepted_candidate_count": accepted_count, "matched_windows": payload["ibkr_tradeflow_matched_windows"]}, indent=2))


if __name__ == "__main__":
    main()
