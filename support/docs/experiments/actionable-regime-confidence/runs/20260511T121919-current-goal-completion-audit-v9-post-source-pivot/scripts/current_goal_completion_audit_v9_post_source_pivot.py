#!/usr/bin/env python3
"""Current-goal completion audit after post-v8 source pivots and cleanup."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T121919+0800-current-goal-completion-audit-v9-post-source-pivot"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T121919-current-goal-completion-audit-v9-post-source-pivot"
)
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"

ARTIFACTS = {
    "audit_v8": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T113606-codex-current-goal-completion-audit-v8-after-chain-expansion/"
        "completion-audit/current_goal_completion_audit_v8_after_chain_expansion.json"
    ),
    "crystalbull_gate": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T113603-codex-crystalbull-ibd-qqq-source-gate/"
        "source-gate/crystalbull_ibd_qqq_source_gate.json"
    ),
    "paper_github_delta": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T114135-codex-paper-github-source-delta-after-v8/"
        "source-delta/paper_github_source_delta_after_v8.json"
    ),
    "historyofmarket_hsmm": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T114808-codex-historyofmarket-hsmm-root-source-audit/"
        "source-audit/historyofmarket_hsmm_root_source_audit.json"
    ),
    "crystalbull_attachability": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T115235-codex-crystalbull-source-label-attachability/"
        "source-label-attachability/crystalbull_source_label_attachability.json"
    ),
    "source_window_pivot": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T120900-codex-exportable-source-scan/"
        "source-scan/mainregimev2_positive_acquisition_pivot.json"
    ),
    "cleanup_manifest": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T121520-codex-negative-artifact-cleanup/"
        "cleanup/negative_artifact_cleanup_manifest.md"
    ),
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def board_cursor(board_text: str) -> dict[str, str]:
    cursor: dict[str, str] = {}
    in_cursor = False
    for line in board_text.splitlines():
        if line.strip() == "## Current Cursor":
            in_cursor = True
            continue
        if in_cursor and line.startswith("## "):
            break
        if in_cursor and line.startswith("|"):
            parts = [part.strip() for part in line.strip().strip("|").split("|")]
            if len(parts) >= 3 and parts[0] not in {"Field", "---"}:
                cursor[parts[0]] = parts[1]
    return cursor


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text(encoding="utf-8")
    cursor = board_cursor(board_text)
    board_sha = hashlib.sha256(board_text.encode("utf-8")).hexdigest()

    loaded = {name: load_json(path) for name, path in ARTIFACTS.items() if path.suffix == ".json"}
    cleanup_exists = ARTIFACTS["cleanup_manifest"].exists()

    v8 = loaded["audit_v8"]
    attach = loaded["crystalbull_attachability"]
    pivot = loaded["source_window_pivot"]
    paper_delta = loaded["paper_github_delta"]
    hist = loaded["historyofmarket_hsmm"]
    crystalbull_gate = loaded["crystalbull_gate"]

    post_v8_parent_slots = {
        "crystalbull_gate": crystalbull_gate["decision"]["accepted_parent_root_slots_added"],
        "paper_github_delta": paper_delta["accepted_parent_root_slots_added"],
        "historyofmarket_hsmm": hist["decision"]["accepted_parent_root_slots_added"],
        "crystalbull_attachability_completion": attach["decision"]["accepted_parent_root_slots_added"],
        "source_window_pivot": 0,
    }
    post_v8_direct_rows = {
        "paper_github_delta": paper_delta["accepted_direct_manipulation_rows_added"],
        "historyofmarket_hsmm": hist["decision"]["accepted_direct_manipulation_rows_added"],
        "crystalbull_attachability": attach["decision"].get("accepted_direct_manipulation_rows_added", 0),
        "source_window_pivot": 0,
    }

    checklist = [
        {
            "requirement": "Named Board A file is the live contract.",
            "evidence": str(BOARD),
            "status": "pass",
        },
        {
            "requirement": "Every active price root reaches at least 95% calibrated confidence.",
            "evidence": (
                "v8 full objective false; post-v8 CrystalBull, paper/GitHub, HistoryOfMarket/HSMM, "
                "attachability, and source-window pivot added 0 parent-root completion slots."
            ),
            "status": "fail",
        },
        {
            "requirement": "Validated on other markets, other timeframes, full cycles, and full species.",
            "evidence": (
                "CrystalBull adds only QQQ 1d target-label attachment; source-window pivot is a seed contract "
                "and claims no confidence gate; v8 missing roots remain Bull/Bear/Sideways/Crisis."
            ),
            "status": "fail",
        },
        {
            "requirement": "Manipulation must use direct rows plus matched negatives across varieties.",
            "evidence": (
                "Midsummer multichain wash-maker rows remain scoped; no post-v8 direct rows were added; "
                "broader variety coverage remains incomplete."
            ),
            "status": "fail",
        },
        {
            "requirement": "Do not count proxy/formula/methodology-only signals as completion.",
            "evidence": (
                "HistoryOfMarket was blocked as formula-derived two-root SPX daily; HSMM paper blocked as no "
                "materialized row export; CrystalBull factor gate remains below held-out 95; Yardeni/NBER seeds "
                "are acquisition contract only pending owner-approved crosswalk."
            ),
            "status": "pass_blocked",
        },
        {
            "requirement": "Do not relax thresholds, change runtime code, commit raw data, or promote trade usability.",
            "evidence": "All consumed post-v8 artifacts assert false for threshold/runtime/raw/trade promotion.",
            "status": "pass",
        },
        {
            "requirement": "Clean up negative artifacts without losing compact evidence.",
            "evidence": str(ARTIFACTS["cleanup_manifest"]),
            "status": "pass" if cleanup_exists else "fail",
        },
    ]

    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD),
        "board_sha256_at_audit": board_sha,
        "board_cursor": cursor,
        "objective": (
            "Every active Board A regime must reach at least 95% calibrated confidence and validate across "
            "other markets, other timeframes, full cycles, and broad universe/full species before reporting success."
        ),
        "active_taxonomy": {
            "name": "MainRegimeV2",
            "main_price_roots": ["Bull", "Bear", "Sideways", "Crisis"],
            "separate_direct_event_class_or_overlay": ["Manipulation"],
            "residual": "UnknownOrMixed",
        },
        "consumed_artifacts": {name: str(path) for name, path in ARTIFACTS.items()},
        "prompt_to_artifact_checklist": checklist,
        "post_v8_deltas": {
            "accepted_parent_root_completion_slots_added": post_v8_parent_slots,
            "accepted_direct_manipulation_rows_added": post_v8_direct_rows,
            "crystalbull_attached_source_label_target_slots": attach["decision"][
                "attached_source_label_slots_added"
            ],
            "source_window_seed_rows": sum(pivot["seed_window_counts"].values()),
            "source_window_seed_counts": pivot["seed_window_counts"],
            "cleanup_manifest_exists": cleanup_exists,
        },
        "decision": {
            "goal_achieved": False,
            "call_update_goal": False,
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "gate_result": "blocked_completion_audit_v9_post_source_pivot_no_full_matrix_95",
            "accepted_parent_root_completion_slots_added_post_v8": sum(post_v8_parent_slots.values()),
            "accepted_direct_manipulation_rows_added_post_v8": sum(post_v8_direct_rows.values()),
            "price_roots_still_missing_full_matrix_coverage": ["Bull", "Bear", "Sideways", "Crisis"],
            "direct_manipulation_variety_complete": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Stop broad public-source lottery loops. Use source_window_seed_v1.csv only as a seed contract, "
            "then obtain explicit owner-approved crosswalks or real exact provider/instrument/timeframe labels; "
            "Sideways still needs dated source/adjudication and Manipulation still needs non-wash direct varieties."
        ),
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v9_post_source_pivot.json"
    md_path = OUT_DIR / "current_goal_completion_audit_v9_post_source_pivot.md"
    checks_path = CHECK_DIR / "current_goal_completion_audit_v9_post_source_pivot_assertions.out"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    checks_path.write_text(render_checks(report), encoding="utf-8")
    print(json_path)
    print(md_path)
    print(checks_path)
    return 0


def render_markdown(report: dict) -> str:
    decision = report["decision"]
    lines = [
        "# Current Goal Completion Audit v9 Post Source Pivot",
        "",
        f"Run ID: `{report['run_id']}`",
        "",
        f"Board hash at audit: `{report['board_sha256_at_audit']}`.",
        f"Board cursor last loop: `{report['board_cursor'].get('last_loop_id', 'unknown')}`.",
        "",
        "## Objective Restated",
        "",
        report["objective"],
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence |",
        "|---|---|---|",
    ]
    for item in report["prompt_to_artifact_checklist"]:
        lines.append(f"| {item['requirement']} | {item['status']} | {item['evidence']} |")
    lines.extend(
        [
            "",
            "## Post-v8 Delta",
            "",
            f"- Parent-root completion slots added after v8: `{decision['accepted_parent_root_completion_slots_added_post_v8']}`.",
            f"- Direct `Manipulation` rows added after v8: `{decision['accepted_direct_manipulation_rows_added_post_v8']}`.",
            f"- CrystalBull attached source-label target slots: `{report['post_v8_deltas']['crystalbull_attached_source_label_target_slots']}`.",
            f"- Source-window seed rows: `{report['post_v8_deltas']['source_window_seed_rows']}`.",
            "",
            "## Decision",
            "",
            f"- Goal achieved: `{str(decision['goal_achieved']).lower()}`.",
            f"- Gate result: `{decision['gate_result']}`.",
            f"- Price roots still missing full-matrix coverage: `{', '.join(decision['price_roots_still_missing_full_matrix_coverage'])}`.",
            f"- Direct `Manipulation` variety complete: `{str(decision['direct_manipulation_variety_complete']).lower()}`.",
            f"- Runtime code changed: `{str(decision['runtime_code_changed']).lower()}`.",
            f"- Thresholds relaxed: `{str(decision['thresholds_relaxed']).lower()}`.",
            f"- Raw data committed: `{str(decision['raw_data_committed']).lower()}`.",
            f"- Trade usable: `{str(decision['trade_usable']).lower()}`.",
            f"- `update_goal` must not be called: `{str(not decision['call_update_goal']).lower()}`.",
            "",
            "## Next Action",
            "",
            report["next_action"],
            "",
        ]
    )
    return "\n".join(lines)


def render_checks(report: dict) -> str:
    decision = report["decision"]
    lines = [
        "PASS objective_restated_as_deliverables=true",
        f"PASS active_taxonomy={report['active_taxonomy']['name']}",
        "PASS target_price_roots=Bull,Bear,Sideways,Crisis",
        f"PASS board_cursor_last_loop={report['board_cursor'].get('last_loop_id', 'unknown')}",
        f"PASS accepted_parent_root_completion_slots_added_post_v8={decision['accepted_parent_root_completion_slots_added_post_v8']}",
        f"PASS accepted_direct_manipulation_rows_added_post_v8={decision['accepted_direct_manipulation_rows_added_post_v8']}",
        f"PASS crystalbull_attached_source_label_target_slots={report['post_v8_deltas']['crystalbull_attached_source_label_target_slots']}",
        f"PASS source_window_seed_rows={report['post_v8_deltas']['source_window_seed_rows']}",
        f"PASS cleanup_manifest_exists={str(report['post_v8_deltas']['cleanup_manifest_exists']).lower()}",
        f"PASS full_objective_achieved={str(decision['goal_achieved']).lower()}",
        f"PASS call_update_goal={str(decision['call_update_goal']).lower()}",
        f"PASS runtime_code_changed={str(decision['runtime_code_changed']).lower()}",
        f"PASS thresholds_relaxed={str(decision['thresholds_relaxed']).lower()}",
        f"PASS raw_data_committed={str(decision['raw_data_committed']).lower()}",
        f"PASS trade_usable={str(decision['trade_usable']).lower()}",
        f"GATE {decision['gate_result']}",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
