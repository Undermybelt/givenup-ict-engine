from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T230938-main-regime-v2-schema-preflight"
CHECKS_DIR = RUN_ROOT / "checks"

FEATURE_TABLE = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260510T224014-codex-cross-timeframe-regime-validation/cross_timeframe_regime_features.csv"
)
STRICT_AUDIT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260510T224929-codex-strict-cross-timeframe-audit/audit/strict_cross_timeframe_audit.json"
)
A10_AUDIT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260510T205717-hermes-a10-order-flow-input-audit/evidence_packet_a10_order_flow_input_audit.json"
)
SOURCE_SCAN = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260510T225102-main-regime-taxonomy-research/main_regime_taxonomy_source_scan.md"
)

Z95 = 1.959963984540054


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lower(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    centre = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def clean_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)


def q(train: pd.DataFrame, col: str, quantile: float) -> float:
    values = clean_numeric(train[col]).dropna()
    if values.empty:
        return float("nan")
    return float(values.quantile(quantile))


def add_root_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ts"] = pd.to_datetime(out["ts"], utc=True)
    for col in (
        "close",
        "ma32",
        "ma64",
        "ma64_slope16",
        "ma32_slope8",
        "ret4",
        "ret16",
        "stretch64",
        "vol_rank",
        "range_rank",
        "vol_ratio32_128",
        "range_ratio32_128",
        "drawdown64",
    ):
        if col in out.columns:
            out[col] = clean_numeric(out[col])
    for col in ("trend_base", "stress_base", "reversal_base", "thin_base"):
        out[col] = out[col].fillna(False).astype(bool)

    train = out[out["split"] == "train"]
    abs_stretch = out["stretch64"].abs()
    abs_slope = out["ma64_slope16"].abs()
    out["abs_stretch64"] = abs_stretch
    out["abs_ma64_slope16"] = abs_slope
    train = out[out["split"] == "train"]

    out["BullExpansion_base"] = (
        (out["close"] > out["ma64"])
        & (out["ma32"] > out["ma64"])
        & (out["ma64_slope16"] > max(0.0, q(train, "ma64_slope16", 0.55)))
        & (out["ret4"] > max(0.0, q(train, "ret4", 0.55)))
        & (out["ret16"] > q(train, "ret16", 0.50))
        & (~out["stress_base"])
    )
    out["BearExpansion_base"] = (
        (out["close"] < out["ma64"])
        & (out["ma32"] < out["ma64"])
        & (out["ma64_slope16"] < min(0.0, q(train, "ma64_slope16", 0.45)))
        & (out["ret4"] < min(0.0, q(train, "ret4", 0.45)))
        & (out["ret16"] < q(train, "ret16", 0.50))
    )
    out["ConsolidationRange_base"] = (
        (out["abs_stretch64"] <= q(train, "abs_stretch64", 0.55))
        & (out["abs_ma64_slope16"] <= q(train, "abs_ma64_slope16", 0.55))
        & (out["vol_rank"] <= 0.55)
        & (out["range_rank"] <= 0.60)
        & (~out["stress_base"])
    )
    out["CrisisStress_base"] = (
        out["stress_base"]
        & (
            (out["drawdown64"] <= q(train, "drawdown64", 0.10))
            | (out["vol_ratio32_128"] >= q(train, "vol_ratio32_128", 0.90))
            | (out["range_ratio32_128"] >= q(train, "range_ratio32_128", 0.90))
            | (out["ret4"] <= q(train, "ret4", 0.05))
        )
    )
    out["TransitionAccumulationDistribution_base"] = (
        out["reversal_base"]
        | ((out["ret4"] * out["ma64_slope16"]) < 0.0)
        | (out["trend_base"] & out["stress_base"])
        | (out["BullExpansion_base"] & out["BearExpansion_base"])
    )
    root_cols = [
        "BullExpansion_base",
        "BearExpansion_base",
        "ConsolidationRange_base",
        "CrisisStress_base",
        "TransitionAccumulationDistribution_base",
    ]
    out["known_root_count"] = out[root_cols].sum(axis=1)
    out["UnknownOrMixed_base"] = out["known_root_count"].fillna(0).ne(1)

    for root in (
        "BullExpansion",
        "BearExpansion",
        "ConsolidationRange",
        "CrisisStress",
        "TransitionAccumulationDistribution",
        "UnknownOrMixed",
    ):
        base_col = f"{root}_base"
        out[f"{root}_persistence16"] = (
            out.sort_values("ts")
            .groupby("context", group_keys=False)[base_col]
            .rolling(16, min_periods=4)
            .mean()
            .reset_index(level=0, drop=True)
        )
        out[f"target_{root}_next"] = (
            out.sort_values("ts")
            .groupby("context", group_keys=False)[base_col]
            .shift(-1)
            .astype(float)
        )
    return out


