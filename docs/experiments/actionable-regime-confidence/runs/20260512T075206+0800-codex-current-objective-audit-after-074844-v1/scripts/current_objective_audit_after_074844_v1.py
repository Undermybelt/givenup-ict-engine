#!/usr/bin/env python3
"""Prompt-to-artifact audit for the Board B objective after 074844/075009."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


RUN_ID = "20260512T075206+0800-codex-current-objective-audit-after-074844-v1"
GATE_RESULT = (
    "current_objective_audit_after_074844_v1="
    "not_complete_source_control_and_user_selection_missing_no_promotion"
)
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = RUN_ROOT / "current-objective-audit-after-074844-v1"
CHECK_ROOT = RUN_ROOT / "checks"

BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"


def read_text(path: Path) -> str:
    return path.read_text(errors="replace") if path.exists() else ""


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assertion_value(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}=(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def exit_code(path: Path) -> int | None:
    if not path.exists():
        return None
    text = path.read_text(errors="replace").strip()
    try:
        return int(text)
    except ValueError:
        return None


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_ROOT.mkdir(parents=True, exist_ok=True)

    board_a_text = read_text(BOARD_A)
    board_b_text = read_text(BOARD_B)

    p074535 = REPO / (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T074535+0800-codex-board-b-current-objective-audit-selection-gate-v1/"
        "checks/board_b_current_objective_audit_selection_gate_v1_assertions.out"
    )
    p074844 = REPO / (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T074844+0800-codex-databento-gc-raw-recency-disposition-after-074424-v1/"
        "checks/databento_gc_raw_recency_disposition_after_074424_v1_assertions.out"
    )
    p075009 = REPO / (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T075009+0800-codex-source-control-arrival-poll-after-074700-v1/"
        "checks/source_control_arrival_poll_after_074700_v1_assertions.out"
    )
    p075108 = REPO / (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T075108+0800-codex-board-b-readonly-provider-runtime-gate-refresh-v1/"
        "readonly_provider_runtime_gate_refresh_v1.md"
    )
    p075108_cmd = REPO / (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T075108+0800-codex-board-b-readonly-provider-runtime-gate-refresh-v1/"
        "command-output"
    )

    a074535 = read_text(p074535)
    a074844 = read_text(p074844)
    a075009 = read_text(p075009)
    r075108 = read_text(p075108)

    exits = {
        "provider_status": exit_code(p075108_cmd / "01_provider_status_agent.exit"),
        "auto_quant_status": exit_code(p075108_cmd / "02_auto_quant_status_compact.exit"),
        "workflow_status": exit_code(p075108_cmd / "03_workflow_status_agent.exit"),
        "pre_bayes_status": exit_code(p075108_cmd / "04_pre_bayes_status_compact.exit"),
        "path_ranking_export": exit_code(p075108_cmd / "05_export_structural_path_ranking_target.exit"),
    }

    checklist = [
        {
            "requirement": "Named Board B markdown is the live contract",
            "evidence": str(BOARD_B.relative_to(REPO)),
            "status": "pass" if BOARD_B.exists() and "Root-First Profit Factor Contract" in board_b_text else "blocked",
            "notes": "Board B was read directly before this audit.",
        },
        {
            "requirement": "Regime-rooted branch path is preserved",
            "evidence": "Board B 074535 selection-gate audit and current cursor",
            "status": "partial_fail_closed" if "path_ranker_validation_0_of_30" in board_b_text else "blocked",
            "notes": "Branch path is visible, but path-ranker validation and execution remain fail-closed.",
        },
        {
            "requirement": "Do not run selected-data AutoQuant without explicit HTF/MTF/LTF selection",
            "evidence": str(p074535.relative_to(REPO)),
            "status": "pass_fail_closed" if assertion_value(a074535, "explicit_user_selected_history_present") == "false" else "blocked",
            "notes": "075535 says next gate is exactly one user-selected HTF/MTF/LTF path.",
        },
        {
            "requirement": "Source/control unlock exists before canonical merge or promotion",
            "evidence": str(p075009.relative_to(REPO)),
            "status": "blocked" if assertion_value(a075009, "valid_required_root_unlock") == "false" else "pass",
            "notes": "075009 reports no new R3/R5/R6 required root.",
        },
        {
            "requirement": "Raw Databento OHLCV is not promoted as labels or controls",
            "evidence": str(p074844.relative_to(REPO)),
            "status": "pass_fail_closed"
            if assertion_value(a074844, "source_label_columns_present") == "false"
            and assertion_value(a074844, "order_lifecycle_columns_present") == "false"
            else "blocked",
            "notes": "Post-cutoff raw OHLCV exists, but no source-label or order-lifecycle columns exist.",
        },
        {
            "requirement": "Provider/runtime surfaces are refreshed with real commands",
            "evidence": str(p075108.relative_to(REPO)),
            "status": "partial_non_promoting" if all(code == 0 for code in exits.values()) else "blocked",
            "notes": "Commands ran, but AutoQuant data is missing and workflow remains user-selected-history blocked.",
        },
        {
            "requirement": "Filter / Pre-Bayes / BBN / CatBoost / execution-tree chain promotes only after gates",
            "evidence": "075108 workflow/pre-bayes/path-ranking read-only outputs",
            "status": "blocked"
            if "user_selected_historical_data_missing" in r075108
            and "execution_blocked" in r075108
            else "needs_review",
            "notes": "Read-only chain state exists; it is not a selected-data rerun or promotion.",
        },
        {
            "requirement": "No update_goal until objective is complete",
            "evidence": "074535, 074844, and 075009 assertions",
            "status": "pass_fail_closed"
            if all("update_goal=false" in text for text in [a074535, a074844, a075009])
            else "blocked",
            "notes": "Objective remains incomplete.",
        },
    ]

    objective_complete = False
    promotion_allowed = False
    update_goal = False

    result = {
        "run_id": RUN_ID,
        "gate_result": GATE_RESULT,
        "board_a_sha256": sha256(BOARD_A),
        "board_b_sha256": sha256(BOARD_B),
        "evidence": {
            "board_b": str(BOARD_B.relative_to(REPO)),
            "board_a": str(BOARD_A.relative_to(REPO)),
            "selection_gate_assertions": str(p074535.relative_to(REPO)),
            "databento_raw_recency_assertions": str(p074844.relative_to(REPO)),
            "source_control_arrival_assertions": str(p075009.relative_to(REPO)),
            "provider_runtime_refresh": str(p075108.relative_to(REPO)),
        },
        "readback": {
            "selection_gate": assertion_value(a074535, "gate_result"),
            "source_control_gate": assertion_value(a075009, "gate_result"),
            "databento_gate": assertion_value(a074844, "gate_result"),
            "explicit_user_selected_history_present": assertion_value(
                a074535, "explicit_user_selected_history_present"
            ),
            "valid_required_root_unlock": assertion_value(a075009, "valid_required_root_unlock"),
            "source_control_evidence_acquired": assertion_value(
                a075009, "source_control_evidence_acquired"
            ),
            "auto_quant_status": "dependency_ready_data_missing"
            if "dependency_ready_data_missing" in r075108
            else "unknown",
            "workflow_blocker": "user_selected_historical_data_missing"
            if "user_selected_historical_data_missing" in r075108
            else "unknown",
            "execution_gate": "execution_blocked" if "execution_blocked" in r075108 else "unknown",
            "command_exits": exits,
        },
        "checklist": checklist,
        "decision": {
            "objective_complete": objective_complete,
            "promotion_allowed": promotion_allowed,
            "update_goal": update_goal,
        },
    }

    json_path = OUT_ROOT / "current_objective_audit_after_074844_v1.json"
    csv_path = OUT_ROOT / "current_objective_audit_after_074844_v1.csv"
    md_path = OUT_ROOT / "current_objective_audit_after_074844_v1.md"
    assertions_path = CHECK_ROOT / "current_objective_audit_after_074844_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["requirement", "evidence", "status", "notes"])
        writer.writeheader()
        writer.writerows(checklist)

    rows = [
        "# Current Objective Audit After 074844 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE_RESULT}`",
        "",
        "## Objective Restatement",
        "",
        "Board B must train and promote profitable factors rooted in Board A regime context, preserve the branch path `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`, and only continue through AutoQuant -> filter / Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree after source/control and user-selected-data gates are satisfied.",
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| Requirement | Evidence | Status | Notes |",
        "|---|---|---|---|",
    ]
    for item in checklist:
        rows.append(
            f"| {item['requirement']} | `{item['evidence']}` | {item['status']} | {item['notes']} |"
        )
    rows.extend(
        [
            "",
            "## Evidence Readback",
            "",
            f"- Board A SHA-256: `{result['board_a_sha256']}`.",
            f"- Board B SHA-256: `{result['board_b_sha256']}`.",
            f"- Selection gate: `{result['readback']['selection_gate']}`.",
            f"- Source/control gate: `{result['readback']['source_control_gate']}`.",
            f"- Databento gate: `{result['readback']['databento_gate']}`.",
            f"- AutoQuant read-only status: `{result['readback']['auto_quant_status']}`.",
            f"- Workflow blocker: `{result['readback']['workflow_blocker']}`.",
            f"- Execution gate: `{result['readback']['execution_gate']}`.",
            f"- Command exits in `075108`: `{result['readback']['command_exits']}`.",
            "",
            "## Decision",
            "",
            "The objective is not complete. The current evidence has real source/control acquisition and read-only runtime refresh, but source/control remains locked, user-selected historical data is missing, selected-data AutoQuant has not run, and downstream promotion remains blocked.",
            "",
            "`promotion_allowed=false`; `update_goal=false`.",
            "",
            "## Next",
            "",
            "Continue source/control acquisition only unless the user explicitly selects exactly one of `HTF`, `MTF`, or `LTF` for non-promotional factor-research. Do not run selected-data AutoQuant or the ordered filter / Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree chain until both the user-selection gate and source/control unlock gate are satisfied.",
            "",
        ]
    )
    md_path.write_text("\n".join(rows))

    failures = []
    if assertion_value(a074535, "explicit_user_selected_history_present") != "false":
        failures.append("selection_gate_not_fail_closed")
    if assertion_value(a075009, "valid_required_root_unlock") != "false":
        failures.append("source_control_unlock_not_false")
    if assertion_value(a075009, "source_control_evidence_acquired") != "false":
        failures.append("source_control_evidence_not_false")
    if assertion_value(a074844, "source_label_columns_present") != "false":
        failures.append("databento_source_label_columns_not_false")
    if assertion_value(a074844, "order_lifecycle_columns_present") != "false":
        failures.append("databento_order_lifecycle_columns_not_false")
    if not all(code == 0 for code in exits.values()):
        failures.append("readonly_command_exit_nonzero")
    if "user_selected_historical_data_missing" not in r075108:
        failures.append("workflow_blocker_not_observed")
    if update_goal:
        failures.append("update_goal_true")

    if failures:
        assertions_path.write_text("FAIL " + "; ".join(failures) + "\n")
        return 1

    assertions_path.write_text(
        "\n".join(
            [
                f"gate_result={GATE_RESULT}",
                "objective_complete=false",
                "promotion_allowed=false",
                "update_goal=false",
                "explicit_user_selected_history_present=false",
                "valid_required_root_unlock=false",
                "source_control_evidence_acquired=false",
                "selected_data_autoquant_run=false",
                "downstream_promotion_rerun=false",
                "next_gate=source_control_acquisition_or_user_select_exactly_one_of_HTF_MTF_LTF",
                "",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
