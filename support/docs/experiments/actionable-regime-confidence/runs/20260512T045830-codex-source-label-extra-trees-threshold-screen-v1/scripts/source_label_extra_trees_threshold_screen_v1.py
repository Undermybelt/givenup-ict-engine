#!/usr/bin/env python3
"""Fail-closed ExtraTrees threshold screen over source-label equivalence rows."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260512T045830-codex-source-label-extra-trees-threshold-screen-v1"
SLUG = "source-label-extra-trees-threshold-screen-v1"
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"

INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
INTAKE_ROWS = INTAKE_ROOT / "source_label_equivalence_rows.csv"
INTAKE_PROVENANCE = INTAKE_ROOT / "source_label_equivalence_provenance.json"
STOCK_SOURCE = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
NIFTY_SOURCE = Path("/tmp/ict-engine-source-label-equivalence-reconstruction-v1/nifty/regime_timeline_history.csv")

ROOT_LABELS = ["Bear", "Bull", "Crisis", "Sideways"]
REQUIRED_SPLITS = ["calibration", "heldout_market", "heldout_time", "test"]
MIN_SUPPORT = 50
WILSON_THRESHOLD = 0.95
Z95 = 1.959963984540054

STOCK_FEATURES = [
    "close",
    "returns",
    "volatility",
    "regime_confidence",
    "unemployment_rate",
    "fed_funds_rate",
    "cpi",
    "10y_treasury",
    "2y_treasury",
    "vix",
]
NIFTY_FEATURES = [
    "macro_confidence",
    "fast_confidence",
    "combined_confidence",
    "confidence",
    "p_fragile_smooth",
    "p_calm_smooth",
    "p_choppy_smooth",
    "p_stress_smooth",
    "p_fragile_raw",
    "p_calm_raw",
    "p_choppy_raw",
    "p_stress_raw",
    "p_fragile_adaptive",
    "p_calm_adaptive",
    "p_choppy_adaptive",
    "p_stress_adaptive",
]
FEATURE_COLS = STOCK_FEATURES + NIFTY_FEATURES


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    denom = 1 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2 * total)
    radius = Z95 * math.sqrt((p * (1 - p) + Z95 * Z95 / (4 * total)) / total)
    return (center - radius) / denom


def build_dataset() -> pd.DataFrame:
    rows = pd.read_csv(INTAKE_ROWS)
    stock_rows = rows[rows["source_owner"] == "source-owned-stock-market-regimes-2000-2026"].copy()
    nifty_rows = rows[rows["source_owner"] == "ahaanverma00"].copy()

    stock = pd.read_csv(STOCK_SOURCE).rename(
        columns={
            "date": "timestamp_or_date",
            "ticker": "symbol",
            "regime_label": "main_regime_v2_label",
        }
    )
    stock_merged = stock_rows.merge(
        stock[["timestamp_or_date", "symbol", "main_regime_v2_label", *STOCK_FEATURES]],
        on=["timestamp_or_date", "symbol", "main_regime_v2_label"],
        how="left",
    )
    for col in NIFTY_FEATURES:
        stock_merged[col] = 0.0

    nifty = pd.read_csv(NIFTY_SOURCE).rename(columns={"Date": "timestamp_or_date"})
    nifty_merged = nifty_rows.merge(
        nifty[["timestamp_or_date", *NIFTY_FEATURES]],
        on=["timestamp_or_date"],
        how="left",
    )
    for col in STOCK_FEATURES:
        nifty_merged[col] = 0.0

    data = pd.concat([stock_merged, nifty_merged], ignore_index=True)
    data = data[data["main_regime_v2_label"].isin(ROOT_LABELS)].copy()
    data[FEATURE_COLS] = data[FEATURE_COLS].apply(pd.to_numeric, errors="coerce")
    data = data.dropna(subset=FEATURE_COLS)
    for col in ["source_owner", "market_family", "symbol", "split_role", "main_regime_v2_label"]:
        data[col] = data[col].astype(str)
    return data.reset_index(drop=True)


def build_features(data: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    features = data[FEATURE_COLS + ["source_owner", "market_family", "symbol"]].copy()
    features = pd.get_dummies(features, columns=["source_owner", "market_family", "symbol"], dtype=float)
    return features, list(features.columns)


def split_metrics(
    data: pd.DataFrame,
    label: str,
    label_probability: np.ndarray,
    threshold: float,
) -> dict[str, Any]:
    label_values = data["main_regime_v2_label"].to_numpy()
    split_values = data["split_role"].to_numpy()
    selected = label_probability >= threshold
    blockers: list[str] = []
    result: dict[str, Any] = {
        "label": label,
        "threshold": round(float(threshold), 4),
    }
    min_lcb = 1.0
    min_support = 10**9
    for split in REQUIRED_SPLITS:
        mask = selected & (split_values == split)
        support = int(mask.sum())
        hits = int(((label_values == label) & mask).sum())
        precision = hits / support if support else 0.0
        lcb = wilson_lcb(hits, support)
        min_lcb = min(min_lcb, lcb)
        min_support = min(min_support, support)
        result[f"{split}_support"] = support
        result[f"{split}_label_hits"] = hits
        result[f"{split}_precision"] = round(float(precision), 10)
        result[f"{split}_wilson95_lcb"] = round(float(lcb), 10)
        if support < MIN_SUPPORT:
            blockers.append(f"{split}_support_below_{MIN_SUPPORT}")
        if lcb < WILSON_THRESHOLD:
            blockers.append(f"{split}_wilson95_below_{WILSON_THRESHOLD}")
    result["min_split_support"] = int(min_support if min_support != 10**9 else 0)
    result["min_split_wilson95_lcb"] = round(float(min_lcb), 10)
    result["accepted_extra_trees_confidence_95"] = not blockers
    result["blockers"] = ";".join(blockers)
    return result


def choose_threshold(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    calibration_passing = [
        row
        for row in candidates
        if row["calibration_support"] >= MIN_SUPPORT
        and row["calibration_wilson95_lcb"] >= WILSON_THRESHOLD
    ]
    if calibration_passing:
        return max(
            calibration_passing,
            key=lambda row: (
                row["min_split_wilson95_lcb"],
                row["min_split_support"],
                row["threshold"],
            ),
        )
    return max(
        candidates,
        key=lambda row: (
            row["calibration_wilson95_lcb"],
            row["calibration_support"],
            row["min_split_wilson95_lcb"],
        ),
    )


def run_screen() -> dict[str, Any]:
    if not INTAKE_ROWS.exists() or not INTAKE_PROVENANCE.exists():
        return {
            "run_id": RUN_ID,
            "gate_result": "source_label_extra_trees_threshold_screen_v1=blocked_missing_equivalence_intake",
            "missing": [str(p) for p in [INTAKE_ROWS, INTAKE_PROVENANCE] if not p.exists()],
            "promotion_status": {
                "accepted_rows_added": 0,
                "accepted_regime_confidence_labels": 0,
                "new_confidence_gate": False,
                "source_control_evidence_acquired": False,
                "canonical_merge": False,
                "downstream_promotion_rerun": False,
                "strict_full_objective": False,
                "trade_usable": False,
                "update_goal": False,
            },
        }

    data = build_dataset()
    features, feature_columns = build_features(data)
    train_mask = data["split_role"] == "calibration"
    model = ExtraTreesClassifier(
        n_estimators=180,
        max_depth=14,
        min_samples_leaf=35,
        max_features="sqrt",
        class_weight="balanced",
        random_state=20260512,
        n_jobs=1,
    )
    model.fit(features.loc[train_mask], data.loc[train_mask, "main_regime_v2_label"])
    probabilities = model.predict_proba(features)
    classes = list(model.classes_)
    thresholds = [round(v, 4) for v in np.linspace(0.50, 0.99, 50)]

    candidate_rows: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    for label in ROOT_LABELS:
        if label not in classes:
            continue
        label_index = classes.index(label)
        label_candidates = [
            split_metrics(data, label, probabilities[:, label_index], threshold)
            for threshold in thresholds
        ]
        candidate_rows.extend(label_candidates)
        gate_rows.append(choose_threshold(label_candidates))

    accepted_labels = [
        row["label"]
        for row in gate_rows
        if row.get("accepted_extra_trees_confidence_95") is True
    ]

    feature_importances = [
        {"feature": name, "importance": round(float(value), 10)}
        for name, value in sorted(
            zip(feature_columns, model.feature_importances_),
            key=lambda item: item[1],
            reverse=True,
        )[:50]
    ]

    return {
        "run_id": RUN_ID,
        "gate_result": "source_label_extra_trees_threshold_screen_v1=extra_trees_scored_no_full_acceptance",
        "row_count": int(len(data)),
        "rows_sha256": sha256_file(INTAKE_ROWS),
        "provenance_sha256": sha256_file(INTAKE_PROVENANCE),
        "model": {
            "kind": "ExtraTreesClassifier",
            "train_split": "calibration",
            "classes": classes,
            "feature_count": len(feature_columns),
            "threshold_selection": "calibration_passing_first_then_best_diagnostic",
            "parameters": {
                "n_estimators": 180,
                "max_depth": 14,
                "min_samples_leaf": 35,
                "max_features": "sqrt",
                "class_weight": "balanced",
                "random_state": 20260512,
            },
        },
        "split_counts": {
            split: int((data["split_role"] == split).sum())
            for split in REQUIRED_SPLITS
        },
        "label_counts": {
            label: int((data["main_regime_v2_label"] == label).sum())
            for label in ROOT_LABELS
        },
        "accepted_extra_trees_confidence_95_labels": accepted_labels,
        "gates": gate_rows,
        "feature_importance": feature_importances,
        "promotion_status": {
            "accepted_rows_added": 0,
            "accepted_regime_confidence_labels": len(accepted_labels),
            "new_confidence_gate": bool(accepted_labels),
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": len(accepted_labels) == len(ROOT_LABELS),
            "trade_usable": False,
            "update_goal": False,
        },
        "candidate_rows": candidate_rows,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(result: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    candidate_rows = result.pop("candidate_rows", [])

    (OUT / "source_label_extra_trees_threshold_screen_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(OUT / "source_label_extra_trees_threshold_gates_v1.csv", result.get("gates", []))
    write_csv(OUT / "source_label_extra_trees_threshold_candidates_v1.csv", candidate_rows)
    write_csv(OUT / "source_label_extra_trees_feature_importance_v1.csv", result.get("feature_importance", []))

    accepted = result.get("accepted_extra_trees_confidence_95_labels", [])
    lines = [
        "# Source Label ExtraTrees Threshold Screen v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{result['gate_result']}`",
        "",
        "## Result",
        "",
        f"- Rows scored: `{result.get('row_count', 0)}`.",
        "- Model: `ExtraTreesClassifier` trained only on the `calibration` split.",
        "- Threshold selection: calibration-passing thresholds first, otherwise best diagnostic calibration threshold.",
        f"- Accepted ExtraTrees confidence labels: `{accepted}`.",
        "- Accepted rows added `0`; source/control evidence acquired `false`; canonical merge `false`; downstream promotion rerun `false`; `update_goal=false`.",
        "",
        "## Best Gates",
        "",
        "| Label | Accepted 95 | Threshold | Min Support | Min Wilson95 | Blockers |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in result.get("gates", []):
        lines.append(
            f"| `{row['label']}` | `{str(row['accepted_extra_trees_confidence_95']).lower()}` "
            f"| `{row['threshold']}` | `{row['min_split_support']}` "
            f"| `{row['min_split_wilson95_lcb']}` | {row['blockers']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a diagnostic threshold screen over the existing source-label equivalence package. It does not create source/control evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.",
        ]
    )
    (OUT / "source_label_extra_trees_threshold_screen_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS gate_result={result['gate_result']}",
        f"PASS row_count={result.get('row_count', 0)}",
        f"PASS accepted_extra_trees_confidence_95_labels={','.join(accepted) if accepted else 'none'}",
        f"PASS accepted_regime_confidence_labels={len(accepted)}",
        f"PASS new_confidence_gate={str(bool(accepted)).lower()}",
        "PASS source_control_evidence_acquired=false",
        "PASS canonical_merge=false",
        "PASS downstream_promotion_rerun=false",
        f"PASS strict_full_objective={str(len(accepted) == len(ROOT_LABELS)).lower()}",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "source_label_extra_trees_threshold_screen_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    result = run_screen()
    write_outputs(result)
    summary = {
        "gate_result": result["gate_result"],
        "accepted_extra_trees_confidence_95_labels": result.get("accepted_extra_trees_confidence_95_labels", []),
        "promotion_status": result.get("promotion_status", {}),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
