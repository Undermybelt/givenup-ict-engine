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
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search"
PREVIOUS_RUN = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T202359-hermes-cross-market-regime-validation"
FEATURE_TABLE = PREVIOUS_RUN / "cross-market/cross_market_regime_features_and_labels.csv"
OUT_DIR = RUN_ROOT / "calibration"

Z95 = 1.959963984540054
Z99 = 2.5758293035489004

REGIMES = {
    "TrendExpansion": {
        "condition": "condition_trend_expansion",
        "target": "target_trend_expansion",
        "allowed_action": "release_candidate_only_when_other_gates_pass",
    },
    "RangeConsolidation": {
        "condition": "condition_range_consolidation",
        "target": "target_range_consolidation",
        "allowed_action": "observe_or_mean_reversion_candidate_only_when_other_gates_pass",
    },
    "ExtremeStress": {
        "condition": "condition_extreme_stress",
        "target": "target_extreme_stress",
        "allowed_action": "guardrail_only_reduce_or_block_release",
    },
    "ReversalBrewing": {
        "condition": "condition_reversal_brewing",
        "target": "target_reversal_brewing",
        "allowed_action": "observe_or_reversal_candidate_only_when_other_gates_pass",
    },
    "ThinLiquidity": {
        "condition": "condition_thin_liquidity",
        "target": "target_thin_liquidity",
        "allowed_action": "guardrail_only_liquidity_context",
    },
}

FEATURES = [
    "ret_1",
    "ret_4",
    "stretch_32",
    "range_pct",
    "realized_vol_rank_252",
    "range_rank_252",
    "volume_rank_252",
    "stretch_abs_rank_252",
]

QUANTILES = [
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
]


@dataclass(frozen=True)
class Predicate:
    feature: str
    direction: str
    threshold: float
    mask: np.ndarray

    @property
    def rule(self) -> str:
        return f"{self.feature} {self.direction} {self.threshold:.10g}"


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lower(success: int, total: int, z: float = Z95) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    centre = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def metric(df: pd.DataFrame, idx: np.ndarray, mask: np.ndarray, target: str, calibrated_probability: float | None = None) -> dict[str, Any]:
    valid_idx = idx[df[target].to_numpy(dtype=float, copy=False)[idx] == df[target].to_numpy(dtype=float, copy=False)[idx]]
    if len(valid_idx) == 0:
        return {
            "support": 0,
            "success": 0,
            "precision": 0.0,
            "precision_wilson_lcb_95": 0.0,
            "precision_wilson_lcb_99": 0.0,
            "coverage": 0.0,
            "ece": None,
            "calibrated_probability": calibrated_probability,
        }
    selected_idx = valid_idx[mask[valid_idx]]
    support = int(len(selected_idx))
    success = int(df[target].to_numpy(dtype=float, copy=False)[selected_idx].sum()) if support else 0
    precision = float(success / support) if support else 0.0
    coverage = float(support / len(valid_idx)) if len(valid_idx) else 0.0
    if calibrated_probability is None:
        ece: float | None = 0.0
    else:
        ece = abs(float(calibrated_probability) - precision)
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lower(success, support, Z95),
        "precision_wilson_lcb_99": wilson_lower(success, support, Z99),
        "coverage": coverage,
        "ece": ece,
        "calibrated_probability": calibrated_probability,
    }


def pass_gate(cal: dict[str, Any], test: dict[str, Any], context_coverage: dict[str, Any], lane: str) -> bool:
    if lane == "95":
        return bool(
            cal["support"] >= 120
            and test["support"] >= 60
            and test["precision_wilson_lcb_95"] >= 0.95
            and test["ece"] is not None
            and test["ece"] <= 0.05
            and test["coverage"] >= 0.03
            and context_coverage["test_contexts_with_support"] >= 3
            and context_coverage["test_markets_with_support"] >= 3
            and context_coverage["test_timeframes_with_support"] >= 2
        )
    return bool(
        cal["support"] >= 300
        and test["support"] >= 120
        and test["precision_wilson_lcb_99"] >= 0.99
        and test["ece"] is not None
        and test["ece"] <= 0.02
        and test["coverage"] >= 0.02
        and context_coverage["test_contexts_with_support"] >= 3
        and context_coverage["test_markets_with_support"] >= 3
        and context_coverage["test_timeframes_with_support"] >= 2
    )


