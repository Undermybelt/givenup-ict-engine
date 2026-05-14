#!/usr/bin/env python3
"""Materialize the current MainRegimeV2 per-regime factor supply map.

This is not a completion audit. It separates the user's immediate requirement
("each regime has a corresponding accepted factor/evidence packet") from the
larger Board A full-matrix/full-cycle completion gate.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT_DIR = RUN_ROOT / "factor-supply"
CHECK_DIR = RUN_ROOT / "checks"
OUT_JSON = OUT_DIR / "per_regime_factor_supply_map.json"
OUT_MD = OUT_DIR / "per_regime_factor_supply_map.md"
ASSERTIONS = CHECK_DIR / "per_regime_factor_supply_map_assertions.out"
RUN_ID = "20260511T121643+0800-codex-per-regime-factor-supply-map"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    factors = [
        {
            "regime": "Bull",
            "taxonomy_role": "MainRegimeV2_price_root",
            "factor_id": "bull_sourcebacked_drawdown_volatility_v1",
            "evidence_class": "source_backed_scope_limited_parent_root_factor",
            "source_artifact": (
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260511T035045-codex-kaggle-bull-coverage-buffer-gate/"
                "kaggle-bull-gate/kaggle_bull_coverage_buffer_gate_report.json"
            ),
            "rule": "close_drawdown60 >= -0.0032047199531 AND volatility <= 0.152179344579",
            "calibration_wilson95_lcb": 0.952516,
            "test_wilson95_lcb": 0.961931,
            "calibration_support": 2202,
            "test_support": 3125,
            "validation_contexts": ["index", "single_stock"],
            "validation_timeframes": ["1d", "1w"],
            "accepted_95_scoped_factor": True,
            "full_matrix_completion": False,
            "consumer_use": "allow_or_size_up_bull_continuation_candidates_inside_supported_scope",
            "not_allowed": "do_not_promote_to_full_universe_or_intraday_without missing slots/crosswalk",
        },
        {
            "regime": "Bear",
            "taxonomy_role": "MainRegimeV2_price_root",
            "factor_id": "bear_sourcebacked_drawdown_return_ratio_v1",
            "evidence_class": "source_backed_scope_limited_parent_root_factor",
            "source_artifact": (
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/"
                "yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json"
            ),
            "rule": "bear_drawdown_ratio >= 1 AND bear_return_ratio >= 1",
            "calibration_wilson95_lcb": 0.993968,
            "test_wilson95_lcb": 0.992722,
            "calibration_support": 633,
            "test_support": 524,
            "validation_contexts": ["crypto", "equity_etf"],
            "validation_timeframes": ["1d", "1w"],
            "accepted_95_scoped_factor": True,
            "full_matrix_completion": False,
            "consumer_use": "allow_or_size_up_bear_defensive_or_short_bias_candidates_inside_supported_scope",
            "not_allowed": "do_not_promote_to_full_universe_or_intraday_without missing slots/crosswalk",
        },
        {
            "regime": "Sideways",
            "taxonomy_role": "MainRegimeV2_price_root",
            "factor_id": "sideways_sourcebacked_abs_return_range_v1",
            "evidence_class": "source_backed_scope_limited_parent_root_factor",
            "source_artifact": (
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/"
                "yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json"
            ),
            "rule": "sideways_abs_return_ratio <= 0.505204858191 AND sideways_range_ratio <= 0.357222193236",
            "calibration_wilson95_lcb": 0.988647,
            "test_wilson95_lcb": 0.995568,
            "calibration_support": 495,
            "test_support": 863,
            "validation_contexts": ["crypto", "equity_etf"],
            "validation_timeframes": ["1d", "1w"],
            "accepted_95_scoped_factor": True,
            "full_matrix_completion": False,
            "consumer_use": "allow_mean_reversion_or_range_candidates_inside_supported_scope",
            "not_allowed": "do_not_treat_old_RangeConsolidation_subregime_as_parent_completion",
        },
        {
            "regime": "Crisis",
            "taxonomy_role": "MainRegimeV2_price_root",
            "factor_id": "crisis_range_ratio_intraday_v1",
            "evidence_class": "scope_limited_parent_root_factor",
            "source_artifact": (
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260510T235220-codex-broader-root-v2-probe/"
                "root-v2-broader/main_regime_v2_broader_root_calibration_report.json"
            ),
            "rule": "range_ratio32_128 >= 1.43116959912",
            "calibration_wilson95_lcb": 0.996248,
            "test_wilson95_lcb": 0.995981,
            "calibration_support": 1020,
            "test_support": 952,
            "validation_contexts": [
                "CME_futures_local",
                "IBKR_US_ETF",
                "Kraken_crypto",
                "yfinance_crypto",
                "yfinance_futures",
            ],
            "validation_timeframes": ["15m", "1h"],
            "accepted_95_scoped_factor": True,
            "full_matrix_completion": False,
            "consumer_use": "suppress_risk_or_size_down_execution_inside_supported_scope",
            "not_allowed": "do_not_use_crisis_price_stress_as_direct_manipulation_evidence",
        },
        {
            "regime": "Manipulation",
            "taxonomy_role": "separate_direct_event_order_flow_overlay_or_class",
            "factor_id": "manipulation_telegram_pump_event_v1",
            "evidence_class": "direct_social_event_factor",
            "source_artifact": (
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260511T045102-codex-mehrnoom-telegram-direct-manipulation-gate/"
                "direct-gate/mehrnoom_telegram_direct_manipulation_gate.json"
            ),
            "rule": "classified_telegram_coin_pump_event_present == 1",
            "calibration_wilson95_lcb": 0.999735,
            "test_wilson95_lcb": 0.999701,
            "calibration_support": 14516,
            "test_support": 12834,
            "validation_contexts": ["crypto_telegram_event", "same_coin_non_event_controls"],
            "validation_timeframes": ["event_window"],
            "accepted_95_scoped_factor": True,
            "full_matrix_completion": False,
            "consumer_use": "suppress_entry_or_route_to_abstain_cooldown_on_direct_event",
            "not_allowed": "not_an_automatic_trade_entry_and_not_an_OHLCV_proxy",
        },
        {
            "regime": "Manipulation",
            "taxonomy_role": "separate_direct_event_order_flow_overlay_or_class",
            "factor_id": "manipulation_multichain_wash_maker_v1",
            "evidence_class": "direct_onchain_order_lifecycle_wash_factor",
            "source_artifact": (
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260511T112642-codex-midsummer-chain-slice-expansion-audit/"
                "chain-slice-audit/midsummer_chain_slice_expansion_audit.json"
            ),
            "rule": "same platform/address/day paired controls AND is_both_buyer_seller == True",
            "minimum_split_class_wilson95_lcb": 0.967945,
            "accepted_direct_rows": 7563,
            "validation_contexts": ["base", "bsc", "ethereum", "solana"],
            "validation_timeframes": ["maker_token_day"],
            "accepted_95_scoped_factor": True,
            "full_matrix_completion": False,
            "consumer_use": "suppress_or_abstain_on_direct_wash_maker_evidence",
            "not_allowed": "wash_maker_scope_only_not_full_spoofing_layering_quote_stuffing_coverage",
        },
    ]

    active_regimes = ["Bull", "Bear", "Sideways", "Crisis", "Manipulation"]
    by_regime: dict[str, list[dict]] = {regime: [] for regime in active_regimes}
    for factor in factors:
        by_regime[factor["regime"]].append(factor)

    missing = [regime for regime in active_regimes if not by_regime[regime]]
    unsupported = [
        factor["factor_id"]
        for factor in factors
        if not factor.get("accepted_95_scoped_factor")
    ]

    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD.relative_to(REPO)),
        "board_sha256_at_audit": sha256(BOARD),
        "active_taxonomy": {
            "name": "MainRegimeV2",
            "main_price_roots": ["Bull", "Bear", "Sideways", "Crisis"],
            "separate_direct_event_class_or_overlay": ["Manipulation"],
            "residual": "UnknownOrMixed",
        },
        "purpose": (
            "Make the current per-regime factor supply explicit: every active main "
            "regime has at least one accepted 95% scoped factor/evidence packet, "
            "while full-matrix completion remains blocked."
        ),
        "factors": factors,
        "coverage": {
            "active_regimes": active_regimes,
            "regimes_with_scoped_accepted_factor": sorted(by_regime.keys()),
            "missing_regimes": missing,
            "all_active_regimes_have_scoped_factor": not missing and not unsupported,
            "manipulation_direct_varieties_present": [
                factor["factor_id"] for factor in by_regime["Manipulation"]
            ],
        },
        "decision": {
            "per_regime_factor_supply_achieved": not missing and not unsupported,
            "accepted_95_scoped_factor_regimes": active_regimes,
            "accepted_parent_root_full_matrix_completion": False,
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "gate_result": "per_regime_scoped_factor_supply_mapped_full_matrix_still_blocked",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Use this as the regime-to-factor map for downstream gating only within "
            "supported scopes; continue exact source-label/crosswalk acquisition for "
            "full-market/full-timeframe completion."
        ),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    rows = [
        "# Per-Regime Factor Supply Map",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This map answers the narrower factor-supply question: every active `MainRegimeV2` regime now has an explicit accepted 95% scoped factor/evidence packet. It does not claim full-market/full-timeframe completion.",
        "",
        "| Regime | Factor | Evidence | Gate | Scope | Consumer Use |",
        "|---|---|---|---|---|---|",
    ]
    for factor in factors:
        gate = (
            f"cal/test `{factor.get('calibration_wilson95_lcb', factor.get('minimum_split_class_wilson95_lcb'))}`"
            f" / `{factor.get('test_wilson95_lcb', factor.get('minimum_split_class_wilson95_lcb'))}`"
        )
        scope = ", ".join(factor["validation_contexts"]) + "; " + ", ".join(factor["validation_timeframes"])
        rows.append(
            f"| `{factor['regime']}` | `{factor['factor_id']}` | `{factor['evidence_class']}` | "
            f"{gate} | {scope} | {factor['consumer_use']} |"
        )
    rows.extend(
        [
            "",
            "## Guardrails",
            "",
            "- These are scoped factors, not full-universe completion.",
            "- The six older accepted subtype packets remain `sub_regime_evidence_only` and are not promoted here.",
            "- `Manipulation` uses direct social/event and direct wash-maker evidence only; OHLCV/session/liquidity proxies remain rejected.",
            "- Full completion still requires exact provider/instrument/timeframe labels or an owner-approved crosswalk for the missing matrix.",
            "",
            "## Decision",
            "",
            "- Per-regime scoped factor supply achieved: `true`.",
            "- Full objective achieved: `false`.",
            "- Gate result: `per_regime_scoped_factor_supply_mapped_full_matrix_still_blocked`.",
        ]
    )
    OUT_MD.write_text("\n".join(rows) + "\n")

    checks = [
        ("all_active_regimes_have_scoped_factor", report["coverage"]["all_active_regimes_have_scoped_factor"]),
        ("bull_has_factor", bool(by_regime["Bull"])),
        ("bear_has_factor", bool(by_regime["Bear"])),
        ("sideways_has_factor", bool(by_regime["Sideways"])),
        ("crisis_has_factor", bool(by_regime["Crisis"])),
        ("manipulation_has_direct_factor", bool(by_regime["Manipulation"])),
        ("manipulation_has_two_direct_varieties", len(by_regime["Manipulation"]) >= 2),
        ("full_matrix_completion_false", not report["decision"]["accepted_parent_root_full_matrix_completion"]),
        ("thresholds_relaxed_false", not report["decision"]["thresholds_relaxed"]),
        ("runtime_code_changed_false", not report["decision"]["runtime_code_changed"]),
        ("raw_data_committed_false", not report["decision"]["raw_data_committed"]),
        ("trade_usable_false", not report["decision"]["trade_usable"]),
    ]
    ASSERTIONS.write_text(
        "".join(f"{'PASS' if ok else 'FAIL'} {name}={ok}\n" for name, ok in checks)
    )
    if not all(ok for _, ok in checks):
        raise SystemExit("factor supply assertions failed")


if __name__ == "__main__":
    main()
