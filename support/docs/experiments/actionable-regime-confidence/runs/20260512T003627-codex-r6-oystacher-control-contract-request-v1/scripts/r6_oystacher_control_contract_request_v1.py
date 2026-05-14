#!/usr/bin/env python3
"""Create a targeted control-contract request for Oystacher Exhibit A SPOOF rows."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T003627-codex-r6-oystacher-control-contract-request-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-oystacher-control-contract-request"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
POLICY_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T003334-codex-r6-oystacher-exhibit-a-policy-review-v1"
    / "r6-oystacher-exhibit-a-policy-review"
)
POLICY_JSON = POLICY_ROOT / "r6_oystacher_exhibit_a_policy_review_v1.json"
MATERIALIZATION_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1"
    / "r6-oystacher-exhibit-a-row-materialization"
)
SPLIT_METRICS = MATERIALIZATION_ROOT / "oystacher_exhibit_a_split_metrics_v1.csv"
TARGET_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")


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

    policy = json.loads(POLICY_JSON.read_text(encoding="utf-8"))
    split_rows = read_csv(SPLIT_METRICS)
    required_cells = []
    for row in split_rows:
        positive_support = int(row["positive_support"])
        invalid_flip_support = int(row["negative_support"])
        required_cells.append(
            {
                "axis": row["axis"],
                "bucket": row["bucket"],
                "positive_spoof_support": positive_support,
                "invalid_flip_candidate_support": invalid_flip_support,
                "required_valid_normal_control_support": 73,
                "valid_normal_control_support_observed": 0,
                "valid_normal_control_shortfall": 73,
                "decision": "needs_source_owned_normal_controls_or_explicit_flip_control_approval",
            }
        )

    control_options = [
        {
            "option_id": "source_owned_normal_controls",
            "decision_before_use": "owner/source export required",
            "required_payload": "matched_negative_normal_activity_rows.csv plus provenance_manifest.json",
            "acceptance_note": "Preferred branch. Controls must be normal/non-manipulation rows matched by instrument or family, venue or family, session, and time window.",
        },
        {
            "option_id": "explicit_flip_as_control_contract",
            "decision_before_use": "explicit board/user approval required",
            "required_payload": "validation_contract_approval.json and owner_approval_reference.md naming FLIP-as-control exception",
            "acceptance_note": "Exception branch. Approval must acknowledge FLIP rows are same-sequence counterpart legs and are not source-owned normal controls.",
        },
    ]

    flip_approval_template = {
        "approval_state": "approved",
        "approved_by": "<user-or-source-owner>",
        "approval_timestamp_utc": "<YYYY-MM-DDTHH:MM:SSZ>",
        "approved_contract_id": "r6_oystacher_exhibit_a_flip_as_control_exception",
        "source_materialization_run": "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1",
        "policy_review_run": "20260512T003334-codex-r6-oystacher-exhibit-a-policy-review-v1",
        "acknowledged_risks": [
            "FLIP rows are same-exhibit same-sequence counterpart legs.",
            "FLIP rows are not source-owned normal/non-manipulation controls under the default R6 contract.",
            "Acceptance is a deliberate control-contract exception and must be recorded before canonical merge.",
        ],
        "required_followup": [
            "copy verifier-native files under /tmp/ict-engine-board-a-r6-owner-export-v1 under shared lock",
            "rerun direct_manipulation_row_intake_verifier",
            "rerun split calibration",
            "rerun provider status for IBKR, TradingView, yfinance, Kraken",
            "rerun Auto-Quant, pre-Bayes/BBN, CatBoost/policy-training, workflow/execution-tree, and path-ranking readback",
        ],
        "no_ohlcv_proxy_acceptance": True,
    }

    target_files = [
        {
            "target_path": str(TARGET_ROOT / "matched_negative_normal_activity_rows.csv"),
            "required_for": "source_owned_normal_controls",
            "status": "missing",
            "notes": "Must contain source-owned normal/non-manipulation rows, not same-sequence FLIP rows, unless exception approved.",
        },
        {
            "target_path": str(TARGET_ROOT / "validation_contract_approval.json"),
            "required_for": "explicit_flip_as_control_contract",
            "status": "missing",
            "notes": "Use flip_control_approval_template_v1.json only if user/owner approves the exception.",
        },
        {
            "target_path": str(TARGET_ROOT / "owner_approval_reference.md"),
            "required_for": "explicit_flip_as_control_contract",
            "status": "missing",
            "notes": "Human-readable approval reference must match validation_contract_approval.json.",
        },
    ]

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "policy_review_run": policy.get("run_id"),
        "positive_rows": policy.get("positive_spoof_candidates", 5182),
        "flip_rows_rejected_as_controls": True,
        "required_cell_count": len(required_cells),
        "control_options": [row["option_id"] for row in control_options],
        "source_owned_normal_controls_acquired": False,
        "flip_as_control_approved": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
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
        "gate_result": "r6_oystacher_control_contract_request_v1=control_request_ready_no_controls_or_approval",
        "next_action": "Supply source-owned normal controls for each required cell or explicitly approve the same-exhibit FLIP-as-control exception before canonical merge and downstream rerun.",
    }

    json_path = OUT / "r6_oystacher_control_contract_request_v1.json"
    md_path = OUT / "r6_oystacher_control_contract_request_v1.md"
    cells_path = OUT / "r6_oystacher_required_normal_control_cells_v1.csv"
    options_path = OUT / "r6_oystacher_control_contract_options_v1.csv"
    target_path = OUT / "r6_oystacher_target_control_files_v1.csv"
    flip_template_path = OUT / "flip_control_approval_template_v1.json"
    assertions_path = CHECKS / "r6_oystacher_control_contract_request_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    flip_template_path.write_text(json.dumps(flip_approval_template, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        cells_path,
        required_cells,
        [
            "axis",
            "bucket",
            "positive_spoof_support",
            "invalid_flip_candidate_support",
            "required_valid_normal_control_support",
            "valid_normal_control_support_observed",
            "valid_normal_control_shortfall",
            "decision",
        ],
    )
    write_csv(options_path, control_options, ["option_id", "decision_before_use", "required_payload", "acceptance_note"])
    write_csv(target_path, target_files, ["target_path", "required_for", "status", "notes"])

    md_lines = [
        "# R6 Oystacher Control Contract Request v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Policy review run: `{policy.get('run_id')}`.",
        "- Purpose: make the V65 control blocker executable without accepting FLIP rows by default.",
        f"- Required validation cells: `{len(required_cells)}`.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Accepted rows added: `0`; controls acquired: `false`; FLIP-as-control approved: `false`; `update_goal=false`.",
        "",
        "## Options",
        "",
        "1. Preferred: supply source-owned normal/non-manipulation controls matched to the Exhibit A SPOOF rows.",
        "2. Exception: explicitly approve the same-exhibit FLIP-as-control contract using the template; this still requires the full verifier/split/provider/Auto-Quant/BBN/CatBoost/execution-tree rerun.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Required normal-control cells: `{cells_path.relative_to(REPO)}`",
        f"- Control contract options: `{options_path.relative_to(REPO)}`",
        f"- Target control files: `{target_path.relative_to(REPO)}`",
        f"- FLIP-control approval template: `{flip_template_path.relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
    ]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertions = [
        ("policy_review_loaded", policy.get("run_id") == "20260512T003334-codex-r6-oystacher-exhibit-a-policy-review-v1"),
        ("required_cells_present", len(required_cells) > 0),
        ("all_cells_need_valid_controls", all(row["valid_normal_control_shortfall"] == 73 for row in required_cells)),
        ("source_controls_not_acquired", result["source_owned_normal_controls_acquired"] is False),
        ("flip_control_not_approved", result["flip_as_control_approved"] is False),
        ("canonical_merge_false", result["canonical_merge_allowed"] is False),
        ("downstream_rerun_false", result["downstream_chain_rerun_allowed"] is False),
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

    print(json.dumps({"gate_result": result["gate_result"], "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
