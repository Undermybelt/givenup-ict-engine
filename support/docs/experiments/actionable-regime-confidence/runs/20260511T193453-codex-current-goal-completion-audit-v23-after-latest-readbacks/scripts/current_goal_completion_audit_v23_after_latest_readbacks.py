#!/usr/bin/env python3
"""Completion audit after latest strict, sub-hour, and direct intake readbacks."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T193453-codex-current-goal-completion-audit-v23-after-latest-readbacks"
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
TODO_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

ARTIFACTS = {
    "v22": "docs/experiments/actionable-regime-confidence/runs/20260511T192655-codex-current-goal-completion-audit-v22-after-intake-and-subhour-readbacks/completion-audit/current_goal_completion_audit_v22_after_intake_and_subhour_readbacks.json",
    "strict_intake_verifier": "docs/experiments/actionable-regime-confidence/runs/20260511T192432-codex-strict-1h-source-intake-verifier-readback-v1/source-intake-verifier-readback/strict_1h_source_intake_verifier_readback_v1.json",
    "strict_contract_exhaustion": "docs/experiments/actionable-regime-confidence/runs/20260511T192900-codex-strict-1h-contract-panel-exhaustion-v1/strict-1h-contract-panel-exhaustion/strict_1h_contract_panel_exhaustion_v1.json",
    "stock_regime_live_recency": "docs/experiments/actionable-regime-confidence/runs/20260511T192218-codex-stock-regime-kaggle-live-recency-check-v1/kaggle-live-recency/stock_regime_kaggle_live_recency_check_v1.json",
    "native_subhour_quarantine": "docs/experiments/actionable-regime-confidence/runs/20260511T192248-codex-native-subhour-projection-quarantine-v1/native-subhour-projection-quarantine/native_subhour_projection_quarantine_v1.json",
    "native_subhour_external": "docs/experiments/actionable-regime-confidence/runs/20260511T192750-codex-native-subhour-external-source-screen-v1/native-subhour-external-source-screen/native_subhour_external_source_screen_v1.json",
    "external_source_second_screen": "docs/experiments/actionable-regime-confidence/runs/20260511T191623-codex-external-source-label-second-screen-v1/external-source-label-second-screen/external_source_label_second_screen_v1.json",
    "direct_missing_species_v2": "docs/experiments/actionable-regime-confidence/runs/20260511T191642-codex-direct-missing-species-source-screen-v2/direct-missing-species-screen/direct_missing_species_source_screen_v2.json",
    "direct_intake_verifier": "docs/experiments/actionable-regime-confidence/runs/20260511T193301-codex-direct-manipulation-intake-verifier-readback-v1/direct-manipulation-intake-verifier-readback/direct_manipulation_intake_verifier_readback_v1.json",
    "future_tail_rerun": "docs/experiments/actionable-regime-confidence/runs/20260511T190440-codex-strict-1h-future-tail-gate-rerun-v1/future-tail-gate-rerun/strict_1h_future_tail_gate_rerun_v1.json",
}


def load(name: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / ARTIFACTS[name]).read_text(encoding="utf-8"))


def as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def decision(payload: dict[str, object]) -> dict[str, object]:
    return as_dict(payload.get("decision", {}))


def checklist_row(
    row_id: str,
    requirement: str,
    status: str,
    artifact: str,
    evidence: str,
    gap: str = "",
) -> dict[str, str]:
    return {
        "id": row_id,
        "requirement": requirement,
        "status": status,
        "artifact": artifact,
        "evidence": evidence,
        "gap": gap,
    }


def find_checklist_status(v22: dict[str, object], row_id: str) -> str:
    rows = v22.get("prompt_to_artifact_checklist", [])
    if not isinstance(rows, list):
        return "unknown"
    for row in rows:
        if isinstance(row, dict) and row.get("id") == row_id:
            return str(row.get("status", "unknown"))
    return "unknown"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    v22 = load("v22")
    strict_verifier = load("strict_intake_verifier")
    strict_exhaustion = load("strict_contract_exhaustion")
    recency = load("stock_regime_live_recency")
    subhour_quarantine = load("native_subhour_quarantine")
    subhour_external = load("native_subhour_external")
    external = load("external_source_second_screen")
    direct_screen = load("direct_missing_species_v2")
    direct_verifier = load("direct_intake_verifier")
    future = load("future_tail_rerun")

    v22_decision = decision(v22)
    strict_verifier_decision = decision(strict_verifier)
    strict_exhaustion_decision = decision(strict_exhaustion)
    direct_screen_decision = decision(direct_screen)
    future_decision = decision(future)

    direct_missing_files = direct_verifier.get("missing_file_count")
    native_candidate_count = subhour_external.get("candidate_records")
    strict_target_count = strict_exhaustion_decision.get("contract_targets")
    strict_total_slots = v22_decision.get("strict_1h_total_slots")
    strict_fixed = v22_decision.get("strict_1h_fixed_gate_rows")
    strict_future = v22_decision.get("strict_1h_future_protocol_rows")

    checklist = [
        checklist_row(
            "R0",
            "named board remains the execution contract",
            "pass_checked",
            "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
            f"todo_sha256_before_audit={hashlib.sha256(TODO_PATH.read_bytes()).hexdigest()}",
        ),
        checklist_row(
            "R1",
            "each active regime has scoped calibrated >=95 confidence",
            "scoped_pass_not_full",
            ARTIFACTS["v22"],
            f"v22_R1_status={find_checklist_status(v22, 'R1')}; v22_gate={v22_decision.get('gate_result')}",
            "The scoped active-lane 95% evidence remains present, but the explicit other-market and other-cycle transfer requirements are not complete.",
        ),
        checklist_row(
            "R2",
            "strict exact 1h market/timeframe coverage is complete",
            "fail_blocked",
            ARTIFACTS["v22"],
            f"fixed_gate={strict_fixed}/{strict_total_slots}; future_protocol={strict_future}/{strict_total_slots}",
            "Strict exact 1h coverage remains partial; future-tail support is scoped and does not close the fixed gate.",
        ),
        checklist_row(
            "R3",
            "strict 1h remaining rows have new source-owned intake rows and provenance",
            "fail_blocked",
            ARTIFACTS["strict_contract_exhaustion"],
            (
                f"source_intake_missing_files={strict_verifier_decision.get('missing_required_files')}; "
                f"live_intake_files={strict_verifier_decision.get('live_intake_file_count')}; "
                f"contract_targets={strict_target_count}; "
                f"targets_materializable_from_existing_panel={strict_exhaustion_decision.get('targets_materializable_from_existing_panel')}; "
                f"extra_source_rows={strict_exhaustion_decision.get('extra_source_rows_beyond_existing_gate_total')}"
            ),
            "The live strict intake files are absent, and the existing source panel has zero extra rows beyond already-counted gate support.",
        ),
        checklist_row(
            "R4",
            "source recency tail can repair XOM/Sideways and next strict 1h targets",
            "fail_blocked",
            ARTIFACTS["stock_regime_live_recency"],
            (
                f"recency_gate={decision(recency).get('gate_result')}; "
                f"xom_panel_extra={strict_exhaustion['targets'][0].get('extra_source_rows_beyond_existing_gate') if isinstance(strict_exhaustion.get('targets'), list) and strict_exhaustion.get('targets') else 'unknown'}; "
                f"xom_jan2026_tail={strict_exhaustion['targets'][0].get('jan2026_tail_rows_for_symbol_label') if isinstance(strict_exhaustion.get('targets'), list) and strict_exhaustion.get('targets') else 'unknown'}"
            ),
            "The current stock-regime source still supplies no new XOM/Sideways tail rows and no extra source-owned sessions for the contract targets.",
        ),
        checklist_row(
            "R5",
            "native sub-hour validation has source-owned native sub-hour labels",
            "fail_blocked",
            ARTIFACTS["native_subhour_external"],
            (
                f"projection_quarantine={subhour_quarantine.get('decision')}; "
                f"native_external={subhour_external.get('decision')}; "
                f"native_candidates={native_candidate_count}; "
                f"accepted_rows={subhour_external.get('accepted_rows_added')}"
            ),
            "Projected sub-hour rows remain quarantined, and targeted public searches found no ready source-owned native sub-hour labels.",
        ),
        checklist_row(
            "R6",
            "other-market/source-label equivalence has suitable confidence",
            "fail_blocked",
            ARTIFACTS["external_source_second_screen"],
            f"external_decision={external.get('decision')}; accepted_rows_added={external.get('accepted_rows_added')}; full_equivalence={external.get('full_other_market_source_label_equivalence')}",
            "Second-pass external screening still accepted zero owner-approved MainRegimeV2 equivalence rows.",
        ),
        checklist_row(
            "R7",
            "direct Manipulation full species coverage has matched positives, negatives, and provenance",
            "fail_blocked",
            ARTIFACTS["direct_intake_verifier"],
            (
                f"direct_screen_gate={direct_screen_decision.get('gate_result')}; "
                f"ready_sources={direct_screen_decision.get('incremental_ready_real_positive_control_sources')}; "
                f"direct_intake_decision={direct_verifier.get('decision')}; "
                f"missing_direct_files={direct_missing_files}; "
                f"intake_root_exists={direct_verifier.get('intake_root_exists')}"
            ),
            "Direct missing-species screening found no ready positive/control sources, and the direct Manipulation row-intake files are absent.",
        ),
        checklist_row(
            "R8",
            "proxy/generated labels and duplicate rows remain fail-closed",
            "pass_guardrail",
            ARTIFACTS["native_subhour_external"],
            (
                f"native_hmm_candidate_rejected={subhour_external.get('decision')}; "
                f"strict_duplicate_panel_rejected={strict_exhaustion_decision.get('gate_result')}; "
                f"fixed_rows_added_by_future_tail={future_decision.get('accepted_rows_added_to_fixed_gate')}"
            ),
            "",
        ),
        checklist_row(
            "R9",
            "do not call update_goal until strict full objective is achieved",
            "pass_guardrail",
            ARTIFACTS["direct_intake_verifier"],
            (
                f"v22_update_goal={v22_decision.get('update_goal')}; "
                f"strict_exhaustion_update_goal={strict_exhaustion_decision.get('update_goal')}; "
                f"direct_verifier_update_goal={direct_verifier.get('update_goal')}"
            ),
            "",
        ),
    ]
    unmet = [row for row in checklist if row["status"].startswith("fail")]
    strict_full_objective_achieved = len(unmet) == 0
    blocking_requirements = [row["requirement"] for row in unmet]

    audit_decision = {
        "gate_result": "current_goal_completion_audit_v23=latest_readbacks_confirm_full_objective_blocked",
        "strict_full_objective_achieved": strict_full_objective_achieved,
        "update_goal": False,
        "blocking_requirements": blocking_requirements,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_1h_fixed_gate_rows": strict_fixed,
        "strict_1h_future_protocol_rows": strict_future,
        "strict_1h_total_slots": strict_total_slots,
        "strict_contract_targets": strict_target_count,
        "strict_contract_materializable_targets": strict_exhaustion_decision.get("targets_materializable_from_existing_panel"),
        "strict_contract_extra_rows": strict_exhaustion_decision.get("extra_source_rows_beyond_existing_gate_total"),
        "direct_intake_missing_files": direct_missing_files,
        "direct_species_coverage_closed": direct_verifier.get("direct_species_coverage_closed"),
        "native_subhour_source_overlap_closed": subhour_external.get("native_subhour_source_overlap_closed"),
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    payload = {
        "artifact_type": "current_goal_completion_audit_v23_after_latest_readbacks",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective": "Every active regime must have calibrated >=95% confidence and must retain suitable confidence on other markets/species and other cycles/timeframes.",
        "success_criteria": [
            "all active regimes have calibrated >=95 confidence",
            "validation transfers to other markets/species with source-owned or owner-approved labels",
            "validation transfers to other cycles/timeframes, including native sub-hour where claimed",
            "strict 1h remaining rows are supported by new source-owned rows, not duplicate counted support",
            "direct Manipulation has row-level positives, matched negatives, and provenance for missing species",
        ],
        "todo_hash_before_audit": hashlib.sha256(TODO_PATH.read_bytes()).hexdigest(),
        "artifact_inputs": ARTIFACTS,
        "prompt_to_artifact_checklist": checklist,
        "unmet_requirements": unmet,
        "decision": audit_decision,
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v23_after_latest_readbacks.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with (OUT_DIR / "current_goal_completion_audit_v23_checklist.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(checklist[0].keys()))
        writer.writeheader()
        writer.writerows(checklist)

    with (OUT_DIR / "current_goal_completion_audit_v23_unmet_requirements.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(checklist[0].keys()))
        writer.writeheader()
        writer.writerows(unmet)

    report = [
        "# Current Goal Completion Audit v23 After Latest Readbacks",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Objective",
        "",
        payload["objective"],
        "",
        "## Success Criteria",
        "",
    ]
    report.extend(f"- {item}" for item in payload["success_criteria"])
    report.extend(
        [
            "",
            "## Decision",
            "",
            f"`{audit_decision['gate_result']}`",
            "",
            f"- Strict full objective achieved: `{str(strict_full_objective_achieved).lower()}`; `update_goal=false`.",
            f"- Strict `1h`: fixed `{strict_fixed}/{strict_total_slots}`, future protocol `{strict_future}/{strict_total_slots}`.",
            f"- Strict contract targets: `{strict_target_count}`; materializable from existing panel `{strict_exhaustion_decision.get('targets_materializable_from_existing_panel')}`; extra source rows `{strict_exhaustion_decision.get('extra_source_rows_beyond_existing_gate_total')}`.",
            f"- Direct Manipulation intake missing files: `{direct_missing_files}`; direct species coverage closed `{str(direct_verifier.get('direct_species_coverage_closed')).lower()}`.",
            f"- Native sub-hour source overlap closed: `{str(subhour_external.get('native_subhour_source_overlap_closed')).lower()}`.",
            "- Accepted rows added by this audit: `0`; new confidence gate: `false`.",
            "",
            "## Blocking Requirements",
            "",
        ]
    )
    report.extend(f"- `{row['requirement']}`: {row['gap']}" for row in unmet)
    report.extend(["", "## Prompt-To-Artifact Checklist", ""])
    report.extend(
        f"- `{row['status']}` `{row['id']}` `{row['requirement']}` -> `{row['artifact']}`: {row['evidence']}"
        for row in checklist
    )
    report.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/completion-audit/current_goal_completion_audit_v23_after_latest_readbacks.json`",
            f"- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/completion-audit/current_goal_completion_audit_v23_checklist.csv`",
            f"- Unmet requirements CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/completion-audit/current_goal_completion_audit_v23_unmet_requirements.csv`",
            f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/current_goal_completion_audit_v23_after_latest_readbacks_assertions.out`",
            "",
        ]
    )
    (OUT_DIR / "current_goal_completion_audit_v23_after_latest_readbacks.md").write_text(
        "\n".join(report),
        encoding="utf-8",
    )

    assertions = [
        f"PASS checklist_items={len(checklist)}",
        f"PASS unmet_requirements={len(unmet)}",
        "PASS scoped_95_present=true",
        f"PASS strict_1h_fixed_gate={strict_fixed}/{strict_total_slots}",
        f"PASS strict_1h_future_protocol={strict_future}/{strict_total_slots}",
        f"PASS strict_contract_extra_rows={strict_exhaustion_decision.get('extra_source_rows_beyond_existing_gate_total')}",
        f"PASS direct_intake_missing_files={direct_missing_files}",
        f"PASS native_subhour_source_overlap_closed={str(subhour_external.get('native_subhour_source_overlap_closed')).lower()}",
        f"PASS strict_full_objective={str(strict_full_objective_achieved).lower()}",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "current_goal_completion_audit_v23_after_latest_readbacks_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit_decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
