#!/usr/bin/env python3
"""Audit the active Board A objective against the latest 010127 cursor."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ID = "20260512T010612-codex-current-objective-completion-audit-after-010127-v1"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / "current-objective-completion-audit-after-010127"
CHECK_DIR = RUN_ROOT / "checks"

REFERENCE_FILES = [
    "docs/experiments/actionable-regime-confidence/runs/20260512T010127-codex-r6-owner-route-entitlement-readback-v1/r6-owner-route-entitlement-readback/r6_owner_route_entitlement_readback_v1.json",
    "docs/experiments/actionable-regime-confidence/runs/20260512T010127-codex-r6-owner-route-entitlement-readback-v1/checks/r6_owner_route_entitlement_readback_v1_assertions.out",
    "docs/experiments/actionable-regime-confidence/runs/20260512T005842-codex-r6-owner-export-outbound-request-messages-v1/checks/r6_owner_export_outbound_request_messages_v1_assertions.out",
    "docs/experiments/actionable-regime-confidence/runs/20260512T005913-codex-r6-owner-export-sendable-requests-v3/checks/r6_owner_export_sendable_requests_v3_assertions.out",
    "docs/experiments/actionable-regime-confidence/runs/20260512T005248-codex-v71-provider-autoquant-readonly-refresh-v1/checks/v71_provider_autoquant_readonly_refresh_v1_assertions.out",
    "docs/experiments/actionable-regime-confidence/runs/20260512T005039-codex-current-objective-reconciliation-after-v71-v1/checks/current_objective_reconciliation_after_v71_v1_assertions.out",
    "docs/experiments/actionable-regime-confidence/runs/20260512T005050-codex-r5-kaggle-stock-regime-recency-refresh-v2/checks/r5_kaggle_stock_regime_recency_refresh_v2_assertions.out",
    "docs/experiments/actionable-regime-confidence/runs/20260512T004636-codex-v69-r3-r5-source-label-current-readback-v1/checks/v69_r3_r5_source_label_current_readback_v1_assertions.out",
]


def read_text(path: Path) -> str:
    return path.read_text(errors="replace") if path.exists() else ""


def board_field(board: str, field: str) -> str:
    prefix = f"| {field} |"
    for line in board.splitlines():
        if line.startswith(prefix):
            parts = line.split("|")
            if len(parts) >= 4:
                return parts[2].strip()
    return ""


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    board = read_text(BOARD)

    last_loop_id = board_field(board, "last_loop_id")
    board_state = board_field(board, "board_state")
    accepted_gate = board_field(board, "accepted_gate")
    blocker = board_field(board, "blocker")
    next_action = board_field(board, "next_action")

    artifact_rows = []
    for ref in REFERENCE_FILES:
        path = Path(ref)
        text = read_text(path)
        artifact_rows.append(
            {
                "artifact": ref,
                "exists": str(path.exists()).lower(),
                "nonempty": str(bool(text.strip())).lower(),
                "contains_update_goal_false": str("update_goal=false" in text or '"update_goal": false' in text).lower(),
                "contains_strict_false": str("strict_full_objective_achieved=false" in text or '"strict_full_objective_achieved": false' in text).lower(),
            }
        )

    checklist = [
        {
            "requirement": "board_file_authority",
            "expected": "active plan is docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
            "evidence": str(BOARD),
            "status": "pass" if BOARD.exists() and "Current Cursor" in board else "fail",
            "gap": "",
        },
        {
            "requirement": "every_regime_confidence_95",
            "expected": "each active regime has accepted >=95 confidence",
            "evidence": f"board_state={board_state}; accepted_gate={accepted_gate[:240]}",
            "status": "blocked",
            "gap": "board_state is blocked; full_objective_gate remains none; source-label confidence 0/4 and R6 controls absent",
        },
        {
            "requirement": "cross_market_cross_period_validation",
            "expected": "accepted regimes have cross-market and cross-period validation",
            "evidence": "latest cursor keeps R6 event/order-lifecycle-only and R5/R3/source-label blockers fail-closed",
            "status": "blocked",
            "gap": "R6 lacks valid normal controls; R5 post-2026-01-30 rows absent; R3 native-subhour root absent",
        },
        {
            "requirement": "provider_autoquant_prebayes_bbn_catboost_execution_tree",
            "expected": "real provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree promotion rerun after accepted inputs",
            "evidence": "005248 provider/Auto-Quant read-only refresh and 004827/005039 readbacks; no promotion rerun allowed",
            "status": "blocked",
            "gap": "no canonical R6 merge or accepted validation-contract change exists",
        },
        {
            "requirement": "ibkr_tradingviewremix_yfinance_kraken",
            "expected": "named provider surfaces checked",
            "evidence": "005248 provider refresh reports yfinance and Kraken CLI ready; IBKR/TradingView/Kraken public non-promoting/dependency-blocked",
            "status": "partial",
            "gap": "IBKR and TradingView MCP are not promotion-ready; provider data does not replace source-owned labels",
        },
        {
            "requirement": "r6_oystacher_source_owned_controls_or_flip_approval",
            "expected": "source-owned normal controls or explicit FLIP-as-control approval",
            "evidence": "010127 route fit improved but controls=0; 005842/005913 request drafts not sent/acquired",
            "status": "blocked",
            "gap": "valid source-owned normal controls acquired 0; FLIP approval false",
        },
        {
            "requirement": "non_r6_source_label_r5_r3_roots",
            "expected": "source-label, R5 recency, and R3 native-subhour roots present and accepted",
            "evidence": "004636 and 005039 readbacks",
            "status": "blocked",
            "gap": "source-label confidence 0/4; R5 post-cutoff rows absent; R3 native-subhour root absent",
        },
        {
            "requirement": "multi_agent_preservation",
            "expected": "append-only board updates and no unrelated rollback",
            "evidence": "this audit is additive and references current cursor without changing it",
            "status": "pass",
            "gap": "",
        },
    ]

    artifact_presence_pass = all(row["exists"] == "true" and row["nonempty"] == "true" for row in artifact_rows)
    strict_complete = False
    gate_result = "current_objective_completion_audit_after_010127_v1=not_complete_r6_controls_source_label_r5_r3_downstream_blocked"

    summary = {
        "run_id": RUN_ID,
        "board_state": board_state,
        "last_loop_id": last_loop_id,
        "gate_result": gate_result,
        "strict_full_objective_achieved": strict_complete,
        "update_goal": False,
        "artifact_presence_pass": artifact_presence_pass,
        "requirements_total": len(checklist),
        "requirements_pass": sum(1 for row in checklist if row["status"] == "pass"),
        "requirements_blocked": sum(1 for row in checklist if row["status"] == "blocked"),
        "requirements_partial": sum(1 for row in checklist if row["status"] == "partial"),
        "accepted_rows_added": 0,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "owner_export_root_mutated": False,
        "raw_data_committed": False,
        "blocker": blocker,
        "next_action": next_action,
    }

    write_csv(OUT_DIR / "prompt_to_artifact_checklist_after_010127_v1.csv", checklist, ["requirement", "expected", "evidence", "status", "gap"])
    write_csv(OUT_DIR / "artifact_presence_after_010127_v1.csv", artifact_rows, ["artifact", "exists", "nonempty", "contains_update_goal_false", "contains_strict_false"])
    (OUT_DIR / "current_objective_completion_audit_after_010127_v1.json").write_text(json.dumps(summary, indent=2) + "\n")
    (OUT_DIR / "current_objective_completion_audit_after_010127_v1.md").write_text(
        f"""# Current Objective Completion Audit After 010127 v1

