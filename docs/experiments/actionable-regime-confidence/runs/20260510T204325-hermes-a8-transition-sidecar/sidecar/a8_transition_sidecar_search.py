from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T204325-hermes-a8-transition-sidecar"
PREVIOUS_SEARCH = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/calibration/per_regime_candidate_search.py"
PRIOR_ACCEPTED = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/evidence_packet_regime_persistence_expansion.json"
OUT_DIR = RUN_ROOT / "sidecar"
CHECKS_DIR = RUN_ROOT / "checks"

MISSING_REGIMES = ["TrendExpansion", "ExtremeStress", "ReversalBrewing"]

SIDECAR_FEATURES = [
    "ret_abs_z_64",
    "ret_pos_z_64",
    "ret_neg_z_64",
    "jump_intensity_32",
    "up_jump_intensity_32",
    "down_jump_intensity_32",
    "sign_flip_rate_16",
    "trend_persistence_16",
    "trend_run_len_norm_16",
    "vol_accel_16_64",
    "range_accel_16_64",
    "volume_z_64",
    "volume_drought_32",
    "compression_persistence_32",
    "stress_persistence_32",
    "trend_condition_persistence_32",
    "reversal_pressure_16",
    "drawdown_from_32_high",
    "rally_from_32_low",
    "ma32_slope_16",
]


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("per_regime_candidate_search", PREVIOUS_SEARCH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {PREVIOUS_SEARCH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def add_sidecar_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = out.sort_values(["instrument", "market", "timeframe", "ts"]).reset_index(drop=True)
    context_cols = ["instrument", "market", "timeframe"]
    for _, idx in out.groupby(context_cols, sort=False).groups.items():
        idx = list(idx)
        g = out.loc[idx].copy()
        ret = pd.to_numeric(g["ret_1"], errors="coerce")
        ret4 = pd.to_numeric(g["ret_4"], errors="coerce")
        close = pd.to_numeric(g["close"], errors="coerce")
        high = pd.to_numeric(g["high"], errors="coerce")
        low = pd.to_numeric(g["low"], errors="coerce")
        volume = pd.to_numeric(g["volume"], errors="coerce")
        range_pct = pd.to_numeric(g["range_pct"], errors="coerce")
        vol_rank = pd.to_numeric(g["realized_vol_rank_252"], errors="coerce")
        range_rank = pd.to_numeric(g["range_rank_252"], errors="coerce")
        volume_rank = pd.to_numeric(g["volume_rank_252"], errors="coerce")
        stretch_rank = pd.to_numeric(g["stretch_abs_rank_252"], errors="coerce")

        eps = 1e-12
        vol64 = ret.rolling(64, min_periods=20).std()
        ret_z = ret / (vol64 + eps)
        out.loc[idx, "ret_abs_z_64"] = ret_z.abs().to_numpy()
        out.loc[idx, "ret_pos_z_64"] = ret_z.clip(lower=0.0).to_numpy()
        out.loc[idx, "ret_neg_z_64"] = (-ret_z.clip(upper=0.0)).to_numpy()
        out.loc[idx, "jump_intensity_32"] = (ret_z.abs() >= 2.0).rolling(32, min_periods=8).mean().to_numpy()
        out.loc[idx, "up_jump_intensity_32"] = (ret_z >= 2.0).rolling(32, min_periods=8).mean().to_numpy()
        out.loc[idx, "down_jump_intensity_32"] = (ret_z <= -2.0).rolling(32, min_periods=8).mean().to_numpy()

        sign = np.sign(ret.fillna(0.0))
        sign_series = pd.Series(sign, index=g.index)
        sign_flip = (sign_series != sign_series.shift(1)) & (sign_series != 0) & (sign_series.shift(1) != 0)
        out.loc[idx, "sign_flip_rate_16"] = sign_flip.rolling(16, min_periods=6).mean().to_numpy()
        out.loc[idx, "trend_persistence_16"] = sign_series.rolling(16, min_periods=6).mean().abs().to_numpy()

        run_lengths: list[float] = []
        last = 0.0
        run = 0
        for value in sign_series.to_numpy():
            if value == 0:
                run = 0
                last = 0.0
            elif value == last:
                run += 1
            else:
                run = 1
                last = value
            run_lengths.append(min(run, 16) / 16.0)
        out.loc[idx, "trend_run_len_norm_16"] = run_lengths

        vol16 = ret.rolling(16, min_periods=8).std()
        range16 = range_pct.rolling(16, min_periods=8).mean()
        range64 = range_pct.rolling(64, min_periods=20).mean()
        out.loc[idx, "vol_accel_16_64"] = (vol16 / (vol64 + eps) - 1.0).to_numpy()
        out.loc[idx, "range_accel_16_64"] = (range16 / (range64 + eps) - 1.0).to_numpy()

        log_volume = np.log(volume.clip(lower=0.0) + 1.0)
        vol_mean64 = log_volume.rolling(64, min_periods=20).mean()
        vol_std64 = log_volume.rolling(64, min_periods=20).std()
        out.loc[idx, "volume_z_64"] = ((log_volume - vol_mean64) / (vol_std64 + eps)).to_numpy()
        out.loc[idx, "volume_drought_32"] = (volume_rank <= 0.20).rolling(32, min_periods=8).mean().to_numpy()
        out.loc[idx, "compression_persistence_32"] = ((range_rank <= 0.35) & (vol_rank <= 0.35)).rolling(32, min_periods=8).mean().to_numpy()
        out.loc[idx, "stress_persistence_32"] = ((range_rank >= 0.85) | (vol_rank >= 0.85)).rolling(32, min_periods=8).mean().to_numpy()

        trend_condition = (ret4 > 0) & (close > close.rolling(32, min_periods=12).mean())
        out.loc[idx, "trend_condition_persistence_32"] = trend_condition.rolling(32, min_periods=8).mean().to_numpy()
        out.loc[idx, "reversal_pressure_16"] = (stretch_rank * out.loc[idx, "sign_flip_rate_16"].astype(float)).to_numpy()

        roll_high = high.rolling(32, min_periods=12).max()
        roll_low = low.rolling(32, min_periods=12).min()
        out.loc[idx, "drawdown_from_32_high"] = (close / (roll_high + eps) - 1.0).to_numpy()
        out.loc[idx, "rally_from_32_low"] = (close / (roll_low + eps) - 1.0).to_numpy()
        ma32 = close.rolling(32, min_periods=12).mean()
        out.loc[idx, "ma32_slope_16"] = (ma32 / (ma32.shift(16) + eps) - 1.0).to_numpy()

    return out


def context_acceptance_summary(report: dict[str, Any]) -> dict[str, Any]:
    accepted = json.loads(PRIOR_ACCEPTED.read_text(encoding="utf-8"))
    packets = accepted.get("accepted_new_regime_packets", [])
    return {
        "existing_session_liquidity": accepted.get("existing_accepted_regime_packets", []),
        "prior_accepted_new_packets": packets,
        "missing_regimes_after_prior_acceptance": MISSING_REGIMES,
        "a8_accepted_missing_regimes": [
            candidate["regime_id"]
            for result in report["results_by_regime"].values()
            for candidate in result["accepted_candidates"]
            if candidate["passes_95"] or candidate["passes_99"]
        ],
    }


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    import csv

    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    base = load_base_module()
    df = add_sidecar_features(base.load_data())
    feature_table = OUT_DIR / "a8_transition_sidecar_features.csv"
    df.to_csv(feature_table, index=False)

    expanded_features = list(base.FEATURES) + SIDECAR_FEATURES
    base.FEATURES = expanded_features
    split_idx = base.indices(df)
    predicates = base.build_predicates(df, split_idx["train"])
    results_list = [base.search_regime(df, split_idx, predicates, regime) for regime in MISSING_REGIMES]
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
        "schema_version": "board-a-a8-transition-sidecar-search/v1",
        "loop_id": "20260510T204325+0800-hermes-a8-transition-sidecar",
        "run_root": repo_rel(RUN_ROOT),
        "source_features": repo_rel(base.FEATURE_TABLE),
        "sidecar_feature_table": repo_rel(feature_table),
        "prior_accepted_packet_source": repo_rel(PRIOR_ACCEPTED),
        "search_policy": {
            "thresholds_relaxed": False,
            "threshold_source": "train split only",
            "candidate_selection_source": "train split only",
            "blocked_feature_prefixes": ["future_", "target_"],
            "searched_features": expanded_features,
            "sidecar_features": SIDECAR_FEATURES,
            "searched_missing_regimes": MISSING_REGIMES,
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
        },
        "validation_universe": [
            {
                "instrument": instrument,
                "market": market,
                "timeframe": timeframe,
                "rows": int(len(group)),
                "time_range": {"start": str(group["ts"].min()), "end": str(group["ts"].max())},
            }
            for (instrument, market, timeframe), group in df.groupby(["instrument", "market", "timeframe"], sort=False)
        ],
        "accepted_95_candidates": accepted_95,
        "accepted_99_candidates": accepted_99,
        "results_by_regime": results,
        "summary": {
            "searched_missing_regimes": MISSING_REGIMES,
            "accepted_95_count": len(accepted_95),
            "accepted_99_count": len(accepted_99),
            "missing_regime_acceptance_complete": all(len(result["accepted_candidates"]) > 0 for result in results_list),
            "thresholds_relaxed": False,
        },
    }
    report["acceptance_context"] = context_acceptance_summary(report)

    report_path = OUT_DIR / "a8_transition_sidecar_candidate_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    rule_path = OUT_DIR / "a8_transition_sidecar_candidate_rules.csv"
    write_csv(base.flatten_rows(results_list), rule_path)

    accepted_by_regime = {regime: len(results[regime]["accepted_candidates"]) for regime in MISSING_REGIMES}
    assertions = [
        f"searched_missing_regimes: {MISSING_REGIMES}",
        f"accepted_by_missing_regime: {accepted_by_regime}",
        f"blocked_future_target_predictors: {not any(f.startswith('future_') or f.startswith('target_') for f in expanded_features)}",
        f"sidecar_feature_count: {len(SIDECAR_FEATURES)}",
        f"thresholds_relaxed: {report['summary']['thresholds_relaxed']}",
        f"missing_regime_acceptance_complete: {report['summary']['missing_regime_acceptance_complete']}",
    ]
    assertion_path = CHECKS_DIR / "a8_transition_sidecar_assertions.out"
    assertion_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    evidence_packet = {
        "schema_version": "board-a-a8-transition-sidecar-evidence/v1",
        "loop_id": report["loop_id"],
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Build jump-model, persistence-penalty, and transition-hazard sidecar features for missing regimes and rerun chronological calibration without relaxing thresholds.",
        "provider_status_source": "docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/provider/provider-status-agent.json",
        "auto_quant_status_source": "docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/autoquant/auto-quant-status-agent.json",
        "source_feature_table": repo_rel(base.FEATURE_TABLE),
        "sidecar_feature_table": repo_rel(feature_table),
        "candidate_search_report": repo_rel(report_path),
        "candidate_rule_table": repo_rel(rule_path),
        "assertions": repo_rel(assertion_path),
        "searched_missing_regimes": MISSING_REGIMES,
        "accepted_95_candidates": len(accepted_95),
        "accepted_99_candidates": len(accepted_99),
        "missing_regime_acceptance_complete": report["summary"]["missing_regime_acceptance_complete"],
        "thresholds_relaxed": False,
        "blocked_feature_prefixes": ["future_", "target_"],
        "best_candidate_by_missing_regime": {
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
    packet_path = RUN_ROOT / "evidence_packet_a8_transition_sidecar.json"
    packet_path.write_text(json.dumps(evidence_packet, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(evidence_packet, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
