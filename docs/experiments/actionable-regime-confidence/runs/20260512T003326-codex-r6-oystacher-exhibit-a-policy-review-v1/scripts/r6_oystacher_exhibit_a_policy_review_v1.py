#!/usr/bin/env python3
"""Policy review for Oystacher Exhibit A before any canonical intake merge."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T003326-codex-r6-oystacher-exhibit-a-policy-review-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-oystacher-exhibit-a-policy-review"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
MATERIALIZATION_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1"
    / "r6-oystacher-exhibit-a-row-materialization"
)
MATERIALIZATION_JSON = MATERIALIZATION_ROOT / "r6_oystacher_exhibit_a_row_materialization_v1.json"
PARSED_ROWS = MATERIALIZATION_ROOT / "oystacher_exhibit_a_parsed_order_rows_v1.csv"
SPLIT_METRICS = MATERIALIZATION_ROOT / "oystacher_exhibit_a_split_metrics_v1.csv"
PROVENANCE = MATERIALIZATION_ROOT / "isolated-oystacher-exhibit-a-intake/provenance_manifest.json"


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

    materialization = json.loads(MATERIALIZATION_JSON.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    parsed_rows = read_csv(PARSED_ROWS)
    split_rows = read_csv(SPLIT_METRICS)
    side_counts: dict[str, int] = {}
    for row in parsed_rows:
        side_counts[row["side_type"]] = side_counts.get(row["side_type"], 0) + 1

    source_policy = {
        "public_recap_pacer_exhibit_a": "usable_as_official_court_filed_positive_source_candidate",
        "positive_spoof_rows": "source_labeled_spoof_positive_candidates",
        "flip_rows": "rejected_as_normal_matched_controls",
        "rationale": (
            "The court-filed Exhibit A labels SPOOF rows directly, but FLIP rows are part of the "
            "same alleged flip sequences and same participant/order-lifecycle narrative. They are "
            "not owner-labeled normal/non-manipulation controls."
        ),
    }

    decision_rows = [
        {
            "requirement": "official_or_owner_source_provenance",
            "evidence": provenance.get("source_pdf_url", ""),
            "decision": "positive_source_candidate_ok",
            "promotion_effect": "can_seed_positive_rows_after owner/user policy approval and reproducible fetch",
        },
        {
            "requirement": "direct_positive_labels",
            "evidence": f"SPOOF rows={side_counts.get('SPOOF', 0)}",
            "decision": "positive_candidates_ok",
            "promotion_effect": "large positive supply for spoofing_layering",
        },
        {
            "requirement": "matched normal/non-manipulation controls",
            "evidence": f"FLIP rows={side_counts.get('FLIP', 0)} from same exhibit/sequences",
            "decision": "rejected",
            "promotion_effect": "cannot use as matched_negative_normal_activity",
        },
        {
            "requirement": "split axes Wilson95",
            "evidence": f"isolated split pass={materialization.get('all_materialized_split_axes_pass')}",
            "decision": "diagnostic_only",
            "promotion_effect": "invalid for acceptance until controls are valid",
        },
        {
            "requirement": "canonical intake merge",
            "evidence": "controls rejected; no owner/user approval file in target root",
            "decision": "blocked",
            "promotion_effect": "do not mutate live intake",
        },
        {
            "requirement": "downstream chain rerun",
            "evidence": "no accepted canonical intake change",
            "decision": "blocked",
            "promotion_effect": "do not rerun provider/Auto-Quant/BBN/CatBoost/execution-tree as promotion evidence",
        },
    ]

    control_risk_rows = [
        {
            "candidate_control_class": "FLIP",
            "source_context": "same court-filed Exhibit A as SPOOF rows",
            "risk": "same alleged manipulation sequence, not normal baseline",
            "decision": "reject_as_normal_control",
            "required_replacement": "owner-approved normal/non-manipulation order-lifecycle rows matched by instrument/venue/session/time window",
        }
    ]

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "materialization_run": materialization.get("run_id"),
        "source_pdf_url": provenance.get("source_pdf_url"),
        "raw_pdf_sha256": provenance.get("raw_pdf_sha256"),
        "parsed_order_rows": len(parsed_rows),
        "side_counts": side_counts,
        "isolated_split_axes_pass": materialization.get("all_materialized_split_axes_pass"),
        "source_policy": source_policy,
        "positive_source_policy_decision": "usable_as_positive_candidate_only",
        "matched_control_policy_decision": "rejected_flip_rows_not_normal_controls",
        "canonical_live_intake_merge_allowed": False,
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
        "gate_result": "r6_oystacher_exhibit_a_policy_review_v1=positive_source_candidate_controls_rejected_no_canonical_merge",
        "next_action": (
            "Source owner-approved normal/non-manipulation matched controls for the Exhibit A SPOOF rows, "
            "or get explicit owner/user approval for a different control contract, before any canonical merge "
            "or downstream chain rerun."
        ),
    }

    json_path = OUT / "r6_oystacher_exhibit_a_policy_review_v1.json"
    md_path = OUT / "r6_oystacher_exhibit_a_policy_review_v1.md"
    decision_path = OUT / "r6_oystacher_exhibit_a_policy_decision_matrix_v1.csv"
    risk_path = OUT / "r6_oystacher_exhibit_a_control_label_risk_v1.csv"
    assertions_path = CHECKS / "r6_oystacher_exhibit_a_policy_review_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(decision_path, decision_rows, ["requirement", "evidence", "decision", "promotion_effect"])
    write_csv(risk_path, control_risk_rows, ["candidate_control_class", "source_context", "risk", "decision", "required_replacement"])

    md_lines = [
        "# R6 Oystacher Exhibit A Policy Review v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Materialization run: `{materialization.get('run_id')}`.",
        f"- Parsed order rows: `{len(parsed_rows)}`; SPOOF rows: `{side_counts.get('SPOOF', 0)}`; FLIP rows: `{side_counts.get('FLIP', 0)}`.",
        f"- Positive source decision: `{result['positive_source_policy_decision']}`.",
        f"- Matched control decision: `{result['matched_control_policy_decision']}`.",
        f"- Canonical live intake merge allowed: `{str(result['canonical_live_intake_merge_allowed']).lower()}`.",
        f"- Downstream chain rerun allowed: `{str(result['downstream_chain_rerun_allowed']).lower()}`.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Rationale",
        "",
        "Court-filed Exhibit A is useful as a positive source candidate because it directly marks SPOOF rows. The FLIP rows are not accepted as normal controls because they are from the same alleged flip sequences and same defendant activity, so treating them as `matched_negative_normal_activity` would mislabel the control side.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Decision matrix: `{decision_path.relative_to(REPO)}`",
        f"- Control-label risk CSV: `{risk_path.relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
    ]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertions = [
        ("materialization_loaded", materialization.get("run_id") == "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1"),
        ("spoof_rows_present", side_counts.get("SPOOF", 0) >= 5000),
        ("flip_rows_present", side_counts.get("FLIP", 0) >= 1000),
        ("positive_source_candidate_only", result["positive_source_policy_decision"] == "usable_as_positive_candidate_only"),
        ("flip_controls_rejected", result["matched_control_policy_decision"] == "rejected_flip_rows_not_normal_controls"),
        ("canonical_merge_false", result["canonical_live_intake_merge_allowed"] is False),
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
