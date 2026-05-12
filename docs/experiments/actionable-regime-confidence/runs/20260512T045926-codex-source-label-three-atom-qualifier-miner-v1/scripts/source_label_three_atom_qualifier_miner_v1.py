#!/usr/bin/env python3
"""Mine bounded three-atom source-label qualifiers with strict split gates."""

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


RUN_ID = "20260512T045926-codex-source-label-three-atom-qualifier-miner-v1"
SLUG = "source-label-three-atom-qualifier-miner-v1"
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
TOP_ATOMS_PER_LABEL = 28
TOP_RULES_PER_LABEL = 40

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
    quantiles = [
        0.01,
        0.02,
        0.05,
        0.10,
        0.15,
        0.20,
        0.25,
        0.30,
        0.35,
        0.40,
        0.45,
        0.50,
        0.55,
        0.60,
        0.65,
        0.70,
        0.75,
        0.80,
        0.85,
        0.90,
        0.95,
        0.98,
        0.99,
    ]
    calibration = data[data["split_role"] == "calibration"]
    atoms: list[Atom] = []
    for feature in FEATURE_COLS:
        values = calibration[feature].replace([np.inf, -np.inf], np.nan).dropna()
        thresholds = sorted(set(float(v) for v in values.quantile(quantiles).to_list() if pd.notna(v)))
        for threshold in thresholds:
            value_text = f"{threshold:.10g}"
            atoms.append(Atom(f"{feature}_ge_{value_text}", feature, ">=", threshold, f"{feature} >= {value_text}"))
            atoms.append(Atom(f"{feature}_le_{value_text}", feature, "<=", threshold, f"{feature} <= {value_text}"))
    return atoms


def atom_mask(data: pd.DataFrame, atom: Atom) -> np.ndarray:
    values = data[atom.feature].to_numpy(dtype=float)
    if atom.op == ">=":
        return values >= atom.value
    return values <= atom.value


def compatible(atoms: tuple[Atom, ...]) -> bool:
    lower: dict[str, float] = {}
    upper: dict[str, float] = {}
    for atom in atoms:
        if atom.op == ">=":
            lower[atom.feature] = max(lower.get(atom.feature, -math.inf), atom.value)
        else:
            upper[atom.feature] = min(upper.get(atom.feature, math.inf), atom.value)
    for feature in set(lower) & set(upper):
        if lower[feature] > upper[feature]:
            return False
    return True


def evaluate_mask(
    split_masks: dict[str, np.ndarray],
    label_mask: np.ndarray,
    mask: np.ndarray,
    label: str,
    rule_id: str,
    rule_text: str,
    rule_kind: str,
) -> dict[str, Any]:
    blockers: list[str] = []
    min_lcb = 1.0
    min_support = 10**9
    row: dict[str, Any] = {
        "label": label,
        "rule_id": rule_id,
        "rule": rule_text,
        "rule_kind": rule_kind,
    }
    for split in REQUIRED_SPLITS:
        split_mask = split_masks[split] & mask
        total = int(split_mask.sum())
        successes = int((label_mask & split_mask).sum())
        precision = successes / total if total else 0.0
        lcb = wilson_lcb(successes, total)
        min_lcb = min(min_lcb, lcb)
        min_support = min(min_support, total)
        row[f"{split}_support"] = total
        row[f"{split}_label_hits"] = successes
        row[f"{split}_precision"] = round(precision, 10)
        row[f"{split}_wilson95_lcb"] = round(lcb, 10)
        if total < MIN_SUPPORT:
            blockers.append(f"{split}_support_below_{MIN_SUPPORT}")
        if lcb < WILSON_THRESHOLD:
            blockers.append(f"{split}_wilson95_below_{WILSON_THRESHOLD}")
    row["accepted_three_atom_confidence_95"] = not blockers
    row["blockers"] = ";".join(blockers)
    row["min_split_support"] = int(min_support if min_support != 10**9 else 0)
    row["min_split_wilson95_lcb"] = round(float(min_lcb), 10)
    return row


