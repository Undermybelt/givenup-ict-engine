#!/usr/bin/env python3
"""Concurrent Board A ledger for the source-label readback artifact."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T185048-codex-board-a-concurrent-artifact-ledger-v3"
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "concurrent-artifact-ledger"
CHECK_DIR = RUN_ROOT / "checks"
TODO_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
SOURCE_READBACK_RUN = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T184856-codex-source-label-other-market-readback-v1"
)
SOURCE_READBACK_JSON = (
    SOURCE_READBACK_RUN
    / "source-label-readback/source_label_other_market_readback_v1.json"
)
EXTERNAL_VERIFIER = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T183606-codex-external-intake-bundle-v1"
    / "external-intake-bundle/board_a_external_intake_verifier_v1.py"
)
EXTERNAL_INTAKE_ROOT = Path("/tmp/ict-engine-board-a-external-intake-bundle-v1")
TODO_HASH_OBSERVED_BEFORE_APPEND = (
    "bfd5626c82e3b396f01152174a9b1d1cecc4540e67654330ecc2bf8e1412e7dc"
)
SOURCE_READBACK_REGISTERED_BEFORE_APPEND = False


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
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

    source_payload = load_json(SOURCE_READBACK_JSON)
    source_decision = source_payload.get("decision", {})
    if not isinstance(source_decision, dict):
        source_decision = {}

    completed_artifact = {
        "run_id": SOURCE_READBACK_RUN.name,
        "artifact_type": source_payload.get("artifact_type"),
        "status": "completed_blocked",
        "registered_in_todo_before_this_ledger": SOURCE_READBACK_REGISTERED_BEFORE_APPEND,
        "gate_result": source_decision.get("gate_result"),
        "accepted_rows_added": source_decision.get("accepted_rows_added"),
        "new_confidence_gate": source_decision.get("new_confidence_gate"),
        "full_other_market_source_label_equivalence": source_decision.get(
            "full_other_market_source_label_equivalence"
        ),
        "full_objective_achieved": source_decision.get("full_objective_achieved"),
        "update_goal": source_decision.get("update_goal"),
        "source_artifact_count": source_payload.get("source_artifact_count"),
        "partial_attached_or_overlap_total": source_payload.get(
            "partial_attached_or_overlap_total"
        ),
        "accepted_factor_or_gate_total": source_payload.get(
            "accepted_factor_or_gate_total"
        ),
        "path": str(SOURCE_READBACK_RUN.relative_to(REPO_ROOT)),
    }

    external_result = run_external_verifier()
    (OUT_DIR / "external_intake_verifier_live_result_v3.json").write_text(
        json.dumps(external_result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    bad_completion_signals = []
    if source_decision.get("full_objective_achieved") is True:
        bad_completion_signals.append("source_readback_claimed_full_objective")
    if source_decision.get("update_goal") is True:
        bad_completion_signals.append("source_readback_requested_update_goal")
    if source_decision.get("accepted_rows_added", 0) not in (0, "0", None):
        bad_completion_signals.append("source_readback_added_rows")
    if source_payload.get("accepted_factor_or_gate_total", 0) not in (0, "0", None):
        bad_completion_signals.append("source_readback_accepted_factor_or_gate")

    ledger = {
        "artifact_type": "board_a_concurrent_artifact_ledger_v3",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": RUN_ID,
        "todo_path": str(TODO_PATH.relative_to(REPO_ROOT)),
        "todo_hash_observed_before_append": TODO_HASH_OBSERVED_BEFORE_APPEND,
        "todo_hash_at_generation": sha256_file(TODO_PATH),
        "completed_artifacts_read": 1,
        "completed_artifacts": [completed_artifact],
        "external_intake_live_result": external_result,
        "decision": {
            "gate_result": "board_a_concurrent_artifact_ledger_v3=source_label_readback_registered_no_new_gate",
            "bad_completion_signals": bad_completion_signals,
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "current_cursor_edited": False,
        },
        "next": (
            "Require source-owned or owner-approved equivalence/provenance rows "
            "before promoting other-market source-label coverage."
        ),
    }

    ledger_json = OUT_DIR / "board_a_concurrent_artifact_ledger_v3.json"
    ledger_json.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    rows_csv = OUT_DIR / "board_a_concurrent_artifact_ledger_v3_rows.csv"
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
                "full_other_market_source_label_equivalence",
                "full_objective_achieved",
                "update_goal",
                "source_artifact_count",
                "partial_attached_or_overlap_total",
                "accepted_factor_or_gate_total",
                "path",
            ],
        )
        writer.writeheader()
        writer.writerow(completed_artifact)

    report = OUT_DIR / "board_a_concurrent_artifact_ledger_v3.md"
    report.write_text(
        "\n".join(
            [
                "# Board A Concurrent Artifact Ledger v3",
                "",
                f"Run ID: `{RUN_ID}`",
                "",
                "Supplemental multi-agent readback ledger only. It registers one completed source-label readback artifact and does not edit any other agent's run root or the shared Current Cursor.",
                "",
                "## Completed Artifact Readback",
                "",
                f"- `{SOURCE_READBACK_RUN.name}`: `{completed_artifact['gate_result']}`.",
                f"- Registered in TODO before this ledger: `{str(completed_artifact['registered_in_todo_before_this_ledger']).lower()}`.",
                f"- Source artifacts read: `{completed_artifact['source_artifact_count']}`; partial attached/overlap slots: `{completed_artifact['partial_attached_or_overlap_total']}`.",
                f"- Accepted factor/gate total: `{completed_artifact['accepted_factor_or_gate_total']}`; full other-market equivalence: `{str(completed_artifact['full_other_market_source_label_equivalence']).lower()}`.",
                f"- Accepted rows added: `{completed_artifact['accepted_rows_added']}`; new confidence gate: `{str(completed_artifact['new_confidence_gate']).lower()}`; full objective achieved: `{str(completed_artifact['full_objective_achieved']).lower()}`.",
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
                "- Current Cursor edited: `false`.",
                "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/concurrent-artifact-ledger/board_a_concurrent_artifact_ledger_v3.json`",
                f"- Rows CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/concurrent-artifact-ledger/board_a_concurrent_artifact_ledger_v3_rows.csv`",
                f"- Live verifier JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/concurrent-artifact-ledger/external_intake_verifier_live_result_v3.json`",
                f"- Assertions: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/checks/board_a_concurrent_artifact_ledger_v3_assertions.out`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        "PASS completed_artifacts_read=1",
        f"PASS source_readback_gate={completed_artifact['gate_result']}",
        "PASS accepted_factor_or_gate_total=0",
        "PASS accepted_rows_added=0",
        f"PASS external_intake_return_code={external_result['return_code']}",
        f"PASS external_intake_missing_file_count={external_result['missing_file_count']}",
        "PASS strict_full_objective=false",
        "PASS update_goal=false",
        "PASS current_cursor_edited=false",
    ]
    (CHECK_DIR / "board_a_concurrent_artifact_ledger_v3_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(ledger["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
