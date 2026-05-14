#!/usr/bin/env python3
"""Compare the V62 owner-export request schema with the unchanged direct verifier."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T002941-codex-r6-owner-export-schema-bridge-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-owner-export-schema-bridge"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
REQUEST_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T001636-codex-r6-owner-export-request-package-v1"
    / "r6-owner-export-request-package"
)
REQUEST_FIELDS = REQUEST_ROOT / "r6_owner_export_request_fields_v1.csv"
REQUEST_MATRIX = REQUEST_ROOT / "r6_owner_export_request_matrix_v1.csv"
TARGET_READBACK = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T002004-codex-r6-owner-export-target-readback-v1"
    / "r6-owner-export-target-readback/r6_owner_export_target_readback_v1.json"
)
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def verifier_constants(path: Path) -> tuple[list[str], dict[str, str]]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    required_fields: list[str] = []
    required_files: dict[str, str] = {}
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "REQUIRED_FIELDS":
                required_fields = ast.literal_eval(node.value)
            if isinstance(target, ast.Name) and target.id == "REQUIRED_FILES":
                required_files = ast.literal_eval(node.value)
    return required_fields, required_files


def request_field_set(rows: list[dict[str, str]], filename: str) -> set[str]:
    return {row["field"] for row in rows if row.get("file") == filename}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    request_rows = read_csv(REQUEST_FIELDS)
    request_matrix = read_csv(REQUEST_MATRIX)
    verifier_fields, verifier_files = verifier_constants(DIRECT_VERIFIER)
    target_readback = json.loads(TARGET_READBACK.read_text(encoding="utf-8")) if TARGET_READBACK.exists() else {}

    positive_fields = request_field_set(request_rows, "direct_manipulation_positive_rows.csv")
    control_fields = request_field_set(request_rows, "direct_manipulation_matched_controls.csv")
    provenance_fields = request_field_set(request_rows, "direct_manipulation_provenance.json")

    bridge_rows: list[dict[str, Any]] = [
        {
            "verifier_field": "label",
            "positive_request_mapping": "positive_label",
            "control_request_mapping": "normal_label",
            "bridge_status": "direct_positive_control_name_split",
            "notes": "Adapter must set verifier label from source-owned positive/normal labels without changing semantics.",
        },
        {
            "verifier_field": "source_report",
            "positive_request_mapping": "source_dataset",
            "control_request_mapping": "provenance_or_source_dataset_required",
            "bridge_status": "partial_mapping_controls_need_source_dataset",
            "notes": "Positive rows carry source_dataset; matched controls need equivalent owner/export identifier.",
        },
        {
            "verifier_field": "source_section",
            "positive_request_mapping": "",
            "control_request_mapping": "",
            "bridge_status": "missing_required_source_locator",
            "notes": "V62 request does not require report section, appendix id, or row block locator.",
        },
        {
            "verifier_field": "trade_date",
            "positive_request_mapping": "event_start",
            "control_request_mapping": "control_event_start_required",
            "bridge_status": "derivable_only_with_timestamp_policy",
            "notes": "Can derive date from event_start only if timezone and session policy are explicit.",
        },
        {
            "verifier_field": "symbol",
            "positive_request_mapping": "symbol",
            "control_request_mapping": "control_symbol_required",
            "bridge_status": "partial_mapping_controls_need_symbol",
            "notes": "V62 control file does not require symbol even though matching_dimensions may describe it.",
        },
        {
            "verifier_field": "venue_or_market_center",
            "positive_request_mapping": "venue_or_market_center",
            "control_request_mapping": "control_venue_or_market_center_required",
            "bridge_status": "partial_mapping_controls_need_venue",
            "notes": "Controls need explicit venue/market center, not only narrative matching dimensions.",
        },
        {
            "verifier_field": "participant_type_code",
            "positive_request_mapping": "",
            "control_request_mapping": "",
            "bridge_status": "missing_required_participant_dimension",
            "notes": "Do not fabricate participant fields; owner export must provide them or verifier contract must be amended.",
        },
        {
            "verifier_field": "participant_identifier",
            "positive_request_mapping": "",
            "control_request_mapping": "",
            "bridge_status": "missing_required_participant_dimension",
            "notes": "Do not fabricate participant identifiers.",
        },
        {
            "verifier_field": "side",
            "positive_request_mapping": "",
            "control_request_mapping": "",
            "bridge_status": "missing_required_order_dimension",
            "notes": "Order side is required by the current verifier and absent from V62 required fields.",
        },
        {
            "verifier_field": "earliest_order_received_time",
            "positive_request_mapping": "event_start",
            "control_request_mapping": "control_event_start_required",
            "bridge_status": "partial_mapping_controls_need_event_start",
            "notes": "Positive event_start can map only if it is the earliest order timestamp.",
        },
        {
            "verifier_field": "latest_order_received_time",
            "positive_request_mapping": "event_end",
            "control_request_mapping": "control_event_end_required",
            "bridge_status": "partial_mapping_controls_need_event_end",
            "notes": "Positive event_end can map only if it is the latest order timestamp.",
        },
        {
            "verifier_field": "order_count",
            "positive_request_mapping": "",
            "control_request_mapping": "",
            "bridge_status": "missing_required_order_dimension",
            "notes": "The current verifier requires order_count; V62 does not.",
        },
        {
            "verifier_field": "total_order_quantity",
            "positive_request_mapping": "",
            "control_request_mapping": "",
            "bridge_status": "missing_required_order_dimension",
            "notes": "The current verifier requires total_order_quantity; V62 does not.",
        },
        {
            "verifier_field": "activity_description",
            "positive_request_mapping": "species + positive_label + event_id",
            "control_request_mapping": "matching_dimensions + normal_label",
            "bridge_status": "derivable_only_with_explicit_policy",
            "notes": "Derived descriptions are acceptable only as adapter metadata, not as source-owned proof.",
        },
        {
            "verifier_field": "matched_negative_group_id",
            "positive_request_mapping": "matched_control_group_id",
            "control_request_mapping": "matched_control_group_id",
            "bridge_status": "direct_group_mapping",
            "notes": "Name differs but semantics match if positive/control groups are owner-approved.",
        },
        {
            "verifier_field": "session_bucket",
            "positive_request_mapping": "",
            "control_request_mapping": "",
            "bridge_status": "missing_or_derivable_only_with_session_policy",
            "notes": "Do not derive without explicit timezone/session policy in provenance.",
        },
        {
            "verifier_field": "source_row_id",
            "positive_request_mapping": "source_row_id",
            "control_request_mapping": "control_row_id",
            "bridge_status": "direct_positive_control_name_split",
            "notes": "Control row id can map to source_row_id only for verifier-native staged controls.",
        },
    ]

    missing_rows = [row for row in bridge_rows if row["bridge_status"].startswith("missing") or "need_" in row["bridge_status"]]
    hard_missing = [row for row in bridge_rows if row["bridge_status"].startswith("missing_required")]
    positive_file_name_ready = verifier_files.get("positive_rows") == "direct_manipulation_positive_rows.csv"
    control_file_name_ready = verifier_files.get("matched_negative_rows") == "direct_manipulation_matched_controls.csv"
    provenance_file_name_ready = verifier_files.get("provenance_manifest") == "direct_manipulation_provenance.json"
    filenames_ready = positive_file_name_ready and control_file_name_ready and provenance_file_name_ready
    unchanged_verifier_adapter_ready = not hard_missing and filenames_ready

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "request_fields_path": rel(REQUEST_FIELDS),
        "request_matrix_path": rel(REQUEST_MATRIX),
        "target_readback_path": rel(TARGET_READBACK),
        "direct_verifier_path": rel(DIRECT_VERIFIER),
        "request_positive_fields": sorted(positive_fields),
        "request_control_fields": sorted(control_fields),
        "request_provenance_fields": sorted(provenance_fields),
        "verifier_required_fields": verifier_fields,
        "request_required_files": sorted({row["file"] for row in request_rows}),
        "verifier_required_files": verifier_files,
        "target_readback_gate_result": target_readback.get("gate_result"),
        "request_vs_verifier_filename_mismatch": not filenames_ready,
        "schema_bridge_rows": len(bridge_rows),
        "schema_gap_rows": len(missing_rows),
        "hard_missing_rows": len(hard_missing),
        "unchanged_verifier_adapter_ready": unchanged_verifier_adapter_ready,
        "gate_result": "r6_owner_export_schema_bridge_v1=adapter_not_ready_request_underspecified_for_unchanged_verifier",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": "Require owner export to provide verifier-native files/fields or amend the V62 request with explicit adapter fields before copying any owner-export CSV into the unchanged direct verifier path.",
    }

    bridge_csv = OUT / "r6_owner_export_schema_bridge_mapping_v1.csv"
    gaps_csv = OUT / "r6_owner_export_schema_bridge_gaps_v1.csv"
    json_path = OUT / "r6_owner_export_schema_bridge_v1.json"
    md_path = OUT / "r6_owner_export_schema_bridge_v1.md"
    checks_path = CHECKS / "r6_owner_export_schema_bridge_v1_assertions.out"
    write_csv(
        bridge_csv,
        bridge_rows,
        ["verifier_field", "positive_request_mapping", "control_request_mapping", "bridge_status", "notes"],
    )
    write_csv(
        gaps_csv,
        missing_rows,
        ["verifier_field", "positive_request_mapping", "control_request_mapping", "bridge_status", "notes"],
    )
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = f"""# R6 Owner Export Schema Bridge v1

