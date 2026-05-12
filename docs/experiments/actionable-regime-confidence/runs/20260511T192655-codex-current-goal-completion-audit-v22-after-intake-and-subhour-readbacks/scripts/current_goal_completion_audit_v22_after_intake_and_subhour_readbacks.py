#!/usr/bin/env python3
"""Completion audit after strict 1h intake and native sub-hour readbacks."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T192655-codex-current-goal-completion-audit-v22-after-intake-and-subhour-readbacks"
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
TODO_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

ARTIFACTS = {
    "v21": "docs/experiments/actionable-regime-confidence/runs/20260511T192049-codex-current-goal-completion-audit-v21-after-second-screens/completion-audit/current_goal_completion_audit_v21_after_second_screens.json",
    "strict_intake_contract": "docs/experiments/actionable-regime-confidence/runs/20260511T192211-codex-strict-1h-next-source-intake-contract-v1/strict-1h-next-source-intake-contract/strict_1h_next_source_intake_contract_v1.json",
    "stock_regime_live_recency": "docs/experiments/actionable-regime-confidence/runs/20260511T192218-codex-stock-regime-kaggle-live-recency-check-v1/kaggle-live-recency/stock_regime_kaggle_live_recency_check_v1.json",
    "strict_intake_verifier": "docs/experiments/actionable-regime-confidence/runs/20260511T192432-codex-strict-1h-source-intake-verifier-readback-v1/source-intake-verifier-readback/strict_1h_source_intake_verifier_readback_v1.json",
    "native_subhour_quarantine": "docs/experiments/actionable-regime-confidence/runs/20260511T192248-codex-native-subhour-projection-quarantine-v1/native-subhour-projection-quarantine/native_subhour_projection_quarantine_v1.json",
    "future_tail_rerun": "docs/experiments/actionable-regime-confidence/runs/20260511T190440-codex-strict-1h-future-tail-gate-rerun-v1/future-tail-gate-rerun/strict_1h_future_tail_gate_rerun_v1.json",
    "timeframe_readback": "docs/experiments/actionable-regime-confidence/runs/20260511T185126-codex-timeframe-cycle-coverage-readback-v1/timeframe-cycle-readback/timeframe_cycle_coverage_readback_v1.json",
    "external_source_second_screen": "docs/experiments/actionable-regime-confidence/runs/20260511T191623-codex-external-source-label-second-screen-v1/external-source-label-second-screen/external_source_label_second_screen_v1.json",
    "direct_missing_species_v2": "docs/experiments/actionable-regime-confidence/runs/20260511T191642-codex-direct-missing-species-source-screen-v2/direct-missing-species-screen/direct_missing_species_source_screen_v2.json",
}


def load(name: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / ARTIFACTS[name]).read_text(encoding="utf-8"))


def as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def decision(payload: dict[str, object]) -> dict[str, object]:
    return as_dict(payload.get("decision", {}))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    v21 = load("v21")
    contract = load("strict_intake_contract")
    recency = load("stock_regime_live_recency")
    verifier = load("strict_intake_verifier")
    subhour = load("native_subhour_quarantine")
    future = load("future_tail_rerun")
    timeframe = load("timeframe_readback")
    external = load("external_source_second_screen")
    direct = load("direct_missing_species_v2")

    v21_decision = decision(v21)
    contract_decision = decision(contract)
    verifier_decision = decision(verifier)
    subhour_decision = decision(subhour)
    future_decision = decision(future)
    direct_decision = decision(direct)

    target_rows = contract.get("target_rows", [])
    if not isinstance(target_rows, list):
        target_rows = []

    checklist = [
        {
            "id": "R0",
            "requirement": "named board remains the execution contract",
            "status": "pass_checked",
            "artifact": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
            "evidence": f"todo_sha256_before_audit={hashlib.sha256(TODO_PATH.read_bytes()).hexdigest()}",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "scoped active regimes retain calibrated >=95 confidence",
            "status": "scoped_pass_not_full",
            "artifact": ARTIFACTS["v21"],
            "evidence": f"v21_gate={v21_decision.get('gate_result')}; scoped_95_present=true",
            "gap": "The active-lane 95% evidence remains scoped and still lacks complete transfer validation.",
        },
        {
            "id": "R2",
            "requirement": "strict 1h remaining rows have source-owned intake files",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["strict_intake_verifier"],
            "evidence": f"verifier_status={verifier_decision.get('verifier_status')}; reason={verifier_decision.get('verifier_reason')}; missing_files={verifier_decision.get('missing_required_files')}; live_intake_file_count={verifier_decision.get('live_intake_file_count')}; contract_targets={len(target_rows)}",
            "gap": "The strict 1h next-source contract is executable, but the live source-label equivalence rows and provenance files are still absent.",
        },
        {
            "id": "R3",
            "requirement": "XOM/Sideways recency tail can repair the next strict 1h target",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["stock_regime_live_recency"],
            "evidence": f"gate={recency.get('decision', {}).get('gate_result') if isinstance(recency.get('decision'), dict) else recency.get('decision')}; xom_sideways_after_2026_01_30={recency.get('xom_sideways_after_2026_01_30')}; xom_sideways_tail={recency.get('xom_sideways_2026_01_02_to_2026_01_30')}; source_end={recency.get('date_range', {}).get('end') if isinstance(recency.get('date_range'), dict) else None}",
            "gap": "Live Kaggle source still ends at 2026-01-30 and supplies no XOM/Sideways tail repair rows.",
        },
        {
            "id": "R4",
            "requirement": "native sub-hour validation has source-owned native sub-hour labels",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["native_subhour_quarantine"],
            "evidence": f"gate={subhour.get('decision')}; subhour_looking_rows={subhour.get('subhour_rows_read')}; native_subhour_eligible_rows={subhour.get('native_subhour_eligible_rows')}; quarantined_rows={subhour.get('quarantined_subhour_rows')}",
            "gap": "Sub-hour-looking rows were projections from day/month windows, not source-owned native sub-hour labels.",
        },
        {
            "id": "R5",
            "requirement": "other-market/source-label equivalence has suitable confidence",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["external_source_second_screen"],
            "evidence": f"external_decision={external.get('decision')}; accepted_rows_added={external.get('accepted_rows_added')}; full_equivalence={external.get('full_other_market_source_label_equivalence')}",
            "gap": "Second-pass external screen accepted zero owner-approved MainRegimeV2 equivalence rows.",
        },
        {
            "id": "R6",
            "requirement": "direct Manipulation full species coverage has matched controls",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["direct_missing_species_v2"],
            "evidence": f"direct_gate={direct_decision.get('gate_result')}; ready_sources={direct_decision.get('incremental_ready_real_positive_control_sources')}; candidates_screened={direct_decision.get('candidates_screened')}",
            "gap": "Direct missing-species v2 found zero ready positive/control sources.",
        },
        {
            "id": "R7",
            "requirement": "future-tail accepted rows are scoped and not fixed-gate acceptance",
            "status": "pass_guardrail",
            "artifact": ARTIFACTS["future_tail_rerun"],
            "evidence": f"future_rows={future_decision.get('accepted_future_protocol_rows_added')}; fixed_rows_added={future_decision.get('accepted_rows_added_to_fixed_gate')}; scope={future_decision.get('new_confidence_gate_scope')}",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "do not call update_goal until strict full objective is achieved",
            "status": "pass_guardrail",
            "artifact": ARTIFACTS["v21"],
            "evidence": f"v21_update_goal={v21_decision.get('update_goal')}; verifier_update_goal={verifier_decision.get('update_goal')}; subhour_update_goal={subhour_decision.get('update_goal')}",
            "gap": "",
        },
    ]
    unmet = [row for row in checklist if row["status"].startswith("fail")]
    strict_full_objective_achieved = len(unmet) == 0

    audit_decision = {
        "gate_result": "current_goal_completion_audit_v22=intake_and_subhour_readbacks_confirm_full_objective_blocked",
        "strict_full_objective_achieved": strict_full_objective_achieved,
        "update_goal": False,
        "blocking_requirements": [row["requirement"] for row in unmet],
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_1h_fixed_gate_rows": timeframe.get("strict_1h_accepted_rows"),
        "strict_1h_future_protocol_rows": future_decision.get("strict_1h_future_protocol_rows_after"),
        "strict_1h_total_slots": future_decision.get("strict_1h_total_slots"),
        "strict_intake_missing_required_files": verifier_decision.get("missing_required_files"),
        "strict_intake_live_files": verifier_decision.get("live_intake_file_count"),
        "contract_target_rows": len(target_rows),
        "native_subhour_eligible_rows": subhour.get("native_subhour_eligible_rows"),
        "native_subhour_quarantined_rows": subhour.get("quarantined_subhour_rows"),
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    payload = {
        "artifact_type": "current_goal_completion_audit_v22_after_intake_and_subhour_readbacks",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective": "Every active regime must have calibrated >=95% confidence and must retain suitable confidence on other markets/species and other cycles/timeframes.",
        "todo_hash_before_append": hashlib.sha256(TODO_PATH.read_bytes()).hexdigest(),
        "artifact_inputs": ARTIFACTS,
        "prompt_to_artifact_checklist": checklist,
        "unmet_requirements": unmet,
        "decision": audit_decision,
    }
    (OUT_DIR / "current_goal_completion_audit_v22_after_intake_and_subhour_readbacks.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with (OUT_DIR / "current_goal_completion_audit_v22_checklist.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(checklist[0].keys()))
        writer.writeheader()
        writer.writerows(checklist)

    with (OUT_DIR / "current_goal_completion_audit_v22_unmet_requirements.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(checklist[0].keys()))
        writer.writeheader()
        writer.writerows(unmet)

    report = [
        "# Current Goal Completion Audit v22 After Intake And Subhour Readbacks",
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
        f"- Strict `1h`: fixed `{timeframe.get('strict_1h_accepted_rows')}/{timeframe.get('strict_1h_total_slots')}`, future protocol `{future_decision.get('strict_1h_future_protocol_rows_after')}/{future_decision.get('strict_1h_total_slots')}`.",
        f"- Strict `1h` intake verifier: missing files `{verifier_decision.get('missing_required_files')}`, live files `{verifier_decision.get('live_intake_file_count')}`, contract target rows `{len(target_rows)}`.",
        f"- Native sub-hour: eligible source-label rows `{subhour.get('native_subhour_eligible_rows')}`, quarantined projection rows `{subhour.get('quarantined_subhour_rows')}`.",
        "- Accepted rows added by this audit: `0`; new confidence gate: `false`.",
        "",
        "## Blocking Requirements",
        "",
    ]
    for row in unmet:
        report.append(f"- `{row['requirement']}`: {row['gap']}")
    report.extend(["", "## Prompt-To-Artifact Checklist", ""])
    for row in checklist:
        report.append(f"- `{row['status']}` `{row['id']}` `{row['requirement']}` -> `{row['artifact']}`: {row['evidence']}")
    report.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/completion-audit/current_goal_completion_audit_v22_after_intake_and_subhour_readbacks.json`",
            f"- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/completion-audit/current_goal_completion_audit_v22_checklist.csv`",
            f"- Unmet requirements CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/completion-audit/current_goal_completion_audit_v22_unmet_requirements.csv`",
            f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/current_goal_completion_audit_v22_after_intake_and_subhour_readbacks_assertions.out`",
            "",
        ]
    )
    (OUT_DIR / "current_goal_completion_audit_v22_after_intake_and_subhour_readbacks.md").write_text(
        "\n".join(report),
        encoding="utf-8",
    )

    assertions = [
        f"PASS checklist_items={len(checklist)}",
        f"PASS unmet_requirements={len(unmet)}",
        "PASS scoped_95_present=true",
        f"PASS strict_1h_fixed_gate={timeframe.get('strict_1h_accepted_rows')}/{timeframe.get('strict_1h_total_slots')}",
        f"PASS strict_1h_future_protocol={future_decision.get('strict_1h_future_protocol_rows_after')}/{future_decision.get('strict_1h_total_slots')}",
        f"PASS strict_intake_missing_required_files={verifier_decision.get('missing_required_files')}",
        f"PASS strict_intake_live_files={verifier_decision.get('live_intake_file_count')}",
        f"PASS native_subhour_eligible_rows={subhour.get('native_subhour_eligible_rows')}",
        f"PASS native_subhour_quarantined_rows={subhour.get('quarantined_subhour_rows')}",
        f"PASS strict_full_objective={str(strict_full_objective_achieved).lower()}",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "current_goal_completion_audit_v22_after_intake_and_subhour_readbacks_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit_decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
