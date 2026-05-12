#!/usr/bin/env python3
"""Mine split-gated source-label qualifying rules without changing runtime code."""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260512T043932-codex-source-label-rule-qualifier-miner-v1"
SLUG = "source-label-rule-qualifier-miner-v1"
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
TOP_ATOMS_PER_LABEL = 35
TOP_RULES_PER_LABEL = 25

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


@dataclass(frozen=True)
class Atom:
    atom_id: str
    feature: str
    op: str
    value: float
    text: str


@dataclass(frozen=True)
class Rule:
    rule_id: str
    text: str
    atoms: tuple[Atom, ...]


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
    for col in ["source_owner", "market_family", "symbol", "split_role", "main_regime_v2_label"]:
        data[col] = data[col].astype(str)
    return data.reset_index(drop=True)


def make_atoms(data: pd.DataFrame) -> list[Atom]:
    atoms: list[Atom] = []
    quantiles = [0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50,
                 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.98, 0.99]
    calibration = data[data["split_role"] == "calibration"]
    for feature in FEATURE_COLS:
        values = calibration[feature].replace([np.inf, -np.inf], np.nan).dropna()
        thresholds = sorted(set(float(v) for v in values.quantile(quantiles).to_list() if pd.notna(v)))
        for threshold in thresholds:
            value_text = f"{threshold:.10g}"
            atoms.append(Atom(f"{feature}_ge_{value_text}", feature, ">=", threshold, f"{feature} >= {value_text}"))
            atoms.append(Atom(f"{feature}_le_{value_text}", feature, "<=", threshold, f"{feature} <= {value_text}"))
    return atoms


def atom_mask(data: pd.DataFrame, atom: Atom) -> np.ndarray:
    values = data[atom.feature].to_numpy()
    if atom.op == ">=":
        return values >= atom.value
    return values <= atom.value


def evaluate_mask(
    data: pd.DataFrame,
    split_masks: dict[str, np.ndarray],
    label_mask: np.ndarray,
    mask: np.ndarray,
    label: str,
    rule_id: str,
    rule_text: str,
) -> dict[str, Any]:
    split_metrics: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []
    min_lcb = 1.0
    min_support = 10**9
    for split in REQUIRED_SPLITS:
        split_mask = split_masks[split] & mask
        total = int(split_mask.sum())
        successes = int((label_mask & split_mask).sum())
        precision = successes / total if total else 0.0
        lcb = wilson_lcb(successes, total)
        min_lcb = min(min_lcb, lcb)
        min_support = min(min_support, total)
        split_metrics[split] = {
            "support": total,
            "label_hits": successes,
            "precision": round(precision, 10),
            "wilson95_lcb": round(lcb, 10),
        }
        if total < MIN_SUPPORT:
            blockers.append(f"{split}_support_below_{MIN_SUPPORT}")
        if lcb < WILSON_THRESHOLD:
            blockers.append(f"{split}_wilson95_below_{WILSON_THRESHOLD}")
    return {
        "label": label,
        "rule_id": rule_id,
        "rule": rule_text,
        "accepted_rule_confidence_95": not blockers,
        "blockers": ";".join(blockers),
        "min_split_support": int(min_support if min_support != 10**9 else 0),
        "min_split_wilson95_lcb": round(float(min_lcb), 10),
        **{
            f"{split}_{field}": value
            for split, metrics in split_metrics.items()
            for field, value in metrics.items()
        },
    }


def calibration_rank(row: dict[str, Any]) -> tuple[float, int, float]:
    return (
        float(row["calibration_wilson95_lcb"]),
        int(row["calibration_support"]),
        float(row["min_split_wilson95_lcb"]),
    )


def evaluate_calibration_atom(
    split_masks: dict[str, np.ndarray],
    label_mask: np.ndarray,
    mask: np.ndarray,
) -> tuple[float, int]:
    calibration_mask = split_masks["calibration"] & mask
    total = int(calibration_mask.sum())
    successes = int((label_mask & calibration_mask).sum())
    return wilson_lcb(successes, total), total


