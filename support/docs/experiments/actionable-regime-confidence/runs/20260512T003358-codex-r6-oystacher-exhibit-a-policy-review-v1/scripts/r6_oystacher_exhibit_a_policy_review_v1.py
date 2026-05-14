#!/usr/bin/env python3
"""Policy review for promoting the isolated Oystacher Exhibit A materialization."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T003358-codex-r6-oystacher-exhibit-a-policy-review-v1"
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
POSITIVE_CSV = MATERIALIZATION_ROOT / "isolated-oystacher-exhibit-a-intake/positive_spoofing_layering_rows.csv"
CONTROL_CSV = MATERIALIZATION_ROOT / "isolated-oystacher-exhibit-a-intake/matched_negative_normal_activity_rows.csv"
PROVENANCE_JSON = MATERIALIZATION_ROOT / "isolated-oystacher-exhibit-a-intake/provenance_manifest.json"
SPLIT_CSV = MATERIALIZATION_ROOT / "oystacher_exhibit_a_split_metrics_v1.csv"


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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    materialization = json.loads(MATERIALIZATION_JSON.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE_JSON.read_text(encoding="utf-8"))
    positive_sample = read_csv_rows(POSITIVE_CSV)[:5]
    control_sample = read_csv_rows(CONTROL_CSV)[:5]
    split_rows = read_csv_rows(SPLIT_CSV)

    decisions = [
        {
            "gate": "source_provenance",
            "evidence": "Court-filed Exhibit A from RECAP/CourtListener with docket URL, raw hash, CFTC complaint URL, and CFTC press URL.",
            "decision": "conditional_candidate_not_canonical",
            "reason": "The artifact is a public court-record copy and strong source evidence, but the active V62 contract still requires owner/user-approved export rows or explicit approval before canonical intake mutation.",
        },
        {
            "gate": "positive_rows",
            "evidence": "Exhibit A labels 5182 rows as SPOOF and the isolated verifier accepts their schema.",
            "decision": "positive_candidates_source_labeled",
            "reason": "SPOOF rows can remain high-quality direct positive candidates, subject to provenance approval.",
        },
        {
            "gate": "matched_controls",
            "evidence": "The 1553 rows used as controls are Exhibit A rows labeled FLIP from the same Oystacher/3Red flip sequences.",
            "decision": "reject_as_normal_controls_without_explicit_approval",
            "reason": "FLIP rows are same-defendant same-exhibit sequence rows, not source-owned normal/non-manipulation labels or report-negative matched controls under the current Board A contract.",
        },
        {
            "gate": "split_metrics",
            "evidence": "Materialized split metrics pass across family, venue, symbol, and year when FLIP rows are treated as negatives.",
            "decision": "not_accepted_until_control_policy_passes",
            "reason": "The split pass depends on treating FLIP rows as matched negatives, so it is a proxy signal until the control policy is approved.",
        },
        {
            "gate": "canonical_merge",
            "evidence": "No shared lock merge or live canonical intake mutation has occurred.",
            "decision": "do_not_merge",
            "reason": "Canonical mutation requires provenance approval plus valid matched controls or explicit user approval of the FLIP-control contract.",
        },
        {
            "gate": "downstream_chain",
            "evidence": "No accepted canonical row or validation-contract change exists after policy review.",
            "decision": "do_not_rerun_downstream",
            "reason": "Provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun would be a proxy signal until canonical acceptance changes.",
        },
    ]

    checklist = [
        {
            "requirement": "real public source row materialization",
            "evidence": rel(MATERIALIZATION_JSON),
            "status": "satisfied_isolated",
        },
        {
            "requirement": "source-owned positives",
            "evidence": f"SPOOF rows={materialization.get('positive_candidate_rows')}",
            "status": "candidate_satisfied",
        },
        {
            "requirement": "matched normal controls",
            "evidence": f"FLIP rows={materialization.get('matched_control_candidate_rows')}",
            "status": "not_satisfied_under_current_contract",
        },
        {
            "requirement": "cross-market/cycle split confidence",
            "evidence": rel(SPLIT_CSV),
            "status": "proxy_only_until_controls_accepted",
        },
        {
            "requirement": "canonical intake merge",
            "evidence": "shared_intake_mutated=false",
            "status": "not_done",
        },
        {
            "requirement": "provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun",
            "evidence": "no accepted canonical row or contract change",
            "status": "not_run_by_policy",
        },
    ]

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "materialization_run": rel(MATERIALIZATION_JSON),
        "positive_rows": materialization.get("positive_candidate_rows"),
        "flip_control_candidate_rows": materialization.get("matched_control_candidate_rows"),
        "matched_groups": (materialization.get("direct_verifier") or {}).get("parsed", {}).get("matched_group_count"),
        "all_materialized_split_axes_pass": materialization.get("all_materialized_split_axes_pass"),
        "source_pdf_url": materialization.get("source_pdf_url"),
        "raw_pdf_sha256": materialization.get("raw_pdf_sha256"),
        "provenance_keys": sorted(provenance.keys()),
        "positive_sample_rows": positive_sample,
        "control_sample_rows": control_sample,
        "split_metric_rows": len(split_rows),
        "decisions": decisions,
        "prompt_to_artifact_checklist": checklist,
        "source_provenance_policy": "conditional_candidate_not_canonical_without_owner_user_approval",
        "control_policy": "flip_rows_rejected_as_matched_normal_controls_without_explicit_approval",
        "canonical_merge_approved": False,
        "rerun_downstream_chain": False,
        "gate_result": "r6_oystacher_exhibit_a_policy_review_v1=positive_rows_candidate_controls_rejected_no_canonical_merge",
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
        "next_action": "If the user approves RECAP/PACER provenance and explicitly approves FLIP rows as matched controls, merge through the shared lock and rerun the direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree chain; otherwise source independent owner-approved normal controls.",
    }

    json_path = OUT / "r6_oystacher_exhibit_a_policy_review_v1.json"
    report_path = OUT / "r6_oystacher_exhibit_a_policy_review_v1.md"
    decisions_csv = OUT / "r6_oystacher_exhibit_a_policy_decisions_v1.csv"
    checklist_csv = OUT / "prompt_to_artifact_checklist_v1.csv"
    checks_path = CHECKS / "r6_oystacher_exhibit_a_policy_review_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(decisions_csv, decisions, ["gate", "evidence", "decision", "reason"])
    write_csv(checklist_csv, checklist, ["requirement", "evidence", "status"])

    report = f"""# R6 Oystacher Exhibit A Policy Review v1

