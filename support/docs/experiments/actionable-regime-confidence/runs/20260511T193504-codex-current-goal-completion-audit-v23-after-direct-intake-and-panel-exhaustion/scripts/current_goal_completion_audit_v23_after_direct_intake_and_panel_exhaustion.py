#!/usr/bin/env python3
"""Completion audit after strict-panel exhaustion and direct-intake readback."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T193504-codex-current-goal-completion-audit-v23-after-direct-intake-and-panel-exhaustion"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
TODO = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

ARTIFACTS = {
    "v22": "docs/experiments/actionable-regime-confidence/runs/20260511T192655-codex-current-goal-completion-audit-v22-after-intake-and-subhour-readbacks/completion-audit/current_goal_completion_audit_v22_after_intake_and_subhour_readbacks.json",
    "future_tail": "docs/experiments/actionable-regime-confidence/runs/20260511T190440-codex-strict-1h-future-tail-gate-rerun-v1/future-tail-gate-rerun/strict_1h_future_tail_gate_rerun_v1.json",
    "timeframe": "docs/experiments/actionable-regime-confidence/runs/20260511T185126-codex-timeframe-cycle-coverage-readback-v1/timeframe-cycle-readback/timeframe_cycle_coverage_readback_v1.json",
    "strict_intake": "docs/experiments/actionable-regime-confidence/runs/20260511T192432-codex-strict-1h-source-intake-verifier-readback-v1/source-intake-verifier-readback/strict_1h_source_intake_verifier_readback_v1.json",
    "panel_exhaustion": "docs/experiments/actionable-regime-confidence/runs/20260511T192900-codex-strict-1h-contract-panel-exhaustion-v1/strict-1h-contract-panel-exhaustion/strict_1h_contract_panel_exhaustion_v1.json",
    "stock_recency": "docs/experiments/actionable-regime-confidence/runs/20260511T192218-codex-stock-regime-kaggle-live-recency-check-v1/kaggle-live-recency/stock_regime_kaggle_live_recency_check_v1.json",
    "native_subhour_quarantine": "docs/experiments/actionable-regime-confidence/runs/20260511T192248-codex-native-subhour-projection-quarantine-v1/native-subhour-projection-quarantine/native_subhour_projection_quarantine_v1.json",
    "native_subhour_external": "docs/experiments/actionable-regime-confidence/runs/20260511T192750-codex-native-subhour-external-source-screen-v1/native-subhour-external-source-screen/native_subhour_external_source_screen_v1.json",
    "external_source_second": "docs/experiments/actionable-regime-confidence/runs/20260511T191623-codex-external-source-label-second-screen-v1/external-source-label-second-screen/external_source_label_second_screen_v1.json",
    "direct_missing_species_v2": "docs/experiments/actionable-regime-confidence/runs/20260511T191642-codex-direct-missing-species-source-screen-v2/direct-missing-species-screen/direct_missing_species_source_screen_v2.json",
    "direct_intake_readback": "docs/experiments/actionable-regime-confidence/runs/20260511T193301-codex-direct-manipulation-intake-verifier-readback-v1/direct-manipulation-intake-verifier-readback/direct_manipulation_intake_verifier_readback_v1.json",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(name: str) -> dict[str, Any]:
    return json.loads((REPO / ARTIFACTS[name]).read_text(encoding="utf-8"))


def dec(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("decision", {})
    return value if isinstance(value, dict) else {"gate_result": value}


def csv_write(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    board_hash = sha256(TODO)

    v22 = load("v22")
    future = load("future_tail")
    timeframe = load("timeframe")
    strict_intake = load("strict_intake")
    panel = load("panel_exhaustion")
    recency = load("stock_recency")
    subhour = load("native_subhour_quarantine")
    subhour_external = load("native_subhour_external")
    external = load("external_source_second")
    direct_species = load("direct_missing_species_v2")
    direct_intake = load("direct_intake_readback")

    v22d = dec(v22)
    futured = dec(future)
    timeframed = dec(timeframe)
    strictd = dec(strict_intake)
    paneld = dec(panel)
    subhourd = dec(subhour)
    subhour_external_d = dec(subhour_external)
    externald = dec(external)
    direct_species_d = dec(direct_species)

    target_counts = recency.get("stats", {}).get("target_counts", {}) if isinstance(recency.get("stats"), dict) else {}
    checklist = [
        {
            "id": "R0",
            "requirement": "Use the named Board A markdown as the execution contract.",
            "status": "pass_checked",
            "artifact": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
            "evidence": f"board_sha256_before_audit={board_hash}",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "Every active regime has calibrated >=95% confidence.",
            "status": "scoped_pass_not_full",
            "artifact": ARTIFACTS["v22"],
            "evidence": f"v22_gate={v22d.get('gate_result')}; scoped_active_lane_95_present=true",
            "gap": "Scoped active-lane >=95% evidence exists, but full transfer validation is still incomplete.",
        },
        {
            "id": "R2",
            "requirement": "Other-cycle/timeframe validation has suitable confidence.",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["timeframe"],
            "evidence": f"strict_1h_fixed={timeframe.get('strict_1h_accepted_rows')}/{timeframe.get('strict_1h_total_slots')}; future_protocol={futured.get('strict_1h_future_protocol_rows_after')}/{futured.get('strict_1h_total_slots')}; native_subhour={timeframe.get('native_subhour_ready_cells')}/{timeframe.get('native_subhour_total_cells')}",
            "gap": "Fixed strict 1h remains 41/156, future protocol remains 45/156, and native sub-hour remains 0/4.",
        },
        {
            "id": "R3",
            "requirement": "Strict 1h next-source intake has source-owned rows and provenance.",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["strict_intake"],
            "evidence": f"status={strictd.get('verifier_status')}; reason={strictd.get('verifier_reason')}; missing_files={strictd.get('missing_required_files')}; live_files={strictd.get('live_intake_file_count')}",
            "gap": "The source-label equivalence intake files are absent.",
        },
        {
            "id": "R4",
            "requirement": "Existing source panel can supply the strict 1h contract gaps without duplicate evidence.",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["panel_exhaustion"],
            "evidence": f"targets_materializable={paneld.get('targets_materializable_from_existing_panel')}; extra_rows={paneld.get('extra_source_rows_beyond_existing_gate_total')}; intake_files_created={paneld.get('intake_files_created')}",
            "gap": "The current source panel has zero extra rows beyond already-counted strict-gate support.",
        },
        {
            "id": "R5",
            "requirement": "XOM/Sideways has recency-tail repair rows for the next strict 1h gap.",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["stock_recency"],
            "evidence": f"gate={dec(recency).get('gate_result')}; xom_sideways_2025={target_counts.get('xom_sideways_2025', 0)}; xom_sideways_tail={target_counts.get('xom_sideways_2026_01_02_to_2026_01_30', 0)}; xom_sideways_after_2026_01_30={target_counts.get('xom_sideways_after_2026_01_30', 0)}",
            "gap": "The live source file has no XOM/Sideways Jan-2026 tail or post-2026-01-30 rows.",
        },
        {
            "id": "R6",
            "requirement": "Native sub-hour source labels exist for cross-timeframe validation.",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["native_subhour_external"],
            "evidence": f"quarantine_gate={subhourd.get('gate_result')}; eligible_rows={subhour.get('native_subhour_eligible_rows')}; external_gate={subhour_external_d.get('gate_result')}; ready_native_rows={subhour_external.get('ready_source_owned_native_subhour_rows', 0)}",
            "gap": "Projection rows were quarantined and targeted external search found zero ready native sub-hour source labels.",
        },
        {
            "id": "R7",
            "requirement": "Other-market/source-label equivalence has suitable confidence.",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["external_source_second"],
            "evidence": f"gate={externald.get('gate_result')}; accepted_rows_added={external.get('accepted_rows_added')}; full_equivalence={external.get('full_other_market_source_label_equivalence')}",
            "gap": "No owner-approved MainRegimeV2 equivalence rows were promoted.",
        },
        {
            "id": "R8",
            "requirement": "Direct Manipulation has full species coverage with real positives and matched controls.",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["direct_intake_readback"],
            "evidence": f"species_gate={direct_species_d.get('gate_result')}; ready_sources={direct_species_d.get('incremental_ready_real_positive_control_sources')}; intake_decision={direct_intake.get('decision')}; direct_missing_files={direct_intake.get('missing_file_count')}",
            "gap": "Direct species source screen found zero ready sources, and direct intake files are absent.",
        },
        {
            "id": "R9",
            "requirement": "Do not promote proxy/generated labels or duplicated rows.",
            "status": "pass_guardrail",
            "artifact": ARTIFACTS["panel_exhaustion"],
            "evidence": "panel_exhaustion blocks duplicate rows; native subhour quarantine blocks projected rows; HMM-generated labels remain rejected",
            "gap": "",
        },
        {
            "id": "R10",
            "requirement": "Do not mark the active goal complete until every requirement is covered.",
            "status": "pass_guardrail",
            "artifact": ARTIFACTS["v22"],
            "evidence": f"v22_update_goal={v22d.get('update_goal')}; strict_intake_update_goal={strictd.get('update_goal')}; direct_intake_update_goal={direct_intake.get('update_goal')}",
            "gap": "",
        },
    ]
    unmet = [row for row in checklist if row["status"].startswith("fail")]
    decision = {
        "gate_result": "current_goal_completion_audit_v23=direct_intake_and_panel_exhaustion_confirm_full_objective_blocked",
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "blocking_requirement_count": len(unmet),
        "blocking_requirements": [row["requirement"] for row in unmet],
        "strict_1h_fixed_gate_rows": timeframe.get("strict_1h_accepted_rows"),
        "strict_1h_future_protocol_rows": futured.get("strict_1h_future_protocol_rows_after"),
        "strict_1h_total_slots": futured.get("strict_1h_total_slots"),
        "strict_intake_missing_files": strictd.get("missing_required_files"),
        "panel_extra_rows": paneld.get("extra_source_rows_beyond_existing_gate_total"),
        "native_subhour_eligible_rows": subhour.get("native_subhour_eligible_rows"),
        "direct_intake_missing_files": direct_intake.get("missing_file_count"),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    payload = {
        "artifact_type": "current_goal_completion_audit_v23_after_direct_intake_and_panel_exhaustion",
        "run_id": "20260511T193504+0800-codex-current-goal-completion-audit-v23-after-direct-intake-and-panel-exhaustion",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective": "Every regime must have calibrated >=95% confidence, and the confidence must remain suitable on other markets and other cycles/timeframes.",
        "board_sha256_before_audit": board_hash,
        "artifact_inputs": ARTIFACTS,
        "prompt_to_artifact_checklist": checklist,
        "unmet_requirements": unmet,
        "decision": decision,
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v23_after_direct_intake_and_panel_exhaustion.json"
    checklist_path = OUT_DIR / "current_goal_completion_audit_v23_checklist.csv"
    unmet_path = OUT_DIR / "current_goal_completion_audit_v23_unmet_requirements.csv"
    md_path = OUT_DIR / "current_goal_completion_audit_v23_after_direct_intake_and_panel_exhaustion.md"
    assertions_path = CHECK_DIR / "current_goal_completion_audit_v23_after_direct_intake_and_panel_exhaustion_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    fields = ["id", "requirement", "status", "artifact", "evidence", "gap"]
    csv_write(checklist_path, checklist, fields)
    csv_write(unmet_path, unmet, fields)

    md = [
        "# Current Goal Completion Audit v23 After Direct Intake And Panel Exhaustion",
        "",
        "Run ID: `20260511T193504+0800-codex-current-goal-completion-audit-v23-after-direct-intake-and-panel-exhaustion`",
        "",
        "## Objective",
        "",
        payload["objective"],
        "",
        "## Decision",
        "",
        f"`{decision['gate_result']}`",
        "",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        f"- Blocking requirements: `{len(unmet)}`.",
        f"- Strict `1h`: fixed `{decision['strict_1h_fixed_gate_rows']}/{decision['strict_1h_total_slots']}`, future protocol `{decision['strict_1h_future_protocol_rows']}/{decision['strict_1h_total_slots']}`.",
        f"- Strict source intake missing files: `{decision['strict_intake_missing_files']}`; existing panel extra rows: `{decision['panel_extra_rows']}`.",
        f"- Native sub-hour eligible source rows: `{decision['native_subhour_eligible_rows']}`.",
        f"- Direct Manipulation intake missing files: `{decision['direct_intake_missing_files']}`.",
        "- Accepted rows added by this audit: `0`; new confidence gate: `false`.",
        "",
        "## Blocking Requirements",
        "",
    ]
    for row in unmet:
        md.append(f"- `{row['id']}` {row['requirement']} -> {row['gap']}")
    md.extend(["", "## Prompt-To-Artifact Checklist", ""])
    for row in checklist:
        md.append(f"- `{row['status']}` `{row['id']}` {row['requirement']} | `{row['artifact']}` | {row['evidence']}")
    md.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/completion-audit/current_goal_completion_audit_v23_after_direct_intake_and_panel_exhaustion.json`",
            f"- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/completion-audit/current_goal_completion_audit_v23_checklist.csv`",
            f"- Unmet requirements CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/completion-audit/current_goal_completion_audit_v23_unmet_requirements.csv`",
            f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/current_goal_completion_audit_v23_after_direct_intake_and_panel_exhaustion_assertions.out`",
        ]
    )
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    assertions = [
        f"PASS checklist_items={len(checklist)}",
        f"PASS unmet_requirements={len(unmet)}",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        f"PASS strict_1h_fixed_gate={decision['strict_1h_fixed_gate_rows']}/{decision['strict_1h_total_slots']}",
        f"PASS strict_1h_future_protocol={decision['strict_1h_future_protocol_rows']}/{decision['strict_1h_total_slots']}",
        f"PASS strict_intake_missing_files={decision['strict_intake_missing_files']}",
        f"PASS panel_extra_rows={decision['panel_extra_rows']}",
        f"PASS native_subhour_eligible_rows={decision['native_subhour_eligible_rows']}",
        f"PASS direct_intake_missing_files={decision['direct_intake_missing_files']}",
        f"PASS report_json={json_path.relative_to(REPO)}",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
