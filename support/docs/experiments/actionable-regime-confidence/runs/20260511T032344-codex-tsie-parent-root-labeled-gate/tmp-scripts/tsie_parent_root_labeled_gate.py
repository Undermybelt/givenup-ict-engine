#!/usr/bin/env python3
"""External labeled parent-root gate for TSIE IDX market regime data.

Run with:
  uv run --with pyarrow --with pandas --with numpy --with scikit-learn python \
    docs/experiments/actionable-regime-confidence/runs/20260511T032344-codex-tsie-parent-root-labeled-gate/tmp-scripts/tsie_parent_root_labeled_gate.py
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import requests
from sklearn.ensemble import HistGradientBoostingClassifier


RUN_ID = "20260511T032344+0800-codex-tsie-parent-root-labeled-gate"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T032344-codex-tsie-parent-root-labeled-gate"
)
OUT_DIR = RUN_ROOT / "tsie-parent-gate"
CHECK_DIR = RUN_ROOT / "checks"
RAW_DIR = Path("/private/tmp/ict-regime-tsie-parent-root")
RAW_PATH = RAW_DIR / "tft_dataset_labeled.parquet"
SOURCE_URL = (
    "https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset/"
    "resolve/main/tft_dataset_labeled.parquet"
)
README_URL = "https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset"

ROOT_MAP = {
    0: "Bear",
    1: "Bear",
    2: "UnknownOrMixed",
    3: "Sideways",
    4: "UnknownOrMixed",
    5: "Bull",
    6: "Bull",
}
EVALUATED_ROOTS = ["Bull", "Bear", "Sideways"]
BLOCKED_COLUMNS = {
    "group_id",
    "time",
    "regime_label",
    "root_label",
    "split",
    "future_volatility",
    "target_return",
}
OBSERVED_FEATURES = [
    "log_return",
    "price_norm",
    "volume_norm",
    "volatility",
    "momentum_3",
    "momentum_10",
    "trend_return",
    "macd_norm",
    "atr_norm",
    "bb_pos",
    "is_opening",
    "is_closing",
    "is_session_1",
    "is_session_2",
    "hour",
    "day_of_week",
    "month",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
]
READ_COLUMNS = ["group_id", "time", "regime_label"] + OBSERVED_FEATURES + [
    "future_volatility",
    "target_return",
]
ACCEPTANCE_95 = {
    "precision_wilson_lcb_95_min": 0.95,
    "calibration_support_min": 120,
    "test_support_min": 60,
    "coverage_min": 0.03,
    "validation_instruments_min": 2,
    "validation_market_contexts_min": 2,
    "validation_timeframes_min": 2,
}
RNG_SEED = 17


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_raw() -> dict[str, Any]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if not RAW_PATH.exists() or RAW_PATH.stat().st_size < 100_000_000:
        tmp = RAW_PATH.with_suffix(".parquet.part")
        with requests.get(SOURCE_URL, stream=True, timeout=60) as response:
            response.raise_for_status()
            done = 0
            last = time.time()
            with tmp.open("wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    f.write(chunk)
                    done += len(chunk)
                    if time.time() - last > 15:
                        print(f"downloaded_bytes={done}", flush=True)
                        last = time.time()
        tmp.rename(RAW_PATH)
    return {
        "source_url": SOURCE_URL,
        "dataset_page": README_URL,
        "raw_path": str(RAW_PATH),
        "raw_bytes": RAW_PATH.stat().st_size,
        "raw_sha256": sha256(RAW_PATH),
        "raw_committed_to_repo": False,
    }


def wilson(success: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    phat = success / total
    denom = 1.0 + z * z / total
    center = phat + z * z / (2.0 * total)
    margin = z * math.sqrt((phat * (1.0 - phat) + z * z / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def metric(df: pd.DataFrame, mask: np.ndarray, root: str, split: str) -> dict[str, Any]:
    split_mask = df["split"].to_numpy() == split
    selected = mask & split_mask
    support = int(selected.sum())
    success = int(((df["root_label"].to_numpy() == root) & selected).sum())
    selected_rows = df.loc[selected]
    split_rows = int(split_mask.sum())
    return {
        "support": support,
        "success": success,
        "precision": success / support if support else 0.0,
        "precision_wilson_lcb_95": wilson(success, support),
        "coverage": support / split_rows if split_rows else 0.0,
        "validation_instruments": int(selected_rows["group_id"].nunique()),
        "validation_market_contexts": ["IDX"],
        "validation_timeframes": ["intraday_hourly"],
    }


def fast_precision(split_probs: np.ndarray, split_labels: np.ndarray, root: str, threshold: float) -> tuple[int, int, float, float]:
    selected = split_probs >= threshold
    support = int(selected.sum())
    success = int(((split_labels == root) & selected).sum())
    precision = success / support if support else 0.0
    return support, success, precision, wilson(success, support)


def blockers(calibration: dict[str, Any], test: dict[str, Any]) -> list[str]:
    found: list[str] = []
    if calibration["support"] < ACCEPTANCE_95["calibration_support_min"]:
        found.append("calibration_support_below_120")
    if test["support"] < ACCEPTANCE_95["test_support_min"]:
        found.append("test_support_below_60")
    if calibration["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        found.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        found.append("test_wilson95_below_0_95")
    if calibration["coverage"] < ACCEPTANCE_95["coverage_min"]:
        found.append("calibration_coverage_below_0_03")
    if test["coverage"] < ACCEPTANCE_95["coverage_min"]:
        found.append("test_coverage_below_0_03")
    if test["validation_instruments"] < ACCEPTANCE_95["validation_instruments_min"]:
        found.append("validation_instruments_below_2")
    if len(test["validation_market_contexts"]) < ACCEPTANCE_95["validation_market_contexts_min"]:
        found.append("validation_market_contexts_below_2")
    if len(test["validation_timeframes"]) < ACCEPTANCE_95["validation_timeframes_min"]:
        found.append("validation_timeframes_below_2")
    return found


def accepted(calibration: dict[str, Any], test: dict[str, Any]) -> bool:
    return not blockers(calibration, test)


def load_dataset() -> pd.DataFrame:
    table = pq.read_table(RAW_PATH, columns=READ_COLUMNS)
    df = table.to_pandas()
    df["root_label"] = df["regime_label"].map(ROOT_MAP).fillna("UnknownOrMixed")
    train_cut, cal_cut = df["time"].quantile([0.60, 0.80]).tolist()
    df["split"] = np.where(df["time"] <= train_cut, "train", np.where(df["time"] <= cal_cut, "calibration", "test"))
    return df


def build_matrix(df: pd.DataFrame) -> pd.DataFrame:
    frame = df[OBSERVED_FEATURES].copy()
    frame = frame.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return frame.astype("float32")


def fit_model(df: pd.DataFrame, x: pd.DataFrame) -> HistGradientBoostingClassifier:
    rng = np.random.default_rng(RNG_SEED)
    train_idx = np.flatnonzero(df["split"].to_numpy() == "train")
    y_train = df["root_label"].iloc[train_idx].to_numpy()
    sample_parts: list[np.ndarray] = []
    for label in sorted(set(y_train.tolist())):
        label_idx = train_idx[y_train == label]
        target_n = max(50_000, int(1_200_000 * len(label_idx) / len(train_idx)))
        target_n = min(len(label_idx), target_n)
        sample_parts.append(rng.choice(label_idx, size=target_n, replace=False))
    fit_idx = np.concatenate(sample_parts)
    clf = HistGradientBoostingClassifier(
        max_iter=160,
        learning_rate=0.08,
        max_leaf_nodes=31,
        l2_regularization=0.01,
        random_state=RNG_SEED,
        early_stopping=True,
        validation_fraction=0.12,
    )
    clf.fit(x.iloc[fit_idx], df["root_label"].iloc[fit_idx])
    clf.fit_row_count_ = int(len(fit_idx))  # type: ignore[attr-defined]
    return clf


def predict_in_chunks(clf: HistGradientBoostingClassifier, x: pd.DataFrame) -> np.ndarray:
    probs = np.zeros((len(x), len(clf.classes_)), dtype="float32")
    for start in range(0, len(x), 500_000):
        end = min(len(x), start + 500_000)
        probs[start:end] = clf.predict_proba(x.iloc[start:end])
    return probs


def select_threshold(df: pd.DataFrame, probs: np.ndarray, root: str, class_idx: int) -> dict[str, Any]:
    cal_mask = df["split"].to_numpy() == "calibration"
    cal_probs = probs[cal_mask, class_idx]
    cal_labels = df.loc[cal_mask, "root_label"].to_numpy()
    thresholds = np.unique(np.quantile(cal_probs, np.linspace(0.50, 0.999, 240)))
    candidates = []
    for threshold in thresholds:
        support, success, precision, lcb = fast_precision(cal_probs, cal_labels, root, float(threshold))
        if support < ACCEPTANCE_95["calibration_support_min"]:
            continue
        candidates.append((lcb, precision, success, support, float(threshold)))
    if not candidates:
        mask = np.zeros(len(df), dtype=bool)
        calibration = metric(df, mask, root, "calibration")
        test = metric(df, mask, root, "test")
        return {
            "root": root,
            "accepted_95": False,
            "selected_rule": "no_calibration_threshold_with_min_support",
            "selected_threshold": None,
            "calibration": calibration,
            "test": test,
            "train": metric(df, mask, root, "train"),
            "blockers": blockers(calibration, test),
        }
    candidates.sort(reverse=True, key=lambda item: item[:4])
    _, _, _, _, threshold = candidates[0]
    mask = probs[:, class_idx] >= threshold
    calibration = metric(df, mask, root, "calibration")
    test = metric(df, mask, root, "test")
    return {
        "root": root,
        "accepted_95": accepted(calibration, test),
        "selected_rule": f"p_model({root}) >= {threshold:.12g}",
        "selected_threshold": threshold,
        "calibration": calibration,
        "test": test,
        "train": metric(df, mask, root, "train"),
        "blockers": blockers(calibration, test),
    }


def write_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    records = []
    for item in rows:
        for split in ["train", "calibration", "test"]:
            metric_row = item[split]
            records.append(
                {
                    "root": item["root"],
                    "split": split,
                    "rule": item["selected_rule"],
                    "support": metric_row["support"],
                    "success": metric_row["success"],
                    "precision": metric_row["precision"],
                    "precision_wilson_lcb_95": metric_row["precision_wilson_lcb_95"],
                    "coverage": metric_row["coverage"],
                    "validation_instruments": metric_row["validation_instruments"],
                    "accepted_95": item["accepted_95"],
                    "blockers": "|".join(item["blockers"]),
                }
            )
    pd.DataFrame(records).to_csv(path, index=False)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    source = ensure_raw()
    df = load_dataset()
    x = build_matrix(df)
    clf = fit_model(df, x)
    probs = predict_in_chunks(clf, x)
    class_index = {label: idx for idx, label in enumerate(clf.classes_)}
    root_reports = [select_threshold(df, probs, root, class_index[root]) for root in EVALUATED_ROOTS]
    accepted_roots = [item["root"] for item in root_reports if item["accepted_95"]]
    split_profile = {
        split: {
            "rows": int((df["split"] == split).sum()),
            "date_min": df.loc[df["split"] == split, "time"].min().isoformat(),
            "date_max": df.loc[df["split"] == split, "time"].max().isoformat(),
            "label_counts": {k: int(v) for k, v in df.loc[df["split"] == split, "root_label"].value_counts().to_dict().items()},
        }
        for split in ["train", "calibration", "test"]
    }
    report = {
        "run_id": RUN_ID,
        "source": source,
        "dataset": {
            "rows": int(len(df)),
            "group_id_count": int(df["group_id"].nunique()),
            "source_label_mapping": ROOT_MAP,
            "label_counts": {k: int(v) for k, v in df["root_label"].value_counts().to_dict().items()},
            "split_profile": split_profile,
            "market_contexts": ["IDX"],
            "timeframes": ["intraday_hourly"],
        },
        "feature_policy": {
            "features_used": OBSERVED_FEATURES,
            "blocked_columns": sorted(BLOCKED_COLUMNS),
            "blocked_future_or_target_columns": ["future_volatility", "target_return"],
            "target_column_used_only_as_label": "regime_label",
            "candidate_regime_labels": EVALUATED_ROOTS,
        },
        "model": {
            "family": "sklearn.HistGradientBoostingClassifier",
            "classes": [str(item) for item in clf.classes_],
            "fit_row_count": int(getattr(clf, "fit_row_count_", 0)),
            "threshold_selected_on": "calibration_split",
            "test_split_held_out": True,
            "random_seed": RNG_SEED,
        },
        "acceptance_95": ACCEPTANCE_95,
        "root_reports": root_reports,
        "decision": {
            "accepted_95_roots_from_this_run": accepted_roots,
            "gate": "accepted_95_partial" if accepted_roots else "blocked_tsie_parent_root_labeled_gate_below_95",
            "active_root_accounting_after_gate": {
                "accepted_95_roots": ["Crisis"] + accepted_roots,
                "missing_95_roots": [root for root in ["Bull", "Bear", "Sideways", "Manipulation"] if root not in accepted_roots],
            },
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "raw_data_committed_to_repo": False,
            "trade_usable": False,
            "blocker": "Strict observed-feature model over external TSIE parent-mapped labels did not pass unchanged 95% held-out and context-breadth gates.",
        },
    }
    json_path = OUT_DIR / "tsie_parent_root_labeled_gate_report.json"
    md_path = OUT_DIR / "tsie_parent_root_labeled_gate_report.md"
    csv_path = OUT_DIR / "tsie_parent_root_labeled_gate_summary.csv"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_summary(csv_path, root_reports)
    lines = [
        "# TSIE Parent Root Labeled Gate",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Source",
        "",
        f"- Dataset page: `{README_URL}`",
        f"- Raw parquet cache: `{RAW_PATH}`",
        "- Raw data committed to repo: false.",
        "- Source labels mapped: `0/1 -> Bear`, `3 -> Sideways`, `5/6 -> Bull`, `2/4 -> UnknownOrMixed`.",
        "- Blocked from predictors: `future_volatility`, `target_return`, `regime_label`, and metadata columns.",
        "",
        "## Split",
        "",
        f"- Train: {split_profile['train']}",
        f"- Calibration: {split_profile['calibration']}",
        f"- Test: {split_profile['test']}",
        "",
        "## Gate Results",
        "",
    ]
    for item in root_reports:
        lines.extend(
            [
                f"### {item['root']}",
                "",
                f"- Rule: `{item['selected_rule']}`.",
                f"- Calibration Wilson95 LCB: `{item['calibration']['precision_wilson_lcb_95']:.6f}` with support {item['calibration']['support']}.",
                f"- Test Wilson95 LCB: `{item['test']['precision_wilson_lcb_95']:.6f}` with support {item['test']['support']}.",
                f"- Test coverage: `{item['test']['coverage']:.6f}`.",
                f"- Test instruments: `{item['test']['validation_instruments']}`; market contexts: `{item['test']['validation_market_contexts']}`; timeframes: `{item['test']['validation_timeframes']}`.",
                f"- Accepted 95: {item['accepted_95']}.",
                f"- Blockers: `{item['blockers']}`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision",
            "",
            f"- Accepted 95 roots from this run: `{accepted_roots}`.",
            f"- Gate: `{report['decision']['gate']}`.",
            "- Thresholds relaxed: false.",
            "- Runtime code changed: false.",
            "- Trade usable: false.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
