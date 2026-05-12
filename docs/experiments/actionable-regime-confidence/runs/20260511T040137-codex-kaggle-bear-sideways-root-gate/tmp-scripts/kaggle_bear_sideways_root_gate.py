#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T040137+0800-codex-kaggle-bear-sideways-root-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T040137-codex-kaggle-bear-sideways-root-gate"
OUT_DIR = RUN_ROOT / "kaggle-bear-sideways-gate"
CHECK_DIR = RUN_ROOT / "checks"
SOURCE_FEATURE_TABLE = Path("/private/tmp/ict-regime-kaggle-regime-label-root/kaggle_regime_label_feature_table.csv")
SOURCE_REPORT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T033017-codex-kaggle-regime-label-root-gate/kaggle-regime-gate/kaggle_regime_label_root_gate_report.json"
PRIOR_BULL_REPORT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T035045-codex-kaggle-bull-coverage-buffer-gate/kaggle-bull-gate/kaggle_bull_coverage_buffer_gate_report.json"

ROOTS = ["Bear", "Sideways"]
Z95 = 1.959963984540054
TRAIN_SUPPORT_MIN = 500
TRAIN_COVERAGE_BUFFER_MIN = 0.045
SUPPORT_MIN = 250
COVERAGE_MIN = 0.03
ECE_MAX = 0.05
VALIDATION_INSTRUMENTS_MIN = 2
VALIDATION_MARKET_CONTEXTS_MIN = 2
VALIDATION_TIMEFRAMES_MIN = 2
QUANTILES = (
    0.005,
    0.01,
    0.02,
    0.03,
    0.04,
    0.05,
    0.075,
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
    0.925,
    0.95,
    0.96,
    0.97,
    0.98,
    0.99,
    0.995,
)
ID_COLUMNS = {
    "date",
    "ticker",
    "timeframe",
    "context",
    "market_context",
    "split",
    "regime_label",
}
BLOCKED_PREFIXES = ("future_", "target_", "next_")


@dataclass(frozen=True)
class Candidate:
    method: str
    rule: str
    mask: np.ndarray


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def numeric_array(series: pd.Series) -> np.ndarray:
    values = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).to_numpy(dtype=float)
    return values


def wilson_lcb(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 * 0.25 / total) / total)
    return max(0.0, (center - margin) / denom)


def build_arrays(df: pd.DataFrame) -> dict[str, np.ndarray]:
    return {
        "split": df["split"].astype(str).to_numpy(),
        "label": df["regime_label"].astype(str).to_numpy(),
        "ticker": df["ticker"].astype(str).to_numpy(),
        "market_context": df["market_context"].astype(str).to_numpy(),
        "timeframe": df["timeframe"].astype(str).to_numpy(),
        "context": df["context"].astype(str).to_numpy(),
    }


def unique_selected(values: np.ndarray, mask: np.ndarray) -> list[str]:
    if not bool(mask.any()):
        return []
    return sorted(np.unique(values[mask]).tolist())


def metric(
    arrays: dict[str, np.ndarray],
    mask: np.ndarray,
    root: str,
    split: str,
    train_precision: float | None = None,
    include_validation: bool = False,
) -> dict[str, Any]:
    split_mask = arrays["split"] == split
    chosen = mask & split_mask
    support = int(chosen.sum())
    success = int(((arrays["label"] == root) & chosen).sum()) if support else 0
    precision = success / support if support else 0.0
    split_total = int(split_mask.sum())
    reference = train_precision if train_precision is not None else precision
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lcb(success, support),
        "coverage": support / split_total if split_total else 0.0,
        "ece": abs(reference - precision) if support else 0.0,
        "validation_instruments": unique_selected(arrays["ticker"], chosen) if include_validation else [],
        "validation_market_contexts": unique_selected(arrays["market_context"], chosen) if include_validation else [],
        "validation_timeframes": unique_selected(arrays["timeframe"], chosen) if include_validation else [],
        "validation_contexts": unique_selected(arrays["context"], chosen) if include_validation else [],
    }


def train_key(arrays: dict[str, np.ndarray], candidate: Candidate, root: str) -> tuple[float, float, float, int]:
    m = metric(arrays, candidate.mask, root, "train")
    return (m["precision_wilson_lcb_95"], m["precision"], m["coverage"], m["support"])


