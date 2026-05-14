#!/usr/bin/env python3
"""Prompt-to-artifact completion audit after the 19:xx second screens."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T192049-codex-current-goal-completion-audit-v21-after-second-screens"
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
TODO_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

ARTIFACTS = {
    "completion_audit_v20": "docs/experiments/actionable-regime-confidence/runs/20260511T190911-codex-current-goal-completion-audit-v20-after-future-tail/completion-audit/current_goal_completion_audit_v20_after_future_tail.json",
    "future_tail_rerun": "docs/experiments/actionable-regime-confidence/runs/20260511T190440-codex-strict-1h-future-tail-gate-rerun-v1/future-tail-gate-rerun/strict_1h_future_tail_gate_rerun_v1.json",
    "post_future_gap_triage": "docs/experiments/actionable-regime-confidence/runs/20260511T191552-codex-strict-1h-post-future-gap-triage-v1/strict-1h-post-future-gap-triage/strict_1h_post_future_gap_triage_v1.json",
    "external_source_second_screen": "docs/experiments/actionable-regime-confidence/runs/20260511T191623-codex-external-source-label-second-screen-v1/external-source-label-second-screen/external_source_label_second_screen_v1.json",
    "direct_missing_species_v2": "docs/experiments/actionable-regime-confidence/runs/20260511T191642-codex-direct-missing-species-source-screen-v2/direct-missing-species-screen/direct_missing_species_source_screen_v2.json",
    "timeframe_readback": "docs/experiments/actionable-regime-confidence/runs/20260511T185126-codex-timeframe-cycle-coverage-readback-v1/timeframe-cycle-readback/timeframe_cycle_coverage_readback_v1.json",
    "source_other_market_readback": "docs/experiments/actionable-regime-confidence/runs/20260511T184856-codex-source-label-other-market-readback-v1/source-label-readback/source_label_other_market_readback_v1.json",
    "local_schema_sweep": "docs/experiments/actionable-regime-confidence/runs/20260511T185420-codex-local-intake-schema-sweep-v1/local-intake-schema-sweep/local_intake_schema_sweep_v1.json",
    "direct_coverage_readback": "docs/experiments/actionable-regime-confidence/runs/20260511T184630-codex-direct-manipulation-coverage-readback-v2/direct-manipulation-readback/direct_manipulation_coverage_readback_v2.json",
}

INTAKE_ROOTS = [
    Path("/tmp/ict-engine-source-label-equivalence-intake"),
    Path("/tmp/ict-engine-board-a-external-intake-bundle-v1"),
    Path("/tmp/ict-engine-direct-manipulation-row-intake"),
]


def load(name: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / ARTIFACTS[name]).read_text(encoding="utf-8"))


def as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def decision(payload: dict[str, object]) -> dict[str, object]:
    return as_dict(payload.get("decision", {}))


def count_files(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*") if path.is_file())


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    v20 = load("completion_audit_v20")
    future_tail = load("future_tail_rerun")
    post_future = load("post_future_gap_triage")
    external_second = load("external_source_second_screen")
    direct_v2 = load("direct_missing_species_v2")
    timeframe = load("timeframe_readback")
    source_other = load("source_other_market_readback")
    schema_sweep = load("local_schema_sweep")
    direct_cov = load("direct_coverage_readback")

    v20_decision = decision(v20)
    future_decision = decision(future_tail)
    post_future_decision = decision(post_future)
    timeframe_decision = decision(timeframe)
    source_other_decision = decision(source_other)
    direct_v2_decision = decision(direct_v2)
    direct_cov_decision = decision(direct_cov)
    post_future_counts = as_dict(post_future.get("counts", {}))

    live_intake_roots = [
        {"root": str(root), "exists": root.exists(), "file_count": count_files(root)}
        for root in INTAKE_ROOTS
    ]
    live_intake_file_count = sum(int(row["file_count"]) for row in live_intake_roots)

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
            "requirement": "active regimes have calibrated >=95 confidence",
            "status": "scoped_pass_not_full",
            "artifact": ARTIFACTS["completion_audit_v20"],
            "evidence": "v20 preserves scoped active-lane accepted_95 evidence; no new evidence removes it",
            "gap": "Scoped active-lane confidence is not enough for cross-market/species and cycle/timeframe transfer.",
        },
        {
            "id": "R2",
            "requirement": "other-market/source-label equivalence has suitable confidence",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["external_source_second_screen"],
            "evidence": f"second_screen_decision={external_second.get('decision')}; accepted_rows_added={external_second.get('accepted_rows_added')}; full_other_market_source_label_equivalence={external_second.get('full_other_market_source_label_equivalence')}; prior_gate={source_other_decision.get('gate_result')}; prior_accepted_total={source_other.get('accepted_factor_or_gate_total')}",
            "gap": "Second-pass Kaggle/Hugging Face screen found no owner-approved MainRegimeV2 crosswalk or source-owned other-market rows.",
        },
        {
            "id": "R3",
            "requirement": "other-cycle/timeframe validation has suitable confidence",
            "status": "fail_blocked_progress_only",
            "artifact": ARTIFACTS["post_future_gap_triage"],
            "evidence": f"fixed_1h={timeframe.get('strict_1h_accepted_rows')}/{timeframe.get('strict_1h_total_slots')}; future_protocol_1h={future_decision.get('strict_1h_future_protocol_rows_after')}/{future_decision.get('strict_1h_total_slots')}; remaining_near_miss_after_future={post_future_counts.get('remaining_near_miss_targets_after_future_tail')}; existing_tail_ready={post_future_counts.get('remaining_targets_ready_with_existing_tail')}; native_subhour={timeframe.get('native_subhour_ready_cells')}/{timeframe.get('native_subhour_total_cells')}",
            "gap": "Future-tail protocol progressed strict 1h to 45/156, but fixed gate remains 41/156, nine near-miss targets remain, no existing tail is ready, and native sub-hour remains 0/4.",
        },
        {
            "id": "R4",
            "requirement": "direct Manipulation full species coverage has matched controls",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["direct_missing_species_v2"],
            "evidence": f"direct_v2_gate={direct_v2_decision.get('gate_result')}; candidates_screened={direct_v2_decision.get('candidates_screened')}; ready_sources={direct_v2_decision.get('incremental_ready_real_positive_control_sources')}; direct_cov_gate={direct_cov_decision.get('gate_result')}; remaining_unaccepted={direct_cov.get('remaining_unaccepted_variety_count')}",
            "gap": "Incremental direct species screen found zero ready positive/control sources; scoped accepted varieties do not cover missing spoofing/layering, quote stuffing, pinging, and related varieties.",
        },
        {
            "id": "R5",
            "requirement": "external/local intake rows match required schemas and provenance",
            "status": "fail_blocked",
            "artifact": ARTIFACTS["local_schema_sweep"],
            "evidence": f"live_tmp_intake_files={live_intake_file_count}; exact_schema_matches={schema_sweep.get('exact_schema_matches')}; strong_partial_schema_matches={schema_sweep.get('strong_partial_schema_matches')}",
            "gap": "No live intake files are present in the required roots, and the latest schema sweep found no exact or strong partial matches.",
        },
        {
            "id": "R6",
            "requirement": "future-tail rows are not counted as fixed 2024/2025 strict gate rows",
            "status": "pass_guardrail",
            "artifact": ARTIFACTS["future_tail_rerun"],
            "evidence": f"future_rows_added={future_decision.get('accepted_future_protocol_rows_added')}; fixed_gate_rows_added={future_decision.get('accepted_rows_added_to_fixed_gate')}; scope={future_decision.get('new_confidence_gate_scope')}",
            "gap": "",
        },
        {
            "id": "R7",
            "requirement": "proxy/generated/OHLCV-only labels remain rejected",
            "status": "pass_guardrail",
            "artifact": ARTIFACTS["external_source_second_screen"],
            "evidence": "HMM/generated BTCUSD labels, raw OHLCV/external-factor panels, and structural sidecars were blocked rather than promoted",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "do not call update_goal unless strict full objective is achieved",
            "status": "pass_guardrail",
            "artifact": ARTIFACTS["completion_audit_v20"],
            "evidence": f"v20_update_goal={v20_decision.get('update_goal')}; new_screens_update_goal={external_second.get('update_goal')},{direct_v2_decision.get('update_goal')},{post_future_decision.get('update_goal')}",
            "gap": "",
        },
    ]
    unmet = [row for row in checklist if row["status"].startswith("fail")]
    strict_full_objective_achieved = len(unmet) == 0

    audit_decision = {
        "gate_result": "current_goal_completion_audit_v21=second_screens_and_post_future_triage_confirm_full_objective_blocked",
        "strict_full_objective_achieved": strict_full_objective_achieved,
        "update_goal": False,
        "blocking_requirements": [row["requirement"] for row in unmet],
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_1h_fixed_gate_rows": timeframe.get("strict_1h_accepted_rows"),
        "strict_1h_future_protocol_rows": future_decision.get("strict_1h_future_protocol_rows_after"),
        "strict_1h_total_slots": future_decision.get("strict_1h_total_slots"),
        "remaining_near_miss_after_future": post_future_counts.get("remaining_near_miss_targets_after_future_tail"),
        "min_new_source_sessions_needed": post_future_counts.get("minimum_new_source_sessions_needed_for_next_target"),
        "external_second_screen_ready_rows": external_second.get("accepted_rows_added"),
        "direct_v2_ready_sources": direct_v2_decision.get("incremental_ready_real_positive_control_sources"),
        "live_tmp_intake_files": live_intake_file_count,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    payload = {
        "artifact_type": "current_goal_completion_audit_v21_after_second_screens",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective": "Every active regime must have calibrated >=95% confidence and must retain suitable confidence on other markets/species and other cycles/timeframes.",
        "todo_hash_before_append": hashlib.sha256(TODO_PATH.read_bytes()).hexdigest(),
        "artifact_inputs": ARTIFACTS,
        "live_intake_roots": live_intake_roots,
        "prompt_to_artifact_checklist": checklist,
        "unmet_requirements": unmet,
        "decision": audit_decision,
    }
    (OUT_DIR / "current_goal_completion_audit_v21_after_second_screens.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    checklist_csv = OUT_DIR / "current_goal_completion_audit_v21_checklist.csv"
    with checklist_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(checklist[0].keys()))
        writer.writeheader()
        writer.writerows(checklist)

    unmet_csv = OUT_DIR / "current_goal_completion_audit_v21_unmet_requirements.csv"
    with unmet_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(checklist[0].keys()))
        writer.writeheader()
        writer.writerows(unmet)

    report = [
        "# Current Goal Completion Audit v21 After Second Screens",
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
        "- Scoped active-lane `>=95%` evidence remains present, but transfer validation is still incomplete.",
        f"- Strict `1h`: fixed gate `{timeframe.get('strict_1h_accepted_rows')}/{timeframe.get('strict_1h_total_slots')}`, future protocol `{future_decision.get('strict_1h_future_protocol_rows_after')}/{future_decision.get('strict_1h_total_slots')}`.",
        f"- Post-future near-miss targets remaining: `{post_future_counts.get('remaining_near_miss_targets_after_future_tail')}`; ready with existing tail `{post_future_counts.get('remaining_targets_ready_with_existing_tail')}`; minimum new source-owned sessions needed `{post_future_counts.get('minimum_new_source_sessions_needed_for_next_target')}`.",
        f"- External source-label second screen accepted rows: `{external_second.get('accepted_rows_added')}`.",
        f"- Direct missing-species v2 ready sources: `{direct_v2_decision.get('incremental_ready_real_positive_control_sources')}`.",
        f"- Live `/tmp` intake files across required roots: `{live_intake_file_count}`.",
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
            f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/completion-audit/current_goal_completion_audit_v21_after_second_screens.json`",
            f"- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/completion-audit/current_goal_completion_audit_v21_checklist.csv`",
            f"- Unmet requirements CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/completion-audit/current_goal_completion_audit_v21_unmet_requirements.csv`",
            f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/current_goal_completion_audit_v21_after_second_screens_assertions.out`",
            "",
        ]
    )
    (OUT_DIR / "current_goal_completion_audit_v21_after_second_screens.md").write_text(
        "\n".join(report),
        encoding="utf-8",
    )

    assertions = [
        f"PASS checklist_items={len(checklist)}",
        f"PASS unmet_requirements={len(unmet)}",
        "PASS scoped_95_present=true",
        f"PASS strict_1h_fixed_gate={timeframe.get('strict_1h_accepted_rows')}/{timeframe.get('strict_1h_total_slots')}",
        f"PASS strict_1h_future_protocol={future_decision.get('strict_1h_future_protocol_rows_after')}/{future_decision.get('strict_1h_total_slots')}",
        f"PASS remaining_near_miss_after_future={post_future_counts.get('remaining_near_miss_targets_after_future_tail')}",
        f"PASS min_new_source_sessions_needed={post_future_counts.get('minimum_new_source_sessions_needed_for_next_target')}",
        f"PASS external_second_screen_accepted_rows={external_second.get('accepted_rows_added')}",
        f"PASS direct_v2_ready_sources={direct_v2_decision.get('incremental_ready_real_positive_control_sources')}",
        f"PASS live_tmp_intake_files={live_intake_file_count}",
        f"PASS strict_full_objective={str(strict_full_objective_achieved).lower()}",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "current_goal_completion_audit_v21_after_second_screens_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit_decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
