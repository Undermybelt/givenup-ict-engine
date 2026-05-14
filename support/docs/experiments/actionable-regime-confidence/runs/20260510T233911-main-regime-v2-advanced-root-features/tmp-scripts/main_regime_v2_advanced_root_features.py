from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T233911-main-regime-v2-advanced-root-features"
CHECKS_DIR = RUN_ROOT / "checks"

SOURCE_FEATURES = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260510T230938-main-regime-v2-schema-preflight/main_regime_v2_augmented_features.csv"
)
PREV_PREFLIGHT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260510T230938-main-regime-v2-schema-preflight/main_regime_v2_calibration_preflight.json"
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


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)


def train_q(df: pd.DataFrame, col: str, quantile: float) -> float:
    values = numeric(df.loc[df["split"] == "train", col]).dropna()
    if values.empty:
        return float("nan")
    return float(values.quantile(quantile))


def train_z(df: pd.DataFrame, col: str) -> pd.Series:
    train_values = numeric(df.loc[df["split"] == "train", col]).dropna()
    if train_values.empty:
        return pd.Series(np.nan, index=df.index)
    mean = float(train_values.mean())
    std = float(train_values.std(ddof=0))
    if std <= 1e-12:
        std = 1.0
    return (numeric(df[col]) - mean) / std


