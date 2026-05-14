#!/usr/bin/env python3
"""Completion audit after R6 v4 request packet and source-arrival poll."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ID = "20260512T015413-codex-current-objective-completion-audit-after-v4-requests-v1"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
BOARD_SHA256 = "8651a75652b7e36279b4577fcf3b3860d03b67a2303e0622d0b9fcdc7dbb1449"
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT = ROOT / "current-objective-completion-audit-after-v4-requests-v1"
CHECKS = ROOT / "checks"

EVIDENCE = {
    "source_label_failclosed": Path("docs/experiments/actionable-regime-confidence/runs/20260512T012425-codex-source-label-qualifying-condition-failclosed-v1/checks/source_label_qualifying_condition_failclosed_v1_assertions.out"),
    "readonly_runtime_chain": Path("docs/experiments/actionable-regime-confidence/runs/20260512T013533-codex-readonly-runtime-chain-refresh-after-013042-v1/checks/readonly_runtime_chain_refresh_after_013042_v1_assertions.out"),
    "autoquant_cache": Path("docs/experiments/actionable-regime-confidence/runs/20260512T013904-codex-autoquant-latest-backtest-cache-readback-v1/checks/autoquant_latest_backtest_cache_readback_v1_assertions.out"),
    "send_channel_preflight": Path("docs/experiments/actionable-regime-confidence/runs/20260512T014300-codex-r6-owner-export-current-send-channel-preflight-v1/checks/r6_owner_export_current_send_channel_preflight_v1_assertions.out"),
    "operator_handoff": Path("docs/experiments/actionable-regime-confidence/runs/20260512T014941-codex-r6-owner-export-operator-handoff-v1/checks/r6_owner_export_operator_handoff_v1_assertions.out"),
    "v4_requests": Path("docs/experiments/actionable-regime-confidence/runs/20260512T015040-codex-r6-owner-export-sendable-requests-v4-current-routes-v1/checks/r6_owner_export_sendable_requests_v4_current_routes_v1_assertions.out"),
    "source_arrival_poll": Path("docs/experiments/actionable-regime-confidence/runs/20260512T015121-codex-post-restoration-source-arrival-poll-v1/checks/post_restoration_source_arrival_poll_v1_assertions.out"),
}

TMP_ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r5_recency_extension": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
    "direct_manipulation_old": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
}


def file_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob("*") if p.is_file())


def root_status(path: Path) -> dict[str, object]:
    return {"path": str(path), "present": path.exists(), "file_count": file_count(path)}


def read_text(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def has_pass(path: Path, key: str) -> bool:
    return f"{key}=PASS" in read_text(path)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    roots = {name: root_status(path) for name, path in TMP_ROOTS.items()}
    evidence_presence = {name: path.exists() and path.stat().st_size > 0 for name, path in EVIDENCE.items()}

    checklist = [
        {
            "requirement": "Named Board A markdown remains the live contract",
            "status": "pass" if BOARD.exists() else "blocked",
            "evidence": f"{BOARD}; sha256_at_audit={BOARD_SHA256}",
            "gap": "none" if BOARD.exists() else "board missing",
        },
        {
            "requirement": "Every MainRegimeV2 regime reaches calibrated confidence >=95%",
            "status": "blocked",
            "evidence": "012425/014305/015121 preserve accepted labels as empty and strict objective false",
            "gap": "No accepted Bull/Bear/Sideways/Crisis packet; Bull/Sideways are field-complete leads only.",
        },
        {
            "requirement": "Each accepted regime has its own qualifying condition",
            "status": "partial",
            "evidence": "012425 source-label fail-closed audit",
            "gap": "Condition leads exist for Bull/Sideways, but no accepted labels; Bear/Crisis remain unaccepted.",
        },
        {
            "requirement": "Validation transfers to other markets and cycles/timeframes",
            "status": "blocked",
            "evidence": f"r3={roots['r3_native_subhour']}; r5={roots['r5_recency_extension']}; source_label={roots['source_label_equivalence']}",
            "gap": "R3 native sub-hour and R5 recency roots absent; source-label equivalence is daily-only and confidence-blocked.",
        },
        {
            "requirement": "R6 direct manipulation has source-owned normal controls or explicit FLIP approval",
            "status": "blocked",
            "evidence": f"r6={roots['r6_owner_export']}; 015040 v4 request packet; 015121 source-arrival poll",
            "gap": "Owner-export root absent; controls 0; FLIP approval false; request drafts are not data.",
        },
        {
            "requirement": "Provider context includes IBKR, TradingViewRemix, yfinance, and Kraken",
            "status": "partial",
            "evidence": "013533 provider/runtime readback and later board registrations",
            "gap": "Provider surfaces are read-only context; yfinance/Kraken CLI usable, while IBKR/TradingView/Kraken public remain not promotion evidence.",
        },
        {
            "requirement": "Operate Auto-Quant as part of the real chain",
            "status": "blocked",
            "evidence": "013904 Auto-Quant cache readback; Tomac latest result has 9 trades and negative profit",
            "gap": "Auto-Quant evidence is parseable but low-trade/negative and contains no accepted source/control roots.",
        },
        {
            "requirement": "Operate ict-engine filter, Pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree surfaces",
            "status": "partial",
            "evidence": "013533 read-only runtime chain refresh",
            "gap": "Commands were callable/read-only; downstream promotion rerun remains disallowed until source/control roots and canonical merge pass.",
        },
        {
            "requirement": "Use v4 sendable request packet only as operator handoff, not acceptance evidence",
            "status": "pass",
            "evidence": "015040 v4 request packet registered as requests_refreshed_current_routes_controls_not_acquired_no_merge",
            "gap": "none for posture; still not completion evidence",
        },
        {
            "requirement": "Multi-agent append-only discipline preserved",
            "status": "pass",
            "evidence": "This audit writes an isolated run root and only appends a board registration after re-read.",
            "gap": "none",
        },
        {
            "requirement": "Goal may be marked complete",
            "status": "blocked",
            "evidence": "accepted_rows_added=0; canonical_merge_allowed=false; downstream_chain_rerun_allowed=false",
            "gap": "Source/control evidence and per-regime 95% acceptance are missing.",
        },
    ]

    payload = {
        "run_id": RUN_ID,
        "gate_result": "current_objective_completion_audit_after_v4_requests_v1=not_complete_owner_export_and_regime_acceptance_blocked",
        "board": str(BOARD),
        "board_sha256_at_audit": BOARD_SHA256,
        "objective_restatement": [
            "Each active MainRegimeV2 regime must have accepted calibrated confidence >=95%.",
            "Accepted confidence must validate across other markets and other cycles/timeframes.",
            "Real Auto-Quant and ict-engine filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree surfaces must be operated in order.",
            "IBKR, TradingViewRemix, yfinance, and Kraken provider context must be recorded.",
            "Multi-agent board edits must stay append-only and not disturb concurrent work.",
        ],
        "prompt_to_artifact_checklist": checklist,
        "checklist_counts": {
            "pass": sum(1 for row in checklist if row["status"] == "pass"),
            "partial": sum(1 for row in checklist if row["status"] == "partial"),
            "blocked": sum(1 for row in checklist if row["status"] == "blocked"),
        },
        "evidence_presence": evidence_presence,
        "root_status": roots,
        "accepted_rows_added": 0,
        "accepted_labels": [],
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_r5_r6_roots_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    write_csv(
        OUT / "current_objective_prompt_to_artifact_checklist_after_v4_requests_v1.csv",
        checklist,
        ["requirement", "status", "evidence", "gap"],
    )
    write_csv(
        OUT / "current_objective_root_status_after_v4_requests_v1.csv",
        [
            {"root": name, **status}
            for name, status in roots.items()
        ],
        ["root", "path", "present", "file_count"],
    )
    (OUT / "current_objective_completion_audit_after_v4_requests_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )

    checklist_lines = "\n".join(
        f"- `{row['status']}`: {row['requirement']} Evidence: {row['evidence']} Gap: {row['gap']}"
        for row in checklist
    )
    report = f"""# Current Objective Completion Audit After v4 Requests v1

