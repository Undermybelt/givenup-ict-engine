#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / "Cargo.toml").exists() and (path / "docs/plans").exists():
            return path
    raise RuntimeError(f"repo root not found from {start}")


REPO = find_repo_root(Path(__file__).resolve())
RUN_ID = "20260512T061356+0800-codex-current-objective-audit-after-061229-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
ARTIFACT_DIR = RUN_ROOT / "current-objective-audit-after-061229-v1"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

REQUIRED_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]
NON_TARGET_EQUIVALENCE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")

EVIDENCE = {
    "hgb_field_materialization": "docs/experiments/actionable-regime-confidence/runs/20260512T053852-codex-hgb-per-regime-field-materialization-v1",
    "hgb_aggregate_readback": "docs/experiments/actionable-regime-confidence/runs/20260512T055058-codex-hgb-aggregate-field-readback-v1",
    "provider_autoquant_cache": "docs/experiments/actionable-regime-confidence/runs/20260512T060056-codex-autoquant-local-cache-isolated-backtest-after-055200-v1",
    "source_arrival_sweep": "docs/experiments/actionable-regime-confidence/runs/20260512T060446-codex-source-arrival-local-drop-sweep-after-055930-v1",
    "route_contact_recency": "docs/experiments/actionable-regime-confidence/runs/20260512T060807-codex-r6-owner-route-public-contact-recency-check-v1",
    "source_label_equivalence_verifier": "docs/experiments/actionable-regime-confidence/runs/20260512T061229+0800-codex-source-label-equivalence-current-verifier-v1",
    "operator_dispatch_handoff": "docs/experiments/actionable-regime-confidence/runs/20260512T061314+0800-codex-r6-v5-operator-dispatch-handoff-after-060807-v1",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def exists_rel(rel: str) -> bool:
    return (REPO / rel).exists()


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    required_roots = {str(root): root.exists() for root in REQUIRED_ROOTS}
    evidence_exists = {name: exists_rel(path) for name, path in EVIDENCE.items()}

    checklist = [
        {
            "requirement": "Each active regime has diagnostic >=95 confidence evidence with per-regime fields",
            "evidence": "053852 plus 055058 HGB field/readback packets",
            "status": "diagnostic_only",
            "gap": "daily/source-label-equivalence context is not source/control promotion evidence",
        },
        {
            "requirement": "Validate across other markets, periods, and timeframes",
            "evidence": "061229 current source-label-equivalence verifier",
            "status": "blocked",
            "gap": "schema_ready_unscored; verifier says to rerun unchanged chronological and heldout-market/timeframe gates",
        },
        {
            "requirement": "Acquire source/control evidence or explicit approval before promotion",
            "evidence": "060446 source-arrival sweep, 060807 route check, 061314 dispatch handoff",
            "status": "missing",
            "gap": "no approval, no sent export response, no verifier-native R6 rows, no target root",
        },
        {
            "requirement": "Unlock one required target root",
            "evidence": "live filesystem root check",
            "status": "missing",
            "gap": "R6 owner export, R3 native sub-hour, and R5 recency-extension roots are absent",
        },
        {
            "requirement": "Run canonical merge after source/control unlock",
            "evidence": "board and recent audit assertions",
            "status": "not_allowed",
            "gap": "no required root or approval exists, so canonical merge remains false",
        },
        {
            "requirement": "Run provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree after merge",
            "evidence": "060056 local AutoQuant cache readback and older downstream readbacks",
            "status": "not_allowed",
            "gap": "post-unlock downstream promotion rerun has not occurred and must not run from proxy evidence",
        },
        {
            "requirement": "Do not claim tradable strategy or call update_goal until complete",
            "evidence": "all recent gates have trade_usable=false and update_goal=false",
            "status": "blocked",
            "gap": "strict full objective remains incomplete",
        },
    ]

    missing_count = sum(1 for row in checklist if row["status"] in {"missing", "blocked", "not_allowed"})
    decision = {
        "objective_complete": False,
        "missing_requirement_count": missing_count,
        "diagnostic_confidence_present": evidence_exists["hgb_field_materialization"] and evidence_exists["hgb_aggregate_readback"],
        "required_roots": required_roots,
        "required_roots_absent": not any(required_roots.values()),
        "non_target_equivalence_root_present": NON_TARGET_EQUIVALENCE_ROOT.exists(),
        "source_control_evidence_acquired": False,
        "approval_present": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    gate_result = "current_objective_audit_after_061229_v1=not_complete_equivalence_schema_ready_unscored_required_roots_absent_no_downstream_rerun"
    packet = {
        "run_id": RUN_ID,
        "generated_at_epoch": int(time.time()),
        "board_sha256_before_artifact": sha256(BOARD),
        "gate_result": gate_result,
        "objective": "Every active regime must reach 95% calibrated confidence across markets/periods/timeframes, then pass the ordered provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain after source/control unlock.",
        "evidence_exists": evidence_exists,
        "checklist": checklist,
        "decision": decision,
        "next_action": "Use approved operator dispatch or source/control approval to unlock R6, or acquire R3 native sub-hour/R5 recency source rows; only then rerun direct verifier, split calibration, canonical merge, providers, AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback.",
    }

    json_path = ARTIFACT_DIR / "current_objective_audit_after_061229_v1.json"
    csv_path = ARTIFACT_DIR / "prompt_to_artifact_checklist_after_061229_v1.csv"
    md_path = ARTIFACT_DIR / "current_objective_audit_after_061229_v1.md"
    checks_path = CHECK_DIR / "current_objective_audit_after_061229_v1_assertions.out"

    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["requirement", "evidence", "status", "gap"])
        writer.writeheader()
        writer.writerows(checklist)

    md_lines = [
        "# Current Objective Audit After 061229 v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Gate result: `{gate_result}`",
        f"Board hash before artifact: `{packet['board_sha256_before_artifact']}`",
        "",
        "## Objective Restatement",
        "",
        packet["objective"],
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| requirement | evidence | status | gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        md_lines.append(f"| {row['requirement']} | {row['evidence']} | {row['status']} | {row['gap']} |")
    md_lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Objective complete: `{decision['objective_complete']}`.",
            f"- Missing requirement count: `{decision['missing_requirement_count']}`.",
            f"- Required roots: `{decision['required_roots']}`.",
            f"- Non-target equivalence root present: `{decision['non_target_equivalence_root_present']}`.",
            "- The equivalence verifier is schema-ready but unscored; schema readiness is not confidence acceptance.",
            "- No source/control approval, canonical merge, or downstream promotion rerun exists.",
            "- `trade_usable=false`; `update_goal=false`.",
            "",
            "## Next",
            "",
            packet["next_action"],
        ]
    )
    md_path.write_text("\n".join(md_lines) + "\n")

    checks = [
        ("gate_result", packet["gate_result"] == gate_result),
        ("objective_complete_false", decision["objective_complete"] is False),
        ("required_roots_absent", decision["required_roots_absent"] is True),
        ("source_control_evidence_acquired_false", decision["source_control_evidence_acquired"] is False),
        ("canonical_merge_false", decision["canonical_merge"] is False),
        ("downstream_promotion_rerun_false", decision["downstream_promotion_rerun"] is False),
        ("trade_usable_false", decision["trade_usable"] is False),
        ("update_goal_false", decision["update_goal"] is False),
    ]
    checks_path.write_text("\n".join(f"{name}={'PASS' if ok else 'FAIL'}" for name, ok in checks) + "\n")
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