def add_advanced_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ts"] = pd.to_datetime(out["ts"], utc=True)
    sort_cols = ["context", "ts"]
    out = out.sort_values(sort_cols).reset_index(drop=True)
    for col in (
        "open",
        "high",
        "low",
        "close",
        "ret1",
        "ret4",
        "ret16",
        "range_pct",
        "ma64_slope16",
        "ma32_slope8",
        "stretch64",
        "vol16",
        "vol_rank",
        "range_rank",
        "volume_rank",
        "vol_ratio32_128",
        "range_ratio32_128",
        "drawdown64",
        "BullExpansion_persistence16",
        "BearExpansion_persistence16",
        "ConsolidationRange_persistence16",
        "CrisisStress_persistence16",
        "TransitionAccumulationDistribution_persistence16",
        "UnknownOrMixed_persistence16",
    ):
        if col in out.columns:
            out[col] = numeric(out[col])

    out["log_close"] = np.log(out["close"])
    grp = out.groupby("context", group_keys=False)
    out["ret8"] = grp["log_close"].diff(8)
    out["ret32"] = grp["log_close"].diff(32)
    out["future_ret4"] = grp["log_close"].shift(-4) - out["log_close"]
    out["future_ret8"] = grp["log_close"].shift(-8) - out["log_close"]
    out["future_abs_ret4"] = out["future_ret4"].abs()
    out["future_range4"] = grp["range_pct"].shift(-1).rolling(4, min_periods=2).mean().reset_index(level=0, drop=True)
    out["future_vol4"] = grp["ret1"].shift(-1).rolling(4, min_periods=2).std().reset_index(level=0, drop=True)

    out["ret4_z"] = train_z(out, "ret4")
    out["ret16_z"] = train_z(out, "ret16")
    out["ret32_z"] = train_z(out, "ret32")
    out["slope64_z"] = train_z(out, "ma64_slope16")
    out["slope32_z"] = train_z(out, "ma32_slope8")
    out["vol_ratio_z"] = train_z(out, "vol_ratio32_128")
    out["range_ratio_z"] = train_z(out, "range_ratio32_128")
    out["abs_slope_z"] = train_z(out.assign(abs_slope=out["ma64_slope16"].abs()), "abs_slope")
    out["abs_stretch_z"] = train_z(out.assign(abs_stretch=out["stretch64"].abs()), "abs_stretch")

    # Directional-change style proxies: price extensions from recent extrema, normalized by train range.
    median_range = max(train_q(out, "range_pct", 0.50), 1e-6)
    rolling_low = grp["low"].rolling(16, min_periods=8).min().reset_index(level=0, drop=True)
    rolling_high = grp["high"].rolling(16, min_periods=8).max().reset_index(level=0, drop=True)
    out["dc_up_extension"] = out["close"] / rolling_low - 1.0
    out["dc_down_extension"] = out["close"] / rolling_high - 1.0
    out["dc_up_event"] = out["dc_up_extension"] >= (2.0 * median_range)
    out["dc_down_event"] = out["dc_down_extension"] <= (-2.0 * median_range)
    out["dc_up_rate16"] = grp["dc_up_event"].rolling(16, min_periods=4).mean().reset_index(level=0, drop=True)
    out["dc_down_rate16"] = grp["dc_down_event"].rolling(16, min_periods=4).mean().reset_index(level=0, drop=True)

    out["bull_state_score"] = (
        out["ret4_z"].fillna(0)
        + out["ret16_z"].fillna(0)
        + out["ret32_z"].fillna(0)
        + out["slope64_z"].fillna(0)
        + out["slope32_z"].fillna(0)
        + out["dc_up_rate16"].fillna(0)
        - out["CrisisStress_persistence16"].fillna(0)
    )
    out["bear_state_score"] = (
        -out["ret4_z"].fillna(0)
        - out["ret16_z"].fillna(0)
        - out["ret32_z"].fillna(0)
        - out["slope64_z"].fillna(0)
        - out["slope32_z"].fillna(0)
        + out["dc_down_rate16"].fillna(0)
    )
    out["consolidation_state_score"] = (
        -out["abs_slope_z"].fillna(0)
        - out["abs_stretch_z"].fillna(0)
        - out["vol_rank"].fillna(0.5)
        - out["range_rank"].fillna(0.5)
        + out["ConsolidationRange_persistence16"].fillna(0)
    )
    out["root_confidence_proxy"] = out[["bull_state_score", "bear_state_score", "consolidation_state_score"]].max(axis=1)

    # H4 target labels are future-root persistence labels, not predictors.
    out["target_BullExpansion_h4"] = (
        (out["future_ret4"] > max(0.0, train_q(out, "future_ret4", 0.60)))
        & (grp["BullExpansion_base"].shift(-1).rolling(4, min_periods=2).mean().reset_index(level=0, drop=True) >= 0.50)
    ).astype(float)
    out["target_BearExpansion_h4"] = (
        (out["future_ret4"] < min(0.0, train_q(out, "future_ret4", 0.40)))
        & (grp["BearExpansion_base"].shift(-1).rolling(4, min_periods=2).mean().reset_index(level=0, drop=True) >= 0.50)
    ).astype(float)
    out["target_ConsolidationRange_h4"] = (
        (out["future_abs_ret4"] <= train_q(out, "future_abs_ret4", 0.55))
        & (out["future_range4"] <= train_q(out, "future_range4", 0.60))
        & (out["future_vol4"] <= train_q(out, "future_vol4", 0.60))
        & (grp["ConsolidationRange_base"].shift(-1).rolling(4, min_periods=2).mean().reset_index(level=0, drop=True) >= 0.50)
    ).astype(float)
    known_targets = (
        out["target_BullExpansion_h4"].fillna(0)
        + out["target_BearExpansion_h4"].fillna(0)
        + out["target_ConsolidationRange_h4"].fillna(0)
        + out["target_CrisisStress_next"].fillna(0)
        + out["target_TransitionAccumulationDistribution_next"].fillna(0)
    )
    out["target_UnknownOrMixed_h4"] = known_targets.ne(1).astype(float)
    return out


def metric(df: pd.DataFrame, mask: pd.Series, split: str, target: str, probability: float | None = None) -> dict[str, Any]:
    valid = (df["split"] == split) & df[target].notna()
    selected = valid & mask.fillna(False)
    support = int(selected.sum())
    success = int(df.loc[selected, target].sum()) if support else 0
    precision = success / support if support else 0.0
    selected_df = df.loc[selected]
    valid_count = int(valid.sum())
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


def passes_95(calibration: dict[str, Any], test: dict[str, Any], release_like: bool = True) -> bool:
    return bool(
        release_like
        and calibration["support"] >= 120
        and test["support"] >= 60
        and test["precision_wilson_lcb_95"] >= 0.95
        and test["ece"] <= 0.05
        and test["coverage"] >= 0.03
        and len(test["validation_instruments"]) >= 2
        and len(test["validation_market_contexts"]) >= 2
        and len(test["validation_timeframes"]) >= 2
    )


