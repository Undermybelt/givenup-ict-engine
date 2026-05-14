#!/usr/bin/env python3
"""Audit current Board A completion after the positive regime factor index."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T141625+0800-current-goal-completion-audit-v12-after-positive-index"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T141625-current-goal-completion-audit-v12-after-positive-index"
)
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
OUT_JSON = RUN_ROOT / "completion-audit/current_goal_completion_audit_v12_after_positive_index.json"
OUT_MD = RUN_ROOT / "completion-audit/current_goal_completion_audit_v12_after_positive_index.md"
OUT_ASSERT = RUN_ROOT / "checks/current_goal_completion_audit_v12_after_positive_index_assertions.out"

EVIDENCE = {
    "positive_index": "docs/experiments/actionable-regime-confidence/runs/20260511T140042-codex-positive-regime-factor-index-v1/positive-factor-index/positive_regime_factor_index_v1.json",
    "positive_index_assertions": "docs/experiments/actionable-regime-confidence/runs/20260511T140042-codex-positive-regime-factor-index-v1/checks/positive_regime_factor_index_v1_assertions.out",
    "daily_parent_roots": "docs/experiments/actionable-regime-confidence/runs/20260511T125122-codex-stock-market-regimes-parent-root-abstain/parent-root-abstain/stock_market_regimes_parent_root_abstain.json",
    "weekly_monthly_axiswise": "docs/experiments/actionable-regime-confidence/runs/20260511T131922-codex-source-consensus-axiswise-timeframe-gate-v1/source-consensus-axiswise/source_consensus_axiswise_timeframe_gate_v1.json",
    "exact_intraday_attachment": "docs/experiments/actionable-regime-confidence/runs/20260511T134756-codex-daily-to-intraday-source-attachment-v1/daily-intraday-attachment/daily_to_intraday_source_attachment_v1.json",
    "strict_etf_tracking_crosswalk": "docs/experiments/actionable-regime-confidence/runs/20260511T135908-codex-crosswalk-tracking-source-attachment-v1/crosswalk-attachment/crosswalk_tracking_source_attachment_v1.json",
    "es_nq_crosswalk": "docs/experiments/actionable-regime-confidence/runs/20260511T135932-codex-es-nq-source-crosswalk-calibration-v1/crosswalk-calibration/es_nq_source_crosswalk_calibration_v1.json",
    "post_axiswise_request": "docs/experiments/actionable-regime-confidence/runs/20260511T133453-codex-post-axiswise-acquisition-request-v12/acquisition-request/post_axiswise_acquisition_request_v12.json",
    "direct_manipulation_matrix": "docs/experiments/actionable-regime-confidence/runs/20260511T131311-codex-direct-manipulation-variety-matrix-v1/direct-manipulation/direct_manipulation_variety_matrix_v1.json",
    "local_row_export_check": "docs/experiments/actionable-regime-confidence/runs/20260511T134038-codex-local-row-export-acquisition-check-v1/acquisition-check/local_row_export_acquisition_check_v1.json",
}


def file_exists(path: str) -> bool:
    return Path(path).exists()


def main() -> int:
    board_sha = __import__("hashlib").sha256(BOARD.read_bytes()).hexdigest()
    missing_evidence = [name for name, path in EVIDENCE.items() if not file_exists(path)]

    checklist = [
        {
            "requirement": "Every active MainRegimeV2 price root reaches 95 confidence in a scoped source-backed gate.",
            "evidence": ["daily_parent_roots", "positive_index"],
            "status": "pass_scoped",
            "finding": "Daily parent-root gates cover Bull, Bear, Sideways, Crisis at 95; positive index records per-root supply present.",
        },
        {
            "requirement": "Other timeframes survive validation.",
            "evidence": ["weekly_monthly_axiswise", "exact_intraday_attachment", "strict_etf_tracking_crosswalk", "es_nq_crosswalk"],
            "status": "partial",
            "finding": "Same-source 1w/1mo cells pass 8/8; intraday parent-day contexts are partial: exact 36/48, ETF tracking 36/168, ES/NQ scoped 2/16.",
        },
        {
            "requirement": "Other markets/species/full-universe coverage is complete.",
            "evidence": ["post_axiswise_request", "positive_index"],
            "status": "fail",
            "finding": "Post-axiswise request still has unsupported/no-source and full-species rows; positive index explicitly says full goal remains blocked.",
        },
        {
            "requirement": "Full-cycle validation covers crisis/support-sparse states.",
            "evidence": ["exact_intraday_attachment", "strict_etf_tracking_crosswalk", "es_nq_crosswalk", "positive_index"],
            "status": "fail",
            "finding": "Crisis intraday/crosswalk support is below the Wilson95 support floor; positive index records that repeating the same lane cannot pass without new labels.",
        },
        {
            "requirement": "Direct Manipulation is complete as a direct-event/order-flow/order-lifecycle/social/on-chain class.",
            "evidence": ["direct_manipulation_matrix", "local_row_export_check", "positive_index"],
            "status": "partial",
            "finding": "Scoped direct varieties exist, but spoofing/layering matched negatives, quote stuffing, pinging, bear raid, and painting-the-tape rows remain open.",
        },
        {
            "requirement": "No proxy labels are accepted as completion evidence.",
            "evidence": ["positive_index", "post_axiswise_request"],
            "status": "pass",
            "finding": "Current board and positive index preserve no-provider-bar/no-OHLCV/no-HMM/no-generated-label guardrails.",
        },
        {
            "requirement": "Completion claim and update_goal are allowed only if every requirement above passes.",
            "evidence": ["positive_index"],
            "status": "fail",
            "finding": "Multiple checklist items are partial/fail, so update_goal must remain false.",
        },
    ]

    goal_achieved = all(item["status"] == "pass" for item in checklist)
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD),
        "board_sha256_at_run": board_sha,
        "objective_restated": (
            "Every active MainRegimeV2 regime must reach 95% confidence and survive validation across other "
            "markets, other timeframes, full-cycle/full-species contexts; direct Manipulation must be backed by "
            "direct event/order-flow/order-lifecycle/social/on-chain rows with negative controls."
        ),
        "evidence": EVIDENCE,
        "missing_evidence_files": missing_evidence,
        "checklist": checklist,
        "decision": {
            "goal_achieved": goal_achieved,
            "call_update_goal": False,
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "gate_result": "completion_audit_v12_positive_supply_present_full_goal_still_blocked",
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Stop repeating provider-bar/OHLCV/HMM/generated-label scans. Completion now requires new independent "
            "source-label panels for unresolved market/timeframe/species cells or direct positive/negative Manipulation row exports."
        ),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_ASSERT.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Current Goal Completion Audit v12 After Positive Index",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Objective",
        "",
        result["objective_restated"],
        "",
        "## Decision",
        "",
        "- Goal achieved: `false`.",
        "- `update_goal`: `false`.",
        "- Accepted full objective gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.",
        "- Gate result: `completion_audit_v12_positive_supply_present_full_goal_still_blocked`.",
        "- Runtime code changed: `false`.",
        "- Thresholds relaxed: `false`.",
        "- Raw data committed: `false`.",
        "- Trade usable: `false`.",
        "",
        "## Checklist",
        "",
        "| Requirement | Status | Finding |",
        "|---|---|---|",
    ]
    for item in checklist:
        lines.append(f"| {item['requirement']} | `{item['status']}` | {item['finding']} |")
    lines.extend(
        [
            "",
            "## Missing Work",
            "",
            "- New independent source-label panels for unresolved intraday/full-species/non-same-source cells.",
            "- Broader crisis-aware source-label support; current exact/crosswalk crisis support cannot pass Wilson95.",
            "- Direct Manipulation positive and matched-negative row exports for remaining varieties.",
            "",
            "## Next",
            "",
            result["next_action"],
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={board_sha}",
        f"missing_evidence_files={len(missing_evidence)}",
        "goal_achieved=false",
        "call_update_goal=false",
        "accepted_full_objective_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS" if not missing_evidence else "assertion_status=FAIL_MISSING_EVIDENCE",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0 if not missing_evidence else 1


if __name__ == "__main__":
    raise SystemExit(main())
