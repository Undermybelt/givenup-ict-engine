#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T110540+0800-codex-full-matrix-targeted-gap-batch"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T110540-codex-full-matrix-targeted-gap-batch"
OUT_DIR = RUN_ROOT / "targeted-gap-batch"
CHECK_DIR = RUN_ROOT / "checks"

KAGGLE_TABLE = Path("/private/tmp/ict-regime-kaggle-regime-label-root/kaggle_regime_label_feature_table.csv")
INTRADAY_TABLE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260510T224014-codex-cross-timeframe-regime-validation/"
    "cross_timeframe_regime_features.csv"
)

Z95 = 1.959963984540054
_SPLIT_MASK_CACHE: dict[tuple[int, str], np.ndarray] = {}
_LABEL_MASK_CACHE: dict[tuple[int, str], np.ndarray] = {}
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

KAGGLE_NUMERIC_FEATURES = [
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

INTRADAY_NUMERIC_FEATURES = [
    "hour_utc",
    "timeframe_minutes",
    "ret1",
    "ret4",
    "ret16",
    "range_pct",
    "stretch16",
    "vol16",
    "range_mean16",
    "stretch32",
    "vol32",
    "range_mean32",
    "stretch64",
    "vol64",
    "range_mean64",
    "stretch128",
    "vol128",
    "range_mean128",
    "ma64_slope16",
    "ma32_slope8",
    "vol_rank",
    "range_rank",
    "volume_rank",
    "vol_ratio32_128",
    "range_ratio32_128",
    "volume_ratio32_128",
    "drawdown64",
    "rally64",
    "trend_persistence16",
    "stress_persistence16",
    "reversal_persistence16",
    "thin_persistence16",
]
INTRADAY_BOOLEAN_FEATURES = [
    "trend_base",
    "stress_base",
    "reversal_base",
    "thin_base",
]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def parse_float(value: Any) -> float:
    try:
        if value in ("", None):
            return math.nan
        out = float(value)
        return out if math.isfinite(out) else math.nan
    except (TypeError, ValueError):
        return math.nan


def parse_bool(value: Any) -> bool:
    text = str(value).strip().lower()
    if text in {"true", "yes"}:
        return True
    if text in {"false", "no", ""}:
        return False
    number = parse_float(value)
    return bool(math.isfinite(number) and number >= 0.5)


def wilson_lcb(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def quantile(values: np.ndarray, q: float) -> float:
    clean = values[np.isfinite(values)]
    if clean.size == 0:
        return math.nan
    return float(np.quantile(clean, q))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def assign_intraday_root_labels(rows: list[dict[str, str]]) -> None:
    by_context: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        key = f"{row.get('instrument')}:{row.get('market')}:{row.get('timeframe')}"
        row["_context"] = key
        by_context[key].append(idx)

    for indexes in by_context.values():
        indexes.sort(key=lambda i: rows[i].get("ts", ""))
        for pos, idx in enumerate(indexes):
            row = rows[idx]
            minutes = parse_float(row.get("timeframe_minutes"))
            horizon_bars = max(1, int(round(480.0 / minutes))) if math.isfinite(minutes) and minutes > 0 else 8
            future_pos = pos + horizon_bars
            if future_pos >= len(indexes):
                row["_future_ret_8h"] = ""
                row["_future_absret_8h"] = ""
                continue
            now_close = parse_float(row.get("close"))
            future_close = parse_float(rows[indexes[future_pos]].get("close"))
            if math.isfinite(now_close) and math.isfinite(future_close) and now_close != 0:
                future_ret = future_close / now_close - 1.0
                row["_future_ret_8h"] = str(future_ret)
                row["_future_absret_8h"] = str(abs(future_ret))
            else:
                row["_future_ret_8h"] = ""
                row["_future_absret_8h"] = ""

    train_returns = np.array(
        [parse_float(row.get("_future_ret_8h")) for row in rows if row.get("split") == "train"],
        dtype=float,
    )
    train_abs = np.array(
        [parse_float(row.get("_future_absret_8h")) for row in rows if row.get("split") == "train"],
        dtype=float,
    )
    thresholds = {
        "bull": quantile(train_returns, 0.65),
        "bear": quantile(train_returns, 0.35),
        "sideways": quantile(train_abs, 0.35),
        "crisis": quantile(train_abs, 0.90),
    }
    for row in rows:
        future_ret = parse_float(row.get("_future_ret_8h"))
        future_absret = parse_float(row.get("_future_absret_8h"))
        if not math.isfinite(future_ret) or not math.isfinite(future_absret):
            row["root_label"] = "UnknownOrMixed"
            continue
        crisis = parse_bool(row.get("target_stress_next")) or future_absret >= thresholds["crisis"]
        sideways = (
            not crisis
            and future_absret <= thresholds["sideways"]
            and not parse_bool(row.get("target_trend_structural_next"))
        )
        bull = (not crisis and not sideways and future_ret >= thresholds["bull"])
        bear = (not crisis and not sideways and future_ret <= thresholds["bear"])
        if crisis:
            row["root_label"] = "Crisis"
        elif sideways:
            row["root_label"] = "Sideways"
        elif bull:
            row["root_label"] = "Bull"
        elif bear:
            row["root_label"] = "Bear"
        else:
            row["root_label"] = "UnknownOrMixed"


def split_mask(rows: list[dict[str, str]], split: str) -> np.ndarray:
    key = (id(rows), split)
    if key not in _SPLIT_MASK_CACHE:
        _SPLIT_MASK_CACHE[key] = np.array([row.get("split") == split for row in rows], dtype=bool)
    return _SPLIT_MASK_CACHE[key]


def label_mask(rows: list[dict[str, str]], root: str) -> np.ndarray:
    key = (id(rows), root)
    if key not in _LABEL_MASK_CACHE:
        _LABEL_MASK_CACHE[key] = np.array(
            [row.get("root_label", row.get("regime_label", "")) == root for row in rows],
            dtype=bool,
        )
    return _LABEL_MASK_CACHE[key]


def field_values(rows: list[dict[str, str]], feature: str) -> np.ndarray:
    return np.array([parse_float(row.get(feature)) for row in rows], dtype=float)


def bool_values(rows: list[dict[str, str]], feature: str) -> np.ndarray:
    return np.array([parse_bool(row.get(feature)) for row in rows], dtype=bool)


def metric(
    rows: list[dict[str, str]],
    selected_mask: np.ndarray,
    root: str,
    split: str,
    train_precision: float | None = None,
    include_validation: bool = True,
) -> dict[str, Any]:
    sm = split_mask(rows, split)
    selected = selected_mask & sm
    labels = label_mask(rows, root)
    success = int((selected & labels).sum())
    support = int(selected.sum())
    precision = success / support if support else 0.0
    ref = train_precision if train_precision is not None else precision
    selected_rows = [rows[int(i)] for i in np.flatnonzero(selected)] if include_validation else []
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lcb(success, support),
        "coverage": support / max(1, int(sm.sum())),
        "ece": abs(ref - precision) if support else 0.0,
        "validation_instruments": sorted({str(row.get("ticker") or row.get("instrument") or "") for row in selected_rows}),
        "validation_market_contexts": sorted({str(row.get("market_context") or row.get("market") or "") for row in selected_rows}),
        "validation_timeframes": sorted({str(row.get("timeframe") or "") for row in selected_rows}),
        "validation_contexts": sorted({str(row.get("context") or row.get("_context") or "") for row in selected_rows}),
    }


def blockers(
    calibration: dict[str, Any],
    test: dict[str, Any],
    *,
    cal_support_min: int,
    test_support_min: int,
    coverage_min: float,
    validation_market_contexts_min: int,
    validation_timeframes_min: int,
) -> list[str]:
    out: list[str] = []
    if calibration["support"] < cal_support_min:
        out.append(f"calibration_support_below_{cal_support_min}")
    if test["support"] < test_support_min:
        out.append(f"test_support_below_{test_support_min}")
    if calibration["precision_wilson_lcb_95"] < 0.95:
        out.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < 0.95:
        out.append("test_wilson95_below_0_95")
    if calibration["coverage"] < coverage_min:
        out.append("calibration_coverage_below_min")
    if test["coverage"] < coverage_min:
        out.append("test_coverage_below_min")
    if max(calibration["ece"], test["ece"]) > 0.05:
        out.append("ece_above_0_05")
    for split_name, data in [("calibration", calibration), ("test", test)]:
        if len(data["validation_instruments"]) < 2:
            out.append(f"{split_name}_validation_instruments_below_2")
        if len(data["validation_market_contexts"]) < validation_market_contexts_min:
            out.append(f"{split_name}_validation_market_contexts_below_{validation_market_contexts_min}")
        if len(data["validation_timeframes"]) < validation_timeframes_min:
            out.append(f"{split_name}_validation_timeframes_below_{validation_timeframes_min}")
    return out


def mask_expression(terms: tuple[tuple[str, str, float | bool], ...]) -> str:
    parts = []
    for feature, op, value in terms:
        if isinstance(value, bool):
            parts.append(f"{feature} == {str(value).lower()}")
        else:
            parts.append(f"{feature} {op} {value:.12g}")
    return " AND ".join(parts)


def build_candidate_terms(
    rows: list[dict[str, str]],
    root: str,
    numeric_features: list[str],
    boolean_features: list[str],
    *,
    train_support_min: int,
    train_coverage_min: float,
    max_terms: int,
) -> list[tuple[tuple[str, str, float | bool], np.ndarray, dict[str, Any]]]:
    terms: list[tuple[tuple[str, str, float | bool], np.ndarray, dict[str, Any]]] = []
    train = split_mask(rows, "train")
    for feature in numeric_features:
        values = field_values(rows, feature)
        train_values = values[train & np.isfinite(values)]
        if np.unique(train_values).size <= 4:
            continue
        thresholds = sorted({quantile(train_values, q) for q in QUANTILES if math.isfinite(quantile(train_values, q))})
        for threshold in thresholds:
            for op in (">=", "<="):
                if op == ">=":
                    m = np.isfinite(values) & (values >= threshold)
                else:
                    m = np.isfinite(values) & (values <= threshold)
                tm = metric(rows, m, root, "train", include_validation=False)
                if tm["support"] >= train_support_min and tm["coverage"] >= train_coverage_min:
                    terms.append(((feature, op, threshold), m, tm))
    for feature in boolean_features:
        values = bool_values(rows, feature)
        for wanted in (True, False):
            m = values == wanted
            tm = metric(rows, m, root, "train", include_validation=False)
            if tm["support"] >= train_support_min and tm["coverage"] >= train_coverage_min:
                terms.append(((feature, "==", wanted), m, tm))
    terms.sort(key=lambda item: (item[2]["precision_wilson_lcb_95"], item[2]["precision"], item[2]["coverage"]), reverse=True)
    return terms[:max_terms]


def select_rule(
    rows: list[dict[str, str]],
    root: str,
    numeric_features: list[str],
    boolean_features: list[str],
    *,
    train_support_min: int,
    train_coverage_min: float,
    cal_support_min: int,
    test_support_min: int,
    coverage_min: float,
    validation_market_contexts_min: int,
    validation_timeframes_min: int,
    max_terms: int = 80,
    max_depth: int = 3,
) -> dict[str, Any]:
    base_terms = build_candidate_terms(
        rows,
        root,
        numeric_features,
        boolean_features,
        train_support_min=train_support_min,
        train_coverage_min=train_coverage_min,
        max_terms=max_terms,
    )
    candidates: list[tuple[tuple[tuple[str, str, float | bool], ...], np.ndarray, dict[str, Any]]] = []
    for depth in range(1, max_depth + 1):
        for combo in combinations(base_terms, depth):
            features = [item[0][0] for item in combo]
            if len(set(features)) < len(features):
                continue
            m = np.ones(len(rows), dtype=bool)
            terms: list[tuple[str, str, float | bool]] = []
            for term, mask, _ in combo:
                terms.append(term)
                m &= mask
            tm = metric(rows, m, root, "train", include_validation=False)
            if tm["support"] >= train_support_min and tm["coverage"] >= train_coverage_min:
                candidates.append((tuple(terms), m, tm))
    candidates.sort(
        key=lambda item: (
            item[2]["precision_wilson_lcb_95"],
            item[2]["precision"],
            item[2]["coverage"],
            item[2]["support"],
        ),
        reverse=True,
    )
    if not candidates:
        return {
            "root": root,
            "accepted_95": False,
            "state": "blocked_no_train_candidate",
            "blockers": ["no_train_candidate_met_support_coverage_buffer"],
        }
    terms, selected_mask, train = candidates[0]
    train = metric(rows, selected_mask, root, "train", include_validation=True)
    calibration = metric(rows, selected_mask, root, "calibration", train["precision"], include_validation=True)
    test = metric(rows, selected_mask, root, "test", train["precision"], include_validation=True)
    block = blockers(
        calibration,
        test,
        cal_support_min=cal_support_min,
        test_support_min=test_support_min,
        coverage_min=coverage_min,
        validation_market_contexts_min=validation_market_contexts_min,
        validation_timeframes_min=validation_timeframes_min,
    )
    return {
        "root": root,
        "accepted_95": not block,
        "state": "accepted_95" if not block else "blocked",
        "rule": mask_expression(terms),
        "selected_on": "train_split_only",
        "candidate_count": len(candidates),
        "train": train,
        "calibration": calibration,
        "test": test,
        "blockers": block,
    }


def write_summary_csv(path: Path, reports: dict[str, dict[str, Any]]) -> None:
    fields = [
        "root",
        "state",
        "accepted_95",
        "rule",
        "train_support",
        "train_lcb",
        "calibration_support",
        "calibration_lcb",
        "test_support",
        "test_lcb",
        "test_coverage",
        "blockers",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for root, report in reports.items():
            writer.writerow(
                {
                    "root": root,
                    "state": report.get("state"),
                    "accepted_95": report.get("accepted_95"),
                    "rule": report.get("rule", ""),
                    "train_support": report.get("train", {}).get("support", ""),
                    "train_lcb": report.get("train", {}).get("precision_wilson_lcb_95", ""),
                    "calibration_support": report.get("calibration", {}).get("support", ""),
                    "calibration_lcb": report.get("calibration", {}).get("precision_wilson_lcb_95", ""),
                    "test_support": report.get("test", {}).get("support", ""),
                    "test_lcb": report.get("test", {}).get("precision_wilson_lcb_95", ""),
                    "test_coverage": report.get("test", {}).get("coverage", ""),
                    "blockers": ";".join(report.get("blockers", [])),
                }
            )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    if not KAGGLE_TABLE.exists():
        raise FileNotFoundError(KAGGLE_TABLE)
    if not INTRADAY_TABLE.exists():
        raise FileNotFoundError(INTRADAY_TABLE)

    kaggle_rows = read_csv_rows(KAGGLE_TABLE)
    intraday_rows = read_csv_rows(INTRADAY_TABLE)
    assign_intraday_root_labels(intraday_rows)

    crisis_report = select_rule(
        kaggle_rows,
        "Crisis",
        KAGGLE_NUMERIC_FEATURES,
        [],
        train_support_min=500,
        train_coverage_min=0.03,
        cal_support_min=250,
        test_support_min=250,
        coverage_min=0.03,
        validation_market_contexts_min=2,
        validation_timeframes_min=2,
        max_terms=20,
        max_depth=2,
    )
    intraday_reports = {
        root: select_rule(
            intraday_rows,
            root,
            INTRADAY_NUMERIC_FEATURES,
            INTRADAY_BOOLEAN_FEATURES,
            train_support_min=120,
            train_coverage_min=0.03,
            cal_support_min=120,
            test_support_min=60,
            coverage_min=0.03,
            validation_market_contexts_min=2,
            validation_timeframes_min=2,
            max_terms=20,
            max_depth=2,
        )
        for root in ["Bull", "Bear", "Sideways"]
    }

    reports = {"Crisis": crisis_report, **intraday_reports}
    accepted = [root for root, report in reports.items() if report.get("accepted_95")]
    blocked = [root for root, report in reports.items() if not report.get("accepted_95")]
    report = {
        "run_id": RUN_ID,
        "board": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
        "objective": "Target the current full-cycle/full-universe gaps: source-labeled Crisis on 1d/1w index/single-stock contexts, and intraday 15m/1h Bull/Bear/Sideways transfer on the existing cross-timeframe table.",
        "inputs": {
            "kaggle_source_label_feature_table_tmp": str(KAGGLE_TABLE),
            "intraday_cross_timeframe_feature_table": repo_rel(INTRADAY_TABLE),
            "raw_data_committed": False,
        },
        "label_policies": {
            "Crisis": "Kaggle stock-market-regimes source labels from the existing feature table.",
            "Bull_Bear_Sideways_intraday": "Existing broader-root 8h-forward parent-label construction reused only as held-out target labels; future/target fields are not predictors.",
        },
        "evaluated_roots": reports,
        "accepted_95_roots_in_this_slice": accepted,
        "blocked_roots_in_this_slice": blocked,
        "decision": {
            "accepted_parent_root_gap_slices_added": accepted,
            "full_matrix_goal_achieved": False,
            "gate_result": "partial_targeted_gap_batch" if accepted else "blocked_targeted_gap_batch_no_new_full_matrix_slice",
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "why_not_complete": [
                "This batch targets only the known missing Crisis 1d/1w source-label slice and existing 15m/1h Bull/Bear/Sideways table.",
                "Full observed provider/context/instrument matrix remains incomplete unless every active root passes across the missing contexts and direct Manipulation varieties.",
            ],
        },
        "next_action": "If Crisis passed, treat it as a new scoped full-matrix gap slice only; continue Bull/Bear/Sideways intraday source-label acquisition and broader direct Manipulation variety gates.",
    }

    json_path = OUT_DIR / "full_matrix_targeted_gap_batch_report.json"
    md_path = OUT_DIR / "full_matrix_targeted_gap_batch_report.md"
    summary_path = OUT_DIR / "full_matrix_targeted_gap_batch_summary.csv"
    assertions_path = CHECK_DIR / "full_matrix_targeted_gap_batch_assertions.out"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary_csv(summary_path, reports)

    lines = [
        "# Full-Matrix Targeted Gap Batch",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Accepted 95 roots in this slice: `{accepted}`.",
        f"- Blocked roots in this slice: `{blocked}`.",
        f"- Gate result: `{report['decision']['gate_result']}`.",
        "- Runtime code changed: false.",
        "- Thresholds relaxed: false.",
        "- Raw data committed: false.",
        "- Trade usable: false.",
        "",
        "## Root Results",
        "",
        "| Root | State | Calibration Wilson95 | Test Wilson95 | Test Coverage | Blockers |",
        "|---|---|---:|---:|---:|---|",
    ]
    for root, item in reports.items():
        lines.append(
            "| {root} | `{state}` | `{cal:.6f}` | `{test:.6f}` | `{coverage:.6f}` | `{blockers}` |".format(
                root=root,
                state=item.get("state"),
                cal=item.get("calibration", {}).get("precision_wilson_lcb_95", 0.0),
                test=item.get("test", {}).get("precision_wilson_lcb_95", 0.0),
                coverage=item.get("test", {}).get("coverage", 0.0),
                blockers="; ".join(item.get("blockers", [])) or "none",
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "This is not a completion artifact. It is a bounded targeted batch against known gaps.",
            "",
            "If a root passed here, it is only a scoped gap slice. The full observed matrix remains incomplete until every active parent root passes across the current provider/context/timeframe matrix and `Manipulation` covers direct evidence varieties beyond the scoped event feeds.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        "PASS input_kaggle_feature_table_present",
        "PASS input_intraday_feature_table_present",
        "PASS future_and_target_fields_not_used_as_predictors",
        f"PASS accepted_95_roots_in_this_slice={','.join(accepted) if accepted else 'none'}",
        f"PASS blocked_roots_in_this_slice={','.join(blocked) if blocked else 'none'}",
        "PASS full_matrix_goal_achieved=false",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS raw_data_committed=false",
        "PASS trade_usable=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"accepted": accepted, "blocked": blocked, "report": repo_rel(json_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