def blockers(calibration: dict[str, Any], test: dict[str, Any]) -> list[str]:
    out: list[str] = []
    if calibration["support"] < SUPPORT_MIN:
        out.append("calibration_support_below_250")
    if test["support"] < SUPPORT_MIN:
        out.append("test_support_below_250")
    if calibration["precision_wilson_lcb_95"] < 0.95:
        out.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < 0.95:
        out.append("test_wilson95_below_0_95")
    if calibration["coverage"] < COVERAGE_MIN:
        out.append("calibration_coverage_below_0_03")
    if test["coverage"] < COVERAGE_MIN:
        out.append("test_coverage_below_0_03")
    if max(calibration["ece"], test["ece"]) > ECE_MAX:
        out.append("ece_above_0_05")
    for split_name, data in [("calibration", calibration), ("test", test)]:
        if len(data["validation_instruments"]) < VALIDATION_INSTRUMENTS_MIN:
            out.append(f"{split_name}_validation_instruments_below_2")
        if len(data["validation_market_contexts"]) < VALIDATION_MARKET_CONTEXTS_MIN:
            out.append(f"{split_name}_validation_market_contexts_below_2")
        if len(data["validation_timeframes"]) < VALIDATION_TIMEFRAMES_MIN:
            out.append(f"{split_name}_validation_timeframes_below_2")
    return out


def numeric_feature_names(df: pd.DataFrame) -> list[str]:
    out: list[str] = []
    for column in df.columns:
        if column in ID_COLUMNS or column == "macro_context":
            continue
        if column.startswith(BLOCKED_PREFIXES):
            continue
        values = pd.to_numeric(df[column], errors="coerce")
        if values.notna().sum() >= 1000 and values.nunique(dropna=True) > 4:
            out.append(column)
    return out


def atom_candidates(df: pd.DataFrame, arrays: dict[str, np.ndarray], root: str) -> list[Candidate]:
    train = arrays["split"] == "train"
    atoms: list[tuple[tuple[float, float, float, int], Candidate]] = []

    for feature in numeric_feature_names(df):
        values = numeric_array(df[feature])
        finite = np.isfinite(values)
        train_values = values[train & finite]
        if len(train_values) < TRAIN_SUPPORT_MIN:
            continue
        for quantile in QUANTILES:
            threshold = float(np.nanquantile(train_values, quantile))
            if not math.isfinite(threshold):
                continue
            for op in (">=", "<="):
                mask = finite & ((values >= threshold) if op == ">=" else (values <= threshold))
                candidate = Candidate("numeric_atom", f"{feature} {op} {threshold:.12g}", mask)
                key = train_key(arrays, candidate, root)
                if key[3] >= TRAIN_SUPPORT_MIN and key[2] >= TRAIN_COVERAGE_BUFFER_MIN:
                    atoms.append((key, candidate))

    train_macro_counts = df.loc[df["split"].eq("train"), "macro_context"].dropna().astype(str).value_counts()
    for macro_value, count in train_macro_counts.items():
        if int(count) < TRAIN_SUPPORT_MIN:
            continue
        mask = df["macro_context"].astype(str).eq(macro_value).to_numpy()
        candidate = Candidate("macro_context_atom", f"macro_context == {macro_value!r}", mask)
        key = train_key(arrays, candidate, root)
        if key[3] >= TRAIN_SUPPORT_MIN and key[2] >= TRAIN_COVERAGE_BUFFER_MIN:
            atoms.append((key, candidate))

    atoms.sort(key=lambda item: item[0], reverse=True)
    return [candidate for _, candidate in atoms[:80]]