def evaluate_candidate(df: pd.DataFrame, root: str, rule: str, mask: pd.Series, target: str, release_like: bool = True) -> dict[str, Any]:
    train = metric(df, mask, "train", target)
    calibration = metric(df, mask, "calibration", target, train["precision"])
    test = metric(df, mask, "test", target, calibration["precision"])
    accepted = passes_95(calibration, test, release_like=release_like)
    blockers: list[str] = []
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
    if not release_like:
        blockers.append("residual_or_abstain_bucket_not_release_gate")
    return {
        "main_regime_id": root,
        "qualifying_condition": rule,
        "target_label": target,
        "horizon": "next 4 native bars",
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
    }


def candidate_grid(df: pd.DataFrame, root: str) -> list[tuple[str, pd.Series, str, bool]]:
    cands: list[tuple[str, pd.Series, str, bool]] = []
    train = df[df["split"] == "train"]
    if root == "BullExpansion":
        target = "target_BullExpansion_h4"
        for score_q in (0.55, 0.60, 0.70, 0.80, 0.90):
            for persist in (0.25, 0.50, 0.75, 0.875):
                mask = (
                    (df["bull_state_score"] >= train_q(df, "bull_state_score", score_q))
                    & (df["BullExpansion_persistence16"].fillna(0) >= persist)
                    & (df["CrisisStress_persistence16"].fillna(0) <= 0.25)
                )
                cands.append((f"bull_state_score >= train_q{score_q} AND BullExpansion_persistence16 >= {persist}", mask, target, True))
    elif root == "BearExpansion":
        target = "target_BearExpansion_h4"
        for score_q in (0.55, 0.60, 0.70, 0.80, 0.90):
            for persist in (0.25, 0.50, 0.75, 0.875):
                mask = (
                    (df["bear_state_score"] >= train_q(df, "bear_state_score", score_q))
                    & (df["BearExpansion_persistence16"].fillna(0) >= persist)
                    & (df["CrisisStress_persistence16"].fillna(0) <= 0.50)
                )
                cands.append((f"bear_state_score >= train_q{score_q} AND BearExpansion_persistence16 >= {persist}", mask, target, True))
    elif root == "ConsolidationRange":
        target = "target_ConsolidationRange_h4"
        for score_q in (0.55, 0.60, 0.70, 0.80, 0.90):
            for persist in (0.25, 0.50, 0.75, 0.875):
                mask = (
                    (df["consolidation_state_score"] >= train_q(df, "consolidation_state_score", score_q))
                    & (df["ConsolidationRange_persistence16"].fillna(0) >= persist)
                    & (df["CrisisStress_persistence16"].fillna(0) <= 0.25)
                )
                cands.append((f"consolidation_state_score >= train_q{score_q} AND ConsolidationRange_persistence16 >= {persist}", mask, target, True))
    elif root == "UnknownOrMixed":
        target = "target_UnknownOrMixed_h4"
        for conf_q in (0.20, 0.30, 0.40):
            mask = df["root_confidence_proxy"] <= train_q(df, "root_confidence_proxy", conf_q)
            cands.append((f"root_confidence_proxy <= train_q{conf_q}", mask, target, False))
    return cands


