#!/usr/bin/env python3
"""Emit a verifier-native owner-export contract for Board A R6.

This is documentation/evidence only. It does not create adapters, mutate intake
roots, or modify runtime verifier behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T003003-codex-r6-owner-export-verifier-native-contract-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
ARTIFACT_DIR = RUN_ROOT / "r6-owner-export-verifier-native-contract"
CHECKS_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
TARGET_ROOT = "/tmp/ict-engine-board-a-r6-owner-export-v1"


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

VERIFIER_FILES = {
    "positive_rows": "positive_spoofing_layering_rows.csv",
    "matched_negative_rows": "matched_negative_normal_activity_rows.csv",
    "provenance_manifest": "provenance_manifest.json",
}

OWNER_REQUEST_FILES = {
    "positive_rows": "direct_manipulation_positive_rows.csv",
    "matched_negative_rows": "direct_manipulation_matched_controls.csv",
    "provenance_manifest": "direct_manipulation_provenance.json",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    board_hash = sha256(BOARD)

    file_rows = [
        {
            "logical_role": role,
            "verifier_native_filename": verifier_name,
            "owner_request_filename": OWNER_REQUEST_FILES[role],
            "target_path": f"{TARGET_ROOT}/{verifier_name}",
            "owner_request_path": f"{TARGET_ROOT}/{OWNER_REQUEST_FILES[role]}",
            "accepted_without_adapter": str(verifier_name == OWNER_REQUEST_FILES[role]).lower(),
            "required_before_chain_rerun": "true",
        }
        for role, verifier_name in VERIFIER_FILES.items()
    ]

    mapping_rows = [
        {
            "owner_file": "direct_manipulation_positive_rows.csv",
            "owner_field": "positive_label",
            "verifier_file": "positive_spoofing_layering_rows.csv",
            "verifier_field": "label",
            "mapping_rule": "must equal or map to positive_spoofing_layering under current verifier; other species need explicit contract/adaptor approval",
        },
        {
            "owner_file": "direct_manipulation_positive_rows.csv",
            "owner_field": "event_start",
            "verifier_file": "positive_spoofing_layering_rows.csv",
            "verifier_field": "earliest_order_received_time",
            "mapping_rule": "timestamp with timezone",
        },
        {
            "owner_file": "direct_manipulation_positive_rows.csv",
            "owner_field": "event_end",
            "verifier_file": "positive_spoofing_layering_rows.csv",
            "verifier_field": "latest_order_received_time",
            "mapping_rule": "timestamp with timezone",
        },
        {
            "owner_file": "direct_manipulation_positive_rows.csv",
            "owner_field": "matched_control_group_id",
            "verifier_file": "positive_spoofing_layering_rows.csv",
            "verifier_field": "matched_negative_group_id",
            "mapping_rule": "join key must also exist in matched_negative_normal_activity_rows.csv",
        },
        {
            "owner_file": "direct_manipulation_matched_controls.csv",
            "owner_field": "matched_control_group_id",
            "verifier_file": "matched_negative_normal_activity_rows.csv",
            "verifier_field": "matched_negative_group_id",
            "mapping_rule": "same join key as positives",
        },
        {
            "owner_file": "direct_manipulation_provenance.json",
            "owner_field": "owner_approval_reference",
            "verifier_file": "provenance_manifest.json",
            "verifier_field": "owner_approval_reference",
            "mapping_rule": "must cite source owner/export approval or source-owned report basis",
        },
        {
            "owner_file": "direct_manipulation_provenance.json",
            "owner_field": "split_contract",
            "verifier_file": "provenance_manifest.json",
            "verifier_field": "split_contract",
            "mapping_rule": "exact split by default; market-family/venue-family only with explicit owner approval",
        },
    ]

    positive_template = ARTIFACT_DIR / "positive_spoofing_layering_rows.header.csv"
    negative_template = ARTIFACT_DIR / "matched_negative_normal_activity_rows.header.csv"
    write_csv(positive_template, VERIFIER_FIELDS, [])
    write_csv(negative_template, VERIFIER_FIELDS, [])

    file_matrix = ARTIFACT_DIR / "r6_owner_export_verifier_native_files_v1.csv"
    mapping_csv = ARTIFACT_DIR / "r6_owner_export_to_verifier_mapping_v1.csv"
    write_csv(
        file_matrix,
        [
            "logical_role",
            "verifier_native_filename",
            "owner_request_filename",
            "target_path",
            "owner_request_path",
            "accepted_without_adapter",
            "required_before_chain_rerun",
        ],
        file_rows,
    )
    write_csv(
        mapping_csv,
        ["owner_file", "owner_field", "verifier_file", "verifier_field", "mapping_rule"],
        mapping_rows,
    )

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": board_hash,
        "target_root": TARGET_ROOT,
        "active_request_package": "docs/experiments/actionable-regime-confidence/runs/20260512T001636-codex-r6-owner-export-request-package-v1/r6-owner-export-request-package/r6_owner_export_request_package_v1.json",
        "readback_reference": "docs/experiments/actionable-regime-confidence/runs/20260512T002004-codex-r6-owner-export-target-readback-v1/r6-owner-export-target-readback/r6_owner_export_target_readback_v1.json",
        "verifier_script": "docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py",
        "verifier_native_files": VERIFIER_FILES,
        "owner_request_files": OWNER_REQUEST_FILES,
        "required_csv_fields": VERIFIER_FIELDS,
        "request_vs_verifier_filename_mismatch_resolved_by_contract": True,
        "adapter_created": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "raw_data_committed": False,
        "thresholds_relaxed": False,
        "external_requests_sent": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "trade_usable": False,
        "gate_result": "r6_owner_export_verifier_native_contract_v1=contract_ready_no_rows_or_adapter_created",
        "next_action": "Drop verifier-native positive_spoofing_layering_rows.csv, matched_negative_normal_activity_rows.csv, and provenance_manifest.json under /tmp/ict-engine-board-a-r6-owner-export-v1, or provide explicit approval for an adapter/contract change before rerunning direct verifier and downstream chain.",
    }

    json_path = ARTIFACT_DIR / "r6_owner_export_verifier_native_contract_v1.json"
    md_path = ARTIFACT_DIR / "r6_owner_export_verifier_native_contract_v1.md"
    checks_path = CHECKS_DIR / "r6_owner_export_verifier_native_contract_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# R6 Owner Export Verifier-Native Contract v1",
                "",
                f"- Run id: `{RUN_ID}`.",
                f"- Target root: `{TARGET_ROOT}`.",
                "- This is a contract/mapping artifact only: no adapter was created and runtime verifier behavior was not changed.",
                "- Verifier-native required files:",
                "  - `positive_spoofing_layering_rows.csv`",
                "  - `matched_negative_normal_activity_rows.csv`",
                "  - `provenance_manifest.json`",
                "- V62 owner-facing filenames are treated as aliases only; they are not accepted by the unchanged verifier unless copied/adapted under explicit approval.",
                "- Gate result: `r6_owner_export_verifier_native_contract_v1=contract_ready_no_rows_or_adapter_created`.",
                "- Accepted rows added: `0`; strict full objective achieved: `false`; `update_goal=false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- File matrix: `{file_matrix.relative_to(REPO)}`",
                f"- Field mapping: `{mapping_csv.relative_to(REPO)}`",
                f"- Positive header template: `{positive_template.relative_to(REPO)}`",
                f"- Matched-control header template: `{negative_template.relative_to(REPO)}`",
                f"- Assertions: `{checks_path.relative_to(REPO)}`",
                "",
                "## Next",
                "",
                "Drop verifier-native files under the target root, or provide explicit approval for an adapter/contract change, then rerun direct verifier and the provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree chain.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    checks = [
        ("verifier_native_positive_filename", VERIFIER_FILES["positive_rows"] == "positive_spoofing_layering_rows.csv"),
        ("verifier_native_negative_filename", VERIFIER_FILES["matched_negative_rows"] == "matched_negative_normal_activity_rows.csv"),
        ("verifier_native_provenance_filename", VERIFIER_FILES["provenance_manifest"] == "provenance_manifest.json"),
        ("required_fields_count_17", len(VERIFIER_FIELDS) == 17),
        ("adapter_created_false", not result["adapter_created"]),
        ("runtime_code_changed_false", not result["runtime_code_changed"]),
        ("shared_intake_mutated_false", not result["shared_intake_mutated"]),
        ("strict_full_objective_false", not result["strict_full_objective_achieved"]),
        ("update_goal_false", not result["update_goal"]),
    ]
    checks_path.write_text("\n".join(f"{name}={'PASS' if ok else 'FAIL'}" for name, ok in checks) + "\n", encoding="utf-8")
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
