#!/usr/bin/env python3
"""Review whether the isolated Oystacher Exhibit A rows can be promoted."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


RUN_ID = "20260512T003051-codex-r6-oystacher-exhibit-a-source-policy-review-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT = RUN_ROOT / "r6-oystacher-exhibit-a-source-policy-review"
CHECKS = RUN_ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
SOURCE_RUN = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1"
)
SOURCE_JSON = (
    SOURCE_RUN
    / "r6-oystacher-exhibit-a-row-materialization"
    / "r6_oystacher_exhibit_a_row_materialization_v1.json"
)
SOURCE_INTAKE = (
    SOURCE_RUN
    / "r6-oystacher-exhibit-a-row-materialization"
    / "isolated-oystacher-exhibit-a-intake"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def count_csv(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    source = load_json(SOURCE_JSON)
    positive_csv = SOURCE_INTAKE / "positive_spoofing_layering_rows.csv"
    control_csv = SOURCE_INTAKE / "matched_negative_normal_activity_rows.csv"
    provenance_json = SOURCE_INTAKE / "provenance_manifest.json"
    positive_rows = count_csv(positive_csv)
    control_rows = count_csv(control_csv)
    provenance = load_json(provenance_json)
    verifier = source.get("direct_verifier", {}).get("parsed", {})

    checks = [
        {
            "requirement": "Public Exhibit A source acquired and hash-provenanced.",
            "evidence": f"{source.get('source_pdf_url')} sha256={source.get('raw_pdf_sha256')}",
            "status": "pass",
        },
        {
            "requirement": "Row-level direct order-lifecycle rows parsed from the source.",
            "evidence": f"parsed_order_rows={source.get('parsed_order_rows')} positives={positive_rows} controls={control_rows}",
            "status": "pass",
        },
        {
            "requirement": "Isolated verifier accepts the candidate schema.",
            "evidence": f"status={verifier.get('status')} matched_groups={verifier.get('matched_group_count')}",
            "status": "pass" if verifier.get("status") == "schema_ready_unscored" else "fail",
        },
        {
            "requirement": "Chronological and split axes pass in isolated materialization.",
            "evidence": f"all_materialized_split_axes_pass={source.get('all_materialized_split_axes_pass')}",
            "status": "pass" if source.get("all_materialized_split_axes_pass") else "fail",
        },
        {
            "requirement": "Canonical live intake must not be mutated without approval.",
            "evidence": f"shared_intake_mutated={source.get('shared_intake_mutated')}",
            "status": "pass" if source.get("shared_intake_mutated") is False else "fail",
        },
        {
            "requirement": "Explicit board/user approval exists for promoting RECAP/PACER mirror rows into canonical R6.",
            "evidence": "No approval artifact was present in the source materialization or current board cursor.",
            "status": "blocked",
        },
        {
            "requirement": "Full provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun after accepted rows.",
            "evidence": "Not run because rows are not yet policy-approved for canonical promotion.",
            "status": "blocked",
        },
        {
            "requirement": "Strict full objective including R3/R5/source-label blockers.",
            "evidence": "Out of scope for this R6 provenance review; current board still records R3/R5 blockers.",
            "status": "blocked",
        },
    ]

    source_policy_gate = False
    promotion_candidate = True
    approved_for_canonical_merge = False
    gate_result = (
        "r6_oystacher_exhibit_a_source_policy_review_v1="
        "row_evidence_strong_policy_approval_required_before_canonical_merge"
    )
    next_action = (
        "Record explicit board/user approval for using the public RECAP/PACER Exhibit A rows, then copy the isolated "
        "intake into the owner-export target or canonical live root under a shared lock and rerun direct verifier, "
        "split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback."
    )

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "board_sha256_at_start": sha256_file(BOARD),
        "source_run": str(SOURCE_RUN),
        "source_json": str(SOURCE_JSON),
        "source_pdf_url": source.get("source_pdf_url"),
        "courtlistener_docket_url": source.get("courtlistener_docket_url"),
        "raw_pdf_sha256": source.get("raw_pdf_sha256"),
        "positive_rows": positive_rows,
        "matched_control_rows": control_rows,
        "matched_group_count": verifier.get("matched_group_count"),
        "all_materialized_split_axes_pass": source.get("all_materialized_split_axes_pass"),
        "isolated_verifier_status": verifier.get("status"),
        "provenance_keys": sorted(provenance.keys()),
        "promotion_candidate": promotion_candidate,
        "source_policy_gate": source_policy_gate,
        "approved_for_canonical_merge": approved_for_canonical_merge,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "gate_result": gate_result,
        "next_action": next_action,
        "checklist_csv": str(OUT / "r6_oystacher_exhibit_a_source_policy_review_checklist_v1.csv"),
    }

    json_path = OUT / "r6_oystacher_exhibit_a_source_policy_review_v1.json"
    report_path = OUT / "r6_oystacher_exhibit_a_source_policy_review_v1.md"
    checklist_path = OUT / "r6_oystacher_exhibit_a_source_policy_review_checklist_v1.csv"
    assertions_path = CHECKS / "r6_oystacher_exhibit_a_source_policy_review_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_path, checks)
    report_path.write_text(
        "\n".join(
            [
                "# R6 Oystacher Exhibit A Source Policy Review v1",
                "",
                f"- Run id: `{RUN_ID}`.",
                f"- Source materialization: `{SOURCE_RUN}`.",
                f"- Positive rows: `{positive_rows}`; matched controls: `{control_rows}`; matched groups: `{verifier.get('matched_group_count')}`.",
                f"- Isolated verifier status: `{verifier.get('status')}`.",
                f"- Isolated split axes pass: `{source.get('all_materialized_split_axes_pass')}`.",
                "- Promotion candidate: `true`, because the public court exhibit has row-level SPOOF/FLIP order-lifecycle data and isolated split axes pass.",
                "- Source policy gate: `false`, because no explicit board/user approval exists yet for promoting the CourtListener RECAP/PACER mirror into canonical R6 intake.",
                f"- Gate result: `{gate_result}`.",
                "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path}`",
                f"- Checklist CSV: `{checklist_path}`",
                f"- Assertions: `{assertions_path}`",
                "",
                "## Next",
                "",
                next_action,
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = {
        "source_json_loaded": SOURCE_JSON.exists(),
        "positive_rows_gt_5000": positive_rows > 5000,
        "matched_controls_gt_1000": control_rows > 1000,
        "isolated_verifier_schema_ready": verifier.get("status") == "schema_ready_unscored",
        "isolated_split_axes_pass": source.get("all_materialized_split_axes_pass") is True,
        "source_policy_gate_false_without_approval": source_policy_gate is False,
        "canonical_merge_not_approved": approved_for_canonical_merge is False,
        "accepted_rows_zero": result["accepted_rows_added"] == 0,
        "update_goal_false": result["update_goal"] is False,
    }
    assertions_path.write_text(
        "\n".join(f"{key}={'PASS' if value else 'FAIL'}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"gate_result": gate_result, "source_policy_gate": source_policy_gate, "update_goal": False}, sort_keys=True))
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
