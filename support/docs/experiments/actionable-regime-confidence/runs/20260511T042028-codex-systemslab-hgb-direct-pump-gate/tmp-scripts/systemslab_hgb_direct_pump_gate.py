#!/usr/bin/env python3
"""Direct manipulation gate over SystemsLab pump/dump labeled features.

Experiment artifact only. Raw source data stays under /private/tmp.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


RUN_ID = "20260511T042028+0800-codex-systemslab-hgb-direct-pump-gate"
FEATURES = [
    "std_rush_order",
    "avg_rush_order",
    "std_trades",
    "std_volume",
    "avg_volume",
    "std_price",
    "avg_price",
    "avg_price_max",
]
BLOCKED_PREDICTORS = [
    "date",
    "pump_index",
    "symbol",
    "gt",
    "hour_sin",
    "hour_cos",
    "minute_sin",
    "minute_cos",
]
TIMEFRAMES = ["5S", "15S", "25S"]
MIN_SUPPORT = 50
MIN_COVERAGE = 0.03
Z95 = 1.959963984540054


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def wilson_lcb(success: int, total: int, z: float = Z95) -> float:
    if total <= 0:
        return 0.0
    phat = success / total
    denom = 1.0 + z * z / total
    center = phat + z * z / (2.0 * total)
    margin = z * math.sqrt((phat * (1.0 - phat) + z * z / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def split_chronological(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ordered = df.sort_values(["date", "pump_index", "symbol"]).reset_index(drop=True)
    n = len(ordered)
    return ordered.iloc[: int(n * 0.60)], ordered.iloc[int(n * 0.60) : int(n * 0.80)], ordered.iloc[int(n * 0.80) :]


def profile(part: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": int(len(part)),
        "positives": int(part["gt"].sum()),
        "negatives": int(len(part) - part["gt"].sum()),
        "date_min_utc": part["date"].min().isoformat(),
        "date_max_utc": part["date"].max().isoformat(),
        "symbols": int(part["symbol"].nunique()),
        "pump_indices": int(part["pump_index"].nunique()),
    }


def sample_train(train: pd.DataFrame) -> pd.DataFrame:
    positives = train[train["gt"].astype(int) == 1]
    negatives = train[train["gt"].astype(int) == 0]
    negatives = negatives.sample(n=min(len(negatives), 80_000), random_state=17)
    return pd.concat([positives, negatives]).sort_values(["date", "pump_index", "symbol"])


def ece_10bin(proba: np.ndarray, y: np.ndarray) -> float:
    if len(proba) == 0:
        return 0.0
    bins = np.linspace(0.0, 1.0, 11)
    ece = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        if hi == 1.0:
            mask = (proba >= lo) & (proba <= hi)
        else:
            mask = (proba >= lo) & (proba < hi)
        if not mask.any():
            continue
        ece += float(mask.mean()) * abs(float(y[mask].mean()) - float(proba[mask].mean()))
    return ece


def score_mask(proba: np.ndarray, y: np.ndarray, threshold: float) -> dict[str, Any]:
    mask = proba >= threshold
    support = int(mask.sum())
    tp = int(y[mask].sum()) if support else 0
    precision = tp / support if support else 0.0
    coverage = support / len(y) if len(y) else 0.0
    return {
        "support": support,
        "true_positive": tp,
        "false_positive": support - tp,
        "precision": precision,
        "wilson95_lcb": wilson_lcb(tp, support),
        "coverage": coverage,
    }


def select_threshold(cal_proba: np.ndarray, cal_y: np.ndarray) -> tuple[float, dict[str, Any]]:
    candidates: list[tuple[float, dict[str, Any]]] = []
    for q in np.concatenate([np.linspace(0.50, 0.9999, 500), np.linspace(0.99991, 0.99999, 20)]):
        threshold = float(np.quantile(cal_proba, q))
        stats = score_mask(cal_proba, cal_y, threshold)
        if stats["support"] >= MIN_SUPPORT:
            stats["quantile"] = float(q)
            candidates.append((threshold, stats))
    return max(
        candidates,
        key=lambda item: (
            item[1]["wilson95_lcb"],
            item[1]["precision"],
            item[1]["true_positive"],
            -item[1]["support"],
        ),
    )


def model_specs(timeframe: str) -> list[tuple[str, Any, bool]]:
    sampled = [
        (
            "hgb_sampled",
            HistGradientBoostingClassifier(
                max_iter=80,
                max_leaf_nodes=7,
                learning_rate=0.05,
                l2_regularization=1.0,
                class_weight="balanced",
                random_state=17,
            ),
            True,
        ),
        (
            "logit_sampled",
            make_pipeline(StandardScaler(), LogisticRegression(max_iter=500, class_weight="balanced", random_state=17)),
            True,
        ),
    ]
    if timeframe == "25S":
        sampled.extend(
            [
                (
                    "hgb_full_7x120",
                    HistGradientBoostingClassifier(
                        max_iter=120,
                        max_leaf_nodes=7,
                        learning_rate=0.04,
                        l2_regularization=1.0,
                        class_weight="balanced",
                        random_state=17,
                    ),
                    False,
                ),
                (
                    "hgb_full_15x160",
                    HistGradientBoostingClassifier(
                        max_iter=160,
                        max_leaf_nodes=15,
                        learning_rate=0.035,
                        l2_regularization=0.5,
                        class_weight="balanced",
                        random_state=19,
                    ),
                    False,
                ),
                (
                    "hgb_full_31x120",
                    HistGradientBoostingClassifier(
                        max_iter=120,
                        max_leaf_nodes=31,
                        learning_rate=0.03,
                        l2_regularization=0.2,
                        class_weight="balanced",
                        random_state=23,
                    ),
                    False,
                ),
            ]
        )
    return sampled


def evaluate_timeframe(source_root: Path, timeframe: str) -> dict[str, Any]:
    path = source_root / "labeled_features" / f"features_{timeframe}.csv.gz"
    df = pd.read_csv(path, parse_dates=["date"]).dropna(subset=FEATURES + ["date", "gt"]).copy()
    df["gt"] = df["gt"].astype(int)
    train, calibration, test = split_chronological(df)
    cal_x = calibration[FEATURES].astype(float)
    cal_y = calibration["gt"].astype(int).to_numpy()
    test_x = test[FEATURES].astype(float)
    test_y = test["gt"].astype(int).to_numpy()

    model_reports = []
    for model_name, model, sampled in model_specs(timeframe):
        fit_frame = sample_train(train) if sampled else train
        fit_x = fit_frame[FEATURES].astype(float)
        fit_y = fit_frame["gt"].astype(int).to_numpy()
        model.fit(fit_x, fit_y)
        cal_proba = model.predict_proba(cal_x)[:, 1]
        test_proba = model.predict_proba(test_x)[:, 1]
        threshold, cal_stats = select_threshold(cal_proba, cal_y)
        test_stats = score_mask(test_proba, test_y, threshold)
        accepted = (
            cal_stats["support"] >= MIN_SUPPORT
            and test_stats["support"] >= MIN_SUPPORT
            and cal_stats["coverage"] >= MIN_COVERAGE
            and test_stats["coverage"] >= MIN_COVERAGE
            and cal_stats["wilson95_lcb"] >= 0.95
            and test_stats["wilson95_lcb"] >= 0.95
            and ece_10bin(cal_proba, cal_y) <= 0.05
            and ece_10bin(test_proba, test_y) <= 0.05
        )
        model_reports.append(
            {
                "timeframe": timeframe,
                "model": model_name,
                "fit_rows": int(len(fit_frame)),
                "fit_positives": int(fit_frame["gt"].sum()),
                "threshold": threshold,
                "calibration": cal_stats,
                "test": test_stats,
                "calibration_ece_10bin": ece_10bin(cal_proba, cal_y),
                "test_ece_10bin": ece_10bin(test_proba, test_y),
                "accepted_95": accepted,
            }
        )

    return {
        "timeframe": timeframe,
        "path": str(path),
        "sha256": sha256(path),
        "features_used": FEATURES,
        "blocked_predictors": BLOCKED_PREDICTORS,
        "profile": {
            "all": profile(df),
            "train_select": profile(train),
            "calibration": profile(calibration),
            "test": profile(test),
        },
        "model_reports": sorted(
            model_reports,
            key=lambda row: (
                row["test"]["wilson95_lcb"],
                row["test"]["precision"],
                row["calibration"]["wilson95_lcb"],
            ),
            reverse=True,
        ),
    }


def write_summary(path: Path, timeframe_reports: list[dict[str, Any]]) -> None:
    fieldnames = [
        "timeframe",
        "model",
        "fit_rows",
        "fit_positives",
        "threshold",
        "cal_support",
        "cal_precision",
        "cal_wilson95_lcb",
        "cal_coverage",
        "cal_ece_10bin",
        "test_support",
        "test_precision",
        "test_wilson95_lcb",
        "test_coverage",
        "test_ece_10bin",
        "accepted_95",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for report in timeframe_reports:
            for row in report["model_reports"]:
                writer.writerow(
                    {
                        "timeframe": row["timeframe"],
                        "model": row["model"],
                        "fit_rows": row["fit_rows"],
                        "fit_positives": row["fit_positives"],
                        "threshold": f"{row['threshold']:.12f}",
                        "cal_support": row["calibration"]["support"],
                        "cal_precision": f"{row['calibration']['precision']:.12f}",
                        "cal_wilson95_lcb": f"{row['calibration']['wilson95_lcb']:.12f}",
                        "cal_coverage": f"{row['calibration']['coverage']:.12f}",
                        "cal_ece_10bin": f"{row['calibration_ece_10bin']:.12f}",
                        "test_support": row["test"]["support"],
                        "test_precision": f"{row['test']['precision']:.12f}",
                        "test_wilson95_lcb": f"{row['test']['wilson95_lcb']:.12f}",
                        "test_coverage": f"{row['test']['coverage']:.12f}",
                        "test_ece_10bin": f"{row['test_ece_10bin']:.12f}",
                        "accepted_95": row["accepted_95"],
                    }
                )


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    best = report["best_model"]
    lines = [
        "# SystemsLab HGB Direct Pump/Dump Gate",
        "",
        f"Run ID: `{RUN_ID}`.",
        "",
        "This is a direct-input `Manipulation` probe using labeled pump/dump exchange-transaction features.",
        "It is not an OHLCV/session/liquidity proxy acceptance path.",
        "",
        "## Decision",
        "",
        f"- Gate: `{report['gate']}`",
        f"- Accepted 95: `{str(report['accepted_95']).lower()}`",
        f"- Best model: `{best['timeframe']}` / `{best['model']}`",
        f"- Calibration Wilson95 / precision / support / coverage: `{best['calibration']['wilson95_lcb']:.6f}` / `{best['calibration']['precision']:.6f}` / `{best['calibration']['support']}` / `{best['calibration']['coverage']:.6f}`",
        f"- Test Wilson95 / precision / support / coverage: `{best['test']['wilson95_lcb']:.6f}` / `{best['test']['precision']:.6f}` / `{best['test']['support']}` / `{best['test']['coverage']:.6f}`",
        "- Blocker: held-out Wilson95 and coverage remain below Board A acceptance thresholds.",
        "",
        "## Policy",
        "",
        f"- Features used: `{', '.join(FEATURES)}`",
        f"- Blocked predictors: `{', '.join(BLOCKED_PREDICTORS)}`",
        "- Runtime code changed: false",
        "- Thresholds relaxed: false",
        "- Raw data committed to repo: false",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    reports = [evaluate_timeframe(args.source_root, timeframe) for timeframe in TIMEFRAMES]
    all_models = [row for report in reports for row in report["model_reports"]]
    best = max(
        all_models,
        key=lambda row: (
            row["test"]["wilson95_lcb"],
            row["test"]["precision"],
            row["calibration"]["wilson95_lcb"],
        ),
    )
    accepted = [row for row in all_models if row["accepted_95"]]
    gate = "accepted_systemslab_hgb_direct_pump_95" if accepted else "blocked_systemslab_hgb_direct_pump_below_95"
    report = {
        "run_id": RUN_ID,
        "candidate_regime": "Manipulation",
        "gate": gate,
        "accepted_95": bool(accepted),
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "raw_data_committed_to_repo": False,
        "source_repo": "https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset",
        "source_root": str(args.source_root),
        "source_context": "Direct crypto pump-and-dump event dataset with labeled exchange-transaction feature chunks.",
        "label_polarity": "gt=1 labeled pump/dump chunk; gt=0 non-pump chunk.",
        "gate_contract": {
            "min_support": MIN_SUPPORT,
            "min_coverage": MIN_COVERAGE,
            "min_calibration_wilson95_lcb": 0.95,
            "min_test_wilson95_lcb": 0.95,
            "max_ece_10bin": 0.05,
        },
        "best_model": best,
        "timeframe_reports": reports,
        "active_root_accounting_after_gate": {
            "accepted_95_roots": ["Bull", "Crisis"] + (["Manipulation"] if accepted else []),
            "missing_95_roots": ["Bear", "Sideways"] + ([] if accepted else ["Manipulation"]),
        },
    }
    (args.out_dir / "systemslab_hgb_direct_pump_gate_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    write_summary(args.out_dir / "systemslab_hgb_direct_pump_gate_summary.csv", reports)
    write_markdown(args.out_dir / "systemslab_hgb_direct_pump_gate_report.md", report)
    print(json.dumps({"gate": gate, "accepted_95": bool(accepted), "best_model": best}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
