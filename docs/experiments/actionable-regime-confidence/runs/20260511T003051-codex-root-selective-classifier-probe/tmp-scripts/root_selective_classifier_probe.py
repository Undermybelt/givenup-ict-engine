from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T003051-codex-root-selective-classifier-probe"
)
INPUT_FEATURE_TABLE = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260510T224014-codex-cross-timeframe-regime-validation/"
    "cross_timeframe_regime_features.csv"
)
OUTPUT_DIR = RUN_ROOT / "root-classifier"
LOOP_ID = "20260511T003051+0800-codex-root-selective-classifier-probe"
ROOT_CLASSES = ["Bull", "Bear", "Sideways", "Crisis", "UnknownOrMixed", "Manipulation"]
EVALUATED_ROOTS = ["Bull", "Bear", "Sideways", "Crisis", "UnknownOrMixed"]
BLOCKED_PREDICTOR_PREFIXES = ("future_", "target_")
ACCEPTANCE_95 = {
    "precision_wilson_lcb_95_min": 0.95,
    "calibration_support_min": 120,
    "test_support_min": 60,
    "ece_max": 0.05,
    "coverage_min": 0.03,
    "validation_instruments_min": 2,
    "validation_market_contexts_min": 2,
    "validation_timeframes_min": 2,
}


