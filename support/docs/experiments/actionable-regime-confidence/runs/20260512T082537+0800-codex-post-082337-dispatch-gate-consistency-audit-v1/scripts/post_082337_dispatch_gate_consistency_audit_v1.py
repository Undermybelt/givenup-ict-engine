#!/usr/bin/env python3
"""Fail-close audit for the post-081705 dispatch-gate readback."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T082537+0800-codex-post-082337-dispatch-gate-consistency-audit-v1"
GATE = "post_082337_dispatch_gate_consistency_audit_v1=contradictory_unlock_flags_fail_closed_no_promotion"

REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "post-082337-dispatch-gate-consistency-audit-v1"
CHECK_DIR = RUN_ROOT / "checks"

SOURCE_082337 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T082337+0800-codex-post-081705-required-root-dispatch-gate-v1/command_output.json"
ASSERT_082314 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T082314+0800-codex-source-control-arrival-poll-after-081705-v1/checks/source_control_arrival_poll_after_081705_v1_assertions.out"


def parse_assertions(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    source = json.loads(SOURCE_082337.read_text(encoding="utf-8"))
    prior = parse_assertions(ASSERT_082314)

    contradictions = []
    if source.get("gate_result", "").endswith("no_required_root_or_dispatch_unlock"):
        for key in ("valid_required_root_unlock", "source_control_evidence_acquired", "r3_native_subhour_unlock"):
            if source.get(key) is True:
                contradictions.append(f"082337_{key}_true_under_no_unlock_gate")
    if prior.get("valid_required_root_unlock") == "false" and source.get("valid_required_root_unlock") is True:
        contradictions.append("082337_valid_required_root_unlock_conflicts_with_082314")
    if prior.get("source_control_evidence_acquired") == "false" and source.get("source_control_evidence_acquired") is True:
        contradictions.append("082337_source_control_evidence_conflicts_with_082314")
    if source.get("local_dispatch_probe", {}).get("external_requests_sent") is False:
        if source.get("local_dispatch_probe", {}).get("approved_operator_dispatch_path") is False:
            contradictions.append("dispatch_not_sent_and_no_approved_operator_path")
    if any(d.get("status") == "draft_missing" for d in source.get("dispatch_drafts", [])):
        contradictions.append("owner_export_dispatch_drafts_missing_in_082337_readback")

    rows = [
        {
            "check": "082337_gate_result",
            "value": source.get("gate_result", ""),
            "status": "fail_closed",
        },
        {
            "check": "082337_valid_required_root_unlock_raw",
            "value": str(source.get("valid_required_root_unlock")).lower(),
            "status": "contradictory_raw_flag",
        },
        {
            "check": "082337_source_control_evidence_raw",
            "value": str(source.get("source_control_evidence_acquired")).lower(),
            "status": "contradictory_raw_flag",
        },
        {
            "check": "082314_valid_required_root_unlock",
            "value": prior.get("valid_required_root_unlock", "missing"),
            "status": "controlling_prior_arrival_poll",
        },
        {
            "check": "082314_source_control_evidence_acquired",
            "value": prior.get("source_control_evidence_acquired", "missing"),
            "status": "controlling_prior_arrival_poll",
        },
        {
            "check": "accepted_rows_added",
            "value": "0",
            "status": "fail_closed",
        },
    ]

    summary = {
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate_result": GATE,
        "source_082337": str(SOURCE_082337.relative_to(REPO)),
        "source_082314_assertions": str(ASSERT_082314.relative_to(REPO)),
        "contradictions": contradictions,
        "raw_082337_gate_result": source.get("gate_result", ""),
        "raw_082337_valid_required_root_unlock": source.get("valid_required_root_unlock"),
        "raw_082337_source_control_evidence_acquired": source.get("source_control_evidence_acquired"),
        "raw_082337_r3_native_subhour_unlock": source.get("r3_native_subhour_unlock"),
        "prior_082314_valid_required_root_unlock": prior.get("valid_required_root_unlock"),
        "prior_082314_source_control_evidence_acquired": prior.get("source_control_evidence_acquired"),
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": False,
        "r5_recency_unlock": False,
        "r3_native_subhour_unlock": False,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    (OUT_DIR / "post_082337_dispatch_gate_consistency_audit_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with (OUT_DIR / "post_082337_dispatch_gate_consistency_audit_v1.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["check", "value", "status"])
        writer.writeheader()
        writer.writerows(rows)

    contradiction_lines = "\n".join(f"- `{item}`" for item in contradictions) or "- `none`"
    report = f"""# Post-082337 Dispatch Gate Consistency Audit v1

Run id: `{RUN_ID}`

Gate result: `{GATE}`

## Scope

Read-only consistency audit for `082337` after its command output reported a
`no_required_root_or_dispatch_unlock` gate while also setting raw unlock booleans
to true. This audit does not mutate target roots, approve R3/R5/R6 evidence,
send owner-export requests, run direct verifier, split calibration, canonical
merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking,
execution-tree promotion, make a trade claim, or call `update_goal`.

## Contradictions

{contradiction_lines}

## Decision

Treat `082337` as fail-closed diagnostic output only. File presence under the R3
native-subhour root does not satisfy Board A's accepted source/control contract,
and `082314` remains the controlling local arrival-poll readback for this slice:
valid required-root unlock false and source/control evidence acquired false.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false;
R3 native-subhour unlock false; valid required-root unlock false; source/control
evidence acquired false; canonical merge false; selected-data AutoQuant promotion
false; downstream promotion rerun false; strict full objective false; trade usable
false; promotion allowed false; `update_goal=false`.

## Next

Continue source/control acquisition only. Use an approved operator path for owner
exports, explicit same-exhibit `FLIP` control approval, or verifier-native R6/R5/R3
source/control roots before any canonical merge or downstream promotion rerun.
"""
    (OUT_DIR / "post_082337_dispatch_gate_consistency_audit_v1.md").write_text(report, encoding="utf-8")

    assertion_lines = [
        f"gate_result={GATE}",
        f"contradictions={len(contradictions)}",
        "accepted_rows_added=0",
        "r6_owner_export_unlock=false",
        "r5_recency_unlock=false",
        "r3_native_subhour_unlock=false",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "post_082337_dispatch_gate_consistency_audit_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n",
        encoding="utf-8",
    )
    print("\n".join(assertion_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