Run id: `{RUN_ID}`
Gate result: `{payload['gate_result']}`

Objective restatement:
- Each active `MainRegimeV2` regime must have accepted calibrated confidence >=95%.
- Accepted confidence must validate across other markets and other cycles/timeframes.
- Real Auto-Quant and ict-engine filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree surfaces must be operated in order.
- IBKR, TradingViewRemix, yfinance, and Kraken provider context must be recorded.
- Multi-agent board edits must stay append-only and not disturb concurrent work.

Prompt-to-artifact checklist:
{checklist_lines}

Current root state:
- R6 owner-export: `{roots['r6_owner_export']}`.
- R3 native sub-hour: `{roots['r3_native_subhour']}`.
- R5 recency extension: `{roots['r5_recency_extension']}`.
- Source-label equivalence: `{roots['source_label_equivalence']}`.
- Old direct-manipulation tmp intake: `{roots['direct_manipulation_old']}`; not the active owner-export root.

Decision:
- Objective achieved: `false`.
- `update_goal=false`.
- Do not run downstream promotion until source/control roots and canonical merge pass.

Next:
- Preserve the Current Cursor next action for R6. Use v4 request drafts for owner/operator submission, or record explicit `FLIP` approval. Only after ticket/export identifiers, verifier-native rows, and provenance arrive should `/tmp/ict-engine-board-a-r6-owner-export-v1` be populated under shared lock and the full chain rerun.
"""
    (OUT / "current_objective_completion_audit_after_v4_requests_v1.md").write_text(report)

    assertions = {
        "run_id": payload["run_id"] == RUN_ID,
        "gate_result": payload["gate_result"].endswith("not_complete_owner_export_and_regime_acceptance_blocked"),
        "board_present": BOARD.exists(),
        "evidence_files_present": all(evidence_presence.values()),
        "r6_owner_export_absent": roots["r6_owner_export"]["present"] is False,
        "r3_native_subhour_absent": roots["r3_native_subhour"]["present"] is False,
        "r5_recency_extension_absent": roots["r5_recency_extension"]["present"] is False,
        "source_label_equivalence_present": roots["source_label_equivalence"]["present"] is True,
        "accepted_labels_empty": payload["accepted_labels"] == [],
        "accepted_rows_added_zero": payload["accepted_rows_added"] == 0,
        "canonical_merge_allowed_false": payload["canonical_merge_allowed"] is False,
        "downstream_chain_rerun_allowed_false": payload["downstream_chain_rerun_allowed"] is False,
        "strict_full_objective_achieved_false": payload["strict_full_objective_achieved"] is False,
        "update_goal_false": payload["update_goal"] is False,
        "external_requests_sent_false": payload["external_requests_sent"] is False,
    }
    assertion_text = "\n".join(f"{k}={'PASS' if v else 'FAIL'}" for k, v in assertions.items()) + "\n"
    (CHECKS / "current_objective_completion_audit_after_v4_requests_v1_assertions.out").write_text(assertion_text)
    if not all(assertions.values()):
        raise SystemExit("assertions failed")


if __name__ == "__main__":
    main()