def run_root(df: pd.DataFrame, arrays: dict[str, np.ndarray], root: str) -> dict[str, Any]:
    atoms = atom_candidates(df, arrays, root)
    best: tuple[tuple[float, float, float, int], Candidate] | None = None

    def consider(candidate: Candidate) -> None:
        nonlocal best
        key = train_key(arrays, candidate, root)
        if key[3] < TRAIN_SUPPORT_MIN or key[2] < TRAIN_COVERAGE_BUFFER_MIN:
            return
        if best is None or key > best[0]:
            best = (key, candidate)

    for candidate in atoms[:60]:
        consider(candidate)
    for i, left in enumerate(atoms[:40]):
        for right in atoms[i + 1 : 40]:
            if left.rule.split()[0] == right.rule.split()[0]:
                continue
            consider(Candidate("rule_pair", f"{left.rule} AND {right.rule}", left.mask & right.mask))
    for i, left in enumerate(atoms[:14]):
        for j, mid in enumerate(atoms[i + 1 : 14], start=i + 1):
            for right in atoms[j + 1 : 14]:
                feature_names = {left.rule.split()[0], mid.rule.split()[0], right.rule.split()[0]}
                if len(feature_names) < 3:
                    continue
                consider(
                    Candidate(
                        "rule_triple",
                        f"{left.rule} AND {mid.rule} AND {right.rule}",
                        left.mask & mid.mask & right.mask,
                    )
                )

    if best is None:
        selected = Candidate("none", "no_train_candidate_with_min_support_and_coverage", np.zeros(len(df), dtype=bool))
        train = metric(arrays, selected.mask, root, "train")
    else:
        selected = best[1]
        train = metric(arrays, selected.mask, root, "train")
    calibration = metric(arrays, selected.mask, root, "calibration", train["precision"], include_validation=True)
    test = metric(arrays, selected.mask, root, "test", train["precision"], include_validation=True)
    block = blockers(calibration, test)
    return {
        "root_class": root,
        "state": "accepted_95" if not block else "blocked",
        "method": selected.method,
        "rule": selected.rule,
        "accepted_95": not block,
        "train": train,
        "calibration": calibration,
        "test": test,
        "blockers": block,
    }


