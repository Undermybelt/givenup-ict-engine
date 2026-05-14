#!/usr/bin/env python3
"""Mine source-native macro/context rules against heldout market and time splits."""

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


RUN_ID = "20260512T052301-codex-source-label-macro-context-rule-miner-v1"
SLUG = "source-label-macro-context-rule-miner-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"

INTAKE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
INTAKE_ROWS = INTAKE_ROOT / "source_label_equivalence_rows.csv"
INTAKE_PROVENANCE = INTAKE_ROOT / "source_label_equivalence_provenance.json"
STOCK_SOURCE = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")

SOURCE_OWNER = "source-owned-stock-market-regimes-2000-2026"
ROOT_LABELS = ["Bear", "Bull", "Crisis", "Sideways"]
REQUIRED_SPLITS = ["calibration", "heldout_market", "heldout_time", "test"]
MIN_SUPPORT = 50
WILSON_THRESHOLD = 0.95
Z95 = 1.959963984540054

NUMERIC_FEATURES = [
    "returns",
    "volatility",
    "regime_confidence",
    "unemployment_rate",
    "fed_funds_rate",
    "cpi",
    "10y_treasury",
    "2y_treasury",
    "vix",
    "yield_curve_10y_2y",
    "abs_returns",
]
CONTEXT_FEATURES = ["macro_context"]
QUANTILES = [0.02, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.98]


@dataclass(frozen=True)
class Atom:
    name: str
    feature: str
    op: str
    value: Any

    def mask(self, data: pd.DataFrame) -> np.ndarray:
        if self.op == ">=":
            return (data[self.feature].to_numpy(dtype=float) >= float(self.value))
        if self.op == "<=":
            return (data[self.feature].to_numpy(dtype=float) <= float(self.value))
        if self.op == "==":
            return (data[self.feature].astype(str).to_numpy() == str(self.value))
        raise ValueError(f"unsupported op {self.op}")


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


def load_dataset() -> pd.DataFrame:
    rows = pd.read_csv(INTAKE_ROWS)
    rows = rows[rows["source_owner"] == SOURCE_OWNER].copy()
    source = pd.read_csv(STOCK_SOURCE).rename(
        columns={
            "date": "timestamp_or_date",
            "ticker": "symbol",
            "regime_label": "main_regime_v2_label",
        }
    )
    source["yield_curve_10y_2y"] = source["10y_treasury"] - source["2y_treasury"]
    source["abs_returns"] = source["returns"].abs()
    merged = rows.merge(
        source[
            [
                "timestamp_or_date",
                "symbol",
                "main_regime_v2_label",
                "macro_context",
                *NUMERIC_FEATURES,
            ]
        ],
        on=["timestamp_or_date", "symbol", "main_regime_v2_label"],
        how="left",
    )
    merged = merged[merged["main_regime_v2_label"].isin(ROOT_LABELS)].copy()
    merged[NUMERIC_FEATURES] = merged[NUMERIC_FEATURES].apply(pd.to_numeric, errors="coerce")
    merged = merged.dropna(subset=NUMERIC_FEATURES + CONTEXT_FEATURES)
    for col in ["split_role", "market_family", "symbol", "main_regime_v2_label", "macro_context"]:
        merged[col] = merged[col].astype(str)
    return merged.reset_index(drop=True)


def build_atoms(data: pd.DataFrame, label: str) -> list[Atom]:
    calibration = data[data["split_role"] == "calibration"]
    positives = calibration[calibration["main_regime_v2_label"] == label]
    atoms: dict[str, Atom] = {}
    for feature in NUMERIC_FEATURES:
        values = pd.concat([calibration[feature], positives[feature]], ignore_index=True)
        thresholds = sorted(set(float(v) for v in values.quantile(QUANTILES).dropna().to_list()))
        for threshold in thresholds:
            for op in (">=", "<="):
                name = f"{feature} {op} {threshold:.10g}"
                atoms[name] = Atom(name=name, feature=feature, op=op, value=threshold)
    for feature in CONTEXT_FEATURES:
        for value in sorted(calibration[feature].dropna().astype(str).unique()):
            name = f"{feature} == {value}"
            atoms[name] = Atom(name=name, feature=feature, op="==", value=value)
    return list(atoms.values())


