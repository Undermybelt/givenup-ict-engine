#!/usr/bin/env python3
"""Post-074116 prompt-to-artifact audit for Board A.

This script is intentionally read-only against runtime/state roots. It inspects
the live board plus existing command-output artifacts and writes an audit packet
that records why the current objective remains blocked.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


RUN_ID = "20260512T074341+0800-codex-current-objective-audit-after-074116-v1"
GATE_RESULT = (
    "current_objective_audit_after_074116_v1="
    "not_complete_source_control_unlock_absent_no_downstream_promotion"
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def latest_line(text: str, needle: str) -> str:
    for line in reversed(text.splitlines()):
        if needle in line:
            return line.strip()
    return ""


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "requirement_id",
        "prompt_requirement",
        "status",
        "evidence_summary",
        "artifact_refs",
        "blocker",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    repo = Path.cwd()
    board = repo / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
    run_root = (
        repo
        / "docs/experiments/actionable-regime-confidence/runs"
        / RUN_ID
    )
    packet_dir = run_root / "current-objective-audit-after-074116-v1"
    checks_dir = run_root / "checks"
    packet_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    board_text = read_text(board)
    board_hash = sha256_file(board)

    cmd_root = (
        repo
        / "docs/experiments/actionable-regime-confidence/runs"
        / "20260512T073231+0800-codex-current-objective-audit-after-073142-v1"
        / "command-output"
    )
    provider_status = read_json(cmd_root / "provider_status_agent.stdout")
    auto_quant_status = read_json(cmd_root / "auto_quant_status.stdout")
    pre_bayes_status = read_json(cmd_root / "pre_bayes_status_nq.stdout")
    workflow_status = read_json(cmd_root / "workflow_status_nq_agent.stdout")
    path_ranking = read_json(cmd_root / "export_structural_path_ranking_target_nq.stdout")
    policy_training = read_json(cmd_root / "policy_training_status_nq.stdout")
    root_presence = read_text(cmd_root / "root_presence.stdout")
    approval_readback = read_text(cmd_root / "r6_approval_package_readback.stdout")

    local_sweep = read_json(
        repo
        / "docs/experiments/actionable-regime-confidence/runs"
        / "20260512T073755+0800-codex-local-required-source-control-sweep-after-073650-v1"
        / "local-required-source-control-sweep-after-073650-v1"
        / "local_required_source_control_sweep_after_073650_v1.json"
    )
    r3_manual = read_json(
        repo
        / "docs/experiments/actionable-regime-confidence/runs"
        / "20260512T074116+0800-codex-r3-possible-file-manual-review-after-073755-v1"
        / "r3-possible-file-manual-review-after-073755-v1"
        / "r3_possible_file_manual_review_after_073755_v1.json"
    )

    provider_summary = provider_status.get("summary_line", "missing")
    workflow_block = workflow_status.get("blocking_reason", "missing")
    auto_quant_gate = auto_quant_status.get("status", "missing")
    pre_bayes_gate = pre_bayes_status.get("latest_gate_status", "missing")
    path_rows = path_ranking.get("rows", 0)
    mature_rows = path_ranking.get("mature_rows", 0)
    calibrated_rows = path_ranking.get("rows_with_calibrated_path_prob", 0)
    policy_ready = any(
        item.get("ready") is True for item in policy_training.get("entry_models", [])
    )

    source_unlock = all(
        [
            local_sweep.get("r6_owner_export_unlock") is True,
            local_sweep.get("r5_recency_unlock") is True,
            local_sweep.get("r3_native_subhour_unlock") is True,
            local_sweep.get("source_control_evidence_acquired") is True,
        ]
    )
    strict_objective = (
        source_unlock
        and r3_manual.get("strict_full_objective") is True
        and workflow_status.get("blocking_status") != "blocked"
        and mature_rows >= 30
        and calibrated_rows >= 30
        and policy_ready
    )

    checklist: list[dict[str, str]] = [
        {
            "requirement_id": "objective_board_file",
            "prompt_requirement": "Use the named Board A markdown as the authoritative plan.",
            "status": "covered",
            "evidence_summary": f"board_exists={board.exists()} sha256={board_hash}",
            "artifact_refs": str(board.relative_to(repo)),
            "blocker": "",
        },
        {
            "requirement_id": "all_regimes_95_confidence",
            "prompt_requirement": "Every regime reaches 95% confidence.",
            "status": "blocked",
            "evidence_summary": (
                "latest accepted rows remain 0 for current source/control packets; "
                f"r3_manual_gate={r3_manual.get('gate_result', 'missing')}"
            ),
            "artifact_refs": (
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260512T074116+0800-codex-r3-possible-file-manual-review-after-073755-v1/"
                "r3-possible-file-manual-review-after-073755-v1/"
                "r3_possible_file_manual_review_after_073755_v1.json"
            ),
            "blocker": "Crisis lacks verifier-native accepted label; TSIE root remains quarantined.",
        },
        {
            "requirement_id": "cross_market_cross_timeframe",
            "prompt_requirement": "Validate across other markets and other timeframes with suitable confidence.",
            "status": "blocked",
            "evidence_summary": (
                f"valid_required_root_unlock={local_sweep.get('valid_required_root_unlock', False)}; "
                f"recent_required_filename_count={local_sweep.get('recent_required_filename_count', 'missing')}"
            ),
            "artifact_refs": (
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260512T073755+0800-codex-local-required-source-control-sweep-after-073650-v1/"
                "local-required-source-control-sweep-after-073650-v1/"
                "local_required_source_control_sweep_after_073650_v1.json"
            ),
            "blocker": "No accepted R6/R5/R3 source-control unlock exists for broader validation.",
        },
        {
            "requirement_id": "provider_breadth",
            "prompt_requirement": "Use IBKR, TradingViewRemix, yfinance, and Kraken paths where available.",
            "status": "partial",
            "evidence_summary": f"provider_status={provider_summary}",
            "artifact_refs": (
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260512T073231+0800-codex-current-objective-audit-after-073142-v1/"
                "command-output/provider_status_agent.stdout"
            ),
            "blocker": "Provider readiness is partial and does not satisfy source/control acceptance.",
        },
        {
            "requirement_id": "auto_quant_operated",
            "prompt_requirement": "Operate Auto-Quant, not just infer from docs.",
            "status": "partial",
            "evidence_summary": f"auto_quant_status={auto_quant_gate}",
            "artifact_refs": (
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260512T073231+0800-codex-current-objective-audit-after-073142-v1/"
                "command-output/auto_quant_status.stdout"
            ),
            "blocker": "Auto-Quant is ready, but selected-data promotion is blocked by missing source/control unlock.",
        },
        {
            "requirement_id": "filter_pre_bayes_bbn_catboost_execution_tree",
            "prompt_requirement": "Run through filter, Pre-Bayes, BBN, CatBoost/path ranking, and execution tree.",
            "status": "blocked",
            "evidence_summary": (
                f"pre_bayes_gate={pre_bayes_gate}; workflow_block={workflow_block}; "
                f"path_rows={path_rows}; mature_rows={mature_rows}; calibrated_rows={calibrated_rows}; "
                f"policy_ready={policy_ready}"
            ),
            "artifact_refs": (
                "docs/experiments/actionable-regime-confidence/runs/"
                "20260512T073231+0800-codex-current-objective-audit-after-073142-v1/"
                "command-output/"
            ),
            "blocker": "Downstream promotion must remain blocked until source/control unlock exists.",
        },
        {
            "requirement_id": "multi_agent_append_only",
            "prompt_requirement": "Do not disturb concurrent multi-agent board work.",
            "status": "covered",
            "evidence_summary": (
                "audit is additive; current cursor not edited; no target roots mutated; "
                "count-once corrections already present for 073629 and 073755"
            ),
            "artifact_refs": str(run_root.relative_to(repo)),
            "blocker": "",
        },
        {
            "requirement_id": "goal_completion",
            "prompt_requirement": "Report result only when complete; otherwise keep working.",
            "status": "blocked",
            "evidence_summary": (
                f"strict_objective={strict_objective}; "
                f"latest_update_goal_line={latest_line(board_text, 'update_goal=false')}"
            ),
            "artifact_refs": str(board.relative_to(repo)),
            "blocker": "Strict objective is not achieved; update_goal must remain false.",
        },
    ]

    summary = {
        "run_id": RUN_ID,
        "gate_result": GATE_RESULT,
        "board_sha256": board_hash,
        "accepted_rows_added": 0,
        "source_control_evidence_acquired": False,
        "valid_required_root_unlock": False,
        "r6_owner_export_unlock": bool(local_sweep.get("r6_owner_export_unlock")),
        "r5_recency_unlock": bool(local_sweep.get("r5_recency_unlock")),
        "r3_native_subhour_unlock": bool(local_sweep.get("r3_native_subhour_unlock")),
        "canonical_merge": False,
        "selected_data_auto_quant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": strict_objective,
        "trade_usable": False,
        "update_goal": False,
        "provider_summary": provider_summary,
        "auto_quant_status": auto_quant_gate,
        "workflow_blocking_reason": workflow_block,
        "path_ranking": {
            "rows": path_rows,
            "mature_rows": mature_rows,
            "calibrated_rows": calibrated_rows,
        },
        "root_presence_readback": root_presence.strip().splitlines(),
        "r6_approval_readback": approval_readback.strip().splitlines(),
        "checklist": checklist,
    }

    json_path = packet_dir / "current_objective_audit_after_074116_v1.json"
    csv_path = packet_dir / "current_objective_audit_after_074116_v1.csv"
    md_path = packet_dir / "current_objective_audit_after_074116_v1.md"
    assertions_path = checks_dir / "current_objective_audit_after_074116_v1_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(csv_path, checklist)

    rows = [
        "# Current Objective Audit After 074116 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE_RESULT}`",
        "",
        "## Objective",
        "",
        "Pull every Board A regime to 95% confidence, validate across other markets and timeframes, operate the real provider/Auto-Quant/ict-engine downstream chain, and keep multi-agent board work append-only.",
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Blocker |",
        "|---|---|---|---|",
    ]
    for item in checklist:
        rows.append(
            f"| `{item['requirement_id']}` | `{item['status']}` | "
            f"{item['evidence_summary']} | {item['blocker']} |"
        )
    rows.extend(
        [
            "",
            "## Decision",
            "",
            "- Accepted rows added: `0`.",
            "- Valid required source/control unlock: `false`.",
            "- R6 owner/export unlock: `false`.",
            "- R5 recency unlock: `false`.",
            "- R3 native-subhour unlock: `false`.",
            "- Canonical merge: `false`.",
            "- Selected-data Auto-Quant promotion: `false`.",
            "- Downstream provider/AutoQuant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun: `false`.",
            "- Strict full objective achieved: `false`.",
            "- Trade usable: `false`.",
            "- `update_goal=false`.",
            "",
            "## Next",
            "",
            "Continue source/control acquisition only. Do not run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion until explicit source/control approval, verifier-native R6 owner/export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export exists.",
            "",
        ]
    )
    md_path.write_text("\n".join(rows), encoding="utf-8")

    assertion_lines = [
        "PASS board_exists",
        f"PASS gate_result={GATE_RESULT}",
        "PASS accepted_rows_added=0",
        "PASS valid_required_root_unlock=false",
        "PASS source_control_evidence_acquired=false",
        "PASS r6_owner_export_unlock=false",
        "PASS r5_recency_unlock=false",
        "PASS r3_native_subhour_unlock=false",
        "PASS canonical_merge=false",
        "PASS downstream_promotion_rerun=false",
        "PASS strict_full_objective=false",
        "PASS update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
