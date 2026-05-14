from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.isotonic import IsotonicRegression


BLOCKED_LEAKAGE_FIELDS = {
    "gate_status",
    "branch",
    "decision_hint",
    "execution_readiness",
    "readiness_gap_to_observe",
    "readiness_gap_to_ready",
    "hybrid_transition_hazard",
    "duration_remaining_expected_bars",
    "same_surface_execution_tree_categorical",
}

LAGS = (1, 4, 8, 16, 32, 64)
HORIZONS = (4, 8, 16)
BAD_LOSS = 0.004
TAIL_LOSS = 0.006
COST = 0.0002


@dataclass(frozen=True)
class LaneSpec:
    lane_id: str
    market: str
    timeframe: str
    provider_observations: tuple[str, ...]
    board_eligible: bool
    board_eligibility_note: str


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(out):
        return default
    return out


def _wilson_lower(success: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    centre = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def _ece(labels: np.ndarray, probs: np.ndarray, bins: int = 10) -> float:
    if len(labels) == 0:
        return 1.0
    labels = labels.astype(float)
    probs = np.clip(probs.astype(float), 0.0, 1.0)
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = len(labels)
    out = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        if hi == 1.0:
            mask = (probs >= lo) & (probs <= hi)
        else:
            mask = (probs >= lo) & (probs < hi)
        n = int(mask.sum())
        if n == 0:
            continue
        out += (n / total) * abs(float(labels[mask].mean()) - float(probs[mask].mean()))
    return float(out)


def _future_extreme(close: np.ndarray, horizon: int, reducer: str) -> np.ndarray:
    out = np.full(len(close), np.nan, dtype=float)
    if len(close) <= horizon:
        return out
    windows = np.lib.stride_tricks.sliding_window_view(close[1:], horizon)
    vals = windows.min(axis=1) if reducer == "min" else windows.max(axis=1)
    out[: len(vals)] = vals
    return out


def _read_aq_feather(data_root: Path, timeframe: str) -> pd.DataFrame:
    path = data_root / f"NQ_USD-{timeframe}.feather"
    df = pd.read_feather(path)
    df = df.rename(columns={c: c.lower() for c in df.columns})
    df["ts"] = pd.to_datetime(df["date"], unit="ms", utc=True).astype("datetime64[ns, UTC]")
    keep = ["ts", "open", "high", "low", "close", "volume"]
    return df[keep].sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def _read_qqq_yf_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    date_col = "date" if "date" in df.columns else "ts"
    df["ts"] = pd.to_datetime(df[date_col], utc=True).astype("datetime64[ns, UTC]")
    keep = ["ts", "open", "high", "low", "close", "volume"]
    return df[keep].sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def _prefix_ohlcv(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    out = df.copy()
    return out.rename(columns={c: f"{prefix}_{c}" for c in ["open", "high", "low", "close", "volume"]})


def _asof_merge(left: pd.DataFrame, right: pd.DataFrame, prefix: str, tolerance: str) -> pd.DataFrame:
    right_prefixed = _prefix_ohlcv(right, prefix)
    left = left.copy()
    right_prefixed = right_prefixed.copy()
    left["ts"] = pd.to_datetime(left["ts"], utc=True).astype("datetime64[ns, UTC]")
    right_prefixed["ts"] = pd.to_datetime(right_prefixed["ts"], utc=True).astype("datetime64[ns, UTC]")
    return pd.merge_asof(
        left.sort_values("ts"),
        right_prefixed.sort_values("ts"),
        on="ts",
        direction="backward",
        tolerance=pd.Timedelta(tolerance),
    )


def build_qqq_nq_related_lane(root: Path, aq_root: Path) -> tuple[LaneSpec, pd.DataFrame]:
    qqq_path = root / "branch-chain/qqq-regime-branch-iteration/candles/yf_QQQ_1h_2024_2025.csv"
    qqq = _prefix_ohlcv(_read_qqq_yf_csv(qqq_path), "qqq_yf_1h")
    nq_1h = _read_aq_feather(aq_root, "1h")
    nq_15m = _read_aq_feather(aq_root, "15m")
    nq_4h = _read_aq_feather(aq_root, "4h")
    df = _asof_merge(qqq, nq_1h, "nq_aq_1h", "75min")
    df = _asof_merge(df, nq_15m, "nq_aq_15m", "20min")
    df = _asof_merge(df, nq_4h, "nq_aq_4h", "5h")
    df = df.dropna(subset=["qqq_yf_1h_close", "nq_aq_1h_close", "nq_aq_15m_close"]).reset_index(drop=True)
    return (
        LaneSpec(
            lane_id="qqq_nq_related_provider_agreement_1h",
            market="QQQ,NQ",
            timeframe="1h/15m",
            provider_observations=("qqq_yfinance_1h", "nq_autoquant_1h", "nq_autoquant_15m", "nq_autoquant_4h"),
            board_eligible=True,
            board_eligibility_note="Uses the active QQQ/NQ market set with yfinance QQQ and Auto-Quant NQ cache. This is related-market provider agreement, not a same-symbol vendor duplicate.",
        ),
        df,
    )


def build_nq_mtf_lane(aq_root: Path) -> tuple[LaneSpec, pd.DataFrame]:
    nq_15m = _prefix_ohlcv(_read_aq_feather(aq_root, "15m"), "nq_aq_15m")
    nq_1h = _read_aq_feather(aq_root, "1h")
    nq_4h = _read_aq_feather(aq_root, "4h")
    nq_1d = _read_aq_feather(aq_root, "1d")
    df = _asof_merge(nq_15m, nq_1h, "nq_aq_1h", "75min")
    df = _asof_merge(df, nq_4h, "nq_aq_4h", "5h")
    df = _asof_merge(df, nq_1d, "nq_aq_1d", "36h")
    df = df.dropna(subset=["nq_aq_15m_close", "nq_aq_1h_close", "nq_aq_4h_close"]).reset_index(drop=True)
    # Keep enough density for calibration while making the probe fast and non-overlapping.
    df = df.iloc[::4].reset_index(drop=True)
    return (
        LaneSpec(
            lane_id="nq_autoquant_multitimeframe_agreement_15m",
            market="NQ",
            timeframe="15m",
            provider_observations=("nq_autoquant_15m", "nq_autoquant_1h", "nq_autoquant_4h", "nq_autoquant_1d"),
            board_eligible=False,
            board_eligibility_note="Statistical sidecar only: all observations come from the Auto-Quant local cache, so this cannot alone satisfy independent provider breadth.",
        ),
        df,
    )


def _add_provider_features(df: pd.DataFrame, providers: list[str], primary_close: str) -> pd.DataFrame:
    out = df.copy()
    out["hour_utc"] = out["ts"].dt.hour.astype(float)
    out["weekday"] = out["ts"].dt.weekday.astype(float)
    for provider in providers:
        close = pd.to_numeric(out[f"{provider}_close"], errors="coerce")
        high = pd.to_numeric(out[f"{provider}_high"], errors="coerce")
        low = pd.to_numeric(out[f"{provider}_low"], errors="coerce")
        volume = pd.to_numeric(out[f"{provider}_volume"], errors="coerce")
        one_ret = close.pct_change()
        out[f"{provider}_ret_1"] = one_ret
        out[f"{provider}_range_pct"] = (high - low) / close.replace(0.0, np.nan)
        for lag in LAGS:
            min_periods = min(lag, max(1, lag // 2))
            out[f"{provider}_ret_{lag}"] = close / close.shift(lag) - 1.0
            out[f"{provider}_vol_{lag}"] = one_ret.rolling(lag, min_periods=min_periods).std()
            abs_sum = one_ret.abs().rolling(lag, min_periods=min_periods).sum()
            out[f"{provider}_eff_{lag}"] = out[f"{provider}_ret_{lag}"].abs() / abs_sum.replace(0.0, np.nan)
            roll_min = close.rolling(lag, min_periods=min_periods).min()
            roll_max = close.rolling(lag, min_periods=min_periods).max()
            out[f"{provider}_pos_{lag}"] = (close - roll_min) / (roll_max - roll_min).replace(0.0, np.nan)
            out[f"{provider}_range_mean_{lag}"] = out[f"{provider}_range_pct"].rolling(lag, min_periods=min_periods).mean()
            out[f"{provider}_volume_z_{lag}"] = (
                (volume - volume.rolling(lag, min_periods=min_periods).mean())
                / volume.rolling(lag, min_periods=min_periods).std().replace(0.0, np.nan)
            )
    for lag in (4, 8, 16, 32):
        long_votes = []
        short_votes = []
        expansion_votes = []
        for provider in providers:
            ret = out[f"{provider}_ret_{lag}"]
            vol = out[f"{provider}_vol_{lag}"].fillna(0.0)
            eff = out[f"{provider}_eff_{lag}"].fillna(0.0)
            long_vote = (ret > (0.25 * vol + COST)) & (eff >= 0.20)
            short_vote = (ret < -(0.25 * vol + COST)) & (eff >= 0.20)
            expansion_vote = (ret.abs() > (0.35 * vol + COST)) & (eff >= 0.20)
            long_votes.append(long_vote.astype(int))
            short_votes.append(short_vote.astype(int))
            expansion_votes.append(expansion_vote.astype(int))
        out[f"provider_agreement_long_count_{lag}"] = np.sum(long_votes, axis=0)
        out[f"provider_agreement_short_count_{lag}"] = np.sum(short_votes, axis=0)
        out[f"provider_expansion_count_{lag}"] = np.sum(expansion_votes, axis=0)
        out[f"provider_agreement_long_ratio_{lag}"] = out[f"provider_agreement_long_count_{lag}"] / len(providers)
        out[f"provider_agreement_short_ratio_{lag}"] = out[f"provider_agreement_short_count_{lag}"] / len(providers)
    out["provider_agreement_long_any"] = (
        (out["provider_agreement_long_count_8"] >= 2) | (out["provider_agreement_long_count_16"] >= 2)
    ).astype(int)
    out["provider_agreement_short_any"] = (
        (out["provider_agreement_short_count_8"] >= 2) | (out["provider_agreement_short_count_16"] >= 2)
    ).astype(int)
    out["provider_disagreement_transition_guardrail"] = (
        (out["provider_agreement_long_any"] == 0) & (out["provider_agreement_short_any"] == 0)
    ).astype(int)
    close = pd.to_numeric(out[primary_close], errors="coerce").to_numpy(dtype=float)
    for horizon in HORIZONS:
        future_close = np.roll(close, -horizon)
        future_close[-horizon:] = np.nan
        future_min = _future_extreme(close, horizon, "min")
        future_max = _future_extreme(close, horizon, "max")
        future_ret = future_close / close - 1.0
        future_min_ret = future_min / close - 1.0
        future_max_ret = future_max / close - 1.0
        out[f"future_ret_{horizon}"] = future_ret
        out[f"future_min_ret_{horizon}"] = future_min_ret
        out[f"future_max_ret_{horizon}"] = future_max_ret
        out[f"target_release_long_h{horizon}"] = (
            (out["provider_agreement_long_any"] == 1)
            & (future_ret > COST)
            & (future_min_ret > -BAD_LOSS)
            & (future_max_ret > -TAIL_LOSS)
        ).astype(int)
        out[f"target_release_short_h{horizon}"] = (
            (out["provider_agreement_short_any"] == 1)
            & (-future_ret > COST)
            & (future_max_ret < BAD_LOSS)
            & (-future_min_ret > -TAIL_LOSS)
        ).astype(int)
        out[f"target_transition_stable_long_h{horizon}"] = (
            (out["provider_agreement_long_any"] == 1) & (future_min_ret > -BAD_LOSS) & (future_ret > -COST)
        ).astype(int)
        out[f"target_transition_stable_short_h{horizon}"] = (
            (out["provider_agreement_short_any"] == 1) & (future_max_ret < BAD_LOSS) & (future_ret < COST)
        ).astype(int)
    return out


def _split_indices(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    train_end = max(1, int(n * 0.50))
    cal_end = max(train_end + 1, int(n * 0.75))
    return np.arange(0, train_end), np.arange(train_end, cal_end), np.arange(cal_end, n)


def _numeric_features(df: pd.DataFrame) -> list[str]:
    blocked_prefixes = ("target_", "future_")
    features: list[str] = []
    for col in df.columns:
        if col in {"ts"} or col in BLOCKED_LEAKAGE_FIELDS or col.startswith(blocked_prefixes):
            continue
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().any():
            df[col] = converted
            features.append(col)
    return features


def _candidate_thresholds(scores: np.ndarray) -> list[float]:
    quantiles = np.unique(np.quantile(scores, np.linspace(0.50, 0.995, 80)))
    return sorted((float(q) for q in quantiles), reverse=True)


def _evaluate_rule(
    *,
    lane: LaneSpec,
    target: str,
    labels: np.ndarray,
    scores: np.ndarray,
    cal_idx: np.ndarray,
    test_idx: np.ndarray,
    candidate_kind: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for threshold in _candidate_thresholds(scores[cal_idx]):
        cal_mask = scores[cal_idx] >= threshold
        test_mask = scores[test_idx] >= threshold
        cal_n = int(cal_mask.sum())
        test_n = int(test_mask.sum())
        if cal_n < 120 or test_n < 60:
            continue
        cal_success = int(labels[cal_idx][cal_mask].sum())
        test_success = int(labels[test_idx][test_mask].sum())
        cal_precision = cal_success / cal_n
        test_precision = test_success / test_n
        cal_wilson = _wilson_lower(cal_success, cal_n)
        test_wilson = _wilson_lower(test_success, test_n)
        selected_scores = scores[test_idx][test_mask]
        selected_labels = labels[test_idx][test_mask]
        selected_ece = _ece(selected_labels, selected_scores)
        coverage = test_n / len(test_idx)
        pass_95 = (
            lane.board_eligible
            and cal_wilson >= 0.95
            and test_wilson >= 0.95
            and selected_ece <= 0.05
            and coverage >= 0.03
        )
        out.append(
            {
                "candidate_kind": candidate_kind,
                "target": target,
                "threshold": threshold,
                "calibration_support": cal_n,
                "calibration_success": cal_success,
                "calibration_precision": cal_precision,
                "calibration_wilson_lcb_95": cal_wilson,
                "test_support": test_n,
                "test_success": test_success,
                "test_precision": test_precision,
                "precision_wilson_lcb_95": test_wilson,
                "ece": selected_ece,
                "coverage": coverage,
                "accepted_95": pass_95,
                "board_eligible": lane.board_eligible,
                "board_eligibility_note": lane.board_eligibility_note,
            }
        )
    out.sort(
        key=lambda item: (
            item["accepted_95"],
            item["precision_wilson_lcb_95"],
            item["test_support"],
            item["calibration_wilson_lcb_95"],
        ),
        reverse=True,
    )
    return out


def _run_baseline_rules(lane: LaneSpec, df: pd.DataFrame, target_cols: list[str], cal_idx: np.ndarray, test_idx: np.ndarray) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for target in target_cols:
        action = "long" if "_long_" in target else "short"
        flag = df[f"provider_agreement_{action}_any"].to_numpy(dtype=float)
        labels = df[target].to_numpy(dtype=int)
        reports.extend(
            _evaluate_rule(
                lane=lane,
                target=target,
                labels=labels,
                scores=flag,
                cal_idx=cal_idx,
                test_idx=test_idx,
                candidate_kind=f"whitebox_provider_agreement_{action}",
            )[:3]
        )
    return reports


def _run_catboost(lane: LaneSpec, df: pd.DataFrame, features: list[str], target_cols: list[str], train_idx: np.ndarray, cal_idx: np.ndarray, test_idx: np.ndarray) -> list[dict[str, Any]]:
    x = df[features].replace([np.inf, -np.inf], np.nan).fillna(-999.0)
    reports: list[dict[str, Any]] = []
    for target in target_cols:
        y = df[target].astype(int).to_numpy()
        meta: dict[str, Any] = {
            "target": target,
            "positive_count": int(y.sum()),
            "negative_count": int(len(y) - y.sum()),
        }
        if len(set(y[train_idx].tolist())) < 2:
            reports.append({**meta, "candidate_kind": "catboost_isotonic", "skipped": True, "reason": "single_class_train_split"})
            continue
        model = CatBoostClassifier(
            iterations=220,
            depth=4,
            learning_rate=0.045,
            loss_function="Logloss",
            verbose=False,
            random_seed=73,
            allow_writing_files=False,
            thread_count=1,
        )
        model.fit(x.iloc[train_idx], y[train_idx])
        raw_scores = model.predict_proba(x)[:, 1]
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(raw_scores[cal_idx], y[cal_idx])
        scores = np.asarray(iso.transform(raw_scores), dtype=float)
        rules = _evaluate_rule(
            lane=lane,
            target=target,
            labels=y,
            scores=scores,
            cal_idx=cal_idx,
            test_idx=test_idx,
            candidate_kind="catboost_isotonic",
        )
        top = sorted(zip(features, model.get_feature_importance()), key=lambda item: item[1], reverse=True)[:16]
        if rules:
            for rule in rules[:5]:
                rule.update(meta)
                rule["top_importances"] = [{"feature": name, "importance": float(value)} for name, value in top]
            reports.extend(rules[:5])
        else:
            reports.append(
                {
                    **meta,
                    "candidate_kind": "catboost_isotonic",
                    "accepted_95": False,
                    "reason": "no_threshold_met_support_and_wilson_gate",
                    "top_importances": [{"feature": name, "importance": float(value)} for name, value in top],
                }
            )
    return reports


def run_lane(lane: LaneSpec, raw: pd.DataFrame, out_dir: Path) -> dict[str, Any]:
    providers = [obs for obs in lane.provider_observations if obs in {"qqq_yfinance_1h"}]
    if lane.lane_id.startswith("qqq_nq"):
        provider_prefixes = ["qqq_yf_1h", "nq_aq_1h", "nq_aq_15m", "nq_aq_4h"]
        primary_close = "nq_aq_15m_close"
    else:
        provider_prefixes = ["nq_aq_15m", "nq_aq_1h", "nq_aq_4h", "nq_aq_1d"]
        primary_close = "nq_aq_15m_close"
    del providers
    df = _add_provider_features(raw, provider_prefixes, primary_close)
    target_cols = [f"target_release_{side}_h{h}" for side in ("long", "short") for h in HORIZONS]
    required = [primary_close, *target_cols]
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=required).reset_index(drop=True)
    features = _numeric_features(df)
    train_idx, cal_idx, test_idx = _split_indices(len(df))
    lane_dir = out_dir / lane.lane_id
    lane_dir.mkdir(parents=True, exist_ok=True)
    feature_path = lane_dir / "provider_agreement_v2_features.csv"
    df.to_csv(feature_path, index=False)
    baseline_reports = _run_baseline_rules(lane, df, target_cols, cal_idx, test_idx)
    catboost_reports = _run_catboost(lane, df, features, target_cols, train_idx, cal_idx, test_idx)
    candidates = baseline_reports + catboost_reports
    accepted = [c for c in candidates if c.get("accepted_95")]
    candidates.sort(
        key=lambda item: (
            item.get("accepted_95", False),
            item.get("precision_wilson_lcb_95", -1.0),
            item.get("test_support", -1),
            item.get("calibration_wilson_lcb_95", -1.0),
        ),
        reverse=True,
    )
    summary = {
        "lane_id": lane.lane_id,
        "market": lane.market,
        "timeframe": lane.timeframe,
        "provider_observations": list(lane.provider_observations),
        "board_eligible": lane.board_eligible,
        "board_eligibility_note": lane.board_eligibility_note,
        "row_count": int(len(df)),
        "feature_count": len(features),
        "feature_table": str(feature_path),
        "split": {"train": int(len(train_idx)), "calibration": int(len(cal_idx)), "test": int(len(test_idx))},
        "target_counts": {
            target: {"positive": int(df[target].sum()), "negative": int(len(df) - df[target].sum())}
            for target in target_cols
        },
        "candidate_count": len(candidates),
        "accepted_95_count": len(accepted),
        "selected_candidate": accepted[0] if accepted else (candidates[0] if candidates else None),
        "top_candidates": candidates[:12],
    }
    (lane_dir / "provider_agreement_v2_lane_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", default="docs/experiments/actionable-regime-confidence/runs/20260510T174651")
    parser.add_argument("--autoquant-data-root", default="/Users/thrill3r/Auto-Quant/user_data/data")
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()
    root = Path(args.run_root)
    aq_root = Path(args.autoquant_data_root)
    out_dir = Path(args.out_dir) if args.out_dir else root / "provider-agreement-v2"
    out_dir.mkdir(parents=True, exist_ok=True)

    lanes: list[tuple[LaneSpec, pd.DataFrame]] = [
        build_qqq_nq_related_lane(root, aq_root),
        build_nq_mtf_lane(aq_root),
    ]
    lane_summaries = [run_lane(lane, raw, out_dir) for lane, raw in lanes]
    accepted = [
        summary["selected_candidate"]
        for summary in lane_summaries
        if summary.get("accepted_95_count", 0) > 0 and summary.get("selected_candidate")
    ]
    accepted = [item for item in accepted if item and item.get("accepted_95")]
    payload = {
        "schema_version": "board-a-provider-agreement-v2-probe/v1",
        "run_root": str(root),
        "output_dir": str(out_dir),
        "threshold_policy": {
            "precision_wilson_lcb_95": 0.95,
            "thresholds_relaxed": False,
            "calibration_support_min": 120,
            "test_support_min": 60,
            "ece_max": 0.05,
            "coverage_min": 0.03,
        },
        "label_policy": {
            "future_horizons_bars": list(HORIZONS),
            "cost": COST,
            "bad_loss": BAD_LOSS,
            "tail_loss": TAIL_LOSS,
            "blocked_leakage_fields": sorted(BLOCKED_LEAKAGE_FIELDS),
            "forbidden_future_fields_as_features": "all future_* and target_* columns are excluded from model features",
        },
        "lanes": lane_summaries,
        "accepted_95_count": len(accepted),
        "accepted_packet": accepted[0] if accepted else None,
        "overall_decision": "accepted_95_candidate" if accepted else "no_95_candidate",
    }
    report_path = out_dir / "provider_agreement_v2_probe_report.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(report_path), "overall_decision": payload["overall_decision"], "accepted_95_count": len(accepted)}, indent=2))


if __name__ == "__main__":
    main()
