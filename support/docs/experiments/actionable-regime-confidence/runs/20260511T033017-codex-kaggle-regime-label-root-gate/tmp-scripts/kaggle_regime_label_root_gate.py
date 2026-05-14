#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import math
import zipfile
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T033017+0800-codex-kaggle-regime-label-root-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T033017-codex-kaggle-regime-label-root-gate"
OUT_DIR = RUN_ROOT / "kaggle-regime-gate"
CHECK_DIR = RUN_ROOT / "checks"
TMP_RAW_DIR = Path("/private/tmp/ict-regime-kaggle-regime-label-root")
KAGGLE_URL = "https://www.kaggle.com/api/v1/datasets/download/mafaqbhatti/stock-market-regimes-20002026"
RAW_ZIP = TMP_RAW_DIR / "stock-market-regimes-20002026.zip"
FEATURE_TABLE = TMP_RAW_DIR / "kaggle_regime_label_feature_table.csv"

ROOTS = ["Bull", "Bear", "Sideways"]
Z95 = 1.959963984540054
QUANTILES = (0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95)
SUPPORT_TRAIN_MIN = 500
SUPPORT_CAL_MIN = 250
SUPPORT_TEST_MIN = 250
COVERAGE_MIN = 0.03
ECE_MAX = 0.05
VALIDATION_INSTRUMENTS_MIN = 5
VALIDATION_TIMEFRAMES_MIN = 2


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype(float).replace([np.inf, -np.inf], np.nan)
    return pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)


def wilson_lcb(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 * 0.25 / total) / total)
    return max(0.0, (center - margin) / denom)


def json_counts(series: pd.Series) -> dict[str, int]:
    out: dict[str, int] = {}
    for key, value in series.items():
        label = "|".join(str(part) for part in key) if isinstance(key, tuple) else str(key)
        out[label] = int(value)
    return out


def download_source() -> dict[str, Any]:
    TMP_RAW_DIR.mkdir(parents=True, exist_ok=True)
    if not RAW_ZIP.exists():
        req = Request(KAGGLE_URL, headers={"User-Agent": "Mozilla/5.0"})
        RAW_ZIP.write_bytes(urlopen(req, timeout=180).read())
    with zipfile.ZipFile(RAW_ZIP) as archive:
        members = {name: archive.getinfo(name).file_size for name in archive.namelist()}
        summary = archive.read("dataset_summary.txt").decode("utf-8", "replace") if "dataset_summary.txt" in members else ""
    return {
        "source_url": KAGGLE_URL,
        "raw_zip_path": str(RAW_ZIP),
        "raw_zip_bytes": RAW_ZIP.stat().st_size,
        "members": members,
        "dataset_summary_excerpt": summary[:1200],
        "raw_provider_files_committed": False,
    }


def read_source_csv() -> pd.DataFrame:
    with zipfile.ZipFile(RAW_ZIP) as archive:
        with archive.open("stock_market_regimes_2000_2026.csv") as fh:
            df = pd.read_csv(fh)
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True).dt.normalize()
    df = df.dropna(subset=["date", "ticker", "regime_label"]).copy()
    df["ticker"] = df["ticker"].astype(str)
    df["regime_label"] = df["regime_label"].astype(str)
    for col in ["close", "returns", "volatility", "regime_confidence", "unemployment_rate", "fed_funds_rate", "cpi", "10y_treasury", "2y_treasury", "vix"]:
        if col in df.columns:
            df[col] = numeric(df[col])
    return df.sort_values(["ticker", "date"]).reset_index(drop=True)


def add_daily_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["timeframe"] = "1d"
    grp = out.groupby("ticker", group_keys=False)
    out["ret1_lag1"] = grp["returns"].shift(1)
    out["ret5"] = grp["returns"].rolling(5, min_periods=3).sum().reset_index(level=0, drop=True)
    out["ret20"] = grp["returns"].rolling(20, min_periods=8).sum().reset_index(level=0, drop=True)
    out["vol20_mean"] = grp["volatility"].rolling(20, min_periods=8).mean().reset_index(level=0, drop=True)
    out["vol60_z"] = (
        (out["volatility"] - grp["volatility"].rolling(60, min_periods=20).mean().reset_index(level=0, drop=True))
        / grp["volatility"].rolling(60, min_periods=20).std().reset_index(level=0, drop=True).replace(0, np.nan)
    )
    out["close_drawdown60"] = out["close"] / grp["close"].rolling(60, min_periods=20).max().reset_index(level=0, drop=True) - 1.0
    return out


