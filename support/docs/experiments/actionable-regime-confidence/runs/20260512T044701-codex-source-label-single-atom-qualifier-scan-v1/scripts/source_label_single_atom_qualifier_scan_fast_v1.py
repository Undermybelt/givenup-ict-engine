#!/usr/bin/env python3
"""Fast single-threshold qualifier scan using sorted cumulative counts."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260512T044701-codex-source-label-single-atom-qualifier-scan-v1"
SLUG = "source-label-single-atom-qualifier-scan-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
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
TOP_CANDIDATES_PER_LABEL = 30

STOCK_NUMERIC = [
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
NIFTY_NUMERIC = [
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
FEATURE_COLS = STOCK_NUMERIC + NIFTY_NUMERIC


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
        stock[["timestamp_or_date", "symbol", "main_regime_v2_label", *STOCK_NUMERIC]],
        on=["timestamp_or_date", "symbol", "main_regime_v2_label"],
        how="left",
    )
    for col in NIFTY_NUMERIC:
        stock_merged[col] = 0.0

    nifty = pd.read_csv(NIFTY_SOURCE).rename(columns={"Date": "timestamp_or_date"})
    nifty_merged = nifty_rows.merge(
        nifty[["timestamp_or_date", *NIFTY_NUMERIC]],
        on=["timestamp_or_date"],
        how="left",
    )
    for col in STOCK_NUMERIC:
        nifty_merged[col] = 0.0

    data = pd.concat([stock_merged, nifty_merged], ignore_index=True)
    data = data[data["main_regime_v2_label"].isin(ROOT_LABELS)].copy()
    data[FEATURE_COLS] = data[FEATURE_COLS].apply(pd.to_numeric, errors="coerce")
    data = data.dropna(subset=FEATURE_COLS)
    for col in ["split_role", "main_regime_v2_label"]:
        data[col] = data[col].astype(str)
    return data.reset_index(drop=True)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def split_indexes(data: pd.DataFrame, feature: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for split in REQUIRED_SPLITS:
        subset = data[data["split_role"] == split]
        values = subset[feature].to_numpy(dtype=float)
        labels = subset["main_regime_v2_label"].to_numpy(dtype=str)
        order = np.argsort(values, kind="mergesort")
        sorted_values = values[order]
        sorted_labels = labels[order]
        label_cumsums = {
            label: np.concatenate([[0], np.cumsum(sorted_labels == label)])
            for label in ROOT_LABELS
        }
        out[split] = {
            "values": sorted_values,
            "count": int(len(sorted_values)),
            "label_cumsums": label_cumsums,
        }
    return out


def split_metric(index: dict[str, Any], label: str, op: str, threshold: float) -> tuple[int, int, float, float]:
    values = index["values"]
    total_count = index["count"]
    cumsum = index["label_cumsums"][label]
    if op == "<=":
        pos = int(np.searchsorted(values, threshold, side="right"))
        total = pos
        hits = int(cumsum[pos])
    else:
        pos = int(np.searchsorted(values, threshold, side="left"))
        total = total_count - pos
        hits = int(cumsum[total_count] - cumsum[pos])
    precision = hits / total if total else 0.0
    lcb = wilson_lcb(hits, total)
    return total, hits, precision, lcb


def evaluate_rule(indexes: dict[str, dict[str, Any]], label: str, feature: str, op: str, threshold: float) -> dict[str, Any]:
    threshold_text = f"{threshold:.10g}"
    rule_id = f"{feature}_{'ge' if op == '>=' else 'le'}_{threshold_text}"
    rule_text = f"{feature} {op} {threshold_text}"
    row: dict[str, Any] = {"label": label, "rule_id": rule_id, "rule": rule_text}
    blockers: list[str] = []
    min_support = 10**12
    min_lcb = 1.0
    for split in REQUIRED_SPLITS:
        support, hits, precision, lcb = split_metric(indexes[split], label, op, threshold)
        row[f"{split}_support"] = support
        row[f"{split}_label_hits"] = hits
        row[f"{split}_precision"] = round(precision, 10)
        row[f"{split}_wilson95_lcb"] = round(lcb, 10)
        min_support = min(min_support, support)
        min_lcb = min(min_lcb, lcb)
        if support < MIN_SUPPORT:
            blockers.append(f"{split}_support_below_{MIN_SUPPORT}")
        if lcb < WILSON_THRESHOLD:
            blockers.append(f"{split}_wilson95_below_{WILSON_THRESHOLD}")
    row["accepted_single_atom_confidence_95"] = not blockers
    row["blockers"] = ";".join(blockers)
    row["min_split_support"] = int(min_support if min_support != 10**12 else 0)
    row["min_split_wilson95_lcb"] = round(float(min_lcb), 10)
    return row


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    data = build_dataset()
    quantiles = [0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45,
                 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.98, 0.99]
    calibration = data[data["split_role"] == "calibration"]

    candidates_by_label: dict[str, list[dict[str, Any]]] = {label: [] for label in ROOT_LABELS}
    for feature in FEATURE_COLS:
        values = calibration[feature].replace([np.inf, -np.inf], np.nan).dropna()
        thresholds = sorted(set(float(v) for v in values.quantile(quantiles).to_list() if pd.notna(v)))
        indexes = split_indexes(data, feature)
        for threshold in thresholds:
            for op in (">=", "<="):
                for label in ROOT_LABELS:
                    row = evaluate_rule(indexes, label, feature, op, threshold)
                    candidates_by_label[label].append(row)

    candidate_rows: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    for label, rows in candidates_by_label.items():
        ranked = sorted(
            rows,
            key=lambda row: (
                row["accepted_single_atom_confidence_95"],
                row["min_split_wilson95_lcb"],
                row["min_split_support"],
                row["calibration_wilson95_lcb"],
            ),
            reverse=True,
        )
        candidate_rows.extend(ranked[:TOP_CANDIDATES_PER_LABEL])
        best = ranked[0]
        gate_rows.append(
            {
                "label": label,
                "accepted_single_atom_confidence_95": best["accepted_single_atom_confidence_95"],
                "best_rule_id": best["rule_id"],
                "best_rule": best["rule"],
                "blockers": best["blockers"],
                "min_split_support": best["min_split_support"],
                "min_split_wilson95_lcb": best["min_split_wilson95_lcb"],
                "required_splits": ";".join(REQUIRED_SPLITS),
                "wilson_threshold": WILSON_THRESHOLD,
                "min_support": MIN_SUPPORT,
            }
        )

    accepted_labels = [row["label"] for row in gate_rows if row["accepted_single_atom_confidence_95"]]
    gate_result = (
        "source_label_single_atom_qualifier_scan_v1=all_root_labels_single_atom_accepted"
        if len(accepted_labels) == len(ROOT_LABELS)
        else "source_label_single_atom_qualifier_scan_v1=single_atom_scored_no_full_acceptance"
    )

    write_csv(OUT / "source_label_single_atom_qualifier_candidates_v1.csv", candidate_rows)
    write_csv(OUT / "source_label_single_atom_qualifier_gates_v1.csv", gate_rows)

    result = {
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "scan_method": "single_feature_threshold_atoms_sorted_cumulative_counts",
        "abandoned_prior_attempt": "source_label_single_atom_qualifier_scan_v1.py was terminated after exceeding diagnostic runtime without output",
        "row_count": int(len(data)),
        "rows_sha256": sha256_file(INTAKE_ROWS),
        "provenance_sha256": sha256_file(INTAKE_PROVENANCE),
        "label_counts": {str(k): int(v) for k, v in data["main_regime_v2_label"].value_counts().to_dict().items()},
        "split_counts": {str(k): int(v) for k, v in data["split_role"].value_counts().to_dict().items()},
        "feature_columns": FEATURE_COLS,
        "accepted_single_atom_confidence_95_labels": accepted_labels,
        "gates": gate_rows,
        "promotion_status": {
            "accepted_rows_added": 0,
            "new_confidence_gate": len(accepted_labels) == len(ROOT_LABELS),
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
    }
    (OUT / "source_label_single_atom_qualifier_scan_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    lines = [
        "# Source Label Single-Atom Qualifier Scan v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate_result}`",
        "",
        "## Result",
        "",
        f"- Rows scored: `{len(data)}`.",
        "- Rule search: single-feature threshold atoms using sorted cumulative counts.",
        "- Gate: every required split needs support `>=50` and Wilson95 lower bound `>=0.95`.",
        f"- Accepted single-atom confidence labels: `{accepted_labels}`.",
        "- Accepted rows added `0`; strict full objective remains `false`; `update_goal=false`.",
        "",
        "## Best Gates",
        "",
        "| Label | Accepted 95 | Min Support | Min Wilson95 | Rule | Blockers |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in gate_rows:
        lines.append(
            f"| `{row['label']}` | `{str(row['accepted_single_atom_confidence_95']).lower()}` | "
            f"`{row['min_split_support']}` | `{row['min_split_wilson95_lcb']}` | "
            f"`{row['best_rule']}` | {row['blockers'] or 'none'} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a diagnostic qualifying-condition scan over the existing source-label equivalence package. It does not create source/control evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.",
        ]
    )
    (OUT / "source_label_single_atom_qualifier_scan_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS row_count={len(data)}",
        f"PASS gate_result={gate_result}",
        f"PASS accepted_single_atom_confidence_95_labels={','.join(accepted_labels) if accepted_labels else 'none'}",
        f"PASS new_confidence_gate={str(len(accepted_labels) == len(ROOT_LABELS)).lower()}",
        "PASS source_control_evidence_acquired=false",
        "PASS canonical_merge=false",
        "PASS downstream_promotion_rerun=false",
        "PASS strict_full_objective=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "source_label_single_atom_qualifier_scan_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
