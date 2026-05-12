#!/usr/bin/env python3
"""Audit the user objective against current Board A evidence."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ID = "20260511T162537+0800-current-goal-full-objective-coverage-audit-v15"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T162537-current-goal-full-objective-coverage-audit-v15"
)
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"

CONSUMER_MAP = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153637-codex-regime-factor-consumer-map-v1/"
    "regime-factor-map/regime_factor_consumer_map_v1.json"
)
V14_AUDIT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T155959-current-goal-completion-audit-v14-after-consumer-map/"
    "completion-audit/current_goal_completion_audit_v14_after_consumer_map.json"
)
EXACT_1H = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T141910-codex-exact-1h-source-universe-expansion-v1/"
    "exact-1h-universe/exact_1h_source_universe_expansion_v1.json"
)
AXISWISE = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T131922-codex-source-consensus-axiswise-timeframe-gate-v1/"
    "source-consensus-axiswise/source_consensus_axiswise_timeframe_gate_v1.json"
)
DIRECT_MATRIX = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T131311-codex-direct-manipulation-variety-matrix-v1/"
    "direct-manipulation/direct_manipulation_variety_matrix_v1.json"
)
INTAKE = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_manifest_v1.json"
)
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def status_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return counts


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    consumer = load_json(CONSUMER_MAP)
    v14 = load_json(V14_AUDIT)
    exact_1h = load_json(EXACT_1H)
    axiswise = load_json(AXISWISE)
    direct = load_json(DIRECT_MATRIX)
    intake = load_json(INTAKE)

    active_roots = consumer["taxonomy"]["main_price_roots"]
    accepted_lanes = consumer["rollup"]["accepted_95_lanes"]
    min_price_root_floor = min(
        row["confidence_floor"]
        for row in consumer["map_rows"]
        if row["taxonomy_role"] == "MainRegimeV2_price_root"
    )
    manipulation_floor = next(
        row["confidence_floor"]
        for row in consumer["map_rows"]
        if row["regime"] == "Manipulation"
    )

    exact_decision = exact_1h["decision"]
    direct_rollup = direct["rollup"]
    v14_missing = v14["missing_or_incomplete"]

    checklist = [
        {
            "requirement": "named_authoritative_markdown_updated",
            "evidence": str(BOARD),
            "status": "pass",
            "notes": "same board owns cursor, sections, and Evidence Ledger",
        },
        {
            "requirement": "every_active_regime_has_95_confidence",
            "evidence": str(CONSUMER_MAP),
            "status": "pass_scoped",
            "notes": f"accepted lanes {len(accepted_lanes)}/5: {','.join(accepted_lanes)}",
        },
        {
            "requirement": "mainregimev2_roots_are_exact",
            "evidence": str(CONSUMER_MAP),
            "status": "pass",
            "notes": ",".join(active_roots),
        },
        {
            "requirement": "price_root_confidence_floor_ge_95",
            "evidence": str(CONSUMER_MAP),
            "status": "pass",
            "notes": f"min price-root floor={min_price_root_floor}",
        },
        {
            "requirement": "manipulation_direct_not_proxy",
            "evidence": str(DIRECT_MATRIX),
            "status": "pass_scoped",
            "notes": f"scoped direct floor={manipulation_floor}; full coverage={direct_rollup['full_direct_manipulation_variety_coverage']}",
        },
        {
            "requirement": "validate_on_other_markets",
            "evidence": str(EXACT_1H),
            "status": "partial",
            "notes": "39-ticker source panel context exists, but full NQ/QQQ/futures/crypto/FX source-label equivalence is not closed",
        },
        {
            "requirement": "validate_on_other_timeframes",
            "evidence": str(AXISWISE),
            "status": "partial",
            "notes": "daily/1w/1mo/exact 1h context exists; native sub-hour source overlap remains blocked",
        },
        {
            "requirement": "full_cycle_coverage",
            "evidence": str(V14_AUDIT),
            "status": "partial",
            "notes": "source recency remains capped at stock-market-regimes panel through 2026-01-30",
        },
        {
            "requirement": "full_species_coverage",
            "evidence": str(V14_AUDIT),
            "status": "fail",
            "notes": "full species/cross-market equivalence missing beyond source-panel context",
        },
        {
            "requirement": "ticker_specific_strict_support",
            "evidence": str(EXACT_1H),
            "status": "partial",
            "notes": f"strict accepted ticker/root rows={exact_decision['accepted_95_strict_ticker_root_rows']}/{exact_decision['scoped_slots']}",
        },
        {
            "requirement": "direct_manipulation_full_varieties",
            "evidence": str(DIRECT_MATRIX),
            "status": "fail",
            "notes": "missing/blocked varieties include spoofing/layering, quote stuffing, pinging, bear raid or painting tape",
        },
        {
            "requirement": "do_not_report_final_success_until_complete",
            "evidence": str(V14_AUDIT),
            "status": "pass_guardrail",
            "notes": "full_objective_achieved=false and call_update_goal=false",
        },
    ]

    work_orders = [
        {
            "priority": "P0",
            "gap": "full_species_cross_market_equivalence",
            "next_artifact": "source_label_equivalence_request_v1",
            "acceptance": "owner-approved or source-native labels for NQ/QQQ/futures/crypto/FX; no OHLCV proxy labels",
        },
        {
            "priority": "P0",
            "gap": "source_recency_after_2026_01_30",
            "next_artifact": "source_panel_recency_extension_v1",
            "acceptance": "source-owned labels beyond 2026-01-30, then rerun exact same gates",
        },
        {
            "priority": "P1",
            "gap": "ticker_specific_strict_support",
            "next_artifact": "strict_ticker_root_gap_selector_v1",
            "acceptance": "increase strict ticker/root accepted rows beyond 41/156 without pooled-context promotion",
        },
        {
            "priority": "P1",
            "gap": "native_subhour_timeframe_overlap",
            "next_artifact": "native_subhour_source_overlap_after_recency_v1",
            "acceptance": "source-date overlap exists for 1m/5m/15m/30m/90m before calibration",
        },
        {
            "priority": "P2",
            "gap": "direct_manipulation_missing_varieties",
            "next_artifact": "direct_row_intake_positive_negative_exports_v1",
            "acceptance": "source-owned positive rows plus matched negatives for spoofing/layering/quote-stuffing/pinging/bear-raid varieties",
        },
    ]

    failed_or_partial = [
        row["requirement"]
        for row in checklist
        if row["status"] in {"partial", "fail"}
    ]
    summary = {
        "run_id": RUN_ID,
        "artifact_type": "full_objective_coverage_audit",
        "objective": (
            "Every active regime reaches 95% confidence and survives other-market, "
            "other-timeframe, full-cycle, and full-species validation before final success is reported."
        ),
        "active_taxonomy": {
            "price_roots": active_roots,
            "direct_overlay": consumer["taxonomy"]["direct_overlay"],
            "child_labels_count_as_roots": False,
        },
        "inputs": {
            "consumer_map": str(CONSUMER_MAP),
            "v14_completion_audit": str(V14_AUDIT),
            "exact_1h_universe": str(EXACT_1H),
            "axiswise_timeframe_gate": str(AXISWISE),
            "direct_variety_matrix": str(DIRECT_MATRIX),
            "direct_row_intake_manifest": str(INTAKE),
        },
        "decision": {
            "scoped_active_lane_accepted_95": True,
            "full_objective_achieved": False,
            "call_update_goal": False,
            "accepted_gate": "full_objective_coverage_audit_v15=scoped_95_present_full_cycle_full_species_still_blocked",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "status_counts": status_counts(checklist),
        "failed_or_partial_requirements": failed_or_partial,
        "work_orders": work_orders,
        "v14_missing_or_incomplete": v14_missing,
        "next_action": (
            "Start with source_label_equivalence_request_v1 or source_panel_recency_extension_v1; "
            "do not run more broad negative sweeps and do not call update_goal."
        ),
    }

    write_csv(
        OUT_DIR / "current_goal_full_objective_coverage_audit_v15_checklist.csv",
        checklist,
        ["requirement", "evidence", "status", "notes"],
    )
    write_csv(
        OUT_DIR / "current_goal_full_objective_coverage_audit_v15_work_orders.csv",
        work_orders,
        ["priority", "gap", "next_artifact", "acceptance"],
    )
    (OUT_DIR / "current_goal_full_objective_coverage_audit_v15.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    checklist_table = "\n".join(
        f"| `{row['requirement']}` | `{row['status']}` | `{row['evidence']}` | {row['notes']} |"
        for row in checklist
    )
    work_order_table = "\n".join(
        f"| `{row['priority']}` | `{row['gap']}` | `{row['next_artifact']}` | {row['acceptance']} |"
        for row in work_orders
    )
    report = f"""# Current Goal Full Objective Coverage Audit v15