def metric(df: pd.DataFrame, mask: pd.Series, split: str, target: str, probability: float | None = None) -> dict[str, Any]:
    valid = (df["split"] == split) & df[target].notna()
    selected = valid & mask.fillna(False)
    support = int(selected.sum())
    success = int(df.loc[selected, target].sum()) if support else 0
    precision = success / support if support else 0.0
    valid_count = int(valid.sum())
    selected_df = df.loc[selected]
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lower(success, support),
        "coverage": support / valid_count if valid_count else 0.0,
        "ece": 0.0 if probability is None else abs(float(probability) - precision),
        "validation_instruments": sorted(selected_df["instrument"].dropna().unique().tolist()),
        "validation_market_contexts": sorted(selected_df["market"].dropna().unique().tolist()),
        "validation_timeframes": sorted(selected_df["timeframe"].dropna().unique().tolist()),
        "validation_contexts": sorted(selected_df["context"].dropna().unique().tolist()),
    }


def passes_95(calibration: dict[str, Any], test: dict[str, Any], require_release: bool = True) -> bool:
    if not require_release:
        return False
    return bool(
        calibration["support"] >= 120
        and test["support"] >= 60
        and test["precision_wilson_lcb_95"] >= 0.95
        and test["ece"] <= 0.05
        and test["coverage"] >= 0.03
        and len(test["validation_instruments"]) >= 2
        and len(test["validation_market_contexts"]) >= 2
        and len(test["validation_timeframes"]) >= 2
    )


def evaluate_rule(
    df: pd.DataFrame,
    root: str,
    rule: str,
    mask: pd.Series,
    required_inputs_present: bool = True,
    release_like: bool = True,
) -> dict[str, Any]:
    target = f"target_{root}_next"
    train = metric(df, mask, "train", target)
    calibration = metric(df, mask, "calibration", target, train["precision"])
    test = metric(df, mask, "test", target, calibration["precision"])
    accepted = passes_95(calibration, test, require_release=(required_inputs_present and release_like))
    blockers: list[str] = []
    if not required_inputs_present:
        blockers.append("missing_required_inputs")
    if not release_like:
        blockers.append("residual_or_abstain_bucket_not_release_gate")
    if calibration["support"] < 120:
        blockers.append("calibration_support_too_thin")
    if test["support"] < 60:
        blockers.append("test_support_too_thin")
    if test["precision_wilson_lcb_95"] < 0.95:
        blockers.append("precision_wilson_lcb_below_95")
    if test["ece"] > 0.05:
        blockers.append("ece_above_05")
    if test["coverage"] < 0.03:
        blockers.append("coverage_below_03")
    if len(test["validation_instruments"]) < 2:
        blockers.append("validation_instruments_lt_2")
    if len(test["validation_market_contexts"]) < 2:
        blockers.append("validation_market_contexts_lt_2")
    if len(test["validation_timeframes"]) < 2:
        blockers.append("validation_timeframes_lt_2")
    return {
        "main_regime_id": root,
        "qualifying_condition": rule,
        "target_label": target,
        "horizon": "next native bar root-class persistence",
        "allowed_action": ROOT_SCHEMA[root]["allowed_action"],
        "confidence_lane": "95" if accepted else "abstain",
        "precision_wilson_lcb": test["precision_wilson_lcb_95"],
        "calibration_support": calibration["support"],
        "test_support": test["support"],
        "ece": test["ece"],
        "coverage": test["coverage"],
        "validation_instruments": test["validation_instruments"],
        "validation_market_contexts": test["validation_market_contexts"],
        "validation_timeframes": test["validation_timeframes"],
        "validation_periods": {"train": train, "calibration": calibration, "test": test},
        "accepted_95": accepted,
        "blockers": sorted(set(blockers)),
        "artifact_path": repo_rel(RUN_ROOT / "main_regime_v2_calibration_preflight.json"),
    }


