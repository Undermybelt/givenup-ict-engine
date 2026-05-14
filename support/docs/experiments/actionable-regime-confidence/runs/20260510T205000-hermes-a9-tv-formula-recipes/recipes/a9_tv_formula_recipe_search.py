from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T205000-hermes-a9-tv-formula-recipes"
BASE_SEARCH = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/calibration/per_regime_candidate_search.py"
RESEARCH_NOTE = REPO / "docs/market-regime-profitable-strategy-research-2026-05-10.md"
PRIOR_ACCEPTED = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/evidence_packet_regime_persistence_expansion.json"
OUT_DIR = RUN_ROOT / "recipes"
CHECKS_DIR = RUN_ROOT / "checks"

MISSING_REGIMES = ["TrendExpansion", "ExtremeStress", "ReversalBrewing"]

TV_FEATURES = [
    "tv_rsi_14",
    "tv_rsi_28",
    "tv_atr_pct_14",
    "tv_atr_rank_252",
    "tv_adx_14",
    "tv_plus_di_14",
    "tv_minus_di_14",
    "tv_dmi_spread_14",
    "tv_ma_slope_20",
    "tv_ma_slope_50",
    "tv_ma_spread_20_50",
    "tv_bb_width_20",
    "tv_bb_width_rank_252",
    "tv_volatility_pctile_63",
    "tv_volatility_pctile_252",
    "tv_trend_expansion_recipe",
    "tv_extreme_stress_recipe",
    "tv_reversal_brewing_recipe",
]


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("per_regime_candidate_search", BASE_SEARCH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {BASE_SEARCH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def pct_rank(series: pd.Series, window: int, min_periods: int) -> pd.Series:
    def last_rank(values: np.ndarray) -> float:
        s = pd.Series(values)
        return float(s.rank(pct=True).iloc[-1])

    return series.rolling(window, min_periods=min_periods).apply(last_rank, raw=True)


def rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / (avg_loss + 1e-12)
    return 100.0 - (100.0 / (1.0 + rs))


def dmi_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    prev_close = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=high.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=high.index)
    atr = tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    plus_di = 100.0 * plus_dm.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean() / (atr + 1e-12)
    minus_di = 100.0 * minus_dm.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean() / (atr + 1e-12)
    dx = 100.0 * (plus_di - minus_di).abs() / ((plus_di + minus_di) + 1e-12)
    adx = dx.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    return atr, plus_di, minus_di, adx


def add_tv_formula_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = out.sort_values(["instrument", "market", "timeframe", "ts"]).reset_index(drop=True)
    context_cols = ["instrument", "market", "timeframe"]
    for _, idx in out.groupby(context_cols, sort=False).groups.items():
        idx = list(idx)
        g = out.loc[idx].copy()
        high = pd.to_numeric(g["high"], errors="coerce")
        low = pd.to_numeric(g["low"], errors="coerce")
        close = pd.to_numeric(g["close"], errors="coerce")
        ret = pd.to_numeric(g["ret_1"], errors="coerce")
        atr14, plus_di, minus_di, adx = dmi_adx(high, low, close, 14)
        ma20 = close.rolling(20, min_periods=10).mean()
        ma50 = close.rolling(50, min_periods=20).mean()
        std20 = close.rolling(20, min_periods=10).std()
        bb_width = (4.0 * std20) / (ma20 + 1e-12)
        vol63 = ret.rolling(63, min_periods=20).std()
        vol252 = ret.rolling(252, min_periods=64).std()

        out.loc[idx, "tv_rsi_14"] = rsi(close, 14).to_numpy()
        out.loc[idx, "tv_rsi_28"] = rsi(close, 28).to_numpy()
        out.loc[idx, "tv_atr_pct_14"] = (atr14 / (close + 1e-12)).to_numpy()
        out.loc[idx, "tv_atr_rank_252"] = pct_rank(atr14 / (close + 1e-12), 252, 64).to_numpy()
        out.loc[idx, "tv_plus_di_14"] = plus_di.to_numpy()
        out.loc[idx, "tv_minus_di_14"] = minus_di.to_numpy()
        out.loc[idx, "tv_dmi_spread_14"] = (plus_di - minus_di).to_numpy()
        out.loc[idx, "tv_adx_14"] = adx.to_numpy()
        out.loc[idx, "tv_ma_slope_20"] = (ma20 / (ma20.shift(10) + 1e-12) - 1.0).to_numpy()
        out.loc[idx, "tv_ma_slope_50"] = (ma50 / (ma50.shift(20) + 1e-12) - 1.0).to_numpy()
        out.loc[idx, "tv_ma_spread_20_50"] = (ma20 / (ma50 + 1e-12) - 1.0).to_numpy()
        out.loc[idx, "tv_bb_width_20"] = bb_width.to_numpy()
        out.loc[idx, "tv_bb_width_rank_252"] = pct_rank(bb_width, 252, 64).to_numpy()
        out.loc[idx, "tv_volatility_pctile_63"] = pct_rank(vol63, 252, 64).to_numpy()
        out.loc[idx, "tv_volatility_pctile_252"] = pct_rank(vol252, 252, 64).to_numpy()

        trend_recipe = (
            (adx >= 22.0)
            & (plus_di > minus_di)
            & (ma20 > ma50)
            & ((ma20 / (ma20.shift(10) + 1e-12) - 1.0) > 0)
            & (pct_rank(atr14 / (close + 1e-12), 252, 64).fillna(0.5) <= 0.85)
        )
        stress_recipe = (
            (pct_rank(atr14 / (close + 1e-12), 252, 64).fillna(0.0) >= 0.85)
            | (pct_rank(bb_width, 252, 64).fillna(0.0) >= 0.85)
            | ((adx >= 28.0) & ((plus_di - minus_di).abs() >= 20.0))
        )
        reversal_recipe = (
            ((rsi(close, 14) >= 70.0) | (rsi(close, 14) <= 30.0))
            & (adx.diff(5) <= 0)
            & (pct_rank(bb_width, 252, 64).fillna(0.5) >= 0.60)
        )
        out.loc[idx, "tv_trend_expansion_recipe"] = trend_recipe.astype(float).to_numpy()
        out.loc[idx, "tv_extreme_stress_recipe"] = stress_recipe.astype(float).to_numpy()
        out.loc[idx, "tv_reversal_brewing_recipe"] = reversal_recipe.astype(float).to_numpy()

    return out


def recipe_manifest() -> dict[str, Any]:
    return {
        "schema_version": "tradingview-formula-recipe-manifest/v1",
        "source_policy": {
            "source_doc": repo_rel(RESEARCH_NOTE),
            "live_tradingview_mcp_status": "fail_closed_unhealthy",
            "profitability_trusted": False,
            "script_profit_or_backtest_used": False,
            "normalization_scope": "formula ingredients only: ADX/DMI, ATR, MA slope/spread, RSI, volatility percentile, Bollinger bandwidth",
        },
        "recipes": [
            {
                "recipe_id": "tv_style_trend_expansion_adx_ma_slope",
                "target_regime": "TrendExpansion",
                "formula": "ADX(14) >= 22 and +DI > -DI and MA20 > MA50 and MA20 slope > 0 and ATR percentile <= 0.85",
                "non_leaky_fields": ["high", "low", "close"],
                "features": ["tv_adx_14", "tv_dmi_spread_14", "tv_ma_spread_20_50", "tv_ma_slope_20", "tv_atr_rank_252"],
                "notes": "Trend/momentum community formula shape only; no script PnL used.",
            },
            {
                "recipe_id": "tv_style_extreme_stress_atr_bandwidth_dmi",
                "target_regime": "ExtremeStress",
                "formula": "ATR percentile >= 0.85 or Bollinger bandwidth percentile >= 0.85 or ADX(14) >= 28 with wide DMI spread",
                "non_leaky_fields": ["high", "low", "close"],
                "features": ["tv_atr_rank_252", "tv_bb_width_rank_252", "tv_adx_14", "tv_dmi_spread_14"],
                "notes": "Stress detector candidate only; no live TradingView data trusted.",
            },
            {
                "recipe_id": "tv_style_reversal_rsi_adx_decay_bandwidth",
                "target_regime": "ReversalBrewing",
                "formula": "RSI(14) extreme and ADX falling over 5 bars and Bollinger bandwidth percentile >= 0.60",
                "non_leaky_fields": ["high", "low", "close"],
                "features": ["tv_rsi_14", "tv_adx_14", "tv_bb_width_rank_252"],
                "notes": "Reversal setup formula candidate only; confirmation still requires chronological calibration.",
            },
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
    df = add_tv_formula_features(base.load_data())
    feature_table = OUT_DIR / "a9_tv_formula_features.csv"
    df.to_csv(feature_table, index=False)

    manifest = recipe_manifest()
    manifest_path = OUT_DIR / "tradingview_formula_recipe_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    expanded_features = list(base.FEATURES) + TV_FEATURES
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
        "schema_version": "board-a-a9-tv-formula-recipe-search/v1",
        "loop_id": "20260510T205000+0800-hermes-a9-tv-formula-recipes",
        "run_root": repo_rel(RUN_ROOT),
        "source_features": repo_rel(base.FEATURE_TABLE),
        "tv_formula_feature_table": repo_rel(feature_table),
        "recipe_manifest": repo_rel(manifest_path),
        "prior_accepted_packet_source": repo_rel(PRIOR_ACCEPTED),
        "search_policy": {
            "thresholds_relaxed": False,
            "threshold_source": "train split only",
            "candidate_selection_source": "train split only",
            "blocked_feature_prefixes": ["future_", "target_"],
            "profitability_trusted": False,
            "live_tradingview_data_used": False,
            "searched_features": expanded_features,
            "tv_formula_features": TV_FEATURES,
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
    report_path = OUT_DIR / "a9_tv_formula_candidate_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    rule_path = OUT_DIR / "a9_tv_formula_candidate_rules.csv"
    write_csv(base.flatten_rows(results_list), rule_path)

    accepted_by_regime = {regime: len(results[regime]["accepted_candidates"]) for regime in MISSING_REGIMES}
    assertions = [
        f"searched_missing_regimes: {MISSING_REGIMES}",
        f"accepted_by_missing_regime: {accepted_by_regime}",
        f"blocked_future_target_predictors: {not any(f.startswith('future_') or f.startswith('target_') for f in expanded_features)}",
        f"tv_formula_feature_count: {len(TV_FEATURES)}",
        f"live_tradingview_data_used: {report['search_policy']['live_tradingview_data_used']}",
        f"profitability_trusted: {report['search_policy']['profitability_trusted']}",
        f"thresholds_relaxed: {report['summary']['thresholds_relaxed']}",
        f"missing_regime_acceptance_complete: {report['summary']['missing_regime_acceptance_complete']}",
    ]
    assertion_path = CHECKS_DIR / "a9_tv_formula_recipe_assertions.out"
    assertion_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    evidence_packet = {
        "schema_version": "board-a-a9-tv-formula-recipes-evidence/v1",
        "loop_id": report["loop_id"],
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Normalize TradingView-style regime formulas into non-leaky feature recipes without trusting script profitability, then rerun missing-regime calibration.",
        "provider_status_source": "docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/provider/provider-status-agent.json",
        "source_research_note": repo_rel(RESEARCH_NOTE),
        "source_feature_table": repo_rel(base.FEATURE_TABLE),
        "recipe_manifest": repo_rel(manifest_path),
        "tv_formula_feature_table": repo_rel(feature_table),
        "candidate_search_report": repo_rel(report_path),
        "candidate_rule_table": repo_rel(rule_path),
        "assertions": repo_rel(assertion_path),
        "searched_missing_regimes": MISSING_REGIMES,
        "accepted_95_candidates": len(accepted_95),
        "accepted_99_candidates": len(accepted_99),
        "missing_regime_acceptance_complete": report["summary"]["missing_regime_acceptance_complete"],
        "thresholds_relaxed": False,
        "blocked_feature_prefixes": ["future_", "target_"],
        "live_tradingview_data_used": False,
        "profitability_trusted": False,
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
    packet_path = RUN_ROOT / "evidence_packet_a9_tv_formula_recipes.json"
    packet_path.write_text(json.dumps(evidence_packet, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(evidence_packet, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
