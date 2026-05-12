from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


Z95 = 1.959963984540054
Z99 = 2.5758293035489004
HORIZON_BARS = 4
MIN_IBKR_COUNT = 800
MIN_IBKR_VOLUME = 100_000.0
CORE_SESSION_START_UTC = 13
CORE_SESSION_END_UTC = 18


def wilson_lower(success: int, total: int, z: float) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    centre = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def build_feature_table(ibkr_path: Path, yfinance_path: Path) -> pd.DataFrame:
    ibkr = pd.read_csv(ibkr_path)
    ibkr["ts"] = pd.to_datetime(ibkr["ts"], utc=True)
    ibkr = ibkr.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    ibkr = ibkr.rename(
        columns={
            "open": "qqq_ibkr_1h_open",
            "high": "qqq_ibkr_1h_high",
            "low": "qqq_ibkr_1h_low",
            "close": "qqq_ibkr_1h_close",
            "volume": "qqq_ibkr_1h_volume",
            "count": "qqq_ibkr_1h_count",
            "wap": "qqq_ibkr_1h_wap",
        }
    )

    yf = pd.read_csv(yfinance_path)
    yf["ts"] = pd.to_datetime(yf["date"], utc=True)
    yf = yf.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    yf = yf.rename(
        columns={
            "open": "qqq_yf_1h_open",
            "high": "qqq_yf_1h_high",
            "low": "qqq_yf_1h_low",
            "close": "qqq_yf_1h_close",
            "volume": "qqq_yf_1h_volume",
        }
    )

    df = pd.merge_asof(
        ibkr,
        yf[["ts", "qqq_yf_1h_open", "qqq_yf_1h_high", "qqq_yf_1h_low", "qqq_yf_1h_close", "qqq_yf_1h_volume"]],
        on="ts",
        direction="nearest",
        tolerance=pd.Timedelta("35min"),
    )
    df["hour_utc"] = df["ts"].dt.hour.astype(int)
    df["weekday"] = df["ts"].dt.weekday.astype(int)
    df["qqq_yfinance_current_bar_present"] = df["qqq_yf_1h_close"].notna().astype(int)
    df["session_core_utc_13_18"] = (
        (df["hour_utc"] >= CORE_SESSION_START_UTC) & (df["hour_utc"] <= CORE_SESSION_END_UTC)
    ).astype(int)

    counts = pd.to_numeric(df["qqq_ibkr_1h_count"], errors="coerce").to_numpy(dtype=float)
    volumes = pd.to_numeric(df["qqq_ibkr_1h_volume"], errors="coerce").to_numpy(dtype=float)
    target = np.zeros(len(df), dtype=int)
    future_median_count = np.full(len(df), np.nan, dtype=float)
    future_median_volume = np.full(len(df), np.nan, dtype=float)
    for idx in range(0, len(df) - HORIZON_BARS):
        count_window = counts[idx + 1 : idx + 1 + HORIZON_BARS]
        volume_window = volumes[idx + 1 : idx + 1 + HORIZON_BARS]
        future_median_count[idx] = float(np.nanmedian(count_window))
        future_median_volume[idx] = float(np.nanmedian(volume_window))
        target[idx] = int(
            future_median_count[idx] > MIN_IBKR_COUNT
            and future_median_volume[idx] > MIN_IBKR_VOLUME
        )
    df["future_median_ibkr_count_h4"] = future_median_count
    df["future_median_ibkr_volume_h4"] = future_median_volume
    df["target_session_liquidity_viable_h4"] = target
    return df.dropna(subset=["future_median_ibkr_count_h4", "future_median_ibkr_volume_h4"]).reset_index(drop=True)


