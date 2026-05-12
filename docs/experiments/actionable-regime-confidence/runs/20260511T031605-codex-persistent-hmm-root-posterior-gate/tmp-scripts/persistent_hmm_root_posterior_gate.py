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
RUN_ID = "20260511T031605+0800-codex-persistent-hmm-root-posterior-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T031605-codex-persistent-hmm-root-posterior-gate"
OUT_DIR = RUN_ROOT / "persistent-hmm-root-posterior-gate"
CHECK_DIR = RUN_ROOT / "checks"

INPUT_PANELS = {
    "breadth_sector": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T030516-codex-breadth-sector-root-gate/breadth-sector-gate/breadth_sector_root_feature_table.csv",
    "cboe_options_vol": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T030759-codex-cboe-options-vol-root-gate/options-vol-gate/cboe_options_vol_root_feature_table.csv",
}

STATES = ["Bull", "Bear", "Sideways", "Crisis", "UnknownOrMixed"]
EVALUATED_ROOTS = ["Bull", "Bear", "Sideways"]
Z95 = 1.959963984540054
MAX_FEATURES_PER_PANEL = 18
TRANSITION_ALPHA = 1.0
PRIOR_ALPHA = 1.0

ACCEPTANCE_95 = {
    "precision_wilson_lcb_95_min": 0.95,
    "calibration_support_min": 120,
    "test_support_min": 60,
    "ece_max": 0.05,
    "coverage_min": 0.03,
    "validation_instruments_min": 2,
    "validation_market_contexts_min": 2,
    "validation_timeframes_min": 2,
}

ID_COLUMNS = {
    "ts",
    "date",
    "ticker",
    "instrument",
    "market",
    "market_context",
    "provider_context",
    "source_panel",
    "timeframe",
    "context",
    "split",
    "root_label",
}
RAW_PRICE_COLUMNS = {"open", "high", "low", "close", "volume"}
BLOCKED_PREFIXES = ("future_", "next_")
BLOCKED_SUBSTRINGS = ("_next",)


@dataclass
class PanelModel:
    source_panel: str
    feature_names: list[str]
    train_medians: pd.Series
    train_means: pd.Series
    train_stds: pd.Series
    emission_means: dict[str, np.ndarray]
    emission_vars: dict[str, np.ndarray]
    transition: np.ndarray
    prior: np.ndarray
    feature_scores: list[dict[str, Any]]
    train_rows: int
    state_counts: dict[str, int]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lcb(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def finite_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype(float)
    return pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)


def entropy(values: np.ndarray) -> float:
    p = values[np.isfinite(values) & (values > 0)]
    if len(p) == 0:
        return 0.0
    return float(-(p * np.log(p)).sum())


