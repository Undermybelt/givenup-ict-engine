#!/usr/bin/env python3
"""Verify that the 012425 fail-closed condition artifact root is restored."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T013106-codex-012425-artifact-restoration-readback-v1"
TARGET_RUN_ID = "20260512T012425-codex-source-label-qualifying-condition-failclosed-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "qualifying-condition-012425-artifact-restoration-readback-v1"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"

TARGET_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / TARGET_RUN_ID
TARGET_SCRIPT = TARGET_ROOT / "scripts/source_label_qualifying_condition_failclosed_v1.py"
TARGET_OUT = TARGET_ROOT / "source-label-qualifying-condition-failclosed-v1"
TARGET_CHECKS = TARGET_ROOT / "checks"

EXPECTED_FILES = {
    "target_script": TARGET_SCRIPT,
    "report": TARGET_OUT / "source_label_qualifying_condition_failclosed_v1.md",
    "json": TARGET_OUT / "source_label_qualifying_condition_failclosed_v1.json",
    "conditions_csv": TARGET_OUT / "source_label_qualifying_condition_failclosed_conditions_v1.csv",
    "split_validation_csv": TARGET_OUT / "source_label_qualifying_condition_failclosed_split_validation_v1.csv",
    "market_contexts_csv": TARGET_OUT / "source_label_qualifying_condition_failclosed_market_contexts_v1.csv",
    "sample_rows_csv": TARGET_OUT / "source_label_qualifying_condition_failclosed_sample_rows_v1.csv",
    "assertions": TARGET_CHECKS / "source_label_qualifying_condition_failclosed_v1_assertions.out",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_target_script() -> dict:
    CMD.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(TARGET_SCRIPT)],
        cwd=str(REPO),
        text=True,
        capture_output=True,
        check=False,
    )
    (CMD / "source_label_qualifying_condition_failclosed_stdout.txt").write_text(
        proc.stdout, encoding="utf-8"
    )
    (CMD / "source_label_qualifying_condition_failclosed_stderr.txt").write_text(
        proc.stderr, encoding="utf-8"
    )
    (CMD / "source_label_qualifying_condition_failclosed_exit_code.txt").write_text(
        f"{proc.returncode}\n", encoding="utf-8"
    )
    return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def file_status_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for artifact_id, path in EXPECTED_FILES.items():
        rows.append(
            {
                "artifact_id": artifact_id,
                "path": str(path.relative_to(REPO)),
                "present": str(path.exists()).lower(),
                "sha256": sha256_file(path) if path.exists() and path.is_file() else "",
            }
        )
    return rows


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    command = run_target_script()
    rows = file_status_rows()
    all_files_present = all(row["present"] == "true" for row in rows)
    target_json = read_json(EXPECTED_FILES["json"]) if EXPECTED_FILES["json"].exists() else {}
    assertions_text = (
        EXPECTED_FILES["assertions"].read_text(encoding="utf-8")
        if EXPECTED_FILES["assertions"].exists()
        else ""
    )
    assertion_failures = [
        line for line in assertions_text.splitlines() if line and not line.endswith("=PASS")
    ]

    decision = (
        "qualifying_condition_012425_artifact_restoration_readback_v1="
        "restored_failclosed_artifact_present_no_acceptance"
        if command["returncode"] == 0 and all_files_present and not assertion_failures
        else "qualifying_condition_012425_artifact_restoration_readback_v1=still_incomplete"
    )
    summary = {
        "run_id": RUN_ID,
        "target_run_id": TARGET_RUN_ID,
        "decision": decision,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_script_exit_code": command["returncode"],
        "all_expected_files_present": all_files_present,
        "file_status": rows,
        "assertion_failures": assertion_failures,
        "target_decision": target_json.get("decision", ""),
        "target_current_cursor_observed": target_json.get("current_cursor_observed", ""),
        "target_accepted_labels": target_json.get("accepted_labels", []),
        "target_field_complete_labels": target_json.get("field_complete_labels", []),
        "target_strict_full_objective_achieved": target_json.get("strict_full_objective_achieved"),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_root_mutated": False,
        "r5_root_mutated": False,
        "r6_owner_export_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    with (OUT / "qualifying_condition_012425_artifact_restoration_file_status_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=["artifact_id", "path", "present", "sha256"])
        writer.writeheader()
        writer.writerows(rows)

    (OUT / "qualifying_condition_012425_artifact_restoration_readback_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    report_lines = [
        "# 012425 Artifact Restoration Readback v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Target run id: `{TARGET_RUN_ID}`.",
        f"- Decision: `{decision}`.",
        f"- Target reproduction script exit code: `{command['returncode']}`.",
        f"- Expected files present: `{str(all_files_present).lower()}`.",
        f"- Assertion failures: `{len(assertion_failures)}`.",
        f"- Target decision: `{summary['target_decision']}`.",
        f"- Target accepted labels: `{summary['target_accepted_labels']}`.",
        f"- Target strict full objective achieved: `{str(summary['target_strict_full_objective_achieved']).lower()}`.",
        "- Accepted rows added: `0`; new confidence gate: false; downstream chain rerun allowed: false.",
        "- Strict full objective achieved: false. `update_goal=false`.",
        "",
        "## Boundary",
        "",
        "This readback only repairs the board-reference integrity gap for the 012425 fail-closed condition artifact. It does not accept Bull/Sideways, does not resolve Bear/Crisis/R3/R5/R6 blockers, and does not authorize downstream promotion.",
    ]
    (OUT / "qualifying_condition_012425_artifact_restoration_readback_v1.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )

    assertions = [
        f"run_id={RUN_ID}",
        f"target_run_id={TARGET_RUN_ID}",
        f"decision={decision}",
        f"target_script_exit_code={command['returncode']}",
        f"all_expected_files_present={str(all_files_present).lower()}",
        f"assertion_failure_count={len(assertion_failures)}",
        f"target_decision={summary['target_decision']}",
        f"target_accepted_labels={summary['target_accepted_labels']}",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "canonical_merge_allowed=false",
        "downstream_chain_rerun_allowed=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
    ]
    (CHECKS / "qualifying_condition_012425_artifact_restoration_readback_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    return 0 if decision.endswith("restored_failclosed_artifact_present_no_acceptance") else 2


if __name__ == "__main__":
    raise SystemExit(main())
