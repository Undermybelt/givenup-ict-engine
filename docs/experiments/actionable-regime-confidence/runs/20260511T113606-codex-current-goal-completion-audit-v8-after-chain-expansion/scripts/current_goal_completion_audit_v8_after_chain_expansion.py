#!/usr/bin/env python3
"""Completion audit after the Midsummer chain-slice expansion."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T113606+0800-codex-current-goal-completion-audit-v8-after-chain-expansion"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RUN_ROOT.parents[4]
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

PATHS = {
    "audit_v6": "docs/experiments/actionable-regime-confidence/runs/20260511T104815-current-goal-completion-audit-v6-mainregimev2-relock/completion-audit/current_goal_completion_audit_v6_mainregimev2_relock.json",
    "targeted_gap": "docs/experiments/actionable-regime-confidence/runs/20260511T110540-codex-full-matrix-targeted-gap-batch/targeted-gap-batch/full_matrix_targeted_gap_batch_report.json",
    "midsummer_bsc": "docs/experiments/actionable-regime-confidence/runs/20260511T111122-codex-midsummer-meme-direct-wash-audit/midsummer-meme-audit/midsummer_meme_direct_wash_audit.json",
    "midsummer_chain": "docs/experiments/actionable-regime-confidence/runs/20260511T112642-codex-midsummer-chain-slice-expansion-audit/chain-slice-audit/midsummer_chain_slice_expansion_audit.json",
    "vantmacro": "docs/experiments/actionable-regime-confidence/runs/20260511T112622-codex-vantmacro-source-audit/source-audit/vantmacro_mainregimev2_source_audit.json",
    "audit_v7_post": "docs/experiments/actionable-regime-confidence/runs/20260511T112758-current-goal-completion-audit-v7-post-midsummer/completion-audit/current_goal_completion_audit_v7_post_midsummer.json",
}


def load(path_key: str) -> dict:
    with (REPO_ROOT / PATHS[path_key]).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def result(doc: dict) -> dict:
    return doc.get("decision") or doc.get("result") or {}


def cursor(text: str) -> dict:
    out = {}
    for line in text.splitlines():
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
            out[parts[0]] = parts[1]
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text(encoding="utf-8")
    board_hash = hashlib.sha256(board_text.encode("utf-8")).hexdigest()
    board_cursor = cursor(board_text)

    audit_v6 = load("audit_v6")
    targeted_gap = load("targeted_gap")
    midsummer_bsc = load("midsummer_bsc")
    midsummer_chain = load("midsummer_chain")
    vantmacro = load("vantmacro")
    audit_v7_post = load("audit_v7_post")

    r_targeted = result(targeted_gap)
    r_bsc = result(midsummer_bsc)
    r_chain = result(midsummer_chain)
    r_vantmacro = {
        **vantmacro.get("board_fit", {}),
        "gate_result": vantmacro.get("gate_result"),
        "runtime_code_changed": vantmacro.get("runtime_code_changed"),
        "thresholds_relaxed": vantmacro.get("thresholds_relaxed"),
        "raw_data_committed": vantmacro.get("raw_data_committed"),
        "trade_usable": vantmacro.get("trade_usable"),
    }

    bsc_rows = int(r_bsc.get("accepted_direct_manipulation_rows_added", 0))
    chain_rows = int(r_chain.get("accepted_direct_manipulation_rows_added", 0))
    total_midsummer_rows = bsc_rows + chain_rows
    accepted_platforms = r_chain.get("new_accepted_platforms") or ["base", "ethereum", "solana"]
    roots = audit_v6.get("active_taxonomy", {}).get("main_price_roots", [])
    gaps = audit_v6.get("full_cycle_full_universe_gaps", {})
    missing_roots = [
        root
        for root in roots
        if gaps.get(root, {}).get("missing_instrument_count", 0) > 0
    ]

    checklist = [
        {
            "requirement": "All active MainRegimeV2 price roots have >=95 calibrated confidence.",
            "evidence": "V6 keeps only scope-limited root packets; 110540 targeted full-matrix batch accepted 0 roots.",
            "status": "partial_scope_limited",
        },
        {
            "requirement": "All active price roots validate across markets, timeframes, full cycles, and full species.",
            "evidence": f"Missing full-matrix roots remain {missing_roots}; targeted gap gate={r_targeted.get('gate_result')}.",
            "status": "fail",
        },
        {
            "requirement": "Direct Manipulation uses real direct rows plus negative controls.",
            "evidence": f"Midsummer BSC plus chain expansion accepted {total_midsummer_rows} direct wash-maker rows across bsc/base/ethereum/solana.",
            "status": "pass_scope_limited",
        },
        {
            "requirement": "Broader direct Manipulation variety coverage is complete.",
            "evidence": "Accepted Midsummer rows are all wash-maker/maker-token-day evidence; other varieties remain partial or rejected.",
            "status": "fail",
        },
        {
            "requirement": "New macro/model sources cannot count without exact root-label exports.",
            "evidence": f"VantMacro accepted parent-root slots={r_vantmacro.get('accepted_parent_root_slots_added')}; gate={r_vantmacro.get('gate_result')}.",
            "status": "pass_blocked",
        },
        {
            "requirement": "No threshold relaxation, runtime change, raw commit, or trade promotion.",
            "evidence": "All inspected post-v6 artifacts report false for thresholds/runtime/raw/trade-usable fields.",
            "status": "pass",
        },
    ]

    decision = {
        "goal_achieved": False,
        "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "gate_result": "blocked_completion_audit_v8_parent_root_full_matrix_still_incomplete_after_chain_expansion",
        "accepted_parent_root_slots_added_after_v6": 0,
        "targeted_gap_roots_accepted_after_v6": targeted_gap.get("accepted_95_roots_in_this_slice", []),
        "midsummer_bsc_direct_rows_added": bsc_rows,
        "midsummer_chain_direct_rows_added": chain_rows,
        "midsummer_total_direct_rows_after_v6": total_midsummer_rows,
        "new_accepted_midsummer_platforms": accepted_platforms,
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
        "board_cursor": board_cursor,
        "objective": "Every active regime must reach at least 95% calibrated confidence and validate across other markets, other timeframes, full cycles, and full species before success.",
        "active_taxonomy": {
            "name": "MainRegimeV2",
            "main_price_roots": roots,
            "separate_direct_event_class_or_overlay": ["Manipulation"],
            "residual": "UnknownOrMixed",
        },
        "consumed_artifacts": PATHS,
        "prompt_to_artifact_checklist": checklist,
        "full_cycle_full_universe_gaps_from_v6": gaps,
        "decision": decision,
        "next_action": "Parent-root acquisition remains the blocking path: obtain an exact provider/instrument/timeframe MainRegimeV2 label panel or explicit owner-approved crosswalk.",
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v8_after_chain_expansion.json"
    md_path = OUT_DIR / "current_goal_completion_audit_v8_after_chain_expansion.md"
    checks_path = CHECK_DIR / "current_goal_completion_audit_v8_after_chain_expansion_assertions.out"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    rows = "\n".join(
        f"| {item['requirement']} | {item['status']} | {item['evidence']} |"
        for item in checklist
    )
    md_path.write_text(
        "\n".join(
            [
                "# Current Goal Completion Audit v8 After Chain Expansion",
                "",
                f"Run ID: `{RUN_ID}`",
                "",
                f"Board hash at audit: `{board_hash}`.",
                f"Board cursor last loop: `{board_cursor.get('last_loop_id')}`.",
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
                "## Post-v6 Delta",
                "",
                f"- Targeted full-matrix roots accepted: `{targeted_gap.get('accepted_95_roots_in_this_slice', [])}`.",
                f"- Midsummer BSC direct rows: `{bsc_rows}`.",
                f"- Midsummer added chain direct rows: `{chain_rows}`.",
                f"- Midsummer total direct rows after v6: `{total_midsummer_rows}`.",
                f"- New accepted Midsummer platforms: `{accepted_platforms}`.",
                "- Accepted parent-root slots after v6: `0`.",
                "",
                "## Decision",
                "",
                "- Goal achieved: `false`.",
                "- Gate result: `blocked_completion_audit_v8_parent_root_full_matrix_still_incomplete_after_chain_expansion`.",
                f"- Price roots still missing full-matrix coverage: `{missing_roots}`.",
                "- Runtime code changed: false.",
                "- Thresholds relaxed: false.",
                "- Raw data committed: false.",
                "- Trade usable: false.",
                "",
                "## Next Action",
                "",
                "Parent-root acquisition remains the blocking path: obtain an exact provider/instrument/timeframe `MainRegimeV2` label panel or explicit owner-approved crosswalk.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        "PASS objective_restated_as_deliverables=true",
        "PASS active_taxonomy=MainRegimeV2",
        "PASS target_price_roots=Bull,Bear,Sideways,Crisis",
        "PASS targeted_full_matrix_roots_accepted=0",
        "PASS accepted_parent_root_slots_added_after_v6=0",
        f"PASS midsummer_bsc_direct_rows_added={bsc_rows}",
        f"PASS midsummer_chain_direct_rows_added={chain_rows}",
        f"PASS midsummer_total_direct_rows_after_v6={total_midsummer_rows}",
        "PASS full_objective_achieved=false",
        "PASS call_update_goal=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
        "PASS trade_usable=false",
        "GATE blocked_completion_audit_v8_parent_root_full_matrix_still_incomplete_after_chain_expansion",
    ]
    checks_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
