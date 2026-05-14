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
OUT_DIR = ROOT / "execution-native-release-512-online-changepoint"
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


def _sigmoid(x: float) -> float:
    x = max(min(x, 20.0), -20.0)
    return 1.0 / (1.0 + math.exp(-x))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
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


def _window_features(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    candles = payload.get("candles", [])
    close = np.array([_safe_float(row.get("close")) for row in candles], dtype=float)
    high = np.array([_safe_float(row.get("high")) for row in candles], dtype=float)
    low = np.array([_safe_float(row.get("low")) for row in candles], dtype=float)
    volume = np.array([_safe_float(row.get("volume")) for row in candles], dtype=float)
    open_ = np.array([_safe_float(row.get("open")) for row in candles], dtype=float)
    out: dict[str, float] = {}
    if len(close) < 20:
        return out

    log_close = np.log(np.maximum(close, 1e-9))
    ret = np.diff(log_close)
    true_range = np.maximum(high - low, np.maximum(np.abs(high - close), np.abs(low - close)))
    true_range = true_range[1:]
    body = np.abs(close - open_)[1:]
    log_volume = np.log1p(np.maximum(volume, 0.0))
    volume_diff = np.diff(log_volume)

    for horizon in (16, 32, 64, 96):
        if len(ret) <= horizon + 2:
            continue
        recent = ret[-horizon:]
        prior = ret[-2 * horizon : -horizon] if len(ret) >= 2 * horizon else ret[: -horizon]
        prior = prior if len(prior) else ret[:-1]
        prior_std = float(np.std(prior)) or 1e-9
        recent_std = float(np.std(recent)) or 1e-9
        half = max(4, horizon // 2)
        recent_half = ret[-half:]
        prior_half = ret[-horizon:-half]
        prior_half_std = float(np.std(prior_half)) or prior_std

        ret_z = (recent[-1] - float(np.mean(prior))) / prior_std
        mean_shift = (float(np.mean(recent_half)) - float(np.mean(prior_half))) / (prior_half_std + 1e-9)
        vol_jump = recent_std / (prior_std + 1e-9)

        tr_recent = true_range[-horizon:]
        tr_prior = true_range[-2 * horizon : -horizon] if len(true_range) >= 2 * horizon else true_range[: -horizon]
        tr_z = (float(np.mean(tr_recent)) - float(np.mean(tr_prior))) / ((float(np.std(tr_prior)) or 1e-9) + 1e-9)

        body_recent = body[-horizon:]
        body_prior = body[-2 * horizon : -horizon] if len(body) >= 2 * horizon else body[: -horizon]
        body_z = (float(np.mean(body_recent)) - float(np.mean(body_prior))) / ((float(np.std(body_prior)) or 1e-9) + 1e-9)

        vd_recent = volume_diff[-horizon:]
        vd_prior = volume_diff[-2 * horizon : -horizon] if len(volume_diff) >= 2 * horizon else volume_diff[: -horizon]
        vd_z = (float(np.mean(vd_recent)) - float(np.mean(vd_prior))) / ((float(np.std(vd_prior)) or 1e-9) + 1e-9)

        z_series = (recent - float(np.mean(prior))) / (prior_std + 1e-9)
        cusum_up = 0.0
        cusum_down = 0.0
        max_up = 0.0
        max_down = 0.0
        for z in z_series:
            cusum_up = max(0.0, cusum_up + float(z) - 0.25)
            cusum_down = max(0.0, cusum_down - float(z) - 0.25)
            max_up = max(max_up, cusum_up)
            max_down = max(max_down, cusum_down)

        abs_z = np.abs(z_series)
        hits = np.where(abs_z >= 2.0)[0]
        age_since_z2 = float(horizon if len(hits) == 0 else horizon - 1 - hits[-1])
        hazard_raw = max(abs(ret_z), abs(mean_shift), abs(tr_z), abs(vd_z), max_up / max(1.0, horizon / 8.0), max_down / max(1.0, horizon / 8.0))

        out[f"online_ret_z_{horizon}"] = float(ret_z)
        out[f"online_mean_shift_z_{horizon}"] = float(mean_shift)
        out[f"online_vol_jump_{horizon}"] = float(vol_jump)
        out[f"online_range_z_{horizon}"] = float(tr_z)
        out[f"online_body_z_{horizon}"] = float(body_z)
        out[f"online_volume_z_{horizon}"] = float(vd_z)
        out[f"online_cusum_up_{horizon}"] = float(max_up)
        out[f"online_cusum_down_{horizon}"] = float(max_down)
        out[f"online_age_since_abs_z2_{horizon}"] = age_since_z2
        out[f"online_changepoint_hazard_{horizon}"] = _sigmoid(hazard_raw - 2.0)

    hazards = [value for key, value in out.items() if key.startswith("online_changepoint_hazard_")]
    out["online_changepoint_hazard_max"] = max(hazards) if hazards else 0.0
    out["online_changepoint_hazard_mean"] = float(np.mean(hazards)) if hazards else 0.0
    out["online_changepoint_any_high"] = 1.0 if hazards and max(hazards) >= 0.75 else 0.0
    return out


def _feature_frame(base: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for window in base["window"].astype(str).str.zfill(3):
        path = WINDOWS_DIR / f"nq_15m_obs_{window}.json"
        row = {"window": window}
        row.update(_window_features(path))
        rows.append(row)
    online = pd.DataFrame(rows)
    merged = base.copy()
    merged["window"] = merged["window"].astype(str).str.zfill(3)
    return merged.merge(online, on="window", how="left")


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
        random_seed=42,
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

    importances = model.get_feature_importance()
    top = sorted(zip(features, importances), key=lambda item: item[1], reverse=True)[:20]
    report.update(
        {
            "status": "ran_catboost",
            "feature_count": len(features),
            "online_changepoint_features": len([name for name in features if name.startswith("online_")]),
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
    df = _feature_frame(base)
    numeric_features = []
    for col in df.columns:
        if col in EXCLUDE_FEATURES or col == "window":
            continue
        if col.startswith("score_"):
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
            row[f"online_cp_score_{target}"] = float(score)

    feature_path = OUT_DIR / "execution_native_online_changepoint_features_512.csv"
    score_path = OUT_DIR / "execution_native_online_changepoint_scores_512.csv"
    report_path = OUT_DIR / "execution_native_online_changepoint_catboost_probe_512.json"
    df.to_csv(feature_path, index=False)
    with score_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(score_rows[0].keys()))
        writer.writeheader()
        writer.writerows(score_rows)
    accepted_count = sum(len(report.get("accepted_rules", [])) for report in reports)
    payload = {
        "schema_version": "execution-native-online-changepoint/v1",
        "input_feature_table": str(BASE_SCORES),
        "feature_table": str(feature_path),
        "score_table": str(score_path),
        "row_count": int(len(df)),
        "feature_count": len(numeric_features),
        "online_changepoint_feature_count": len([name for name in numeric_features if name.startswith("online_")]),
        "training_policy": {
            "chronological_split": {"train": 256, "calibration": 128, "final_holdout": 128},
            "excluded_features": sorted(EXCLUDE_FEATURES | {name for name in df.columns if name.startswith("score_")}),
            "leakage_policy": "online features use only candles inside each scan window; no offline changepoint labels or future rows are used",
        },
        "catboost_reports": reports,
        "accepted_candidate_count": accepted_count,
        "overall_decision": "accepted_95_candidate" if accepted_count else "no_95_candidate",
    }
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"report": str(report_path), "overall_decision": payload["overall_decision"], "accepted_candidate_count": accepted_count}, indent=2))


if __name__ == "__main__":
    main()