def load_panel(source_panel: str, path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["source_panel"] = source_panel
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    if "market_context" not in df.columns and "market" in df.columns:
        df["market_context"] = df["market"]
    if "market_context" not in df.columns:
        df["market_context"] = source_panel
    if "instrument" not in df.columns and "ticker" in df.columns:
        df["instrument"] = df["ticker"]
    if "provider_context" not in df.columns:
        df["provider_context"] = source_panel
    df["context"] = (
        df["source_panel"].astype(str)
        + ":"
        + df["instrument"].astype(str)
        + ":"
        + df["timeframe"].astype(str)
    )
    df = df[df["split"].isin(["train", "calibration", "test"])].copy()
    df = df[df["root_label"].isin(STATES)].copy()
    df = df.dropna(subset=["ts", "instrument", "timeframe", "split", "root_label"]).copy()
    return df.sort_values(["context", "ts"]).reset_index(drop=True)


def candidate_feature_names(df: pd.DataFrame) -> list[str]:
    names: list[str] = []
    for col in df.columns:
        if col in ID_COLUMNS or col in RAW_PRICE_COLUMNS:
            continue
        if col.startswith(BLOCKED_PREFIXES):
            continue
        if any(part in col for part in BLOCKED_SUBSTRINGS):
            continue
        if col == "target_source_backed_root":
            continue
        values = finite_numeric(df[col])
        non_null = int(values.notna().sum())
        if non_null < 300:
            continue
        if values.dropna().nunique() <= 1:
            continue
        names.append(col)
    return names


def score_features_train_only(df: pd.DataFrame, names: list[str]) -> list[dict[str, Any]]:
    train = df["split"].eq("train")
    y = df.loc[train, "root_label"].astype(str)
    scored: list[dict[str, Any]] = []
    for name in names:
        values = finite_numeric(df.loc[train, name])
        valid = values.notna() & y.isin(STATES)
        if int(valid.sum()) < 300:
            continue
        global_mean = float(values[valid].mean())
        global_var = float(values[valid].var(ddof=0))
        if not math.isfinite(global_var) or global_var <= 1e-12:
            continue
        between = 0.0
        within = 0.0
        state_support: dict[str, int] = {}
        for state in STATES:
            state_values = values[valid & y.eq(state)]
            support = int(state_values.notna().sum())
            state_support[state] = support
            if support == 0:
                continue
            state_mean = float(state_values.mean())
            state_var = float(state_values.var(ddof=0)) if support > 1 else 0.0
            between += support * (state_mean - global_mean) ** 2
            within += support * state_var
        score = between / max(within, 1e-12)
        scored.append(
            {
                "feature": name,
                "score": float(score),
                "non_null_train": int(valid.sum()),
                "state_support": state_support,
            }
        )
    scored.sort(key=lambda item: (item["score"], item["non_null_train"]), reverse=True)
    return scored


def make_z_matrix(df: pd.DataFrame, feature_names: list[str]) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    x = pd.DataFrame({name: finite_numeric(df[name]) for name in feature_names})
    train = df["split"].eq("train")
    medians = x.loc[train].median(numeric_only=True).fillna(0.0)
    x = x.fillna(medians).fillna(0.0)
    means = x.loc[train].mean(numeric_only=True)
    stds = x.loc[train].std(numeric_only=True, ddof=0).replace(0.0, 1.0).fillna(1.0)
    z = (x - means) / stds
    z = z.replace([np.inf, -np.inf], 0.0).fillna(0.0)
    return z, medians, means, stds


def fit_panel_model(source_panel: str, df: pd.DataFrame) -> PanelModel:
    names = candidate_feature_names(df)
    scored = score_features_train_only(df, names)
    selected_names = [item["feature"] for item in scored[:MAX_FEATURES_PER_PANEL]]
    if not selected_names:
        raise RuntimeError(f"{source_panel}: no usable current/past numeric features")
    z, medians, means, stds = make_z_matrix(df, selected_names)
    train = df["split"].eq("train").to_numpy()
    labels = df["root_label"].astype(str).to_numpy()
    x_train = z.to_numpy(dtype=float)[train]
    y_train = labels[train]
    global_var = np.var(x_train, axis=0) + 1e-3
    emission_means: dict[str, np.ndarray] = {}
    emission_vars: dict[str, np.ndarray] = {}
    state_counts: dict[str, int] = {}
    for state in STATES:
        mask = y_train == state
        state_counts[state] = int(mask.sum())
        if int(mask.sum()) >= 30:
            state_values = x_train[mask]
            emission_means[state] = np.mean(state_values, axis=0)
            state_var = np.var(state_values, axis=0) + 1e-3
            emission_vars[state] = 0.75 * state_var + 0.25 * global_var
        else:
            emission_means[state] = np.mean(x_train, axis=0)
            emission_vars[state] = global_var.copy()

    state_index = {state: i for i, state in enumerate(STATES)}
    transition = np.full((len(STATES), len(STATES)), TRANSITION_ALPHA, dtype=float)
    first_counts = np.full(len(STATES), PRIOR_ALPHA, dtype=float)
    train_df = df[df["split"].eq("train")].sort_values(["context", "ts"])
    for _, group in train_df.groupby("context", sort=False):
        group_labels = group["root_label"].astype(str).tolist()
        if not group_labels:
            continue
        first_counts[state_index[group_labels[0]]] += 1.0
        for left, right in zip(group_labels, group_labels[1:]):
            transition[state_index[left], state_index[right]] += 1.0
    transition = transition / transition.sum(axis=1, keepdims=True)
    prior = first_counts / first_counts.sum()

    return PanelModel(
        source_panel=source_panel,
        feature_names=selected_names,
        train_medians=medians,
        train_means=means,
        train_stds=stds,
        emission_means=emission_means,
        emission_vars=emission_vars,
        transition=transition,
        prior=prior,
        feature_scores=scored[:MAX_FEATURES_PER_PANEL],
        train_rows=int(train.sum()),
        state_counts=state_counts,
    )


def emission_log_probs(x: np.ndarray, model: PanelModel) -> np.ndarray:
    rows: list[np.ndarray] = []
    d = max(1, x.shape[1])
    temperature = math.sqrt(d)
    for state in STATES:
        mean = model.emission_means[state]
        var = np.maximum(model.emission_vars[state], 1e-4)
        logp = -0.5 * (np.log(2.0 * math.pi * var) + ((x - mean) ** 2) / var).sum(axis=1)
        rows.append(logp / temperature)
    return np.vstack(rows).T


def posterior_filter_panel(df: pd.DataFrame, model: PanelModel) -> pd.DataFrame:
    x = pd.DataFrame({name: finite_numeric(df[name]) for name in model.feature_names})
    x = x.fillna(model.train_medians).fillna(0.0)
    z = ((x - model.train_means) / model.train_stds).replace([np.inf, -np.inf], 0.0).fillna(0.0)
    log_emit = emission_log_probs(z.to_numpy(dtype=float), model)
    out = df[["ts", "source_panel", "instrument", "market_context", "provider_context", "timeframe", "context", "split", "root_label"]].copy()
    posterior_rows: list[np.ndarray] = []
    row_positions = {idx: pos for pos, idx in enumerate(df.index)}
    for _, group in df.groupby("context", sort=False):
        prev: np.ndarray | None = None
        for idx in group.index:
            row_pos = row_positions[idx]
            if prev is None:
                predicted = model.prior.copy()
            else:
                predicted = prev @ model.transition
            le = log_emit[row_pos]
            likelihood = np.exp(le - np.max(le))
            posterior = predicted * likelihood
            denom = float(posterior.sum())
            if not math.isfinite(denom) or denom <= 0.0:
                posterior = np.full(len(STATES), 1.0 / len(STATES))
            else:
                posterior = posterior / denom
            posterior_rows.append(posterior)
            prev = posterior
    posterior_matrix = np.vstack(posterior_rows)
    for i, state in enumerate(STATES):
        out[f"p_{state}"] = posterior_matrix[:, i]
    out["state_entropy"] = [entropy(row) for row in posterior_matrix]
    out["top_state"] = [STATES[int(np.argmax(row))] for row in posterior_matrix]
    out["top_state_probability"] = posterior_matrix.max(axis=1)
    return out


def split_metric(df: pd.DataFrame, selected: pd.Series, root: str, split: str) -> dict[str, Any]:
    split_mask = df["split"].eq(split)
    selected_mask = split_mask & selected.fillna(False)
    chosen = df[selected_mask]
    support = int(len(chosen))
    success = int(chosen["root_label"].eq(root).sum()) if support else 0
    precision = success / support if support else 0.0
    split_total = int(split_mask.sum())
    return {
        "support": support,
        "success": success,
        "precision": float(precision),
        "precision_wilson_lcb_95": wilson_lcb(success, support),
        "coverage": support / split_total if split_total else 0.0,
        "mean_posterior": float(chosen[f"p_{root}"].mean()) if support else 0.0,
        "validation_instruments": sorted(chosen["instrument"].dropna().astype(str).unique().tolist()),
        "validation_market_contexts": sorted(chosen["market_context"].dropna().astype(str).unique().tolist()),
        "validation_timeframes": sorted(chosen["timeframe"].dropna().astype(str).unique().tolist()),
        "validation_source_panels": sorted(chosen["source_panel"].dropna().astype(str).unique().tolist()),
        "validation_contexts": sorted(chosen["context"].dropna().astype(str).unique().tolist()),
    }


def blockers(calibration: dict[str, Any], test: dict[str, Any], ece: float) -> list[str]:
    out: list[str] = []
    if calibration["support"] < ACCEPTANCE_95["calibration_support_min"]:
        out.append("calibration_support_below_120")
    if test["support"] < ACCEPTANCE_95["test_support_min"]:
        out.append("test_support_below_60")
    if calibration["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        out.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        out.append("test_wilson95_below_0_95")
    if calibration["coverage"] < ACCEPTANCE_95["coverage_min"]:
        out.append("calibration_coverage_below_0_03")
    if test["coverage"] < ACCEPTANCE_95["coverage_min"]:
        out.append("test_coverage_below_0_03")
    if ece > ACCEPTANCE_95["ece_max"]:
        out.append("ece_above_0_05")
    if len(test["validation_instruments"]) < ACCEPTANCE_95["validation_instruments_min"]:
        out.append("validation_instruments_below_2")
    if len(test["validation_market_contexts"]) < ACCEPTANCE_95["validation_market_contexts_min"]:
        out.append("validation_market_contexts_below_2")
    if len(test["validation_timeframes"]) < ACCEPTANCE_95["validation_timeframes_min"]:
        out.append("validation_timeframes_below_2")
    return out


def select_threshold(scored: pd.DataFrame, root: str) -> tuple[float, str]:
    cal_scores = scored.loc[scored["split"].eq("calibration"), f"p_{root}"].dropna()
    if cal_scores.empty:
        return 1.0, "no_calibration_scores"
    quantiles = np.concatenate(
        [
            np.linspace(0.50, 0.95, 46),
            np.linspace(0.96, 0.995, 15),
        ]
    )
    candidates = sorted({float(cal_scores.quantile(q)) for q in quantiles if math.isfinite(float(cal_scores.quantile(q)))})
    if not candidates:
        return float(cal_scores.max()), "fallback_max_calibration_score"
    best_threshold = candidates[0]
    best_key = (-1.0, -1.0, -1, -1.0)
    selected_reason = "calibration_support_and_coverage_candidate"
    fallback_threshold = candidates[0]
    fallback_key = (-1.0, -1.0, -1, -1.0)
    for threshold in candidates:
        selected = scored[f"p_{root}"] >= threshold
        metrics = split_metric(scored, selected, root, "calibration")
        key = (
            metrics["precision_wilson_lcb_95"],
            metrics["precision"],
            metrics["support"],
            metrics["coverage"],
        )
        if key > fallback_key:
            fallback_key = key
            fallback_threshold = threshold
        if metrics["support"] < ACCEPTANCE_95["calibration_support_min"]:
            continue
        if metrics["coverage"] < ACCEPTANCE_95["coverage_min"]:
            continue
        if key > best_key:
            best_key = key
            best_threshold = threshold
    if best_key[0] < 0.0:
        return fallback_threshold, "fallback_best_calibration_lcb_without_min_support_or_coverage"
    return best_threshold, selected_reason


def run_root(scored: pd.DataFrame, root: str) -> dict[str, Any]:
    threshold, threshold_selection = select_threshold(scored, root)
    selected = scored[f"p_{root}"] >= threshold
    train = split_metric(scored, selected, root, "train")
    calibration = split_metric(scored, selected, root, "calibration")
    test = split_metric(scored, selected, root, "test")
    ece = abs(test["precision"] - calibration["precision"]) if calibration["support"] else 1.0
    block = blockers(calibration, test, ece)
    return {
        "root_class": root,
        "state": "accepted_95" if not block else "blocked",
        "model": "supervised_gaussian_hmm_forward_filter",
        "qualifying_condition": f"p_{root}_persistent_hmm >= {threshold:.12g}",
        "threshold": float(threshold),
        "threshold_selected_on": threshold_selection,
        "train": train,
        "calibration": calibration,
        "test": test,
        "ece": float(ece),
        "accepted_95": not block,
        "blockers": block,
    }


def write_summary_csv(path: Path, reports: list[dict[str, Any]]) -> None:
    fields = [
        "root_class",
        "state",
        "rule",
        "threshold_selected_on",
        "train_support",
        "train_lcb",
        "calibration_support",
        "calibration_lcb",
        "test_support",
        "test_lcb",
        "test_precision",
        "test_coverage",
        "ece",
        "test_instruments",
        "test_market_contexts",
        "test_timeframes",
        "test_source_panels",
        "blockers",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for report in reports:
            writer.writerow(
                {
                    "root_class": report["root_class"],
                    "state": report["state"],
                    "rule": report["qualifying_condition"],
                    "threshold_selected_on": report["threshold_selected_on"],
                    "train_support": report["train"]["support"],
                    "train_lcb": report["train"]["precision_wilson_lcb_95"],
                    "calibration_support": report["calibration"]["support"],
                    "calibration_lcb": report["calibration"]["precision_wilson_lcb_95"],
                    "test_support": report["test"]["support"],
                    "test_lcb": report["test"]["precision_wilson_lcb_95"],
                    "test_precision": report["test"]["precision"],
                    "test_coverage": report["test"]["coverage"],
                    "ece": report["ece"],
                    "test_instruments": ";".join(report["test"]["validation_instruments"]),
                    "test_market_contexts": ";".join(report["test"]["validation_market_contexts"]),
                    "test_timeframes": ";".join(report["test"]["validation_timeframes"]),
                    "test_source_panels": ";".join(report["test"]["validation_source_panels"]),
                    "blockers": ";".join(report["blockers"]),
                }
            )


def write_report_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Persistent HMM Root Posterior Gate",
        "",
        f"Run id: `{report['loop_id']}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{report['decision']['gate_result']}`",
        f"- Accepted new MainRegimeV2 roots: {', '.join(report['decision']['accepted_new_roots_95']) or 'none'}",
        f"- Effective accepted roots after retained prior: {', '.join(report['decision']['accepted_root_classes_95_effective']) or 'none'}",
        f"- Missing roots: {', '.join(report['decision']['missing_root_classes_95_effective'])}",
        f"- Runtime code changed: `{str(report['decision']['runtime_code_changed']).lower()}`",
        f"- Thresholds relaxed: `{str(report['decision']['thresholds_relaxed']).lower()}`",
        "",
        "## Inputs",
        "",
    ]
    for name, source in report["input_feature_tables"].items():
        lines.append(f"- `{name}`: `{source}`")
    lines.extend(
        [
            "",
            "## Parent Root Results",
            "",
            "| Root | State | Cal support | Cal LCB | Test support | Test LCB | Test precision | Test coverage | Blockers |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for root in EVALUATED_ROOTS:
        item = report["root_reports"][root]
        lines.append(
            "| {root} | {state} | {cal_support} | {cal_lcb:.6f} | {test_support} | {test_lcb:.6f} | {test_precision:.6f} | {test_coverage:.6f} | {blockers} |".format(
                root=root,
                state=item["state"],
                cal_support=item["calibration"]["support"],
                cal_lcb=item["calibration"]["precision_wilson_lcb_95"],
                test_support=item["test"]["support"],
                test_lcb=item["test"]["precision_wilson_lcb_95"],
                test_precision=item["test"]["precision"],
                test_coverage=item["test"]["coverage"],
                blockers=", ".join(item["blockers"]) or "none",
            )
        )
    lines.extend(
        [
            "",
            "## Model Policy",
            "",
            "- Model family: supervised Gaussian HMM forward filter with train-only transition/emission estimates.",
            "- Candidate labels: active MainRegimeV2 parent labels only: `Bull`, `Bear`, `Sideways`; `Crisis` and `UnknownOrMixed` are hidden competing states but not reissued here.",
            "- Feature policy: current/past numeric fields only; `future_`, `next_`, root labels, identifiers, and raw OHLCV price columns are blocked as predictors.",
            "- Threshold policy: posterior threshold selected on chronological calibration only, then held-out test is read once.",
            "- Manipulation policy: not evaluated because these panels do not contain direct event/order-lifecycle/L2 evidence.",
            "",
            "## Artifacts",
            "",
            f"- Report JSON: `{report['artifacts']['report_json']}`",
            f"- Summary CSV: `{report['artifacts']['summary_csv']}`",
            f"- Scores CSV: `{report['artifacts']['scores_csv']}`",
            f"- Score sample CSV: `{report['artifacts']['score_sample_csv']}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    panels = {name: load_panel(name, path) for name, path in INPUT_PANELS.items()}
    models: dict[str, PanelModel] = {}
    scored_parts: list[pd.DataFrame] = []
    model_report: dict[str, Any] = {}
    for source_panel, frame in panels.items():
        model = fit_panel_model(source_panel, frame)
        models[source_panel] = model
        scored_parts.append(posterior_filter_panel(frame, model))
        model_report[source_panel] = {
            "train_rows": model.train_rows,
            "state_counts_train": model.state_counts,
            "selected_features": model.feature_names,
            "feature_scores_train_only": model.feature_scores,
            "transition_rows": {
                state: {STATES[j]: float(model.transition[i, j]) for j in range(len(STATES))}
                for i, state in enumerate(STATES)
            },
            "prior": {state: float(model.prior[i]) for i, state in enumerate(STATES)},
        }

    scored = pd.concat(scored_parts, ignore_index=True).sort_values(["source_panel", "context", "ts"]).reset_index(drop=True)
    root_reports = {root: run_root(scored, root) for root in EVALUATED_ROOTS}
    accepted_new = [root for root, item in root_reports.items() if item["accepted_95"]]
    retained_prior = ["Crisis"]
    effective = sorted(set(accepted_new + retained_prior), key=lambda item: ["Bull", "Bear", "Sideways", "Crisis", "Manipulation"].index(item))
    missing_effective = [root for root in ["Bull", "Bear", "Sideways", "Manipulation"] if root not in effective]

    scores_csv = OUT_DIR / "persistent_hmm_root_scores.csv"
    score_sample_csv = OUT_DIR / "persistent_hmm_root_score_sample.csv"
    summary_csv = OUT_DIR / "persistent_hmm_root_gate_summary.csv"
    report_json = OUT_DIR / "persistent_hmm_root_gate_report.json"
    report_md = OUT_DIR / "persistent_hmm_root_gate_report.md"
    checks = CHECK_DIR / "persistent_hmm_root_gate_assertions.out"

    score_cols = [
        "ts",
        "source_panel",
        "instrument",
        "market_context",
        "provider_context",
        "timeframe",
        "context",
        "split",
        "root_label",
        "p_Bull",
        "p_Bear",
        "p_Sideways",
        "p_Crisis",
        "p_UnknownOrMixed",
        "state_entropy",
        "top_state",
        "top_state_probability",
    ]
    scored[score_cols].to_csv(scores_csv, index=False)
    scored[score_cols].groupby(["source_panel", "split"], group_keys=False).head(40).to_csv(score_sample_csv, index=False)
    write_summary_csv(summary_csv, list(root_reports.values()))

    split_counts = {
        split: int((scored["split"] == split).sum()) for split in ["train", "calibration", "test"]
    }
    report: dict[str, Any] = {
        "loop_id": RUN_ID,
        "objective": "Persistent-state MainRegimeV2 parent-root posterior gate for Bull/Bear/Sideways from existing breadth-sector and CBOE options-volatility panels.",
        "input_feature_tables": {name: repo_rel(path) for name, path in INPUT_PANELS.items()},
        "acceptance_95": ACCEPTANCE_95,
        "feature_policy": {
            "blocked_predictor_prefixes": list(BLOCKED_PREFIXES),
            "blocked_predictor_substrings": list(BLOCKED_SUBSTRINGS),
            "blocked_predictor_columns": sorted(ID_COLUMNS | RAW_PRICE_COLUMNS),
            "allowed_target_prefix_note": "`target_` current/past engineered fields are allowed only where they are already present in the source feature table; `future_` and label fields are never predictors.",
            "uses_current_and_past_fields_only": True,
            "target_columns_used_only_as_labels": True,
            "candidate_root_labels": EVALUATED_ROOTS,
            "hidden_competing_states": STATES,
        },
        "model_policy": {
            "family": "supervised_gaussian_hmm_forward_filter",
            "fit_scope": "per_source_panel_train_split_only",
            "transition_estimation": "chronological train root-label transitions per context with Laplace smoothing",
            "emission_estimation": "train-only diagonal Gaussian emissions over selected current/past features",
            "feature_selection": "train-only ANOVA-style between-state score per panel",
            "posterior_filter": "causal forward filter per source/instrument/timeframe context",
            "threshold_selection": "chronological calibration split only; held-out test is not used for threshold choice",
        },
        "source_panel_report": model_report,
        "split_counts": split_counts,
        "label_counts": {str(k): int(v) for k, v in scored["root_label"].value_counts(dropna=False).items()},
        "context_counts": {
            "source_panels": sorted(scored["source_panel"].unique().tolist()),
            "instruments": sorted(scored["instrument"].astype(str).unique().tolist()),
            "market_contexts": sorted(scored["market_context"].astype(str).unique().tolist()),
            "timeframes": sorted(scored["timeframe"].astype(str).unique().tolist()),
            "contexts": sorted(scored["context"].astype(str).unique().tolist()),
        },
        "root_reports": root_reports,
        "decision": {
            "gate_result": "accepted_95" if accepted_new else "blocked_persistent_hmm_root_posterior_gate_below_95",
            "accepted_new_roots_95": accepted_new,
            "retained_prior_accepted_root_classes_95": retained_prior,
            "accepted_root_classes_95_effective": effective,
            "missing_root_classes_95_effective": missing_effective,
            "manipulation_evaluated": False,
            "manipulation_blocker": "No direct event/order-lifecycle/L2 evidence in these input panels.",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        },
        "artifacts": {
            "report_json": repo_rel(report_json),
            "report_md": repo_rel(report_md),
            "summary_csv": repo_rel(summary_csv),
            "scores_csv": repo_rel(scores_csv),
            "score_sample_csv": repo_rel(score_sample_csv),
            "assertions": repo_rel(checks),
        },
    }
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_report_md(report_md, report)

    assertion_lines = [
        f"loop_id={RUN_ID}",
        f"rows={len(scored)}",
        f"source_panels={','.join(report['context_counts']['source_panels'])}",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        f"accepted_new_roots_95={','.join(accepted_new) if accepted_new else 'none'}",
        f"gate_result={report['decision']['gate_result']}",
    ]
    for root in EVALUATED_ROOTS:
        item = root_reports[root]
        assertion_lines.append(
            f"{root}:cal_lcb={item['calibration']['precision_wilson_lcb_95']:.6f}:test_lcb={item['test']['precision_wilson_lcb_95']:.6f}:accepted={str(item['accepted_95']).lower()}"
        )
    checks.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
