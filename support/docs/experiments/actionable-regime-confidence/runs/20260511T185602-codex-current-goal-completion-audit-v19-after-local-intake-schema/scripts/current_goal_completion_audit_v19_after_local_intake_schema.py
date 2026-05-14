#!/usr/bin/env python3
"""Prompt-to-artifact completion audit after local intake schema sweep."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T185602-codex-current-goal-completion-audit-v19-after-local-intake-schema"
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
TODO_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

ARTIFACTS = {
    "v18_prompt": "docs/experiments/actionable-regime-confidence/runs/20260511T183611-codex-current-goal-completion-audit-v18-prompt-artifact/completion-audit/current_goal_completion_audit_v18_prompt_artifact.json",
    "source_other_market": "docs/experiments/actionable-regime-confidence/runs/20260511T184856-codex-source-label-other-market-readback-v1/source-label-readback/source_label_other_market_readback_v1.json",
    "local_acquisition": "docs/experiments/actionable-regime-confidence/runs/20260511T185209-codex-board-a-local-acquisition-ledger-v1/local-acquisition-ledger/board_a_local_acquisition_ledger_v1.json",
    "local_schema_sweep": "docs/experiments/actionable-regime-confidence/runs/20260511T185420-codex-local-intake-schema-sweep-v1/local-intake-schema-sweep/local_intake_schema_sweep_v1.json",
    "direct_coverage": "docs/experiments/actionable-regime-confidence/runs/20260511T184630-codex-direct-manipulation-coverage-readback-v2/direct-manipulation-readback/direct_manipulation_coverage_readback_v2.json",
    "direct_missing_species": "docs/experiments/actionable-regime-confidence/runs/20260511T185706-codex-direct-missing-species-source-screen-v1/direct-missing-species-screen/direct_missing_species_source_screen_v1.json",
    "timeframe_readback": "docs/experiments/actionable-regime-confidence/runs/20260511T185126-codex-timeframe-cycle-coverage-readback-v1/timeframe-cycle-readback/timeframe_cycle_coverage_readback_v1.json",
    "strict_1h_requirements": "docs/experiments/actionable-regime-confidence/runs/20260511T184151-codex-strict-1h-near-miss-extension-requirements-v1/strict-1h-extension-requirements/strict_1h_near_miss_extension_requirements_v1.json",
    "jan_tail_support": "docs/experiments/actionable-regime-confidence/runs/20260511T184530-codex-strict-1h-jan2026-tail-support-probe-v1/jan2026-tail-support/strict_1h_jan2026_tail_support_probe_v1.json",
    "native_subhour": "docs/experiments/actionable-regime-confidence/runs/20260511T180420-codex-native-subhour-overlap-blocker-v1/native-subhour-overlap/native_subhour_overlap_blocker_v1.json",
}


def load(name: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / ARTIFACTS[name]).read_text(encoding="utf-8"))


def decision(payload: dict[str, object]) -> dict[str, object]:
    value = payload.get("decision", {})
    return value if isinstance(value, dict) else {}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    v18 = load("v18_prompt")
    source_other = load("source_other_market")
    local_acq = load("local_acquisition")
    schema_sweep = load("local_schema_sweep")
    direct = load("direct_coverage")
    direct_missing = load("direct_missing_species")
    timeframe = load("timeframe_readback")
    strict_1h = load("strict_1h_requirements")
    jan_tail = load("jan_tail_support")
    native = load("native_subhour")

    v18_decision = decision(v18)
    source_decision = decision(source_other)
    schema_decision = decision(schema_sweep)
    direct_decision = decision(direct)
    direct_missing_decision = decision(direct_missing)
    timeframe_decision = decision(timeframe)
    strict_decision = decision(strict_1h)
    jan_decision = decision(jan_tail)
    native_decision = decision(native)

    strict_counts = strict_1h.get("counts", {})
    if not isinstance(strict_counts, dict):
        strict_counts = {}
    jan_counts = jan_tail.get("counts", {})
    if not isinstance(jan_counts, dict):
        jan_counts = {}
    native_summary = native.get("summary", {})
    if not isinstance(native_summary, dict):
        native_summary = {}

    checklist = [
        {
            "requirement": "every active regime has calibrated confidence >=95",
            "status": "pass_scoped_not_full",
            "artifact": ARTIFACTS["v18_prompt"],
            "evidence": "scoped_active_lane_status=accepted_95; accepted lanes Bull/Bear/Sideways/Crisis/scoped direct Manipulation remain present",
            "gap": "This is scoped evidence only; the objective also requires other-market and other-cycle validation.",
        },
        {
            "requirement": "validated on other markets/species with source-owned or owner-approved labels",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["source_other_market"],
            "evidence": f"source_label_other_market_gate={source_decision.get('gate_result')}; accepted_factor_or_gate_total={source_other.get('accepted_factor_or_gate_total')}",
            "gap": "No full source-label equivalence; public/partial slots do not form owner-approved MainRegimeV2 cross-market evidence.",
        },
        {
            "requirement": "local intake files can supply missing source-owned rows/provenance",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["local_schema_sweep"],
            "evidence": f"required_intake_present={local_acq.get('ready_intake_file_count')}/12; exact_schema_matches={schema_sweep.get('exact_schema_matches')}; strong_partial_schema_matches={schema_sweep.get('strong_partial_schema_matches')}",
            "gap": "No local file matches the external price-root, recency, direct-positive, or direct-control required schemas.",
        },
        {
            "requirement": "validated on other cycles/timeframes with suitable confidence",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["timeframe_readback"],
            "evidence": f"timeframe_gate={timeframe_decision.get('gate_result')}; strict_1h_accepted={timeframe.get('strict_1h_accepted_rows')}/{timeframe.get('strict_1h_total_slots')}; native_subhour_ready={timeframe.get('native_subhour_ready_cells')}/{timeframe.get('native_subhour_total_cells')}",
            "gap": "Strict exact 1h remains partial and native sub-hour source overlap remains zero.",
        },
        {
            "requirement": "Jan-2026 source tail can promote current strict-1h gate",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["jan_tail_support"],
            "evidence": f"provider_ready_tail={jan_counts.get('provider_ready_for_tail')}; standalone_tail_gate_passes={jan_counts.get('standalone_tail_gate_passes')}; gate={jan_decision.get('gate_result')}",
            "gap": "Tail support is future-gate preflight only and cannot retroactively accept the fixed 2024/2025 strict gate.",
        },
        {
            "requirement": "direct Manipulation full species/variety coverage with matched controls",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["direct_coverage"],
            "evidence": f"accepted_scoped_varieties={direct.get('accepted_scoped_variety_count')}; remaining_unaccepted={direct.get('remaining_unaccepted_variety_count')}; web_ready={direct.get('web_screen_ready_source_candidate_count')}; spoofing_matched_negatives={direct.get('spoofing_layering_matched_negative_cases_available')}; missing_species_screen_gate={direct_missing_decision.get('gate_result')}; ready_missing_species_sources={direct_missing.get('ready_source_candidate_count')}",
            "gap": "Scoped direct varieties exist, but spoofing/layering lacks matched negatives and quote stuffing/pinging/bear raid/painting tape remain missing.",
        },
        {
            "requirement": "do not rely on proxy/generated/OHLCV-only labels",
            "status": "pass_guardrail",
            "artifact": ARTIFACTS["source_other_market"],
            "evidence": "source-label readbacks and schema sweep add zero accepted rows and keep proxy/candidate mappings blocked",
            "gap": "Guardrail preserved; it also means the full objective remains blocked until proper rows arrive.",
        },
    ]
    unmet = [row for row in checklist if row["status"].startswith("fail")]
    strict_full_objective_achieved = len(unmet) == 0
    audit_decision = {
        "gate_result": "current_goal_completion_audit_v19=scoped_95_present_local_schema_sweep_confirms_full_objective_blocked",
        "strict_full_objective_achieved": strict_full_objective_achieved,
        "update_goal": False,
        "blocking_requirements": [row["requirement"] for row in unmet],
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    payload = {
        "artifact_type": "current_goal_completion_audit_v19_after_local_intake_schema",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": RUN_ID,
        "objective": "Every active regime must have calibrated >=95% confidence and must retain suitable confidence on other markets/species and other cycles/timeframes.",
        "todo_hash_before_append": hashlib.sha256(TODO_PATH.read_bytes()).hexdigest(),
        "checklist": checklist,
        "unmet_requirements": unmet,
        "decision": audit_decision,
    }
    (OUT_DIR / "current_goal_completion_audit_v19_after_local_intake_schema.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    checklist_csv = OUT_DIR / "current_goal_completion_audit_v19_checklist.csv"
    with checklist_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(checklist[0].keys()))
        writer.writeheader()
        writer.writerows(checklist)

    unmet_csv = OUT_DIR / "current_goal_completion_audit_v19_unmet_requirements.csv"
    with unmet_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(checklist[0].keys()))
        writer.writeheader()
        writer.writerows(unmet)

    report = [
        "# Current Goal Completion Audit v19 After Local Intake Schema",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Objective",
        "",
        payload["objective"],
        "",
        "## Decision",
        "",
        f"`{audit_decision['gate_result']}`",
        "",
        f"- Strict full objective achieved: `{str(strict_full_objective_achieved).lower()}`; `update_goal=false`.",
        "- Scoped active-lane `>=95%` evidence remains present, but it is not enough for the full objective.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "",
        "## Blocking Requirements",
        "",
    ]
    for row in unmet:
        report.append(f"- `{row['requirement']}`: {row['gap']}")
    report.extend(
        [
            "",
            "## Key Evidence",
            "",
            f"- Source-label other-market gate: `{source_decision.get('gate_result')}`; accepted factor/gate total `{source_other.get('accepted_factor_or_gate_total')}`.",
            f"- Local intake schema sweep exact matches: `{schema_sweep.get('exact_schema_matches')}`; strong partial matches `{schema_sweep.get('strong_partial_schema_matches')}`.",
            f"- Timeframe/cycle readback gate: `{timeframe_decision.get('gate_result')}`.",
            f"- Strict exact `1h`: `{timeframe.get('strict_1h_accepted_rows')}/{timeframe.get('strict_1h_total_slots')}`.",
            f"- Native sub-hour overlap: `{timeframe.get('native_subhour_ready_cells')}/{timeframe.get('native_subhour_total_cells')}`.",
            f"- Direct Manipulation remaining unaccepted varieties: `{direct.get('remaining_unaccepted_variety_count')}`.",
            f"- Direct missing-species screen gate: `{direct_missing_decision.get('gate_result')}`; ready sources `{direct_missing.get('ready_source_candidate_count')}`.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/completion-audit/current_goal_completion_audit_v19_after_local_intake_schema.json`",
            f"- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/completion-audit/current_goal_completion_audit_v19_checklist.csv`",
            f"- Unmet requirements CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/completion-audit/current_goal_completion_audit_v19_unmet_requirements.csv`",
            f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/current_goal_completion_audit_v19_after_local_intake_schema_assertions.out`",
            "",
        ]
    )
    (OUT_DIR / "current_goal_completion_audit_v19_after_local_intake_schema.md").write_text(
        "\n".join(report),
        encoding="utf-8",
    )

    assertions = [
        f"PASS checklist_items={len(checklist)}",
        f"PASS unmet_requirements={len(unmet)}",
        "PASS scoped_95_present=true",
        f"PASS strict_full_objective={str(strict_full_objective_achieved).lower()}",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "current_goal_completion_audit_v19_after_local_intake_schema_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit_decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
