#!/usr/bin/env python3
"""Bounded direct Manipulation gate on the Mendeley Mt. Gox wash-trading sample."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T043249+0800-codex-mendeley-gox-hgb-wash-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T043249-codex-mendeley-gox-hgb-wash-gate"
OUT_DIR = RUN_ROOT / "gox-hgb-wash-gate"
CHECK_DIR = RUN_ROOT / "checks"

SOURCE_PATH_CANDIDATES = [
    Path("/private/tmp/gox_ml_samples.csv"),
    Path("/tmp/gox_ml_samples.csv"),
    Path("/private/tmp/ict-regime-mendeley-wash-trading/gox_ml_samples.csv"),
]
CHUNKSIZE = 250_000
FIT_SAMPLE_MAX = 450_000
RNG_SEED = 42
Z95 = 1.959963984540054

LABEL = "wash"
AMOUNT = "bitcoins"
STRICT_FEATURES = [
    "bitcoins",
    "log_bitcoins",
    "round_level",
    "buyer_24h_trade_count",
    "buyer_7d_trade_count",
    "seller_24h_trade_count",
    "seller_7d_trade_count",
    "buyer_24h_btc_sum",
    "buyer_7d_btc_sum",
    "seller_24h_btc_sum",
    "seller_7d_btc_sum",
    "buyer_seller_24h_count_ratio",
    "buyer_seller_7d_count_ratio",
    "buyer_seller_24h_btc_ratio",
    "buyer_seller_7d_btc_ratio",
    "abs_price_deviation",
    "log_time_since_last_trade",
    "hours",
]
SOURCE_USECOLS = [
    "bitcoins",
    "round_level",
    "buyer_24h_trade_count",
    "buyer_7d_trade_count",
    "seller_24h_trade_count",
    "seller_7d_trade_count",
    "buyer_24h_btc_sum",
    "buyer_7d_btc_sum",
    "seller_24h_btc_sum",
    "seller_7d_btc_sum",
    "price_deviation",
    "time_since_last_trade",
    "hours",
    LABEL,
]
BLOCKED_PREDICTORS = [
    "wash",
    "cumu_wash_percent_opt",
    "timestamp",
    "time",
    "future_*",
    "target_*",
    "next_*",
    "*_next",
]

ACCEPTANCE_95 = {
    "precision_wilson_lcb_95_min": 0.95,
    "calibration_support_min": 120,
    "test_support_min": 60,
    "coverage_min": 0.03,
    "ece_max": 0.05,
}


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lcb(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def source_path() -> Path:
    for path in SOURCE_PATH_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("gox_ml_samples.csv not found under expected temp paths")


def normalize_label(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.astype(bool)
    return series.astype(str).str.lower().str.strip().isin({"1", "true", "t", "yes", "y"})


def normalize_features(chunk: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=chunk.index)
    for col in SOURCE_USECOLS:
        if col == LABEL:
            continue
        out[col] = pd.to_numeric(chunk[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
    out["bitcoins"] = out["bitcoins"].fillna(0.0)
    out["log_bitcoins"] = np.log1p(np.abs(out["bitcoins"]))
    out["abs_price_deviation"] = np.abs(out["price_deviation"].fillna(0.0))
    out["log_time_since_last_trade"] = np.log1p(np.abs(out["time_since_last_trade"].fillna(0.0)))
    out["buyer_seller_24h_count_ratio"] = (out["buyer_24h_trade_count"].fillna(0.0) + 1.0) / (
        out["seller_24h_trade_count"].fillna(0.0) + 1.0
    )
    out["buyer_seller_7d_count_ratio"] = (out["buyer_7d_trade_count"].fillna(0.0) + 1.0) / (
        out["seller_7d_trade_count"].fillna(0.0) + 1.0
    )
    out["buyer_seller_24h_btc_ratio"] = (out["buyer_24h_btc_sum"].fillna(0.0) + 1.0) / (
        out["seller_24h_btc_sum"].fillna(0.0) + 1.0
    )
    out["buyer_seller_7d_btc_ratio"] = (out["buyer_7d_btc_sum"].fillna(0.0) + 1.0) / (
        out["seller_7d_btc_sum"].fillna(0.0) + 1.0
    )
    return out[STRICT_FEATURES].replace([np.inf, -np.inf], np.nan)


def split_bounds(path: Path) -> dict[str, Any]:
    rows = 0
    positives = 0
    for chunk in pd.read_csv(path, usecols=[LABEL], chunksize=CHUNKSIZE):
        labels = normalize_label(chunk[LABEL])
        rows += len(labels)
        positives += int(labels.sum())
    train_end = int(rows * 0.60)
    calibration_end = int(rows * 0.80)
    return {
        "rows": rows,
        "positives": positives,
        "negatives": rows - positives,
        "train_end": train_end,
        "calibration_end": calibration_end,
    }


def split_for_offsets(start: int, length: int, bounds: dict[str, Any]) -> np.ndarray:
    idx = np.arange(start, start + length)
    split = np.full(length, "test", dtype=object)
    split[idx < bounds["calibration_end"]] = "calibration"
    split[idx < bounds["train_end"]] = "train"
    return split


def collect_fit_sample(path: Path, bounds: dict[str, Any]) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    rng = np.random.default_rng(RNG_SEED)
    x_parts: list[pd.DataFrame] = []
    y_parts: list[pd.Series] = []
    seen = 0
    kept = 0
    for chunk in pd.read_csv(path, usecols=SOURCE_USECOLS, chunksize=CHUNKSIZE):
        start = seen
        seen += len(chunk)
        if start >= bounds["train_end"]:
            break
        train_len = max(0, min(seen, bounds["train_end"]) - start)
        if train_len <= 0:
            continue
        train_chunk = chunk.iloc[:train_len].copy()
        remaining_seen = start + np.arange(train_len)
        # Deterministic bounded reservoir-style thinning.
        remaining_train = max(1, bounds["train_end"] - int(remaining_seen[0]))
        remaining_slots = max(0, FIT_SAMPLE_MAX - kept)
        keep_prob = min(1.0, remaining_slots / remaining_train)
        mask = rng.random(train_len) <= keep_prob
        if not mask.any():
            continue
        selected = train_chunk.loc[mask].copy()
        x_parts.append(normalize_features(selected))
        y_parts.append(normalize_label(selected[LABEL]))
        kept += int(mask.sum())
        if kept >= FIT_SAMPLE_MAX:
            break
    if not x_parts:
        raise RuntimeError("empty fit sample")
    x = pd.concat(x_parts, ignore_index=True)
    y = pd.concat(y_parts, ignore_index=True)
    medians = x.median(numeric_only=True).fillna(0.0)
    return x.fillna(medians), y.astype(bool), medians


def predict_split(path: Path, bounds: dict[str, Any], model: HistGradientBoostingClassifier, medians: pd.Series, split: str) -> tuple[np.ndarray, np.ndarray]:
    probs: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    seen = 0
    for chunk in pd.read_csv(path, usecols=SOURCE_USECOLS, chunksize=CHUNKSIZE):
        start = seen
        seen += len(chunk)
        split_names = split_for_offsets(start, len(chunk), bounds)
        mask = split_names == split
        if not mask.any():
            continue
        part = chunk.loc[mask].copy()
        x = normalize_features(part).fillna(medians)
        probs.append(model.predict_proba(x.to_numpy(float))[:, 1])
        labels.append(normalize_label(part[LABEL]).to_numpy(bool))
    if not probs:
        return np.array([], dtype=float), np.array([], dtype=bool)
    return np.concatenate(probs), np.concatenate(labels)


def metrics_for_threshold(probs: np.ndarray, labels: np.ndarray, threshold: float) -> dict[str, Any]:
    selected = probs >= threshold
    support = int(selected.sum())
    successes = int(labels[selected].sum()) if support else 0
    precision = float(successes / support) if support else 0.0
    coverage = float(support / len(labels)) if len(labels) else 0.0
    return {
        "rows": int(len(labels)),
        "support": support,
        "successes": successes,
        "precision": precision,
        "wilson_lcb_95": float(wilson_lcb(successes, support)),
        "coverage": coverage,
    }


def ece_10bin(probs: np.ndarray, labels: np.ndarray) -> float:
    if len(labels) == 0:
        return 0.0
    total = 0.0
    for lo in np.linspace(0.0, 0.9, 10):
        hi = lo + 0.1
        mask = (probs >= lo) & (probs < hi if hi < 1.0 else probs <= hi)
        if not mask.any():
            continue
        total += float(mask.mean()) * abs(float(probs[mask].mean()) - float(labels[mask].mean()))
    return float(total)


def select_threshold(cal_probs: np.ndarray, cal_labels: np.ndarray) -> tuple[float, dict[str, Any], list[dict[str, Any]]]:
    quantiles = np.unique(np.quantile(cal_probs, np.linspace(0.10, 0.9999, 120)))
    leaderboard: list[dict[str, Any]] = []
    for threshold in quantiles:
        metrics = metrics_for_threshold(cal_probs, cal_labels, float(threshold))
        metrics["threshold"] = float(threshold)
        metrics["passes_coverage"] = metrics["coverage"] >= ACCEPTANCE_95["coverage_min"]
        metrics["passes_support"] = metrics["support"] >= ACCEPTANCE_95["calibration_support_min"]
        metrics["passes_wilson"] = metrics["wilson_lcb_95"] >= ACCEPTANCE_95["precision_wilson_lcb_95_min"]
        leaderboard.append(metrics)
    leaderboard.sort(
        key=lambda item: (
            item["passes_wilson"],
            item["passes_coverage"],
            item["wilson_lcb_95"],
            item["precision"],
            item["coverage"],
        ),
        reverse=True,
    )
    best = leaderboard[0]
    return float(best["threshold"]), best, leaderboard[:30]


def write_report_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Mendeley Mt. Gox HGB Wash-Trading Gate",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{report['decision']['gate_result']}`",
        f"- Accepted 95 `Manipulation`: `{str(report['decision']['accepted_95']).lower()}`",
        f"- Runtime code changed: `{str(report['decision']['runtime_code_changed']).lower()}`",
        f"- Thresholds relaxed: `{str(report['decision']['thresholds_relaxed']).lower()}`",
        f"- Trade usable: `{str(report['decision']['trade_usable']).lower()}`",
        "",
        "## Source",
        "",
        "- Dataset: Mendeley Data `Detecting Crypto Wash Trades via Machine Learning`, DOI `10.17632/4hyxfwzpgg.3`",
        "- File: `gox_ml_samples.csv`",
        "- Label polarity: `wash=true` is source wash-trading positive; `wash=false` is negative.",
        "- Chronology: indirect source-script chronology; upstream `gox_ml_sample.py` sorts by `time` before writing the ML CSV, but the emitted CSV no longer carries timestamps.",
        "- Blocked predictors: label, diagnostic wash percent, timestamps, future/target/next fields.",
        "",
        "## Metrics",
        "",
        "| Split | Rows | Support | Precision | Wilson95 LCB | Coverage | ECE |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for split in ["calibration", "test"]:
        row = report["metrics"][split]
        lines.append(
            f"| {split} | {row['rows']} | {row['support']} | {row['precision']:.6f} | {row['wilson_lcb_95']:.6f} | {row['coverage']:.6f} | {row['ece_10bin']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Result",
            "",
            report["decision"]["summary"],
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    path = source_path()
    bounds = split_bounds(path)
    x_fit, y_fit, medians = collect_fit_sample(path, bounds)
    model = HistGradientBoostingClassifier(
        max_iter=180,
        learning_rate=0.08,
        max_leaf_nodes=31,
        l2_regularization=0.01,
        random_state=RNG_SEED,
        early_stopping=True,
        validation_fraction=0.12,
    )
    model.fit(x_fit.to_numpy(float), y_fit.to_numpy(bool))

    cal_probs, cal_labels = predict_split(path, bounds, model, medians, "calibration")
    test_probs, test_labels = predict_split(path, bounds, model, medians, "test")
    threshold, cal_selected, leaderboard = select_threshold(cal_probs, cal_labels)
    cal_metrics = metrics_for_threshold(cal_probs, cal_labels, threshold)
    test_metrics = metrics_for_threshold(test_probs, test_labels, threshold)
    cal_metrics["ece_10bin"] = ece_10bin(cal_probs, cal_labels)
    test_metrics["ece_10bin"] = ece_10bin(test_probs, test_labels)

    blockers: list[str] = []
    if cal_metrics["wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        blockers.append("calibration_wilson_lcb_below_95")
    if test_metrics["wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        blockers.append("test_wilson_lcb_below_95")
    if cal_metrics["support"] < ACCEPTANCE_95["calibration_support_min"]:
        blockers.append("calibration_support_below_min")
    if test_metrics["support"] < ACCEPTANCE_95["test_support_min"]:
        blockers.append("test_support_below_min")
    if cal_metrics["coverage"] < ACCEPTANCE_95["coverage_min"]:
        blockers.append("calibration_coverage_below_min")
    if test_metrics["coverage"] < ACCEPTANCE_95["coverage_min"]:
        blockers.append("test_coverage_below_min")
    if cal_metrics["ece_10bin"] > ACCEPTANCE_95["ece_max"]:
        blockers.append("calibration_ece_above_max")
    if test_metrics["ece_10bin"] > ACCEPTANCE_95["ece_max"]:
        blockers.append("test_ece_above_max")

    accepted = not blockers
    gate_result = "accepted_mendeley_gox_hgb_wash_95" if accepted else "blocked_mendeley_gox_hgb_wash_below_95"
    summary = (
        "This run accepts direct-input-gated `Manipulation` at 95% on the Mt. Gox wash-trading sample."
        if accepted
        else "The Mt. Gox HGB wash-trading model improves source coverage but remains blocked under the unchanged direct-evidence gate."
    )

    report_json = OUT_DIR / "mendeley_gox_hgb_wash_gate_report.json"
    report_md = OUT_DIR / "mendeley_gox_hgb_wash_gate_report.md"
    summary_csv = OUT_DIR / "mendeley_gox_hgb_wash_gate_summary.csv"
    assertions = CHECK_DIR / "mendeley_gox_hgb_wash_gate_assertions.out"

    report = {
        "run_id": RUN_ID,
        "source": {
            "dataset": "Mendeley Data: Detecting Crypto Wash Trades via Machine Learning",
            "doi": "10.17632/4hyxfwzpgg.3",
            "source_path": str(path),
            "raw_committed_to_repo": False,
            "chronology": "indirect_source_script_chronology",
            "chronology_note": "Upstream gox_ml_sample.py sorts by time before writing features; emitted ML CSV has no timestamp column.",
        },
        "feature_policy": {
            "features": STRICT_FEATURES,
            "blocked_predictors": BLOCKED_PREDICTORS,
            "label": LABEL,
        },
        "model": {
            "type": "sklearn.HistGradientBoostingClassifier",
            "fit_sample_rows": int(len(x_fit)),
            "fit_sample_positives": int(y_fit.sum()),
            "threshold_selected_on": "calibration_split_only",
            "selected_threshold": threshold,
            "calibration_selected": cal_selected,
        },
        "split": {
            "rows": bounds["rows"],
            "positives": bounds["positives"],
            "negatives": bounds["negatives"],
            "train_end_row_exclusive": bounds["train_end"],
            "calibration_end_row_exclusive": bounds["calibration_end"],
        },
        "metrics": {
            "calibration": cal_metrics,
            "test": test_metrics,
        },
        "leaderboard_top30": leaderboard,
        "decision": {
            "gate_result": gate_result,
            "accepted_95": accepted,
            "accepted_new_root": "Manipulation" if accepted else None,
            "blockers": blockers,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "fresh_calibration_rerun": True,
            "raw_committed_to_repo": False,
            "trade_usable": False,
            "summary": summary,
            "next_action": (
                "If accepted, run an independent direct-source confirmation before trade usability; if blocked, acquire stronger direct event/order-lifecycle evidence."
            ),
        },
        "artifacts": {
            "report_json": repo_rel(report_json),
            "report_md": repo_rel(report_md),
            "summary_csv": repo_rel(summary_csv),
            "assertions": repo_rel(assertions),
            "script": repo_rel(Path(__file__)),
        },
    }

    report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_report_md(report_md, report)
    with summary_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["split", "rows", "support", "successes", "precision", "wilson_lcb_95", "coverage", "ece_10bin"],
        )
        writer.writeheader()
        for split, metrics in [("calibration", cal_metrics), ("test", test_metrics)]:
            writer.writerow({"split": split, **metrics})
    assertions.write_text(
        "\n".join(
            [
                f"gate_result={gate_result}",
                f"accepted={accepted}",
                f"blockers={','.join(blockers) if blockers else 'none'}",
                f"threshold={threshold:.12f}",
                f"calibration_wilson_lcb_95={cal_metrics['wilson_lcb_95']:.12f}",
                f"test_wilson_lcb_95={test_metrics['wilson_lcb_95']:.12f}",
                f"calibration_support={cal_metrics['support']}",
                f"test_support={test_metrics['support']}",
                f"calibration_coverage={cal_metrics['coverage']:.12f}",
                f"test_coverage={test_metrics['coverage']:.12f}",
                "runtime_code_changed=false",
                "thresholds_relaxed=false",
                "raw_committed_to_repo=false",
            ]
        )
        + "\n"
    )
    print(json.dumps({"gate_result": gate_result, "accepted": accepted, "report": repo_rel(report_json)}, indent=2))


if __name__ == "__main__":
    main()
