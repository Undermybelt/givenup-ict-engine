#!/usr/bin/env python3
"""Build the R6 split-contract approval handoff template.

This script does not approve a contract, acquire rows, or mutate the live intake.
It only materializes the files needed for a user/owner to record an explicit
validation-contract approval in a form future verifier runs can inspect.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T003017-codex-r6-split-contract-approval-template-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-split-contract-approval-template"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
TARGET_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
REQUEST_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T001636-codex-r6-owner-export-request-package-v1"
    / "r6-owner-export-request-package"
)
REQUEST_MATRIX = REQUEST_ROOT / "r6_owner_export_request_matrix_v1.csv"
REQUEST_FIELDS = REQUEST_ROOT / "r6_owner_export_request_fields_v1.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    request_matrix = read_csv(REQUEST_MATRIX)
    request_fields = read_csv(REQUEST_FIELDS)
    generated_at = datetime.now(timezone.utc).isoformat()

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Board A R6 validation_contract_approval.json",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "approval_state",
            "approved_by",
            "approval_timestamp_utc",
            "owner_approval_reference",
            "approved_contract_id",
            "approved_split_contract",
            "filename_contract",
            "required_followup_chain",
            "no_proxy_acceptance",
        ],
        "properties": {
            "approval_state": {
                "const": "approved",
                "description": "Only an explicit approved value can unblock the split-contract branch.",
            },
            "approved_by": {"type": "string", "minLength": 1},
            "approval_timestamp_utc": {"type": "string", "format": "date-time"},
            "owner_approval_reference": {
                "type": "string",
                "minLength": 1,
                "description": "Ticket, signed note, source-owner export id, or user approval reference.",
            },
            "approved_contract_id": {
                "enum": [
                    "r6_exact_contract_bulk_export",
                    "r6_family_contract_export",
                    "r6_species_completion_export",
                    "r6_other_owner_approved_contract",
                ]
            },
            "approved_split_contract": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "split_unit",
                    "heldout_axes",
                    "minimum_positive_rows_per_accepted_cell",
                    "minimum_control_rows_per_accepted_cell",
                    "matched_control_policy",
                    "species_policy",
                ],
                "properties": {
                    "split_unit": {
                        "enum": [
                            "exact_symbol_exact_venue",
                            "market_family_venue_family",
                            "owner_defined_documented_split",
                        ]
                    },
                    "heldout_axes": {
                        "type": "array",
                        "minItems": 2,
                        "items": {
                            "enum": [
                                "chronological_period",
                                "symbol_or_instrument",
                                "venue_or_market_center",
                                "market_family",
                                "venue_family",
                                "direct_species",
                                "owner_native_split",
                            ]
                        },
                    },
                    "minimum_positive_rows_per_accepted_cell": {"type": "integer", "minimum": 73},
                    "minimum_control_rows_per_accepted_cell": {"type": "integer", "minimum": 73},
                    "matched_control_policy": {"type": "string", "minLength": 1},
                    "species_policy": {"type": "string", "minLength": 1},
                },
            },
            "filename_contract": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "request_positive_rows",
                    "request_matched_controls",
                    "request_provenance",
                    "verifier_positive_rows",
                    "verifier_matched_controls",
                    "verifier_provenance",
                    "adapter_required",
                    "adapter_approval_reference",
                ],
                "properties": {
                    "request_positive_rows": {"const": "direct_manipulation_positive_rows.csv"},
                    "request_matched_controls": {"const": "direct_manipulation_matched_controls.csv"},
                    "request_provenance": {"const": "direct_manipulation_provenance.json"},
                    "verifier_positive_rows": {"const": "positive_spoofing_layering_rows.csv"},
                    "verifier_matched_controls": {"const": "matched_negative_normal_activity_rows.csv"},
                    "verifier_provenance": {"const": "provenance_manifest.json"},
                    "adapter_required": {"type": "boolean"},
                    "adapter_approval_reference": {"type": "string"},
                },
            },
            "required_followup_chain": {
                "type": "array",
                "minItems": 7,
                "items": {"type": "string"},
            },
            "no_proxy_acceptance": {
                "const": True,
                "description": "OHLCV proxies and inferred labels cannot satisfy direct Manipulation.",
            },
        },
    }

    approval_template = {
        "approval_state": "approved",
        "approved_by": "<user-or-source-owner>",
        "approval_timestamp_utc": "<YYYY-MM-DDTHH:MM:SSZ>",
        "owner_approval_reference": "<ticket/signed-note/source-export-id>",
        "approved_contract_id": "r6_family_contract_export",
        "approved_split_contract": {
            "split_unit": "market_family_venue_family",
            "heldout_axes": [
                "chronological_period",
                "market_family",
                "venue_family",
                "direct_species",
            ],
            "minimum_positive_rows_per_accepted_cell": 73,
            "minimum_control_rows_per_accepted_cell": 73,
            "matched_control_policy": "Controls must be owner-approved normal/non-manipulation rows matched by symbol or market family, venue or venue family, session, and time window.",
            "species_policy": "Direct species labels must remain source-owned or explicitly owner-approved; no labels inferred from OHLCV or raw order-book heuristics.",
        },
        "filename_contract": {
            "request_positive_rows": "direct_manipulation_positive_rows.csv",
            "request_matched_controls": "direct_manipulation_matched_controls.csv",
            "request_provenance": "direct_manipulation_provenance.json",
            "verifier_positive_rows": "positive_spoofing_layering_rows.csv",
            "verifier_matched_controls": "matched_negative_normal_activity_rows.csv",
            "verifier_provenance": "provenance_manifest.json",
            "adapter_required": True,
            "adapter_approval_reference": "<approval-reference-for-copy-or-transform-step>",
        },
        "required_followup_chain": [
            "direct_manipulation_row_intake_verifier",
            "split_calibration_chronological_symbol_venue_or_approved_family",
            "provider_status_ibkr_tradingview_yfinance_kraken",
            "auto_quant_status_or_prepare",
            "pre_bayes_bbn_readback",
            "catboost_or_policy_training_readback",
            "workflow_execution_tree_and_path_ranking_readback",
        ],
        "no_proxy_acceptance": True,
    }

    target_files = [
        {
            "target_path": str(TARGET_ROOT / "validation_contract_approval.json"),
            "source_template": "validation_contract_approval_template_v1.json",
            "required_before_use": True,
            "purpose": "Explicit owner/user approval for a non-exact split contract or adapter branch.",
        },
        {
            "target_path": str(TARGET_ROOT / "owner_approval_reference.md"),
            "source_template": "owner_approval_reference_template_v1.md",
            "required_before_use": True,
            "purpose": "Human-readable approval reference matching the JSON approval.",
        },
        {
            "target_path": str(TARGET_ROOT / "positive_spoofing_layering_rows.csv"),
            "source_template": "filename_contract_checklist_v1.csv",
            "required_before_use": True,
            "purpose": "Verifier-native positive rows or approved adapter output.",
        },
        {
            "target_path": str(TARGET_ROOT / "matched_negative_normal_activity_rows.csv"),
            "source_template": "filename_contract_checklist_v1.csv",
            "required_before_use": True,
            "purpose": "Verifier-native matched controls or approved adapter output.",
        },
        {
            "target_path": str(TARGET_ROOT / "provenance_manifest.json"),
            "source_template": "filename_contract_checklist_v1.csv",
            "required_before_use": True,
            "purpose": "Verifier-native provenance or approved adapter output.",
        },
    ]

    followup_rows = [
        {
            "step": "1",
            "command_or_check": "python3 <direct_manipulation_row_intake_verifier_v1.py> --intake-root /tmp/ict-engine-board-a-r6-owner-export-v1",
            "required_evidence": "status is schema_ready_unscored or stricter pass, required files present, rows counted",
            "may_accept_without": "false",
        },
        {
            "step": "2",
            "command_or_check": "rerun chronological/symbol/venue or approved-family split calibration",
            "required_evidence": "every accepted bucket has Wilson95 LCB >= 0.95 with positive/control support",
            "may_accept_without": "false",
        },
        {
            "step": "3",
            "command_or_check": "provider-status for IBKR, TradingViewRemix/MCP, yfinance, Kraken",
            "required_evidence": "provider readiness recorded; missing providers are non-promoting blockers",
            "may_accept_without": "false",
        },
        {
            "step": "4",
            "command_or_check": "Auto-Quant status/prepare/readback",
            "required_evidence": "Auto-Quant state and artifacts captured under docs/experiments",
            "may_accept_without": "false",
        },
        {
            "step": "5",
            "command_or_check": "pre-Bayes/BBN, CatBoost or policy-training, workflow-status, execution-tree/path-ranking",
            "required_evidence": "downstream readbacks consume the accepted export or remain explicitly non-promoting",
            "may_accept_without": "false",
        },
    ]

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": generated_at,
        "board_sha256_at_start": sha256(BOARD),
        "target_root": str(TARGET_ROOT),
        "request_matrix_rows": len(request_matrix),
        "request_field_rows": len(request_fields),
        "schema_path": "validation_contract_approval_schema_v1.json",
        "template_path": "validation_contract_approval_template_v1.json",
        "target_files": target_files,
        "approval_created": False,
        "rows_acquired": False,
        "shared_intake_mutated": False,
        "runtime_code_changed": False,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "gate_result": "r6_split_contract_approval_template_v1=template_ready_no_approval_rows_not_acquired",
        "next_action": "Owner/user must place approved row exports and validation_contract_approval.json under the target root or approve a different split contract before the direct verifier and downstream chain can rerun.",
    }

    schema_path = OUT / "validation_contract_approval_schema_v1.json"
    template_path = OUT / "validation_contract_approval_template_v1.json"
    summary_path = OUT / "r6_split_contract_approval_template_v1.json"
    md_path = OUT / "r6_split_contract_approval_template_v1.md"
    owner_ref_path = OUT / "owner_approval_reference_template_v1.md"
    target_files_path = OUT / "target_root_file_contract_v1.csv"
    followup_path = OUT / "post_approval_followup_chain_v1.csv"
    assertions_path = CHECKS / "r6_split_contract_approval_template_v1_assertions.out"

    schema_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    template_path.write_text(json.dumps(approval_template, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        target_files_path,
        target_files,
        ["target_path", "source_template", "required_before_use", "purpose"],
    )
    write_csv(
        followup_path,
        followup_rows,
        ["step", "command_or_check", "required_evidence", "may_accept_without"],
    )

    owner_ref_path.write_text(
        "\n".join(
            [
                "# Owner Approval Reference Template v1",
                "",
                "This file is a template, not an approval.",
                "",
                "- Approval state: `<approved>`",
                "- Approved by: `<user-or-source-owner>`",
                "- Approval timestamp UTC: `<YYYY-MM-DDTHH:MM:SSZ>`",
                "- Approved contract id: `<r6_exact_contract_bulk_export|r6_family_contract_export|r6_species_completion_export|r6_other_owner_approved_contract>`",
                "- Source/export reference: `<ticket/signed-note/source-export-id>`",
                "- Adapter/copy-step approval reference: `<required if request filenames differ from verifier filenames>`",
                "",
                "Required statement:",
                "",
                "> I approve this validation contract for Board A R6 direct Manipulation only. I understand this does not accept rows, relax thresholds, or allow OHLCV/proxy labels. The direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readbacks must rerun before any confidence claim.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    md_lines = [
        "# R6 Split-Contract Approval Template v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Target root: `{TARGET_ROOT}`.",
        "- Approval created: `false`; rows acquired: `false`; shared intake mutated: `false`.",
        f"- Gate result: `{summary['gate_result']}`.",
        "",
        "## Files",
        "",
        f"- Summary JSON: `{summary_path.relative_to(REPO)}`",
        f"- Approval schema: `{schema_path.relative_to(REPO)}`",
        f"- Approval JSON template: `{template_path.relative_to(REPO)}`",
        f"- Owner approval markdown template: `{owner_ref_path.relative_to(REPO)}`",
        f"- Target-root file contract: `{target_files_path.relative_to(REPO)}`",
        f"- Post-approval followup chain: `{followup_path.relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        "",
        "## Interpretation",
        "",
        "The V62 request package already defines the row-export branch. This artifact makes the alternate explicit split-contract approval branch concrete and machine-checkable. It is not an approval and cannot unblock Board A by itself.",
    ]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertions = [
        ("schema_written", schema_path.exists()),
        ("template_written", template_path.exists()),
        ("owner_reference_template_written", owner_ref_path.exists()),
        ("target_root_contract_written", target_files_path.exists()),
        ("followup_chain_written", followup_path.exists()),
        ("approval_created_false", summary["approval_created"] is False),
        ("rows_acquired_false", summary["rows_acquired"] is False),
        ("strict_full_objective_false", summary["strict_full_objective_achieved"] is False),
        ("update_goal_false", summary["update_goal"] is False),
        ("proxy_acceptance_forbidden", approval_template["no_proxy_acceptance"] is True),
    ]
    assertions_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in assertions) + "\n",
        encoding="utf-8",
    )
    if not all(passed for _, passed in assertions):
        raise SystemExit(2)

    print(json.dumps({"gate_result": summary["gate_result"], "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