def write_summary(path: Path, root_reports: list[dict[str, Any]]) -> None:
    fields = [
        "root_class",
        "state",
        "method",
        "rule",
        "train_support",
        "train_lcb",
        "calibration_support",
        "calibration_lcb",
        "calibration_coverage",
        "test_support",
        "test_lcb",
        "test_precision",
        "test_coverage",
        "blockers",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for item in root_reports:
            writer.writerow(
                {
                    "root_class": item["root_class"],
                    "state": item["state"],
                    "method": item["method"],
                    "rule": item["rule"],
                    "train_support": item["train"]["support"],
                    "train_lcb": item["train"]["precision_wilson_lcb_95"],
                    "calibration_support": item["calibration"]["support"],
                    "calibration_lcb": item["calibration"]["precision_wilson_lcb_95"],
                    "calibration_coverage": item["calibration"]["coverage"],
                    "test_support": item["test"]["support"],
                    "test_lcb": item["test"]["precision_wilson_lcb_95"],
                    "test_precision": item["test"]["precision"],
                    "test_coverage": item["test"]["coverage"],
                    "blockers": ";".join(item["blockers"]),
                }
            )


def write_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Kaggle Bear/Sideways MainRegimeV2 Root Gate",
        "",
        f"Run id: `{report['loop_id']}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{report['decision']['gate_result']}`",
        f"- Accepted new roots: {', '.join(report['decision']['accepted_new_roots_95']) or 'none'}",
        f"- Effective accepted roots: {', '.join(report['decision']['accepted_root_classes_95_effective'])}",
        f"- Missing roots: {', '.join(report['decision']['missing_root_classes_95_effective'])}",
        "",
        "## Results",
        "",
        "| Root | State | Rule | Cal support | Cal LCB | Test support | Test LCB | Test precision | Blockers |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in report["root_reports"]:
        lines.append(
            "| {root} | {state} | `{rule}` | {cal_support} | {cal_lcb:.6f} | {test_support} | {test_lcb:.6f} | {test_precision:.6f} | {blockers} |".format(
                root=item["root_class"],
                state=item["state"],
                rule=item["rule"],
                cal_support=item["calibration"]["support"],
                cal_lcb=item["calibration"]["precision_wilson_lcb_95"],
                test_support=item["test"]["support"],
                test_lcb=item["test"]["precision_wilson_lcb_95"],
                test_precision=item["test"]["precision"],
                blockers=", ".join(item["blockers"]) or "none",
            )
        )
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- Thresholds were selected on the train split only.",
            "- The train selector required a coverage buffer of at least 0.045 before held-out calibration/test checks.",
            "- `regime_label` was used only as the target label; `future_*`, `target_*`, and `next_*` predictors stayed blocked.",
            "- Raw provider data and the full feature table stayed under `/private/tmp`.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    if not SOURCE_FEATURE_TABLE.exists():
        raise FileNotFoundError(f"missing source feature table: {SOURCE_FEATURE_TABLE}")
    df = pd.read_csv(SOURCE_FEATURE_TABLE, parse_dates=["date"])
    arrays = build_arrays(df)
    root_reports = [run_root(df, arrays, root) for root in ROOTS]
    accepted = [item["root_class"] for item in root_reports if item["accepted_95"]]
    effective = ["Bull", "Crisis"] + [root for root in ROOTS if root in accepted]
    missing = [root for root in ["Bear", "Sideways", "Manipulation"] if root not in accepted]
    gate_result = "accepted_kaggle_bear_sideways_95" if set(ROOTS).issubset(set(accepted)) else "blocked_kaggle_bear_sideways_root_gate_below_95"

    report_json = OUT_DIR / "kaggle_bear_sideways_root_gate_report.json"
    report_md = OUT_DIR / "kaggle_bear_sideways_root_gate_report.md"
    summary_csv = OUT_DIR / "kaggle_bear_sideways_root_gate_summary.csv"
    assertions = CHECK_DIR / "kaggle_bear_sideways_root_gate_assertions.out"
    report = {
        "loop_id": RUN_ID,
        "objective": "Kaggle direct-label MainRegimeV2 Bear and Sideways root gate with train-only coverage-buffer rule selection.",
        "source": {
            "feature_table_tmp_path": str(SOURCE_FEATURE_TABLE),
            "source_report": repo_rel(SOURCE_REPORT),
            "prior_bull_report": repo_rel(PRIOR_BULL_REPORT),
            "raw_or_full_feature_table_committed": False,
        },
        "selection_policy": {
            "root_classes": ROOTS,
            "thresholds_selected_on": "train_split_only",
            "train_support_min": TRAIN_SUPPORT_MIN,
            "train_coverage_buffer_min": TRAIN_COVERAGE_BUFFER_MIN,
            "blocked_future_target_next_predictors": True,
            "source_label_used_only_as_target": True,
            "feature_families": ["numeric_market_macro_features", "macro_context_category_atoms"],
        },
        "threshold_policy": {
            "precision_wilson_lcb_95_min": 0.95,
            "support_min": SUPPORT_MIN,
            "coverage_min": COVERAGE_MIN,
            "ece_max": ECE_MAX,
            "validation_instruments_min": VALIDATION_INSTRUMENTS_MIN,
            "validation_market_contexts_min": VALIDATION_MARKET_CONTEXTS_MIN,
            "validation_timeframes_min": VALIDATION_TIMEFRAMES_MIN,
        },
        "row_count": int(len(df)),
        "split_counts": df["split"].value_counts().to_dict(),
        "label_counts": df["regime_label"].value_counts().to_dict(),
        "context_counts": {
            "instruments": int(df["ticker"].nunique()),
            "market_contexts": sorted(df["market_context"].dropna().astype(str).unique().tolist()),
            "timeframes": sorted(df["timeframe"].dropna().astype(str).unique().tolist()),
            "contexts": int(df["context"].nunique()),
        },
        "root_reports": root_reports,
        "decision": {
            "gate_result": gate_result,
            "accepted_new_roots_95": accepted,
            "retained_prior_accepted_root_classes_95": ["Bull", "Crisis"],
            "accepted_root_classes_95_effective": effective,
            "missing_root_classes_95_effective": missing,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "fresh_calibration_rerun": True,
            "trade_usable": False,
            "next_action": "Continue MainRegimeV2 root gates for any missing Bear/Sideways root; keep Manipulation blocked until direct event/order-lifecycle labels exist.",
        },
        "artifacts": {
            "report_json": repo_rel(report_json),
            "report_md": repo_rel(report_md),
            "summary_csv": repo_rel(summary_csv),
            "assertions": repo_rel(assertions),
        },
    }
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_md(report_md, report)
    write_summary(summary_csv, root_reports)
    assertion_lines = [
        f"loop_id={RUN_ID}",
        f"gate_result={gate_result}",
        f"accepted_new_roots_95={','.join(accepted) if accepted else 'none'}",
        f"missing_root_classes_95_effective={','.join(missing) if missing else 'none'}",
        f"thresholds_relaxed={str(report['decision']['thresholds_relaxed']).lower()}",
        f"runtime_code_changed={str(report['decision']['runtime_code_changed']).lower()}",
        "raw_or_full_feature_table_committed=false",
    ]
    for item in root_reports:
        assertion_lines.append(
            "{root}:cal_lcb={cal_lcb:.6f}:test_lcb={test_lcb:.6f}:accepted={accepted}:blockers={blockers}".format(
                root=item["root_class"],
                cal_lcb=item["calibration"]["precision_wilson_lcb_95"],
                test_lcb=item["test"]["precision_wilson_lcb_95"],
                accepted=str(item["accepted_95"]).lower(),
                blockers=",".join(item["blockers"]),
            )
        )
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
