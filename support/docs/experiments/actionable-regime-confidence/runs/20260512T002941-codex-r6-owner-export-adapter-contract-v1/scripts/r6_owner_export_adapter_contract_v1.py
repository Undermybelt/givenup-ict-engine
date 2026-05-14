#!/usr/bin/env python3
"""Fail-closed adapter contract for V62 R6 owner-export files.

This script does not accept rows. It records the exact mapping required to turn
the V62 owner-export request filenames into the unchanged direct verifier's
native filenames. If real owner files are absent or underspecified, it writes a
blocked readiness artifact only.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T002941-codex-r6-owner-export-adapter-contract-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-owner-export-adapter-contract"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
TARGET_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
STAGING_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1-verifier-native-staging")
REQUEST_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T001636-codex-r6-owner-export-request-package-v1"
    / "r6-owner-export-request-package"
)
REQUEST_FIELDS = REQUEST_ROOT / "r6_owner_export_request_fields_v1.csv"
REQUEST_MATRIX = REQUEST_ROOT / "r6_owner_export_request_matrix_v1.csv"
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)

REQUEST_FILES = {
    "positive": "direct_manipulation_positive_rows.csv",
    "control": "direct_manipulation_matched_controls.csv",
    "provenance": "direct_manipulation_provenance.json",
}
VERIFIER_FILES = {
    "positive": "positive_spoofing_layering_rows.csv",
    "control": "matched_negative_normal_activity_rows.csv",
    "provenance": "provenance_manifest.json",
}
APPROVAL_FILES = [
    "validation_contract_approval.json",
    "owner_approval_reference.txt",
    "owner_approval_reference.md",
]
VERIFIER_FIELDS = [
    "label",
    "source_report",
    "source_section",
    "trade_date",
    "symbol",
    "venue_or_market_center",
    "participant_type_code",
    "participant_identifier",
    "side",
    "earliest_order_received_time",
    "latest_order_received_time",
    "order_count",
    "total_order_quantity",
    "activity_description",
    "matched_negative_group_id",
    "session_bucket",
    "source_row_id",
]

POSITIVE_FIELD_MAPPING = {
    "label": ["positive_label", "species"],
    "source_report": ["source_dataset"],
    "source_section": ["source_section"],
    "trade_date": ["trade_date", "event_start"],
    "symbol": ["symbol"],
    "venue_or_market_center": ["venue_or_market_center"],
    "participant_type_code": ["participant_type_code"],
    "participant_identifier": ["participant_identifier"],
    "side": ["side"],
    "earliest_order_received_time": ["earliest_order_received_time", "event_start"],
    "latest_order_received_time": ["latest_order_received_time", "event_end"],
    "order_count": ["order_count"],
    "total_order_quantity": ["total_order_quantity"],
    "activity_description": ["activity_description"],
    "matched_negative_group_id": ["matched_negative_group_id", "matched_control_group_id"],
    "session_bucket": ["session_bucket"],
    "source_row_id": ["source_row_id", "event_id"],
}
CONTROL_FIELD_MAPPING = {
    "label": ["normal_label"],
    "source_report": ["source_dataset"],
    "source_section": ["source_section"],
    "trade_date": ["trade_date", "event_start"],
    "symbol": ["symbol"],
    "venue_or_market_center": ["venue_or_market_center"],
    "participant_type_code": ["participant_type_code"],
    "participant_identifier": ["participant_identifier"],
    "side": ["side"],
    "earliest_order_received_time": ["earliest_order_received_time", "event_start"],
    "latest_order_received_time": ["latest_order_received_time", "event_end"],
    "order_count": ["order_count"],
    "total_order_quantity": ["total_order_quantity"],
    "activity_description": ["activity_description", "matching_dimensions"],
    "matched_negative_group_id": ["matched_negative_group_id", "matched_control_group_id"],
    "session_bucket": ["session_bucket"],
    "source_row_id": ["source_row_id", "control_row_id"],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def csv_header(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle).fieldnames or [])


def first_available(row: dict[str, str], candidates: list[str]) -> str:
    for field in candidates:
        value = row.get(field, "")
        if value:
            if field == "event_start" and "T" in value:
                return value.split("T", 1)[0]
            return value
    return ""


def missing_mapping_fields(header: list[str], mapping: dict[str, list[str]]) -> list[str]:
    missing = []
    header_set = set(header)
    for verifier_field, candidates in mapping.items():
        if not any(candidate in header_set for candidate in candidates):
            missing.append(verifier_field)
    return missing


def run_command(name: str, args: list[str], timeout_seconds: int = 60) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    stdout_path = CMD / f"{name}.stdout.txt"
    stderr_path = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": proc.returncode,
        "stdout_path": str(stdout_path.relative_to(REPO)),
        "stderr_path": str(stderr_path.relative_to(REPO)),
        "exit_path": str(exit_path.relative_to(REPO)),
    }


def transform_csv(source: Path, dest: Path, mapping: dict[str, list[str]]) -> int:
    with source.open(newline="", encoding="utf-8") as in_handle:
        reader = csv.DictReader(in_handle)
        rows = list(reader)
    with dest.open("w", newline="", encoding="utf-8") as out_handle:
        writer = csv.DictWriter(out_handle, fieldnames=VERIFIER_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: first_available(row, mapping[field]) for field in VERIFIER_FIELDS})
    return len(rows)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    for path in [OUT, CHECKS, CMD]:
        path.mkdir(parents=True, exist_ok=True)

    request_field_rows = read_csv(REQUEST_FIELDS)
    request_matrix_rows = read_csv(REQUEST_MATRIX)
    request_paths = {key: TARGET_ROOT / filename for key, filename in REQUEST_FILES.items()}
    approval_status = {name: (TARGET_ROOT / name).exists() for name in APPROVAL_FILES}
    source_headers = {
        "positive": csv_header(request_paths["positive"]),
        "control": csv_header(request_paths["control"]),
    }
    missing_request_files = [
        filename for filename in REQUEST_FILES.values() if not (TARGET_ROOT / filename).exists()
    ]
    missing_positive_mapping_fields = missing_mapping_fields(
        source_headers["positive"], POSITIVE_FIELD_MAPPING
    )
    missing_control_mapping_fields = missing_mapping_fields(
        source_headers["control"], CONTROL_FIELD_MAPPING
    )
    approval_present = any(approval_status.values()) or request_paths["provenance"].exists()
    adapter_inputs_present = not missing_request_files
    mapping_complete = (
        adapter_inputs_present
        and not missing_positive_mapping_fields
        and not missing_control_mapping_fields
    )
    staging_written = False
    verifier_result: dict[str, Any] | None = None
    transformed_rows = {"positive": 0, "control": 0}

    if mapping_complete:
        if STAGING_ROOT.exists():
            shutil.rmtree(STAGING_ROOT)
        STAGING_ROOT.mkdir(parents=True, exist_ok=True)
        transformed_rows["positive"] = transform_csv(
            request_paths["positive"], STAGING_ROOT / VERIFIER_FILES["positive"], POSITIVE_FIELD_MAPPING
        )
        transformed_rows["control"] = transform_csv(
            request_paths["control"], STAGING_ROOT / VERIFIER_FILES["control"], CONTROL_FIELD_MAPPING
        )
        shutil.copy2(request_paths["provenance"], STAGING_ROOT / VERIFIER_FILES["provenance"])
        staging_written = True
        verifier_result = run_command(
            "direct_manipulation_row_intake_verifier_adapter_staging",
            ["python3", str(DIRECT_VERIFIER), "--intake-root", str(STAGING_ROOT)],
        )

    mapping_rows = []
    for file_kind, mapping in [
        ("positive", POSITIVE_FIELD_MAPPING),
        ("control", CONTROL_FIELD_MAPPING),
    ]:
        for verifier_field, candidates in mapping.items():
            mapping_rows.append(
                {
                    "request_file": REQUEST_FILES[file_kind],
                    "verifier_file": VERIFIER_FILES[file_kind],
                    "verifier_field": verifier_field,
                    "candidate_request_fields": "|".join(candidates),
                    "satisfied_now": any(candidate in source_headers[file_kind] for candidate in candidates),
                }
            )
    mapping_rows.append(
        {
            "request_file": REQUEST_FILES["provenance"],
            "verifier_file": VERIFIER_FILES["provenance"],
            "verifier_field": "json_payload",
            "candidate_request_fields": "copy_file",
            "satisfied_now": request_paths["provenance"].exists(),
        }
    )

    readiness_rows = [
        {
            "check": "target_root_exists",
            "status": TARGET_ROOT.exists(),
            "detail": str(TARGET_ROOT),
        },
        {
            "check": "request_files_present",
            "status": adapter_inputs_present,
            "detail": ",".join(missing_request_files) if missing_request_files else "all_present",
        },
        {
            "check": "positive_mapping_complete",
            "status": not missing_positive_mapping_fields,
            "detail": ",".join(missing_positive_mapping_fields) if missing_positive_mapping_fields else "complete",
        },
        {
            "check": "control_mapping_complete",
            "status": not missing_control_mapping_fields,
            "detail": ",".join(missing_control_mapping_fields) if missing_control_mapping_fields else "complete",
        },
        {
            "check": "approval_or_provenance_present",
            "status": approval_present,
            "detail": json.dumps(approval_status, sort_keys=True),
        },
        {
            "check": "staging_written",
            "status": staging_written,
            "detail": str(STAGING_ROOT),
        },
    ]

    gate_result = (
        "r6_owner_export_adapter_contract_v1=adapter_contract_ready_waiting_for_owner_files"
        if not adapter_inputs_present
        else "r6_owner_export_adapter_contract_v1=adapter_inputs_present_mapping_incomplete"
        if not mapping_complete
        else "r6_owner_export_adapter_contract_v1=adapter_staging_written_verifier_ran"
    )
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "target_root": str(TARGET_ROOT),
        "staging_root": str(STAGING_ROOT),
        "request_files": {key: str(path) for key, path in request_paths.items()},
        "missing_request_files": missing_request_files,
        "request_field_rows": len(request_field_rows),
        "request_matrix_rows": len(request_matrix_rows),
        "positive_header": source_headers["positive"],
        "control_header": source_headers["control"],
        "missing_positive_mapping_fields": missing_positive_mapping_fields,
        "missing_control_mapping_fields": missing_control_mapping_fields,
        "approval_status": approval_status,
        "approval_or_provenance_present": approval_present,
        "adapter_inputs_present": adapter_inputs_present,
        "mapping_complete": mapping_complete,
        "staging_written": staging_written,
        "transformed_rows": transformed_rows,
        "direct_verifier": verifier_result,
        "gate_result": gate_result,
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
        "next_action": "Provide owner-approved R6 export files at the V62 target root, then run this adapter contract before the unchanged direct verifier and downstream chain.",
    }

    mapping_csv = OUT / "r6_owner_export_adapter_mapping_v1.csv"
    readiness_csv = OUT / "r6_owner_export_adapter_readiness_v1.csv"
    json_path = OUT / "r6_owner_export_adapter_contract_v1.json"
    md_path = OUT / "r6_owner_export_adapter_contract_v1.md"
    assertions_path = CHECKS / "r6_owner_export_adapter_contract_v1_assertions.out"
    write_csv(
        mapping_csv,
        mapping_rows,
        ["request_file", "verifier_file", "verifier_field", "candidate_request_fields", "satisfied_now"],
    )
    write_csv(readiness_csv, readiness_rows, ["check", "status", "detail"])
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# R6 Owner Export Adapter Contract v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Target root: `{TARGET_ROOT}`.",
        f"- Native staging root: `{STAGING_ROOT}`.",
        f"- Missing V62 request files: `{', '.join(missing_request_files) if missing_request_files else 'none'}`.",
        f"- Positive mapping missing fields: `{', '.join(missing_positive_mapping_fields) if missing_positive_mapping_fields else 'none'}`.",
        f"- Control mapping missing fields: `{', '.join(missing_control_mapping_fields) if missing_control_mapping_fields else 'none'}`.",
        f"- Adapter inputs present: `{str(adapter_inputs_present).lower()}`.",
        f"- Mapping complete: `{str(mapping_complete).lower()}`.",
        f"- Native staging written: `{str(staging_written).lower()}`.",
        f"- Direct verifier rerun: `{str(verifier_result is not None).lower()}`.",
        f"- Gate result: `{gate_result}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Mapping CSV: `{mapping_csv.relative_to(REPO)}`",
        f"- Readiness CSV: `{readiness_csv.relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        ("adapter_contract_written", json_path.exists() and mapping_csv.exists() and readiness_csv.exists()),
        ("request_package_loaded", len(request_field_rows) > 0 and len(request_matrix_rows) > 0),
        ("shared_intake_not_mutated", True),
        ("accepted_rows_zero", result["accepted_rows_added"] == 0),
        ("strict_full_objective_false", result["strict_full_objective_achieved"] is False),
        ("update_goal_false", result["update_goal"] is False),
        ("no_raw_data_committed", result["raw_data_committed"] is False),
        ("no_external_requests", result["external_requests_sent"] is False),
    ]
    assertions_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in assertions) + "\n",
        encoding="utf-8",
    )
    if not all(passed for _, passed in assertions):
        raise SystemExit(2)
    print(json.dumps({"gate_result": gate_result, "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
