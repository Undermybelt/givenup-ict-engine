#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T035045+0800-codex-kaggle-bull-coverage-buffer-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T035045-codex-kaggle-bull-coverage-buffer-gate"
OUT_DIR = RUN_ROOT / "kaggle-bull-gate"
CHECK_DIR = RUN_ROOT / "checks"
SOURCE_FEATURE_TABLE = Path("/private/tmp/ict-regime-kaggle-regime-label-root/kaggle_regime_label_feature_table.csv")
SOURCE_REPORT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T033017-codex-kaggle-regime-label-root-gate/kaggle-regime-gate/kaggle_regime_label_root_gate_report.json"

ROOT = "Bull"
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
)
FEATURES = [
    "10y_treasury",
    "2y_treasury",
    "close",
    "close_drawdown60",
    "cpi",
    "fed_funds_rate",
    "real_rate_proxy",
    "ret1_lag1",
    "ret20",
    "ret5",
    "returns",
    "unemployment_rate",
    "vix",
    "vol20_mean",
    "vol60_z",
    "volatility",
    "yield_curve_10y_2y",
]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)


def wilson_lcb(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 * 0.25 / total) / total)
    return max(0.0, (center - margin) / denom)


Rule = list[tuple[str, str, float]]


def format_rule(rule: Rule) -> str:
    return " AND ".join(f"{feature} {op} {value:.12g}" for feature, op, value in rule)


def rule_mask(df: pd.DataFrame, rule: Rule) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for feature, op, value in rule:
        values = numeric(df[feature])
        if op == ">=":
            mask &= values >= value
        elif op == "<=":
            mask &= values <= value
        else:
            raise ValueError(op)
    return mask.fillna(False)


def metric(df: pd.DataFrame, mask: pd.Series, split: str, train_precision: float | None = None) -> dict[str, Any]:
    split_mask = df["split"].eq(split)
    selected = df[split_mask & mask]
    support = int(len(selected))
    success = int(selected["regime_label"].eq(ROOT).sum()) if support else 0
    precision = success / support if support else 0.0
    total_split = int(split_mask.sum())
    reference = train_precision if train_precision is not None else precision
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lcb(success, support),
        "coverage": support / total_split if total_split else 0.0,
        "ece": abs(reference - precision) if support else 0.0,
        "validation_instruments": sorted(selected["ticker"].dropna().astype(str).unique().tolist()),
        "validation_market_contexts": sorted(selected["market_context"].dropna().astype(str).unique().tolist()),
        "validation_timeframes": sorted(selected["timeframe"].dropna().astype(str).unique().tolist()),
        "validation_contexts": sorted(selected["context"].dropna().astype(str).unique().tolist()),
    }


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


def train_candidates(df: pd.DataFrame) -> list[tuple[float, float, float, int, Rule, dict[str, Any]]]:
    train = df[df["split"].eq("train")]
    singles: list[tuple[float, float, float, int, Rule, dict[str, Any]]] = []
    for feature in FEATURES:
        values = numeric(train[feature]).dropna()
        if values.nunique() <= 4:
            continue
        for quantile in QUANTILES:
            threshold = float(values.quantile(quantile))
            if not math.isfinite(threshold):
                continue
            for op in [">=", "<="]:
                rule = [(feature, op, threshold)]
                m = metric(df, rule_mask(df, rule), "train")
                if m["support"] >= TRAIN_SUPPORT_MIN and m["coverage"] >= TRAIN_COVERAGE_BUFFER_MIN:
                    singles.append((m["precision_wilson_lcb_95"], m["precision"], m["coverage"], m["support"], rule, m))
    singles.sort(key=lambda item: item[:4], reverse=True)
    candidates = list(singles)
    for index, (_, _, _, _, left, _) in enumerate(singles[:40]):
        for _, _, _, _, right, _ in singles[index + 1 : 40]:
            if left[0][0] == right[0][0]:
                continue
            rule = left + right
            m = metric(df, rule_mask(df, rule), "train")
            if m["support"] >= TRAIN_SUPPORT_MIN and m["coverage"] >= TRAIN_COVERAGE_BUFFER_MIN:
                candidates.append((m["precision_wilson_lcb_95"], m["precision"], m["coverage"], m["support"], rule, m))
    candidates.sort(key=lambda item: item[:4], reverse=True)
    return candidates


