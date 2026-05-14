#!/usr/bin/env python3
"""Policy review for the isolated Oystacher Exhibit A materialization."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T003334-codex-r6-oystacher-exhibit-a-policy-review-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r6-oystacher-exhibit-a-policy-review"
CHECKS = RUN_ROOT / "checks"
SOURCE_RUN = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/"
    / "r6-oystacher-exhibit-a-row-materialization"
)
POSITIVE = SOURCE_RUN / "isolated-oystacher-exhibit-a-intake/positive_spoofing_layering_rows.csv"
NEGATIVE = SOURCE_RUN / "isolated-oystacher-exhibit-a-intake/matched_negative_normal_activity_rows.csv"
PARSED = SOURCE_RUN / "oystacher_exhibit_a_parsed_order_rows_v1.csv"
SPLITS = SOURCE_RUN / "oystacher_exhibit_a_split_metrics_v1.csv"
MATERIALIZATION_JSON = SOURCE_RUN / "r6_oystacher_exhibit_a_row_materialization_v1.json"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    positives = read_rows(POSITIVE)
    negatives = read_rows(NEGATIVE)
    parsed = read_rows(PARSED)
    split_rows = read_rows(SPLITS)
    materialization = json.loads(MATERIALIZATION_JSON.read_text(encoding="utf-8"))

    parsed_side_counts = Counter(row.get("side_type", "") for row in parsed)
    negative_activity_counts = Counter(
        "flip_marked_same_exhibit"
        if "marks this row as FLIP" in row.get("activity_description", "")
        else "other"
        for row in negatives
    )
    negative_labels = Counter(row.get("label", "") for row in negatives)
    positive_labels = Counter(row.get("label", "") for row in positives)
    min_split_lcb = min(float(row["min_wilson95_lcb"]) for row in split_rows)
    split_axes_pass = all(row.get("pooled95_pass") == "True" for row in split_rows)

    policy_checks = [
        {
            "check": "public_recapped_court_exhibit_positive_source",
            "status": "pass_for_positive_candidate",
            "reason": "CourtListener/RECAP PDF is a public copy of court-filed CFTC Exhibit A and the parsed rows carry source labels marked SPOOF.",
        },
        {
            "check": "spoof_rows_source_owned_positive_label",
            "status": "pass_for_positive_candidate",
            "reason": f"Positive candidate rows={len(positives)} and labels={dict(positive_labels)}.",
        },
        {
            "check": "flip_rows_are_normal_matched_controls",
            "status": "fail_current_contract",
            "reason": "Rows marked FLIP in the same CFTC exhibit are counterpart legs in the alleged flip sequence, not source-owned normal/non-manipulation controls.",
        },
        {
            "check": "canonical_merge_without_approval",
            "status": "fail_closed",
            "reason": "Existing R6 verifier contract calls the negative file matched_negative_normal_activity_rows.csv; same-exhibit FLIP rows require explicit policy approval or a separate control taxonomy before promotion.",
        },
    ]
    gate_result = (
        "r6_oystacher_exhibit_a_policy_review_v1="
        "positive_source_passed_flip_controls_rejected_no_canonical_merge"
    )
    decision = {
        "gate_result": gate_result,
        "public_recapped_court_exhibit_positive_source_ok": True,
        "spoof_rows_can_be_positive_candidates": True,
        "flip_rows_accepted_as_matched_normal_controls": False,
        "canonical_live_intake_merge_approved": False,
        "rerun_downstream_chain": False,
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
    }
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_materialization": str(MATERIALIZATION_JSON.relative_to(REPO)),
        "source_materialization_gate": materialization.get("decision", {}).get("gate_result"),
        "row_counts": {
            "parsed_order_rows": len(parsed),
            "parsed_side_counts": dict(parsed_side_counts),
            "positive_candidates": len(positives),
            "flip_control_candidates": len(negatives),
            "positive_label_counts": dict(positive_labels),
            "negative_label_counts": dict(negative_labels),
            "negative_activity_counts": dict(negative_activity_counts),
        },
        "split_readback": {
            "axis_rows": len(split_rows),
            "all_axes_pass_in_isolated_candidate": split_axes_pass,
            "min_split_wilson95_lcb": min_split_lcb,
            "split_metrics": str(SPLITS.relative_to(REPO)),
        },
        "policy_checks": policy_checks,
        "decision": decision,
        "next_action": (
            "Keep Oystacher Exhibit A rows isolated unless the user/owner explicitly approves "
            "same-exhibit FLIP rows as controls or supplies source-owned normal controls; after "
            "approval or new controls, merge through the verifier-native contract and rerun "
            "direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, "
            "CatBoost/path-ranking, and execution-tree readback while keeping R5 and R3 blocked."
        ),
    }

    json_path = OUT / "r6_oystacher_exhibit_a_policy_review_v1.json"
    report_path = OUT / "r6_oystacher_exhibit_a_policy_review_v1.md"
    checks_path = OUT / "r6_oystacher_exhibit_a_policy_checks_v1.csv"
    assertion_path = CHECKS / "r6_oystacher_exhibit_a_policy_review_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(checks_path, policy_checks, ["check", "status", "reason"])
    lines = [
        "# R6 Oystacher Exhibit A Policy Review v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Source materialization: `{result['source_materialization']}`.",
        f"- Parsed order rows: `{len(parsed)}`; side counts: `{dict(parsed_side_counts)}`.",
        f"- Positive SPOOF candidates: `{len(positives)}`.",
        f"- FLIP same-exhibit control candidates: `{len(negatives)}`.",
        f"- Isolated split axes pass: `{str(split_axes_pass).lower()}`; minimum split Wilson95 LCB: `{min_split_lcb}`.",
        f"- Gate result: `{gate_result}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Decision",
        "",
        "- Public RECAP/CourtListener Exhibit A is sufficient to preserve Oystacher `SPOOF` rows as positive candidates for policy review.",
        "- The same exhibit's `FLIP` rows are not accepted as `matched_negative_normal_activity` under the current R6 contract because they are sequence counterpart legs, not source-owned normal/non-manipulation controls.",
        "- Canonical intake merge and downstream rerun remain blocked unless the user/owner explicitly approves the FLIP-control contract or supplies source-owned normal controls.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Policy checks CSV: `{checks_path.relative_to(REPO)}`",
        f"- Assertions: `{assertion_path.relative_to(REPO)}`",
        "",
        "## Next",
        "",
        result["next_action"],
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    assertion_path.write_text(
        "\n".join(
            [
                f"gate_result={gate_result}",
                "public_recapped_court_exhibit_positive_source_ok=true",
                "spoof_rows_can_be_positive_candidates=true",
                "flip_rows_accepted_as_matched_normal_controls=false",
                "canonical_live_intake_merge_approved=false",
                "accepted_rows_added=0",
                "update_goal=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"gate_result": gate_result, "report": str(report_path.relative_to(REPO))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