def mine_rules(data: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    atoms = make_atoms(data)
    atom_masks = {atom.atom_id: atom_mask(data, atom) for atom in atoms}
    split_values = data["split_role"].to_numpy()
    split_masks = {split: split_values == split for split in REQUIRED_SPLITS}
    label_values = data["main_regime_v2_label"].to_numpy()
    candidate_rows: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    atom_summary_rows: list[dict[str, Any]] = []

    for label in ROOT_LABELS:
        label_mask = label_values == label
        ranked_atoms: list[tuple[Atom, float, int]] = []
        for atom in atoms:
            calibration_lcb, calibration_support = evaluate_calibration_atom(
                split_masks,
                label_mask,
                atom_masks[atom.atom_id],
            )
            ranked_atoms.append((atom, calibration_lcb, calibration_support))

        top_atoms = [
            atom for atom, _, support in sorted(ranked_atoms, key=lambda item: (item[1], item[2]), reverse=True)
            if support >= MIN_SUPPORT
        ][:TOP_ATOMS_PER_LABEL]

        label_candidates: list[dict[str, Any]] = []
        for atom in top_atoms:
            row = evaluate_mask(data, split_masks, label_mask, atom_masks[atom.atom_id], label, atom.atom_id, atom.text)
            row["rule_kind"] = "single_atom"
            label_candidates.append(row)
            atom_summary_rows.append(row)

        for left, right in itertools.combinations(top_atoms, 2):
            if left.feature == right.feature and left.op != right.op:
                if left.op == ">=" and left.value > right.value:
                    continue
                if right.op == ">=" and right.value > left.value:
                    continue
            mask = atom_masks[left.atom_id] & atom_masks[right.atom_id]
            rule_id = f"{left.atom_id}__and__{right.atom_id}"
            rule_text = f"{left.text} AND {right.text}"
            row = evaluate_mask(data, split_masks, label_mask, mask, label, rule_id, rule_text)
            row["rule_kind"] = "two_atom_conjunction"
            label_candidates.append(row)

        ranked = sorted(label_candidates, key=lambda row: (row["accepted_rule_confidence_95"], row["min_split_wilson95_lcb"], row["min_split_support"], row["calibration_wilson95_lcb"]), reverse=True)
        top_rows = ranked[:TOP_RULES_PER_LABEL]
        candidate_rows.extend(top_rows)
        best = top_rows[0]
        gate_rows.append(
            {
                "label": label,
                "accepted_rule_confidence_95": best["accepted_rule_confidence_95"],
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
    return candidate_rows, gate_rows, atom_summary_rows


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
    data = build_dataset()
    candidate_rows, gate_rows, atom_summary_rows = mine_rules(data)
    accepted_labels = [row["label"] for row in gate_rows if row["accepted_rule_confidence_95"]]

    write_csv(OUT / "source_label_rule_qualifier_candidates_v1.csv", candidate_rows)
    write_csv(OUT / "source_label_rule_qualifier_gates_v1.csv", gate_rows)
    write_csv(OUT / "source_label_rule_qualifier_atom_summary_v1.csv", atom_summary_rows)

    result = {
        "run_id": RUN_ID,
        "gate_result": (
            "source_label_rule_qualifier_miner_v1=all_root_labels_rule_accepted"
            if len(accepted_labels) == len(ROOT_LABELS)
            else "source_label_rule_qualifier_miner_v1=rules_scored_no_full_acceptance"
        ),
        "row_count": int(len(data)),
        "rows_sha256": sha256_file(INTAKE_ROWS),
        "provenance_sha256": sha256_file(INTAKE_PROVENANCE),
        "label_counts": {k: int(v) for k, v in data["main_regime_v2_label"].value_counts().to_dict().items()},
        "split_counts": {k: int(v) for k, v in data["split_role"].value_counts().to_dict().items()},
        "feature_columns": FEATURE_COLS,
        "accepted_rule_confidence_95_labels": accepted_labels,
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
    (OUT / "source_label_rule_qualifier_miner_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    lines = [
        "# Source Label Rule Qualifier Miner v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{result['gate_result']}`",
        "",
        "## Result",
        "",
        f"- Rows scored: `{len(data)}`.",
        "- Rule search: single-feature threshold atoms plus bounded two-atom conjunctions.",
        "- Gate: every required split needs support `>=50` and Wilson95 lower bound `>=0.95`.",
        f"- Accepted rule-confidence labels: `{accepted_labels}`.",
        "- Accepted rows added `0`; strict full objective remains `false`; `update_goal=false`.",
        "",
        "## Best Gates",
        "",
        "| Label | Accepted 95 | Min Support | Min Wilson95 | Rule | Blockers |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in gate_rows:
        lines.append(
            f"| `{row['label']}` | `{str(row['accepted_rule_confidence_95']).lower()}` | "
            f"`{row['min_split_support']}` | `{row['min_split_wilson95_lcb']}` | "
            f"`{row['best_rule']}` | {row['blockers'] or 'none'} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a diagnostic qualifying-condition miner over the existing source-label equivalence package. It does not create source/control evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.",
        ]
    )
    (OUT / "source_label_rule_qualifier_miner_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS row_count={len(data)}",
        f"PASS accepted_rule_confidence_95_labels={','.join(accepted_labels) if accepted_labels else 'none'}",
        f"PASS new_confidence_gate={str(len(accepted_labels) == len(ROOT_LABELS)).lower()}",
        "PASS source_control_evidence_acquired=false",
        "PASS canonical_merge=false",
        "PASS downstream_promotion_rerun=false",
        "PASS strict_full_objective=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "source_label_rule_qualifier_miner_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
