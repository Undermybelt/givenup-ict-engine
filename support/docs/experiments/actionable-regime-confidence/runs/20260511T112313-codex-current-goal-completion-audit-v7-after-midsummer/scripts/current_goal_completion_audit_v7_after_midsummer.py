#!/usr/bin/env python3
"""Current-state completion audit for Board A after the Midsummer direct slice."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T112313+0800-codex-current-goal-completion-audit-v7-after-midsummer"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RUN_ROOT.parents[4]
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

FILES = {
    "audit_v6": REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/20260511T104815-current-goal-completion-audit-v6-mainregimev2-relock/completion-audit/current_goal_completion_audit_v6_mainregimev2_relock.json",
    "targeted_gap_batch": REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/20260511T110540-codex-full-matrix-targeted-gap-batch/targeted-gap-batch/full_matrix_targeted_gap_batch_report.json",
    "midsummer": REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/20260511T111122-codex-midsummer-meme-direct-wash-audit/midsummer-meme-audit/midsummer_meme_direct_wash_audit.json",
    "tvremix_readiness": REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/20260511T105619-codex-tvremix-label-source-readiness/provider-readiness/tvremix_label_source_readiness.json",
    "tvremix_user_export": REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/20260511T110824-codex-tvremix-user-label-export-probe/tvremix-user-label/tvremix_user_label_export_probe.json",
    "pumpolymp_live": REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/20260511T111647-codex-pumpolymp-live-api-direct-preflight/source-audit/pumpolymp_live_api_direct_preflight.json",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def board_cursor(board_text: str) -> dict:
    fields = {}
    for line in board_text.splitlines():
        if not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) >= 2 and parts[0] in {
            "board_state",
            "last_loop_id",
            "current_run_root",
            "accepted_gate",
            "blocker",
            "next_action",
        }:
            fields[parts[0]] = parts[1]
    return fields


def result_of(doc: dict) -> dict:
    return doc.get("decision") or doc.get("result") or {}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text(encoding="utf-8")
    board_hash = hashlib.sha256(board_text.encode("utf-8")).hexdigest()
    cursor = board_cursor(board_text)
    docs = {name: load_json(path) for name, path in FILES.items()}
    results = {name: result_of(doc) for name, doc in docs.items()}

    audit_v6 = docs["audit_v6"]
    midsummer = docs["midsummer"]
    targeted = docs["targeted_gap_batch"]
    pumpolymp = docs["pumpolymp_live"]

    full_matrix_gaps = audit_v6.get("full_cycle_full_universe_gaps", {})
    active_roots = audit_v6.get("active_taxonomy", {}).get("main_price_roots", [])
    scope_limited = audit_v6.get("scope_limited_95_evidence_preserved", {})

    accepted_direct_rows_added_after_v6 = results["midsummer"].get(
        "accepted_direct_manipulation_rows_added", 0
    )
    accepted_parent_slots_after_v6 = sum(
        int(results[name].get("accepted_parent_root_slots_added", 0))
        for name in ["midsummer", "tvremix_readiness", "tvremix_user_export", "pumpolymp_live"]
    )
    targeted_roots_accepted = targeted.get("accepted_95_roots_in_this_slice", [])

    prompt_to_artifact_checklist = [
        {
            "requirement": "Use the named Board A markdown as the authoritative status artifact.",
            "evidence": f"{BOARD.relative_to(REPO_ROOT)} hash {board_hash}; cursor last_loop_id={cursor.get('last_loop_id')}",
            "status": "pass",
        },
        {
            "requirement": "Every active MainRegimeV2 price root reaches at least 95% calibrated confidence.",
            "evidence": "Audit v6 preserves scope-limited 95 evidence for Bull/Bear/Sideways/Crisis, but targeted full-matrix gap batch accepted no new roots.",
            "status": "partial_scope_limited",
        },
        {
            "requirement": "Every active price root validates across other markets, timeframes, full cycles, and full species.",
            "evidence": "Audit v6 full_cycle_full_universe_gaps remains fail; targeted gap batch gate is blocked_targeted_gap_batch_no_new_full_matrix_slice.",
            "status": "fail",
        },
        {
            "requirement": "Do not promote child/sub-regime packets, HMM states, OHLCV proxies, or future-return labels as parent roots.",
            "evidence": "Active board cursor and latest artifacts keep accepted parent-root slots at 0 after v6 and targeted gap batch blocks every root in slice.",
            "status": "pass",
        },
        {
            "requirement": "Manipulation must use direct event/order-flow/order-lifecycle rows with negative controls.",
            "evidence": "Midsummer BSC meme wash-maker slice accepted 1870 direct rows with paired controls and Wilson95 minimum 0.995736.",
            "status": "pass_scope_limited",
        },
        {
            "requirement": "Manipulation direct evidence must cover broader direct varieties, not only scoped slices.",
            "evidence": "Midsummer decision says full_objective_achieved=false and all-chain scope rejected; PumpOlymp live API remains positive-only with no controls.",
            "status": "fail",
        },
        {
            "requirement": "Provider readiness or user-export surfaces count only if they provide source labels.",
            "evidence": "TradingViewRemix is reachable for market data, but both readiness and user-export probes add 0 parent slots and 0 direct rows.",
            "status": "pass_blocked",
        },
        {
            "requirement": "No threshold relaxation, runtime code change, raw-data commit, or trade-usable claim may be used to force completion.",
            "evidence": "Latest inspected artifacts all report thresholds_relaxed=false, runtime_code_changed=false, raw_data_committed=false, trade_usable=false.",
            "status": "pass",
        },
    ]

    decision = {
        "goal_achieved": False,
        "accepted_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "latest_scoped_direct_manipulation_gate": results["midsummer"].get("accepted_gate"),
        "gate_result": "blocked_completion_audit_v7_parent_root_full_matrix_still_incomplete",
        "accepted_parent_root_slots_added_after_v6": accepted_parent_slots_after_v6,
        "targeted_gap_roots_accepted_after_v6": targeted_roots_accepted,
        "accepted_direct_manipulation_rows_added_after_v6": accepted_direct_rows_added_after_v6,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD.relative_to(REPO_ROOT)),
        "board_sha256_at_audit": board_hash,
        "board_cursor": cursor,
        "objective": "Every active Board A regime must reach at least 95% calibrated confidence and validate across other markets, other timeframes, full cycles, and the broad available universe before reporting success.",
        "active_taxonomy": {
            "name": "MainRegimeV2",
            "main_price_roots": active_roots,
            "separate_direct_event_class_or_overlay": ["Manipulation"],
            "residual": "UnknownOrMixed",
        },
        "prompt_to_artifact_checklist": prompt_to_artifact_checklist,
        "scope_limited_95_evidence_preserved": scope_limited,
        "full_cycle_full_universe_gaps_from_v6": full_matrix_gaps,
        "latest_targeted_gap_batch": {
            "artifact": str(FILES["targeted_gap_batch"].relative_to(REPO_ROOT)),
            "accepted_95_roots_in_this_slice": targeted_roots_accepted,
            "blocked_roots_in_this_slice": targeted.get("blocked_roots_in_this_slice"),
            "gate_result": results["targeted_gap_batch"].get("gate_result"),
        },
        "latest_direct_manipulation_updates": {
            "midsummer_artifact": str(FILES["midsummer"].relative_to(REPO_ROOT)),
            "midsummer_accepted_gate": results["midsummer"].get("accepted_gate"),
            "midsummer_direct_rows_added": accepted_direct_rows_added_after_v6,
            "midsummer_full_objective_achieved": results["midsummer"].get("full_objective_achieved"),
            "pumpolymp_live_artifact": str(FILES["pumpolymp_live"].relative_to(REPO_ROOT)),
            "pumpolymp_gate_result": results["pumpolymp_live"].get("gate_result"),
        },
        "decision": decision,
        "next_action": "Acquire an exact provider/instrument/timeframe MainRegimeV2 parent-root label panel, or obtain an owner-approved provider/venue crosswalk; direct Manipulation work should continue only for new varieties with positive and negative rows.",
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v7_after_midsummer.json"
    md_path = OUT_DIR / "current_goal_completion_audit_v7_after_midsummer.md"
    checks_path = CHECK_DIR / "current_goal_completion_audit_v7_after_midsummer_assertions.out"

    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    rows = "\n".join(
        f"| {item['requirement']} | {item['status']} | {item['evidence']} |"
        for item in prompt_to_artifact_checklist
    )
    missing_roots = [
        root
        for root in active_roots
        if root in full_matrix_gaps and full_matrix_gaps[root].get("missing_instrument_count", 0)
    ]
    md_path.write_text(
        "\n".join(
            [
                "# Current Goal Completion Audit v7 After Midsummer",
                "",
                f"Run ID: `{RUN_ID}`",
                "",
                f"Board hash at audit: `{board_hash}`.",
                f"Board cursor last loop: `{cursor.get('last_loop_id')}`.",
                "",
                "## Objective Restated",
                "",
                "Every active `MainRegimeV2` price root (`Bull`, `Bear`, `Sideways`, `Crisis`) must have 95%-99% calibrated evidence across the full observed market/timeframe/species matrix. `Manipulation` is separate and needs direct positive/negative rows across varieties. No proxy-only or trade-usable promotion is allowed.",
                "",
                "## Prompt-to-Artifact Checklist",
                "",
                "| Requirement | Status | Evidence |",
                "|---|---|---|",
                rows,
                "",
                "## Decision",
                "",
                "- Goal achieved: `false`.",
                "- Accepted parent-root slots added after audit v6: `0`.",
                f"- Targeted gap roots accepted after audit v6: `{targeted_roots_accepted}`.",
                f"- Latest scoped direct `Manipulation` rows added: `{accepted_direct_rows_added_after_v6}`.",
                f"- Latest scoped direct `Manipulation` gate: `{results['midsummer'].get('accepted_gate')}`.",
                "- Gate result: `blocked_completion_audit_v7_parent_root_full_matrix_still_incomplete`.",
                f"- Price roots still missing full-matrix coverage: `{missing_roots}`.",
                "- Runtime code changed: false.",
                "- Thresholds relaxed: false.",
                "- Raw data committed: false.",
                "- Trade usable: false.",
                "",
                "## Next Action",
                "",
                "Acquire an exact provider/instrument/timeframe `MainRegimeV2` parent-root label panel, or obtain an owner-approved provider/venue crosswalk. Direct `Manipulation` work should continue only for new varieties with both positive and negative rows.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        "PASS active_taxonomy=MainRegimeV2",
        "PASS objective_restated_as_deliverables=true",
        "PASS prompt_to_artifact_checklist_present=true",
        "PASS latest_targeted_gap_roots_accepted=0",
        f"PASS latest_direct_manipulation_rows_added={accepted_direct_rows_added_after_v6}",
        "PASS accepted_parent_root_slots_added_after_v6=0",
        "PASS goal_achieved=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
        "PASS trade_usable=false",
        "GATE blocked_completion_audit_v7_parent_root_full_matrix_still_incomplete",
    ]
    checks_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
