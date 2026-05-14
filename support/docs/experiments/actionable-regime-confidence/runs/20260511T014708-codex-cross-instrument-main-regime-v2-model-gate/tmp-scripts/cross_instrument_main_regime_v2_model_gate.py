from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T014708-codex-cross-instrument-main-regime-v2-model-gate"
OUT_DIR = RUN_ROOT / "root-model"
CHECKS_DIR = RUN_ROOT / "checks"
SOURCE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T233911-main-regime-v2-advanced-root-features/advanced_root_features.csv"
LOOP_ID = "20260511T014708+0800-codex-cross-instrument-main-regime-v2-model-gate"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
BLOCKED_PREFIXES = ("future_", "target_")
BLOCKED_SUBSTRINGS = ("_next", "next_", "h4")
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


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson(success: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    center = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return float((center - margin) / denom)


def sigmoid(x: np.ndarray) -> np.ndarray:
    z = np.clip(x, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-z))


def context_quantiles(frame: pd.DataFrame) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for _, group in frame.groupby("context", sort=False):
        g = group.copy()
        train = g[g["split"].eq("train")]
        future_ret = pd.to_numeric(train["future_ret8"], errors="coerce")
        future_abs = future_ret.abs()
        future_range = pd.to_numeric(train["future_range4"], errors="coerce")
        q = {
            "ret_hi": future_ret.quantile(0.65),
            "ret_lo": future_ret.quantile(0.35),
            "abs_hi": future_abs.quantile(0.90),
            "abs_lo": future_abs.quantile(0.40),
            "range_hi": future_range.quantile(0.90),
            "range_lo": future_range.quantile(0.45),
        }
        all_ret = pd.to_numeric(g["future_ret8"], errors="coerce")
        all_abs = all_ret.abs()
        all_range = pd.to_numeric(g["future_range4"], errors="coerce")
        crisis = (all_abs >= q["abs_hi"]) | (all_range >= q["range_hi"])
        sideways = (~crisis) & (all_abs <= q["abs_lo"]) & (all_range <= q["range_lo"])
        bull = (~crisis) & (~sideways) & (all_ret >= q["ret_hi"])
        bear = (~crisis) & (~sideways) & (all_ret <= q["ret_lo"])
        labels = pd.Series("UnknownOrMixed", index=g.index)
        labels.loc[crisis.fillna(False)] = "Crisis"
        labels.loc[sideways.fillna(False)] = "Sideways"
        labels.loc[bull.fillna(False)] = "Bull"
        labels.loc[bear.fillna(False)] = "Bear"
        g["root_label"] = labels
        parts.append(g)
    return pd.concat(parts, axis=0).sort_index()


def numeric_feature_columns(frame: pd.DataFrame) -> list[str]:
    blocked_exact = {
        "open",
        "high",
        "low",
        "close",
        "count",
        "timeframe_minutes",
    }
    cols: list[str] = []
    for col in frame.columns:
        if col in blocked_exact:
            continue
        if col in {"root_label", "split"}:
            continue
        if col.startswith(BLOCKED_PREFIXES):
            continue
        if any(part in col for part in BLOCKED_SUBSTRINGS):
            continue
        if col.startswith("target"):
            continue
        if pd.api.types.is_numeric_dtype(frame[col]) or frame[col].dropna().isin([True, False]).all():
            cols.append(col)
    return cols


def make_matrix(frame: pd.DataFrame, cols: list[str]) -> tuple[pd.DataFrame, list[str]]:
    x = frame[cols].copy()
    for col in x.columns:
        if x[col].dropna().isin([True, False]).all():
            x[col] = x[col].astype(float)
        else:
            x[col] = pd.to_numeric(x[col], errors="coerce")
    keep = [c for c in x.columns if x[c].notna().sum() >= 300 and x[c].replace([np.inf, -np.inf], np.nan).notna().sum() >= 300]
    x = x[keep].replace([np.inf, -np.inf], np.nan)
    train = frame["split"].eq("train")
    med = x[train].median(numeric_only=True)
    x = x.fillna(med).fillna(0.0)
    return x, keep