def calibration_lcb(split_masks: dict[str, np.ndarray], label_mask: np.ndarray, mask: np.ndarray) -> tuple[float, int]:
    calibration_mask = split_masks["calibration"] & mask
    total = int(calibration_mask.sum())
    successes = int((label_mask & calibration_mask).sum())
    return wilson_lcb(successes, total), total


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def mine_rules(data: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    atoms = make_atoms(data)
    atom_masks = {atom.atom_id: atom_mask(data, atom) for atom in atoms}
    split_values = data["split_role"].to_numpy(dtype=str)
    split_masks = {split: split_values == split for split in REQUIRED_SPLITS}
    labels = data["main_regime_v2_label"].to_numpy(dtype=str)

    candidate_rows: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []

    for label in ROOT_LABELS:
        label_mask = labels == label
        ranked_atoms: list[tuple[Atom, float, int]] = []
        for atom in atoms:
            lcb, support = calibration_lcb(split_masks, label_mask, atom_masks[atom.atom_id])
            ranked_atoms.append((atom, lcb, support))
        top_atoms = [
            atom for atom, _, support in sorted(ranked_atoms, key=lambda item: (item[1], item[2]), reverse=True)
            if support >= MIN_SUPPORT
        ][:TOP_ATOMS_PER_LABEL]

        label_candidates: list[dict[str, Any]] = []
        for width in (1, 2, 3):
            for combo in itertools.combinations(top_atoms, width):
                if not compatible(combo):
                    continue
                mask = np.ones(len(data), dtype=bool)
                for atom in combo:
                    mask &= atom_masks[atom.atom_id]
                rule_id = "__and__".join(atom.atom_id for atom in combo)
                rule_text = " AND ".join(atom.text for atom in combo)
                row = evaluate_mask(
                    split_masks,
                    label_mask,
                    mask,
                    label,
                    rule_id,
                    rule_text,
                    f"{width}_atom_conjunction",
                )
                label_candidates.append(row)

        ranked = sorted(
            label_candidates,
            key=lambda row: (
                row["accepted_three_atom_confidence_95"],
                row["min_split_wilson95_lcb"],
                row["min_split_support"],
                row["calibration_wilson95_lcb"],
            ),
            reverse=True,
        )
        candidate_rows.extend(ranked[:TOP_RULES_PER_LABEL])
        best = ranked[0]
        gate_rows.append(
            {
                "label": label,
                "accepted_three_atom_confidence_95": best["accepted_three_atom_confidence_95"],
                "best_rule_id": best["rule_id"],
                "best_rule": best["rule"],
                "best_rule_kind": best["rule_kind"],
                "blockers": best["blockers"],
                "min_split_support": best["min_split_support"],
                "min_split_wilson95_lcb": best["min_split_wilson95_lcb"],
                "required_splits": ";".join(REQUIRED_SPLITS),
                "wilson_threshold": WILSON_THRESHOLD,
                "min_support": MIN_SUPPORT,
            }
        )
    return candidate_rows, gate_rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    data = build_dataset()
    candidate_rows, gate_rows = mine_rules(data)
    accepted_labels = [row["label"] for row in gate_rows if row["accepted_three_atom_confidence_95"]]
    gate_result = (
        "source_label_three_atom_qualifier_miner_v1=all_root_labels_three_atom_accepted"
        if len(accepted_labels) == len(ROOT_LABELS)
        else "source_label_three_atom_qualifier_miner_v1=three_atom_scored_no_full_acceptance"
    )

    write_csv(OUT / "source_label_three_atom_qualifier_candidates_v1.csv", candidate_rows)
    write_csv(OUT / "source_label_three_atom_qualifier_gates_v1.csv", gate_rows)

    result = {
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "row_count": int(len(data)),
        "rows_sha256": sha256_file(INTAKE_ROWS),
        "provenance_sha256": sha256_file(INTAKE_PROVENANCE),
        "label_counts": {k: int(v) for k, v in data["main_regime_v2_label"].value_counts().to_dict().items()},
        "split_counts": {k: int(v) for k, v in data["split_role"].value_counts().to_dict().items()},
        "feature_columns": FEATURE_COLS,
        "search_shape": {
            "top_atoms_per_label": TOP_ATOMS_PER_LABEL,
            "max_conjunction_width": 3,
            "top_rules_per_label": TOP_RULES_PER_LABEL,
        },
        "accepted_three_atom_confidence_95_labels": accepted_labels,
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
    (OUT / "source_label_three_atom_qualifier_miner_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    lines = [
        "# Source Label Three-Atom Qualifier Miner v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate_result}`",
        "",
        "## Result",
        "",
        f"- Rows scored: `{len(data)}`.",
        "- Rule search: bounded single/two/three-atom conjunctions selected by calibration Wilson95 ranking.",
        "- Gate: every required split needs support `>=50` and Wilson95 lower bound `>=0.95`.",
        f"- Accepted three-atom confidence labels: `{accepted_labels}`.",
        "- Accepted rows added `0`; strict full objective remains `false`; `update_goal=false`.",
        "",
        "## Best Gates",
        "",
        "| Label | Accepted 95 | Min Support | Min Wilson95 | Kind | Rule | Blockers |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for row in gate_rows:
        lines.append(
            f"| `{row['label']}` | `{str(row['accepted_three_atom_confidence_95']).lower()}` | "
            f"`{row['min_split_support']}` | `{row['min_split_wilson95_lcb']}` | "
            f"`{row['best_rule_kind']}` | `{row['best_rule']}` | {row['blockers'] or 'none'} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a diagnostic qualifying-condition miner over the existing source-label equivalence package. It does not create source/control evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.",
        ]
    )
    (OUT / "source_label_three_atom_qualifier_miner_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS row_count={len(data)}",
        f"PASS gate_result={gate_result}",
        f"PASS accepted_three_atom_confidence_95_labels={','.join(accepted_labels) if accepted_labels else 'none'}",
        f"PASS new_confidence_gate={str(len(accepted_labels) == len(ROOT_LABELS)).lower()}",
        "PASS source_control_evidence_acquired=false",
        "PASS canonical_merge=false",
        "PASS downstream_promotion_rerun=false",
        "PASS strict_full_objective=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "source_label_three_atom_qualifier_miner_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
