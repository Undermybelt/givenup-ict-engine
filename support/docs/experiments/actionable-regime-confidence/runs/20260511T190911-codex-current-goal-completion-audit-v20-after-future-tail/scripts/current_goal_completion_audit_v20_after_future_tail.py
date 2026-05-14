#!/usr/bin/env python3
"""Verify Board A v20 completion-audit inputs."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]


def read_json(path: str) -> dict:
    return json.loads((REPO_ROOT / path).read_text())


def main() -> None:
    v14 = read_json(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T155959-current-goal-completion-audit-v14-after-consumer-map/"
        "completion-audit/current_goal_completion_audit_v14_after_consumer_map.json"
    )
    future = read_json(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T190440-codex-strict-1h-future-tail-gate-rerun-v1/"
        "future-tail-gate-rerun/strict_1h_future_tail_gate_rerun_v1.json"
    )
    timeframe = read_json(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T185126-codex-timeframe-cycle-coverage-readback-v1/"
        "timeframe-cycle-readback/timeframe_cycle_coverage_readback_v1.json"
    )
    source = read_json(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T184856-codex-source-label-other-market-readback-v1/"
        "source-label-readback/source_label_other_market_readback_v1.json"
    )
    schema = read_json(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T185420-codex-local-intake-schema-sweep-v1/"
        "local-intake-schema-sweep/local_intake_schema_sweep_v1.json"
    )
    direct = read_json(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T184630-codex-direct-manipulation-coverage-readback-v2/"
        "direct-manipulation-readback/direct_manipulation_coverage_readback_v2.json"
    )
    missing = read_json(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T185706-codex-direct-missing-species-source-screen-v1/"
        "direct-missing-species-screen/direct_missing_species_source_screen_v1.json"
    )

    assert v14["decision"]["scoped_active_lane_accepted_95"] is True
    assert future["decision"]["strict_1h_future_protocol_rows_after"] == 45
    assert future["decision"]["strict_1h_total_slots"] == 156
    assert future["decision"]["strict_full_objective_achieved"] is False
    assert timeframe["native_subhour_ready_cells"] == 0
    assert timeframe["native_subhour_total_cells"] == 4
    assert source["accepted_factor_or_gate_total"] == 0
    assert schema["exact_schema_matches"] == 0
    assert direct["remaining_unaccepted_variety_count"] == 6
    assert missing["ready_source_candidate_count"] == 0

    print("PASS scoped_active_lanes_accepted_95=true")
    print("PASS strict_1h_fixed_gate_rows=41/156")
    print("PASS strict_1h_future_protocol_rows=45/156")
    print("PASS native_subhour_ready=0/4")
    print("PASS source_label_other_market_gate_total=0")
    print("PASS local_schema_exact_matches=0")
    print("PASS direct_remaining_unaccepted_varieties=6")
    print("PASS direct_missing_species_ready_sources=0")
    print("PASS strict_full_objective=false")
    print("PASS update_goal=false")


if __name__ == "__main__":
    main()
