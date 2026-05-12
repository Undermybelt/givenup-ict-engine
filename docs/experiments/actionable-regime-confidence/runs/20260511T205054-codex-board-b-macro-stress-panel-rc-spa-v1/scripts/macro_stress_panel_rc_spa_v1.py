#!/usr/bin/env python3
"""Board B macro-stress panel RC-SPA readback.

Run-local additive experiment. It consumes the downloaded public Kaggle
macro-stress panel as a price/feature panel, not as source-owned regime labels.
Board A source-root labels still come from the accepted stock-market-regimes
schedule used by earlier Board B RC-SPA evaluators.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T205054+0800-codex-board-b-macro-stress-panel-rc-spa-v1"
SCHEMA_VERSION = "board-b-macro-stress-panel/v1"
RECIPE_ID = "MacroStressPanelRelativeValueV1"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
MACRO_CSV = Path("/tmp/ict-engine-public-source-intake-scout/macro/Global_Market_Stress_and_Liquidity_Regimes.csv")
NIFTY_BEHAVIOR_CSV = Path("/tmp/ict-engine-public-source-intake-scout/nifty/behavior_regime_predictions.csv")
BASE_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T193803-codex-board-b-root-transition-triad-clean-v1/scripts/"
    "board_b_root_transition_triad_clean_v1.py"
)

ASSET_COLUMNS = {
    "Equities_US": "Equities_US",
    "Equities_Tech": "Equities_Tech",
    "Equities_Emerging": "Equities_Emerging",
    "Bonds_LongTerm": "Bonds_LongTerm",
    "Gold": "Gold",
    "Oil": "Oil",
    "Crypto_Bitcoin": "Crypto_Bitcoin",
}


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("board_b_root_transition_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base evaluator: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_risk_asset(market: str) -> bool:
    return market in {"Equities_US", "Equities_Tech", "Equities_Emerging", "Oil", "Crypto_Bitcoin"}


def is_defensive_asset(market: str) -> bool:
    return market in {"Bonds_LongTerm", "Gold"}


def roundtrip_cost(market: str, timeframe: str) -> float:
    if market == "Crypto_Bitcoin":
        return 0.0015
    if market == "Oil":
        return 0.0010
    return 0.0007


def signal_direction(row: pd.Series, variant: dict[str, Any]) -> int:
    root = str(row["parent_regime_root"])
    market = str(row["market"])
    mode = str(variant["mode"])
    lookback = int(variant["lookback"])
    ema_col = f"ema{int(variant['ema'])}"
    trend = float(row.get(f"ret{lookback}", row["ret5"]))
    ret1 = float(row["ret1"])
    ret3 = float(row["ret3"])
    z_value = float(row["z20"])
    close = float(row["close"])
    ema_value = float(row[ema_col])
    ema50 = float(row["ema50"])
    z_threshold = float(variant["z"])
    stress = float(row["financial_stress_index"])
    high_yield_spread = float(row["high_yield_spread"])
    stock_bond_corr = float(row["stock_bond_corr_90d"])
    spy_drawdown = float(row["spy_drawdown"])
    spy_rsi = float(row["spy_rsi_14"])
    gl_d_rsi = float(row["gld_rsi_14"])
    risk_asset = is_risk_asset(market)
    defensive = is_defensive_asset(market)
    low_slope = abs(float(row["ema20_slope"])) < max(0.0025, float(row["realized_vol20"]) * 0.20)
    stress_high = stress > 0.15 or high_yield_spread >= 5.0 or spy_drawdown <= -0.10
    stress_low = stress < -0.10 and high_yield_spread <= 4.0

    if root == "Bull":
        if mode == "risk_on_momentum":
            return 1 if risk_asset and trend > 0 and close > ema_value and stress_low else 0
        if mode == "risk_on_pullback":
            return 1 if risk_asset and close > ema50 and z_value <= -z_threshold and ret1 > 0 else 0
        if mode == "defensive_fade":
            return -1 if defensive and trend < 0 and close < ema_value and stress_low else 0
        return 0

    if root == "Bear":
        if mode == "risk_off_short":
            return -1 if risk_asset and trend < 0 and close < ema_value else 0
        if mode == "defensive_long":
            return 1 if defensive and trend > 0 and close > ema_value else 0
        if mode == "credit_stress_short":
            return -1 if risk_asset and (stress_high or stock_bond_corr > 0.25) and ret3 < 0 else 0
        return 0

    if root == "Sideways":
        if mode == "range_reversion":
            if low_slope and z_value >= z_threshold:
                return -1
            if low_slope and z_value <= -z_threshold:
                return 1
        if mode == "rsi_reversion":
            if risk_asset and spy_rsi < 35 and ret1 > 0:
                return 1
            if market == "Gold" and gl_d_rsi > 65 and z_value > 0.5:
                return -1
        return 0

    if root == "Crisis":
        if mode == "crisis_defensive_long":
            return 1 if defensive and (trend > 0 or close > ema_value) and stress_high else 0
        if mode == "crisis_risk_short":
            return -1 if risk_asset and stress_high and (trend < 0 or ret3 < 0) else 0
        if mode == "panic_reversal":
            panic = risk_asset and spy_rsi < 28 and z_value <= -max(1.4, z_threshold)
            return 1 if panic and ret1 > 0 and stress < 1.0 else 0
        return 0

    return 0


def branch_path(module: Any, root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> MacroStressRiskOn -> RiskAssetMomentumOrPullback -> {RECIPE_ID}:{variant_id}"
    if root == "Bear":
        return f"{root} -> MacroStressRiskOff -> ShortOrDefensiveRotation -> {RECIPE_ID}:{variant_id}"
    if root == "Sideways":
        return f"{root} -> MacroStressRange -> CrossAssetMeanReversion -> {RECIPE_ID}:{variant_id}"
    if root == "Crisis":
        return f"{root} -> MacroStressCrisis -> DefensiveLongOrRiskShort -> {RECIPE_ID}:{variant_id}"
    return "Manipulation(scoped) -> DirectEventOverlayMissing -> no_direct_event_rows -> suppress_or_abstain"


def branch_fields(root: str) -> dict[str, str]:
    if root == "Bull":
        return {
            "sub_regime_tags": "MacroStressRiskOn",
            "sub_sub_regime_or_profit_factor": "RiskAssetMomentumOrPullback",
            "profit_factor_family": "macro_stress_relative_value",
            "allowed_action": "long_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bull_macro_stress_branch_rc_spa_fails",
        }
    if root == "Bear":
        return {
            "sub_regime_tags": "MacroStressRiskOff",
            "sub_sub_regime_or_profit_factor": "ShortOrDefensiveRotation",
            "profit_factor_family": "macro_stress_relative_value",
            "allowed_action": "short_or_defensive_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bear_macro_stress_branch_rc_spa_fails",
        }
    if root == "Sideways":
        return {
            "sub_regime_tags": "MacroStressRange",
            "sub_sub_regime_or_profit_factor": "CrossAssetMeanReversion",
            "profit_factor_family": "macro_stress_relative_value",
            "allowed_action": "long_short_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_sideways_macro_stress_branch_rc_spa_fails",
        }
    if root == "Crisis":
        return {
            "sub_regime_tags": "MacroStressCrisis",
            "sub_sub_regime_or_profit_factor": "DefensiveLongOrRiskShort",
            "profit_factor_family": "macro_stress_relative_value",
            "allowed_action": "short_or_defensive_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "tail_guard_blocks_macro_stress_branch_if_rc_spa_fails",
        }
    return {
        "sub_regime_tags": "DirectEventOverlayMissing",
        "sub_sub_regime_or_profit_factor": "no_direct_event_rows",
        "profit_factor_family": "direct_manipulation_overlay",
        "allowed_action": "suppress_or_abstain",
        "suppression_rule": "no_direct_manipulation_profit_rows",
    }


def load_panel(path: Path, market: str, timeframe: str, lookup: Any) -> pd.DataFrame:
    if path != MACRO_CSV:
        raise RuntimeError(f"unexpected macro panel path: {path}")
    close_col = ASSET_COLUMNS[market]
    df = pd.read_csv(path, parse_dates=["Date"])
    df["date"] = pd.to_datetime(df["Date"], utc=True)
    df = df[(df["date"] >= pd.Timestamp("2014-10-17", tz="UTC")) & (df["date"] <= pd.Timestamp("2026-01-31", tz="UTC"))].copy()
    df = df.sort_values("date").reset_index(drop=True)
    df["close"] = pd.to_numeric(df[close_col], errors="coerce")
    feature_cols = {
        "Financial_Stress_Index": "financial_stress_index",
        "High_Yield_Spread": "high_yield_spread",
        "Yield_Curve_Spread": "yield_curve_spread",
        "Stock_Bond_Corr_90d": "stock_bond_corr_90d",
        "SPY_Drawdown": "spy_drawdown",
        "SPY_RSI_14": "spy_rsi_14",
        "GLD_RSI_14": "gld_rsi_14",
        "SPY_Rolling_Vol_30d": "spy_rolling_vol_30d",
        "BTC_Rolling_Vol_30d": "btc_rolling_vol_30d",
    }
    for source_col, target_col in feature_cols.items():
        df[target_col] = pd.to_numeric(df[source_col], errors="coerce").ffill().bfill()
    df = df.dropna(subset=["close"]).reset_index(drop=True)
    df["session_date"] = df["date"].dt.tz_convert(None).dt.normalize()
    root_rows = [lookup.lookup(value) for value in df["session_date"]]
    root_df = pd.DataFrame(root_rows)
    df = pd.concat([df, root_df], axis=1)
    df["market"] = market
    df["timeframe"] = timeframe
    df["ret1"] = df["close"].pct_change().fillna(0.0)
    df["ret3"] = df["close"].pct_change(3).fillna(0.0)
    df["ret5"] = df["close"].pct_change(5).fillna(0.0)
    df["ret10"] = df["close"].pct_change(10).fillna(0.0)
    df["ret20"] = df["close"].pct_change(20).fillna(0.0)
    df["realized_vol20"] = df["ret1"].rolling(20, min_periods=10).std().fillna(0.0)
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    mean20 = df["close"].rolling(20, min_periods=10).mean()
    std20 = df["close"].rolling(20, min_periods=10).std()
    df["z20"] = ((df["close"] - mean20) / std20.replace(0, np.nan)).fillna(0.0)
    df["ema20_slope"] = df["ema20"].pct_change(5).fillna(0.0)
    return df


def patch_module(module: Any) -> None:
    module.RUN_ID = RUN_ID
    module.SCHEMA_VERSION = SCHEMA_VERSION
    module.RECIPE_ID = RECIPE_ID
    module.RUN_ROOT = RUN_ROOT
    module.OUT_DIR = RUN_ROOT / "branch-rc-spa"
    module.CHECK_DIR = RUN_ROOT / "checks"
    module.FAIL_CLOSED_DIR = RUN_ROOT / "ict-engine-fail-closed"
    module.ALL_ROWS_CSV = module.OUT_DIR / "macro_stress_panel_variant_rows_v1.csv"
    module.SELECTED_ROWS_CSV = module.OUT_DIR / "macro_stress_panel_selected_rows_v1.csv"
    module.SUMMARY_CSV = module.OUT_DIR / "macro_stress_panel_branch_summary_v1.csv"
    module.PANEL_SUMMARY_CSV = module.OUT_DIR / "macro_stress_panel_panel_summary_v1.csv"
    module.REPORT_JSON = module.OUT_DIR / "macro_stress_panel_rc_spa_report_v1.json"
    module.REPORT_MD = module.OUT_DIR / "macro_stress_panel_rc_spa_report_v1.md"
    module.ASSERTIONS = module.CHECK_DIR / "macro_stress_panel_rc_spa_v1_assertions.out"
    module.FAIL_CLOSED_MD = module.FAIL_CLOSED_DIR / "macro_stress_panel_fail_closed_summary_v1.md"
    module.PANELS = [(market, "1d", MACRO_CSV) for market in ASSET_COLUMNS]
    module.VARIANTS = [
        {"variant_id": "risk_on_momentum", "mode": "risk_on_momentum", "lookback": 20, "ema": 50, "z": 1.0, "hold": {"1d": 5}},
        {"variant_id": "risk_on_pullback", "mode": "risk_on_pullback", "lookback": 5, "ema": 20, "z": 1.0, "hold": {"1d": 4}},
        {"variant_id": "risk_off_short", "mode": "risk_off_short", "lookback": 10, "ema": 20, "z": 1.0, "hold": {"1d": 5}},
        {"variant_id": "credit_stress_short", "mode": "credit_stress_short", "lookback": 5, "ema": 20, "z": 0.9, "hold": {"1d": 5}},
        {"variant_id": "defensive_long", "mode": "defensive_long", "lookback": 10, "ema": 20, "z": 1.0, "hold": {"1d": 8}},
        {"variant_id": "range_reversion", "mode": "range_reversion", "lookback": 5, "ema": 20, "z": 0.9, "hold": {"1d": 4}},
        {"variant_id": "rsi_reversion", "mode": "rsi_reversion", "lookback": 5, "ema": 20, "z": 0.8, "hold": {"1d": 4}},
        {"variant_id": "crisis_defensive_long", "mode": "crisis_defensive_long", "lookback": 10, "ema": 20, "z": 1.0, "hold": {"1d": 8}},
        {"variant_id": "crisis_risk_short", "mode": "crisis_risk_short", "lookback": 5, "ema": 20, "z": 1.0, "hold": {"1d": 5}},
        {"variant_id": "panic_reversal", "mode": "panic_reversal", "lookback": 3, "ema": 20, "z": 1.2, "hold": {"1d": 4}},
    ]
    module.signal_direction = signal_direction
    module.roundtrip_cost = roundtrip_cost
    module.load_panel = load_panel
    module.branch_fields = branch_fields
    module.branch_path = lambda root, variant_id: branch_path(module, root, variant_id)


def rewrite_reports(module: Any) -> None:
    payload = json.loads(module.REPORT_JSON.read_text(encoding="utf-8"))
    decision = payload["decision"]
    payload["inputs"]["macro_stress_panel_csv"] = str(MACRO_CSV)
    payload["inputs"]["nifty_duplicate_scout_csv"] = str(NIFTY_BEHAVIOR_CSV)
    payload["inputs"]["macro_panel_boundary"] = (
        "price_feature_panel_only; not a source-owned MainRegimeV2 label panel; "
        "NIFTY scout is known duplicate/blocked without owner-approved crosswalk"
    )
    if decision["gate_result"] == "pass":
        decision["next_action"] = "B5: run Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree branch consumption."
    else:
        decision["next_action"] = (
            "B2R-repeat: macro-stress panel is scored fail-closed; do not reuse NIFTY/macro as source labels "
            "without owner-approved crosswalk, and acquire tradeable scoped Manipulation rows before downstream promotion."
        )
    module.REPORT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    branch_lines = [
        "| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["branch_summaries"]:
        branch_lines.append(
            f"| {row['parent_regime_root']} | `{row['selected_variant_id']}` | "
            f"{row['total_trades']} | {row['test_folds']} | {row['min_trades_per_test_fold']} | "
            f"{row['fold_positive_rate']:.4f} | {row['bootstrap_edge_lcb_5pct']:.6f} | "
            f"{row['pbo']:.3f} | {row['dsr']:.4f} | {row['rc_spa']:.4f} | `{row['hard_gate_result']}` |"
        )

    module.REPORT_MD.write_text(
        "\n".join(
            [
                "# Macro-Stress Panel RC-SPA v1",
                "",
                f"Run id: `{RUN_ID}`.",
                "",
                "## Decision",
                "",
                f"- Gate result: `{decision['gate_result']}`",
                f"- Stable profit score: `{decision['stable_profit_score']:.4f}`",
                f"- Variant rows: `{decision['variant_trade_rows']}`",
                f"- Selected rows: `{decision['selected_trade_rows']}`",
                f"- Branch paths passed: `{decision['branch_paths_passed']}/5`",
                f"- Selected root counts: `{decision['selected_root_trade_counts']}`",
                f"- Downstream consumption: `{decision['downstream_consumption']}`",
                f"- Primary blocker: {decision['primary_blocker']}",
                "",
                "## Boundary",
                "",
                "- The macro-stress CSV is used as a daily price/feature panel only.",
                "- The NIFTY files from the same live scout remain duplicate/blocked source-label material without an owner-approved MainRegimeV2 crosswalk.",
                "- No raw Kaggle files were copied into the repo; this run writes derived RC-SPA evidence only.",
                "",
                "## Selected Branch Summary",
                "",
                *branch_lines,
                "",
                "## Inputs",
                "",
                f"- Macro-stress panel CSV: `{MACRO_CSV}`",
                f"- Base RC-SPA evaluator: `{module.rel(BASE_SCRIPT)}`",
                f"- Board A consumer map: `{payload['accepted_regime_artifact']}`",
                "",
                "## Artifacts",
                "",
                f"- Report JSON: `{module.rel(module.REPORT_JSON)}`",
                f"- Selected rows: `{module.rel(module.SELECTED_ROWS_CSV)}`",
                f"- Variant rows: `{module.rel(module.ALL_ROWS_CSV)}`",
                f"- Branch summary: `{module.rel(module.SUMMARY_CSV)}`",
                f"- Panel summary: `{module.rel(module.PANEL_SUMMARY_CSV)}`",
                f"- Fail-closed downstream summary: `{module.rel(module.FAIL_CLOSED_MD)}`",
                f"- Assertions: `{module.rel(module.ASSERTIONS)}`",
                "",
                "## Next",
                "",
                f"- {decision['next_action']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    module.FAIL_CLOSED_MD.write_text(
        "\n".join(
            [
                "# Macro-Stress Panel ict-engine Fail-Closed Summary v1",
                "",
                f"Run id: `{RUN_ID}`.",
                "",
                f"- Branch RC-SPA gate: `{decision['gate_result']}`",
                f"- Downstream consumption: `{decision['downstream_consumption']}`",
                "- Pre-Bayes / BBN / CatBoost / execution-tree were not started unless every required branch hard gate passed.",
                "- This is a fail-closed readback, not a promoted profitability packet.",
                "",
                f"Primary blocker: {decision['primary_blocker']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    if not MACRO_CSV.exists() or MACRO_CSV.stat().st_size == 0:
        raise RuntimeError(f"missing macro panel: {MACRO_CSV}")
    module = load_base_module()
    patch_module(module)
    rc = module.main()
    rewrite_reports(module)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