- Run id: `{RUN_ID}`.
- V62 request fields: positive `{len(positive_fields)}`, controls `{len(control_fields)}`, provenance `{len(provenance_fields)}`.
- Unchanged direct verifier required fields: `{len(verifier_fields)}`.
- Request/verifier filename mismatch: `{str(payload["request_vs_verifier_filename_mismatch"]).lower()}`.
- Schema bridge rows: `{len(bridge_rows)}`; gap rows: `{len(missing_rows)}`; hard missing rows: `{len(hard_missing)}`.
- Unchanged verifier adapter ready: `{str(unchanged_verifier_adapter_ready).lower()}`.
- Gate result: `{payload["gate_result"]}`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Interpretation

The V62 request package is not yet sufficient for a safe copy/rename into the unchanged direct verifier. The filename mismatch is real, and the schema mismatch is also real: the unchanged verifier requires participant, side, order-count, quantity, source-section, and session-bucket fields that the V62 required export schema does not currently require.

No adapter should fabricate these fields. A future owner export must either provide verifier-native files and all verifier-native columns, or the V62 request package must be amended with explicit source-owned fields and an adapter policy before any verifier/calibration/downstream rerun.

## Artifacts

- JSON: `{rel(json_path)}`
- Mapping CSV: `{rel(bridge_csv)}`
- Gap CSV: `{rel(gaps_csv)}`
- Assertions: `{rel(checks_path)}`
"""
    md_path.write_text(report, encoding="utf-8")

    assertions = [
        ("request_fields_loaded", bool(request_rows)),
        ("verifier_required_fields_loaded", len(verifier_fields) == 17),
        ("filename_mismatch_recorded", payload["request_vs_verifier_filename_mismatch"] is True),
        ("schema_gaps_recorded", len(missing_rows) > 0),
        ("hard_missing_rows_recorded", len(hard_missing) > 0),
        ("adapter_not_ready", unchanged_verifier_adapter_ready is False),
        ("accepted_rows_zero", payload["accepted_rows_added"] == 0),
        ("strict_full_objective_false", payload["strict_full_objective_achieved"] is False),
        ("update_goal_false", payload["update_goal"] is False),
    ]
    checks_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in assertions) + "\n",
        encoding="utf-8",
    )
    return 0 if all(passed for _, passed in assertions) else 2


if __name__ == "__main__":
    raise SystemExit(main())
