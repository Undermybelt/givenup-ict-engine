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
RUN_ID = "20260511T040241+0800-codex-kaggle-bear-sideways-logodds-probe"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T040241-codex-kaggle-bear-sideways-logodds-probe"
OUT_DIR = RUN_ROOT / "kaggle-logodds-probe"
CHECK_DIR = RUN_ROOT / "checks"
SOURCE_FEATURE_TABLE = Path("/private/tmp/ict-regime-kaggle-regime-label-root/kaggle_regime_label_feature_table.csv")

ROOTS = ["Bear", "Sideways"]
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

Z95 = 1.959963984540054
TRAIN_SUPPORT_MIN = 500
TRAIN_COVERAGE_BUFFER_MIN = 0.035
SUPPORT_MIN = 250
COVERAGE_MIN = 0.03
ECE_MAX = 0.05
VALIDATION_INSTRUMENTS_MIN = 2
VALIDATION_MARKET_CONTEXTS_MIN = 2
VALIDATION_TIMEFRAMES_MIN = 2


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lcb(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 * 0.25 / total) / total)
    return max(0.0, (center - margin) / denom)


def split_metric(
    df: pd.DataFrame,
    mask: np.ndarray,
    y: np.ndarray,
    split_name: str,
    train_precision: float | None = None,
    include_validation: bool = True,
) -> dict[str, Any]:
    split_mask = df["split"].to_numpy() == split_name
    selected = mask & split_mask
    support = int(selected.sum())
    success = int((selected & y).sum())
    precision = success / support if support else 0.0
    reference = precision if train_precision is None else train_precision
    metric: dict[str, Any] = {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lcb(success, support),
        "coverage": support / int(split_mask.sum()) if int(split_mask.sum()) else 0.0,
        "ece": abs(reference - precision) if support else 0.0,
    }
    if include_validation:
        selected_df = df.loc[selected]
        metric["validation_instruments"] = sorted(selected_df["ticker"].dropna().astype(str).unique().tolist())
        metric["validation_market_contexts"] = sorted(selected_df["market_context"].dropna().astype(str).unique().tolist())
        metric["validation_timeframes"] = sorted(selected_df["timeframe"].dropna().astype(str).unique().tolist())
    return metric


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
    for split_name, metric in [("calibration", calibration), ("test", test)]:
        if len(metric["validation_instruments"]) < VALIDATION_INSTRUMENTS_MIN:
            out.append(f"{split_name}_validation_instruments_below_2")
        if len(metric["validation_market_contexts"]) < VALIDATION_MARKET_CONTEXTS_MIN:
            out.append(f"{split_name}_validation_market_contexts_below_2")
        if len(metric["validation_timeframes"]) < VALIDATION_TIMEFRAMES_MIN:
            out.append(f"{split_name}_validation_timeframes_below_2")
    return out