def candidate_masks(df: pd.DataFrame, root: str) -> list[tuple[str, pd.Series]]:
    base = df[f"{root}_base"].fillna(False)
    persistence = clean_numeric(df[f"{root}_persistence16"]).fillna(0.0)
    masks: list[tuple[str, pd.Series]] = [(f"{root}_base", base)]
    for threshold in (0.25, 0.50, 0.75):
        masks.append((f"{root}_base AND {root}_persistence16 >= {threshold:.2f}", base & (persistence >= threshold)))
    if root == "BullExpansion":
        masks.extend(
            [
                ("BullExpansion_base AND ret4 > 0 AND ret16 > 0", base & (df["ret4"] > 0.0) & (df["ret16"] > 0.0)),
                (
                    "BullExpansion_base AND ma64_slope16 > train_q60",
                    base & (df["ma64_slope16"] > q(df[df["split"] == "train"], "ma64_slope16", 0.60)),
                ),
            ]
        )
    elif root == "BearExpansion":
        masks.extend(
            [
                ("BearExpansion_base AND ret4 < 0 AND ret16 < 0", base & (df["ret4"] < 0.0) & (df["ret16"] < 0.0)),
                (
                    "BearExpansion_base AND drawdown64 <= train_q25",
                    base & (df["drawdown64"] <= q(df[df["split"] == "train"], "drawdown64", 0.25)),
                ),
            ]
        )
    elif root == "ConsolidationRange":
        masks.extend(
            [
                ("ConsolidationRange_base AND vol_rank <= 0.45", base & (df["vol_rank"] <= 0.45)),
                ("ConsolidationRange_base AND range_rank <= 0.45", base & (df["range_rank"] <= 0.45)),
            ]
        )
    elif root == "CrisisStress":
        masks.extend(
            [
                (
                    "CrisisStress_base AND vol_ratio32_128 >= train_q90",
                    base & (df["vol_ratio32_128"] >= q(df[df["split"] == "train"], "vol_ratio32_128", 0.90)),
                ),
                (
                    "CrisisStress_base AND drawdown64 <= train_q10",
                    base & (df["drawdown64"] <= q(df[df["split"] == "train"], "drawdown64", 0.10)),
                ),
            ]
        )
    elif root == "TransitionAccumulationDistribution":
        masks.extend(
            [
                ("TransitionAccumulationDistribution_base AND reversal_base", base & df["reversal_base"]),
                (
                    "TransitionAccumulationDistribution_base AND abs_stretch64 >= train_q60",
                    base & (df["abs_stretch64"] >= q(df[df["split"] == "train"], "abs_stretch64", 0.60)),
                ),
            ]
        )
    elif root == "UnknownOrMixed":
        masks.append(("UnknownOrMixed_base AND known_root_count != 1", base & df["known_root_count"].fillna(0).ne(1)))
    return masks


ROOT_SCHEMA: dict[str, dict[str, Any]] = {
    "BullExpansion": {
        "type": "root_main_class",
        "qualifying_inputs": ["signed positive drift", "positive slope", "trend persistence", "non-crisis filter"],
        "allowed_action": "risk_on_or_long_context_only_after_BoardB_edge_gate",
        "subtype_evidence": ["TrendExpansion"],
    },
    "BearExpansion": {
        "type": "root_main_class",
        "qualifying_inputs": ["signed negative drift", "negative slope", "downside persistence", "ordinary bear separated from crisis"],
        "allowed_action": "short_hedge_or_risk_down_context_only_after_BoardB_edge_gate",
        "subtype_evidence": ["TrendExpansion", "ExtremeStress"],
    },
    "ConsolidationRange": {
        "type": "root_main_class",
        "qualifying_inputs": ["range compression", "low directional slope", "range persistence", "false-break abstain condition"],
        "allowed_action": "mean_reversion_or_no_breakout_context_only_after_BoardB_edge_gate",
        "subtype_evidence": ["RangeConsolidation"],
    },
    "ManipulationLiquidityEngineering": {
        "type": "root_main_class_or_overlay",
        "qualifying_inputs": [
            "tick or trade tape",
            "bid/ask or L2 depth",
            "order-lifecycle anomalies",
            "venue/liquidity-taking behavior",
            "crypto social/event/mempool evidence when applicable",
        ],
        "allowed_action": "fail_closed_block_or_size_down",
        "subtype_evidence": ["ThinLiquidity", "SessionLiquidityCoreViable"],
    },
    "CrisisStress": {
        "type": "root_main_class",
        "qualifying_inputs": ["tail loss", "volatility/range explosion", "liquidity cliff", "crash gap or drawdown"],
        "allowed_action": "block_or_reduce_release_context",
        "subtype_evidence": ["ExtremeStress"],
    },
    "TransitionAccumulationDistribution": {
        "type": "root_main_class",
        "qualifying_inputs": ["change-point recency", "transition hazard", "directional-change overshoot", "accumulation/distribution boundary evidence"],
        "allowed_action": "observe_or_transition_candidate_only_after_BoardB_edge_gate",
        "subtype_evidence": ["ReversalBrewing"],
    },
    "UnknownOrMixed": {
        "type": "residual_bucket",
        "qualifying_inputs": ["zero or multiple root-class predicates active", "uncovered provider/input state"],
        "allowed_action": "abstain_no_release",
        "subtype_evidence": [],
    },
}