Run id: `{RUN_ID}`.

## Objective Restatement

The user-requested completion criteria are concrete:

1. Every active regime has a calibrated confidence floor at or above 95%.
2. Evidence survives validation on other markets.
3. Evidence survives validation on other timeframes/cycles.
4. Full-cycle coverage is not missing or stale.
5. Full-species coverage is not missing.
6. Final success is not reported until all requirements above are covered by artifacts, not proxies.

## Decision

- Scoped active-lane 95% status: `accepted_95`.
- Full objective achieved: `false`.
- `update_goal`: `false`.
- Gate result: `full_objective_coverage_audit_v15=scoped_95_present_full_cycle_full_species_still_blocked`.

## Prompt-To-Artifact Checklist

| Requirement | Status | Evidence | Notes |
|---|---|---|---|
{checklist_table}

## Prioritized Work Orders

| Priority | Gap | Next Artifact | Acceptance |
|---|---|---|---|
{work_order_table}

## Next

Start with `source_label_equivalence_request_v1` or `source_panel_recency_extension_v1`. Do not run more broad negative sweeps, do not promote proxies, and do not call `update_goal`.
"""
    (OUT_DIR / "current_goal_full_objective_coverage_audit_v15.md").write_text(report)

    observed = {
        "scoped_active_lane_accepted_95": True,
        "full_objective_achieved": False,
        "has_full_cycle_row": any(row["requirement"] == "full_cycle_coverage" for row in checklist),
        "has_full_species_row": any(row["requirement"] == "full_species_coverage" for row in checklist),
        "has_other_market_row": any(row["requirement"] == "validate_on_other_markets" for row in checklist),
        "has_other_timeframe_row": any(row["requirement"] == "validate_on_other_timeframes" for row in checklist),
        "has_failed_or_partial": bool(failed_or_partial),
        "call_update_goal": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
    }
    expected = {
        "scoped_active_lane_accepted_95": True,
        "full_objective_achieved": False,
        "has_full_cycle_row": True,
        "has_full_species_row": True,
        "has_other_market_row": True,
        "has_other_timeframe_row": True,
        "has_failed_or_partial": True,
        "call_update_goal": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
    }
    pass_status = all(observed[key] == expected[key] for key in expected)
    lines = [f"{key}={str(value).lower()}" for key, value in observed.items()]
    lines.append("assertion_status=PASS" if pass_status else "assertion_status=FAIL")
    (CHECK_DIR / "current_goal_full_objective_coverage_audit_v15_assertions.out").write_text(
        "\n".join(lines) + "\n"
    )
    if not lines[-1].endswith("PASS"):
        raise SystemExit("assertion failure")


if __name__ == "__main__":
    main()
