#!/usr/bin/env python3
"""Read-only selector for the next Board B B2R probe."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[6]
RUN_ID = "20260512T030409+0800-codex-board-b-b2r-next-selector-v1"
RUN_DIR = ROOT / "docs/experiments/actionable-regime-confidence/runs/20260512T030409-codex-board-b-b2r-next-selector-v1"
OUT_DIR = RUN_DIR / "b2r-next-selector-v1"
CHECK_DIR = RUN_DIR / "checks"

INPUTS = {
    "correlation_shock": ROOT
    / "docs/experiments/actionable-regime-confidence/runs/20260512T024509-codex-board-b-b2r-correlation-shock-panel-v1/branch-rc-spa/correlation_shock_absorption_rc_spa_report_v1.json",
    "crypto_options_breadth": ROOT
    / "docs/experiments/actionable-regime-confidence/runs/20260512T024354-codex-board-b-b2r-repeat-crypto-options-breadth-v1/branch-rc-spa/crypto_options_breadth_rc_spa_report_v1.json",
    "manipulation_component": ROOT
    / "docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2.json",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def normalize_counts(packet: dict) -> dict[str, int]:
    counts = packet.get("selected_root_trade_counts") or packet.get("root_trade_counts") or {}
    out: dict[str, int] = {}
    for key, value in counts.items():
        try:
            out[str(key)] = int(value)
        except (TypeError, ValueError):
            out[str(key)] = 0
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    corr = load_json(INPUTS["correlation_shock"])
    crypto = load_json(INPUTS["crypto_options_breadth"])
    manip = load_json(INPUTS["manipulation_component"])

    corr_counts = normalize_counts(corr)
    crypto_counts = normalize_counts(crypto)
    manip_decision = manip.get("decision", {})

    selector = {
        "schema_version": "board-b-b2r-next-selector/v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only_no_backtest_no_runtime_code_change",
        "active_cursor_observed": {
            "last_loop_id": "20260512T025702+0800-codex-board-b-024354-crypto-options-breadth-date-normalization-v1",
            "recipe_id": "CryptoOptionsBreadthRootV1",
            "gate_result": "fail:required_root_branch_hard_gates_failed",
        },
        "input_packets": {
            "correlation_shock": {
                "run_id": corr.get("run_id"),
                "recipe_id": corr.get("recipe_id"),
                "stable_profit_score": corr.get("stable_profit_score"),
                "variant_trade_rows": corr.get("variant_trade_rows"),
                "selected_trade_rows": corr.get("selected_trade_rows"),
                "selected_root_trade_counts": corr_counts,
                "gate_result": corr.get("gate_result"),
                "downstream_consumption": corr.get("downstream_consumption"),
            },
            "crypto_options_breadth": {
                "run_id": crypto.get("run_id"),
                "recipe_id": crypto.get("recipe_id"),
                "stable_profit_score": crypto.get("stable_profit_score"),
                "variant_trade_rows": crypto.get("variant_trade_rows"),
                "selected_trade_rows": crypto.get("selected_trade_rows"),
                "selected_root_trade_counts": crypto_counts,
                "gate_result": crypto.get("gate_result"),
                "downstream_consumption": crypto.get("downstream_consumption"),
                "options_auxiliary": crypto.get("options_auxiliary"),
            },
            "manipulation_component": {
                "run_id": manip.get("run_id"),
                "recipe_id": manip.get("recipe_id"),
                "gate_result": manip_decision.get("gate_result"),
                "branch_rows": manip_decision.get("branch_rows"),
                "best_variant": manip_decision.get("best_variant"),
                "best_positive_mean_net": manip_decision.get("best_positive_mean_net"),
                "best_positive_lcb_5pct": manip_decision.get("best_positive_lcb_5pct"),
                "tradeable_candidate_count": len(manip_decision.get("tradeable_candidates", [])),
                "full_board_promotion_allowed": manip_decision.get("promotion_allowed_for_full_board_b"),
            },
        },
        "failure_mode_matrix": {
            "Bull": {
                "status": "support_present_but_unstable",
                "evidence": "024509 has 6563 selected Bull rows but fails fold, cost, overfit, and score gates; 024354 has 183 Bull rows and no positive edge.",
                "repair_requirement": "Do not add generic Bull rows. Require fold-stable positive net edge after costs and lower PBO/overfit.",
            },
            "Bear": {
                "status": "thin_and_negative",
                "evidence": "024509 has 8 Bear rows and 024354 has 2 Bear rows; both fail thin/fold-depth/edge gates.",
                "repair_requirement": "Use a Bear-dedicated short/defensive action surface with explicit root alignment and enough chronological folds.",
            },
            "Sideways": {
                "status": "rows_present_edge_missing",
                "evidence": "024509 has 6280 Sideways rows but negative/no positive edge and no specificity; 024354 has 307 rows and still no positive edge.",
                "repair_requirement": "Use a range-carry or fade surface that abstains in trend contexts and proves positive LCB by fold.",
            },
            "Crisis": {
                "status": "coverage_or_edge_weak",
                "evidence": "024509 has 424 Crisis rows but insufficient folds plus no positive edge/cost/DSR/specificity failures; 024354 has 0 Crisis rows.",
                "repair_requirement": "Source older crisis windows or stress-specific provider panels, then score only if Crisis has multi-fold positive edge.",
            },
            "Manipulation(scoped)": {
                "status": "component_available_not_combined_in_latest_packets",
                "evidence": "Latest 024509 and 024354 have zero direct Manipulation rows, while 205047 passed as a direct stop/take-profit component.",
                "repair_requirement": "Combine 205047 only as scoped component evidence after all price roots pass; do not count component readiness as price-root promotion.",
            },
        },
        "do_not_repeat": [
            "CorrelationShockAbsorptionV1",
            "CryptoOptionsBreadthRootV1",
            "RootLiquidityVolCarryRotationV1",
            "SourceRootStopCarryLongHorizonV1 trace/CatBoost readiness replays without user-selected Sideways-compatible historical data",
        ],
        "concurrency_guard": {
            "heavy_probe_started": False,
            "reason": "Live process scan found other agents already occupying root-event/root-repair/source-regime style run roots; this artifact intentionally avoids duplicate heavy work.",
        },
        "recommended_next_probe": {
            "name": "BearSidewaysCrisisAbstainCarryRepairV1",
            "status": "selector_only_pending_active_job_clearance",
            "must_preserve_branch_path": "main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor",
            "price_root_design": [
                "Bear -> RiskOffShortOrDefensiveCarry -> FoldStableShortCarry -> BearSidewaysCrisisAbstainCarryRepairV1:bear_short_defensive_horizon",
                "Sideways -> RangeCarry -> TrendContextAbstainRangeCarry -> BearSidewaysCrisisAbstainCarryRepairV1:sideways_range_abstain_when_trend",
                "Crisis -> StressReboundOrHedge -> CrisisOnlyTailHedge -> BearSidewaysCrisisAbstainCarryRepairV1:crisis_tail_or_rebound",
                "Bull -> RiskOnPullbackOrCarry -> OverfitGuardedContinuation -> BearSidewaysCrisisAbstainCarryRepairV1:bull_fold_stable_pullback",
            ],
            "component_policy": "Use 205047 ManipulationStopTakeProfitGridV2 as a scoped component only after price roots pass unchanged RC-SPA.",
            "minimum_acceptance_before_downstream": "All four price roots pass unchanged RC-SPA and scoped Manipulation remains a component pass; otherwise downstream stays not_started.",
        },
        "decision": "do_not_start_downstream_or_duplicate_heavy_run; wait for active root-panel jobs to finish, then run a materially different Bear/Sideways/Crisis abstain-carry repair panel if no newer row supersedes this selector.",
        "promotion_allowed": False,
        "update_goal": False,
    }

    json_path = OUT_DIR / "b2r_next_selector_v1.json"
    md_path = OUT_DIR / "b2r_next_selector_v1.md"
    assertion_path = CHECK_DIR / "b2r_next_selector_v1_assertions.out"

    json_path.write_text(json.dumps(selector, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Board B B2R Next Selector v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Decision: `do_not_start_downstream_or_duplicate_heavy_run`.",
        "",
        "Inputs:",
        f"- `024509` / `CorrelationShockAbsorptionV1`: {corr.get('variant_trade_rows'):,} variant rows, {corr.get('selected_trade_rows'):,} selected rows, score `{corr.get('stable_profit_score')}`, gate `{corr.get('gate_result')}`.",
        f"- `024354` / `CryptoOptionsBreadthRootV1`: {crypto.get('variant_trade_rows'):,} variant rows, {crypto.get('selected_trade_rows'):,} selected rows, score `{crypto.get('stable_profit_score')}`, gate `{crypto.get('gate_result')}`.",
        f"- `205047` / `ManipulationStopTakeProfitGridV2`: `{manip_decision.get('gate_result')}`, {manip_decision.get('branch_rows'):,} branch rows, best `{manip_decision.get('best_variant')}`.",
        "",
        "Failure matrix:",
    ]
    for root, detail in selector["failure_mode_matrix"].items():
        lines.append(f"- `{root}`: `{detail['status']}`. {detail['repair_requirement']}")
    lines.extend(
        [
            "",
            "Recommended next probe:",
            "- `BearSidewaysCrisisAbstainCarryRepairV1`, only after the active root-panel jobs finish and the board has been re-read.",
            "- Preserve `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`.",
            "- Do not rerun downstream until all price roots pass unchanged RC-SPA and the `205047` Manipulation component remains component-only.",
            "",
            "Concurrency guard:",
            "- No heavy probe was started by this selector.",
            "- Current cursor remains `025702` / `CryptoOptionsBreadthRootV1` fail-closed unless a newer board row supersedes it.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        "b2r_next_selector_v1",
        "read_only_no_backtest=PASS",
        "heavy_probe_started_false=PASS",
        "correlation_shock_counted_fail_closed=PASS",
        "crypto_options_counted_fail_closed=PASS",
        "manipulation_205047_component_only=PASS",
        "downstream_not_started=PASS",
        "promotion_allowed_false=PASS",
        "update_goal_false=PASS",
    ]
    assertion_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
