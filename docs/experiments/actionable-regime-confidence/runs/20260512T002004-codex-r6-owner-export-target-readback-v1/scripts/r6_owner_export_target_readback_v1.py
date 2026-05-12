#!/usr/bin/env python3
"""Read back the requested R6 owner-export target root without accepting rows."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T002004-codex-r6-owner-export-target-readback-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-owner-export-target-readback"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
TARGET_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
REQUEST_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T001636-codex-r6-owner-export-request-package-v1"
    / "r6-owner-export-request-package"
)
REQUEST_JSON = REQUEST_ROOT / "r6_owner_export_request_package_v1.json"
REQUEST_FIELDS = REQUEST_ROOT / "r6_owner_export_request_fields_v1.csv"
REQUEST_MATRIX = REQUEST_ROOT / "r6_owner_export_request_matrix_v1.csv"
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

REQUIRED_FILES = [
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
]
VERIFIER_EXPECTED_FILES = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]
APPROVAL_FILES = [
    "validation_contract_approval.json",
    "owner_approval_reference.txt",
    "owner_approval_reference.md",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(name: str, args: list[str], timeout_seconds: int = 45) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        returncode = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout_seconds}s\n"
        returncode = 124
        timed_out = True
    out_path = CMD / f"{name}.stdout.txt"
    err_path = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{returncode}\n", encoding="utf-8")
    try:
        parsed: Any = json.loads(stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout_path": str(out_path.relative_to(REPO)),
        "stderr_path": str(err_path.relative_to(REPO)),
        "exit_path": str(exit_path.relative_to(REPO)),
        "parsed": parsed,
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    for path in [OUT, CHECKS, CMD]:
        path.mkdir(parents=True, exist_ok=True)

    request_json = json.loads(REQUEST_JSON.read_text(encoding="utf-8")) if REQUEST_JSON.exists() else {}
    request_fields = read_csv(REQUEST_FIELDS)
    request_matrix = read_csv(REQUEST_MATRIX)
    root_exists = TARGET_ROOT.exists()
    required_status = {
        name: {
            "path": str(TARGET_ROOT / name),
            "exists": (TARGET_ROOT / name).exists(),
            "size_bytes": (TARGET_ROOT / name).stat().st_size if (TARGET_ROOT / name).exists() else 0,
        }
        for name in REQUIRED_FILES
    }
    verifier_expected_status = {
        name: {
            "path": str(TARGET_ROOT / name),
            "exists": (TARGET_ROOT / name).exists(),
            "size_bytes": (TARGET_ROOT / name).stat().st_size if (TARGET_ROOT / name).exists() else 0,
        }
        for name in VERIFIER_EXPECTED_FILES
    }
    approval_status = {
        name: {
            "path": str(TARGET_ROOT / name),
            "exists": (TARGET_ROOT / name).exists(),
            "size_bytes": (TARGET_ROOT / name).stat().st_size if (TARGET_ROOT / name).exists() else 0,
        }
        for name in APPROVAL_FILES
    }
    verifier = run_command(
        "direct_manipulation_row_intake_verifier_owner_export_target",
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(TARGET_ROOT)],
    )
    missing_required = [name for name, status in required_status.items() if not status["exists"]]
    missing_verifier_expected = [name for name, status in verifier_expected_status.items() if not status["exists"]]
    approval_present = any(status["exists"] for status in approval_status.values())
    files_ready = not missing_required
    verifier_files_ready = not missing_verifier_expected
    request_vs_verifier_filename_mismatch = set(REQUIRED_FILES) != set(VERIFIER_EXPECTED_FILES)
    should_rerun_chain = files_ready or approval_present
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "active_request_package": str(REQUEST_JSON.relative_to(REPO)),
        "target_root": str(TARGET_ROOT),
        "target_root_exists": root_exists,
        "required_files": required_status,
        "missing_required_files": missing_required,
        "verifier_expected_files": verifier_expected_status,
        "missing_verifier_expected_files": missing_verifier_expected,
        "request_vs_verifier_filename_mismatch": request_vs_verifier_filename_mismatch,
        "approval_files": approval_status,
        "approval_present": approval_present,
        "request_field_rows": len(request_fields),
        "request_matrix_rows": len(request_matrix),
        "request_gate_result": request_json.get("gate_result"),
        "direct_verifier": verifier,
        "files_ready_for_calibration": files_ready,
        "verifier_files_ready": verifier_files_ready,
        "should_rerun_provider_autoquant_bbn_catboost_execution_tree": should_rerun_chain,
        "gate_result": "r6_owner_export_target_readback_v1=target_root_missing_request_verifier_names_mismatch_no_chain_rerun",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "shared_intake_mutated": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": "Place owner/user-approved R6 export files under /tmp/ict-engine-board-a-r6-owner-export-v1 or record explicit split-contract approval, then rerun the direct verifier and downstream provider/Auto-Quant/BBN/CatBoost/execution-tree chain.",
    }
    json_path = OUT / "r6_owner_export_target_readback_v1.json"
    md_path = OUT / "r6_owner_export_target_readback_v1.md"
    assertions_path = CHECKS / "r6_owner_export_target_readback_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# R6 Owner Export Target Readback v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Target root: `{TARGET_ROOT}`.",
        f"- Target root exists: `{str(root_exists).lower()}`.",
        f"- Missing required files: `{', '.join(missing_required) if missing_required else 'none'}`.",
        f"- Missing unchanged-verifier files: `{', '.join(missing_verifier_expected) if missing_verifier_expected else 'none'}`.",
        f"- Request/verifier filename mismatch: `{str(request_vs_verifier_filename_mismatch).lower()}`.",
        f"- Explicit approval file present: `{str(approval_present).lower()}`.",
        f"- Direct verifier return code: `{verifier['returncode']}`.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Downstream chain rerun: `false`, because no owner export files or explicit split-contract approval are present.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Direct verifier stdout: `{verifier['stdout_path']}`",
        f"- Direct verifier stderr: `{verifier['stderr_path']}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        ("target_root_missing_or_incomplete", (not root_exists) or bool(missing_required)),
        ("direct_verifier_fail_closed", verifier["returncode"] != 0),
        ("request_verifier_filename_mismatch_recorded", request_vs_verifier_filename_mismatch is True),
        ("no_approval_present", approval_present is False),
        ("no_chain_rerun_without_rows_or_approval", should_rerun_chain is False),
        ("accepted_rows_zero", result["accepted_rows_added"] == 0),
        ("strict_full_objective_false", result["strict_full_objective_achieved"] is False),
        ("update_goal_false", result["update_goal"] is False),
    ]
    assertions_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in assertions) + "\n",
        encoding="utf-8",
    )
    if not all(passed for _, passed in assertions):
        raise SystemExit(2)
    print(json.dumps({"gate_result": result["gate_result"], "target_root_exists": root_exists, "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
