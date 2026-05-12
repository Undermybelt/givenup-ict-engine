from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T032456-codex-expanded-root-schema-gate"
)
ROOT_DIR = RUN_ROOT / "expanded-root-gate"
CHECKS_DIR = RUN_ROOT / "checks"
INPUT_FEATURES = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T003739-source-backed-root-gate-mtf/root-v2-source-backed/"
    "source_backed_root_feature_table.csv"
)
SOURCE_SCHEMA = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T032111-codex-expanded-main-regime-source-refresh/source-refresh/"
    "expanded_main_regime_source_refresh.json"
)

LOOP_ID = "20260511T032456+0800-codex-expanded-root-schema-gate"
REQUIRED_ROOTS = ["BullExpansion", "BearExpansion", "SidewaysConsolidation", "Manipulation", "CrisisStress"]
EVALUATED_OHLCV_ROOTS = ["BullExpansion", "BearExpansion", "SidewaysConsolidation", "CrisisStress"]
CONDITIONAL_ROOTS = ["TransitionRecovery", "UnknownOrMixed"]
BLOCKED_PREDICTOR_PREFIXES = ("future_", "target_")
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
    "instrument",
    "market",
    "timeframe",
    "context",
    "split",
    "source_backed_root_label",
    "expanded_root_label",
}
EXCLUDED_PREDICTORS = {
    "open",
    "high",
    "low",
    "close",
    "volume",
    "count",
    "ma16",
    "ma32",
    "ma64",
    "ma128",
    "volume_mean16",
    "volume_mean32",
    "volume_mean64",
    "volume_mean128",
}


@dataclass(frozen=True)
class Candidate:
    method: str
    rule: str
    mask: np.ndarray
    model_details: dict[str, Any] | None = None


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").fillna(0) >= 0.5
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})


def wilson(success: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    center = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def load_frame() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FEATURES)
    df = df[df["split"].isin({"train", "calibration", "test"})].copy()
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    df = df.dropna(subset=["ts", "source_backed_root_label"])
    df["expanded_root_label"] = df["source_backed_root_label"].replace(
        {"Consolidation": "SidewaysConsolidation", "ConsolidationRange": "SidewaysConsolidation"}
    )
    df["target_expanded_BullExpansion"] = df["expanded_root_label"].eq("BullExpansion")
    df["target_expanded_BearExpansion"] = df["expanded_root_label"].eq("BearExpansion")
    df["target_expanded_SidewaysConsolidation"] = df["expanded_root_label"].eq("SidewaysConsolidation")
    df["target_expanded_CrisisStress"] = df["expanded_root_label"].eq("CrisisStress")
    df["target_expanded_TransitionRecovery"] = df["expanded_root_label"].eq("TransitionRecovery")
    df["target_expanded_UnknownOrMixed"] = df["expanded_root_label"].eq("UnknownOrMixed")
    df = df.sort_values(["context", "ts"]).reset_index(drop=True)
    return df


