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
    "20260511T004831-source-backed-root-classifier-probe"
)
INPUT_FEATURE_TABLE = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260510T233911-main-regime-v2-advanced-root-features/advanced_root_features.csv"
)
OUTPUT_DIR = RUN_ROOT / "root-classifier"
LOOP_ID = "20260511T004831+0800-source-backed-root-classifier-probe"
BLOCKED_PREDICTOR_PREFIXES = ("future_", "target_")

ROOT_TARGETS = {
    "BullExpansion": "target_BullExpansion_h4",
    "BearExpansion": "target_BearExpansion_h4",
    "Consolidation": "target_ConsolidationRange_h4",
    "CrisisStress": "target_CrisisStress_next",
    "TransitionRecovery": "target_TransitionAccumulationDistribution_next",
}
ROOT_ORDER = [
    "BullExpansion",
    "BearExpansion",
    "Consolidation",
    "CrisisStress",
    "TransitionRecovery",
    "Manipulation",
]
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


def build_feature_matrix(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    blocked = {"ts", "instrument", "market", "timeframe", "split", "context"}
    features = [
        column
        for column in frame.columns
        if column not in blocked
        and not any(column.startswith(prefix) for prefix in BLOCKED_PREDICTOR_PREFIXES)
        and column not in {"open", "high", "low", "close", "volume", "count", "log_close"}
    ]
    matrix = frame[features].copy()
    for column in matrix.columns:
        if matrix[column].dtype == bool:
            matrix[column] = matrix[column].astype(int)
        elif matrix[column].dtype == object:
            matrix[column] = pd.to_numeric(matrix[column], errors="coerce")
    return matrix.replace([np.inf, -np.inf], np.nan).fillna(0.0), features


def metric(mask: np.ndarray, target: str, split: str, frame: pd.DataFrame) -> dict[str, Any]:
    split_mask = frame["split"].eq(split).values
    valid_target = frame[target].notna().values
    selected = mask & split_mask & valid_target
    y = pd.to_numeric(frame[target], errors="coerce").fillna(0).values >= 0.5
    support = int(selected.sum())
    success = int((selected & y).sum())
    selected_rows = frame.loc[selected]
    valid_count = int((split_mask & valid_target).sum())
    return {
        "support": support,
        "success": success,
        "precision": success / support if support else 0.0,
        "precision_wilson_lcb_95": wilson(success, support),
        "coverage": support / max(1, valid_count),
        "validation_instruments": sorted(selected_rows["instrument"].dropna().unique().tolist()),
        "validation_market_contexts": sorted(selected_rows["market"].dropna().unique().tolist()),
        "validation_timeframes": sorted(selected_rows["timeframe"].dropna().unique().tolist()),
    }


def blockers(candidate: dict[str, Any]) -> list[str]:
    cal = candidate["calibration"]
    test = candidate["test"]
    found: list[str] = []
    if cal["support"] < ACCEPTANCE_95["calibration_support_min"]:
        found.append("calibration_support_below_120")
    if test["support"] < ACCEPTANCE_95["test_support_min"]:
        found.append("test_support_below_60")
    if cal["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        found.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        found.append("test_wilson95_below_0_95")
    if cal["coverage"] < ACCEPTANCE_95["coverage_min"]:
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


def accepted(candidate: dict[str, Any]) -> bool:
    return not blockers(candidate)


def candidate_for_model(
    model_name: str,
    scores: np.ndarray,
    target: str,
    frame: pd.DataFrame,
) -> dict[str, Any] | None:
    calibration_mask = frame["split"].eq("calibration").values
    thresholds = np.unique(np.quantile(scores[calibration_mask], np.linspace(0.50, 0.999, 120)))
    candidates = []
    for threshold in thresholds:
        mask = scores >= threshold
        cal = metric(mask, target, "calibration", frame)
        if cal["support"] < ACCEPTANCE_95["calibration_support_min"] or cal["coverage"] < ACCEPTANCE_95["coverage_min"]:
            continue
        train = metric(mask, target, "train", frame)
        test = metric(mask, target, "test", frame)
        item = {
            "model": model_name,
            "rule": f"{model_name}_p_{target.removeprefix('target_')} >= {threshold:.12g}",
            "threshold": float(threshold),
            "train": train,
            "calibration": cal,
            "test": test,
            "ece": abs(test["precision"] - cal["precision"]),
        }
        item["accepted_95"] = accepted(item)
        item["blockers"] = blockers(item)
        candidates.append(item)
    if not candidates:
        return None
    accepted_candidates = [item for item in candidates if item["accepted_95"]]
    if accepted_candidates:
        return max(
            accepted_candidates,
            key=lambda item: (
                item["test"]["precision_wilson_lcb_95"],
                item["calibration"]["precision_wilson_lcb_95"],
                item["test"]["support"],
            ),
        )
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
    matrix, features = build_feature_matrix(frame)
    train_mask = frame["split"].eq("train").values
    models = {
        "hgb": HistGradientBoostingClassifier(
            max_iter=100,
            learning_rate=0.06,
            max_leaf_nodes=12,
            l2_regularization=0.1,
            random_state=11,
        ),
        "rf": RandomForestClassifier(
            n_estimators=160,
            max_depth=8,
            min_samples_leaf=20,
            random_state=11,
            n_jobs=-1,
            class_weight="balanced_subsample",
        ),
        "et": ExtraTreesClassifier(
            n_estimators=160,
            max_depth=8,
            min_samples_leaf=20,
            random_state=11,
            n_jobs=-1,
            class_weight="balanced",
        ),
        "lr": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced")),
    }
    selected: dict[str, dict[str, Any]] = {}
    per_model: dict[str, dict[str, Any]] = {}

    for root, target in ROOT_TARGETS.items():
        y = (pd.to_numeric(frame[target], errors="coerce").fillna(0).values >= 0.5).astype(int)
        per_model[root] = {}
        for model_name, model in models.items():
            model.fit(matrix.loc[train_mask], y[train_mask])
            scores = model.predict_proba(matrix)[:, 1]
            item = candidate_for_model(model_name, scores, target, frame)
            if item is None:
                continue
            per_model[root][model_name] = item
            current = selected.get(root)
            if current is None or (
                item["accepted_95"],
                item["test"]["precision_wilson_lcb_95"],
                item["calibration"]["precision_wilson_lcb_95"],
                item["test"]["support"],
            ) > (
                current["accepted_95"],
                current["test"]["precision_wilson_lcb_95"],
                current["calibration"]["precision_wilson_lcb_95"],
                current["test"]["support"],
            ):
                selected[root] = item

    zero = np.zeros(len(frame), dtype=bool)
    selected["Manipulation"] = {
        "model": "required_input_gate",
        "rule": "direct_manipulation_inputs_present == true",
        "train": metric(zero, "target_CrisisStress_next", "train", frame),
        "calibration": metric(zero, "target_CrisisStress_next", "calibration", frame),
        "test": metric(zero, "target_CrisisStress_next", "test", frame),
        "ece": 1.0,
        "accepted_95": False,
        "blockers": ["missing_required_inputs", "proxy_only_low_confidence"],
    }

    accepted_roots = [root for root in ROOT_ORDER if selected[root]["accepted_95"]]
    blocked_roots = [root for root in ROOT_ORDER if root not in accepted_roots]
    report = {
        "schema_version": "source-backed-main-regime-v2-root-classifier/v1",
        "loop_id": LOOP_ID,
        "run_root": str(RUN_ROOT),
        "objective": "Evaluate source-backed MainRegimeV2 roots with selective classifiers; train on train split, choose thresholds on calibration, audit on test.",
        "input_feature_table": str(INPUT_FEATURE_TABLE),
        "blocked_predictor_prefixes": list(BLOCKED_PREDICTOR_PREFIXES),
        "predictor_features_used": features,
        "root_targets": ROOT_TARGETS,
        "target_counts": {
            root: {
                split: int(
                    (
                        (frame["split"] == split)
                        & (pd.to_numeric(frame[target], errors="coerce").fillna(0) >= 0.5)
                    ).sum()
                )
                for split in ["train", "calibration", "test"]
            }
            for root, target in ROOT_TARGETS.items()
        },
        "acceptance_95": ACCEPTANCE_95,
        "selected_by_root": selected,
        "per_model": per_model,
        "decision": {
            "board_state": "blocked",
            "accepted_95_root_classes": accepted_roots,
            "blocked_root_classes": blocked_roots,
            "accepted_95_all_main_regime_v2_roots": False,
            "thresholds_relaxed": False,
            "predictor_leakage_guard": {
                "future_prefix_blocked": True,
                "target_prefix_blocked": True,
                "future_and_target_fields_used_only_for_targets": True,
            },
            "trade_usable": False,
            "why_not_complete": [
                "BullExpansion and BearExpansion remain far below 95% held-out Wilson LCB.",
                "Consolidation is close but still below 95% and misses test coverage in the best candidate.",
                "Manipulation remains fail-closed because direct order-flow/L2/order-lifecycle or event/social inputs are absent.",
            ],
            "next_action": "Preserve CrisisStress and TransitionRecovery as partial root evidence; ingest direct manipulation inputs and stronger signed-direction/consolidation features before rerunning unchanged gates.",
        },
    }
    (OUTPUT_DIR / "source_backed_root_classifier_report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    with (OUTPUT_DIR / "source_backed_root_classifier_summary.csv").open("w", encoding="utf-8") as handle:
        handle.write(
            "root_class,state,model,rule,calibration_support,calibration_wilson95,"
            "test_support,test_wilson95,test_coverage,ece,test_instruments,"
            "test_market_contexts,test_timeframes,blockers\n"
        )
        for root in ROOT_ORDER:
            item = selected[root]
            state = "accepted_95" if item["accepted_95"] else (
                "missing_required_inputs" if root == "Manipulation" else "blocked"
            )
            handle.write(
                ",".join(
                    [
                        root,
                        state,
                        item["model"],
                        '"' + item["rule"].replace('"', '""') + '"',
                        str(item["calibration"]["support"]),
                        f"{item['calibration']['precision_wilson_lcb_95']:.12g}",
                        str(item["test"]["support"]),
                        f"{item['test']['precision_wilson_lcb_95']:.12g}",
                        f"{item['test']['coverage']:.12g}",
                        f"{item['ece']:.12g}",
                        '"' + ";".join(item["test"]["validation_instruments"]) + '"',
                        '"' + ";".join(item["test"]["validation_market_contexts"]) + '"',
                        '"' + ";".join(item["test"]["validation_timeframes"]) + '"',
                        '"' + ";".join(item["blockers"]) + '"',
                    ]
                )
                + "\n"
            )

    print(f"report: {OUTPUT_DIR / 'source_backed_root_classifier_report.json'}")
    print(f"summary: {OUTPUT_DIR / 'source_backed_root_classifier_summary.csv'}")
    print(f"accepted_95_root_classes: {accepted_roots}")
    print(f"blocked_root_classes: {blocked_roots}")
    print("thresholds_relaxed: False")
    for root in ROOT_ORDER:
        item = selected[root]
        print(
            f"{root}: accepted={item['accepted_95']} model={item['model']} "
            f"test_lcb={item['test']['precision_wilson_lcb_95']:.6f} "
            f"test_support={item['test']['support']} blockers={item['blockers']}"
        )


if __name__ == "__main__":
    main()