def write_summary(path: Path, report: dict[str, Any]) -> None:
    fields = [
        "root_class",
        "state",
        "rule",
        "train_support",
        "train_lcb",
        "calibration_support",
        "calibration_lcb",
        "test_support",
        "test_lcb",
        "test_precision",
        "test_coverage",
        "blockers",
    ]
    row = {
        "root_class": ROOT,
        "state": report["state"],
        "rule": report["rule"],
        "train_support": report["train"]["support"],
        "train_lcb": report["train"]["precision_wilson_lcb_95"],
        "calibration_support": report["calibration"]["support"],
        "calibration_lcb": report["calibration"]["precision_wilson_lcb_95"],
        "test_support": report["test"]["support"],
        "test_lcb": report["test"]["precision_wilson_lcb_95"],
        "test_precision": report["test"]["precision"],
        "test_coverage": report["test"]["coverage"],
        "blockers": ";".join(report["blockers"]),
    }
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    if not SOURCE_FEATURE_TABLE.exists():
        raise FileNotFoundError(f"missing source feature table: {SOURCE_FEATURE_TABLE}")
    df = pd.read_csv(SOURCE_FEATURE_TABLE, parse_dates=["date"])
    candidates = train_candidates(df)
    if not candidates:
        raise RuntimeError("no train candidate met the predeclared support/coverage buffer")
    _, _, _, _, selected_rule, train = candidates[0]
    mask = rule_mask(df, selected_rule)
    calibration = metric(df, mask, "calibration", train["precision"])
    test = metric(df, mask, "test", train["precision"])
    block = blockers(calibration, test)
    report = {
        "loop_id": RUN_ID,
        "objective": "Kaggle direct-label MainRegimeV2 Bull root gate with train-only coverage-buffer rule selection.",
        "source": {
            "feature_table_tmp_path": str(SOURCE_FEATURE_TABLE),
            "source_report": repo_rel(SOURCE_REPORT),
            "raw_or_full_feature_table_committed": False,
        },
        "selection_policy": {
            "root_class": ROOT,
            "thresholds_selected_on": "train_split_only",
            "train_support_min": TRAIN_SUPPORT_MIN,
            "train_coverage_buffer_min": TRAIN_COVERAGE_BUFFER_MIN,
            "candidate_count": len(candidates),
            "blocked_future_target_next_predictors": True,
            "source_label_used_only_as_target": True,
        },
        "rule": format_rule(selected_rule),
        "state": "accepted_95" if not block else "blocked",
        "accepted_95": not block,
        "train": train,
        "calibration": calibration,
        "test": test,
        "blockers": block,
        "decision": {
            "accepted_new_roots_95": [ROOT] if not block else [],
            "retained_prior_accepted_root_classes_95": ["Crisis"],
            "accepted_root_classes_95_effective": ["Bull", "Crisis"] if not block else ["Crisis"],
            "missing_root_classes_95_effective": ["Bear", "Sideways", "Manipulation"] if not block else ["Bull", "Bear", "Sideways", "Manipulation"],
            "gate_result": "accepted_bull_95" if not block else "blocked_kaggle_bull_coverage_buffer_gate",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "fresh_calibration_rerun": True,
            "trade_usable": False,
            "next_action": "Continue MainRegimeV2 root gates for Bear and Sideways; keep Manipulation blocked until direct event/order-lifecycle labels exist.",
        },
    }
    report_json = OUT_DIR / "kaggle_bull_coverage_buffer_gate_report.json"
    report_md = OUT_DIR / "kaggle_bull_coverage_buffer_gate_report.md"
    summary_csv = OUT_DIR / "kaggle_bull_coverage_buffer_gate_summary.csv"
    assertions = CHECK_DIR / "kaggle_bull_coverage_buffer_gate_assertions.out"
    report["artifacts"] = {
        "report_json": repo_rel(report_json),
        "report_md": repo_rel(report_md),
        "summary_csv": repo_rel(summary_csv),
        "assertions": repo_rel(assertions),
    }
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Kaggle Bull Coverage-Buffer Gate",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{report['decision']['gate_result']}`",
        f"- Accepted 95 `Bull`: `{str(report['accepted_95']).lower()}`",
        f"- Rule: `{report['rule']}`",
        f"- Calibration Wilson95 LCB / coverage: `{calibration['precision_wilson_lcb_95']:.6f}` / `{calibration['coverage']:.6f}`",
        f"- Test Wilson95 LCB / coverage: `{test['precision_wilson_lcb_95']:.6f}` / `{test['coverage']:.6f}`",
        f"- Blockers: {', '.join(block) or 'none'}",
        "",
        "## Policy",
        "",
        "- Thresholds were selected on the train split only.",
        "- The train selector required a coverage buffer of at least 0.045 before held-out calibration/test checks.",
        "- Source `regime_label` was used only as the target label; source confidence and future/target/next predictors stayed blocked.",
        "- Raw provider data and the full feature table stayed under `/private/tmp`.",
    ]
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_summary(summary_csv, report)
    assertion_lines = [
        f"loop_id={RUN_ID}",
        f"root={ROOT}",
        f"rule={report['rule']}",
        f"accepted_95={str(report['accepted_95']).lower()}",
        f"gate_result={report['decision']['gate_result']}",
        f"train_support={train['support']}",
        f"train_lcb={train['precision_wilson_lcb_95']:.6f}",
        f"calibration_support={calibration['support']}",
        f"calibration_lcb={calibration['precision_wilson_lcb_95']:.6f}",
        f"calibration_coverage={calibration['coverage']:.6f}",
        f"test_support={test['support']}",
        f"test_lcb={test['precision_wilson_lcb_95']:.6f}",
        f"test_coverage={test['coverage']:.6f}",
        f"thresholds_relaxed={str(report['decision']['thresholds_relaxed']).lower()}",
        f"runtime_code_changed={str(report['decision']['runtime_code_changed']).lower()}",
        f"raw_or_full_feature_table_committed=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
