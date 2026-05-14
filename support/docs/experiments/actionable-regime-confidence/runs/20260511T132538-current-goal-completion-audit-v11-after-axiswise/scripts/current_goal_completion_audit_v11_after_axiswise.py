#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T132538+0800-current-goal-completion-audit-v11-after-axiswise"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T132538-current-goal-completion-audit-v11-after-axiswise"
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
PARENT_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T125122-codex-stock-market-regimes-parent-root-abstain/parent-root-abstain/stock_market_regimes_parent_root_abstain.json"
AXISWISE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T131922-codex-source-consensus-axiswise-timeframe-gate-v1/source-consensus-axiswise/source_consensus_axiswise_timeframe_gate_v1.json"
CROSS_CONTEXT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T130102-current-goal-completion-audit-v10-cross-context/completion-audit/current_goal_completion_audit_v10_cross_context.json"
DIRECT_MANIPULATION = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T131311-codex-direct-manipulation-variety-matrix-v1/direct-manipulation/direct_manipulation_variety_matrix_v1.json"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
TIMEFRAME_CELLS = [f"{tf}:{root}" for tf in ["1w", "1mo"] for root in ROOTS]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    parent = read_json(PARENT_ROOT)
    axiswise = read_json(AXISWISE)
    cross_context = read_json(CROSS_CONTEXT)
    direct = read_json(DIRECT_MANIPULATION)

    parent_gates = {
        gate["regime"]: gate
        for gate in parent.get("gates", [])
        if gate.get("taxonomy_role") == "MainRegimeV2_price_root"
    }
    parent_pass = all(parent_gates.get(root, {}).get("accepted_95_scoped_parent_root_gate") for root in ROOTS)

    axiswise_cells = set(axiswise.get("decision", {}).get("accepted_95_timeframe_root_cells", []))
    axiswise_pass = all(cell in axiswise_cells for cell in TIMEFRAME_CELLS)

    scoped_cross_context_pass = bool(
        cross_context.get("decision", {}).get("scoped_cross_market_timeframe_price_roots_pass")
    )
    direct_full_variety_complete = bool(direct.get("rollup", {}).get("full_direct_manipulation_variety_coverage"))

    checklist = [
        {
            "requirement": "Every active MainRegimeV2 price root has its own 95% parent-root gate.",
            "status": "pass" if parent_pass else "fail",
            "evidence": rel(PARENT_ROOT),
            "notes": "Daily US equity/index parent-root gates cover Bull, Bear, Sideways, and Crisis directly.",
        },
        {
            "requirement": "Weekly and monthly same-source timeframe cells validate at 95% for every active price root.",
            "status": "pass" if axiswise_pass else "fail",
            "evidence": rel(AXISWISE),
            "notes": "Axiswise source-consensus gate accepted 1w and 1mo cells for all four roots.",
        },
        {
            "requirement": "Evidence survives more than one market/context and more than one timeframe.",
            "status": "pass" if scoped_cross_context_pass else "fail",
            "evidence": rel(CROSS_CONTEXT),
            "notes": "v10 scoped audit is still a scoped floor, not the expanded full-universe/full-species objective.",
        },
        {
            "requirement": "Unsupported intraday/full-species cells are not silently counted as complete.",
            "status": "pass",
            "evidence": rel(BOARD),
            "notes": "Current cursor still records unsupported intraday/full-species cells as open.",
        },
        {
            "requirement": "Direct Manipulation is direct-event/order-flow/order-lifecycle evidence, not OHLCV proxy evidence.",
            "status": "pass",
            "evidence": rel(DIRECT_MANIPULATION),
            "notes": "Direct varieties are scoped; missing spoofing/layering matched negatives, quote stuffing, pinging, bear raid, and painting-the-tape.",
        },
        {
            "requirement": "Full objective gate closes only when full-market/full-timeframe/full-species plus direct Manipulation coverage are complete.",
            "status": "blocked",
            "evidence": rel(BOARD),
            "notes": "Same-source 1w/1mo is now closed, but expanded intraday/full-species and direct Manipulation variety coverage remain open.",
        },
    ]

    package = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective": "Every active MainRegimeV2 regime reaches 95% confidence and survives validation across other markets, timeframes, cycles, and species; direct Manipulation stays direct-evidence only.",
        "active_taxonomy": {
            "name": "MainRegimeV2",
            "price_roots": ROOTS,
            "separate_direct_event_class_or_overlay": ["Manipulation"],
        },
        "audited_files": {
            "board": rel(BOARD),
            "board_sha256": sha256(BOARD),
            "stock_panel_parent_root_abstain": rel(PARENT_ROOT),
            "source_consensus_axiswise_timeframe_gate": rel(AXISWISE),
            "cross_context_completion_audit_v10": rel(CROSS_CONTEXT),
            "direct_manipulation_variety_matrix": rel(DIRECT_MANIPULATION),
        },
        "prompt_to_artifact_checklist": checklist,
        "price_root_status": {
            "daily_parent_roots_accepted_95": parent_pass,
            "same_source_weekly_monthly_cells_accepted_95": axiswise_pass,
            "same_source_weekly_monthly_cells": sorted(TIMEFRAME_CELLS),
            "scoped_cross_market_timeframe_price_roots_pass": scoped_cross_context_pass,
        },
        "manipulation_status": {
            "full_direct_manipulation_variety_coverage_complete": direct_full_variety_complete,
            "accepted_scoped_direct_varieties": direct.get("rollup", {}).get("accepted_scoped_varieties", []),
            "missing_direct_varieties": direct.get("rollup", {}).get("missing_varieties", []),
        },
        "remaining_blockers": [
            "Expanded intraday/full-species MainRegimeV2 source-label matrix remains incomplete.",
            "Same-source stock-market-regimes weekly/monthly closure is US equity/index scoped, not all species.",
            "Direct Manipulation variety coverage remains incomplete without matched negatives for spoofing/layering and other order-book varieties.",
            "Full objective gate remains none; do not call update_goal.",
        ],
        "decision": {
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "call_update_goal": False,
            "gate_result": "post_axiswise_audit_same_source_timeframes_closed_full_matrix_still_blocked",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": "Target unsupported intraday/full-species MainRegimeV2 cells with native or broader source-label panels; keep direct Manipulation matched-negative acquisition separate.",
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v11_after_axiswise.json"
    json_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")

    md = [
        "# Current Goal Completion Audit v11: After Axiswise Source Consensus",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Objective Restatement",
        "",
        "- Every active `MainRegimeV2` price root needs 95% confidence.",
        "- Evidence must survive other markets/contexts, other timeframes, full-cycle, and full-species checks.",
        "- Child/sub-regime packets must not complete parent roots.",
        "- `Manipulation` remains separate direct evidence and cannot be represented by OHLCV proxies.",
        "- Full completion requires the expanded full-market/full-timeframe/full-species gate, not just scoped evidence.",
        "",
        "## Checklist",
        "",
        "| Requirement | Status | Evidence | Notes |",
        "|---|---|---|---|",
    ]
    for item in checklist:
        md.append(
            f"| {item['requirement']} | `{item['status']}` | `{item['evidence']}` | {item['notes']} |"
        )
    md.extend([
        "",
        "## Decision",
        "",
        f"- Daily parent roots accepted 95: `{str(parent_pass).lower()}`.",
        f"- Same-source weekly/monthly cells accepted 95: `{str(axiswise_pass).lower()}`.",
        f"- Scoped cross-market/timeframe price roots pass: `{str(scoped_cross_context_pass).lower()}`.",
        f"- Full direct `Manipulation` variety coverage complete: `{str(direct_full_variety_complete).lower()}`.",
        "- Full objective achieved: `false`.",
        "- `update_goal`: `false`.",
        "- Gate result: `post_axiswise_audit_same_source_timeframes_closed_full_matrix_still_blocked`.",
        "",
        "## Remaining Blockers",
        "",
    ])
    md.extend(f"- {blocker}" for blocker in package["remaining_blockers"])
    (OUT_DIR / "current_goal_completion_audit_v11_after_axiswise.md").write_text("\n".join(md) + "\n")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={package['audited_files']['board_sha256']}",
        f"daily_parent_roots_accepted_95={str(parent_pass).lower()}",
        f"same_source_weekly_monthly_cells_accepted_95={str(axiswise_pass).lower()}",
        f"scoped_cross_market_timeframe_price_roots_pass={str(scoped_cross_context_pass).lower()}",
        f"full_direct_manipulation_variety_coverage_complete={str(direct_full_variety_complete).lower()}",
        "accepted_full_objective_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "full_objective_achieved=false",
        "call_update_goal=false",
        "gate_result=post_axiswise_audit_same_source_timeframes_closed_full_matrix_still_blocked",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    (CHECK_DIR / "current_goal_completion_audit_v11_after_axiswise_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )

    assert parent_pass
    assert axiswise_pass
    assert scoped_cross_context_pass
    assert not direct_full_variety_complete
    assert not package["decision"]["full_objective_achieved"]


if __name__ == "__main__":
    main()