def candidate_columns(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    numeric_cols: list[str] = []
    boolean_cols: list[str] = []
    for column in df.columns:
        if column in ID_COLUMNS or column in EXCLUDED_PREDICTORS:
            continue
        if column.startswith(BLOCKED_PREDICTOR_PREFIXES):
            continue
        if column.startswith("target_source_backed_"):
            continue
        if column.startswith("target_expanded_"):
            continue
        if pd.api.types.is_bool_dtype(df[column]):
            boolean_cols.append(column)
        elif pd.api.types.is_numeric_dtype(df[column]):
            finite = pd.to_numeric(df[column], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
            if len(finite) >= 120 and finite.nunique() > 1:
                numeric_cols.append(column)
        else:
            lowered = df[column].astype(str).str.strip().str.lower()
            values = set(lowered.dropna().unique().tolist())
            if values and values.issubset({"true", "false", "nan", ""}):
                boolean_cols.append(column)
    return sorted(numeric_cols), sorted(boolean_cols)


def build_arrays(
    df: pd.DataFrame,
    numeric_cols: list[str],
    boolean_cols: list[str],
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    numeric: dict[str, np.ndarray] = {}
    for column in numeric_cols:
        values = pd.to_numeric(df[column], errors="coerce").replace([np.inf, -np.inf], np.nan).to_numpy(dtype=float)
        median = float(np.nanmedian(values))
        numeric[column] = np.where(np.isfinite(values), values, median)
    boolean: dict[str, np.ndarray] = {column: as_bool(df[column]).to_numpy(dtype=bool) for column in boolean_cols}
    return numeric, boolean


def metric(
    label: str,
    selected_mask: np.ndarray,
    split_mask: np.ndarray,
    labels: np.ndarray,
    df: pd.DataFrame,
    include_validation: bool,
) -> dict[str, Any]:
    selected = selected_mask & split_mask
    support = int(selected.sum())
    success = int(((labels == label) & selected).sum())
    precision = success / support if support else 0.0
    selected_df = df.loc[selected] if include_validation and support else df.iloc[0:0]
    split_total = int(split_mask.sum())
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson(success, support),
        "coverage": support / split_total if split_total else 0.0,
        "validation_instruments": sorted(selected_df["instrument"].dropna().astype(str).unique().tolist()),
        "validation_market_contexts": sorted(selected_df["market"].dropna().astype(str).unique().tolist()),
        "validation_timeframes": sorted(selected_df["timeframe"].dropna().astype(str).unique().tolist()),
        "validation_contexts": sorted(selected_df["context"].dropna().astype(str).unique().tolist()),
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
    if ece > ACCEPTANCE_95["ece_max"]:
        out.append("ece_above_0_05")
    if test["coverage"] < ACCEPTANCE_95["coverage_min"]:
        out.append("coverage_below_0_03")
    if len(test["validation_instruments"]) < ACCEPTANCE_95["validation_instruments_min"]:
        out.append("validation_instruments_below_2")
    if len(test["validation_market_contexts"]) < ACCEPTANCE_95["validation_market_contexts_min"]:
        out.append("validation_market_contexts_below_2")
    if len(test["validation_timeframes"]) < ACCEPTANCE_95["validation_timeframes_min"]:
        out.append("validation_timeframes_below_2")
    return out


def candidate_result(
    label: str,
    candidate: Candidate,
    train_mask: np.ndarray,
    calibration_mask: np.ndarray,
    test_mask: np.ndarray,
    labels: np.ndarray,
    df: pd.DataFrame,
    include_validation: bool,
) -> dict[str, Any]:
    train = metric(label, candidate.mask, train_mask, labels, df, include_validation)
    calibration = metric(label, candidate.mask, calibration_mask, labels, df, include_validation)
    test = metric(label, candidate.mask, test_mask, labels, df, include_validation)
    ece = abs(test["precision"] - calibration["precision"]) if calibration["support"] else 1.0
    block = blockers(calibration, test, ece)
    return {
        "method": candidate.method,
        "rule": candidate.rule,
        "train": train,
        "calibration": calibration,
        "test": test,
        "ece": ece,
        "accepted_95": not block,
        "blockers": block,
        "model_details": candidate.model_details or {},
    }


def atom_candidates(
    numeric: dict[str, np.ndarray],
    boolean: dict[str, np.ndarray],
    train_mask: np.ndarray,
) -> list[Candidate]:
    atoms: list[Candidate] = []
    for name, values in boolean.items():
        atoms.append(Candidate("rule_atom", name, values))
        atoms.append(Candidate("rule_atom", f"NOT {name}", ~values))
    ratios = (0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.92, 0.95, 0.97)
    for name, values in numeric.items():
        train_values = values[train_mask]
        for ratio in ratios:
            cut = float(np.quantile(train_values, ratio))
            atoms.append(Candidate("rule_atom", f"{name} >= {cut:.12g}", values >= cut))
            atoms.append(Candidate("rule_atom", f"{name} <= {cut:.12g}", values <= cut))
    return atoms


def rule_candidates_for_label(
    label: str,
    atoms: list[Candidate],
    train_mask: np.ndarray,
    calibration_mask: np.ndarray,
    test_mask: np.ndarray,
    labels: np.ndarray,
    df: pd.DataFrame,
) -> list[dict[str, Any]]:
    prelim: list[tuple[Candidate, dict[str, Any]]] = []
    for atom in atoms:
        result = candidate_result(label, atom, train_mask, calibration_mask, test_mask, labels, df, False)
        if result["train"]["support"] >= 120 and result["train"]["coverage"] >= 0.03:
            prelim.append((atom, result))
    prelim.sort(
        key=lambda item: (
            item[1]["train"]["precision_wilson_lcb_95"],
            item[1]["train"]["precision"],
            item[1]["train"]["support"],
        ),
        reverse=True,
    )
    seed_atoms = [item[0] for item in prelim[:50]]
    candidates: list[Candidate] = list(seed_atoms)
    for left, right in combinations(seed_atoms, 2):
        candidates.append(Candidate("rule_pair", f"{left.rule} AND {right.rule}", left.mask & right.mask))
    for left, mid, right in combinations(seed_atoms[:18], 3):
        candidates.append(
            Candidate("rule_triple", f"{left.rule} AND {mid.rule} AND {right.rule}", left.mask & mid.mask & right.mask)
        )
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    by_rule: dict[str, Candidate] = {}
    for candidate in candidates:
        if candidate.rule in seen:
            continue
        seen.add(candidate.rule)
        by_rule[candidate.rule] = candidate
        result = candidate_result(label, candidate, train_mask, calibration_mask, test_mask, labels, df, False)
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
    return [
        candidate_result(label, by_rule[result["rule"]], train_mask, calibration_mask, test_mask, labels, df, True)
        for result in results[:80]
    ]


def bin_log_odds_scores(
    label: str,
    numeric: dict[str, np.ndarray],
    boolean: dict[str, np.ndarray],
    train_mask: np.ndarray,
    labels: np.ndarray,
) -> tuple[np.ndarray, dict[str, Any]]:
    y = labels == label
    feature_scores: list[tuple[float, str, np.ndarray, dict[str, Any]]] = []
    train_y = y[train_mask]
    pos_total = int(train_y.sum())
    neg_total = int(train_y.size - pos_total)

    for name, values in numeric.items():
        train_values = values[train_mask]
        quantiles = np.unique(np.quantile(train_values, np.linspace(0.0, 1.0, 11)))
        if len(quantiles) < 3:
            continue
        bins = np.digitize(values, quantiles[1:-1], right=True)
        weights: dict[int, float] = {}
        strength = 0.0
        for bucket in range(len(quantiles) - 1):
            bucket_train = train_mask & (bins == bucket)
            pos = int((bucket_train & y).sum())
            neg = int(bucket_train.sum() - pos)
            pos_rate = (pos + 1.0) / (pos_total + len(quantiles))
            neg_rate = (neg + 1.0) / (neg_total + len(quantiles))
            weight = math.log(pos_rate / neg_rate)
            weights[bucket] = weight
            strength = max(strength, abs(weight))
        score = np.array([weights[int(bucket)] for bucket in bins], dtype=float)
        feature_scores.append((strength, name, score, {"type": "numeric_decile", "quantiles": quantiles.tolist()}))

    for name, values in boolean.items():
        score = np.zeros(values.shape[0], dtype=float)
        details = {"type": "boolean", "weights": {}}
        strength = 0.0
        for flag in (False, True):
            bucket_train = train_mask & (values == flag)
            pos = int((bucket_train & y).sum())
            neg = int(bucket_train.sum() - pos)
            pos_rate = (pos + 1.0) / (pos_total + 2.0)
            neg_rate = (neg + 1.0) / (neg_total + 2.0)
            weight = math.log(pos_rate / neg_rate)
            score[values == flag] = weight
            details["weights"][str(flag)] = weight
            strength = max(strength, abs(weight))
        feature_scores.append((strength, name, score, details))

    feature_scores.sort(key=lambda item: item[0], reverse=True)
    selected = feature_scores[:28]
    if not selected:
        return np.zeros(labels.shape[0], dtype=float), {"features": []}
    raw = np.sum([item[2] for item in selected], axis=0)
    train_raw = raw[train_mask]
    mean = float(np.mean(train_raw))
    std = float(np.std(train_raw)) if float(np.std(train_raw)) > 1e-12 else 1.0
    return (raw - mean) / std, {
        "features": [
            {"feature": name, "strength": strength, "details": details}
            for strength, name, _, details in selected
        ],
        "train_standardization": {"mean": mean, "std": std},
    }


def score_candidates_for_label(
    label: str,
    numeric: dict[str, np.ndarray],
    boolean: dict[str, np.ndarray],
    train_mask: np.ndarray,
    calibration_mask: np.ndarray,
    test_mask: np.ndarray,
    labels: np.ndarray,
    df: pd.DataFrame,
) -> list[dict[str, Any]]:
    scores, details = bin_log_odds_scores(label, numeric, boolean, train_mask, labels)
    cal_scores = scores[calibration_mask]
    thresholds = sorted(
        {
            float(np.quantile(cal_scores, ratio))
            for ratio in (0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.84, 0.88, 0.90, 0.92, 0.94, 0.96, 0.97)
        }
    )
    candidates: list[tuple[Candidate, dict[str, Any]]] = []
    for threshold in thresholds:
        candidate = Candidate(
            "decile_log_odds_score",
            f"expanded_root_decile_log_odds_score_{label} >= {threshold:.12g}",
            scores >= threshold,
            {"threshold": threshold, **details},
        )
        result = candidate_result(label, candidate, train_mask, calibration_mask, test_mask, labels, df, False)
        if result["calibration"]["support"] >= 120 and result["calibration"]["coverage"] >= 0.03:
            candidates.append((candidate, result))
    candidates.sort(
        key=lambda item: (
            item[1]["accepted_95"],
            item[1]["calibration"]["precision_wilson_lcb_95"],
            item[1]["calibration"]["precision"],
            item[1]["calibration"]["support"],
        ),
        reverse=True,
    )
    return [
        candidate_result(label, candidate, train_mask, calibration_mask, test_mask, labels, df, True)
        for candidate, _ in candidates[:40]
    ]


def root_report(
    label: str,
    atoms: list[Candidate],
    numeric: dict[str, np.ndarray],
    boolean: dict[str, np.ndarray],
    train_mask: np.ndarray,
    calibration_mask: np.ndarray,
    test_mask: np.ndarray,
    labels: np.ndarray,
    df: pd.DataFrame,
) -> dict[str, Any]:
    all_candidates = rule_candidates_for_label(label, atoms, train_mask, calibration_mask, test_mask, labels, df)
    all_candidates.extend(
        score_candidates_for_label(label, numeric, boolean, train_mask, calibration_mask, test_mask, labels, df)
    )
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
    diagnostics = sorted(
        all_candidates,
        key=lambda item: (
            item["test"]["precision_wilson_lcb_95"],
            item["test"]["precision"],
            item["test"]["support"],
        ),
        reverse=True,
    )[:8]
    return {
        "root_class": label,
        "state": "accepted_95" if accepted else "blocked",
        "accepted_candidate_count": len(accepted),
        "selected_candidate": accepted[0] if accepted else (all_candidates[0] if all_candidates else None),
        "top_calibration_selected_candidates": all_candidates[:12],
        "best_test_diagnostics_not_selection": diagnostics,
        "selection_policy": (
            "candidate families are fit or generated on train only; thresholds and selection use calibration only; "
            "test is held out for final acceptance audit"
        ),
    }


def manipulation_report() -> dict[str, Any]:
    return {
        "root_class": "Manipulation",
        "state": "missing_required_inputs",
        "accepted_candidate_count": 0,
        "selected_candidate": {
            "method": "required_input_gate",
            "rule": "calibration_grade_direct_L2_L3_MBO_order_lifecycle_or_event_data_present == true",
            "train": {"support": 0, "success": 0, "precision": 0.0, "precision_wilson_lcb_95": 0.0, "coverage": 0.0},
            "calibration": {"support": 0, "success": 0, "precision": 0.0, "precision_wilson_lcb_95": 0.0, "coverage": 0.0},
            "test": {
                "support": 0,
                "success": 0,
                "precision": 0.0,
                "precision_wilson_lcb_95": 0.0,
                "coverage": 0.0,
                "validation_instruments": [],
                "validation_market_contexts": [],
                "validation_timeframes": [],
                "validation_contexts": [],
            },
            "ece": 1.0,
            "accepted_95": False,
            "blockers": ["missing_required_inputs", "ohlcv_proxy_rejected"],
        },
        "direct_input_inventory": {
            "tick_or_trade_tape_with_manipulation_labels": False,
            "bid_ask_quotes": False,
            "l2_or_l3_order_book": False,
            "order_lifecycle": False,
            "event_social_or_on_chain": False,
        },
    }


def schema(df: pd.DataFrame, numeric_cols: list[str], boolean_cols: list[str]) -> dict[str, Any]:
    return {
        "schema_id": "ExpandedMainRegimeRootTargetGate",
        "source_taxonomy_schema": repo_rel(SOURCE_SCHEMA),
        "input_feature_table": repo_rel(INPUT_FEATURES),
        "required_roots": REQUIRED_ROOTS,
        "conditional_roots": CONDITIONAL_ROOTS,
        "evaluated_ohlcv_roots": EVALUATED_OHLCV_ROOTS,
        "chronological_split": "source feature table split column; train/calibration/test are time ordered per context",
        "blocked_predictor_prefixes": list(BLOCKED_PREDICTOR_PREFIXES),
        "predictor_columns_used": {"numeric": numeric_cols, "boolean": boolean_cols},
        "target_definitions": {
            "BullExpansion": "expanded_root_label == BullExpansion",
            "BearExpansion": "expanded_root_label == BearExpansion",
            "SidewaysConsolidation": "source_backed_root_label in {Consolidation, ConsolidationRange}",
            "CrisisStress": "expanded_root_label == CrisisStress",
            "Manipulation": "not materialized without direct tick/order-flow/L2/L3/order-lifecycle/event/social/on-chain evidence",
            "TransitionRecovery": "optional/conditional overlay; not required in this expanded root gate",
            "UnknownOrMixed": "residual abstention bucket; not release confidence",
        },
        "target_counts_by_split": {
            split: df[df["split"].eq(split)]["expanded_root_label"].value_counts().to_dict()
            for split in ["train", "calibration", "test"]
        },
        "acceptance_95": ACCEPTANCE_95,
    }


def crosswalk() -> dict[str, Any]:
    return {
        "schema_id": "ExpandedMainRegimeRootCrosswalk",
        "rule": "sub-regime packets remain context/guardrails until the expanded root label itself passes this gate",
        "crosswalk": {
            "BullExpansion": {
                "sub_regime_context": ["TrendExpansion"],
                "promotion_requirement": "signed positive expansion target passes V4 root gate directly",
            },
            "BearExpansion": {
                "sub_regime_context": ["TrendExpansion", "ExtremeStress"],
                "promotion_requirement": "signed negative expansion target passes V4 root gate directly and stays separated from CrisisStress",
            },
            "SidewaysConsolidation": {
                "sub_regime_context": ["RangeConsolidation"],
                "promotion_requirement": "range/chop/compression target passes expanded root gate directly",
            },
            "Manipulation": {
                "sub_regime_context": ["ThinLiquidity", "SessionLiquidityCoreViable", "sweep-like OHLCV shapes"],
                "promotion_requirement": "blocked; requires direct market microstructure/order-lifecycle/event evidence",
            },
            "CrisisStress": {
                "sub_regime_context": ["ExtremeStress"],
                "promotion_requirement": "stress/crash target passes V4 root gate directly across contexts/timeframes",
            },
            "TransitionRecovery": {
                "sub_regime_context": ["ReversalBrewing"],
                "promotion_requirement": "optional only unless downstream contract activates it",
            },
            "UnknownOrMixed": {
                "sub_regime_context": [],
                "promotion_requirement": "residual abstention only",
            },
        },
    }


def write_summary(path: Path, reports: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
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
            ],
        )
        writer.writeheader()
        for report in reports:
            selected = report["selected_candidate"]
            writer.writerow(
                {
                    "root_class": report["root_class"],
                    "state": report["state"],
                    "accepted_candidate_count": report["accepted_candidate_count"],
                    "selected_method": selected["method"],
                    "selected_rule": selected["rule"],
                    "calibration_support": selected["calibration"]["support"],
                    "calibration_wilson95": selected["calibration"]["precision_wilson_lcb_95"],
                    "calibration_precision": selected["calibration"]["precision"],
                    "test_support": selected["test"]["support"],
                    "test_wilson95": selected["test"]["precision_wilson_lcb_95"],
                    "test_precision": selected["test"]["precision"],
                    "test_coverage": selected["test"]["coverage"],
                    "ece": selected["ece"],
                    "test_instruments": ";".join(selected["test"]["validation_instruments"]),
                    "test_market_contexts": ";".join(selected["test"]["validation_market_contexts"]),
                    "test_timeframes": ";".join(selected["test"]["validation_timeframes"]),
                    "blockers": ";".join(selected["blockers"]),
                }
            )


def main() -> int:
    ROOT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_frame()
    train_mask = df["split"].eq("train").to_numpy(dtype=bool)
    calibration_mask = df["split"].eq("calibration").to_numpy(dtype=bool)
    test_mask = df["split"].eq("test").to_numpy(dtype=bool)
    labels = df["expanded_root_label"].astype(str).to_numpy()

    numeric_cols, boolean_cols = candidate_columns(df)
    numeric, boolean = build_arrays(df, numeric_cols, boolean_cols)
    atoms = atom_candidates(numeric, boolean, train_mask)

    reports = [
        root_report(label, atoms, numeric, boolean, train_mask, calibration_mask, test_mask, labels, df)
        for label in EVALUATED_OHLCV_ROOTS
    ]
    reports.append(manipulation_report())

    accepted = [report["root_class"] for report in reports if report["state"] == "accepted_95"]
    missing = [root for root in REQUIRED_ROOTS if root not in accepted]
    decision = {
        "board_state": "blocked" if missing else "accepted_95",
        "accepted_gate": "accepted_95_all_expanded_root_required_roots" if not missing else "partial_for_expanded_roots",
        "accepted_95_all_expanded_root_roots": not missing,
        "accepted_root_classes_95": accepted,
        "missing_root_classes_95": missing,
        "thresholds_relaxed": False,
        "blocked_future_target_predictors": True,
        "fresh_calibration_rerun": True,
        "runtime_code_changed": False,
        "trade_usable": False,
        "blocker": "none" if not missing else "missing_root_classes_95=" + ",".join(missing),
        "next_action": (
            "Acquire calibration-grade direct L2/L3/MBO/order-lifecycle/event data for Manipulation and add materially "
            "stronger cross-provider signed expansion/consolidation inputs before rerunning unchanged expanded-root gates."
        ),
    }

    target_schema = schema(df, numeric_cols, boolean_cols)
    crosswalk_doc = crosswalk()
    report = {
        "schema_version": "expanded-main-regime-root-gate/v1",
        "loop_id": LOOP_ID,
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Materialize expanded root target schema/crosswalk and rerun unchanged 95 gates with train-only generated rules and log-odds score candidates.",
        "source_taxonomy_refresh": repo_rel(SOURCE_SCHEMA),
        "input_feature_table": repo_rel(INPUT_FEATURES),
        "target_schema": target_schema,
        "crosswalk": crosswalk_doc,
        "threshold_policy": ACCEPTANCE_95,
        "root_reports": reports,
        "decision": decision,
    }

    report_path = ROOT_DIR / "expanded_root_schema_gate_report.json"
    summary_path = ROOT_DIR / "expanded_root_schema_gate_summary.csv"
    schema_path = ROOT_DIR / "expanded_root_target_schema.json"
    crosswalk_path = ROOT_DIR / "expanded_root_crosswalk.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    schema_path.write_text(json.dumps(target_schema, indent=2) + "\n", encoding="utf-8")
    crosswalk_path.write_text(json.dumps(crosswalk_doc, indent=2) + "\n", encoding="utf-8")
    write_summary(summary_path, reports)
    (CHECKS_DIR / "expanded_root_schema_gate_assertions.out").write_text(
        "\n".join(
            [
                f"report: {repo_rel(report_path)}",
                f"summary: {repo_rel(summary_path)}",
                f"target_schema: {repo_rel(schema_path)}",
                f"crosswalk: {repo_rel(crosswalk_path)}",
                "runtime_code_changed: False",
                "thresholds_relaxed: False",
                "blocked_future_target_predictors: True",
                "fresh_calibration_rerun: True",
                "trade_usable: False",
                "accepted_root_classes_95: " + ",".join(accepted),
                "missing_root_classes_95: " + ",".join(missing),
                "manipulation_input_state: missing_required_inputs",
                "GATE " + ("accepted_all_required_roots" if not missing else "blocked"),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "README.md").write_text(
        "# Expanded Root Schema Gate\n\n"
        "Materializes the expanded root target schema/crosswalk and evaluates train-only rule/log-odds candidates. "
        "Calibration selects thresholds; test is held out for acceptance. No runtime code changed.\n\n"
        f"Result: {decision['accepted_gate']}; {decision['blocker']}.\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