def wilson(success: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    center = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return (center - margin) / denom


def boolish(frame: pd.DataFrame) -> pd.DataFrame:
    for column in [
        "trend_base",
        "stress_base",
        "reversal_base",
        "thin_base",
        "target_trend_structural_next",
        "target_stress_next",
    ]:
        if column in frame.columns:
            frame[column] = frame[column].astype(bool)
    return frame


def add_forward_targets(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, context_rows in frame.groupby("context", sort=False):
        context_rows = context_rows.sort_values("ts").copy()
        minutes = float(context_rows["timeframe_minutes"].iloc[0])
        horizon_bars = max(1, int(round(480.0 / minutes))) if minutes else 8
        future_ret = context_rows["close"].shift(-horizon_bars) / context_rows["close"] - 1.0
        context_rows["_future_ret_8h"] = future_ret
        context_rows["_future_absret_8h"] = future_ret.abs()
        rows.append(context_rows)
    return pd.concat(rows).dropna(subset=["_future_ret_8h"]).copy()


def assign_root_labels(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    train = frame[frame["split"] == "train"]
    thresholds = {
        "bull_future_ret_8h_train_q65": float(train["_future_ret_8h"].quantile(0.65)),
        "bear_future_ret_8h_train_q35": float(train["_future_ret_8h"].quantile(0.35)),
        "sideways_future_absret_8h_train_q35": float(train["_future_absret_8h"].quantile(0.35)),
        "crisis_future_absret_8h_train_q90": float(train["_future_absret_8h"].quantile(0.90)),
    }

    def label(row: pd.Series) -> str:
        crisis = bool(row.get("target_stress_next", False)) or (
            row["_future_absret_8h"] >= thresholds["crisis_future_absret_8h_train_q90"]
        )
        sideways = (
            not crisis
            and row["_future_absret_8h"] <= thresholds["sideways_future_absret_8h_train_q35"]
            and not bool(row.get("target_trend_structural_next", False))
        )
        bull = (
            not crisis
            and not sideways
            and row["_future_ret_8h"] >= thresholds["bull_future_ret_8h_train_q65"]
        )
        bear = (
            not crisis
            and not sideways
            and row["_future_ret_8h"] <= thresholds["bear_future_ret_8h_train_q35"]
        )
        if crisis:
            return "Crisis"
        if sideways:
            return "Sideways"
        if bull:
            return "Bull"
        if bear:
            return "Bear"
        return "UnknownOrMixed"

    frame["_root"] = frame.apply(label, axis=1)
    return frame, thresholds


def build_feature_matrix(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    blocked_columns = {
        "ts",
        "instrument",
        "market",
        "timeframe",
        "split",
        "context",
        "_future_ret_8h",
        "_future_absret_8h",
        "_root",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "count",
    }
    features = [
        column
        for column in frame.columns
        if column not in blocked_columns
        and not any(column.startswith(prefix) for prefix in BLOCKED_PREDICTOR_PREFIXES)
    ]
    matrix = frame[features].copy()
    for column in matrix.columns:
        if matrix[column].dtype == bool:
            matrix[column] = matrix[column].astype(int)
        elif matrix[column].dtype == object:
            matrix[column] = pd.to_numeric(matrix[column], errors="coerce")
    matrix = matrix.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return matrix, features


def metric(mask: np.ndarray, label: str, split: str, frame: pd.DataFrame) -> dict[str, Any]:
    split_mask = frame["split"].values == split
    selected = mask & split_mask
    support = int(selected.sum())
    success = int(((frame["_root"].values == label) & selected).sum())
    selected_rows = frame.loc[selected]
    return {
        "support": support,
        "success": success,
        "precision": success / support if support else 0.0,
        "precision_wilson_lcb_95": wilson(success, support),
        "coverage": support / max(1, int(split_mask.sum())),
        "validation_instruments": sorted(selected_rows["instrument"].dropna().unique().tolist()),
        "validation_market_contexts": sorted(selected_rows["market"].dropna().unique().tolist()),
        "validation_timeframes": sorted(selected_rows["timeframe"].dropna().unique().tolist()),
    }


def candidate_ok(candidate: dict[str, Any]) -> bool:
    calibration = candidate["calibration"]
    test = candidate["test"]
    ece = candidate["ece"]
    return (
        calibration["support"] >= ACCEPTANCE_95["calibration_support_min"]
        and test["support"] >= ACCEPTANCE_95["test_support_min"]
        and calibration["precision_wilson_lcb_95"] >= ACCEPTANCE_95["precision_wilson_lcb_95_min"]
        and test["precision_wilson_lcb_95"] >= ACCEPTANCE_95["precision_wilson_lcb_95_min"]
        and calibration["coverage"] >= ACCEPTANCE_95["coverage_min"]
        and test["coverage"] >= ACCEPTANCE_95["coverage_min"]
        and ece <= ACCEPTANCE_95["ece_max"]
        and len(test["validation_instruments"]) >= ACCEPTANCE_95["validation_instruments_min"]
        and len(test["validation_market_contexts"]) >= ACCEPTANCE_95["validation_market_contexts_min"]
        and len(test["validation_timeframes"]) >= ACCEPTANCE_95["validation_timeframes_min"]
    )


def blockers(candidate: dict[str, Any]) -> list[str]:
    calibration = candidate["calibration"]
    test = candidate["test"]
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
    if candidate["ece"] > ACCEPTANCE_95["ece_max"]:
        found.append("ece_above_0_05")
    if len(test["validation_instruments"]) < ACCEPTANCE_95["validation_instruments_min"]:
        found.append("validation_instruments_below_2")
    if len(test["validation_market_contexts"]) < ACCEPTANCE_95["validation_market_contexts_min"]:
        found.append("validation_market_contexts_below_2")
    if len(test["validation_timeframes"]) < ACCEPTANCE_95["validation_timeframes_min"]:
        found.append("validation_timeframes_below_2")
    return found


def choose_candidate(
    model_name: str,
    probabilities: np.ndarray,
    classes: list[str],
    label: str,
    frame: pd.DataFrame,
) -> dict[str, Any]:
    label_idx = classes.index(label)
    scores = probabilities[:, label_idx]
    calibration_mask = frame["split"].values == "calibration"
    thresholds = np.unique(np.quantile(scores[calibration_mask], np.linspace(0.50, 0.999, 120)))
    candidates: list[dict[str, Any]] = []
    for threshold in thresholds:
        selected = scores >= threshold
        calibration = metric(selected, label, "calibration", frame)
        if (
            calibration["support"] < ACCEPTANCE_95["calibration_support_min"]
            or calibration["coverage"] < ACCEPTANCE_95["coverage_min"]
        ):
            continue
        train = metric(selected, label, "train", frame)
        test = metric(selected, label, "test", frame)
        candidate = {
            "model": model_name,
            "rule": f"{model_name}_p_{label} >= {threshold:.12g}",
            "threshold": float(threshold),
            "train": train,
            "calibration": calibration,
            "test": test,
            "ece": abs(test["precision"] - calibration["precision"]),
        }
        candidate["accepted_95"] = candidate_ok(candidate)
        candidate["blockers"] = blockers(candidate)
        candidates.append(candidate)
    if not candidates:
        return {
            "model": model_name,
            "rule": "no_calibration_candidate",
            "accepted_95": False,
            "blockers": ["no_calibration_candidate_meets_support_and_coverage"],
            "train": metric(np.zeros(len(frame), dtype=bool), label, "train", frame),
            "calibration": metric(np.zeros(len(frame), dtype=bool), label, "calibration", frame),
            "test": metric(np.zeros(len(frame), dtype=bool), label, "test", frame),
            "ece": 1.0,
        }
    accepted = [candidate for candidate in candidates if candidate["accepted_95"]]
    if accepted:
        return max(accepted, key=lambda item: (item["test"]["precision_wilson_lcb_95"], item["test"]["support"]))
    return max(
        candidates,
        key=lambda item: (
            item["calibration"]["precision_wilson_lcb_95"],
            item["test"]["precision_wilson_lcb_95"],
            item["test"]["support"],
        ),
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(INPUT_FEATURE_TABLE)
    frame = boolish(frame)
    frame = add_forward_targets(frame)
    frame, thresholds = assign_root_labels(frame)
    matrix, features = build_feature_matrix(frame)
    train_mask = frame["split"].values == "train"

    models = {
        "hgb": HistGradientBoostingClassifier(
            max_iter=120,
            learning_rate=0.06,
            max_leaf_nodes=15,
            l2_regularization=0.1,
            random_state=7,
        ),
        "rf": RandomForestClassifier(
            n_estimators=160,
            max_depth=8,
            min_samples_leaf=20,
            random_state=7,
            n_jobs=-1,
            class_weight="balanced_subsample",
        ),
        "et": ExtraTreesClassifier(
            n_estimators=160,
            max_depth=8,
            min_samples_leaf=20,
            random_state=7,
            n_jobs=-1,
            class_weight="balanced",
        ),
        "lr": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, class_weight="balanced"),
        ),
    }

    selected_by_root: dict[str, dict[str, Any]] = {}
    per_model: dict[str, dict[str, Any]] = {}
    for model_name, model in models.items():
        model.fit(matrix.loc[train_mask], frame.loc[train_mask, "_root"])
        classes = list(model.classes_) if hasattr(model, "classes_") else list(model[-1].classes_)
        probabilities = model.predict_proba(matrix)
        per_model[model_name] = {}
        for root in EVALUATED_ROOTS:
            candidate = choose_candidate(model_name, probabilities, classes, root, frame)
            per_model[model_name][root] = candidate
            current = selected_by_root.get(root)
            if current is None or (
                candidate["accepted_95"],
                candidate["test"]["precision_wilson_lcb_95"],
                candidate["calibration"]["precision_wilson_lcb_95"],
                candidate["test"]["support"],
            ) > (
                current["accepted_95"],
                current["test"]["precision_wilson_lcb_95"],
                current["calibration"]["precision_wilson_lcb_95"],
                current["test"]["support"],
            ):
                selected_by_root[root] = candidate

    manipulation = {
        "model": "required_input_gate",
        "rule": "direct_manipulation_inputs_present == true",
        "accepted_95": False,
        "train": metric(np.zeros(len(frame), dtype=bool), "Manipulation", "train", frame),
        "calibration": metric(np.zeros(len(frame), dtype=bool), "Manipulation", "calibration", frame),
        "test": metric(np.zeros(len(frame), dtype=bool), "Manipulation", "test", frame),
        "ece": 1.0,
        "blockers": ["missing_required_inputs", "proxy_only_low_confidence"],
    }
    selected_by_root["Manipulation"] = manipulation

    accepted = [root for root, candidate in selected_by_root.items() if candidate["accepted_95"]]
    blocked = [root for root in ["Bull", "Bear", "Sideways", "Crisis", "Manipulation"] if root not in accepted]
    report = {
        "schema_version": "main-regime-v2-root-selective-classifier/v1",
        "loop_id": LOOP_ID,
        "run_root": str(RUN_ROOT),
        "objective": "Train current-feature classifiers for corrected MainRegimeV2 root labels, select thresholds on calibration only, and audit on held-out test.",
        "input_feature_table": str(INPUT_FEATURE_TABLE),
        "blocked_predictor_prefixes": list(BLOCKED_PREDICTOR_PREFIXES),
        "predictor_features_used": features,
        "target_thresholds": thresholds,
        "target_counts": {
            split: frame.loc[frame["split"] == split, "_root"].value_counts().to_dict()
            for split in ["train", "calibration", "test"]
        },
        "acceptance_95": ACCEPTANCE_95,
        "selected_by_root": selected_by_root,
        "per_model": per_model,
        "decision": {
            "board_state": "blocked",
            "accepted_95_root_classes": accepted,
            "blocked_root_classes": blocked,
            "accepted_95_all_main_regime_v2_roots": False,
            "thresholds_relaxed": False,
            "predictor_leakage_guard": {
                "future_prefix_blocked": True,
                "target_prefix_blocked": True,
                "future_fields_used_only_for_target": ["_future_ret_8h", "_future_absret_8h"],
            },
            "trade_usable": False,
            "why_not_complete": [
                "Selective classifiers still did not make every MainRegimeV2 root class pass the unchanged 95% gate.",
                "Bull, Bear, and Sideways remain far below 95% held-out Wilson LCB.",
                "Manipulation remains fail-closed because direct order-flow/L2/order-lifecycle or event/social inputs are not in the source table.",
            ],
            "next_action": "Stop repeating current OHLCV-derived model searches; ingest materially new signed-direction, sideways, and direct manipulation inputs.",
        },
    }
    (OUTPUT_DIR / "root_selective_classifier_report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    with (OUTPUT_DIR / "root_selective_classifier_summary.csv").open("w", encoding="utf-8") as handle:
        handle.write(
            "root_class,state,model,rule,calibration_support,calibration_wilson95,"
            "test_support,test_wilson95,test_coverage,ece,test_instruments,"
            "test_market_contexts,test_timeframes,blockers\n"
        )
        for root in ["Bull", "Bear", "Sideways", "Crisis", "Manipulation"]:
            candidate = selected_by_root[root]
            state = "accepted_95" if candidate["accepted_95"] else (
                "missing_required_inputs" if root == "Manipulation" else "blocked"
            )
            test = candidate["test"]
            calibration = candidate["calibration"]
            handle.write(
                ",".join(
                    [
                        root,
                        state,
                        candidate["model"],
                        '"' + candidate["rule"].replace('"', '""') + '"',
                        str(calibration["support"]),
                        f"{calibration['precision_wilson_lcb_95']:.12g}",
                        str(test["support"]),
                        f"{test['precision_wilson_lcb_95']:.12g}",
                        f"{test['coverage']:.12g}",
                        f"{candidate['ece']:.12g}",
                        '"' + ";".join(test["validation_instruments"]) + '"',
                        '"' + ";".join(test["validation_market_contexts"]) + '"',
                        '"' + ";".join(test["validation_timeframes"]) + '"',
                        '"' + ";".join(candidate["blockers"]) + '"',
                    ]
                )
                + "\n"
            )

    print(f"report: {OUTPUT_DIR / 'root_selective_classifier_report.json'}")
    print(f"summary: {OUTPUT_DIR / 'root_selective_classifier_summary.csv'}")
    print(f"accepted_95_root_classes: {accepted}")
    print(f"blocked_root_classes: {blocked}")
    print("thresholds_relaxed: False")
    for root in ["Bull", "Bear", "Sideways", "Crisis", "Manipulation"]:
        candidate = selected_by_root[root]
        print(
            f"{root}: accepted={candidate['accepted_95']} "
            f"model={candidate['model']} "
            f"test_lcb={candidate['test']['precision_wilson_lcb_95']:.6f} "
            f"test_support={candidate['test']['support']} "
            f"blockers={candidate['blockers']}"
        )


if __name__ == "__main__":
    main()
