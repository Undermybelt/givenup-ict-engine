#!/usr/bin/env python3
"""Build a prompt-to-artifact completion audit for the active Board A objective."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T003646-codex-current-objective-completion-audit-v66"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "current-objective-completion-audit"
CMD = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
LIVE_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
OWNER_EXPORT_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

POLICY_REVIEW = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T003334-codex-r6-oystacher-exhibit-a-policy-review-v1"
    / "r6-oystacher-exhibit-a-policy-review/r6_oystacher_exhibit_a_policy_review_v1.json"
)
SOURCE_POLICY_REVIEW = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T003051-codex-r6-oystacher-exhibit-a-source-policy-review-v1"
    / "r6-oystacher-exhibit-a-source-policy-review/r6_oystacher_exhibit_a_source_policy_review_v1.json"
)
ROW_MATERIALIZATION = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1"
    / "r6-oystacher-exhibit-a-row-materialization/r6_oystacher_exhibit_a_row_materialization_v1.json"
)
APPROVAL_TEMPLATE = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T003017-codex-r6-split-contract-approval-template-v1"
    / "r6-split-contract-approval-template/validation_contract_approval_template_v1.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_verifier(name: str, intake_root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(intake_root)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    stdout = CMD / f"{name}.stdout.txt"
    stderr = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    stdout.write_text(proc.stdout, encoding="utf-8")
    stderr.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed: dict[str, Any] = {}
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {}
    return {
        "name": name,
        "intake_root": str(intake_root),
        "returncode": proc.returncode,
        "stdout_path": rel(stdout),
        "stderr_path": rel(stderr),
        "exit_path": rel(exit_path),
        "parsed": parsed,
    }


def parse_cursor(board_text: str) -> dict[str, str]:
    cursor: dict[str, str] = {}
    in_cursor = False
    for line in board_text.splitlines():
        if line.strip() == "## Current Cursor":
            in_cursor = True
            continue
        if in_cursor and line.startswith("## "):
            break
        if in_cursor and line.startswith("|") and not line.startswith("|---") and "Field" not in line:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 2:
                cursor[cells[0]] = cells[1]
    return cursor


def status_row(requirement: str, status: str, evidence: str, gap: str, next_action: str) -> dict[str, str]:
    return {
        "requirement": requirement,
        "status": status,
        "evidence": evidence,
        "gap": gap,
        "next_action": next_action,
    }


def main() -> int:
    for path in [OUT, CMD, CHECKS]:
        path.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text(encoding="utf-8")
    cursor = parse_cursor(board_text)
    board_hash = sha256(BOARD)
    current_run_root_text = cursor.get("current_run_root", "").strip("`")
    cursor_policy_review = (
        REPO
        / current_run_root_text
        / "r6-oystacher-exhibit-a-policy-review/r6_oystacher_exhibit_a_policy_review_v1.json"
        if current_run_root_text
        else POLICY_REVIEW
    )
    policy_review_path = cursor_policy_review if cursor_policy_review.exists() else POLICY_REVIEW
    policy = load_json(policy_review_path)
    source_policy = load_json(SOURCE_POLICY_REVIEW)
    materialization = load_json(ROW_MATERIALIZATION)
    approval_template_exists = APPROVAL_TEMPLATE.exists()
    live_verifier = run_verifier("live_direct_manipulation_row_intake_verifier", LIVE_INTAKE)
    owner_verifier = run_verifier("owner_export_target_verifier", OWNER_EXPORT_ROOT)

    last_loop_id = cursor.get("last_loop_id", "")
    accepted_gate = cursor.get("accepted_gate", "")
    blocker = cursor.get("blocker", "")
    next_action = cursor.get("next_action", "")
    board_state = cursor.get("board_state", "")
    policy_gate = policy.get("gate_result", "") or policy.get("decision", {}).get("gate_result", "")
    materialization_gate = materialization.get("gate_result", "")
    source_policy_gate = source_policy.get("gate_result", "")

    checklist = [
        status_row(
            "Use named Board A markdown as authority",
            "pass",
            f"board_sha256={board_hash}; last_loop_id={last_loop_id}",
            "none",
            "continue append-only; re-read cursor before edits",
        ),
        status_row(
            "Every active regime/root reaches 95 percent confidence",
            "blocked",
            f"board_state={board_state}; accepted_gate={accepted_gate}",
            "strict full objective remains blocked; full_objective_gate is none",
            "do not call update_goal; continue missing gates",
        ),
        status_row(
            "Validate across other markets and other periods",
            "blocked",
            "V65 preserves Oystacher R6 positives but rejects FLIP controls; R5 and R3 blockers remain in cursor text",
            "R6 lacks approved controls; R5 post-2026-01-30 rows absent; R3 native-subhour root absent",
            "supply source-owned normal controls or approval; separately populate R5/R3 roots",
        ),
        status_row(
            "Run real artifacts instead of inferring from prose",
            "partial",
            f"live_verifier_returncode={live_verifier['returncode']}; live_status={live_verifier['parsed'].get('status')}",
            "provider/Auto-Quant/BBN/CatBoost/execution-tree rerun is intentionally deferred until approval/canonical merge",
            "after approval/controls, rerun full downstream chain",
        ),
        status_row(
            "Use IBKR, TradingViewRemix/MCP, yfinance, Kraken provider context",
            "deferred",
            cursor.get("provider_status", ""),
            "no fresh provider rerun allowed by active next action before approval/canonical merge",
            "rerun provider-status/readbacks after accepted row or contract change",
        ),
        status_row(
            "Run Auto-Quant -> filter/pre-Bayes/BBN -> CatBoost/path-ranking -> execution tree",
            "deferred",
            "current cursor says downstream rerun false until approval or source-owned normal controls and canonical merge",
            "no canonical accepted intake to feed downstream chain",
            "run chain only after approval/controls and locked copy",
        ),
        status_row(
            "Preserve multi-agent board work",
            "pass",
            f"read board before audit; cursor remains {last_loop_id}",
            "none",
            "append supplemental audit without moving cursor",
        ),
        status_row(
            "R6 Oystacher public RECAP/PACER provenance approved",
            "blocked",
            f"source_policy_gate={source_policy_gate}",
            "explicit board/user approval file or statement not present",
            "get explicit approval or use owner export",
        ),
        status_row(
            "R6 same-exhibit FLIP rows accepted as normal controls",
            "blocked",
            f"policy_gate={policy_gate}",
            "V65 rejects FLIP rows as normal controls under current contract",
            "get explicit FLIP-as-control approval or source-owned normal controls",
        ),
        status_row(
            "Owner-export target ready for verifier",
            "blocked",
            f"owner_verifier_returncode={owner_verifier['returncode']}; owner_status={owner_verifier['parsed'].get('status')}",
            "target root is absent or missing required files",
            "place verifier-native files plus approval docs under owner-export target",
        ),
        status_row(
            "No runtime code pollution",
            "pass",
            "this audit writes docs/experiments artifacts only and runs read-only verifiers",
            "none",
            "keep runtime code unchanged until explicit implementation need",
        ),
    ]

    checklist_csv = OUT / "current_objective_prompt_to_artifact_checklist_v66.csv"
    write_csv(checklist_csv, checklist, ["requirement", "status", "evidence", "gap", "next_action"])

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_path": rel(BOARD),
        "board_sha256_at_start": board_hash,
        "current_cursor": cursor,
        "loaded_artifacts": {
            "policy_review": rel(policy_review_path),
            "source_policy_review": rel(SOURCE_POLICY_REVIEW),
            "row_materialization": rel(ROW_MATERIALIZATION),
            "approval_template": rel(APPROVAL_TEMPLATE),
            "approval_template_exists": approval_template_exists,
        },
        "artifact_gate_results": {
            "r6_oystacher_exhibit_a_policy_review_v1": policy_gate,
            "r6_oystacher_exhibit_a_source_policy_review_v1": source_policy_gate,
            "r6_oystacher_exhibit_a_row_materialization_v1": materialization_gate,
        },
        "fresh_readbacks": {
            "live_direct_intake_verifier": live_verifier,
            "owner_export_target_verifier": owner_verifier,
        },
        "prompt_to_artifact_checklist_csv": rel(checklist_csv),
        "completion_audit_decision": "not_achieved",
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "provider_downstream_rerun": False,
        "provider_downstream_rerun_reason": "deferred by active cursor until explicit source/control-policy approval or source-owned normal controls and canonical merge",
        "next_action": next_action,
    }

    json_path = OUT / "current_objective_completion_audit_v66.json"
    md_path = OUT / "current_objective_completion_audit_v66.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Current Objective Completion Audit v66",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Board hash at start: `{board_hash}`.",
        f"- Current cursor: `{last_loop_id}`.",
        f"- Board state: `{board_state}`.",
        f"- Live direct verifier: return code `{live_verifier['returncode']}`, status `{live_verifier['parsed'].get('status', 'unknown')}`, positives `{live_verifier['parsed'].get('positive_rows', 'unknown')}`, matched negatives `{live_verifier['parsed'].get('matched_negative_rows', 'unknown')}`.",
        f"- Owner-export target verifier: return code `{owner_verifier['returncode']}`, status `{owner_verifier['parsed'].get('status', 'unknown')}`.",
        f"- Active policy gate: `{policy_gate}`.",
        f"- Completion audit decision: `not_achieved`; `update_goal=false`.",
        "- Provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun: `false`, deferred until approval/controls and canonical merge.",
        "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`.",
        "",
        "## Checklist",
        "",
    ]
    for row in checklist:
        lines.append(f"- `{row['status']}` {row['requirement']}: {row['gap']}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(json_path)}`",
            f"- Checklist CSV: `{rel(checklist_csv)}`",
            f"- Live verifier stdout: `{live_verifier['stdout_path']}`",
            f"- Owner-export verifier stdout: `{owner_verifier['stdout_path']}`",
            "",
            "## Next",
            "",
            next_action,
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = {
        "board_cursor_read": bool(last_loop_id),
        "active_cursor_is_blocked": board_state == "blocked",
        "live_direct_verifier_ran": live_verifier["returncode"] == 0,
        "live_direct_schema_ready": live_verifier["parsed"].get("status") == "schema_ready_unscored",
        "owner_export_target_not_ready": owner_verifier["returncode"] != 0,
        "policy_review_loaded": bool(policy_gate),
        "flip_controls_not_accepted": "controls_rejected" in policy_gate,
        "completion_not_achieved": result["strict_full_objective_achieved"] is False,
        "update_goal_false": result["update_goal"] is False,
        "runtime_code_changed_false": result["runtime_code_changed"] is False,
    }
    assertions_path = CHECKS / "current_objective_completion_audit_v66_assertions.out"
    assertions_path.write_text(
        "\n".join(f"{key}={'PASS' if value else 'FAIL'}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )
    failures = [key for key, value in assertions.items() if not value]
    if failures:
        print(json.dumps({"run_id": RUN_ID, "failures": failures}, sort_keys=True))
        return 1
    print(json.dumps({"run_id": RUN_ID, "decision": "not_achieved", "next_action": next_action}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