def train_only_scores(df: pd.DataFrame, root: str) -> tuple[np.ndarray, list[dict[str, Any]]]:
    train_mask = df["split"].eq("train").to_numpy()
    y = df["regime_label"].eq(root).to_numpy()
    prior = float((y & train_mask).sum() / train_mask.sum())
    prior_log_odds = math.log((prior + 1e-9) / (1.0 - prior + 1e-9))
    score = np.zeros(len(df), dtype=float)
    feature_report: list[dict[str, Any]] = []

    for feature in FEATURES:
        train_values = pd.to_numeric(df.loc[train_mask, feature], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna().to_numpy(float)
        if len(train_values) == 0:
            continue
        edges = np.unique(np.quantile(train_values, np.linspace(0.02, 0.98, 25)))
        median = float(np.nanmedian(train_values))
        values = pd.to_numeric(df[feature], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(median).to_numpy(float)
        codes = np.digitize(values, edges, right=False).astype(np.int16)
        total = np.bincount(codes[train_mask], minlength=int(codes.max()) + 1).astype(float)
        positive = np.bincount(codes[train_mask], weights=y[train_mask].astype(float), minlength=int(codes.max()) + 1).astype(float)
        p_bin = (positive + 5.0) / (total + 10.0)
        contribution = np.log(p_bin / (1.0 - p_bin)) - prior_log_odds
        score += contribution[codes]
        top_bins = np.argsort(contribution)[-3:][::-1]
        feature_report.append(
            {
                "feature": feature,
                "top_train_only_bins": [
                    {
                        "bin": int(idx),
                        "contribution": float(contribution[idx]),
                        "train_support": int(total[idx]),
                        "smoothed_precision": float(p_bin[idx]),
                    }
                    for idx in top_bins
                ],
            }
        )
    return score, feature_report


def evaluate_root(df: pd.DataFrame, root: str) -> dict[str, Any]:
    score, feature_report = train_only_scores(df, root)
    y = df["regime_label"].eq(root).to_numpy()
    train_mask = df["split"].eq("train").to_numpy()
    train_scores = score[train_mask]
    thresholds = np.unique(np.quantile(train_scores, np.linspace(0.01, 0.99, 197)))
    candidates: list[dict[str, Any]] = []
    for threshold in thresholds:
        for op in [">=", "<="]:
            mask = score >= threshold if op == ">=" else score <= threshold
            train = split_metric(df, mask, y, "train", include_validation=False)
            if train["support"] < TRAIN_SUPPORT_MIN or train["coverage"] < TRAIN_COVERAGE_BUFFER_MIN:
                continue
            candidates.append(
                {
                    "root_class": root,
                    "rule": f"train_only_quantile_log_odds_score_{root} {op} {threshold:.12g}",
                    "op": op,
                    "threshold": float(threshold),
                    "state": "train_selected_not_yet_evaluated",
                    "accepted_95": False,
                    "threshold_selected_on": "train_split_only",
                    "train": train,
                    "sort_key": [
                        train["precision_wilson_lcb_95"],
                        train["precision"],
                        train["coverage"],
                        train["support"],
                    ],
                }
            )
    candidates.sort(key=lambda item: item["sort_key"], reverse=True)
    if candidates:
        selected = dict(candidates[0])
        mask = score >= selected["threshold"] if selected["op"] == ">=" else score <= selected["threshold"]
        selected["train"] = split_metric(df, mask, y, "train")
        selected["calibration"] = split_metric(df, mask, y, "calibration", selected["train"]["precision"])
        selected["test"] = split_metric(df, mask, y, "test", selected["train"]["precision"])
        selected["blockers"] = blockers(selected["calibration"], selected["test"])
        selected["state"] = "accepted_95" if not selected["blockers"] else "blocked"
        selected["accepted_95"] = not selected["blockers"]
    else:
        selected = {
        "root_class": root,
        "rule": "no_train_candidate_with_min_support",
        "state": "blocked",
        "accepted_95": False,
        "threshold_selected_on": "train_split_only",
        "train": split_metric(df, np.zeros(len(df), dtype=bool), y, "train"),
        "calibration": split_metric(df, np.zeros(len(df), dtype=bool), y, "calibration"),
        "test": split_metric(df, np.zeros(len(df), dtype=bool), y, "test"),
        "blockers": ["no_train_candidate_with_min_support"],
        "sort_key": [0.0, 0.0, 0.0, 0],
        }
    selected["feature_report"] = feature_report
    selected["top_train_candidates"] = [
        {key: item[key] for key in ["rule", "train"]}
        for item in candidates[:20]
    ]
    selected.pop("op", None)
    selected.pop("threshold", None)
    selected.pop("sort_key", None)
    return selected


def write_summary(path: Path, root_reports: dict[str, dict[str, Any]]) -> None:
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
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for root, item in root_reports.items():
            writer.writerow(
                {
                    "root_class": root,
                    "state": item["state"],
                    "rule": item["rule"],
                    "train_support": item["train"]["support"],
                    "train_lcb": item["train"]["precision_wilson_lcb_95"],
                    "calibration_support": item["calibration"]["support"],
                    "calibration_lcb": item["calibration"]["precision_wilson_lcb_95"],
                    "test_support": item["test"]["support"],
                    "test_lcb": item["test"]["precision_wilson_lcb_95"],
                    "test_precision": item["test"]["precision"],
                    "test_coverage": item["test"]["coverage"],
                    "blockers": ";".join(item["blockers"]),
                }
            )


def write_report_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Kaggle Bear/Sideways Train-Only Log-Odds Probe",
        "",
        f"Run id: `{report['loop_id']}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{report['decision']['gate_result']}`",
        f"- Accepted new roots: {', '.join(report['decision']['accepted_new_roots_95']) or 'none'}",
        f"- Missing roots after preserved accounting: {', '.join(report['decision']['missing_root_classes_95_effective'])}",
        "- Thresholds relaxed: `false`",
        "- Runtime code changed: `false`",
        "",
        "## Root Results",
        "",
        "| Root | State | Rule | Cal LCB | Test LCB | Test Precision | Test Coverage | Blockers |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for root, item in report["root_reports"].items():
        lines.append(
            "| {root} | {state} | `{rule}` | {cal_lcb:.6f} | {test_lcb:.6f} | {test_precision:.6f} | {test_coverage:.6f} | {blockers} |".format(
                root=root,
                state=item["state"],
                rule=item["rule"],
                cal_lcb=item["calibration"]["precision_wilson_lcb_95"],
                test_lcb=item["test"]["precision_wilson_lcb_95"],
                test_precision=item["test"]["precision"],
                test_coverage=item["test"]["coverage"],
                blockers=", ".join(item["blockers"]) or "none",
            )
        )
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- Source `regime_label` is target-only.",
            "- Source `regime_confidence`, labels, identifiers, and `future_*` / `target_*` / `next_*` fields are not predictors.",
            "- Score bins and thresholds are selected on the train split only.",
            "- `Manipulation` is not evaluated here because Kaggle OHLCV/macro labels are not direct manipulation evidence.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    usecols = ["split", "regime_label", "ticker", "market_context", "timeframe"] + FEATURES
    df = pd.read_csv(SOURCE_FEATURE_TABLE, usecols=usecols)
    root_reports = {root: evaluate_root(df, root) for root in ROOTS}
    accepted = [root for root, item in root_reports.items() if item["accepted_95"]]
    retained_prior = ["Bull", "Crisis"]
    missing = [root for root in ["Bear", "Sideways", "Manipulation"] if root not in accepted]

    report_json = OUT_DIR / "kaggle_bear_sideways_logodds_probe_report.json"
    report_md = OUT_DIR / "kaggle_bear_sideways_logodds_probe_report.md"
    summary_csv = OUT_DIR / "kaggle_bear_sideways_logodds_probe_summary.csv"
    assertions = CHECK_DIR / "kaggle_bear_sideways_logodds_probe_assertions.out"
    report = {
        "loop_id": RUN_ID,
        "objective": "Train-only quantile log-odds factor probe for missing MainRegimeV2 Bear and Sideways roots using existing Kaggle direct-label table.",
        "source": {
            "feature_table_tmp_path": str(SOURCE_FEATURE_TABLE),
            "raw_or_full_feature_table_committed": False,
        },
        "feature_policy": {
            "candidate_features": FEATURES,
            "source_label_used_only_as_target": True,
            "source_regime_confidence_blocked_as_predictor": True,
            "blocked_future_target_next_predictors": True,
            "thresholds_selected_on": "train_split_only",
            "runtime_code_changed": False,
        },
        "acceptance_95": {
            "precision_wilson_lcb_95_min": 0.95,
            "support_min": SUPPORT_MIN,
            "coverage_min": COVERAGE_MIN,
            "ece_max": ECE_MAX,
            "validation_instruments_min": VALIDATION_INSTRUMENTS_MIN,
            "validation_market_contexts_min": VALIDATION_MARKET_CONTEXTS_MIN,
            "validation_timeframes_min": VALIDATION_TIMEFRAMES_MIN,
        },
        "root_reports": root_reports,
        "decision": {
            "gate_result": "accepted_95" if accepted else "blocked_kaggle_bear_sideways_logodds_below_95",
            "accepted_new_roots_95": accepted,
            "retained_prior_accepted_root_classes_95": retained_prior,
            "accepted_root_classes_95_effective": retained_prior + accepted,
            "missing_root_classes_95_effective": missing,
            "manipulation_evaluated": False,
            "manipulation_blocker": "Kaggle OHLCV/macro regime labels are not direct event/order-lifecycle/L2/L3/MBO/social/on-chain manipulation evidence.",
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "fresh_calibration_rerun": True,
            "trade_usable": False,
            "next_action": "Stop repeating Kaggle OHLCV/macro transformations for Bear/Sideways; acquire materially stronger parent-labeled bear/sideways regime-cycle evidence, and keep Manipulation on direct-event evidence only.",
        },
        "artifacts": {
            "report_json": repo_rel(report_json),
            "report_md": repo_rel(report_md),
            "summary_csv": repo_rel(summary_csv),
            "assertions": repo_rel(assertions),
        },
    }
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_summary(summary_csv, root_reports)
    write_report_md(report_md, report)
    assertion_lines = [
        f"loop_id={RUN_ID}",
        f"gate_result={report['decision']['gate_result']}",
        f"accepted_new_roots_95={','.join(accepted) if accepted else 'none'}",
        "thresholds_relaxed=false",
        "runtime_code_changed=false",
        "raw_or_full_feature_table_committed=false",
    ]
    for root, item in root_reports.items():
        assertion_lines.append(
            f"{root}:state={item['state']}:cal_lcb={item['calibration']['precision_wilson_lcb_95']:.6f}:test_lcb={item['test']['precision_wilson_lcb_95']:.6f}:test_precision={item['test']['precision']:.6f}:test_coverage={item['test']['coverage']:.6f}"
        )
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