def weekly_label(values: pd.Series) -> str:
    counts = values.value_counts()
    return str(counts.index[0]) if len(counts) else "UnknownOrMixed"


def add_weekly_view(daily: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for ticker, group in daily.groupby("ticker", sort=False):
        g = group.set_index("date").sort_index()
        agg = pd.DataFrame(
            {
                "ticker": ticker,
                "close": g["close"].resample("W-FRI").last(),
                "returns": g["returns"].resample("W-FRI").sum(),
                "volatility": g["volatility"].resample("W-FRI").mean(),
                "regime_label": g["regime_label"].resample("W-FRI").apply(weekly_label),
                "macro_context": g["macro_context"].resample("W-FRI").last(),
                "unemployment_rate": g["unemployment_rate"].resample("W-FRI").last(),
                "fed_funds_rate": g["fed_funds_rate"].resample("W-FRI").last(),
                "cpi": g["cpi"].resample("W-FRI").last(),
                "10y_treasury": g["10y_treasury"].resample("W-FRI").last(),
                "2y_treasury": g["2y_treasury"].resample("W-FRI").last(),
                "vix": g["vix"].resample("W-FRI").last(),
            }
        ).dropna(subset=["close", "regime_label"])
        agg = agg.reset_index()
        rows.append(agg)
    weekly = pd.concat(rows, ignore_index=True) if rows else daily.iloc[0:0].copy()
    weekly["timeframe"] = "1w"
    grp = weekly.groupby("ticker", group_keys=False)
    weekly["ret1_lag1"] = grp["returns"].shift(1)
    weekly["ret5"] = grp["returns"].rolling(5, min_periods=3).sum().reset_index(level=0, drop=True)
    weekly["ret20"] = grp["returns"].rolling(20, min_periods=8).sum().reset_index(level=0, drop=True)
    weekly["vol20_mean"] = grp["volatility"].rolling(20, min_periods=8).mean().reset_index(level=0, drop=True)
    weekly["vol60_z"] = (
        (weekly["volatility"] - grp["volatility"].rolling(60, min_periods=20).mean().reset_index(level=0, drop=True))
        / grp["volatility"].rolling(60, min_periods=20).std().reset_index(level=0, drop=True).replace(0, np.nan)
    )
    weekly["close_drawdown60"] = weekly["close"] / grp["close"].rolling(60, min_periods=20).max().reset_index(level=0, drop=True) - 1.0
    return weekly


def build_feature_table(source: pd.DataFrame) -> pd.DataFrame:
    daily = add_daily_features(source)
    weekly = add_weekly_view(source)
    combined = pd.concat([daily, weekly], ignore_index=True, sort=False)
    combined["yield_curve_10y_2y"] = combined["10y_treasury"] - combined["2y_treasury"]
    combined["real_rate_proxy"] = combined["fed_funds_rate"] - combined["cpi"].pct_change().fillna(0.0)
    combined["market_context"] = np.where(combined["ticker"].str.startswith("^"), "index", "single_stock")
    combined["context"] = combined["ticker"] + ":" + combined["timeframe"]
    macro_dummies = pd.get_dummies(combined["macro_context"].fillna("unknown"), prefix="macro", dtype=float)
    combined = pd.concat([combined, macro_dummies], axis=1)
    combined = combined.sort_values(["timeframe", "date", "ticker"]).reset_index(drop=True)
    splits: list[str] = []
    for _, group in combined.groupby("context", sort=False):
        n = len(group)
        split = np.full(n, "train", dtype=object)
        split[int(n * 0.60) :] = "calibration"
        split[int(n * 0.80) :] = "test"
        splits.extend(split.tolist())
    combined["split"] = splits
    return combined.dropna(subset=["returns", "volatility", "regime_label"]).copy()


def candidate_features(df: pd.DataFrame) -> list[str]:
    blocked = {
        "date",
        "ticker",
        "timeframe",
        "context",
        "split",
        "regime_label",
        "regime_confidence",
        "macro_context",
        "market_context",
    }
    features: list[str] = []
    for col in df.columns:
        if col in blocked or col.startswith(("future_", "target_", "next_")):
            continue
        values = numeric(df[col])
        if values.notna().sum() < 1000 or values.dropna().nunique() <= 2:
            continue
        features.append(col)
    return sorted(features)


def metric(df: pd.DataFrame, mask: pd.Series, root: str, split: str, train_precision: float | None = None) -> dict[str, Any]:
    split_mask = df["split"].eq(split)
    selected = df[split_mask & mask.fillna(False)]
    support = int(len(selected))
    success = int(selected["regime_label"].eq(root).sum()) if support else 0
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
    if calibration["support"] < SUPPORT_CAL_MIN:
        out.append("calibration_support_below_250")
    if test["support"] < SUPPORT_TEST_MIN:
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
    if min(len(calibration["validation_instruments"]), len(test["validation_instruments"])) < VALIDATION_INSTRUMENTS_MIN:
        out.append("validation_instruments_below_5")
    if min(len(calibration["validation_timeframes"]), len(test["validation_timeframes"])) < VALIDATION_TIMEFRAMES_MIN:
        out.append("validation_timeframes_below_2")
    return out


def rule_mask(df: pd.DataFrame, rule: str) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for part in rule.split(" AND "):
        if " >= " in part:
            feature, value = part.split(" >= ")
            mask &= numeric(df[feature]) >= float(value)
        elif " <= " in part:
            feature, value = part.split(" <= ")
            mask &= numeric(df[feature]) <= float(value)
        else:
            raise ValueError(part)
    return mask


def train_candidate_rules(df: pd.DataFrame, root: str, features: list[str]) -> list[tuple[tuple[float, float, int], str]]:
    train = df[df["split"].eq("train")]
    candidates: list[tuple[tuple[float, float, int], str]] = []
    for feature in features:
        values = numeric(train[feature]).dropna()
        if values.nunique() <= 4:
            continue
        for q in QUANTILES:
            threshold = float(values.quantile(q))
            if not math.isfinite(threshold):
                continue
            for op in [">=", "<="]:
                rule = f"{feature} {op} {threshold:.12g}"
                m = metric(train, rule_mask(train, rule), root, "train")
                if m["support"] >= SUPPORT_TRAIN_MIN and m["coverage"] >= COVERAGE_MIN:
                    candidates.append(((m["precision_wilson_lcb_95"], m["precision"], m["support"]), rule))
    candidates.sort(key=lambda item: item[0], reverse=True)
    seeds = candidates[:32]
    for i, (_, left) in enumerate(seeds[:20]):
        left_feature = left.split(" ")[0]
        for _, right in seeds[i + 1 : 20]:
            right_feature = right.split(" ")[0]
            if left_feature == right_feature:
                continue
            rule = f"{left} AND {right}"
            m = metric(train, rule_mask(train, rule), root, "train")
            if m["support"] >= SUPPORT_TRAIN_MIN and m["coverage"] >= COVERAGE_MIN:
                candidates.append(((m["precision_wilson_lcb_95"], m["precision"], m["support"]), rule))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates


def run_root(df: pd.DataFrame, root: str, features: list[str]) -> dict[str, Any]:
    candidates = train_candidate_rules(df, root, features)
    if not candidates:
        false_mask = pd.Series(False, index=df.index)
        train = metric(df, false_mask, root, "train")
        calibration = metric(df, false_mask, root, "calibration")
        test = metric(df, false_mask, root, "test")
        return {
            "root_class": root,
            "state": "blocked",
            "rule": "no_train_candidate_with_min_support",
            "train": train,
            "calibration": calibration,
            "test": test,
            "accepted_95": False,
            "blockers": ["no_train_candidate_with_min_support"],
        }
    _, selected_rule = candidates[0]
    mask = rule_mask(df, selected_rule)
    train = metric(df, mask, root, "train")
    calibration = metric(df, mask, root, "calibration", train["precision"])
    test = metric(df, mask, root, "test", train["precision"])
    block = blockers(calibration, test)
    return {
        "root_class": root,
        "state": "accepted_95" if not block else "blocked",
        "rule": selected_rule,
        "threshold_selected_on": "train_split_only",
        "train": train,
        "calibration": calibration,
        "test": test,
        "accepted_95": not block,
        "blockers": block,
    }


def write_summary(path: Path, reports: list[dict[str, Any]]) -> None:
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
        "test_timeframes",
        "test_instruments",
        "blockers",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for item in reports:
            writer.writerow(
                {
                    "root_class": item["root_class"],
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
                    "test_timeframes": ";".join(item["test"]["validation_timeframes"]),
                    "test_instruments": ";".join(item["test"]["validation_instruments"]),
                    "blockers": ";".join(item["blockers"]),
                }
            )


def write_report_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Kaggle Direct Regime-Label Root Gate",
        "",
        f"Run id: `{report['loop_id']}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{report['decision']['gate_result']}`",
        f"- Accepted new roots: {', '.join(report['decision']['accepted_new_roots_95']) or 'none'}",
        f"- Missing roots: {', '.join(report['decision']['missing_root_classes_95_effective'])}",
        f"- Runtime code changed: `{str(report['decision']['runtime_code_changed']).lower()}`",
        f"- Thresholds relaxed: `{str(report['decision']['thresholds_relaxed']).lower()}`",
        "",
        "## Results",
        "",
        "| Root | State | Rule | Cal support | Cal LCB | Test support | Test LCB | Test precision | Blockers |",
        "|---|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for root in ROOTS:
        item = report["root_reports"][root]
        lines.append(
            "| {root} | {state} | `{rule}` | {cal_support} | {cal_lcb:.6f} | {test_support} | {test_lcb:.6f} | {test_precision:.6f} | {blockers} |".format(
                root=root,
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
            "- Source `regime_label` is used only as the target label.",
            "- Source `regime_confidence` and future/target/next columns are blocked as predictors.",
            "- Candidate roots are active MainRegimeV2 parent labels `Bull`, `Bear`, and `Sideways` only.",
            "- `Manipulation` is not evaluated because this source is not direct event/order-lifecycle/L2 evidence.",
            "- Raw Kaggle ZIP/CSV and the full derived feature table stay under `/private/tmp` and are not committed to the repo.",
            "- Repo artifacts are compact: report JSON/MD, summary CSV, assertion output, and feature sample only.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    source_meta = download_source()
    source = read_source_csv()
    feature_table = build_feature_table(source)
    features = candidate_features(feature_table)
    root_reports = {root: run_root(feature_table, root, features) for root in ROOTS}
    accepted_new = [root for root, item in root_reports.items() if item["accepted_95"]]
    retained_prior = ["Crisis"]
    missing = [root for root in ["Bull", "Bear", "Sideways", "Manipulation"] if root not in accepted_new + retained_prior]

    feature_csv = FEATURE_TABLE
    legacy_repo_feature_csv = OUT_DIR / "kaggle_regime_label_feature_table.csv"
    feature_sample_csv = OUT_DIR / "kaggle_regime_label_feature_sample.csv"
    summary_csv = OUT_DIR / "kaggle_regime_label_root_gate_summary.csv"
    report_json = OUT_DIR / "kaggle_regime_label_root_gate_report.json"
    report_md = OUT_DIR / "kaggle_regime_label_root_gate_report.md"
    assertions = CHECK_DIR / "kaggle_regime_label_root_gate_assertions.out"

    compact_cols = [
        "date",
        "ticker",
        "timeframe",
        "context",
        "market_context",
        "split",
        "regime_label",
        "close",
        "returns",
        "volatility",
        "macro_context",
    ] + features
    feature_table[compact_cols].to_csv(feature_csv, index=False)
    if legacy_repo_feature_csv.exists():
        legacy_repo_feature_csv.unlink()
    feature_table[compact_cols].groupby(["ticker", "timeframe", "split"], group_keys=False).head(10).to_csv(feature_sample_csv, index=False)
    write_summary(summary_csv, list(root_reports.values()))

    report: dict[str, Any] = {
        "loop_id": RUN_ID,
        "objective": "Direct parent-labeled Kaggle stock-market regime root gate for active MainRegimeV2 Bull/Bear/Sideways labels.",
        "sources": {
            "kaggle": source_meta,
        },
        "feature_policy": {
            "candidate_feature_count": len(features),
            "candidate_features": features,
            "source_label_used_only_as_target": True,
            "source_regime_confidence_blocked_as_predictor": True,
            "blocked_future_predictors": True,
            "runtime_code_changed": False,
        },
        "split_counts": {split: int((feature_table["split"] == split).sum()) for split in ["train", "calibration", "test"]},
        "label_counts": {str(k): int(v) for k, v in feature_table["regime_label"].value_counts(dropna=False).items()},
        "label_counts_by_timeframe": json_counts(feature_table.groupby(["regime_label", "timeframe"]).size()),
        "context_counts": {
            "instruments": sorted(feature_table["ticker"].astype(str).unique().tolist()),
            "market_contexts": sorted(feature_table["market_context"].astype(str).unique().tolist()),
            "timeframes": sorted(feature_table["timeframe"].astype(str).unique().tolist()),
            "contexts": sorted(feature_table["context"].astype(str).unique().tolist()),
        },
        "acceptance_95": {
            "precision_wilson_lcb_95_min": 0.95,
            "calibration_support_min": SUPPORT_CAL_MIN,
            "test_support_min": SUPPORT_TEST_MIN,
            "coverage_min": COVERAGE_MIN,
            "ece_max": ECE_MAX,
            "validation_instruments_min": VALIDATION_INSTRUMENTS_MIN,
            "validation_timeframes_min": VALIDATION_TIMEFRAMES_MIN,
        },
        "root_reports": root_reports,
        "decision": {
            "gate_result": "accepted_95" if accepted_new else "blocked_kaggle_regime_label_root_gate_below_95",
            "accepted_new_roots_95": accepted_new,
            "retained_prior_accepted_root_classes_95": retained_prior,
            "accepted_root_classes_95_effective": sorted(set(accepted_new + retained_prior), key=lambda item: ["Bull", "Bear", "Sideways", "Crisis", "Manipulation"].index(item)),
            "missing_root_classes_95_effective": missing,
            "manipulation_evaluated": False,
            "manipulation_blocker": "Kaggle stock-market regime labels are not direct event/order-lifecycle/L2 manipulation evidence.",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "fresh_calibration_rerun": True,
            "trade_usable": False,
            "next_action": "If all source-labeled price/macro gates fail, acquire an authoritative regime-cycle label source or reopen feature design; keep Manipulation blocked until direct event/order-lifecycle labels exist.",
        },
        "artifacts": {
            "report_json": repo_rel(report_json),
            "report_md": repo_rel(report_md),
            "summary_csv": repo_rel(summary_csv),
            "feature_table_tmp_path": str(feature_csv),
            "feature_table_committed": False,
            "feature_sample": repo_rel(feature_sample_csv),
            "assertions": repo_rel(assertions),
        },
    }
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_report_md(report_md, report)
    assertion_lines = [
        f"loop_id={RUN_ID}",
        f"rows={len(feature_table)}",
        "raw_committed_to_repo=false",
        f"runtime_code_changed={str(report['decision']['runtime_code_changed']).lower()}",
        f"thresholds_relaxed={str(report['decision']['thresholds_relaxed']).lower()}",
        f"accepted_new_roots_95={','.join(accepted_new) if accepted_new else 'none'}",
        f"gate_result={report['decision']['gate_result']}",
    ]
    for root in ROOTS:
        item = root_reports[root]
        assertion_lines.append(
            f"{root}:cal_lcb={item['calibration']['precision_wilson_lcb_95']:.6f}:test_lcb={item['test']['precision_wilson_lcb_95']:.6f}:accepted={str(item['accepted_95']).lower()}"
        )
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
