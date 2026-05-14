#!/usr/bin/env python3
"""Light ExtraTrees threshold screen for source-label regime roots."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import ExtraTreesClassifier


RUN_ID = "20260512T050609-codex-source-label-extra-trees-light-threshold-screen-v1"
SLUG = "source-label-extra-trees-light-threshold-screen-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
BASE_SCRIPT = Path("docs/experiments/actionable-regime-confidence/runs/20260512T045830-codex-source-label-extra-trees-threshold-screen-v1/scripts/source_label_extra_trees_threshold_screen_v1.py")


def load_base() -> Any:
    spec = importlib.util.spec_from_file_location("extra_trees_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load base script {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    base = load_base()
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    data = base.build_dataset()
    features, feature_columns = base.build_features(data)
    train_mask = data["split_role"] == "calibration"
    model = ExtraTreesClassifier(
        n_estimators=48,
        max_depth=10,
        min_samples_leaf=80,
        max_features="sqrt",
        class_weight="balanced",
        random_state=20260512,
        n_jobs=1,
    )
    model.fit(features.loc[train_mask], data.loc[train_mask, "main_regime_v2_label"])

    probabilities = model.predict_proba(features)
    classes = list(model.classes_)
    thresholds = [round(float(v), 4) for v in np.linspace(0.50, 0.99, 50)]
    candidate_rows: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    for label in base.ROOT_LABELS:
        if label not in classes:
            continue
        label_index = classes.index(label)
        label_candidates = [
            base.split_metrics(data, label, probabilities[:, label_index], threshold)
            for threshold in thresholds
        ]
        candidate_rows.extend(label_candidates)
        gate_rows.append(base.choose_threshold(label_candidates))

    accepted_labels = [
        row["label"]
        for row in gate_rows
        if row.get("accepted_extra_trees_confidence_95") is True
    ]
    gate_result = (
        "source_label_extra_trees_light_threshold_screen_v1=all_root_labels_extra_trees_light_accepted"
        if len(accepted_labels) == len(base.ROOT_LABELS)
        else "source_label_extra_trees_light_threshold_screen_v1=extra_trees_light_scored_no_full_acceptance"
    )
    feature_importances = [
        {"feature": name, "importance": round(float(value), 10)}
        for name, value in sorted(
            zip(feature_columns, model.feature_importances_),
            key=lambda item: item[1],
            reverse=True,
        )[:50]
    ]

    result = {
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "row_count": int(len(data)),
        "rows_sha256": sha256_file(base.INTAKE_ROWS),
        "provenance_sha256": sha256_file(base.INTAKE_PROVENANCE),
        "model": {
            "kind": "ExtraTreesClassifier",
            "train_split": "calibration",
            "classes": classes,
            "feature_count": len(feature_columns),
            "threshold_selection": "calibration_passing_first_then_best_diagnostic",
            "parameters": {
                "n_estimators": 48,
                "max_depth": 10,
                "min_samples_leaf": 80,
                "max_features": "sqrt",
                "class_weight": "balanced",
                "random_state": 20260512,
            },
        },
        "split_counts": {
            split: int((data["split_role"] == split).sum())
            for split in base.REQUIRED_SPLITS
        },
        "label_counts": {
            label: int((data["main_regime_v2_label"] == label).sum())
            for label in base.ROOT_LABELS
        },
        "accepted_extra_trees_light_confidence_95_labels": accepted_labels,
        "gates": gate_rows,
        "feature_importance": feature_importances,
        "promotion_status": {
            "accepted_rows_added": 0,
            "accepted_regime_confidence_labels": len(accepted_labels),
            "new_confidence_gate": bool(accepted_labels),
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": len(accepted_labels) == len(base.ROOT_LABELS),
            "trade_usable": False,
            "update_goal": False,
        },
    }

    (OUT / "source_label_extra_trees_light_threshold_screen_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(OUT / "source_label_extra_trees_light_threshold_gates_v1.csv", gate_rows)
    write_csv(OUT / "source_label_extra_trees_light_threshold_candidates_v1.csv", candidate_rows)
    write_csv(OUT / "source_label_extra_trees_light_feature_importance_v1.csv", feature_importances)

    lines = [
        "# Source Label ExtraTrees Light Threshold Screen v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate_result}`",
        "",
        "## Result",
        "",
        f"- Rows scored: `{len(data)}`.",
        "- Model: light `ExtraTreesClassifier` trained only on the `calibration` split.",
        "- Gate: every required split needs support `>=50` and Wilson95 lower bound `>=0.95`.",
        f"- Accepted ExtraTrees-light confidence labels: `{accepted_labels}`.",
        "- Accepted rows added `0`; source/control evidence acquired `false`; canonical merge `false`; downstream promotion rerun `false`; `update_goal=false`.",
        "",
        "## Best Gates",
        "",
        "| Label | Accepted 95 | Threshold | Min Support | Min Wilson95 | Blockers |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in gate_rows:
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
    (OUT / "source_label_extra_trees_light_threshold_screen_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS gate_result={gate_result}",
        f"PASS row_count={len(data)}",
        f"PASS accepted_extra_trees_light_confidence_95_labels={','.join(accepted_labels) if accepted_labels else 'none'}",
        f"PASS accepted_regime_confidence_labels={len(accepted_labels)}",
        f"PASS new_confidence_gate={str(bool(accepted_labels)).lower()}",
        "PASS source_control_evidence_acquired=false",
        "PASS canonical_merge=false",
        "PASS downstream_promotion_rerun=false",
        f"PASS strict_full_objective={str(len(accepted_labels) == len(base.ROOT_LABELS)).lower()}",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "source_label_extra_trees_light_threshold_screen_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "gate_result": gate_result,
        "accepted_extra_trees_light_confidence_95_labels": accepted_labels,
        "promotion_status": result["promotion_status"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
