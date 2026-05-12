#!/usr/bin/env python3
"""Prompt-to-artifact completion audit after the Sapienza pump/dump gate."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
REPO_ROOT = Path.cwd()

SAP_GATE = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T195945-codex-sapienza-pumpdump-control-gate-v1/sapienza-pumpdump-control-gate/sapienza_pumpdump_control_gate_v1.json"
V25 = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T195401-codex-current-goal-completion-audit-v25-after-local-inventory/completion-audit/current_goal_completion_audit_v25_after_local_inventory.json"
STRICT_CONTRACT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T195728-codex-strict-objective-acquisition-contract-v1/strict-objective-acquisition-contract/strict_objective_acquisition_contract_v1.json"
DIRECT_VERIFIER = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T193301-codex-direct-manipulation-intake-verifier-readback-v1/direct-manipulation-intake-verifier-readback/direct_manipulation_intake_verifier_readback_v1.json"
EXACT_SEARCH = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T194739-codex-strict-1h-target-exact-source-search-v1/strict-1h-target-exact-source-search/strict_1h_target_exact_source_search_v1.json"
NATIVE_RECHECK = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T194400-codex-native-subhour-source-recheck-v2/native-subhour-source-recheck/native_subhour_source_recheck_v2.json"
LOCAL_INVENTORY = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T194952-codex-local-broad-source-owned-label-inventory-v1/local-broad-source-owned-label-inventory/local_broad_source_owned_label_inventory_v1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    sap = load(SAP_GATE)
    v25 = load(V25)
    strict_contract = load(STRICT_CONTRACT)
    direct = load(DIRECT_VERIFIER)
    exact = load(EXACT_SEARCH)
    native = load(NATIVE_RECHECK)
    local = load(LOCAL_INVENTORY)
    exact_tail_counts = {
        f"{row['symbol']}/{row['root']}": row["rows_after_2026_01_30"]
        for row in exact.get("local_source_panel_counts", [])
    }

    checklist = [
        {
            "id": "R0",
            "requirement": "Use the named Board A markdown as the execution contract.",
            "status": "pass_checked",
            "artifact": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
            "evidence": "Current Cursor updated to sapienza_pumpdump_control_gate_v1.",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "Every active regime has scoped calibrated >=95% confidence.",
            "status": "pass_scoped_not_full",
            "artifact": "regime_factor_consumer_map_v1; sapienza_pumpdump_control_gate_v1",
            "evidence": f"Sapienza direct pump/dump gate accepted={sap['new_confidence_gate']} min_lcb={sap['min_split_wilson95_lcb']:.12f}; existing scoped consumer map remains accepted.",
            "gap": "Scoped acceptance is not the same as strict full-market/full-cycle/full-species completion.",
        },
        {
            "id": "R2",
            "requirement": "Other-market/source-label equivalence has suitable confidence.",
            "status": "fail_blocked",
            "artifact": "web/source-label screens; local broad inventory",
            "evidence": f"local={local['decision']}; v25 failed rows include R2.",
            "gap": "No promotable source-owned or owner-approved other-market equivalence rows were found.",
        },
        {
            "id": "R3",
            "requirement": "Other-cycle/timeframe validation has suitable confidence, including native sub-hour labels.",
            "status": "fail_blocked",
            "artifact": str(NATIVE_RECHECK.relative_to(REPO_ROOT)),
            "evidence": f"native={native['decision']}; ready_sources={native.get('ready_native_subhour_source_owned_label_sources', 0)}.",
            "gap": "Native sub-hour price-root source labels remain absent.",
        },
        {
            "id": "R4",
            "requirement": "Strict exact 1h remaining slots have source-owned rows and provenance.",
            "status": "fail_blocked",
            "artifact": str(EXACT_SEARCH.relative_to(REPO_ROOT)),
            "evidence": f"exact_search={exact['decision']}; ready_sources={exact.get('ready_source_owned_exact_target_sources', 0)}.",
            "gap": "Strict exact 1h source-owned row intake is still missing.",
        },
        {
            "id": "R5",
            "requirement": "XOM/Sideways and remaining strict 1h targets have recency-tail repair where required.",
            "status": "fail_blocked",
            "artifact": str(EXACT_SEARCH.relative_to(REPO_ROOT)),
            "evidence": f"rows_after_2026_01_30={exact_tail_counts}.",
            "gap": "Strict target rows still have zero post-2026-01-30 source-panel rows.",
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation has row-level positives, matched controls, and provenance across required species.",
            "status": "partial_still_blocked",
            "artifact": str(SAP_GATE.relative_to(REPO_ROOT)),
            "evidence": f"Sapienza accepted {sap['accepted_rows_added']} pump/dump event groups at min Wilson95 LCB {sap['min_split_wilson95_lcb']:.12f}; direct verifier remains {direct.get('decision', direct.get('status'))}.",
            "gap": "Spoofing/layering, quote stuffing, pinging, bear raid, and painting tape still lack source-owned positive/control rows.",
        },
        {
            "id": "R7",
            "requirement": "Guardrails reject proxy/generated/duplicated rows.",
            "status": "pass_guardrail",
            "artifact": str(STRICT_CONTRACT.relative_to(REPO_ROOT)),
            "evidence": f"strict_contract={strict_contract['decision']}; Sapienza raw rows remain under /tmp and are not trade usable.",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "Goal can be marked complete only if every strict requirement is covered.",
            "status": "fail_blocked",
            "artifact": str(RUN_ROOT.relative_to(REPO_ROOT)),
            "evidence": "Rows R2, R3, R4, R5, and R6 remain incomplete after the new Sapienza scoped gate.",
            "gap": "Strict full objective is not achieved; update_goal must remain false.",
        },
    ]
    unmet = [row for row in checklist if row["status"] in {"fail_blocked", "partial_still_blocked"}]
    result = {
        "run_id": "20260511T200319+0800-codex-current-goal-completion-audit-v26-after-sapienza-gate",
        "decision": "current_goal_completion_audit_v26=scoped_sapienza_gate_added_strict_full_objective_blocked",
        "checklist_rows": len(checklist),
        "unmet_rows": len(unmet),
        "unmet_ids": [row["id"] for row in unmet],
        "sapienza_gate_added": True,
        "sapienza_accepted_event_groups": sap["accepted_rows_added"],
        "sapienza_min_split_wilson95_lcb": sap["min_split_wilson95_lcb"],
        "accepted_rows_added_since_v25": sap["accepted_rows_added"],
        "new_confidence_gate_since_v25": True,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "checklist": checklist,
    }

    (OUT_DIR / "current_goal_completion_audit_v26_after_sapienza_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    write_csv(
        OUT_DIR / "current_goal_completion_audit_v26_checklist.csv",
        checklist,
        ["id", "requirement", "status", "artifact", "evidence", "gap"],
    )
    write_csv(
        OUT_DIR / "current_goal_completion_audit_v26_unmet_requirements.csv",
        unmet,
        ["id", "requirement", "status", "artifact", "evidence", "gap"],
    )

    md_lines = [
        "# Current Goal Completion Audit v26 After Sapienza Gate",
        "",
        "- Decision: `current_goal_completion_audit_v26=scoped_sapienza_gate_added_strict_full_objective_blocked`",
        f"- Checklist rows: `{len(checklist)}`",
        f"- Unmet rows: `{len(unmet)}`",
        f"- Unmet ids: `{', '.join(row['id'] for row in unmet)}`",
        f"- Sapienza accepted event groups: `{sap['accepted_rows_added']}`",
        f"- Sapienza minimum split Wilson95 LCB: `{sap['min_split_wilson95_lcb']:.12f}`",
        "- New confidence gate since v25: `true`",
        "- Strict full objective achieved: `false`; `update_goal=false`",
        "",
        "## Objective Restatement",
        "",
        "Every active regime must have calibrated `>=95%` confidence, and that confidence must remain suitable across other markets/species and other cycles/timeframes before the goal can be marked complete.",
        "",
        "## Checklist",
        "",
        "| ID | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        md_lines.append(
            f"| `{row['id']}` | `{row['status']}` | {row['evidence']} | {row['gap']} |"
        )
    md_lines.extend(
        [
            "",
            "## Decision",
            "",
            "Sapienza materially improves direct `Manipulation` by adding a scoped pump/dump positive-control gate, but the original strict objective remains blocked because the price-root transfer requirements and the remaining direct manipulation species are still uncovered.",
        ]
    )
    (OUT_DIR / "current_goal_completion_audit_v26_after_sapienza_gate.md").write_text(
        "\n".join(md_lines) + "\n"
    )

    assert result["sapienza_gate_added"] is True
    assert result["sapienza_accepted_event_groups"] == 317
    assert result["new_confidence_gate_since_v25"] is True
    assert result["strict_full_objective_achieved"] is False
    assert result["update_goal"] is False
    assert set(result["unmet_ids"]) == {"R2", "R3", "R4", "R5", "R6", "R8"}

    (CHECK_DIR / "current_goal_completion_audit_v26_after_sapienza_gate_assertions.out").write_text(
        "\n".join(
            [
                "PASS sapienza_gate_added=true",
                "PASS sapienza_accepted_event_groups=317",
                "PASS new_confidence_gate_since_v25=true",
                "PASS strict_full_objective_achieved=false",
                "PASS update_goal=false",
                "PASS unmet_ids=R2,R3,R4,R5,R6,R8",
            ]
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
