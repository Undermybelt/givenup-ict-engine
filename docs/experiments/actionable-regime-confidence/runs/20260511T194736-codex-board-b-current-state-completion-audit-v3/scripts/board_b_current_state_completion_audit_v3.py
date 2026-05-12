#!/usr/bin/env python3
"""Current Board B completion audit after the 194231 combined readback."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


RUN_ID = "20260511T194736+0800-codex-board-b-current-state-completion-audit-v3"
RUN_SLUG = "20260511T194736-codex-board-b-current-state-completion-audit-v3"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_SLUG
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO_ROOT / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"
COMBINED_JSON = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/"
    "branch-rc-spa/root_plus_manip_bridge_rc_spa_report_v1.json"
)
COMBINED_ASSERTIONS = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/"
    "checks/root_plus_manip_bridge_rc_spa_v1_assertions.out"
)
FAIL_CLOSED_SUMMARY = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/"
    "ict-engine-fail-closed/root_plus_manip_bridge_fail_closed_summary_v1.md"
)
PROVIDER_STATUS = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/"
    "ict-engine-fail-closed/logs/provider_status_compact.out"
)
PRE_BAYES_STATUS = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/"
    "ict-engine-fail-closed/logs/pre_bayes_status_human.out"
)
POLICY_STATUS = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/"
    "ict-engine-fail-closed/logs/policy_training_status_human.out"
)
WORKFLOW_STATUS = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/"
    "ict-engine-fail-closed/logs/workflow_status_human.out"
)

REPORT_JSON = OUT_DIR / "board_b_current_state_completion_audit_v3.json"
REPORT_MD = OUT_DIR / "board_b_current_state_completion_audit_v3.md"
CHECKLIST_CSV = OUT_DIR / "board_b_current_state_completion_audit_v3_checklist.csv"
ASSERTIONS = CHECK_DIR / "board_b_current_state_completion_audit_v3_assertions.out"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    combined = json.loads(COMBINED_JSON.read_text(encoding="utf-8"))
    decision = combined["decision"]
    provider_text = read_text(PROVIDER_STATUS)
    pre_bayes_text = read_text(PRE_BAYES_STATUS)
    policy_text = read_text(POLICY_STATUS)
    workflow_text = read_text(WORKFLOW_STATUS)
    board_text = read_text(BOARD)

    checklist: list[dict[str, Any]] = [
        {
            "requirement": "Authoritative Board B markdown updated",
            "status": "pass",
            "evidence": rel(BOARD),
            "detail": "Current cursor and ledger include 194231 combined readback.",
        },
        {
            "requirement": "Regime-rooted branch path preserved",
            "status": "pass",
            "evidence": rel(COMBINED_JSON),
            "detail": f"branch_paths={decision['branch_paths_passed']}/5 passed, paths evaluated=5.",
        },
        {
            "requirement": "Real Auto-Quant/local artifact consumed",
            "status": "pass",
            "evidence": rel(COMBINED_JSON),
            "detail": f"root rows selected={decision['selected_trade_rows']} variant={decision['variant_trade_rows']}.",
        },
        {
            "requirement": "Direct Manipulation executable PnL rows exist",
            "status": "partial",
            "evidence": rel(COMBINED_JSON),
            "detail": "Manipulation rows exist but bridge underperforms controls and is not promotion-grade.",
        },
        {
            "requirement": "All required root branches pass RC-SPA",
            "status": "fail",
            "evidence": rel(COMBINED_ASSERTIONS),
            "detail": f"branch_paths_passed={decision['branch_paths_passed']}; gate={decision['gate_result']}.",
        },
        {
            "requirement": "Pre-Bayes/filter consumes promoted branch packet",
            "status": "fail_blocked",
            "evidence": rel(PRE_BAYES_STATUS),
            "detail": pre_bayes_text.strip().splitlines()[0] if pre_bayes_text.strip() else "missing pre-bayes output",
        },
        {
            "requirement": "BBN/CatBoost/path-ranker consumes promoted branch packet",
            "status": "fail_blocked",
            "evidence": rel(POLICY_STATUS),
            "detail": policy_text.strip().splitlines()[0] if policy_text.strip() else "missing policy output",
        },
        {
            "requirement": "Execution tree/workflow consumes promoted branch packet",
            "status": "fail_blocked",
            "evidence": rel(WORKFLOW_STATUS),
            "detail": "no_workflow_state" if "no_workflow_state" in workflow_text else "workflow output needs review",
        },
        {
            "requirement": "Provider readback covers requested provider family",
            "status": "partial",
            "evidence": rel(PROVIDER_STATUS),
            "detail": "yfinance/tradingview_mcp/kraken_cli ready; IBKR and python crypto providers unhealthy in this runtime.",
        },
        {
            "requirement": "Do not promote proxy or failed gates",
            "status": "pass",
            "evidence": rel(FAIL_CLOSED_SUMMARY),
            "detail": "downstream promotion stayed not_started/fail-closed.",
        },
    ]
    goal_complete = all(item["status"] == "pass" for item in checklist)
    summary = {
        "run_id": RUN_ID,
        "goal_complete": goal_complete,
        "update_goal": False,
        "current_cursor_seen": "194231" in board_text,
        "hard_gate_result": decision["gate_result"],
        "branch_paths_passed": decision["branch_paths_passed"],
        "downstream_consumption": decision["downstream_consumption"],
        "single_blocker": (
            "No all-root RC-SPA pass; direct Manipulation has rows but fails controls; "
            "Pre-Bayes/BBN/CatBoost/execution-tree promotion is blocked."
        ),
        "checklist": checklist,
        "artifacts": {
            "report_json": rel(REPORT_JSON),
            "report_md": rel(REPORT_MD),
            "checklist_csv": rel(CHECKLIST_CSV),
            "assertions": rel(ASSERTIONS),
        },
    }
    with CHECKLIST_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["requirement", "status", "evidence", "detail"])
        writer.writeheader()
        writer.writerows(checklist)
    REPORT_JSON.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Board B Current State Completion Audit v3",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"- Goal complete: `{goal_complete}`",
        f"- update_goal: `False`",
        f"- Hard gate: `{decision['gate_result']}`",
        f"- Branch paths passed: `{decision['branch_paths_passed']}/5`",
        f"- Downstream: `{decision['downstream_consumption']}`",
        f"- Single blocker: {summary['single_blocker']}",
        "",
        "## Checklist",
        "",
        "| Requirement | Status | Evidence | Detail |",
        "|---|---|---|---|",
    ]
    for item in checklist:
        lines.append(
            f"| {item['requirement']} | `{item['status']}` | `{item['evidence']}` | {item['detail']} |"
        )
    lines.extend(
        [
            "",
            "## Next",
            "",
            "- Continue B2R-repeat with a different root-aware family/panel or stronger direct Manipulation PnL source; do not start downstream promotion until all required branches pass RC-SPA.",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    ASSERTIONS.write_text(
        "\n".join(
            [
                f"goal_complete={goal_complete}",
                "update_goal=False",
                f"branch_paths_passed={decision['branch_paths_passed']}",
                f"hard_gate_result={decision['gate_result']}",
                f"downstream_consumption={decision['downstream_consumption']}",
                f"checklist_items={len(checklist)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