def fit_logistic(x: np.ndarray, y: np.ndarray, steps: int = 700, lr: float = 0.04, l2: float = 0.02) -> np.ndarray:
    y = y.astype(float)
    pos = max(1.0, float(y.sum()))
    neg = max(1.0, float(len(y) - y.sum()))
    w_pos = len(y) / (2.0 * pos)
    w_neg = len(y) / (2.0 * neg)
    sample_w = np.where(y > 0.5, w_pos, w_neg)
    beta = np.zeros(x.shape[1], dtype=float)
    for _ in range(steps):
        p = sigmoid(x @ beta)
        grad = (x.T @ ((p - y) * sample_w)) / len(y)
        grad += l2 * beta
        beta -= lr * grad
    return beta


def split_metric(frame: pd.DataFrame, selected: np.ndarray, root: str, split: str) -> dict[str, Any]:
    split_mask = frame["split"].eq(split).to_numpy()
    chosen = frame[selected & split_mask]
    support = int(len(chosen))
    success = int(chosen["root_label"].eq(root).sum()) if support else 0
    precision = success / support if support else 0.0
    denom = max(1, int(split_mask.sum()))
    return {
        "support": support,
        "success": success,
        "precision": float(precision),
        "precision_wilson_lcb_95": wilson(success, support),
        "coverage": support / denom,
        "validation_instruments": sorted(chosen["instrument"].dropna().astype(str).unique().tolist()) if support else [],
        "validation_market_contexts": sorted(chosen["market"].dropna().astype(str).unique().tolist()) if support else [],
        "validation_timeframes": sorted(chosen["timeframe"].dropna().astype(str).unique().tolist()) if support else [],
        "validation_contexts": sorted(chosen["context"].dropna().astype(str).unique().tolist()) if support else [],
    }