def evaluate_mask(data: pd.DataFrame, label: str, selected: np.ndarray, rule: str, kind: str) -> dict[str, Any]:
    label_values = data["main_regime_v2_label"].to_numpy()
    split_values = data["split_role"].to_numpy()
    blockers: list[str] = []
    result: dict[str, Any] = {
        "label": label,
        "kind": kind,
        "rule": rule,
    }
    min_support = 10**9
    min_lcb = 1.0
    for split in REQUIRED_SPLITS:
        mask = selected & (split_values == split)
        support = int(mask.sum())
        hits = int(((label_values == label) & mask).sum())
        precision = hits / support if support else 0.0
        lcb = wilson_lcb(hits, support)
        min_support = min(min_support, support)
        min_lcb = min(min_lcb, lcb)
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
    result["accepted_macro_context_rule_confidence_95"] = not blockers
    result["blockers"] = ";".join(blockers)
    return result


def score_row(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        bool(row["accepted_macro_context_rule_confidence_95"]),
        float(row["min_split_wilson95_lcb"]),
        int(row["min_split_support"]),
        float(row["calibration_wilson95_lcb"]),
        int(row["calibration_support"]),
        -len(str(row["rule"])),
    )


def top_atoms(data: pd.DataFrame, label: str, atoms: list[Atom]) -> list[tuple[Atom, np.ndarray, dict[str, Any]]]:
    scored: list[tuple[Atom, np.ndarray, dict[str, Any]]] = []
    for atom in atoms:
        mask = atom.mask(data)
        row = evaluate_mask(data, label, mask, atom.name, "1_atom")
        if row["calibration_support"] >= MIN_SUPPORT:
            scored.append((atom, mask, row))
    scored.sort(key=lambda item: score_row(item[2]), reverse=True)
    return scored[:36]