- Run id: `{RUN_ID}`.
- Materialization reviewed: `{rel(MATERIALIZATION_JSON)}`.
- Positive candidate rows: `{payload["positive_rows"]}`.
- FLIP control candidate rows: `{payload["flip_control_candidate_rows"]}`.
- Isolated split axes pass: `{str(payload["all_materialized_split_axes_pass"]).lower()}`.
- Source provenance policy: `{payload["source_provenance_policy"]}`.
- Control policy: `{payload["control_policy"]}`.
- Canonical merge approved: `false`; downstream chain rerun: `false`.
- Gate result: `{payload["gate_result"]}`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Decision

The Oystacher Exhibit A materialization is valuable positive evidence, but it is not enough to mutate the canonical R6 intake under the current Board A contract.

The `SPOOF` rows are source-labeled direct positive candidates. The `FLIP` rows remain blocked as matched normal controls: they are same-defendant, same-exhibit sequence rows, not source-owned normal/non-manipulation labels or report-negative matched controls. Therefore the isolated split pass is not accepted as a strict Board A confidence gate.

## Next

If the user approves RECAP/PACER provenance and explicitly approves `FLIP` rows as matched controls, merge through the shared lock and rerun the direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree chain. Otherwise source independent owner-approved normal controls for the Oystacher `SPOOF` positives.

## Artifacts

- JSON: `{rel(json_path)}`
- Policy decisions CSV: `{rel(decisions_csv)}`
- Prompt-to-artifact checklist: `{rel(checklist_csv)}`
- Assertions: `{rel(checks_path)}`
"""
    report_path.write_text(report, encoding="utf-8")

    assertions = [
        ("materialization_loaded", materialization.get("positive_candidate_rows", 0) >= 5000),
        ("isolated_splits_pass_seen", materialization.get("all_materialized_split_axes_pass") is True),
        ("positive_candidates_preserved", payload["positive_rows"] == 5182),
        ("flip_controls_rejected_without_approval", payload["control_policy"].startswith("flip_rows_rejected")),
        ("canonical_merge_false", payload["canonical_merge_approved"] is False),
        ("downstream_rerun_false", payload["rerun_downstream_chain"] is False),
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
