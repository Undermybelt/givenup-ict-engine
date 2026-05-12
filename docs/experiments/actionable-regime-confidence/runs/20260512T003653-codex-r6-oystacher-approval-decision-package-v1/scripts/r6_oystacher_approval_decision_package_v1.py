#!/usr/bin/env python3
"""Build the R6 Oystacher approval decision package.

This script is intentionally write-only under its run root. It reads the
existing isolated materialization and V65 policy review, then emits a
machine-readable decision packet. It does not approve the packet, mutate any
intake root, or run downstream gates.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ID = "20260512T003653-codex-r6-oystacher-approval-decision-package-v1"
GENERATED_AT_UTC = "2026-05-11T16:36:53+00:00"
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT = ROOT / "r6-oystacher-approval-decision-package"
CHECKS = ROOT / "checks"

MATERIALIZATION_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/"
    "r6-oystacher-exhibit-a-row-materialization/"
    "r6_oystacher_exhibit_a_row_materialization_v1.json"
)
SOURCE_POLICY_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T003051-codex-r6-oystacher-exhibit-a-source-policy-review-v1/"
    "r6-oystacher-exhibit-a-source-policy-review/"
    "r6_oystacher_exhibit_a_source_policy_review_v1.json"
)
CONTROL_POLICY_JSON = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T003334-codex-r6-oystacher-exhibit-a-policy-review-v1/"
    "r6-oystacher-exhibit-a-policy-review/"
    "r6_oystacher_exhibit_a_policy_review_v1.json"
)


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    materialization = read_json(MATERIALIZATION_JSON)
    source_policy = read_json(SOURCE_POLICY_JSON)
    control_policy = read_json(CONTROL_POLICY_JSON)

    row_counts = {
        "parsed_order_rows": materialization["parsed_order_rows"],
        "positive_spoof_rows": materialization["positive_candidate_rows"],
        "flip_rows": materialization["matched_control_candidate_rows"],
        "matched_groups": materialization["direct_verifier"]["parsed"]["matched_group_count"],
        "isolated_split_axes_pass": materialization["all_materialized_split_axes_pass"],
        "isolated_verifier_status": materialization["direct_verifier"]["parsed"]["status"],
    }

    approval_slots = [
        {
            "slot_id": "public_recap_pacer_provenance",
            "current_state": "pending_explicit_user_or_board_approval",
            "current_evidence": "CourtListener/RECAP mirror of court-filed CFTC Exhibit A with stable PDF SHA-256.",
            "minimum_approval_value": "approved",
            "merge_effect_if_approved": "Allows source provenance to be used for canonical R6 intake, subject to control-policy approval or separate normal controls.",
        },
        {
            "slot_id": "same_exhibit_flip_as_matched_controls",
            "current_state": "rejected_under_current_contract",
            "current_evidence": "FLIP rows are same-exhibit sequence counterpart legs, not source-owned normal/non-manipulation labels.",
            "minimum_approval_value": "explicitly_approved_as_matched_controls",
            "merge_effect_if_approved": "Allows isolated FLIP rows to populate matched_negative_normal_activity_rows.csv after verifier-native copy under lock.",
        },
        {
            "slot_id": "source_owned_normal_controls_alternative",
            "current_state": "not_supplied",
            "current_evidence": "No independent owner-approved normal controls are present in the target root.",
            "minimum_approval_value": "source_owned_normal_controls_supplied",
            "merge_effect_if_approved": "Allows R6 to proceed without approving same-exhibit FLIP rows as controls.",
        },
    ]

    decision_options = [
        {
            "decision_id": "approve_recap_and_flip_controls",
            "public_recap_pacer_provenance": "approved",
            "flip_control_policy": "explicitly_approved_as_matched_controls",
            "source_owned_normal_controls_required": "false",
            "canonical_merge_allowed_after_lock": "true",
            "downstream_rerun_required": "true",
            "gate_if_chosen": "approval_ready_merge_then_rerun_full_chain",
        },
        {
            "decision_id": "approve_recap_reject_flip_supply_controls",
            "public_recap_pacer_provenance": "approved",
            "flip_control_policy": "rejected",
            "source_owned_normal_controls_required": "true",
            "canonical_merge_allowed_after_lock": "only_after_controls_supplied",
            "downstream_rerun_required": "true_after_controls",
            "gate_if_chosen": "source_positive_ready_controls_still_required",
        },
        {
            "decision_id": "reject_recap_use_owner_export_only",
            "public_recap_pacer_provenance": "rejected",
            "flip_control_policy": "not_applicable",
            "source_owned_normal_controls_required": "true",
            "canonical_merge_allowed_after_lock": "false_until_owner_export",
            "downstream_rerun_required": "false_until_owner_export",
            "gate_if_chosen": "owner_export_required",
        },
        {
            "decision_id": "no_decision_keep_blocked",
            "public_recap_pacer_provenance": "pending",
            "flip_control_policy": "pending_or_rejected",
            "source_owned_normal_controls_required": "true_if_flip_rejected",
            "canonical_merge_allowed_after_lock": "false",
            "downstream_rerun_required": "false",
            "gate_if_chosen": "decision_package_ready_no_approval_no_merge",
        },
    ]

    followup_chain = [
        {
            "step_order": 1,
            "step_id": "shared_lock",
            "command_or_artifact": "/tmp/ict-engine-direct-manipulation-row-intake.lock",
            "allowed_before_approval": "false",
            "required_after_approval": "true",
        },
        {
            "step_order": 2,
            "step_id": "verifier_native_copy",
            "command_or_artifact": "/tmp/ict-engine-board-a-r6-owner-export-v1/{positive_spoofing_layering_rows.csv,matched_negative_normal_activity_rows.csv,provenance_manifest.json}",
            "allowed_before_approval": "false",
            "required_after_approval": "true",
        },
        {
            "step_order": 3,
            "step_id": "direct_verifier",
            "command_or_artifact": "direct_manipulation_row_intake_verifier",
            "allowed_before_approval": "false",
            "required_after_approval": "true",
        },
        {
            "step_order": 4,
            "step_id": "split_calibration",
            "command_or_artifact": "chronological plus symbol/venue or explicitly approved family split calibration",
            "allowed_before_approval": "false",
            "required_after_approval": "true",
        },
        {
            "step_order": 5,
            "step_id": "provider_and_downstream_chain",
            "command_or_artifact": "provider status, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, workflow/execution-tree readback",
            "allowed_before_approval": "false",
            "required_after_approval": "true",
        },
    ]

    approval_template = {
        "approval_state": "pending",
        "approval_timestamp_utc": None,
        "approved_by": None,
        "run_id_under_review": RUN_ID,
        "source_pdf_url": materialization["source_pdf_url"],
        "raw_pdf_sha256": materialization["raw_pdf_sha256"],
        "decisions": {
            "public_recap_pacer_provenance": None,
            "same_exhibit_flip_as_matched_controls": None,
            "source_owned_normal_controls_supplied": None,
        },
        "required_if_approved": {
            "use_shared_lock": True,
            "use_verifier_native_filenames": True,
            "rerun_direct_verifier": True,
            "rerun_split_calibration": True,
            "rerun_provider_autoquant_prebayes_bbn_catboost_execution_tree": True,
        },
        "approval_reference": None,
        "notes": "Set the two decision booleans explicitly, or attach source-owned normal controls if FLIP is rejected.",
    }

    assertions = {
        "approval_present": False,
        "canonical_merge_allowed_now": False,
        "downstream_rerun_allowed_now": False,
        "flip_controls_accepted_under_current_contract": False,
        "public_recap_source_positive_candidate": True,
        "shared_intake_mutated": False,
        "strict_full_objective_achieved": False,
        "trade_usable": False,
        "update_goal": False,
    }

    package = {
        "run_id": RUN_ID,
        "generated_at_utc": GENERATED_AT_UTC,
        "source_materialization_json": str(MATERIALIZATION_JSON),
        "source_policy_json": str(SOURCE_POLICY_JSON),
        "control_policy_json": str(CONTROL_POLICY_JSON),
        "row_counts": row_counts,
        "source": {
            "source_pdf_url": materialization["source_pdf_url"],
            "raw_pdf_sha256": materialization["raw_pdf_sha256"],
            "courtlistener_docket_url": materialization["courtlistener_docket_url"],
            "raw_data_committed": False,
        },
        "approval_slots": approval_slots,
        "decision_options": decision_options,
        "followup_chain": followup_chain,
        "assertions": assertions,
        "gate_result": "r6_oystacher_approval_decision_package_v1=decision_package_ready_no_approval_no_merge",
        "next_action": "Record one explicit decision option. Do not merge isolated rows or rerun downstream chain until RECAP/PACER provenance plus FLIP-as-control approval exist, or source-owned normal controls are supplied.",
    }

    checks = [
        ("materialization_rows_match", row_counts["parsed_order_rows"] == 6735),
        ("positive_rows_match", row_counts["positive_spoof_rows"] == 5182),
        ("flip_rows_match", row_counts["flip_rows"] == 1553),
        ("source_policy_not_approved", source_policy["approved_for_canonical_merge"] is False),
        (
            "control_policy_rejects_flip_controls",
            control_policy["decision"]["flip_rows_accepted_as_matched_normal_controls"] is False,
        ),
        ("canonical_merge_blocked_now", assertions["canonical_merge_allowed_now"] is False),
        ("downstream_rerun_blocked_now", assertions["downstream_rerun_allowed_now"] is False),
    ]
    failed = [name for name, ok in checks if not ok]
    if failed:
        raise SystemExit(f"assertions failed: {', '.join(failed)}")

    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    write_json(OUT / "r6_oystacher_approval_decision_package_v1.json", package)
    write_json(OUT / "r6_oystacher_approval_template_v1.json", approval_template)
    write_csv(
        OUT / "r6_oystacher_approval_options_v1.csv",
        decision_options,
        [
            "decision_id",
            "public_recap_pacer_provenance",
            "flip_control_policy",
            "source_owned_normal_controls_required",
            "canonical_merge_allowed_after_lock",
            "downstream_rerun_required",
            "gate_if_chosen",
        ],
    )
    write_csv(
        OUT / "r6_oystacher_post_approval_chain_v1.csv",
        followup_chain,
        [
            "step_order",
            "step_id",
            "command_or_artifact",
            "allowed_before_approval",
            "required_after_approval",
        ],
    )
    report = "\n".join(
        [
            "# R6 Oystacher Approval Decision Package v1",
            "",
            f"Run ID: `{RUN_ID}`",
            "",
            "This package does not approve canonical promotion. It isolates the two explicit decisions needed before any copy into the owner-export root or canonical live intake.",
            "",
            "## Current evidence",
            "",
            f"- `SPOOF` positive candidates: `{row_counts['positive_spoof_rows']}`.",
            f"- Same-exhibit `FLIP` rows: `{row_counts['flip_rows']}`.",
            f"- Isolated verifier status: `{row_counts['isolated_verifier_status']}`.",
            f"- Isolated split axes pass: `{row_counts['isolated_split_axes_pass']}`.",
            f"- PDF SHA-256: `{materialization['raw_pdf_sha256']}`.",
            "",
            "## Required decision",
            "",
            "Choose exactly one decision option from `r6_oystacher_approval_options_v1.csv`. Until then, canonical merge and downstream rerun remain blocked.",
            "",
            "## Gate",
            "",
            "`r6_oystacher_approval_decision_package_v1=decision_package_ready_no_approval_no_merge`.",
        ]
    )
    (OUT / "r6_oystacher_approval_decision_package_v1.md").write_text(report + "\n", encoding="utf-8")
    CHECKS.joinpath("r6_oystacher_approval_decision_package_v1_assertions.out").write_text(
        "\n".join(f"{name}=pass" for name, _ in checks)
        + "\ncanonical_merge_allowed_now=false\n"
        + "downstream_rerun_allowed_now=false\n"
        + "strict_full_objective_achieved=false\n"
        + "update_goal=false\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
