#!/usr/bin/env python3
"""Evaluate SystemsLab-Sapienza direct pump/dump labeled features.

Experiment artifact only. Source data stays under /private/tmp.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


RUN_ID = "20260511T030031+0800-codex-systemslab-direct-pump-gate"
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
TIMEFRAMES = ["5S", "25S"]
MIN_SUPPORT = 50
QUANTILES = [0.001, 0.0025, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.80, 0.90, 0.95, 0.98, 0.99, 0.995, 0.9975, 0.999]
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
    train_end = int(n * 0.60)
    cal_end = int(n * 0.80)
    return ordered.iloc[:train_end], ordered.iloc[train_end:cal_end], ordered.iloc[cal_end:]


def stats(mask: np.ndarray, y: np.ndarray) -> dict:
    support = int(mask.sum())
    tp = int(y[mask].sum()) if support else 0
    precision = tp / support if support else 0.0
    return {
        "support": support,
        "true_positive": tp,
        "false_positive": support - tp,
        "precision": precision,
        "wilson95_lcb": wilson_lcb(tp, support),
    }


def evaluate_rule(df: pd.DataFrame, feature: str, op: str, threshold: float) -> dict:
    values = df[feature].to_numpy(dtype=float)
    y = df["gt"].astype(int).to_numpy()
    if op == ">=":
        mask = values >= threshold
    else:
        mask = values <= threshold
    out = stats(mask, y)
    out.update(
        {
            "feature": feature,
            "op": op,
            "threshold": float(threshold),
            "rule": f"{feature} {op} {threshold:.12g}",
        }
    )
    return out


def evaluate_timeframe(source_root: Path, timeframe: str) -> dict:
    path = source_root / "labeled_features" / f"features_{timeframe}.csv.gz"
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.dropna(subset=FEATURES + ["date", "gt"]).copy()
    df["gt"] = df["gt"].astype(int)
    train, calibration, test = split_chronological(df)

    candidates = []
    for feature in FEATURES:
        values = train[feature].to_numpy(dtype=float)
        thresholds = sorted(set(float(x) for x in np.quantile(values, QUANTILES)))
        for threshold in thresholds:
            for op in (">=", "<="):
                train_stats = evaluate_rule(train, feature, op, threshold)
                if train_stats["support"] >= MIN_SUPPORT:
                    candidates.append(train_stats)

    selected = max(
        candidates,
        key=lambda row: (
            row["wilson95_lcb"],
            row["precision"],
            row["true_positive"],
            row["support"],
        ),
    )
    cal_stats = evaluate_rule(calibration, selected["feature"], selected["op"], selected["threshold"])
    test_stats = evaluate_rule(test, selected["feature"], selected["op"], selected["threshold"])

    accepted_95 = (
        cal_stats["support"] >= MIN_SUPPORT
        and test_stats["support"] >= MIN_SUPPORT
        and cal_stats["wilson95_lcb"] >= 0.95
        and test_stats["wilson95_lcb"] >= 0.95
    )

    top_train = sorted(
        candidates,
        key=lambda row: (
            row["wilson95_lcb"],
            row["precision"],
            row["true_positive"],
            row["support"],
        ),
        reverse=True,
    )[:20]

    def profile(part: pd.DataFrame) -> dict:
        return {
            "rows": int(len(part)),
            "positives": int(part["gt"].sum()),
            "negatives": int(len(part) - part["gt"].sum()),
            "date_min_utc": part["date"].min().isoformat(),
            "date_max_utc": part["date"].max().isoformat(),
            "symbols": int(part["symbol"].nunique()),
            "pump_indices": int(part["pump_index"].nunique()),
        }

    return {
        "timeframe": timeframe,
        "path": str(path),
        "sha256": sha256(path),
        "candidate_rules": len(candidates),
        "features_used": FEATURES,
        "blocked_predictors": ["date", "pump_index", "symbol", "gt", "hour_sin", "hour_cos", "minute_sin", "minute_cos"],
        "profile": {
            "all": profile(df),
            "train_select": profile(train),
            "calibration": profile(calibration),
            "test": profile(test),
        },
        "selected_rule": selected["rule"],
        "selected_train": selected,
        "selected_calibration": cal_stats,
        "selected_test": test_stats,
        "accepted_95": accepted_95,
        "top_train_rules": top_train,
    }


def write_summary(path: Path, timeframe_reports: list[dict]) -> None:
    rows = []
    for report in timeframe_reports:
        for split_name, key in [
            ("train_select", "selected_train"),
            ("calibration", "selected_calibration"),
            ("test", "selected_test"),
        ]:
            row = dict(report[key])
            row["timeframe"] = report["timeframe"]
            row["split"] = split_name
            rows.append(row)
    fieldnames = [
        "timeframe",
        "split",
        "rule",
        "support",
        "true_positive",
        "false_positive",
        "precision",
        "wilson95_lcb",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "timeframe": row["timeframe"],
                    "split": row["split"],
                    "rule": row["rule"],
                    "support": row["support"],
                    "true_positive": row["true_positive"],
                    "false_positive": row["false_positive"],
                    "precision": f"{row['precision']:.12f}",
                    "wilson95_lcb": f"{row['wilson95_lcb']:.12f}",
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    reports = [evaluate_timeframe(args.source_root, timeframe) for timeframe in TIMEFRAMES]
    accepted = [r for r in reports if r["accepted_95"]]
    gate = "accepted_95" if accepted else "blocked_systemslab_direct_pump_gate_below_95"
    root_accepted = bool(accepted)

    source_commit = "unknown"
    git_dir = args.source_root / ".git"
    if git_dir.exists():
        import subprocess

        source_commit = subprocess.check_output(["git", "-C", str(args.source_root), "rev-parse", "HEAD"], text=True).strip()

    report = {
        "run_id": RUN_ID,
        "candidate_regime": "Manipulation",
        "gate": gate,
        "accepted_95": root_accepted,
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "raw_data_committed_to_repo": False,
        "source_repo": "https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset",
        "source_commit": source_commit,
        "source_root": str(args.source_root),
        "source_context": "Direct crypto pump-and-dump event dataset with labeled exchange-transaction feature chunks.",
        "label_polarity": "gt=1 labeled pump/dump chunk; gt=0 non-pump chunk.",
        "timeframes_evaluated": TIMEFRAMES,
        "min_support": MIN_SUPPORT,
        "timeframe_reports": reports,
        "active_root_accounting_after_gate": {
            "accepted_95_roots": ["Crisis"] + (["Manipulation"] if root_accepted else []),
            "missing_95_roots": ["Bull", "Bear", "Sideways"] + ([] if root_accepted else ["Manipulation"]),
        },
    }

    json_path = args.out_dir / "systemslab_direct_pump_gate_report.json"
    md_path = args.out_dir / "systemslab_direct_pump_gate_report.md"
    csv_path = args.out_dir / "systemslab_direct_pump_gate_summary.csv"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_summary(csv_path, reports)

    lines = [
        "# SystemsLab Direct Pump/Dump Manipulation Gate",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Source",
        "",
        f"- Repo: `{report['source_repo']}`",
        f"- Commit: `{source_commit}`",
        f"- Source root: `{args.source_root}`",
        "- Raw data committed to repo: false",
        "- Label polarity: `gt=1` labeled pump/dump chunk, `gt=0` non-pump chunk.",
        "- Predictors used: transaction-derived market features only; timestamps, pump ids, symbols, labels, and cyclic clock fields blocked.",
        "",
        "## Gate Results",
        "",
    ]
    for item in reports:
        lines.extend(
            [
                f"### {item['timeframe']}",
                "",
                f"- Rows train/cal/test: {item['profile']['train_select']['rows']:,} / {item['profile']['calibration']['rows']:,} / {item['profile']['test']['rows']:,}.",
                f"- Positives train/cal/test: {item['profile']['train_select']['positives']:,} / {item['profile']['calibration']['positives']:,} / {item['profile']['test']['positives']:,}.",
                f"- Selected train-only rule: `{item['selected_rule']}`.",
                f"- Train Wilson95 LCB: `{item['selected_train']['wilson95_lcb']:.6f}` with support {item['selected_train']['support']:,}.",
                f"- Calibration Wilson95 LCB: `{item['selected_calibration']['wilson95_lcb']:.6f}` with support {item['selected_calibration']['support']:,}.",
                f"- Test Wilson95 LCB: `{item['selected_test']['wilson95_lcb']:.6f}` with support {item['selected_test']['support']:,}.",
                f"- Accepted 95: {item['accepted_95']}.",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision",
            "",
            f"- Accepted 95 `Manipulation` root: {root_accepted}.",
            f"- Gate: `{gate}`.",
            "- Thresholds relaxed: false.",
            "- Runtime code changed: false.",
            "- Trade usable: false.",
            "",
            "The source supplies a second direct manipulation context with explicit timestamps and positive/negative labels, but the unchanged chronological held-out gate must pass before `Manipulation` can count as an accepted MainRegimeV2 root.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