def split_by_context(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["split"] = ""
    context_cols = ["instrument", "market", "timeframe"]
    for _, group in out.groupby(context_cols, sort=False):
        order = group.sort_values("ts").index.to_numpy()
        n = len(order)
        train_end = n // 2
        cal_end = (n * 3) // 4
        out.loc[order[:train_end], "split"] = "train"
        out.loc[order[train_end:cal_end], "split"] = "calibration"
        out.loc[order[cal_end:], "split"] = "test"
    return out


def load_data() -> pd.DataFrame:
    df = pd.read_csv(FEATURE_TABLE)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df = df.sort_values(["instrument", "market", "timeframe", "ts"]).reset_index(drop=True)
    for feature in FEATURES:
        df[feature] = pd.to_numeric(df[feature], errors="coerce")
    for spec in REGIMES.values():
        df[spec["condition"]] = df[spec["condition"]].astype(bool)
        df[spec["target"]] = pd.to_numeric(df[spec["target"]], errors="coerce")
    return split_by_context(df)


def indices(df: pd.DataFrame) -> dict[str, np.ndarray]:
    return {
        "train": df.index[df["split"] == "train"].to_numpy(),
        "calibration": df.index[df["split"] == "calibration"].to_numpy(),
        "test": df.index[df["split"] == "test"].to_numpy(),
    }


def build_predicates(df: pd.DataFrame, train_idx: np.ndarray) -> list[Predicate]:
    predicates: list[Predicate] = []
    for feature in FEATURES:
        train_values = pd.to_numeric(df.loc[train_idx, feature], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if train_values.empty:
            continue
        thresholds = sorted({float(train_values.quantile(q)) for q in QUANTILES if math.isfinite(float(train_values.quantile(q)))})
        values = df[feature].to_numpy(dtype=float, copy=False)
        valid = np.isfinite(values)
        for threshold in thresholds:
            predicates.append(Predicate(feature, ">=", threshold, valid & (values >= threshold)))
            predicates.append(Predicate(feature, "<=", threshold, valid & (values <= threshold)))
    return predicates


def candidate_score(train: dict[str, Any]) -> float:
    if train["support"] <= 0:
        return -1.0
    support_factor = min(1.0, train["support"] / 240.0)
    coverage_factor = min(1.0, train["coverage"] / 0.08)
    return float(train["precision_wilson_lcb_95"] * 0.65 + train["precision"] * 0.20 + support_factor * 0.10 + coverage_factor * 0.05)


def context_metrics(df: pd.DataFrame, mask: np.ndarray, target: str, calibrated_probability: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    context_cols = ["instrument", "market", "timeframe"]
    for keys, group in df.groupby(context_cols, sort=False):
        instrument, market, timeframe = keys
        entry: dict[str, Any] = {"instrument": instrument, "market": market, "timeframe": timeframe}
        for split in ["calibration", "test"]:
            idx = group.index[group["split"] == split].to_numpy()
            entry[split] = metric(df, idx, mask, target, calibrated_probability)
        rows.append(entry)
    return rows


def context_coverage(per_context: list[dict[str, Any]]) -> dict[str, Any]:
    test_supported = [r for r in per_context if r["test"]["support"] > 0]
    cal_supported = [r for r in per_context if r["calibration"]["support"] > 0]
    return {
        "calibration_contexts_with_support": len(cal_supported),
        "test_contexts_with_support": len(test_supported),
        "test_markets_with_support": len({r["market"] for r in test_supported}),
        "test_instruments_with_support": len({r["instrument"] for r in test_supported}),
        "test_timeframes_with_support": len({r["timeframe"] for r in test_supported}),
    }


def blocker(cal: dict[str, Any], test: dict[str, Any], coverage: dict[str, Any]) -> str:
    blockers: list[str] = []
    if cal["support"] < 120:
        blockers.append("calibration_support_below_120")
    if test["support"] < 60:
        blockers.append("test_support_below_60")
    if test["precision_wilson_lcb_95"] < 0.95:
        blockers.append("wilson95_below_0_95")
    if test["ece"] is None or test["ece"] > 0.05:
        blockers.append("ece_above_0_05")
    if test["coverage"] < 0.03:
        blockers.append("coverage_below_0_03")
    if coverage["test_contexts_with_support"] < 3:
        blockers.append("cross_market_context_support_below_3")
    if coverage["test_markets_with_support"] < 3:
        blockers.append("cross_market_market_support_below_3")
    if coverage["test_timeframes_with_support"] < 2:
        blockers.append("cross_market_timeframe_support_below_2")
    return ";".join(blockers) if blockers else "none"


def row_for_candidate(
    df: pd.DataFrame,
    split_idx: dict[str, np.ndarray],
    regime_id: str,
    rule_name: str,
    mask: np.ndarray,
    target: str,
    selected_by: str,
    train_selection_score: float,
    train_selection_rank: int,
) -> dict[str, Any]:
    train = metric(df, split_idx["train"], mask, target)
    cal = metric(df, split_idx["calibration"], mask, target)
    calibrated_probability = cal["precision"]
    test = metric(df, split_idx["test"], mask, target, calibrated_probability)
    per_context = context_metrics(df, mask, target, calibrated_probability)
    coverage = context_coverage(per_context)
    passes_95 = pass_gate(cal, test, coverage, "95")
    passes_99 = pass_gate(cal, test, coverage, "99")
    return {
        "regime_id": regime_id,
        "rule": rule_name,
        "selected_by": selected_by,
        "train_selection_score": train_selection_score,
        "train_selection_rank": train_selection_rank,
        "train": train,
        "calibration": cal,
        "test": test,
        "context_coverage": coverage,
        "per_context": per_context,
        "passes_95": passes_95,
        "passes_99": passes_99,
        "blocker": blocker(cal, test, coverage),
    }


def search_regime(df: pd.DataFrame, split_idx: dict[str, np.ndarray], predicates: list[Predicate], regime_id: str) -> dict[str, Any]:
    spec = REGIMES[regime_id]
    target = spec["target"]
    base_mask = df[spec["condition"]].to_numpy(dtype=bool, copy=False)

    initial: list[tuple[float, str, np.ndarray, dict[str, Any]]] = []
    initial.append((0.0, f"{spec['condition']} == true", base_mask, metric(df, split_idx["train"], base_mask, target)))
    for pred in predicates:
        for name, mask in [
            (pred.rule, pred.mask),
            (f"{spec['condition']} == true AND {pred.rule}", base_mask & pred.mask),
        ]:
            train = metric(df, split_idx["train"], mask, target)
            if train["support"] >= 120 and train["coverage"] >= 0.03:
                initial.append((candidate_score(train), name, mask, train))

    pruned = sorted(initial, key=lambda item: (item[0], item[3]["precision_wilson_lcb_95"], item[3]["support"]), reverse=True)[:120]

    pair_candidates: list[tuple[float, str, np.ndarray, dict[str, Any]]] = []
    # Use only simple predicates for pairs; base variants are added after pair construction.
    simple_preds = [p for p in predicates if metric(df, split_idx["train"], p.mask, target)["support"] >= 80]
    ranked_simple = sorted(
        simple_preds,
        key=lambda p: candidate_score(metric(df, split_idx["train"], p.mask, target)),
        reverse=True,
    )[:70]
    for i, left in enumerate(ranked_simple):
        for right in ranked_simple[i + 1 :]:
            if left.feature == right.feature and left.direction != right.direction:
                continue
            pair_mask = left.mask & right.mask
            for name, mask in [
                (f"{left.rule} AND {right.rule}", pair_mask),
                (f"{spec['condition']} == true AND {left.rule} AND {right.rule}", base_mask & pair_mask),
            ]:
                train = metric(df, split_idx["train"], mask, target)
                if train["support"] >= 120 and train["coverage"] >= 0.03:
                    pair_candidates.append((candidate_score(train), name, mask, train))

    candidate_pool = pruned + sorted(
        pair_candidates,
        key=lambda item: (item[0], item[3]["precision_wilson_lcb_95"], item[3]["support"]),
        reverse=True,
    )[:180]

    seen: set[str] = set()
    evaluated: list[dict[str, Any]] = []
    sorted_pool = sorted(
        candidate_pool,
        key=lambda item: (item[0], item[3]["precision_wilson_lcb_95"], item[3]["support"]),
        reverse=True,
    )
    rank = 0
    for score, name, mask, _ in sorted_pool:
        if name in seen:
            continue
        seen.add(name)
        rank += 1
        evaluated.append(
            row_for_candidate(
                df,
                split_idx,
                regime_id,
                name,
                mask,
                target,
                "train_threshold_search",
                score,
                rank,
            )
        )

    train_selected = evaluated[:10]
    accepted = [row for row in train_selected if row["passes_95"] or row["passes_99"]]
    accepted = sorted(
        accepted,
        key=lambda row: (
            row["passes_99"],
            row["passes_95"],
            row["test"]["precision_wilson_lcb_95"],
            row["test"]["support"],
        ),
        reverse=True,
    )
    baseline = row_for_candidate(
        df,
        split_idx,
        regime_id,
        f"{spec['condition']} == true",
        base_mask,
        target,
        "baseline_condition_matrix_rule",
        0.0,
        0,
    )

    return {
        "regime_id": regime_id,
        "target": target,
        "base_condition": spec["condition"],
        "allowed_action": spec["allowed_action"],
        "baseline": baseline,
        "accepted_candidates": accepted,
        "top_train_selected_candidates": train_selected,
        "evaluated_candidate_count": len(evaluated),
    }


def flatten_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        candidates = result["accepted_candidates"] or result["top_train_selected_candidates"][:5]
        for candidate in candidates:
            rows.append(
                {
                    "regime_id": candidate["regime_id"],
                    "passes_95": candidate["passes_95"],
                    "passes_99": candidate["passes_99"],
                    "rule": candidate["rule"],
                    "cal_support": candidate["calibration"]["support"],
                    "cal_success": candidate["calibration"]["success"],
                    "cal_wilson95": candidate["calibration"]["precision_wilson_lcb_95"],
                    "test_support": candidate["test"]["support"],
                    "test_success": candidate["test"]["success"],
                    "test_wilson95": candidate["test"]["precision_wilson_lcb_95"],
                    "test_ece": candidate["test"]["ece"],
                    "test_coverage": candidate["test"]["coverage"],
                    "test_contexts": candidate["context_coverage"]["test_contexts_with_support"],
                    "test_markets": candidate["context_coverage"]["test_markets_with_support"],
                    "test_timeframes": candidate["context_coverage"]["test_timeframes_with_support"],
                    "blocker": candidate["blocker"],
                }
            )
    return rows


def assertion_lines(report: dict[str, Any]) -> list[str]:
    covered_regimes = sorted(report["results_by_regime"])
    accepted_by_regime = {
        regime: len(result["accepted_candidates"])
        for regime, result in report["results_by_regime"].items()
    }
    searched_features = report["search_policy"]["searched_features"]
    blocked_ok = not any(f.startswith("future_") or f.startswith("target_") for f in searched_features)
    every_regime_has_candidates = all(
        report["results_by_regime"][regime]["evaluated_candidate_count"] > 0
        for regime in REGIMES
    )
    every_regime_has_context_validation = all(
        len(report["results_by_regime"][regime]["top_train_selected_candidates"][0]["per_context"]) == 4
        for regime in REGIMES
    )
    return [
        f"covered_regimes: {covered_regimes}",
        f"accepted_by_regime: {accepted_by_regime}",
        f"blocked_future_target_predictors: {blocked_ok}",
        f"every_regime_has_candidates: {every_regime_has_candidates}",
        f"every_regime_has_context_validation: {every_regime_has_context_validation}",
        f"accepted_regime_count: {sum(1 for n in accepted_by_regime.values() if n > 0)}",
        f"per_regime_acceptance_complete: {all(n > 0 for n in accepted_by_regime.values())}",
    ]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()
    split_idx = indices(df)
    predicates = build_predicates(df, split_idx["train"])
    results_list = [search_regime(df, split_idx, predicates, regime) for regime in REGIMES]
    results = {result["regime_id"]: result for result in results_list}
    accepted_95 = [
        candidate
        for result in results_list
        for candidate in result["accepted_candidates"]
        if candidate["passes_95"]
    ]
    accepted_99 = [
        candidate
        for result in results_list
        for candidate in result["accepted_candidates"]
        if candidate["passes_99"]
    ]
    report = {
        "schema_version": "board-a-per-regime-candidate-search/v1",
        "loop_id": "20260510T203010+0800-hermes-per-regime-candidate-search",
        "run_root": repo_rel(RUN_ROOT),
        "source_features": repo_rel(FEATURE_TABLE),
        "search_policy": {
            "thresholds_relaxed": False,
            "threshold_source": "train split only",
            "candidate_selection_source": "train split only",
            "calibration_source": "chronological calibration split",
            "test_source": "chronological held-out test split",
            "blocked_feature_prefixes": ["future_", "target_"],
            "searched_features": FEATURES,
            "candidate_forms": [
                "base regime condition",
                "single non-leaky threshold predicate",
                "base regime condition AND single predicate",
                "two non-leaky threshold predicates",
                "base regime condition AND two predicates",
            ],
            "acceptance_95": {
                "precision_wilson_lcb_95": 0.95,
                "calibration_support": 120,
                "test_support": 60,
                "ece": 0.05,
                "coverage": 0.03,
                "cross_market_contexts": 3,
                "cross_market_markets": 3,
                "cross_market_timeframes": 2,
            },
            "acceptance_99": {
                "precision_wilson_lcb_99": 0.99,
                "calibration_support": 300,
                "test_support": 120,
                "ece": 0.02,
                "coverage": 0.02,
                "cross_market_contexts": 3,
                "cross_market_markets": 3,
                "cross_market_timeframes": 2,
            },
        },
        "validation_universe": [
            {
                "instrument": instrument,
                "market": market,
                "timeframe": timeframe,
                "rows": int(len(group)),
                "time_range": {
                    "start": str(group["ts"].min()),
                    "end": str(group["ts"].max()),
                },
            }
            for (instrument, market, timeframe), group in df.groupby(["instrument", "market", "timeframe"], sort=False)
        ],
        "accepted_95_candidates": accepted_95,
        "accepted_99_candidates": accepted_99,
        "results_by_regime": results,
        "summary": {
            "required_regimes": list(REGIMES),
            "accepted_95_count": len(accepted_95),
            "accepted_99_count": len(accepted_99),
            "per_regime_acceptance_complete": all(len(result["accepted_candidates"]) > 0 for result in results_list),
            "thresholds_relaxed": False,
        },
    }

    report_path = OUT_DIR / "per_regime_candidate_search_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    row_path = OUT_DIR / "per_regime_candidate_rules.csv"
    rows = flatten_rows(results_list)
    with row_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    assertions = assertion_lines(report)
    checks_dir = RUN_ROOT / "checks"
    checks_dir.mkdir(parents=True, exist_ok=True)
    (checks_dir / "per_regime_candidate_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")

    evidence_packet = {
        "schema_version": "board-a-per-regime-candidate-search-evidence/v1",
        "loop_id": report["loop_id"],
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Generate stronger per-regime candidates and rerun cross-market chronological calibration without relaxing thresholds.",
        "provider_status": repo_rel(RUN_ROOT / "provider/provider-status-agent.json"),
        "auto_quant_status": repo_rel(RUN_ROOT / "autoquant/auto-quant-status-agent.json"),
        "source_feature_table": repo_rel(FEATURE_TABLE),
        "candidate_search_report": repo_rel(report_path),
        "candidate_rule_table": repo_rel(row_path),
        "assertions": repo_rel(checks_dir / "per_regime_candidate_assertions.out"),
        "accepted_95_candidates": len(accepted_95),
        "accepted_99_candidates": len(accepted_99),
        "per_regime_acceptance_complete": report["summary"]["per_regime_acceptance_complete"],
        "thresholds_relaxed": False,
        "blocked_feature_prefixes": ["future_", "target_"],
        "best_candidate_by_regime": {
            regime: {
                "rule": result["top_train_selected_candidates"][0]["rule"],
                "calibration": result["top_train_selected_candidates"][0]["calibration"],
                "test": result["top_train_selected_candidates"][0]["test"],
                "context_coverage": result["top_train_selected_candidates"][0]["context_coverage"],
                "passes_95": result["top_train_selected_candidates"][0]["passes_95"],
                "passes_99": result["top_train_selected_candidates"][0]["passes_99"],
                "blocker": result["top_train_selected_candidates"][0]["blocker"],
            }
            for regime, result in results.items()
        },
    }
    (RUN_ROOT / "evidence_packet_per_regime_candidate_search.json").write_text(
        json.dumps(evidence_packet, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(json.dumps(evidence_packet, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