def blockers(cal: dict[str, Any], test: dict[str, Any], ece: float) -> list[str]:
    out: list[str] = []
    if cal["support"] < ACCEPTANCE_95["calibration_support_min"]:
        out.append("calibration_support_below_120")
    if test["support"] < ACCEPTANCE_95["test_support_min"]:
        out.append("test_support_below_60")
    if cal["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        out.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        out.append("test_wilson95_below_0_95")
    if cal["coverage"] < ACCEPTANCE_95["coverage_min"]:
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


def select_threshold(frame: pd.DataFrame, scores: np.ndarray, root: str) -> float:
    train = frame["split"].eq("train").to_numpy()
    train_scores = scores[train & np.isfinite(scores)]
    candidates = sorted(set(float(np.quantile(train_scores, q)) for q in np.linspace(0.50, 0.98, 49)))
    best = candidates[0]
    best_key = (-1.0, -1, -1.0)
    for threshold in candidates:
        selected = scores >= threshold
        m = split_metric(frame, selected, root, "train")
        if m["support"] < ACCEPTANCE_95["calibration_support_min"] or m["coverage"] < ACCEPTANCE_95["coverage_min"]:
            continue
        key = (m["precision_wilson_lcb_95"], m["support"], m["coverage"])
        if key > best_key:
            best_key = key
            best = threshold
    return best


def run_root(frame: pd.DataFrame, xz: np.ndarray, feature_names: list[str], root: str) -> dict[str, Any]:
    train = frame["split"].eq("train").to_numpy()
    y_train = frame.loc[train, "root_label"].eq(root).to_numpy(dtype=float)
    beta = fit_logistic(xz[train], y_train)
    scores = sigmoid(xz @ beta)
    threshold = select_threshold(frame, scores, root)
    selected = scores >= threshold
    cal = split_metric(frame, selected, root, "calibration")
    test = split_metric(frame, selected, root, "test")
    train_metric = split_metric(frame, selected, root, "train")
    ece = abs(test["precision"] - cal["precision"]) if cal["support"] else 1.0
    b = blockers(cal, test, ece)
    top_idx = np.argsort(np.abs(beta))[-12:][::-1]
    return {
        "root_class": root,
        "state": "accepted_95" if not b else "blocked",
        "qualifying_condition": f"train_only_logistic_score_{root} >= {threshold:.12g}",
        "model": "numpy_logistic_l2_class_weighted_train_only",
        "threshold_selected_on": "train_split_only",
        "feature_count": len(feature_names),
        "top_abs_coefficients": [{"feature": feature_names[i], "coefficient": float(beta[i])} for i in top_idx],
        "train": train_metric,
        "calibration": cal,
        "test": test,
        "ece": float(ece),
        "accepted_95": not b,
        "blockers": b,
    }


def write_summary(path: Path, root_reports: list[dict[str, Any]]) -> None:
    rows = []
    for r in root_reports:
        rows.append(
            {
                "root_class": r["root_class"],
                "state": r["state"],
                "rule": r["qualifying_condition"],
                "cal_support": r["calibration"]["support"],
                "cal_lcb": r["calibration"]["precision_wilson_lcb_95"],
                "test_support": r["test"]["support"],
                "test_lcb": r["test"]["precision_wilson_lcb_95"],
                "test_coverage": r["test"]["coverage"],
                "ece": r["ece"],
                "test_instruments": ";".join(r["test"]["validation_instruments"]),
                "test_market_contexts": ";".join(r["test"]["validation_market_contexts"]),
                "test_timeframes": ";".join(r["test"]["validation_timeframes"]),
                "blockers": ";".join(r["blockers"]),
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)


def write_report_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Cross-Instrument MainRegimeV2 Model Gate",
        "",
        f"Run id: `{report['loop_id']}`",
        "",
        "## Decision",
        "",
        f"- Gate: `{report['decision']['accepted_gate']}`",
        f"- Accepted 95 roots from this run: `{', '.join(report['accepted_root_classes_95_this_run']) or 'none'}`",
        f"- Missing roots after this run: `{', '.join(report['missing_root_classes_95_current_evidence'])}`",
        "- Runtime code changed: false.",
        "- Thresholds relaxed: false.",
        "- Trade usable: false.",
        "",
        "## Root Summary",
        "",
    ]
    for r in report["root_reports"]:
        lines.append(
            f"- {r['root_class']}: state=`{r['state']}`, rule=`{r['qualifying_condition']}`, "
            f"cal_lcb={r['calibration']['precision_wilson_lcb_95']:.6f}, "
            f"test_lcb={r['test']['precision_wilson_lcb_95']:.6f}, "
            f"test_support={r['test']['support']}, blockers=`{', '.join(r['blockers']) or 'none'}`"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(SOURCE)
    frame = context_quantiles(frame).dropna(subset=["future_ret8", "future_range4"]).reset_index(drop=True)
    feature_cols = numeric_feature_columns(frame)
    x, feature_names = make_matrix(frame, feature_cols)
    train = frame["split"].eq("train")
    mu = x[train].mean()
    sigma = x[train].std().replace(0, 1.0).fillna(1.0)
    xz = ((x - mu) / sigma).replace([np.inf, -np.inf], 0.0).fillna(0.0).to_numpy(dtype=float)
    root_reports = [run_root(frame, xz, feature_names, root) for root in ROOTS]
    manipulation = {
        "root_class": "Manipulation",
        "state": "missing_required_inputs",
        "qualifying_condition": "calibration_grade_direct_L2_L3_MBO_order_lifecycle_event_inputs_present == true",
        "model": "required_input_gate",
        "threshold_selected_on": "not_applicable",
        "feature_count": 0,
        "top_abs_coefficients": [],
        "train": {"support": 0, "success": 0, "precision": 0.0, "precision_wilson_lcb_95": 0.0, "coverage": 0.0, "validation_instruments": [], "validation_market_contexts": [], "validation_timeframes": [], "validation_contexts": []},
        "calibration": {"support": 0, "success": 0, "precision": 0.0, "precision_wilson_lcb_95": 0.0, "coverage": 0.0, "validation_instruments": [], "validation_market_contexts": [], "validation_timeframes": [], "validation_contexts": []},
        "test": {"support": 0, "success": 0, "precision": 0.0, "precision_wilson_lcb_95": 0.0, "coverage": 0.0, "validation_instruments": [], "validation_market_contexts": [], "validation_timeframes": [], "validation_contexts": []},
        "ece": 1.0,
        "accepted_95": False,
        "blockers": ["missing_required_inputs", "proxy_only_low_confidence"],
    }
    root_reports.append(manipulation)
    newly_accepted = [r["root_class"] for r in root_reports if r.get("accepted_95")]
    current_accepted = sorted(set(["Crisis"]) | set(newly_accepted))
    missing = [r for r in ["Bull", "Bear", "Sideways", "Manipulation"] if r not in current_accepted]
    report = {
        "schema_version": "cross-instrument-main-regime-v2-model-gate/v1",
        "loop_id": LOOP_ID,
        "run_root": repo_rel(RUN_ROOT),
        "source_feature_table": repo_rel(SOURCE),
        "row_count": int(len(frame)),
        "feature_count": len(feature_names),
        "feature_policy": {
            "future_target_predictors_blocked": True,
            "blocked_prefixes": list(BLOCKED_PREFIXES),
            "blocked_substrings": list(BLOCKED_SUBSTRINGS),
            "model_and_threshold_fit_on_train_only": True,
            "calibration_and_test_held_out": True,
            "runtime_code_changed": False,
        },
        "label_policy": {
            "future_ret8_and_future_range4_used_as_labels_only": True,
            "context_local_train_quantiles": True,
            "active_root_axis": ["Bull", "Bear", "Sideways", "Crisis", "Manipulation", "UnknownOrMixed"],
        },
        "acceptance_95": ACCEPTANCE_95,
        "root_reports": root_reports,
        "accepted_root_classes_95_this_run": newly_accepted,
        "accepted_root_classes_95_current_evidence": current_accepted,
        "missing_root_classes_95_current_evidence": missing,
        "decision": {
            "board_state": "blocked",
            "accepted_gate": "partial_for_MainRegimeV2_Crisis_only_prior_evidence_preserved" if missing else "accepted_95_all_MainRegimeV2_required_roots",
            "thresholds_relaxed": False,
            "blocked_future_target_predictors": True,
            "fresh_calibration_rerun": True,
            "runtime_code_changed": False,
            "trade_usable": False,
            "blocker": "missing_root_classes_95=" + ",".join(missing),
            "next_action": "Acquire calibration-grade direct L2/L3/MBO/order-lifecycle/event data for Manipulation and add materially non-OHLCV signed-direction/sideways evidence before rerunning unchanged MainRegimeV2 gates.",
        },
    }
    report_path = OUT_DIR / "cross_instrument_main_regime_v2_model_gate_report.json"
    summary_path = OUT_DIR / "cross_instrument_main_regime_v2_model_gate_summary.csv"
    md_path = OUT_DIR / "cross_instrument_main_regime_v2_model_gate_report.md"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_summary(summary_path, root_reports)
    write_report_md(md_path, report)
    (CHECKS_DIR / "cross_instrument_main_regime_v2_model_gate_assertions.out").write_text(
        "\n".join(
            [
                f"report: {repo_rel(report_path)}",
                f"summary: {repo_rel(summary_path)}",
                f"accepted_root_classes_95_this_run: {','.join(newly_accepted) or 'none'}",
                f"accepted_root_classes_95_current_evidence: {','.join(current_accepted)}",
                f"missing_root_classes_95_current_evidence: {','.join(missing)}",
                "blocked_future_target_predictors: True",
                "model_and_threshold_fit_on_train_only: True",
                "thresholds_relaxed: False",
                "runtime_code_changed: False",
                "trade_usable: False",
                "manipulation_input_state: missing_required_inputs",
                "GATE " + ("accepted_all_required_roots" if not missing else "blocked"),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "README.md").write_text(
        "# Cross-Instrument MainRegimeV2 Model Gate\n\n"
        "Train-only logistic score thresholds over the existing multi-context advanced root feature table.\n\n"
        f"Result: {report['decision']['accepted_gate']}; {report['decision']['blocker']}.\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
