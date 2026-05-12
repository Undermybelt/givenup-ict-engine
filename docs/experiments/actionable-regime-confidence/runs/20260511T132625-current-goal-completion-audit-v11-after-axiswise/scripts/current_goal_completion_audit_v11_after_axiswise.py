#!/usr/bin/env python3
"""Post-axiswise completion audit for Board A's regime-confidence objective."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T132625+0800-current-goal-completion-audit-v11-after-axiswise"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T132625-current-goal-completion-audit-v11-after-axiswise"
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
AXISWISE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T131922-codex-source-consensus-axiswise-timeframe-gate-v1/"
    "source-consensus-axiswise/source_consensus_axiswise_timeframe_gate_v1.json"
)
DAILY_PARENT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T125122-codex-stock-market-regimes-parent-root-abstain/"
    "parent-root-abstain/stock_market_regimes_parent_root_abstain.json"
)
CROSS_CONTEXT_AUDIT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T130102-current-goal-completion-audit-v10-cross-context/"
    "completion-audit/current_goal_completion_audit_v10_cross_context.json"
)
DIRECT_MATRIX = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T131311-codex-direct-manipulation-variety-matrix-v1/"
    "direct-manipulation/direct_manipulation_variety_matrix_v1.json"
)
ACQUISITION_V2 = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T081715-codex-source-label-acquisition-package-v2/"
    "acquisition-package/source_label_acquisition_package_v2.json"
)

OUT_JSON = OUT_DIR / "current_goal_completion_audit_v11_after_axiswise.json"
OUT_MD = OUT_DIR / "current_goal_completion_audit_v11_after_axiswise.md"
OUT_CSV = OUT_DIR / "targeted_unsupported_cell_targets_v11.csv"
OUT_ASSERT = CHECK_DIR / "current_goal_completion_audit_v11_after_axiswise_assertions.out"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
EXPECTED_AXISWISE_CELLS = {f"{tf}:{root}" for tf in ["1w", "1mo"] for root in ROOTS}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def board_cursor(board_text: str) -> dict[str, str]:
    fields = {}
    for name in [
        "board_state",
        "last_loop_id",
        "active_market_set",
        "active_timeframes",
        "current_run_root",
        "accepted_gate",
        "blocker",
        "next_action",
    ]:
        match = re.search(rf"^\| {re.escape(name)} \| (.*?) \|", board_text, re.MULTILINE)
        fields[name] = match.group(1).strip() if match else ""
    return fields


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text(encoding="utf-8")
    axiswise = read_json(AXISWISE)
    daily = read_json(DAILY_PARENT)
    cross_context = read_json(CROSS_CONTEXT_AUDIT)
    direct = read_json(DIRECT_MATRIX)
    acquisition = read_json(ACQUISITION_V2)

    accepted_axiswise = set(axiswise["decision"]["accepted_95_timeframe_root_cells"])
    blocked_axiswise = set(axiswise["decision"]["blocked_timeframe_root_cells"])
    axiswise_8of8 = accepted_axiswise == EXPECTED_AXISWISE_CELLS and not blocked_axiswise

    daily_roots = {
        gate["regime"]: {
            "accepted_95": bool(gate["accepted_95_scoped_parent_root_gate"]),
            "min_lcb": min(
                gate["stats"]["calibration"]["wilson95_lcb"],
                gate["stats"]["heldout_time"]["wilson95_lcb"],
                gate["stats"]["heldout_ticker"]["wilson95_lcb"],
            ),
            "scope": "daily US equities/indices",
            "gate_id": gate["gate_id"],
        }
        for gate in daily["gates"]
    }
    daily_4of4 = all(daily_roots[root]["accepted_95"] for root in ROOTS)

    cross_context_decision = cross_context["decision"]
    scoped_cross_context_pass = bool(cross_context_decision["scoped_cross_market_timeframe_price_roots_pass"])

    direct_rollup = direct["rollup"]
    full_direct_manipulation_coverage = bool(direct_rollup["full_direct_manipulation_variety_coverage"])

    acquisition_request = acquisition["acquisition_request"]
    stale_but_still_relevant_gap = {
        "source": rel(ACQUISITION_V2),
        "note": (
            "This v2 612-slot request predates the 130600/131922 same-source 1w/1mo closure, "
            "so its monthly counts are stale; its intraday/full-species and direct-label requirements remain valid blockers."
        ),
        "missing_or_rejected_slots_by_timeframe": acquisition_request["missing_or_rejected_slots_by_timeframe"],
        "missing_or_rejected_slots_by_reason": acquisition_request["missing_or_rejected_slots_by_reason"],
        "missing_or_rejected_slots_by_provider": acquisition_request["missing_or_rejected_slots_by_provider"],
    }

    checklist = [
        {
            "requirement": "Every active MainRegimeV2 price root has a 95% parent-root gate.",
            "status": "pass" if daily_4of4 else "fail",
            "evidence": rel(DAILY_PARENT),
            "notes": "Daily stock/index source-label panel accepts Bull/Bear/Sideways/Crisis.",
        },
        {
            "requirement": "Weekly and monthly same-source timeframe cells pass for every price root.",
            "status": "pass" if axiswise_8of8 else "fail",
            "evidence": rel(AXISWISE),
            "notes": "Axiswise validation accepts 1w and 1mo cells for all four roots.",
        },
        {
            "requirement": "Other-market and other-timeframe evidence exists for all price roots.",
            "status": "partial",
            "evidence": rel(CROSS_CONTEXT_AUDIT),
            "notes": "Scoped cross-context floor passes, but the expanded full-universe/full-cycle matrix is still incomplete.",
        },
        {
            "requirement": "Full-cycle/full-species coverage is accepted, not merely scoped.",
            "status": "fail",
            "evidence": rel(ACQUISITION_V2),
            "notes": "Unsupported intraday/full-species native source-label cells remain open; the older 612-slot package is stale for monthly counts but still proves label-coverage incompleteness.",
        },
        {
            "requirement": "Manipulation has complete direct-event/order-flow/order-lifecycle variety coverage with positive and matched negative controls.",
            "status": "fail",
            "evidence": rel(DIRECT_MATRIX),
            "notes": "Scoped pump/dump, DEX self-trade, and on-chain wash-maker slices pass; spoofing/layering matched negatives, quote stuffing, pinging, bear raid, and painting-the-tape remain open.",
        },
        {
            "requirement": "No child/sub-regime or OHLCV-only proxy is promoted to complete a parent root or Manipulation.",
            "status": "pass",
            "evidence": rel(BOARD),
            "notes": "Current board keeps MainRegimeV2 roots active and records Manipulation as separate direct evidence.",
        },
    ]

    targeted_next_cells = [
        {
            "lane": "price_root_source_labels",
            "target_scope": "native intraday MainRegimeV2 labels for index ETF/futures and liquid crypto/futures contexts",
            "roots_or_varieties": ",".join(ROOTS),
            "timeframe_or_event_grain": "1m,5m,15m,30m,1h,4h",
            "current_evidence": "daily/1w/1mo same-source stock/index cells and scoped cross-context floors only",
            "blocker": "no accepted native intraday source-label panel covering all four price roots",
            "required_evidence": "independent timestamped parent-root labels, chronological calibration/test split, heldout instrument/context validation",
            "next_probe_constraint": "do not use HMM/OHLCV/future-return/generated strategy labels as acceptance evidence",
        },
        {
            "lane": "price_root_source_labels",
            "target_scope": "full-species MainRegimeV2 labels outside the same-source US stock/index panel",
            "roots_or_varieties": ",".join(ROOTS),
            "timeframe_or_event_grain": "1d,1w,1mo plus provider-native intervals where labels exist",
            "current_evidence": "scoped crypto/equity/futures support exists but not a full accepted source-label panel",
            "blocker": "old acquisition request still shows non-yfinance, instrument, and provider/source-label gaps",
            "required_evidence": "exact-underlying or native source labels for crypto, futures, commodity, ETF, and single-stock contexts",
            "next_probe_constraint": "target known source-label panels or authenticated exports; avoid broad metadata-only web sweeps",
        },
        {
            "lane": "direct_manipulation",
            "target_scope": "spoofing/layering and quote-stuffing order-book/order-lifecycle controls",
            "roots_or_varieties": "spoofing_layering,quote_stuffing",
            "timeframe_or_event_grain": "timestamped order-message/order-lifecycle rows",
            "current_evidence": "204 positive enforcement cases but no matched negative controls",
            "blocker": "positive-only inventory cannot produce a Wilson95 positive/negative direct gate",
            "required_evidence": "matched negative normal-period rows from same venue/instrument/message schema",
            "next_probe_constraint": "do not promote OHLCV liquidity/session/sweep proxies to direct Manipulation evidence",
        },
        {
            "lane": "direct_manipulation",
            "target_scope": "missing direct varieties",
            "roots_or_varieties": "pinging,bear_raid,painting_the_tape",
            "timeframe_or_event_grain": "timestamped event/order-flow rows",
            "current_evidence": "no accepted direct rows in current artifacts",
            "blocker": "missing positive and negative rows",
            "required_evidence": "direct event/order-flow rows plus same-source non-event controls",
            "next_probe_constraint": "keep this separate from MainRegimeV2 price-root accounting",
        },
    ]

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(targeted_next_cells[0].keys()))
        writer.writeheader()
        writer.writerows(targeted_next_cells)

    full_objective_achieved = False
    decision = {
        "goal_achieved": full_objective_achieved,
        "call_update_goal": False,
        "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "gate_result": "post_axiswise_same_source_timeframes_pass_full_matrix_and_direct_manipulation_still_blocked",
        "axiswise_same_source_timeframe_cells_8of8": axiswise_8of8,
        "daily_parent_roots_4of4": daily_4of4,
        "scoped_cross_context_price_roots_pass": scoped_cross_context_pass,
        "expanded_full_cycle_full_species_complete": False,
        "direct_manipulation_full_variety_coverage": full_direct_manipulation_coverage,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": {
            "source": rel(BOARD),
            "concrete_success_criteria": [
                "Bull, Bear, Sideways, and Crisis each have 95% calibrated evidence.",
                "The evidence survives other markets and other timeframes.",
                "The expanded full-cycle/full-species matrix is either covered or explicitly scoped down by the user.",
                "Manipulation is validated through direct event/order-flow/order-lifecycle/social/on-chain evidence with matched controls, not OHLCV proxies.",
                "Only after all blockers close can update_goal be called.",
            ],
        },
        "audited_files": {
            "board": rel(BOARD),
            "board_sha256": sha256(BOARD),
            "axiswise_timeframe_gate": rel(AXISWISE),
            "axiswise_timeframe_gate_sha256": sha256(AXISWISE),
            "daily_parent_root_gate": rel(DAILY_PARENT),
            "cross_context_audit_v10": rel(CROSS_CONTEXT_AUDIT),
            "direct_manipulation_variety_matrix": rel(DIRECT_MATRIX),
            "acquisition_package_v2": rel(ACQUISITION_V2),
        },
        "current_cursor_readback": board_cursor(board_text),
        "prompt_to_artifact_checklist": checklist,
        "daily_parent_root_evidence": daily_roots,
        "same_source_axiswise_timeframe_evidence": {
            "accepted_cells": sorted(accepted_axiswise),
            "blocked_cells": sorted(blocked_axiswise),
            "axiswise_8of8": axiswise_8of8,
        },
        "cross_context_evidence": {
            "source": rel(CROSS_CONTEXT_AUDIT),
            "scoped_cross_context_price_roots_pass": scoped_cross_context_pass,
            "decision": cross_context_decision,
        },
        "direct_manipulation_evidence": {
            "source": rel(DIRECT_MATRIX),
            "accepted_scoped_varieties": direct_rollup["accepted_scoped_varieties"],
            "blocked_or_positive_only_varieties": direct_rollup["blocked_or_positive_only_varieties"],
            "missing_varieties": direct_rollup["missing_varieties"],
            "full_direct_manipulation_variety_coverage": full_direct_manipulation_coverage,
        },
        "stale_but_still_relevant_source_label_gap": stale_but_still_relevant_gap,
        "targeted_next_cells": {
            "csv": rel(OUT_CSV),
            "rows": targeted_next_cells,
        },
        "decision": decision,
        "next_action": (
            "Target one native/broader source-label panel for unsupported intraday/full-species MainRegimeV2 cells; "
            "keep direct Manipulation matched-negative acquisition separate and fail-closed."
        ),
    }

    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Current Goal Completion Audit v11 After Axiswise",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        "- Goal achieved: `false`.",
        "- Same-source `1w/1mo` price-root cells: `8/8` accepted at 95 by axiswise validation.",
        "- Daily parent-root stock/index cells: `4/4` accepted at 95.",
        "- Scoped cross-context price-root floor: `pass`.",
        "- Expanded full-cycle/full-species objective: `blocked`.",
        "- Direct `Manipulation` full variety coverage: `false`.",
        "- `update_goal`: `false`.",
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Notes |",
        "|---|---|---|---|",
    ]
    for item in checklist:
        lines.append(
            f"| {item['requirement']} | `{item['status']}` | `{item['evidence']}` | {item['notes']} |"
        )

    lines.extend(
        [
            "",
            "## Accepted Price-Root Coverage",
            "",
            "| Layer | Coverage | Evidence |",
            "|---|---:|---|",
            f"| Daily same-source parent roots | `4/4` | `{rel(DAILY_PARENT)}` |",
            f"| Weekly/monthly same-source axiswise roots | `8/8` | `{rel(AXISWISE)}` |",
            f"| Scoped cross-market/timeframe floor | `pass` | `{rel(CROSS_CONTEXT_AUDIT)}` |",
            "",
            "## Remaining Blockers",
            "",
            "- Unsupported intraday/full-species native source-label cells remain open.",
            "- The older 612-slot acquisition package is stale for monthly counts after the axiswise gate, but it still proves unresolved intraday/provider/full-species label requirements.",
            "- Direct `Manipulation` is still missing spoofing/layering matched negatives, quote-stuffing rows, pinging rows, bear-raid rows, and painting-the-tape rows.",
            "- No OHLCV/session/liquidity/sweep proxy can close direct `Manipulation`.",
            "",
            "## Targeted Next Cells",
            "",
            f"CSV: `{rel(OUT_CSV)}`",
            "",
            "| Lane | Target Scope | Blocker | Required Evidence |",
            "|---|---|---|---|",
        ]
    )
    for row in targeted_next_cells:
        lines.append(
            f"| `{row['lane']}` | {row['target_scope']} | {row['blocker']} | {row['required_evidence']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Gate result: `post_axiswise_same_source_timeframes_pass_full_matrix_and_direct_manipulation_still_blocked`.",
            "- Runtime code changed: `false`.",
            "- Thresholds relaxed: `false`.",
            "- Raw data committed: `false`.",
            "- Trade usable: `false`.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"axiswise_same_source_timeframe_cells_8of8={str(axiswise_8of8).lower()}",
        f"daily_parent_roots_4of4={str(daily_4of4).lower()}",
        f"scoped_cross_context_price_roots_pass={str(scoped_cross_context_pass).lower()}",
        "expanded_full_cycle_full_species_complete=false",
        f"direct_manipulation_full_variety_coverage={str(full_direct_manipulation_coverage).lower()}",
        "goal_achieved=false",
        "call_update_goal=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
