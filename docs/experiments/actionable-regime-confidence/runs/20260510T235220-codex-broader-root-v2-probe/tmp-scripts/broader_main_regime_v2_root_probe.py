from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260510T235220-codex-broader-root-v2-probe"
)
INPUT_FEATURE_TABLE = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260510T224014-codex-cross-timeframe-regime-validation/"
    "cross_timeframe_regime_features.csv"
)
OUTPUT_DIR = RUN_ROOT / "root-v2-broader"

LOOP_ID = "20260510T235220+0800-codex-broader-root-v2-probe"
BLOCKED_PREDICTOR_PREFIXES = ("future_", "target_")
ROOT_CLASSES = ["Bull", "Bear", "Sideways", "Crisis", "Manipulation", "UnknownOrMixed"]
EVALUATED_ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
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

NUMERIC_FEATURES = [
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
BOOLEAN_FEATURES = [
    "trend_base",
    "stress_base",
    "reversal_base",
    "thin_base",
]


def _float(value: Any) -> float:
    try:
        if value in ("", None):
            return math.nan
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _bool(value: Any) -> bool:
    text = str(value).strip().lower()
    if text in {"true", "yes"}:
        return True
    if text in {"false", "no", ""}:
        return False
    number = _float(value)
    return math.isfinite(number) and number >= 0.5


def _quantile(values: list[float], ratio: float) -> float:
    clean = sorted(value for value in values if math.isfinite(value))
    if not clean:
        return math.nan
    idx = min(len(clean) - 1, max(0, int((len(clean) - 1) * ratio)))
    return clean[idx]


def _wilson(success: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    center = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return (center - margin) / denom


def _read_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with INPUT_FEATURE_TABLE.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            row["_context"] = f"{row['instrument']}:{row['market']}:{row['timeframe']}"
            rows.append(row)
    by_context: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_context[str(row["_context"])].append(row)
    for context_rows in by_context.values():
        context_rows.sort(key=lambda item: str(item["ts"]))
        for idx, row in enumerate(context_rows):
            minutes = _float(row.get("timeframe_minutes"))
            horizon_bars = max(1, int(round(480.0 / minutes))) if minutes else 8
            future_idx = idx + horizon_bars
            if future_idx < len(context_rows):
                now_close = _float(row.get("close"))
                future_close = _float(context_rows[future_idx].get("close"))
                if math.isfinite(now_close) and math.isfinite(future_close) and now_close != 0:
                    future_ret = future_close / now_close - 1.0
                    row["_future_ret_8h"] = future_ret
                    row["_future_absret_8h"] = abs(future_ret)
    return [
        row
        for row in rows
        if row.get("split") in {"train", "calibration", "test"}
        and math.isfinite(_float(row.get("_future_ret_8h")))
    ]


def _root_thresholds(train_rows: list[dict[str, Any]]) -> dict[str, float]:
    future_returns = [_float(row.get("_future_ret_8h")) for row in train_rows]
    future_abs_returns = [_float(row.get("_future_absret_8h")) for row in train_rows]
    return {
        "bull_future_ret_8h_train_q65": _quantile(future_returns, 0.65),
        "bear_future_ret_8h_train_q35": _quantile(future_returns, 0.35),
        "sideways_future_absret_8h_train_q35": _quantile(future_abs_returns, 0.35),
        "crisis_future_absret_8h_train_q90": _quantile(future_abs_returns, 0.90),
    }


def _assign_root_label(row: dict[str, Any], thresholds: dict[str, float]) -> str:
    future_ret = _float(row.get("_future_ret_8h"))
    future_absret = _float(row.get("_future_absret_8h"))
    crisis = _bool(row.get("target_stress_next")) or (
        math.isfinite(future_absret)
        and future_absret >= thresholds["crisis_future_absret_8h_train_q90"]
    )
    sideways = (
        not crisis
        and math.isfinite(future_absret)
        and future_absret <= thresholds["sideways_future_absret_8h_train_q35"]
        and not _bool(row.get("target_trend_structural_next"))
    )
    bull = (
        not crisis
        and not sideways
        and math.isfinite(future_ret)
        and future_ret >= thresholds["bull_future_ret_8h_train_q65"]
    )
    bear = (
        not crisis
        and not sideways
        and math.isfinite(future_ret)
        and future_ret <= thresholds["bear_future_ret_8h_train_q35"]
    )
    if crisis:
        return "Crisis"
    if sideways:
        return "Sideways"
    if bull:
        return "Bull"
    if bear:
        return "Bear"
    return "UnknownOrMixed"


def _metric(
    label: str,
    selected_mask: np.ndarray,
    split_mask: np.ndarray,
    labels: np.ndarray,
    rows: list[dict[str, Any]],
    include_validation: bool = True,
) -> dict[str, Any]:
    selected = selected_mask & split_mask
    support = int(selected.sum())
    success = int(((labels == label) & selected).sum())
    precision = success / support if support else 0.0
    selected_rows = [rows[idx] for idx in np.flatnonzero(selected)] if include_validation else []
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": _wilson(success, support),
        "coverage": support / max(1, int(split_mask.sum())),
        "validation_instruments": sorted({str(row.get("instrument", "")) for row in selected_rows}),
        "validation_market_contexts": sorted({str(row.get("market", "")) for row in selected_rows}),
        "validation_timeframes": sorted({str(row.get("timeframe", "")) for row in selected_rows}),
        "validation_contexts": sorted({str(row.get("_context", "")) for row in selected_rows}),
    }


def _passes_gate(calibration: dict[str, Any], test: dict[str, Any], ece: float) -> bool:
    return (
        calibration["support"] >= ACCEPTANCE_95["calibration_support_min"]
        and test["support"] >= ACCEPTANCE_95["test_support_min"]
        and calibration["precision_wilson_lcb_95"]
        >= ACCEPTANCE_95["precision_wilson_lcb_95_min"]
        and test["precision_wilson_lcb_95"] >= ACCEPTANCE_95["precision_wilson_lcb_95_min"]
        and ece <= ACCEPTANCE_95["ece_max"]
        and test["coverage"] >= ACCEPTANCE_95["coverage_min"]
        and len(test["validation_instruments"]) >= ACCEPTANCE_95["validation_instruments_min"]
        and len(test["validation_market_contexts"])
        >= ACCEPTANCE_95["validation_market_contexts_min"]
        and len(test["validation_timeframes"]) >= ACCEPTANCE_95["validation_timeframes_min"]
    )


def _blockers(calibration: dict[str, Any], test: dict[str, Any], ece: float) -> list[str]:
    blockers: list[str] = []
    if calibration["support"] < ACCEPTANCE_95["calibration_support_min"]:
        blockers.append("calibration_support_below_120")
    if test["support"] < ACCEPTANCE_95["test_support_min"]:
        blockers.append("test_support_below_60")
    if calibration["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        blockers.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        blockers.append("test_wilson95_below_0_95")
    if ece > ACCEPTANCE_95["ece_max"]:
        blockers.append("ece_above_0_05")
    if test["coverage"] < ACCEPTANCE_95["coverage_min"]:
        blockers.append("coverage_below_0_03")
    if len(test["validation_instruments"]) < ACCEPTANCE_95["validation_instruments_min"]:
        blockers.append("validation_instruments_below_2")
    if len(test["validation_market_contexts"]) < ACCEPTANCE_95["validation_market_contexts_min"]:
        blockers.append("validation_market_contexts_below_2")
    if len(test["validation_timeframes"]) < ACCEPTANCE_95["validation_timeframes_min"]:
        blockers.append("validation_timeframes_below_2")
    return blockers


@dataclass(frozen=True)
class Candidate:
    method: str
    rule: str
    mask: np.ndarray
    model_details: dict[str, Any] | None = None


def _candidate_result(
    label: str,
    candidate: Candidate,
    train_mask: np.ndarray,
    calibration_mask: np.ndarray,
    test_mask: np.ndarray,
    labels: np.ndarray,
    rows: list[dict[str, Any]],
    include_validation: bool = True,
) -> dict[str, Any]:
    train = _metric(label, candidate.mask, train_mask, labels, rows, include_validation)
    calibration = _metric(label, candidate.mask, calibration_mask, labels, rows, include_validation)
    test = _metric(label, candidate.mask, test_mask, labels, rows, include_validation)
    ece = abs(test["precision"] - calibration["precision"]) if calibration["support"] else 1.0
    return {
        "method": candidate.method,
        "rule": candidate.rule,
        "train": train,
        "calibration": calibration,
        "test": test,
        "ece": ece,
        "accepted_95": _passes_gate(calibration, test, ece),
        "blockers": _blockers(calibration, test, ece),
        "model_details": candidate.model_details or {},
    }


def _build_feature_arrays(rows: list[dict[str, Any]]) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    numeric: dict[str, np.ndarray] = {}
    boolean: dict[str, np.ndarray] = {}
    for name in NUMERIC_FEATURES:
        if any(name.startswith(prefix) for prefix in BLOCKED_PREDICTOR_PREFIXES):
            continue
        values = np.array([_float(row.get(name)) for row in rows], dtype=float)
        if np.isfinite(values).sum() >= 120:
            median = float(np.nanmedian(values))
            values = np.where(np.isfinite(values), values, median)
            numeric[name] = values
    for name in BOOLEAN_FEATURES:
        if any(name.startswith(prefix) for prefix in BLOCKED_PREDICTOR_PREFIXES):
            continue
        boolean[name] = np.array([_bool(row.get(name)) for row in rows], dtype=bool)
    return numeric, boolean


def _atom_candidates(
    *,
    numeric: dict[str, np.ndarray],
    boolean: dict[str, np.ndarray],
    train_mask: np.ndarray,
) -> list[Candidate]:
    atoms: list[Candidate] = []
    for name, values in boolean.items():
        atoms.append(Candidate("rule_atom", name, values))
        atoms.append(Candidate("rule_atom", f"NOT {name}", ~values))
    for name, values in numeric.items():
        train_values = values[train_mask]
        for ratio in [
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
        ]:
            cut = float(np.quantile(train_values, ratio))
            atoms.append(Candidate("rule_atom", f"{name} >= {cut:.12g}", values >= cut))
            atoms.append(Candidate("rule_atom", f"{name} <= {cut:.12g}", values <= cut))
    return atoms


def _rule_candidates_for_label(
    *,
    label: str,
    atoms: list[Candidate],
    train_mask: np.ndarray,
    calibration_mask: np.ndarray,
    test_mask: np.ndarray,
    labels: np.ndarray,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    atom_results: list[tuple[Candidate, dict[str, Any]]] = []
    for atom in atoms:
        result = _candidate_result(
            label,
            atom,
            train_mask,
            calibration_mask,
            test_mask,
            labels,
            rows,
            include_validation=False,
        )
        train = result["train"]
        if train["support"] >= 120 and train["coverage"] >= 0.03:
            atom_results.append((atom, result))
    atom_results.sort(
        key=lambda item: (
            item[1]["train"]["precision_wilson_lcb_95"],
            item[1]["train"]["precision"],
            item[1]["train"]["support"],
        ),
        reverse=True,
    )
    top_atoms = [item[0] for item in atom_results[:35]]
    candidates: list[Candidate] = [item[0] for item in atom_results]
    for left, right in combinations(top_atoms, 2):
        candidates.append(
            Candidate(
                "rule_pair",
                f"{left.rule} AND {right.rule}",
                left.mask & right.mask,
            )
        )

    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate.rule in seen:
            continue
        seen.add(candidate.rule)
        result = _candidate_result(
            label,
            candidate,
            train_mask,
            calibration_mask,
            test_mask,
            labels,
            rows,
            include_validation=False,
        )
        if result["train"]["support"] < 120 or result["train"]["coverage"] < 0.03:
            continue
        results.append(result)
    results.sort(
        key=lambda item: (
            item["accepted_95"],
            item["calibration"]["precision_wilson_lcb_95"],
            item["calibration"]["precision"],
            item["calibration"]["support"],
        ),
        reverse=True,
    )
    top_candidates = results[:50]
    enriched: list[dict[str, Any]] = []
    for item in top_candidates:
        matching = next(candidate for candidate in candidates if candidate.rule == item["rule"])
        enriched.append(
            _candidate_result(
                label,
                matching,
                train_mask,
                calibration_mask,
                test_mask,
                labels,
                rows,
                include_validation=True,
            )
        )
    enriched.sort(
        key=lambda item: (
            item["accepted_95"],
            item["calibration"]["precision_wilson_lcb_95"],
            item["calibration"]["precision"],
            item["calibration"]["support"],
        ),
        reverse=True,
    )
    return enriched


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(values, -40.0, 40.0)))


def _model_candidates_for_label(
    *,
    label: str,
    numeric: dict[str, np.ndarray],
    train_mask: np.ndarray,
    calibration_mask: np.ndarray,
    test_mask: np.ndarray,
    labels: np.ndarray,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    feature_names = list(numeric)
    if not feature_names:
        return []
    x = np.column_stack([numeric[name] for name in feature_names])
    x_train = x[train_mask]
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0)
    std = np.where(std > 1e-12, std, 1.0)
    x_scaled = (x - mean) / std
    x_train_scaled = x_scaled[train_mask]
    y_train = (labels[train_mask] == label).astype(float)
    pos = max(1.0, float(y_train.sum()))
    neg = max(1.0, float(len(y_train) - y_train.sum()))
    weights = np.where(y_train > 0.5, 0.5 / pos, 0.5 / neg)
    coef = np.zeros(x_train_scaled.shape[1], dtype=float)
    intercept = 0.0
    lr = 0.25
    l2 = 0.015
    for _ in range(700):
        logits = x_train_scaled @ coef + intercept
        pred = _sigmoid(logits)
        err = (pred - y_train) * weights
        grad = x_train_scaled.T @ err + l2 * coef
        bias_grad = float(err.sum())
        coef -= lr * grad
        intercept -= lr * bias_grad
    scores = _sigmoid(x_scaled @ coef + intercept)
    cal_scores = scores[calibration_mask]
    thresholds = sorted(
        {
            float(np.quantile(cal_scores, ratio))
            for ratio in [
                0.50,
                0.55,
                0.60,
                0.65,
                0.70,
                0.75,
                0.80,
                0.85,
                0.90,
                0.92,
                0.94,
                0.96,
                0.97,
                0.98,
                0.99,
            ]
        }
    )
    top_coefficients = sorted(
        [
            {"feature": name, "coefficient": float(value)}
            for name, value in zip(feature_names, coef, strict=True)
        ],
        key=lambda item: abs(item["coefficient"]),
        reverse=True,
    )[:12]
    results: list[dict[str, Any]] = []
    for threshold in thresholds:
        candidate = Candidate(
            "linear_score_threshold",
            f"linear_current_past_score_{label} >= {threshold:.12g}",
            scores >= threshold,
            {
                "threshold": threshold,
                "intercept": float(intercept),
                "top_coefficients": top_coefficients,
            },
        )
        result = _candidate_result(
            label,
            candidate,
            train_mask,
            calibration_mask,
            test_mask,
            labels,
            rows,
            include_validation=False,
        )
        if result["calibration"]["support"] < 120 or result["calibration"]["coverage"] < 0.03:
            continue
        results.append(result)
    results.sort(
        key=lambda item: (
            item["accepted_95"],
            item["calibration"]["precision_wilson_lcb_95"],
            item["calibration"]["precision"],
            item["calibration"]["support"],
        ),
        reverse=True,
    )
    top_results = results[:20]
    enriched: list[dict[str, Any]] = []
    for item in top_results:
        threshold = float(item["model_details"]["threshold"])
        candidate = Candidate(
            "linear_score_threshold",
            f"linear_current_past_score_{label} >= {threshold:.12g}",
            scores >= threshold,
            {
                "threshold": threshold,
                "intercept": float(intercept),
                "top_coefficients": top_coefficients,
            },
        )
        enriched.append(
            _candidate_result(
                label,
                candidate,
                train_mask,
                calibration_mask,
                test_mask,
                labels,
                rows,
                include_validation=True,
            )
        )
    enriched.sort(
        key=lambda item: (
            item["accepted_95"],
            item["calibration"]["precision_wilson_lcb_95"],
            item["calibration"]["precision"],
            item["calibration"]["support"],
        ),
        reverse=True,
    )
    return enriched


def _root_report(
    *,
    label: str,
    atoms: list[Candidate],
    numeric: dict[str, np.ndarray],
    train_mask: np.ndarray,
    calibration_mask: np.ndarray,
    test_mask: np.ndarray,
    labels: np.ndarray,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    rule_results = _rule_candidates_for_label(
        label=label,
        atoms=atoms,
        train_mask=train_mask,
        calibration_mask=calibration_mask,
        test_mask=test_mask,
        labels=labels,
        rows=rows,
    )
    model_results = _model_candidates_for_label(
        label=label,
        numeric=numeric,
        train_mask=train_mask,
        calibration_mask=calibration_mask,
        test_mask=test_mask,
        labels=labels,
        rows=rows,
    )
    all_candidates = rule_results + model_results
    all_candidates.sort(
        key=lambda item: (
            item["accepted_95"],
            item["calibration"]["precision_wilson_lcb_95"],
            item["calibration"]["precision"],
            item["calibration"]["support"],
        ),
        reverse=True,
    )
    accepted = [item for item in all_candidates if item["accepted_95"]]
    diagnostic = sorted(
        all_candidates,
        key=lambda item: (
            item["test"]["precision_wilson_lcb_95"],
            item["test"]["precision"],
            item["test"]["support"],
        ),
        reverse=True,
    )[:5]
    return {
        "root_class": label,
        "state": "accepted_95" if accepted else "blocked",
        "accepted_candidate_count": len(accepted),
        "selected_candidate": accepted[0] if accepted else (all_candidates[0] if all_candidates else None),
        "top_calibration_selected_candidates": all_candidates[:10],
        "best_test_diagnostics_not_selection": diagnostic,
    }


def _schema(
    thresholds: dict[str, float],
    row_counts: dict[str, dict[str, int]],
    context_counts: dict[str, int],
) -> dict[str, Any]:
    return {
        "schema_version": "main-regime-v2-broader-target-schema/v1",
        "root_axis": ["Bull", "Bear", "Sideways", "Crisis"],
        "manipulation_treatment": "fifth_main_class_or_overlay_fail_closed",
        "residual_bucket": "UnknownOrMixed",
        "input_feature_table": str(INPUT_FEATURE_TABLE),
        "chronological_split": "source split column from 224014 cross-timeframe table",
        "forward_horizon": "8h derived per context from close[t + round(480 / timeframe_minutes)]",
        "blocked_predictor_prefixes": list(BLOCKED_PREDICTOR_PREFIXES),
        "predictor_features_used": {
            "numeric": NUMERIC_FEATURES,
            "boolean": BOOLEAN_FEATURES,
            "excluded_current_fields": [
                "open",
                "high",
                "low",
                "close",
                "volume",
                "count",
                "raw moving averages and raw volume means",
            ],
        },
        "target_definitions": {
            "Crisis": (
                "target_stress_next == true OR derived_future_absret_8h >= train_q90; "
                "evaluated before Bull/Bear/Sideways"
            ),
            "Sideways": (
                "derived_future_absret_8h <= train_q35 AND target_trend_structural_next == false "
                "AND NOT Crisis"
            ),
            "Bull": "derived_future_ret_8h >= train_q65 AND NOT Crisis AND NOT Sideways",
            "Bear": "derived_future_ret_8h <= train_q35 AND NOT Crisis AND NOT Sideways",
            "Manipulation": (
                "not materialized from this OHLCV-derived table; requires direct tick/order-flow/"
                "L2/order-lifecycle or crypto event/social evidence"
            ),
            "UnknownOrMixed": "residual bucket after Crisis/Sideways/Bull/Bear",
        },
        "train_thresholds": thresholds,
        "row_counts_by_split_and_root": row_counts,
        "context_counts": context_counts,
        "acceptance_95": ACCEPTANCE_95,
    }


def _crosswalk() -> dict[str, Any]:
    return {
        "schema_version": "main-regime-v2-crosswalk/v2",
        "rule": "sub-regime packets are evidence only and cannot promote a root class without this root gate",
        "crosswalk": {
            "Bull": {
                "sub_regime_evidence": ["TrendExpansion"],
                "promotion_requirement": "signed positive 8h forward root packet",
            },
            "Bear": {
                "sub_regime_evidence": ["TrendExpansion", "ExtremeStress"],
                "promotion_requirement": "signed negative 8h forward root packet separate from Crisis",
            },
            "Sideways": {
                "sub_regime_evidence": ["RangeConsolidation"],
                "promotion_requirement": "low-forward-absolute-return range/chop root packet plus residual bucket",
            },
            "Crisis": {
                "sub_regime_evidence": ["ExtremeStress"],
                "promotion_requirement": "tail/stress/liquidity-cliff root packet, separate from ordinary Bear",
            },
            "Manipulation": {
                "sub_regime_evidence": [],
                "blocked_context_only": ["ThinLiquidity", "SessionLiquidityCoreViable"],
                "promotion_requirement": "direct non-OHLCV manipulation inputs",
                "failure_state": "missing_required_inputs",
            },
            "UnknownOrMixed": {
                "sub_regime_evidence": [],
                "promotion_requirement": "explicit residual bucket, not a tradable accepted class",
            },
        },
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _write_summary_csv(path: Path, reports: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "root_class",
        "state",
        "accepted_candidate_count",
        "selected_method",
        "selected_rule",
        "calibration_support",
        "calibration_wilson95",
        "calibration_precision",
        "test_support",
        "test_wilson95",
        "test_precision",
        "test_coverage",
        "ece",
        "test_instruments",
        "test_market_contexts",
        "test_timeframes",
        "blockers",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for report in reports:
            selected = report.get("selected_candidate") or {}
            calibration = selected.get("calibration", {})
            test = selected.get("test", {})
            writer.writerow(
                {
                    "root_class": report["root_class"],
                    "state": report["state"],
                    "accepted_candidate_count": report["accepted_candidate_count"],
                    "selected_method": selected.get("method", ""),
                    "selected_rule": selected.get("rule", ""),
                    "calibration_support": calibration.get("support", 0),
                    "calibration_wilson95": calibration.get("precision_wilson_lcb_95", 0.0),
                    "calibration_precision": calibration.get("precision", 0.0),
                    "test_support": test.get("support", 0),
                    "test_wilson95": test.get("precision_wilson_lcb_95", 0.0),
                    "test_precision": test.get("precision", 0.0),
                    "test_coverage": test.get("coverage", 0.0),
                    "ece": selected.get("ece", 1.0),
                    "test_instruments": ";".join(test.get("validation_instruments", [])),
                    "test_market_contexts": ";".join(test.get("validation_market_contexts", [])),
                    "test_timeframes": ";".join(test.get("validation_timeframes", [])),
                    "blockers": ";".join(selected.get("blockers", [])),
                }
            )


def main() -> int:
    rows = _read_rows()
    train_rows = [row for row in rows if row.get("split") == "train"]
    thresholds = _root_thresholds(train_rows)
    for row in rows:
        row["_root_label"] = _assign_root_label(row, thresholds)

    labels = np.array([row["_root_label"] for row in rows], dtype=object)
    train_mask = np.array([row.get("split") == "train" for row in rows], dtype=bool)
    calibration_mask = np.array([row.get("split") == "calibration" for row in rows], dtype=bool)
    test_mask = np.array([row.get("split") == "test" for row in rows], dtype=bool)
    numeric, boolean = _build_feature_arrays(rows)
    atoms = _atom_candidates(numeric=numeric, boolean=boolean, train_mask=train_mask)

    row_counts: dict[str, dict[str, int]] = {}
    for split_name, split_mask in [
        ("train", train_mask),
        ("calibration", calibration_mask),
        ("test", test_mask),
    ]:
        counts = Counter(labels[split_mask])
        row_counts[split_name] = {label: int(counts.get(label, 0)) for label in ROOT_CLASSES}
    context_counts = Counter(str(row["_context"]) for row in rows)

    reports = [
        _root_report(
            label=label,
            atoms=atoms,
            numeric=numeric,
            train_mask=train_mask,
            calibration_mask=calibration_mask,
            test_mask=test_mask,
            labels=labels,
            rows=rows,
        )
        for label in EVALUATED_ROOTS
    ]
    manipulation_report = {
        "root_class": "Manipulation",
        "state": "missing_required_inputs",
        "accepted_candidate_count": 0,
        "selected_candidate": {
            "method": "required_input_gate",
            "rule": "",
            "calibration": {"support": 0, "precision_wilson_lcb_95": 0.0, "precision": 0.0},
            "test": {
                "support": 0,
                "precision_wilson_lcb_95": 0.0,
                "precision": 0.0,
                "coverage": 0.0,
                "validation_instruments": [],
                "validation_market_contexts": [],
                "validation_timeframes": [],
            },
            "ece": 1.0,
            "accepted_95": False,
            "blockers": ["missing_required_inputs", "proxy_only_low_confidence"],
        },
        "required_inputs": [
            "tick/trade tape with aggressor side or enough fields to infer order-flow imbalance",
            "bid/ask quotes or L2 depth snapshots",
            "order lifecycle anomalies",
            "venue/liquidity-taking behavior",
            "crypto event/social/mempool evidence when applicable",
        ],
        "explicit_non_evidence": [
            "ThinLiquidity",
            "SessionLiquidityCoreViable",
            "volume ratios",
            "daily range compression",
            "sweep-like OHLCV shapes",
        ],
    }
    all_reports = reports + [manipulation_report]
    accepted_roots = [item["root_class"] for item in all_reports if item["state"] == "accepted_95"]
    blocked_roots = [item["root_class"] for item in all_reports if item["state"] != "accepted_95"]

    calibration_report = {
        "schema_version": "main-regime-v2-broader-root-calibration/v1",
        "loop_id": LOOP_ID,
        "run_root": str(RUN_ROOT),
        "objective": (
            "Rerun corrected MainRegimeV2 root gates on the broader 224014 15m/1h table "
            "with derived 8h signed targets and current/past predictors only."
        ),
        "input_feature_table": str(INPUT_FEATURE_TABLE),
        "blocked_predictor_prefixes": list(BLOCKED_PREDICTOR_PREFIXES),
        "target_schema": str(OUTPUT_DIR / "main_regime_v2_broader_target_schema.json"),
        "crosswalk": str(OUTPUT_DIR / "main_regime_v2_broader_crosswalk.json"),
        "acceptance_95": ACCEPTANCE_95,
        "root_reports": all_reports,
        "decision": {
            "board_state": "blocked",
            "accepted_95_root_classes": accepted_roots,
            "blocked_root_classes": blocked_roots,
            "accepted_95_all_main_regime_v2_roots": len(blocked_roots) == 0,
            "trade_usable": False,
            "thresholds_relaxed": False,
            "predictor_leakage_guard": {
                "future_prefix_blocked": True,
                "target_prefix_blocked": True,
                "future_fields_used_only_for_target": [
                    "_future_ret_8h",
                    "_future_absret_8h",
                ],
            },
            "why_not_complete": [
                "Not every MainRegimeV2 root class passed the unchanged 95% gate.",
                "Manipulation remains fail-closed because the source table has OHLCV-derived context only and no direct microstructure/order-flow/order-lifecycle inputs.",
            ],
            "next_action": (
                "Add direct Manipulation inputs and stronger root-specific Bull/Bear/Sideways/Crisis "
                "features, then rerun the unchanged root gate without promoting sub-regime packets."
            ),
        },
    }

    _write_json(OUTPUT_DIR / "main_regime_v2_broader_target_schema.json", _schema(thresholds, row_counts, dict(context_counts)))
    _write_json(OUTPUT_DIR / "main_regime_v2_broader_crosswalk.json", _crosswalk())
    _write_json(OUTPUT_DIR / "main_regime_v2_broader_root_calibration_report.json", calibration_report)
    _write_summary_csv(OUTPUT_DIR / "main_regime_v2_broader_root_probe_summary.csv", all_reports)
    (RUN_ROOT / "README.md").write_text(
        "# Broader MainRegimeV2 Root Probe\n\n"
        "This run reruns the corrected MainRegimeV2 root gate on the broader cross-timeframe "
        "feature table. It derives 8h forward targets per context and blocks all `future_*` "
        "and `target_*` fields from predictor use. Existing subtype packets remain evidence only.\n\n"
        f"- input feature table: `{INPUT_FEATURE_TABLE}`\n"
        f"- schema: `{OUTPUT_DIR / 'main_regime_v2_broader_target_schema.json'}`\n"
        f"- crosswalk: `{OUTPUT_DIR / 'main_regime_v2_broader_crosswalk.json'}`\n"
        f"- calibration report: `{OUTPUT_DIR / 'main_regime_v2_broader_root_calibration_report.json'}`\n"
        f"- summary CSV: `{OUTPUT_DIR / 'main_regime_v2_broader_root_probe_summary.csv'}`\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": True,
                "accepted_roots": accepted_roots,
                "blocked_roots": blocked_roots,
                "report": str(OUTPUT_DIR / "main_regime_v2_broader_root_calibration_report.json"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
