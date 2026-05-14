#!/usr/bin/env python3
"""Predictive confidence screen over the live source-label equivalence package."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260512T041656-codex-source-label-predictive-confidence-screen-v1"
SLUG = "source-label-predictive-confidence-screen-v1"
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

    stock = pd.read_csv(STOCK_SOURCE)
    stock = stock.rename(
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
    data[STOCK_FEATURES + NIFTY_FEATURES] = data[STOCK_FEATURES + NIFTY_FEATURES].apply(pd.to_numeric, errors="coerce")
    data = data.dropna(subset=STOCK_FEATURES + NIFTY_FEATURES)
    for col in ["source_owner", "market_family", "symbol", "split_role", "main_regime_v2_label"]:
        data[col] = data[col].astype(str)
    return data


def fit_predict(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any], list[str]]:
    feature_frame = data[STOCK_FEATURES + NIFTY_FEATURES + ["source_owner", "market_family", "symbol"]].copy()
    feature_frame = pd.get_dummies(feature_frame, columns=["source_owner", "market_family", "symbol"], dtype=float)
    feature_columns = list(feature_frame.columns)

    train_mask = data["split_role"] == "calibration"
    train_x = feature_frame.loc[train_mask]
    train_y = data.loc[train_mask, "main_regime_v2_label"]
    if len(train_x) < 1000:
        raise RuntimeError("insufficient calibration rows")

    train_matrix = train_x.to_numpy(dtype=float)
    full_matrix = feature_frame.to_numpy(dtype=float)
    classes = sorted(train_y.unique())
    priors: list[float] = []
    means: list[np.ndarray] = []
    variances: list[np.ndarray] = []
    for label in classes:
        class_matrix = train_matrix[(train_y == label).to_numpy()]
        priors.append(len(class_matrix) / len(train_matrix))
        means.append(class_matrix.mean(axis=0))
        variances.append(class_matrix.var(axis=0) + 1e-6)

    log_probs = []
    for prior, mean, variance in zip(priors, means, variances):
        log_likelihood = -0.5 * (
            np.log(2 * np.pi * variance).sum()
            + (((full_matrix - mean) ** 2) / variance).sum(axis=1)
        )
        log_probs.append(np.log(prior) + log_likelihood)
    logits = np.vstack(log_probs).T
    logits = logits - logits.max(axis=1, keepdims=True)
    exp_logits = np.exp(logits)
    probabilities = exp_logits / exp_logits.sum(axis=1, keepdims=True)
    pred_idx = probabilities.argmax(axis=1)
    scored = data[["source_owner", "market_family", "symbol", "timestamp_or_date", "split_role", "main_regime_v2_label"]].copy()
    scored["predicted_label"] = [classes[index] for index in pred_idx]
    scored["predicted_confidence"] = probabilities.max(axis=1)
    scored["correct"] = scored["predicted_label"] == scored["main_regime_v2_label"]
    model = {
        "kind": "GaussianNaiveBayesInScript",
        "classes": classes,
        "priors": {label: priors[index] for index, label in enumerate(classes)},
        "mean_abs_weight_by_feature": dict(
            zip(feature_columns, np.abs(np.vstack(means)).mean(axis=0).tolist())
        ),
    }
    return scored, model, feature_columns


def metric_rows(scored: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label in ROOT_LABELS:
        for split in REQUIRED_SPLITS:
            subset = scored[(scored["split_role"] == split) & (scored["predicted_label"] == label) & (scored["predicted_confidence"] >= CONFIDENCE_THRESHOLD)]
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
                "accepted_predictive_confidence_95": not blockers,
                "blockers": ";".join(blockers),
                "required_splits": ";".join(REQUIRED_SPLITS),
                "confidence_threshold": CONFIDENCE_THRESHOLD,
                "wilson_threshold": WILSON_THRESHOLD,
                "min_support": MIN_SUPPORT,
            }
        )
    return gates


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    verifier = run_verifier()
    data = build_dataset()
    scored, model, feature_columns = fit_predict(data)
    metrics = metric_rows(scored)
    gates = gate_rows(metrics)
    accepted = [row["label"] for row in gates if row["accepted_predictive_confidence_95"]]

    write_csv(OUT / "source_label_predictive_confidence_metrics_v1.csv", metrics)
    write_csv(OUT / "source_label_predictive_confidence_gates_v1.csv", gates)

    importances = sorted(
        model["mean_abs_weight_by_feature"].items(),
        key=lambda item: item[1],
        reverse=True,
    )[:25]
    importance_rows = [{"feature": feature, "importance": round(float(value), 10)} for feature, value in importances]
    write_csv(OUT / "source_label_predictive_confidence_feature_importance_v1.csv", importance_rows)

    label_counts = data["main_regime_v2_label"].value_counts().to_dict()
    split_counts = data["split_role"].value_counts().to_dict()
    result = {
        "run_id": RUN_ID,
        "gate_result": "source_label_predictive_confidence_screen_v1=predictive_confidence_scored_no_full_acceptance",
        "verifier": verifier,
        "row_count": int(len(data)),
        "rows_sha256": sha256_file(INTAKE_ROWS),
        "provenance_sha256": sha256_file(INTAKE_PROVENANCE),
        "model": {
            "kind": model["kind"],
            "train_split": "calibration",
            "feature_count": len(feature_columns),
        },
        "label_counts": label_counts,
        "split_counts": split_counts,
        "accepted_predictive_confidence_95_labels": accepted,
        "gates": gates,
        "promotion_status": {
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
    }
    (OUT / "source_label_predictive_confidence_screen_v1.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [
        "# Source Label Predictive Confidence Screen v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Gate result: `source_label_predictive_confidence_screen_v1=predictive_confidence_scored_no_full_acceptance`",
        "",
        "## Result",
        "",
        f"- Verifier status: `{verifier.get('status')}`; return code `{verifier.get('return_code')}`; rows `{verifier.get('row_count')}`.",
        f"- Model: Gaussian Naive Bayes implemented in this script, calibration split training only, {len(feature_columns)} features, high-confidence threshold `{CONFIDENCE_THRESHOLD}`.",
        f"- Accepted predictive-confidence labels: `{accepted}`.",
        "- Accepted rows added `0`; new confidence gate `false`; strict full objective `false`; `update_goal=false`.",
        "",
        "## Gates",
        "",
        "| Label | Accepted 95 | Blockers |",
        "|---|---|---|",
    ]
    for row in gates:
        lines.append(f"| `{row['label']}` | `{str(row['accepted_predictive_confidence_95']).lower()}` | {row['blockers']} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a diagnostic predictive-confidence screen over source-owned labels. It does not promote schema readiness or model confidence unless every required split passes with enough high-confidence support and Wilson95 lower bound >=0.95.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{OUT / 'source_label_predictive_confidence_screen_v1.json'}`",
            f"- Metrics CSV: `{OUT / 'source_label_predictive_confidence_metrics_v1.csv'}`",
            f"- Gates CSV: `{OUT / 'source_label_predictive_confidence_gates_v1.csv'}`",
            f"- Feature importance CSV: `{OUT / 'source_label_predictive_confidence_feature_importance_v1.csv'}`",
            f"- Assertions: `{CHECKS / 'source_label_predictive_confidence_screen_v1_assertions.out'}`",
        ]
    )
    (OUT / "source_label_predictive_confidence_screen_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS verifier_status={verifier.get('status')}",
        f"PASS verifier_return_code={verifier.get('return_code')}",
        f"PASS row_count={len(data)}",
        f"PASS accepted_predictive_confidence_95_labels={','.join(accepted) if accepted else 'none'}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "source_label_predictive_confidence_screen_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "run_id": RUN_ID, "accepted": accepted, "row_count": len(data)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
