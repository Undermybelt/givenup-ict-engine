#!/usr/bin/env python3
"""Run-local Board B repair probe after NQRootAdaptiveEventPanelV1.

This wrapper reuses the previous NQ long-history evaluator but writes a new
artifact tree and prepends repair variants for Bull cost survival, Bear/Sideways
mean reversion, and Crisis support. It does not edit ict-engine runtime code or
the Auto-Quant checkout.
"""

from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path


RUN_ID = "20260512T031912+0800-codex-board-b-nq-cost-crisis-repair-v2"
SCHEMA_VERSION = "board-b-nq-cost-crisis-repair/v2"
RECIPE_ID = "NQRootAdaptiveCostCrisisRepairV2"
SYMBOL = "B2R_NQ_COST_CRISIS_REPAIR_031912"

RUN_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = RUN_ROOT.parent
SOURCE_SCRIPT = (
    RUNS_ROOT
    / "20260512T030356-codex-board-b-b2r-repeat-nq-root-adaptive-v1"
    / "scripts"
    / "nq_root_adaptive_event_panel_v1.py"
)


def load_base_module():
    spec = importlib.util.spec_from_file_location("nq_root_adaptive_base", SOURCE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load base evaluator: {SOURCE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def branch_path(root: str, child: str, leaf: str, variant_id: str) -> str:
    return f"{root} -> {child} -> {leaf} -> {RECIPE_ID}:{variant_id}"


REPAIR_VARIANTS = [
    {
        "root": "Bull",
        "variant_id": "bull_source_root_carry_h72",
        "branch_path": branch_path("Bull", "TrendExpansion", "NQSourceRootCarry", "bull_source_root_carry_h72"),
        "hold": 72,
        "action": "long",
    },
    {
        "root": "Bull",
        "variant_id": "bull_breakout_mid_z_h48",
        "branch_path": branch_path("Bull", "TrendExpansion", "NQMidZBreakout", "bull_breakout_mid_z_h48"),
        "hold": 48,
        "action": "long",
        "ret24_min": 0.007185894723864883,
        "zscore_min": -0.50,
        "zscore_max": 1.50,
        "vol_z_max": 0.11066300966775416,
    },
    {
        "root": "Bear",
        "variant_id": "bear_oversold_high_vix_rebound_h72",
        "branch_path": branch_path("Bear", "BearMarketDrawdown", "NQHighVixOversoldRebound", "bear_oversold_high_vix_rebound_h72"),
        "hold": 72,
        "action": "long",
        "ret24_max": -0.010236344303936813,
        "zscore_max": -1.6494724470978201,
        "source_vix_min": 30.02,
    },
    {
        "root": "Bear",
        "variant_id": "bear_low_z_rebound_h48",
        "branch_path": branch_path("Bear", "BearMarketDrawdown", "NQLowZRebound", "bear_low_z_rebound_h48"),
        "hold": 48,
        "action": "long",
        "zscore_max": -1.6494724470978201,
        "vol_z_max": 0.19067452437217808,
    },
    {
        "root": "Bear",
        "variant_id": "bear_oversold_rebound_h48",
        "branch_path": branch_path("Bear", "BearMarketDrawdown", "NQOversoldRebound", "bear_oversold_rebound_h48"),
        "hold": 48,
        "action": "long",
        "ret24_max": -0.010236344303936813,
        "zscore_max": -1.6494724470978201,
    },
    {
        "root": "Sideways",
        "variant_id": "sideways_deep_low_z_low_conf_rebound_h48",
        "branch_path": branch_path("Sideways", "RangeConsolidation", "NQDeepLowZLowConfidenceRebound", "sideways_deep_low_z_low_conf_rebound_h48"),
        "hold": 48,
        "action": "long",
        "zscore_max": -1.8,
        "vol_z_max": 0.21041480363891474,
        "source_regime_confidence_max": 0.375,
    },
    {
        "root": "Sideways",
        "variant_id": "sideways_low_z_rebound_h36",
        "branch_path": branch_path("Sideways", "RangeConsolidation", "NQLowZRebound", "sideways_low_z_rebound_h36"),
        "hold": 36,
        "action": "long",
        "zscore_max": -1.390666601048322,
        "vol_z_max": 0.21041480363891474,
    },
    {
        "root": "Sideways",
        "variant_id": "sideways_low_z_rebound_h48",
        "branch_path": branch_path("Sideways", "RangeConsolidation", "NQLowZRebound", "sideways_low_z_rebound_h48"),
        "hold": 48,
        "action": "long",
        "zscore_max": -1.390666601048322,
        "vol_z_max": 0.21041480363891474,
    },
    {
        "root": "Crisis",
        "variant_id": "crisis_source_root_rebound_h72",
        "branch_path": branch_path("Crisis", "ExtremeStress", "NQSourceRootRebound", "crisis_source_root_rebound_h72"),
        "hold": 72,
        "action": "long",
    },
    {
        "root": "Crisis",
        "variant_id": "crisis_flush_rebound_h72",
        "branch_path": branch_path("Crisis", "ExtremeStress", "NQFlushRebound", "crisis_flush_rebound_h72"),
        "hold": 72,
        "action": "long",
        "ret24_max": -0.00634689932564929,
    },
]


def variant_mask_with_source_fields(original):
    def wrapped(df, variant):
        mask = original(df, variant)
        if "source_vix_min" in variant:
            mask &= df["source_vix"] >= float(variant["source_vix_min"])
        if "source_vix_max" in variant:
            mask &= df["source_vix"] <= float(variant["source_vix_max"])
        if "source_regime_confidence_min" in variant:
            mask &= df["source_regime_confidence"] >= float(variant["source_regime_confidence_min"])
        if "source_regime_confidence_max" in variant:
            mask &= df["source_regime_confidence"] <= float(variant["source_regime_confidence_max"])
        return mask

    return wrapped


def main() -> int:
    base = load_base_module()
    base.RUN_ID = RUN_ID
    base.SCHEMA_VERSION = SCHEMA_VERSION
    base.RECIPE_ID = RECIPE_ID
    base.SYMBOL = SYMBOL

    previous_variants = []
    for variant in deepcopy(base.VARIANTS):
        variant["branch_path"] = variant["branch_path"].replace("NQRootAdaptiveEventPanelV1", RECIPE_ID)
        previous_variants.append(variant)
    base.VARIANTS = [*REPAIR_VARIANTS, *previous_variants]
    base.variant_mask = variant_mask_with_source_fields(base.variant_mask)

    base.RUN_ROOT = RUN_ROOT
    base.OUT_DIR = RUN_ROOT / "nq-cost-crisis-repair-v2"
    base.CHECK_DIR = RUN_ROOT / "checks"
    base.COMMAND_DIR = RUN_ROOT / "command-output"
    base.STATE_SYMBOL_DIR = RUN_ROOT / "state_nq_cost_crisis_repair_v2" / SYMBOL
    base.REPORT_JSON = base.OUT_DIR / "nq_cost_crisis_repair_rc_spa_v2.json"
    base.REPORT_MD = base.OUT_DIR / "nq_cost_crisis_repair_rc_spa_v2.md"
    base.VARIANT_ROWS_CSV = base.OUT_DIR / "nq_cost_crisis_repair_variant_rows_v2.csv"
    base.SELECTED_ROWS_CSV = base.OUT_DIR / "nq_cost_crisis_repair_selected_rows_v2.csv"
    base.BRANCH_SUMMARY_CSV = base.OUT_DIR / "nq_cost_crisis_repair_branch_summary_v2.csv"
    base.INPUTS_JSON = base.OUT_DIR / "nq_cost_crisis_repair_inputs_v2.json"
    base.REAL_TRADES = base.OUT_DIR / "nq_cost_crisis_repair_real_trades_v2.jsonl"
    base.STRATEGY_LIBRARY = base.OUT_DIR / "strategy_library_nq_cost_crisis_repair_v2.json"
    base.ASSERTIONS = base.CHECK_DIR / "nq_cost_crisis_repair_v2_assertions.out"

    return int(base.main())


if __name__ == "__main__":
    raise SystemExit(main())