Decision: `{gate_result}`.

Objective restatement:
- Pull every active regime to at least 95% confidence.
- Validate across other markets and other periods/timeframes.
- Use real provider/Auto-Quant/filter/pre-Bayes/BBN/CatBoost/execution-tree evidence, including IBKR, TradingViewRemix, yfinance, and Kraken where available.
- Preserve the multi-agent board and do not disturb concurrent work.

Current cursor:
- board_state: `{board_state}`
- last_loop_id: `{last_loop_id}`

Result:
- Requirements pass: `{summary['requirements_pass']}/{summary['requirements_total']}`.
- Requirements partial: `{summary['requirements_partial']}`.
- Requirements blocked: `{summary['requirements_blocked']}`.
- Artifact presence pass: `{str(artifact_presence_pass).lower()}`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Accepted rows added: `0`; canonical merge allowed: false; downstream promotion rerun allowed: false.
- Runtime code changed: false; shared intake mutated: false; owner-export root mutated: false; raw data committed: false.

Main blockers:
- R6 valid source-owned normal controls remain `0`; same-exhibit `FLIP` approval remains false.
- R6 route fit and outbound/sendable request artifacts are improved, but requests are not satisfied and controls are not acquired.
- Source-label confidence remains `0/4`.
- R5 post-`2026-01-30` source-panel rows remain absent.
- R3 native-subhour source-label root remains absent.
- Full provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree promotion rerun remains disallowed until accepted source/control inputs and canonical merge exist.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/current-objective-completion-audit-after-010127/current_objective_completion_audit_after_010127_v1.json`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/current-objective-completion-audit-after-010127/prompt_to_artifact_checklist_after_010127_v1.csv`
- Artifact presence CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/current-objective-completion-audit-after-010127/artifact_presence_after_010127_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/current_objective_completion_audit_after_010127_v1_assertions.out`

Next:
- Satisfy the owner/source export branch or explicit `FLIP` approval branch, then rerun the direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree chain under the shared-lock path.
"""
    )

    assertions = [
        f"run_id={RUN_ID}",
        f"board_state={board_state}",
        f"last_loop_id={last_loop_id}",
        f"gate_result={gate_result}",
        f"artifact_presence_pass={str(artifact_presence_pass).lower()}",
        f"requirements_total={len(checklist)}",
        f"requirements_pass={summary['requirements_pass']}",
        f"requirements_partial={summary['requirements_partial']}",
        f"requirements_blocked={summary['requirements_blocked']}",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        "accepted_rows_added=0",
        "canonical_merge_allowed=false",
        "downstream_chain_rerun_allowed=false",
        "runtime_code_changed=false",
        "shared_intake_mutated=false",
        "owner_export_root_mutated=false",
        "raw_data_committed=false",
    ]
    (CHECK_DIR / "current_objective_completion_audit_after_010127_v1_assertions.out").write_text("\n".join(assertions) + "\n")


if __name__ == "__main__":
    main()
