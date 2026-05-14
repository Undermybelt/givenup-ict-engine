#!/usr/bin/env python3
"""Board B cross-asset root-rotation RC-SPA readback.

Run-local additive experiment. It reuses the existing Board B RC-SPA evaluator
and changes only the recipe/panel/signal definitions for a non-Tomac/non-VRP
cross-asset rotation family over local Auto-Quant feathers.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260511T204238+0800-codex-board-b-cross-asset-root-rotation-v1"
SCHEMA_VERSION = "board-b-cross-asset-root-rotation/v1"
RECIPE_ID = "CrossAssetRootRotationV1"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
DATA_DIR = Path("/Users/thrill3r/Auto-Quant/user_data/data")
BASE_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T193803-codex-board-b-root-transition-triad-clean-v1/scripts/"
    "board_b_root_transition_triad_clean_v1.py"
)


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("board_b_root_transition_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base evaluator: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_defensive_market(market: str) -> bool:
    return market.startswith("GLD")


def is_crypto_market(market: str) -> bool:
    return "USDT" in market


def is_small_cap_market(market: str) -> bool:
    return market.startswith("IWM")


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
    ema20_slope = float(row["ema20_slope"])
    atr_pct = float(row["atr_pct"])
    vix = float(row["source_ticker_vix"])
    z_threshold = float(variant["z"])
    low_slope = abs(ema20_slope) < max(0.003, atr_pct * 0.40)
    defensive = is_defensive_market(market)
    crypto = is_crypto_market(market)
    small_cap = is_small_cap_market(market)

    if root == "Bull":
        if mode == "risk_on_momentum":
            return 1 if not defensive and trend > 0 and close > ema_value else 0
        if mode == "pullback_continuation":
            return 1 if not defensive and close > ema50 and z_value < -z_threshold and ret1 > 0 else 0
        if mode == "defensive_rotation":
            return 0 if defensive else (1 if trend > 0 and close > ema_value else 0)
        return 0

    if root == "Bear":
        if mode == "risk_off_short":
            return -1 if not defensive and trend < 0 and close < ema_value else 0
        if mode == "defensive_rotation":
            return 1 if defensive and trend > 0 and close > ema_value else 0
        if mode == "bear_relief_reversal":
            oversold = z_value <= -z_threshold or ret3 < -max(0.006, atr_pct * 1.25)
            return 1 if oversold and ret1 > 0 and close > float(row["low20_prev"]) and vix < 45 else 0
        if mode == "crypto_beta_short":
            return -1 if crypto and trend < -max(0.003, atr_pct * 0.45) and close < ema_value else 0
        return 0

    if root == "Sideways":
        if mode == "range_reversion":
            if low_slope and z_value >= z_threshold:
                return -1
            if low_slope and z_value <= -z_threshold:
                return 1
        if mode == "small_cap_breakout":
            if small_cap and low_slope and close > float(row["high20_prev"]) and ret1 > 0:
                return 1
            if small_cap and low_slope and close < float(row["low20_prev"]) and ret1 < 0:
                return -1
        if mode == "defensive_rotation":
            return 1 if defensive and trend > 0 and close > ema_value else 0
        return 0

    if root == "Crisis":
        if mode == "crisis_tail_short":
            return -1 if not defensive and (trend < 0 or ret3 < -max(0.008, atr_pct * 1.5)) and close < ema_value else 0
        if mode == "defensive_rotation":
            return 1 if defensive and trend > 0 and close > ema_value else 0
        if mode == "panic_reversal":
            panic = z_value <= -max(1.4, z_threshold) or ret3 <= -max(0.012, atr_pct * 2.0)
            return 1 if panic and ret1 > 0 and vix < 55 else 0
        return 0

    return 0


def branch_path(module: Any, root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> CrossAssetRiskOn -> MomentumOrPullback -> {RECIPE_ID}:{variant_id}"
    if root == "Bear":
        return f"{root} -> CrossAssetRiskOff -> ShortOrDefensiveRotation -> {RECIPE_ID}:{variant_id}"
    if root == "Sideways":
        return f"{root} -> CrossAssetRange -> ReversionOrBreakout -> {RECIPE_ID}:{variant_id}"
    if root == "Crisis":
        return f"{root} -> CrossAssetStress -> TailShortOrDefense -> {RECIPE_ID}:{variant_id}"
    return "Manipulation(scoped) -> DirectEventOverlayMissing -> no_direct_event_rows -> suppress_or_abstain"


def branch_fields(root: str) -> dict[str, str]:
    if root == "Bull":
        return {
            "sub_regime_tags": "CrossAssetRiskOn",
            "sub_sub_regime_or_profit_factor": "MomentumOrPullback",
            "profit_factor_family": "cross_asset_root_rotation",
            "allowed_action": "long_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bull_cross_asset_branch_rc_spa_fails",
        }
    if root == "Bear":
        return {
            "sub_regime_tags": "CrossAssetRiskOff",
            "sub_sub_regime_or_profit_factor": "ShortOrDefensiveRotation",
            "profit_factor_family": "cross_asset_root_rotation",
            "allowed_action": "short_or_defensive_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bear_cross_asset_branch_rc_spa_fails",
        }
    if root == "Sideways":
        return {
            "sub_regime_tags": "CrossAssetRange",
            "sub_sub_regime_or_profit_factor": "ReversionOrBreakout",
            "profit_factor_family": "cross_asset_root_rotation",
            "allowed_action": "long_short_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_sideways_cross_asset_branch_rc_spa_fails",
        }
    if root == "Crisis":
        return {
            "sub_regime_tags": "CrossAssetStress",
            "sub_sub_regime_or_profit_factor": "TailShortOrDefense",
            "profit_factor_family": "cross_asset_root_rotation",
            "allowed_action": "short_or_defensive_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "tail_guard_blocks_cross_asset_branch_if_rc_spa_fails",
        }
    return {
        "sub_regime_tags": "DirectEventOverlayMissing",
        "sub_sub_regime_or_profit_factor": "no_direct_event_rows",
        "profit_factor_family": "direct_manipulation_overlay",
        "allowed_action": "suppress_or_abstain",
        "suppression_rule": "no_direct_manipulation_profit_rows",
    }


def patch_module(module: Any) -> None:
    module.RUN_ID = RUN_ID
    module.SCHEMA_VERSION = SCHEMA_VERSION
    module.RECIPE_ID = RECIPE_ID
    module.RUN_ROOT = RUN_ROOT
    module.OUT_DIR = RUN_ROOT / "branch-rc-spa"
    module.CHECK_DIR = RUN_ROOT / "checks"
    module.FAIL_CLOSED_DIR = RUN_ROOT / "ict-engine-fail-closed"
    module.ALL_ROWS_CSV = module.OUT_DIR / "cross_asset_root_rotation_variant_rows_v1.csv"
    module.SELECTED_ROWS_CSV = module.OUT_DIR / "cross_asset_root_rotation_selected_rows_v1.csv"
    module.SUMMARY_CSV = module.OUT_DIR / "cross_asset_root_rotation_branch_summary_v1.csv"
    module.PANEL_SUMMARY_CSV = module.OUT_DIR / "cross_asset_root_rotation_panel_summary_v1.csv"
    module.REPORT_JSON = module.OUT_DIR / "cross_asset_root_rotation_rc_spa_report_v1.json"
    module.REPORT_MD = module.OUT_DIR / "cross_asset_root_rotation_rc_spa_report_v1.md"
    module.ASSERTIONS = module.CHECK_DIR / "cross_asset_root_rotation_v1_assertions.out"
    module.FAIL_CLOSED_MD = module.FAIL_CLOSED_DIR / "cross_asset_root_rotation_fail_closed_summary_v1.md"
    module.PANELS = [
        ("NQ/USD", "4h", DATA_DIR / "NQ_USD-4h.feather"),
        ("QQQ/USD", "1h", DATA_DIR / "QQQ_USD-1h.feather"),
        ("QQQ/USD", "4h", DATA_DIR / "QQQ_USD-4h.feather"),
        ("SPY/USD", "1h", DATA_DIR / "SPY_USD-1h.feather"),
        ("IWM/USD", "1h", DATA_DIR / "IWM_USD-1h.feather"),
        ("DIA/USD", "1h", DATA_DIR / "DIA_USD-1h.feather"),
        ("GLD/USD", "1h", DATA_DIR / "GLD_USD-1h.feather"),
        ("GLD/USD", "4h", DATA_DIR / "GLD_USD-4h.feather"),
        ("BTC/USDT", "4h", DATA_DIR / "BTC_USDT-4h.feather"),
        ("ETH/USDT", "4h", DATA_DIR / "ETH_USDT-4h.feather"),
        ("SOL/USDT", "4h", DATA_DIR / "SOL_USDT-4h.feather"),
        ("AVAX/USDT", "4h", DATA_DIR / "AVAX_USDT-4h.feather"),
    ]
    module.VARIANTS = [
        {"variant_id": "risk_on_momentum_fast", "mode": "risk_on_momentum", "lookback": 5, "ema": 20, "z": 0.9, "hold": {"15m": 16, "1h": 8, "4h": 5, "1d": 5}},
        {"variant_id": "risk_off_short", "mode": "risk_off_short", "lookback": 10, "ema": 20, "z": 1.0, "hold": {"15m": 24, "1h": 12, "4h": 6, "1d": 6}},
        {"variant_id": "crypto_beta_short", "mode": "crypto_beta_short", "lookback": 10, "ema": 20, "z": 1.0, "hold": {"15m": 20, "1h": 12, "4h": 6, "1d": 6}},
        {"variant_id": "range_reversion_dense", "mode": "range_reversion", "lookback": 5, "ema": 20, "z": 0.85, "hold": {"15m": 16, "1h": 6, "4h": 4, "1d": 4}},
        {"variant_id": "defensive_rotation", "mode": "defensive_rotation", "lookback": 10, "ema": 20, "z": 1.0, "hold": {"15m": 24, "1h": 10, "4h": 6, "1d": 8}},
        {"variant_id": "crisis_tail_short", "mode": "crisis_tail_short", "lookback": 5, "ema": 20, "z": 1.0, "hold": {"15m": 28, "1h": 14, "4h": 7, "1d": 6}},
        {"variant_id": "panic_reversal", "mode": "panic_reversal", "lookback": 3, "ema": 20, "z": 1.2, "hold": {"15m": 16, "1h": 8, "4h": 4, "1d": 4}},
    ]
    module.signal_direction = signal_direction
    module.branch_fields = branch_fields
    module.branch_path = lambda root, variant_id: branch_path(module, root, variant_id)


def rewrite_reports(module: Any) -> None:
    payload = json.loads(module.REPORT_JSON.read_text(encoding="utf-8"))
    decision = payload["decision"]
    if decision["gate_result"] == "pass":
        decision["next_action"] = "B5: run Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree branch consumption."
    else:
        decision["next_action"] = (
            "B2R-repeat: cross-asset root rotation did not clear required branch hard gates; "
            "switch family/panel or source executable Manipulation rows before downstream promotion."
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
                "# Cross-Asset Root Rotation RC-SPA v1",
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
                "## Selected Branch Summary",
                "",
                *branch_lines,
                "",
                "## Inputs",
                "",
                f"- Local Auto-Quant feathers: `{DATA_DIR}`",
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
                "# Cross-Asset Root Rotation ict-engine Fail-Closed Summary v1",
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
    module = load_base_module()
    patch_module(module)
    rc = module.main()
    rewrite_reports(module)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