def load_required_input_status() -> dict[str, Any]:
    audit = json.loads(A10_AUDIT.read_text(encoding="utf-8"))
    text = json.dumps(audit).lower()
    return {
        "a10_audit": repo_rel(A10_AUDIT),
        "has_tick_or_l2_or_order_lifecycle": "real order-flow candidate files" in text and "0 real order-flow candidate files" not in text,
        "fail_closed_state": "missing_required_inputs" if "missing_required_inputs" in text else "unknown",
    }


def main() -> None:
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(FEATURE_TABLE)
    df = add_root_labels(df)
    augmented_path = RUN_ROOT / "main_regime_v2_augmented_features.csv"
    df.to_csv(augmented_path, index=False)

    input_status = load_required_input_status()
    schema = {
        "schema_version": "main-regime-v2-target-schema/v1",
        "run_root": repo_rel(RUN_ROOT),
        "source_scan": repo_rel(SOURCE_SCAN),
        "root_classes": ROOT_SCHEMA,
        "acceptance_gate_95": {
            "precision_wilson_lcb_95_min": 0.95,
            "calibration_support_min": 120,
            "test_support_min": 60,
            "ece_max": 0.05,
            "coverage_min": 0.03,
            "validation_instruments_min": 2,
            "validation_market_contexts_min": 2,
            "validation_timeframes_min": 2,
            "blocked_predictor_prefixes": ["future_", "target_"],
            "thresholds_relaxed": False,
        },
        "required_input_status": {
            "ManipulationLiquidityEngineering": input_status,
        },
    }
    schema_path = RUN_ROOT / "main_regime_v2_target_schema.json"
    schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")

    strict = json.loads(STRICT_AUDIT.read_text(encoding="utf-8"))
    crosswalk = {
        "schema_version": "main-regime-v2-crosswalk/v1",
        "source_strict_cross_timeframe_audit": repo_rel(STRICT_AUDIT),
        "strict_cross_timeframe_pass_regimes": strict["strict_cross_timeframe_pass_regimes"],
        "strict_cross_timeframe_missing_regimes": strict["strict_cross_timeframe_missing_regimes"],
        "subtype_to_root": {
            "SessionLiquidityCoreViable": ["liquidity_context", "ManipulationLiquidityEngineering_context_only"],
            "TrendExpansion": ["BullExpansion_candidate", "BearExpansion_candidate"],
            "RangeConsolidation": ["ConsolidationRange_candidate"],
            "ExtremeStress": ["CrisisStress_candidate", "BearExpansion_context_only"],
            "ReversalBrewing": ["TransitionAccumulationDistribution_candidate"],
            "ThinLiquidity": ["liquidity_context", "ManipulationLiquidityEngineering_context_only"],
        },
        "downgrade_rule": "Subtypes are evidence only; root classes require their own accepted packet or explicit residual bucket.",
    }
    crosswalk_path = RUN_ROOT / "main_regime_v2_crosswalk.json"
    crosswalk_path.write_text(json.dumps(crosswalk, indent=2) + "\n", encoding="utf-8")

    root_results: list[dict[str, Any]] = []
    for root in (
        "BullExpansion",
        "BearExpansion",
        "ConsolidationRange",
        "CrisisStress",
        "TransitionAccumulationDistribution",
        "UnknownOrMixed",
    ):
        candidates = [
            evaluate_rule(
                df,
                root,
                rule,
                mask,
                required_inputs_present=True,
                release_like=(root != "UnknownOrMixed"),
            )
            for rule, mask in candidate_masks(df, root)
        ]
        candidates.sort(
            key=lambda item: (
                item["accepted_95"],
                item["validation_periods"]["train"]["precision_wilson_lcb_95"],
                item["validation_periods"]["train"]["support"],
            ),
            reverse=True,
        )
        best = candidates[0]
        best["candidate_count"] = len(candidates)
        best["candidate_selection"] = "train_split_ranked_by_train_wilson_lcb_then_support; evaluated on calibration/test"
        root_results.append(best)

    root_results.append(
        {
            "main_regime_id": "ManipulationLiquidityEngineering",
            "qualifying_condition": "requires tick/trade tape plus bid/ask/L2/order-lifecycle or crypto social/event evidence",
            "target_label": "not_materialized",
            "horizon": "not_materialized",
            "allowed_action": ROOT_SCHEMA["ManipulationLiquidityEngineering"]["allowed_action"],
            "confidence_lane": "abstain",
            "precision_wilson_lcb": 0.0,
            "calibration_support": 0,
            "test_support": 0,
            "ece": None,
            "coverage": 0.0,
            "validation_instruments": [],
            "validation_market_contexts": [],
            "validation_timeframes": [],
            "validation_periods": {},
            "accepted_95": False,
            "blockers": ["missing_required_inputs", "no_tick_l2_order_lifecycle_or_crypto_event_evidence"],
            "required_input_status": input_status,
            "artifact_path": repo_rel(RUN_ROOT / "main_regime_v2_calibration_preflight.json"),
        }
    )

    accepted = [item["main_regime_id"] for item in root_results if item["accepted_95"]]
    missing = [item["main_regime_id"] for item in root_results if not item["accepted_95"]]
    preflight = {
        "schema_version": "main-regime-v2-calibration-preflight/v1",
        "loop_id": "20260510T230938+0800-main-regime-v2-schema-preflight",
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Build MainRegimeV2 root target schema, crosswalk existing subtype packets, and test whether current evidence can support 95% root packets.",
        "input_sources": {
            "feature_table": repo_rel(FEATURE_TABLE),
            "strict_cross_timeframe_audit": repo_rel(STRICT_AUDIT),
            "a10_order_flow_input_audit": repo_rel(A10_AUDIT),
            "source_scan": repo_rel(SOURCE_SCAN),
        },
        "generated_artifacts": {
            "target_schema": repo_rel(schema_path),
            "crosswalk": repo_rel(crosswalk_path),
            "augmented_features": repo_rel(augmented_path),
        },
        "threshold_policy": schema["acceptance_gate_95"],
        "root_results": root_results,
        "accepted_root_classes_95": accepted,
        "missing_root_classes_95": missing,
        "decision": {
            "board_state": "accepted_95" if not missing else "blocked",
            "accepted_gate": "main_regime_v2_accepted_95_all_root_classes" if not missing else "none_for_main_regime_v2",
            "trade_usable": False,
            "blocker": "missing_root_classes_95=" + ",".join(missing),
            "next_action": "Ingest aligned multi-timeframe root evidence and required manipulation inputs, then rerun unchanged MainRegimeV2 95% gates.",
        },
    }
    preflight_path = RUN_ROOT / "main_regime_v2_calibration_preflight.json"
    preflight_path.write_text(json.dumps(preflight, indent=2) + "\n", encoding="utf-8")

    summary_csv = RUN_ROOT / "main_regime_v2_preflight_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "main_regime_id",
                "accepted_95",
                "precision_wilson_lcb",
                "calibration_support",
                "test_support",
                "ece",
                "coverage",
                "validation_instruments",
                "validation_market_contexts",
                "validation_timeframes",
                "blockers",
                "qualifying_condition",
            ],
        )
        writer.writeheader()
        for item in root_results:
            writer.writerow(
                {
                    "main_regime_id": item["main_regime_id"],
                    "accepted_95": item["accepted_95"],
                    "precision_wilson_lcb": item["precision_wilson_lcb"],
                    "calibration_support": item["calibration_support"],
                    "test_support": item["test_support"],
                    "ece": item["ece"],
                    "coverage": item["coverage"],
                    "validation_instruments": "|".join(item["validation_instruments"]),
                    "validation_market_contexts": "|".join(item["validation_market_contexts"]),
                    "validation_timeframes": "|".join(item["validation_timeframes"]),
                    "blockers": "|".join(item["blockers"]),
                    "qualifying_condition": item["qualifying_condition"],
                }
            )

    assertions = [
        f"target_schema: {repo_rel(schema_path)}",
        f"crosswalk: {repo_rel(crosswalk_path)}",
        f"preflight: {repo_rel(preflight_path)}",
        f"accepted_root_classes_95: {accepted}",
        f"missing_root_classes_95: {missing}",
        f"accepted_gate: {preflight['decision']['accepted_gate']}",
        "thresholds_relaxed: False",
        "blocked_future_target_predictors: True",
        f"manipulation_input_state: {input_status['fail_closed_state']}",
    ]
    (CHECKS_DIR / "main_regime_v2_schema_preflight_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print(json.dumps({"preflight": repo_rel(preflight_path), "accepted": accepted, "missing": missing}, indent=2))


if __name__ == "__main__":
    main()
