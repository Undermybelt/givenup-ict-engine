#!/usr/bin/env python3
"""Prompt-to-artifact completion audit after post-v26 intake and tail rechecks."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T201254-codex-current-goal-completion-audit-v27-after-live-intake-and-tail-rechecks"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
REPO_ROOT = Path.cwd()

V26 = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T200319-codex-current-goal-completion-audit-v26-after-sapienza-gate/completion-audit/current_goal_completion_audit_v26_after_sapienza_gate.json"
SAP_GATE = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T195945-codex-sapienza-pumpdump-control-gate-v1/sapienza-pumpdump-control-gate/sapienza_pumpdump_control_gate_v1.json"
SOURCE_RECHECK = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T200347-codex-spoofing-layering-current-source-recheck-v1/spoofing-layering-current-source-recheck/spoofing_layering_current_source_recheck_v1.json"
LIVE_INTAKE = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T200951-codex-live-intake-verifier-recheck-v2-after-v26/live-intake-verifier-recheck/live_intake_verifier_recheck_v2_after_v26.json"
RECENCY_TAIL = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T200909-codex-strict-1h-recency-tail-current-source-recheck-v1/recency-tail-current-source-recheck/strict_1h_recency_tail_current_source_recheck_v1.json"
ACQUISITION_SCREEN = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T200726-codex-spoofing-layering-source-acquisition-screen-v1/spoofing-layering-source-acquisition-screen/spoofing_layering_source_acquisition_screen_v1.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    v26 = load(V26)
    sap = load(SAP_GATE)
    source_recheck = load(SOURCE_RECHECK)
    live_intake = load(LIVE_INTAKE)
    recency_tail = load(RECENCY_TAIL)
    acquisition = load(ACQUISITION_SCREEN)

    tail_zero_rows = {
        f"{row['ticker']}/{row['regime_label']}": row["rows_after_2026_01_30"]
        for row in recency_tail["target_rows"]
    }
    missing_direct_files = live_intake["direct_manipulation_recheck"]["stdout_json"]["missing_files"]
    missing_equivalence_files = live_intake["source_label_recheck"]["stdout_json"]["missing_files"]

    checklist = [
        {
            "id": "R0",
            "requirement": "Use the named Board A markdown as the execution contract and write results back there.",
            "status": "pass_checked",
            "artifact": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
            "evidence": "Board cursor and ledger were re-read; this v27 audit is generated under docs/experiments for the same board.",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "Every active regime has calibrated >=95% confidence.",
            "status": "pass_scoped_not_full",
            "artifact": f"{rel(SAP_GATE)}; {rel(V26)}",
            "evidence": f"Scoped active-lane 95% evidence persists; Sapienza pump/dump adds {sap['accepted_rows_added']} event groups with min split Wilson95 LCB {sap['min_split_wilson95_lcb']:.12f}.",
            "gap": "This remains scoped evidence, not strict full-market/full-cycle/full-species closure.",
        },
        {
            "id": "R2",
            "requirement": "The 95% regime result transfers to other markets/species using source-owned or owner-approved labels.",
            "status": "fail_blocked",
            "artifact": rel(LIVE_INTAKE),
            "evidence": f"Source-label equivalence verifier status={live_intake['source_label_status']}; missing files={len(missing_equivalence_files)}.",
            "gap": "No source_label_equivalence_rows.csv or provenance file is present; no other-market/source-label equivalence can be accepted.",
        },
        {
            "id": "R3",
            "requirement": "The 95% regime result transfers to other cycles/timeframes, including native sub-hour source labels.",
            "status": "fail_blocked",
            "artifact": rel(V26),
            "evidence": "v26 still carries native sub-hour and strict timeframe blockers; no post-v26 artifact supplies native sub-hour source-owned labels.",
            "gap": "Native sub-hour price-root source labels remain missing.",
        },
        {
            "id": "R4",
            "requirement": "Strict exact 1h remaining slots have source-owned rows and provenance.",
            "status": "fail_blocked",
            "artifact": rel(LIVE_INTAKE),
            "evidence": f"Intake files present under checked /tmp roots={live_intake['intake_files_present']}; source-label verifier remains blocked.",
            "gap": "Strict exact 1h row/provenance intake is still absent.",
        },
        {
            "id": "R5",
            "requirement": "Strict 1h recency-tail targets after 2026-01-30 are repaired with source-owned labels.",
            "status": "fail_blocked",
            "artifact": rel(RECENCY_TAIL),
            "evidence": f"Recency gate={recency_tail['gate_result']}; rows_after_2026_01_30={tail_zero_rows}; ready_external_tail_sources={recency_tail['ready_external_tail_sources']}.",
            "gap": "XOM/Sideways, UNH/Bear, ^DJI/Sideways, and AMD/Bear still have zero post-cutoff source rows.",
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation has source-owned row-level positives, matched controls, and provenance across required species.",
            "status": "partial_still_blocked",
            "artifact": f"{rel(SOURCE_RECHECK)}; {rel(ACQUISITION_SCREEN)}; {rel(LIVE_INTAKE)}",
            "evidence": f"Pump/dump scoped gate remains accepted, but source_recheck={source_recheck['decision']['gate_result']}; acquisition_screen={acquisition['decision']}; direct_intake_status={live_intake['direct_manipulation_status']}; missing_direct_files={len(missing_direct_files)}.",
            "gap": "Spoofing/layering, quote stuffing, pinging, bear raid, and painting tape still lack acceptable positive/control row packages.",
        },
        {
            "id": "R7",
            "requirement": "No proxy, generated, synthetic, future-return, duplicated, or OHLCV-only labels are promoted.",
            "status": "pass_guardrail",
            "artifact": f"{rel(ACQUISITION_SCREEN)}; {rel(RECENCY_TAIL)}",
            "evidence": "Post-v26 screens keep proprietary, synthetic, simulated, metadata-only, and public-doc-only sources fail-closed; thresholds_relaxed=false and raw_data_committed=false.",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "Mark the goal complete only if every explicit requirement is covered by real evidence.",
            "status": "fail_blocked",
            "artifact": rel(RUN_ROOT),
            "evidence": "R2, R3, R4, R5, and R6 remain uncovered or partial after the post-v26 evidence.",
            "gap": "Strict full objective is not achieved; update_goal must remain false.",
        },
    ]
    unmet = [row for row in checklist if row["status"] in {"fail_blocked", "partial_still_blocked"}]
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": (
            "Every active regime in Board A must have calibrated >=95% confidence, and the same regime "
            "confidence must remain suitable across other markets/species and other cycles/timeframes before reporting completion."
        ),
        "decision": "current_goal_completion_audit_v27=post_v26_rechecks_confirm_strict_full_objective_blocked",
        "checklist_rows": len(checklist),
        "unmet_rows": len(unmet),
        "unmet_ids": [row["id"] for row in unmet],
        "post_v26_artifacts_checked": [
            rel(SOURCE_RECHECK),
            rel(LIVE_INTAKE),
            rel(RECENCY_TAIL),
            rel(ACQUISITION_SCREEN),
        ],
        "v26_prior_decision": v26["decision"],
        "new_confidence_gate_since_v26": False,
        "accepted_rows_added_since_v26": 0,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "checklist": checklist,
    }

    (OUT_DIR / "current_goal_completion_audit_v27_after_live_intake_and_tail_rechecks.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    write_csv(
        OUT_DIR / "current_goal_completion_audit_v27_checklist.csv",
        checklist,
        ["id", "requirement", "status", "artifact", "evidence", "gap"],
    )
    write_csv(
        OUT_DIR / "current_goal_completion_audit_v27_unmet_requirements.csv",
        unmet,
        ["id", "requirement", "status", "artifact", "evidence", "gap"],
    )

    md_lines = [
        "# Current Goal Completion Audit v27 After Live Intake And Tail Rechecks",
        "",
        f"- Decision: `{result['decision']}`",
        f"- Checklist rows: `{len(checklist)}`",
        f"- Unmet rows: `{len(unmet)}`",
        f"- Unmet ids: `{', '.join(result['unmet_ids'])}`",
        "- New confidence gate since v26: `false`",
        "- Accepted rows added since v26: `0`",
        "- Strict full objective achieved: `false`; `update_goal=false`",
        "",
        "## Objective Restatement",
        "",
        result["objective_restatement"],
        "",
        "## Post-v26 Evidence Checked",
        "",
    ]
    md_lines.extend(f"- `{path}`" for path in result["post_v26_artifacts_checked"])
    md_lines.extend(
        [
            "",
            "## Prompt-to-Artifact Checklist",
            "",
            "| ID | Status | Evidence | Gap |",
            "|---|---|---|---|",
        ]
    )
    for row in checklist:
        md_lines.append(f"| `{row['id']}` | `{row['status']}` | {row['evidence']} | {row['gap']} |")
    md_lines.extend(
        [
            "",
            "## Decision",
            "",
            "The post-v26 evidence does not close the strict objective. It confirms the same hard blockers: source-label equivalence intake is missing, native sub-hour/strict `1h` transfer evidence is missing, recency-tail rows remain absent after `2026-01-30`, and direct `Manipulation` still lacks source-owned spoofing/layering plus other species positive/control row packages.",
        ]
    )
    (OUT_DIR / "current_goal_completion_audit_v27_after_live_intake_and_tail_rechecks.md").write_text(
        "\n".join(md_lines) + "\n"
    )

    assert result["new_confidence_gate_since_v26"] is False
    assert result["accepted_rows_added_since_v26"] == 0
    assert result["strict_full_objective_achieved"] is False
    assert result["update_goal"] is False
    assert set(result["unmet_ids"]) == {"R2", "R3", "R4", "R5", "R6", "R8"}
    assert live_intake["source_label_status"] == "blocked"
    assert live_intake["direct_manipulation_status"] == "blocked"
    assert recency_tail["all_tail_rows_present"] is False
    assert acquisition["ready_positive_control_sources"] == 0

    (CHECK_DIR / "current_goal_completion_audit_v27_after_live_intake_and_tail_rechecks_assertions.out").write_text(
        "\n".join(
            [
                "PASS new_confidence_gate_since_v26=false",
                "PASS accepted_rows_added_since_v26=0",
                "PASS strict_full_objective_achieved=false",
                "PASS update_goal=false",
                "PASS unmet_ids=R2,R3,R4,R5,R6,R8",
                "PASS source_label_status=blocked",
                "PASS direct_manipulation_status=blocked",
                "PASS recency_tail_all_rows_present=false",
                "PASS ready_positive_control_sources=0",
            ]
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
