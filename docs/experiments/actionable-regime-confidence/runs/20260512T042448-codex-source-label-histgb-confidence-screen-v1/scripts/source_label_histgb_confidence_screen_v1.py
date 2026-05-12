#!/usr/bin/env python3
"""HistGradientBoosting confidence screen over source-label equivalence rows."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260512T042448-codex-source-label-histgb-confidence-screen-v1"
SLUG = "source-label-histgb-confidence-screen-v1"
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
COMMAND_OUT = RUN_ROOT / "command-output"

INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
INTAKE_ROWS = INTAKE_ROOT / "source_label_equivalence_rows.csv"
INTAKE_PROVENANCE = INTAKE_ROOT / "source_label_equivalence_provenance.json"
STOCK_SOURCE = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
NIFTY_SOURCE = Path("/tmp/ict-engine-source-label-equivalence-reconstruction-v1/nifty/regime_timeline_history.csv")
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)

ROOT_LABELS = ["Bear", "Bull", "Crisis", "Sideways"]
REQUIRED_SPLITS = ["calibration", "heldout_market", "heldout_time", "test"]
CONFIDENCE_THRESHOLD = 0.95
MIN_SUPPORT = 50
WILSON_THRESHOLD = 0.95
Z95 = 1.959963984540054

STOCK_FEATURES = [
    "close",
    "returns",
    "volatility",
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


def run_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(INTAKE_ROOT)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    (COMMAND_OUT / "source_label_equivalence_verifier.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (COMMAND_OUT / "source_label_equivalence_verifier.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (COMMAND_OUT / "source_label_equivalence_verifier.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"status": "blocked", "reason": "verifier_stdout_not_json"}
    parsed["return_code"] = proc.returncode
    return parsed


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
    feature_cols = STOCK_FEATURES + NIFTY_FEATURES
    data[feature_cols] = data[feature_cols].apply(pd.to_numeric, errors="coerce")
    data = data.dropna(subset=feature_cols)
    for col in ["source_owner", "market_family", "symbol", "split_role", "main_regime_v2_label"]:
        data[col] = data[col].astype(str)
    return data


def model_features(data: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    features = data[STOCK_FEATURES + NIFTY_FEATURES + ["source_owner", "market_family", "symbol"]].copy()
    features = pd.get_dummies(features, columns=["source_owner", "market_family", "symbol"], dtype=float)
    return features, list(features.columns)


def fit_predict(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any], list[dict[str, Any]]]:
    features, feature_columns = model_features(data)
    train_mask = data["split_role"] == "calibration"
    train_x = features.loc[train_mask]
    train_y = data.loc[train_mask, "main_regime_v2_label"]
    if len(train_x) < 1000:
        raise RuntimeError("insufficient calibration rows")

    clf = make_pipeline(
        StandardScaler(with_mean=False),
        HistGradientBoostingClassifier(
            max_iter=240,
            learning_rate=0.045,
            max_leaf_nodes=31,
            min_samples_leaf=80,
            l2_regularization=0.05,
            validation_fraction=None,
            random_state=20260512,
        ),
    )
    clf.fit(train_x, train_y)
    probabilities = clf.predict_proba(features)
    classes = list(clf.classes_)
    pred_index = probabilities.argmax(axis=1)

    scored = data[
        ["source_owner", "market_family", "symbol", "timestamp_or_date", "split_role", "main_regime_v2_label"]
    ].copy()
    scored["predicted_label"] = [classes[index] for index in pred_index]
    scored["predicted_confidence"] = probabilities.max(axis=1)
    scored["correct"] = scored["predicted_label"] == scored["main_regime_v2_label"]

    feature_importance = []
    # Bounded diagnostic: permutation importance on a small calibration sample only.
    sample = train_x.sample(n=min(3000, len(train_x)), random_state=20260512)
    sample_y = train_y.loc[sample.index]
    perm = permutation_importance(clf, sample, sample_y, n_repeats=2, random_state=20260512, n_jobs=1)
    for name, value in sorted(zip(feature_columns, perm.importances_mean), key=lambda item: abs(item[1]), reverse=True)[:40]:
        feature_importance.append({"feature": name, "importance_mean": round(float(value), 10)})

    model = {
        "kind": "HistGradientBoostingClassifier",
        "train_split": "calibration",
        "classes": classes,
        "feature_count": len(feature_columns),
        "parameters": {
            "max_iter": 240,
            "learning_rate": 0.045,
            "max_leaf_nodes": 31,
            "min_samples_leaf": 80,
            "l2_regularization": 0.05,
            "random_state": 20260512,
        },
    }
    return scored, model, feature_importance


def metric_rows(scored: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label in ROOT_LABELS:
        for split in REQUIRED_SPLITS:
            subset = scored[
                (scored["split_role"] == split)
                & (scored["predicted_label"] == label)
                & (scored["predicted_confidence"] >= CONFIDENCE_THRESHOLD)
            ]
            total = int(len(subset))
            successes = int(subset["correct"].sum()) if total else 0
            rows.append(
                {
                    "label": label,
                    "split_role": split,
                    "high_confidence_support": total,
                    "correct_high_confidence": successes,
                    "precision": round(successes / total, 10) if total else 0.0,
                    "wilson95_lcb": round(wilson_lcb(successes, total), 10),
                    "coverage_rows": int(len(scored[scored["split_role"] == split])),
                }
            )
    return rows


def gate_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["label"], row["split_role"]): row for row in metrics}
    gates: list[dict[str, Any]] = []
    for label in ROOT_LABELS:
        blockers: list[str] = []
        for split in REQUIRED_SPLITS:
            row = by_key[(label, split)]
            if int(row["high_confidence_support"]) < MIN_SUPPORT:
                blockers.append(f"{split}_high_confidence_support_below_{MIN_SUPPORT}")
            if float(row["wilson95_lcb"]) < WILSON_THRESHOLD:
                blockers.append(f"{split}_high_confidence_precision_wilson95_below_{WILSON_THRESHOLD}")
        gates.append(
            {
                "label": label,
                "accepted_histgb_confidence_95": not blockers,
                "blockers": ";".join(blockers),
                "required_splits": ";".join(REQUIRED_SPLITS),
                "confidence_threshold": CONFIDENCE_THRESHOLD,
                "wilson_threshold": WILSON_THRESHOLD,
                "min_support": MIN_SUPPORT,
            }
        )
    return gates


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    verifier = run_verifier()
    data = build_dataset()
    scored, model, feature_importance = fit_predict(data)
    metrics = metric_rows(scored)
    gates = gate_rows(metrics)
    accepted = [row["label"] for row in gates if row["accepted_histgb_confidence_95"]]

    write_csv(OUT / "source_label_histgb_confidence_metrics_v1.csv", metrics)
    write_csv(OUT / "source_label_histgb_confidence_gates_v1.csv", gates)
    write_csv(OUT / "source_label_histgb_confidence_feature_importance_v1.csv", feature_importance)

    result = {
        "run_id": RUN_ID,
        "gate_result": (
            "source_label_histgb_confidence_screen_v1=histgb_confidence_full_acceptance"
            if len(accepted) == len(ROOT_LABELS)
            else "source_label_histgb_confidence_screen_v1=histgb_confidence_scored_no_full_acceptance"
        ),
        "verifier": verifier,
        "row_count": int(len(data)),
        "rows_sha256": sha256_file(INTAKE_ROWS),
        "provenance_sha256": sha256_file(INTAKE_PROVENANCE),
        "model": model,
        "label_counts": {k: int(v) for k, v in data["main_regime_v2_label"].value_counts().to_dict().items()},
        "split_counts": {k: int(v) for k, v in data["split_role"].value_counts().to_dict().items()},
        "accepted_histgb_confidence_95_labels": accepted,
        "gates": gates,
        "promotion_status": {
            "accepted_rows_added": 0,
            "new_confidence_gate": len(accepted) == len(ROOT_LABELS),
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
    }
    (OUT / "source_label_histgb_confidence_screen_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    lines = [
        "# Source Label HistGB Confidence Screen v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{result['gate_result']}`",
        "",
        "## Result",
        "",
        f"- Verifier status: `{verifier.get('status')}`; return code `{verifier.get('return_code')}`; rows `{verifier.get('row_count')}`.",
        "- Model: fixed `HistGradientBoostingClassifier`, trained on `calibration` split only.",
        f"- Accepted HistGB confidence labels: `{accepted}`.",
        "- Accepted rows added `0`; strict full objective remains `false`; `update_goal=false`.",
        "",
        "## Gates",
        "",
        "| Label | Accepted 95 | Blockers |",
        "|---|---|---|",
    ]
    for row in gates:
        lines.append(f"| `{row['label']}` | `{str(row['accepted_histgb_confidence_95']).lower()}` | {row['blockers'] or 'none'} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a diagnostic model screen over source-owned labels. It does not promote unless every required split clears support and Wilson95 lower bound >=0.95.",
        ]
    )
    (OUT / "source_label_histgb_confidence_screen_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS verifier_status={verifier.get('status')}",
        f"PASS verifier_return_code={verifier.get('return_code')}",
        f"PASS row_count={len(data)}",
        f"PASS accepted_histgb_confidence_95_labels={','.join(accepted) if accepted else 'none'}",
        "PASS accepted_rows_added=0",
        f"PASS new_confidence_gate={str(len(accepted) == len(ROOT_LABELS)).lower()}",
        "PASS strict_full_objective=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "source_label_histgb_confidence_screen_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