def main() -> None:
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SOURCE_FEATURES)
    advanced = add_advanced_features(df)
    features_path = RUN_ROOT / "advanced_root_features.csv"
    advanced.to_csv(features_path, index=False)

    root_results: list[dict[str, Any]] = []
    top_candidates: dict[str, list[dict[str, Any]]] = {}
    for root in ("BullExpansion", "BearExpansion", "ConsolidationRange", "UnknownOrMixed"):
        evaluated = [
            evaluate_candidate(advanced, root, rule, mask, target, release_like=release_like)
            for rule, mask, target, release_like in candidate_grid(advanced, root)
        ]
        evaluated.sort(
            key=lambda item: (
                item["accepted_95"],
                item["validation_periods"]["train"]["precision_wilson_lcb_95"],
                item["precision_wilson_lcb"],
                item["test_support"],
            ),
            reverse=True,
        )
        best = evaluated[0]
        best["candidate_count"] = len(evaluated)
        best["candidate_selection"] = "train_split_ranked_by_train_wilson_lcb_then_test_lcb; evaluated on calibration/test"
        root_results.append(best)
        top_candidates[root] = evaluated[:8]

    previous = json.loads(PREV_PREFLIGHT.read_text(encoding="utf-8"))
    carried = [
        item
        for item in previous["root_results"]
        if item["main_regime_id"] in {"CrisisStress", "TransitionAccumulationDistribution", "ManipulationLiquidityEngineering"}
    ]
    all_results = root_results + carried
    accepted = [item["main_regime_id"] for item in all_results if item.get("accepted_95")]
    missing = [item["main_regime_id"] for item in all_results if not item.get("accepted_95")]

    report = {
        "schema_version": "main-regime-v2-advanced-root-features/v1",
        "loop_id": "20260510T233911+0800-main-regime-v2-advanced-root-features",
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Try stronger directional-change/persistence/segmentation-style root features for missing MainRegimeV2 classes without threshold relaxation.",
        "input_sources": {
            "source_features": repo_rel(SOURCE_FEATURES),
            "previous_preflight": repo_rel(PREV_PREFLIGHT),
        },
        "generated_artifacts": {
            "advanced_features": repo_rel(features_path),
            "summary_csv": repo_rel(RUN_ROOT / "advanced_root_feature_summary.csv"),
        },
        "feature_notes": [
            "No sklearn/hmmlearn/ruptures package is installed in this environment; this run uses deterministic local directional-change and state-score proxies.",
            "Predictors exclude future_* and target_* columns; future labels are targets only.",
            "Thresholds are selected on the train split and evaluated on chronological calibration/test splits.",
        ],
        "threshold_policy": {
            "precision_wilson_lcb_95_min": 0.95,
            "calibration_support_min": 120,
            "test_support_min": 60,
            "ece_max": 0.05,
            "coverage_min": 0.03,
            "validation_instruments_min": 2,
            "validation_market_contexts_min": 2,
            "validation_timeframes_min": 2,
            "thresholds_relaxed": False,
            "blocked_predictor_prefixes": ["future_", "target_"],
        },
        "root_results": all_results,
        "top_candidates_for_missing_roots": top_candidates,
        "accepted_root_classes_95": accepted,
        "missing_root_classes_95": missing,
        "decision": {
            "board_state": "accepted_95" if not missing else "blocked",
            "accepted_gate": "main_regime_v2_accepted_95_all_root_classes" if not missing else "none_for_main_regime_v2",
            "trade_usable": False,
            "blocker": "missing_root_classes_95=" + ",".join(missing),
            "next_action": "The remaining root gaps require new provider inputs or materially better root labels; current OHLCV-derived advanced features did not close all MainRegimeV2 gates.",
        },
    }
    report_path = RUN_ROOT / "advanced_root_feature_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    summary_path = RUN_ROOT / "advanced_root_feature_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
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
        for item in all_results:
            writer.writerow(
                {
                    "main_regime_id": item["main_regime_id"],
                    "accepted_95": item.get("accepted_95"),
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
        f"report: {repo_rel(report_path)}",
        f"accepted_root_classes_95: {accepted}",
        f"missing_root_classes_95: {missing}",
        f"accepted_gate: {report['decision']['accepted_gate']}",
        "thresholds_relaxed: False",
        "blocked_future_target_predictors: True",
    ]
    for item in all_results:
        assertions.append(
            f"{item['main_regime_id']}: accepted={item.get('accepted_95')} "
            f"lcb={float(item['precision_wilson_lcb']):.6f} "
            f"cal={item['calibration_support']} test={item['test_support']} blockers={item['blockers']}"
        )
    (CHECKS_DIR / "advanced_root_feature_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"report": repo_rel(report_path), "accepted": accepted, "missing": missing}, indent=2))


if __name__ == "__main__":
    main()
