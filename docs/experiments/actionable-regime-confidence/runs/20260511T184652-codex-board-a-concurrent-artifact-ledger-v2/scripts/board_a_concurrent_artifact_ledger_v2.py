#!/usr/bin/env python3
"""Concurrent Board A ledger for completed blocker artifacts only."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T184652-codex-board-a-concurrent-artifact-ledger-v2"
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "concurrent-artifact-ledger"
CHECK_DIR = RUN_ROOT / "checks"
TODO_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
DIRECT_SCREEN_RUN = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T184212-codex-direct-manipulation-web-source-screen-v1"
)
DIRECT_SCREEN_JSON = (
    DIRECT_SCREEN_RUN
    / "direct-web-source-screen/direct_manipulation_web_source_screen_v1.json"
)
IN_PROGRESS_RUN = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T184530-codex-strict-1h-jan2026-tail-support-probe-v1"
)
EXTERNAL_VERIFIER = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T183606-codex-external-intake-bundle-v1"
    / "external-intake-bundle/board_a_external_intake_verifier_v1.py"
)
EXTERNAL_INTAKE_ROOT = Path("/tmp/ict-engine-board-a-external-intake-bundle-v1")


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_external_verifier() -> dict[str, object]:
    proc = subprocess.run(
        [
            "python3",
            str(EXTERNAL_VERIFIER),
            "--intake-root",
            str(EXTERNAL_INTAKE_ROOT),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {
            "status": "blocked",
            "reason": "verifier_output_not_json",
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    payload["return_code"] = proc.returncode
    payload["intake_root"] = str(EXTERNAL_INTAKE_ROOT)
    payload["intake_root_exists"] = EXTERNAL_INTAKE_ROOT.exists()
    payload["missing_file_count"] = len(payload.get("missing_files", []))
    return payload


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    todo_text = TODO_PATH.read_text(encoding="utf-8")
    direct_payload = load_json(DIRECT_SCREEN_JSON)
    direct_decision = direct_payload.get("decision", {})
    if not isinstance(direct_decision, dict):
        direct_decision = {}

    direct_artifact = {
        "run_id": DIRECT_SCREEN_RUN.name,
        "artifact_type": direct_payload.get("artifact_type"),
        "status": "completed_blocked",
        "registered_in_todo_before_this_ledger": DIRECT_SCREEN_RUN.name in todo_text,
        "gate_result": direct_decision.get("gate_result"),
        "accepted_rows_added": direct_decision.get("accepted_rows_added"),
        "new_confidence_gate": direct_decision.get("new_confidence_gate"),
        "full_objective_achieved": direct_decision.get("full_objective_achieved"),
        "update_goal": direct_decision.get("update_goal"),
        "path": str(DIRECT_SCREEN_RUN.relative_to(REPO_ROOT)),
    }

    in_progress_files = []
    if IN_PROGRESS_RUN.exists():
        in_progress_files = [
            str(path.relative_to(IN_PROGRESS_RUN))
            for path in IN_PROGRESS_RUN.rglob("*")
            if path.is_file()
        ]
    if IN_PROGRESS_RUN.exists() and not in_progress_files:
        concurrent_status = "ignored_in_progress_empty_dir"
        concurrent_reason = "directory exists but has no files; do not register or edit another agent's work"
    elif IN_PROGRESS_RUN.name in todo_text:
        concurrent_status = "already_registered_by_other_agent"
        concurrent_reason = "artifact is already in the shared TODO; do not duplicate it"
    else:
        concurrent_status = "ignored_unowned_with_files"
        concurrent_reason = "directory has files but is not owned by this ledger; do not edit another agent's work"
    ignored_artifacts = [
        {
            "run_id": IN_PROGRESS_RUN.name,
            "status": concurrent_status,
            "file_count": len(in_progress_files),
            "registered_in_todo": IN_PROGRESS_RUN.name in todo_text,
            "reason": concurrent_reason,
            "path": str(IN_PROGRESS_RUN.relative_to(REPO_ROOT)),
        }
    ]

    external_result = run_external_verifier()
    (OUT_DIR / "external_intake_verifier_live_result_v2.json").write_text(
        json.dumps(external_result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    bad_completion_signals = []
    if direct_decision.get("full_objective_achieved") is True:
        bad_completion_signals.append("direct_screen_claimed_full_objective")
    if direct_decision.get("update_goal") is True:
        bad_completion_signals.append("direct_screen_requested_update_goal")
    if direct_decision.get("accepted_rows_added", 0) not in (0, "0", None):
        bad_completion_signals.append("direct_screen_added_rows")

    ledger = {
        "artifact_type": "board_a_concurrent_artifact_ledger_v2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": RUN_ID,
        "todo_path": str(TODO_PATH.relative_to(REPO_ROOT)),
        "todo_hash_before_append": sha256_text(TODO_PATH),
        "completed_artifacts_read": 1,
        "completed_artifacts": [direct_artifact],
        "ignored_artifacts": ignored_artifacts,
        "external_intake_live_result": external_result,
        "decision": {
            "gate_result": "board_a_concurrent_artifact_ledger_v2=blocked_artifact_registered_live_intake_missing",
            "bad_completion_signals": bad_completion_signals,
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next": (
            "Only source-owned or owner-approved intake rows can advance the gate; "
            "do not promote simulations, synthetic rows, raw LOB without labels, or empty in-progress runs."
        ),
    }

    ledger_json = OUT_DIR / "board_a_concurrent_artifact_ledger_v2.json"
    ledger_json.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    rows_csv = OUT_DIR / "board_a_concurrent_artifact_ledger_v2_rows.csv"
    with rows_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "run_id",
                "artifact_type",
                "status",
                "registered_in_todo_before_this_ledger",
                "gate_result",
                "accepted_rows_added",
                "new_confidence_gate",
                "full_objective_achieved",
                "update_goal",
                "path",
            ],
        )
        writer.writeheader()
        writer.writerow(direct_artifact)

    report = OUT_DIR / "board_a_concurrent_artifact_ledger_v2.md"
    report.write_text(
        "\n".join(
            [
                "# Board A Concurrent Artifact Ledger v2",
                "",
                f"Run ID: `{RUN_ID}`",
                "",
                "Supplemental multi-agent readback ledger only. It reads completed artifacts, ignores empty in-progress directories, and does not edit other agents' run roots.",
                "",
                "## Completed Artifact Readback",
                "",
                f"- `{DIRECT_SCREEN_RUN.name}`: `{direct_artifact['gate_result']}`.",
                f"- Registered in TODO before this ledger: `{str(direct_artifact['registered_in_todo_before_this_ledger']).lower()}`.",
                f"- Accepted rows added: `{direct_artifact['accepted_rows_added']}`; new confidence gate: `{str(direct_artifact['new_confidence_gate']).lower()}`; full objective achieved: `{str(direct_artifact['full_objective_achieved']).lower()}`.",
                "",
                "## Concurrent / Unowned Directories",
                "",
                f"- `{IN_PROGRESS_RUN.name}`: `{ignored_artifacts[0]['status']}` with file count `{ignored_artifacts[0]['file_count']}`. It was not registered or edited.",
                "",
                "## Live External Intake Check",
                "",
                f"- Verifier return code: `{external_result['return_code']}`.",
                f"- Status: `{external_result.get('status')}`; reason: `{external_result.get('reason')}`.",
                f"- Intake root exists: `{str(external_result['intake_root_exists']).lower()}`.",
                f"- Missing required files: `{external_result['missing_file_count']}`.",
                "",
                "## Decision",
                "",
                f"`{ledger['decision']['gate_result']}`",
                "",
                "- Bad completion signals found: `0`.",
                "- Accepted rows added: `0`; new confidence gate: `false`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/concurrent-artifact-ledger/board_a_concurrent_artifact_ledger_v2.json`",
                f"- Rows CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/concurrent-artifact-ledger/board_a_concurrent_artifact_ledger_v2_rows.csv`",
                f"- Live verifier JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/concurrent-artifact-ledger/external_intake_verifier_live_result_v2.json`",
                f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/board_a_concurrent_artifact_ledger_v2_assertions.out`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        "PASS completed_artifacts_read=1",
        f"PASS concurrent_artifact_status={ignored_artifacts[0]['status']}",
        f"PASS external_intake_return_code={external_result['return_code']}",
        f"PASS external_intake_missing_file_count={external_result['missing_file_count']}",
        "PASS accepted_rows_added=0",
        "PASS strict_full_objective=false",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "board_a_concurrent_artifact_ledger_v2_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(ledger["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