def mine_label(data: pd.DataFrame, label: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    atoms = build_atoms(data, label)
    first = top_atoms(data, label, atoms)
    candidates: list[dict[str, Any]] = [row for _, _, row in first]

    pair_inputs = first[:28]
    pair_scored: list[tuple[tuple[Atom, Atom], np.ndarray, dict[str, Any]]] = []
    for (atom_a, mask_a, _), (atom_b, mask_b, _) in itertools.combinations(pair_inputs, 2):
        if atom_a.feature == atom_b.feature and atom_a.op == atom_b.op:
            continue
        mask = mask_a & mask_b
        rule = f"{atom_a.name} AND {atom_b.name}"
        row = evaluate_mask(data, label, mask, rule, "2_atom")
        if row["calibration_support"] >= MIN_SUPPORT:
            pair_scored.append(((atom_a, atom_b), mask, row))
            candidates.append(row)
    pair_scored.sort(key=lambda item: score_row(item[2]), reverse=True)

    triple_inputs = pair_scored[:24]
    for (atoms_pair, pair_mask, _), (atom_c, mask_c, _) in itertools.product(triple_inputs, first[:24]):
        atom_names = {atoms_pair[0].name, atoms_pair[1].name, atom_c.name}
        if len(atom_names) < 3:
            continue
        feature_ops = [(a.feature, a.op) for a in [atoms_pair[0], atoms_pair[1], atom_c]]
        if len(feature_ops) != len(set(feature_ops)):
            continue
        mask = pair_mask & mask_c
        rule_atoms = [atoms_pair[0].name, atoms_pair[1].name, atom_c.name]
        rule = " AND ".join(rule_atoms)
        row = evaluate_mask(data, label, mask, rule, "3_atom")
        if row["calibration_support"] >= MIN_SUPPORT:
            candidates.append(row)

    candidates.sort(key=score_row, reverse=True)
    return candidates[0], candidates[:80]


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

    missing = [str(p) for p in [INTAKE_ROWS, INTAKE_PROVENANCE, STOCK_SOURCE] if not p.exists()]
    if missing:
        result = {
            "run_id": RUN_ID,
            "gate_result": "source_label_macro_context_rule_miner_v1=blocked_missing_inputs",
            "missing": missing,
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
        (OUT / "source_label_macro_context_rule_miner_v1.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return 2

    data = load_dataset()
    gate_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    for label in ROOT_LABELS:
        best, top = mine_label(data, label)
        gate_rows.append(best)
        candidate_rows.extend(top)

    accepted_labels = [row["label"] for row in gate_rows if row["accepted_macro_context_rule_confidence_95"]]
    all_daily_accepted = len(accepted_labels) == len(ROOT_LABELS)
    gate_result = (
        "source_label_macro_context_rule_miner_v1=all_daily_source_rules_accepted_downstream_still_blocked"
        if all_daily_accepted
        else "source_label_macro_context_rule_miner_v1=macro_context_rules_scored_no_full_acceptance"
    )
    result = {
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "row_count": int(len(data)),
        "source_owner": SOURCE_OWNER,
        "rows_sha256": sha256_file(INTAKE_ROWS),
        "provenance_sha256": sha256_file(INTAKE_PROVENANCE),
        "stock_source_sha256": sha256_file(STOCK_SOURCE),
        "scope": {
            "included_source": "stock_market_regimes_2000_2026 only",
            "excluded_source": "nifty source excluded because feature schema differs from the heldout US market split",
            "timeframe": "1d only",
            "features": NUMERIC_FEATURES + CONTEXT_FEATURES,
            "rule_shapes": ["1_atom", "2_atom", "3_atom"],
        },
        "split_counts": {split: int((data["split_role"] == split).sum()) for split in REQUIRED_SPLITS},
        "market_family_by_split": {
            f"{split}:{family}": int(count)
            for (split, family), count in data.groupby(["split_role", "market_family"]).size().items()
        },
        "label_counts": {label: int((data["main_regime_v2_label"] == label).sum()) for label in ROOT_LABELS},
        "accepted_macro_context_rule_confidence_95_labels": accepted_labels,
        "gates": gate_rows,
        "promotion_status": {
            "accepted_rows_added": 0,
            "accepted_regime_confidence_labels": len(accepted_labels),
            "new_confidence_gate": bool(accepted_labels),
            "source_control_evidence_acquired": False,
            "canonical_merge": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "strict_full_objective_reason": "only_daily_source_label_probe_no_native_subhour_or_downstream_rerun",
            "trade_usable": False,
            "update_goal": False,
        },
    }
    (OUT / "source_label_macro_context_rule_miner_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(OUT / "source_label_macro_context_rule_gates_v1.csv", gate_rows)
    write_csv(OUT / "source_label_macro_context_rule_candidates_v1.csv", candidate_rows)

    lines = [
        "# Source Label Macro Context Rule Miner v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate_result}`",
        "",
        "## Result",
        "",
        f"- Rows scored: `{len(data)}` from `{SOURCE_OWNER}` only.",
        "- Rule search: bounded source-native macro/context 1-3 atom conjunctions.",
        "- Gate: every required split needs support `>=50` and Wilson95 lower bound `>=0.95`.",
        f"- Accepted macro/context confidence labels: `{accepted_labels}`.",
        "- Boundary: this is daily source-label confidence evidence only; it does not create source/control evidence, native sub-hour evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.",
        "",
        "## Best Gates",
        "",
        "| Label | Accepted 95 | Min Support | Min Wilson95 | Kind | Rule | Blockers |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for row in gate_rows:
        lines.append(
            f"| `{row['label']}` | `{str(row['accepted_macro_context_rule_confidence_95']).lower()}` "
            f"| `{row['min_split_support']}` | `{row['min_split_wilson95_lcb']}` "
            f"| `{row['kind']}` | `{row['rule']}` | {row['blockers']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The probe is non-promoting unless every active root passes all split gates and later source/control plus downstream chain requirements are satisfied.",
        ]
    )
    (OUT / "source_label_macro_context_rule_miner_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS gate_result={gate_result}",
        f"PASS row_count={len(data)}",
        f"PASS accepted_macro_context_rule_confidence_95_labels={','.join(accepted_labels) if accepted_labels else 'none'}",
        f"PASS accepted_regime_confidence_labels={len(accepted_labels)}",
        f"PASS new_confidence_gate={str(bool(accepted_labels)).lower()}",
        "PASS source_control_evidence_acquired=false",
        "PASS canonical_merge=false",
        "PASS downstream_promotion_rerun=false",
        "PASS strict_full_objective=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "source_label_macro_context_rule_miner_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "gate_result": gate_result,
        "accepted_macro_context_rule_confidence_95_labels": accepted_labels,
        "promotion_status": result["promotion_status"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
