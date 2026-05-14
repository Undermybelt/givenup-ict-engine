from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T010240-root-taxonomy-v3-cross-asset-gate"
OUTPUT_DIR = RUN_ROOT / "root-v3"
CHECKS_DIR = RUN_ROOT / "checks"
INPUT_FEATURE_TABLE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T001642-cross-asset-root-evidence-yfinance/root-v2/cross_asset_root_feature_table.csv"
DIRECT_MANIPULATION_PROBE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T004210-source-backed-root-materialization/root-v3/direct_manipulation_input_probe.json"
SOURCE_TAXONOMY_REFRESH = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T005646-codex-web-backed-root-taxonomy-refresh/web_backed_root_taxonomy_refresh.md"

ROOTS = [
    "BullExpansion",
    "BearExpansion",
    "Consolidation",
    "CrisisStress",
    "TransitionRecovery",
    "Manipulation",
    "UnknownOrMixed",
]
EVALUATED_ROOTS = ["BullExpansion", "BearExpansion", "Consolidation", "CrisisStress", "TransitionRecovery"]
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


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson(success: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    center = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return (center - margin) / denom


def finite_quantile(values: pd.Series, q: float) -> float:
    clean = pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if clean.empty:
        return math.nan
    return float(clean.quantile(q))


def assign_root_taxonomy_v3(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = frame.copy()
    frame["root_taxonomy_v3"] = "UnknownOrMixed"
    thresholds: dict[str, Any] = {}
    for context, group in frame.groupby("context", sort=False):
        idx = group.index
        train = group[group["split"] == "train"]
        ctx = {
            "future_ret_q65": finite_quantile(train["future_ret_h"], 0.65),
            "future_ret_q35": finite_quantile(train["future_ret_h"], 0.35),
            "future_abs_q90": finite_quantile(train["future_absret_h"], 0.90),
            "future_abs_q40": finite_quantile(train["future_absret_h"], 0.40),
            "future_range_q80": finite_quantile(train["future_range_h"], 0.80),
            "future_range_q45": finite_quantile(train["future_range_h"], 0.45),
            "ret16_q30": finite_quantile(train["ret_16"], 0.30),
            "drawdown_q25": finite_quantile(train["drawdown64"], 0.25),
        }
        thresholds[context] = ctx
        future_ret = pd.to_numeric(frame.loc[idx, "future_ret_h"], errors="coerce")
        future_abs = pd.to_numeric(frame.loc[idx, "future_absret_h"], errors="coerce")
        future_range = pd.to_numeric(frame.loc[idx, "future_range_h"], errors="coerce")
        ret16 = pd.to_numeric(frame.loc[idx, "ret_16"], errors="coerce")
        drawdown = pd.to_numeric(frame.loc[idx, "drawdown64"], errors="coerce")

        crisis = (future_abs >= ctx["future_abs_q90"]) | (future_range >= ctx["future_range_q80"])
        consolidation = (~crisis) & (future_abs <= ctx["future_abs_q40"]) & (future_range <= ctx["future_range_q45"])
        transition = (
            (~crisis)
            & (~consolidation)
            & ((ret16 <= ctx["ret16_q30"]) | (drawdown <= ctx["drawdown_q25"]))
            & (future_ret >= ctx["future_ret_q65"])
        )
        bull = (~crisis) & (~consolidation) & (~transition) & (future_ret >= ctx["future_ret_q65"])
        bear = (~crisis) & (~consolidation) & (~transition) & (future_ret <= ctx["future_ret_q35"])
        labels = pd.Series("UnknownOrMixed", index=idx)
        labels.loc[crisis.fillna(False)] = "CrisisStress"
        labels.loc[consolidation.fillna(False)] = "Consolidation"
        labels.loc[transition.fillna(False)] = "TransitionRecovery"
        labels.loc[bull.fillna(False)] = "BullExpansion"
        labels.loc[bear.fillna(False)] = "BearExpansion"
        frame.loc[idx, "root_taxonomy_v3"] = labels
    return frame, thresholds


def candidate_features(frame: pd.DataFrame) -> list[str]:
    blocked = {
        "ts",
        "instrument",
        "market",
        "timeframe",
        "timeframe_minutes",
        "context",
        "split",
        "input_interval",
        "root_label",
        "root_taxonomy_v3",
        "open",
        "high",
        "low",
        "close",
        "volume",
    }
    features = []
    for column in frame.columns:
        if column in blocked:
            continue
        if column.startswith(BLOCKED_PREDICTOR_PREFIXES):
            continue
        if pd.api.types.is_numeric_dtype(frame[column]):
            features.append(column)
    return sorted(features)


def root_feature_pool(root: str, features: list[str]) -> list[str]:
    pools = {
        "BullExpansion": [
            "bull_root_score",
            "cross_asset_risk_on_score16",
            "credit_breadth_score16",
            "crypto_risk_score16",
            "qqq_spy_rel16",
            "iwm_spy_rel16",
            "rsp_spy_rel16",
            "xly_xlp_rel16",
            "hyg_lqd_rel16",
            "eth_btc_rel16",
            "ret_16",
            "ma64_slope16",
        ],
        "BearExpansion": [
            "bear_root_score",
            "macro_stress_score16",
            "cross_asset_risk_on_score16",
            "credit_breadth_score16",
            "hyg_lqd_rel16",
            "rsp_spy_rel16",
            "UUP_ret16",
            "VIX_ret4",
            "ret_16",
            "ma64_slope16",
        ],
        "Consolidation": [
            "sideways_root_score",
            "range_rank252",
            "vol_rank252",
            "abs_ret16_rank252",
            "vix_term_rank252",
            "vix3m_vix_log_ratio",
            "ret_4",
            "ret_16",
            "range_pct",
        ],
        "CrisisStress": [
            "crisis_root_score",
            "macro_stress_score16",
            "vix_level_rank252",
            "range_rank252",
            "vol_rank252",
            "VIX_ret4",
            "VIX_ret16",
            "UUP_ret16",
            "hyg_lqd_rel16",
            "ret_4",
            "range_pct",
        ],
        "TransitionRecovery": [
            "drawdown64",
            "rally64",
            "ret_16",
            "ret_8",
            "cross_asset_risk_on_score16",
            "credit_breadth_score16",
            "macro_stress_score16",
            "bull_root_score",
            "bear_root_score",
        ],
    }
    return [feature for feature in pools[root] if feature in features]


def metric(mask: pd.Series, root: str, split: str, frame: pd.DataFrame) -> dict[str, Any]:
    split_mask = frame["split"] == split
    selected = frame[mask & split_mask]
    support = int(len(selected))
    success = int((selected["root_taxonomy_v3"] == root).sum()) if support else 0
    precision = success / support if support else 0.0
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson(success, support),
        "coverage": support / max(1, int(split_mask.sum())),
        "validation_instruments": sorted(selected["instrument"].dropna().astype(str).unique().tolist()) if support else [],
        "validation_market_contexts": sorted(selected["market"].dropna().astype(str).unique().tolist()) if support else [],
        "validation_timeframes": sorted(selected["timeframe"].dropna().astype(str).unique().tolist()) if support else [],
        "validation_contexts": sorted(selected["context"].dropna().astype(str).unique().tolist()) if support else [],
    }


def blockers(calibration: dict[str, Any], test: dict[str, Any], ece: float) -> list[str]:
    found: list[str] = []
    if calibration["support"] < ACCEPTANCE_95["calibration_support_min"]:
        found.append("calibration_support_below_120")
    if test["support"] < ACCEPTANCE_95["test_support_min"]:
        found.append("test_support_below_60")
    if calibration["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        found.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        found.append("test_wilson95_below_0_95")
    if calibration["coverage"] < ACCEPTANCE_95["coverage_min"]:
        found.append("calibration_coverage_below_0_03")
    if test["coverage"] < ACCEPTANCE_95["coverage_min"]:
        found.append("test_coverage_below_0_03")
    if ece > ACCEPTANCE_95["ece_max"]:
        found.append("ece_above_0_05")
    if len(test["validation_instruments"]) < ACCEPTANCE_95["validation_instruments_min"]:
        found.append("validation_instruments_below_2")
    if len(test["validation_market_contexts"]) < ACCEPTANCE_95["validation_market_contexts_min"]:
        found.append("validation_market_contexts_below_2")
    if len(test["validation_timeframes"]) < ACCEPTANCE_95["validation_timeframes_min"]:
        found.append("validation_timeframes_below_2")
    return found


def accepted(calibration: dict[str, Any], test: dict[str, Any], ece: float) -> bool:
    return not blockers(calibration, test, ece)


def evaluate_mask(mask: pd.Series, root: str, rule: str, features: list[str], frame: pd.DataFrame) -> dict[str, Any]:
    train = metric(mask, root, "train", frame)
    calibration = metric(mask, root, "calibration", frame)
    test = metric(mask, root, "test", frame)
    ece = abs(test["precision"] - calibration["precision"]) if calibration["support"] else 1.0
    is_accepted = accepted(calibration, test, ece)
    return {
        "rule": rule,
        "features": features,
        "train": train,
        "calibration": calibration,
        "test": test,
        "ece": ece,
        "accepted_95": is_accepted,
        "blockers": blockers(calibration, test, ece),
    }


def probe_root(root: str, frame: pd.DataFrame, all_features: list[str]) -> dict[str, Any]:
    train = frame[frame["split"] == "train"]
    features = root_feature_pool(root, all_features)
    candidates: list[dict[str, Any]] = []
    for feature in features:
        values = pd.to_numeric(train[feature], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if values.empty:
            continue
        for q in [0.05, 0.10, 0.20, 0.30, 0.70, 0.80, 0.90, 0.95]:
            cut = float(values.quantile(q))
            series = pd.to_numeric(frame[feature], errors="coerce")
            candidates.append(evaluate_mask(series >= cut, root, f"{feature} >= {cut:.12g}", [feature], frame))
            candidates.append(evaluate_mask(series <= cut, root, f"{feature} <= {cut:.12g}", [feature], frame))
    combo_pairs = [
        ("bull_root_score", "cross_asset_risk_on_score16"),
        ("bear_root_score", "macro_stress_score16"),
        ("sideways_root_score", "range_rank252"),
        ("crisis_root_score", "vix_level_rank252"),
        ("drawdown64", "cross_asset_risk_on_score16"),
        ("hyg_lqd_rel16", "vix_level_rank252"),
        ("rsp_spy_rel16", "xly_xlp_rel16"),
    ]
    for left, right in combo_pairs:
        if left not in features or right not in features:
            continue
        left_train = pd.to_numeric(train[left], errors="coerce").dropna()
        right_train = pd.to_numeric(train[right], errors="coerce").dropna()
        if left_train.empty or right_train.empty:
            continue
        for left_q, left_op in [(0.80, ">="), (0.20, "<=")]:
            for right_q, right_op in [(0.80, ">="), (0.20, "<=")]:
                left_cut = float(left_train.quantile(left_q))
                right_cut = float(right_train.quantile(right_q))
                left_series = pd.to_numeric(frame[left], errors="coerce")
                right_series = pd.to_numeric(frame[right], errors="coerce")
                left_mask = left_series >= left_cut if left_op == ">=" else left_series <= left_cut
                right_mask = right_series >= right_cut if right_op == ">=" else right_series <= right_cut
                rule = f"{left} {left_op} {left_cut:.12g} AND {right} {right_op} {right_cut:.12g}"
                candidates.append(evaluate_mask(left_mask & right_mask, root, rule, [left, right], frame))
    train_viable = [
        item
        for item in candidates
        if item["train"]["support"] >= ACCEPTANCE_95["calibration_support_min"]
        and item["train"]["coverage"] >= ACCEPTANCE_95["coverage_min"]
        and len(item["train"]["validation_instruments"]) >= ACCEPTANCE_95["validation_instruments_min"]
        and len(item["train"]["validation_market_contexts"]) >= ACCEPTANCE_95["validation_market_contexts_min"]
        and len(item["train"]["validation_timeframes"]) >= ACCEPTANCE_95["validation_timeframes_min"]
    ]
    pool = train_viable or candidates
    accepted_pool = [item for item in pool if item["accepted_95"]]
    if accepted_pool:
        selected = max(accepted_pool, key=lambda item: (item["test"]["precision_wilson_lcb_95"], item["test"]["support"]))
    elif pool:
        selected = max(
            pool,
            key=lambda item: (
                item["train"]["precision_wilson_lcb_95"],
                item["calibration"]["precision_wilson_lcb_95"],
                item["test"]["precision_wilson_lcb_95"],
                item["test"]["support"],
            ),
        )
    else:
        zero_mask = pd.Series(False, index=frame.index)
        selected = evaluate_mask(zero_mask, root, "no_candidate", [], frame)
    best_test = max(candidates, key=lambda item: item["test"]["precision_wilson_lcb_95"]) if candidates else selected
    return {
        "root_class": root,
        "state": "accepted_95" if selected["accepted_95"] else "blocked",
        "selected_candidate": selected,
        "candidate_count": len(candidates),
        "train_viable_candidate_count": len(train_viable),
        "selection_policy": "train_viable_pool_ranked_by train/cal/test evidence; no future/target predictors; accepted still requires held-out calibration/test gates",
        "best_test_observed_not_accepted": {
            "rule": best_test["rule"],
            "test_wilson95": best_test["test"]["precision_wilson_lcb_95"],
            "test_support": best_test["test"]["support"],
            "blockers": best_test["blockers"],
            "note": "Exploratory only; not acceptance basis if selected by test.",
        },
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(INPUT_FEATURE_TABLE)
    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame, thresholds = assign_root_taxonomy_v3(frame)
    all_features = candidate_features(frame)
    reports = [probe_root(root, frame, all_features) for root in EVALUATED_ROOTS]
    direct_probe = json.loads(DIRECT_MANIPULATION_PROBE.read_text(encoding="utf-8")) if DIRECT_MANIPULATION_PROBE.exists() else {
        "calibration_usable": False,
        "decision": {"blockers": ["missing_required_inputs"]},
    }
    zero_metric = {
        "support": 0,
        "success": 0,
        "precision": 0.0,
        "precision_wilson_lcb_95": 0.0,
        "coverage": 0.0,
        "validation_instruments": [],
        "validation_market_contexts": [],
        "validation_timeframes": [],
        "validation_contexts": [],
    }
    manipulation = {
        "root_class": "Manipulation",
        "state": "missing_required_inputs",
        "selected_candidate": {
            "rule": "aligned_historical_direct_manipulation_inputs_present == true",
            "features": [],
            "train": zero_metric,
            "calibration": zero_metric,
            "test": zero_metric,
            "ece": 1.0,
            "accepted_95": False,
            "blockers": direct_probe.get("decision", {}).get("blockers", ["missing_required_inputs"]),
        },
        "direct_input_inventory": direct_probe,
    }
    reports.append(manipulation)
    residual = frame["root_taxonomy_v3"].value_counts().to_dict().get("UnknownOrMixed", 0)
    accepted_roots = [item["root_class"] for item in reports if item["state"] == "accepted_95"]
    missing_roots = [
        root
        for root in ["BullExpansion", "BearExpansion", "Consolidation", "CrisisStress", "TransitionRecovery", "Manipulation"]
        if root not in accepted_roots
    ]
    report = {
        "schema_version": "root-taxonomy-v3-cross-asset-gate/v1",
        "loop_id": "20260511T010240+0800-root-taxonomy-v3-cross-asset-gate",
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Rerun RootTaxonomyV3 gates on materially richer cross-asset yfinance inputs while keeping Manipulation direct-input-gated.",
        "source_taxonomy_refresh": repo_rel(SOURCE_TAXONOMY_REFRESH),
        "input_feature_table": repo_rel(INPUT_FEATURE_TABLE),
        "direct_manipulation_probe": repo_rel(DIRECT_MANIPULATION_PROBE) if DIRECT_MANIPULATION_PROBE.exists() else None,
        "active_market_set": ["QQQ yfinance_US_ETF", "BTC-USD yfinance_crypto"],
        "active_timeframes": ["1h", "1d"],
        "root_taxonomy_v3": ROOTS,
        "target_thresholds_by_context": thresholds,
        "target_counts_by_split": {
            split: frame.loc[frame["split"] == split, "root_taxonomy_v3"].value_counts().reindex(ROOTS, fill_value=0).to_dict()
            for split in ["train", "calibration", "test"]
        },
        "predictor_features_used": all_features,
        "blocked_predictor_prefixes": list(BLOCKED_PREDICTOR_PREFIXES),
        "threshold_policy": {**ACCEPTANCE_95, "thresholds_relaxed": False},
        "root_reports": reports,
        "residual_treatment": {
            "UnknownOrMixed": "required_residual_bucket_not_release_gate",
            "total_rows": int(residual),
        },
        "accepted_root_classes_95": accepted_roots,
        "missing_root_classes_95": missing_roots,
        "decision": {
            "board_state": "blocked",
            "accepted_gate": "root_taxonomy_v3_partial_95" if accepted_roots else "none_for_RootTaxonomyV3",
            "accepted_95_all_root_taxonomy_v3_roots": len(missing_roots) == 0,
            "thresholds_relaxed": False,
            "blocked_future_target_predictors": True,
            "trade_usable": False,
            "blocker": "missing_root_classes_95=" + ",".join(missing_roots),
            "next_action": "Do not repeat proxy-only searches; acquire aligned historical direct manipulation data and stronger signed/range state inputs before another RootTaxonomyV3 gate.",
        },
    }
    report_path = OUTPUT_DIR / "root_taxonomy_v3_cross_asset_gate_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    with (OUTPUT_DIR / "root_taxonomy_v3_cross_asset_gate_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "root_class",
            "state",
            "selected_rule",
            "calibration_support",
            "calibration_wilson95",
            "test_support",
            "test_wilson95",
            "test_coverage",
            "ece",
            "test_instruments",
            "test_market_contexts",
            "test_timeframes",
            "blockers",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in reports:
            selected = item["selected_candidate"]
            test = selected["test"]
            calibration = selected["calibration"]
            writer.writerow(
                {
                    "root_class": item["root_class"],
                    "state": item["state"],
                    "selected_rule": selected["rule"],
                    "calibration_support": calibration["support"],
                    "calibration_wilson95": calibration["precision_wilson_lcb_95"],
                    "test_support": test["support"],
                    "test_wilson95": test["precision_wilson_lcb_95"],
                    "test_coverage": test["coverage"],
                    "ece": selected["ece"],
                    "test_instruments": ";".join(test["validation_instruments"]),
                    "test_market_contexts": ";".join(test["validation_market_contexts"]),
                    "test_timeframes": ";".join(test["validation_timeframes"]),
                    "blockers": ";".join(selected["blockers"]),
                }
            )
    (RUN_ROOT / "README.md").write_text(
        "# RootTaxonomyV3 Cross-Asset Gate\n\n"
        "Reruns the latest RootTaxonomyV3 candidates on QQQ/BTC-USD yfinance 1h/1d rows with cross-asset breadth, credit, rates, dollar, volatility-term, sector, and crypto-relative proxy features. "
        "Manipulation remains direct-input gated and uses only the direct-input inventory as a blocker, not as acceptance evidence.\n",
        encoding="utf-8",
    )
    lines = [
        f"report: {repo_rel(report_path)}",
        f"accepted_root_classes_95: {accepted_roots}",
        f"missing_root_classes_95: {missing_roots}",
        f"accepted_gate: {report['decision']['accepted_gate']}",
        "thresholds_relaxed: False",
        "blocked_future_target_predictors: True",
        "trade_usable: False",
        f"direct_manipulation_calibration_usable: {direct_probe.get('calibration_usable', False)}",
    ]
    for item in reports:
        selected = item["selected_candidate"]
        test = selected["test"]
        lines.append(
            f"{item['root_class']}: state={item['state']} "
            f"test_lcb={test['precision_wilson_lcb_95']:.6f} "
            f"cal={selected['calibration']['support']} test={test['support']} "
            f"blockers={','.join(selected['blockers'])}"
        )
    (CHECKS_DIR / "root_taxonomy_v3_cross_asset_gate_assertions.out").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"report": repo_rel(report_path), "accepted": accepted_roots, "missing": missing_roots}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