def split_indices(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    train_end = max(1, int(n * 0.50))
    cal_end = max(train_end + 1, int(n * 0.75))
    return np.arange(0, train_end), np.arange(train_end, cal_end), np.arange(cal_end, n)


def index_time_range(df: pd.DataFrame, idx: np.ndarray) -> dict[str, str]:
    if len(idx) == 0:
        return {"start": "", "end": ""}
    return {
        "start": str(df.loc[int(idx[0]), "ts"]),
        "end": str(df.loc[int(idx[-1]), "ts"]),
    }


def evaluate_core_session_rule(df: pd.DataFrame, cal_idx: np.ndarray, test_idx: np.ndarray) -> dict[str, Any]:
    labels = df["target_session_liquidity_viable_h4"].to_numpy(dtype=int)
    selected = df["session_core_utc_13_18"].to_numpy(dtype=int) == 1

    cal_mask = selected[cal_idx]
    test_mask = selected[test_idx]
    cal_n = int(cal_mask.sum())
    test_n = int(test_mask.sum())
    cal_success = int(labels[cal_idx][cal_mask].sum())
    test_success = int(labels[test_idx][test_mask].sum())
    cal_precision = cal_success / cal_n if cal_n else 0.0
    test_precision = test_success / test_n if test_n else 0.0
    calibrated_probability = cal_precision
    ece = abs(test_precision - calibrated_probability)

    return {
        "candidate_kind": "whitebox_session_calendar_guardrail",
        "regime_id": "SessionLiquidityCoreViable",
        "market": "QQQ",
        "timeframe": "1h",
        "horizon": f"{HORIZON_BARS} observed IBKR bars",
        "allowed_action": "observe_or_release_candidate_only_when_other_gates_pass",
        "rule": "13 <= hour_utc <= 18",
        "target": "target_session_liquidity_viable_h4",
        "target_definition": (
            "median future IBKR trade count over next 4 observed 1h bars > 800 "
            "and median future IBKR volume over next 4 observed 1h bars > 100000"
        ),
        "calibration_support": cal_n,
        "calibration_success": cal_success,
        "calibration_precision": cal_precision,
        "calibrated_probability": calibrated_probability,
        "calibration_wilson_lcb_95": wilson_lower(cal_success, cal_n, Z95),
        "calibration_wilson_lcb_99": wilson_lower(cal_success, cal_n, Z99),
        "test_support": test_n,
        "test_success": test_success,
        "test_precision": test_precision,
        "precision_wilson_lcb_95": wilson_lower(test_success, test_n, Z95),
        "precision_wilson_lcb_99": wilson_lower(test_success, test_n, Z99),
        "ece": ece,
        "coverage": test_n / len(test_idx) if len(test_idx) else 0.0,
        "transition_hazard": 1.0 - test_precision,
        "duration_viable": test_precision >= 0.95,
        "board_eligible": True,
        "board_eligibility_note": (
            "Same-market QQQ session-liquidity packet. IBKR supplies extended-hours trade count/volume truth; "
            "yfinance supplies regular-session bar presence as provider cross-check. The candidate uses only current UTC session fields."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", default="docs/experiments/actionable-regime-confidence/runs/20260510T184532-codex-session-liquidity")
    parser.add_argument("--ibkr-path", default="docs/experiments/actionable-regime-confidence/runs/20260510T183454/provider/ibkr_QQQ_1h.csv")
    parser.add_argument("--yfinance-path", default="docs/experiments/actionable-regime-confidence/runs/20260510T183454/provider/yf_QQQ_1h_20240601_20260509.csv")
    args = parser.parse_args()

    run_root = Path(args.run_root)
    out_dir = run_root / "session-liquidity"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = build_feature_table(Path(args.ibkr_path), Path(args.yfinance_path))
    feature_path = out_dir / "session_liquidity_features.csv"
    df.to_csv(feature_path, index=False)

    train_idx, cal_idx, test_idx = split_indices(len(df))
    candidate = evaluate_core_session_rule(df, cal_idx, test_idx)
    accepted_95 = (
        candidate["board_eligible"]
        and candidate["calibration_support"] >= 120
        and candidate["test_support"] >= 60
        and candidate["calibration_wilson_lcb_95"] >= 0.95
        and candidate["precision_wilson_lcb_95"] >= 0.95
        and candidate["ece"] <= 0.05
        and candidate["coverage"] >= 0.03
    )
    accepted_99 = (
        candidate["board_eligible"]
        and candidate["calibration_support"] >= 300
        and candidate["test_support"] >= 120
        and candidate["calibration_wilson_lcb_99"] >= 0.99
        and candidate["precision_wilson_lcb_99"] >= 0.99
        and candidate["ece"] <= 0.02
        and candidate["coverage"] >= 0.02
    )
    candidate["accepted_95"] = accepted_95
    candidate["accepted_99"] = accepted_99

    accepted_packet = None
    if accepted_95:
        accepted_packet = {
            "accepted_regime_id": candidate["regime_id"],
            "market": candidate["market"],
            "timeframe": candidate["timeframe"],
            "horizon": candidate["horizon"],
            "allowed_action": candidate["allowed_action"],
            "confidence_lane": "99" if accepted_99 else "95",
            "precision_wilson_lcb": candidate["precision_wilson_lcb_99"] if accepted_99 else candidate["precision_wilson_lcb_95"],
            "calibration_support": candidate["calibration_support"],
            "test_support": candidate["test_support"],
            "ece": candidate["ece"],
            "coverage": candidate["coverage"],
            "transition_hazard": candidate["transition_hazard"],
            "duration_viable": candidate["duration_viable"],
            "downstream_evidence_fields": [
                "hour_utc",
                "session_core_utc_13_18",
                "qqq_ibkr_1h_count",
                "qqq_ibkr_1h_volume",
                "qqq_yfinance_current_bar_present",
            ],
            "artifact_path": str(out_dir / "session_liquidity_regime_probe_report.json"),
        }

    payload = {
        "schema_version": "board-a-session-liquidity-regime-probe/v1",
        "run_root": str(run_root),
        "output_dir": str(out_dir),
        "input_paths": {
            "ibkr_qqq_1h": args.ibkr_path,
            "yfinance_qqq_1h": args.yfinance_path,
        },
        "threshold_policy": {
            "precision_wilson_lcb_95": 0.95,
            "precision_wilson_lcb_99": 0.99,
            "thresholds_relaxed": False,
            "calibration_support_min_95": 120,
            "test_support_min_95": 60,
            "ece_max_95": 0.05,
            "coverage_min_95": 0.03,
        },
        "label_policy": {
            "future_horizon_observed_bars": HORIZON_BARS,
            "min_ibkr_count": MIN_IBKR_COUNT,
            "min_ibkr_volume": MIN_IBKR_VOLUME,
            "forbidden_future_fields_as_features": "future_* and target_* columns are excluded from the white-box rule",
            "blocked_leakage_fields": [
                "gate_status",
                "branch",
                "decision_hint",
                "execution_readiness",
                "readiness_gap_to_observe",
                "readiness_gap_to_ready",
                "hybrid_transition_hazard",
                "duration_remaining_expected_bars",
                "same_surface_execution_tree_categorical",
            ],
        },
        "provider_observations": [
            "ibkr_QQQ_1h_count_volume",
            "yfinance_QQQ_1h_regular_session_presence",
        ],
        "feature_table": str(feature_path),
        "split": {
            "train": int(len(train_idx)),
            "calibration": int(len(cal_idx)),
            "test": int(len(test_idx)),
            "train_time_range": index_time_range(df, train_idx),
            "calibration_time_range": index_time_range(df, cal_idx),
            "test_time_range": index_time_range(df, test_idx),
        },
        "candidate": candidate,
        "accepted_95_count": 1 if accepted_95 else 0,
        "accepted_99_count": 1 if accepted_99 else 0,
        "accepted_packet": accepted_packet,
        "overall_decision": "accepted_99_candidate" if accepted_99 else ("accepted_95_candidate" if accepted_95 else "no_95_candidate"),
    }
    report_path = out_dir / "session_liquidity_regime_probe_report.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(report_path), "overall_decision": payload["overall_decision"], "accepted_95_count": payload["accepted_95_count"], "accepted_99_count": payload["accepted_99_count"]}, indent=2))


if __name__ == "__main__":
    main()
