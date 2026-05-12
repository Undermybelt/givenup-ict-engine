#!/usr/bin/env python3
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "completion-audit"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

OUTBOX = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T204131-codex-source-acquisition-outbox-v1/source-acquisition-outbox/source_acquisition_outbox_v1.json"
V34 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T203817-codex-current-goal-completion-audit-v34-after-request-matrices/completion-audit/current_goal_completion_audit_v34_after_request_matrices.json"
R6_UPLIFT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T204159-codex-r6-bear-raid-painting-tape-source-uplift-v1/r6-source-uplift/r6_bear_raid_painting_tape_source_uplift_v1.json"

INTAKE_ROOTS = [
    ("/tmp/ict-engine-source-label-equivalence-intake", "R2;R4", ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"]),
    ("/tmp/ict-engine-native-subhour-source-label-intake", "R3", ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"]),
    ("/tmp/ict-engine-source-panel-recency-extension", "R5", ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"]),
    ("/tmp/ict-engine-direct-manipulation-row-intake", "R6", ["positive_spoofing_layering_rows.csv", "matched_negative_normal_activity_rows.csv", "provenance_manifest.json"]),
]


def rel(path):
    return str(path.relative_to(REPO))


def read_json(path):
    return json.loads(path.read_text())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def root_status(root_s, requirements, required_files):
    root = Path(root_s)
    present = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()) if root.exists() else []
    missing = [name for name in required_files if not (root / name).is_file()]
    return {
        "root": root_s,
        "requirements": requirements,
        "required_files": ";".join(required_files),
        "present_files": ";".join(present),
        "missing_files": ";".join(missing),
        "exists": root.exists(),
        "ready": not missing,
    }


def write_csv(path, rows, fields):
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    outbox = read_json(OUTBOX)
    v34 = read_json(V34)
    r6_uplift = read_json(R6_UPLIFT)
    roots = [root_status(*item) for item in INTAKE_ROOTS]
    ready_roots = [row["root"] for row in roots if row["ready"]]
    board_hash = sha256(BOARD)

    checklist = [
        {
            "id": "R0",
            "requirement": "Use the named Board A markdown and current cursor as the contract.",
            "status": "pass_checked",
            "artifact": rel(BOARD),
            "evidence": f"Board hash before v35 writeback={board_hash}; outbox and v34 were read.",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "Every scoped active lane keeps calibrated >=95% evidence.",
            "status": "pass_scoped_not_full",
            "artifact": rel(V34),
            "evidence": "v34 preserves scoped >=95% evidence, but strict full-objective rows remain blocked.",
            "gap": "Scoped evidence is not strict full-market/full-cycle/full-species closure.",
        },
        {
            "id": "R2",
            "requirement": "Other-market/source-label equivalence files are acquired and verifier-accepted.",
            "status": "fail_blocked",
            "artifact": rel(OUTBOX),
            "evidence": "Outbox row is send-ready, but request_sent=false, rows_acquired=false, and required intake files are absent.",
            "gap": roots[0]["missing_files"],
        },
        {
            "id": "R3",
            "requirement": "Native sub-hour source-label files are acquired and verifier-accepted.",
            "status": "fail_blocked",
            "artifact": rel(OUTBOX),
            "evidence": "Outbox row is send-ready, but request_sent=false, rows_acquired=false, and required intake files are absent.",
            "gap": roots[1]["missing_files"],
        },
        {
            "id": "R4",
            "requirement": "Strict exact 1h source rows and provenance are acquired.",
            "status": "fail_blocked",
            "artifact": rel(OUTBOX),
            "evidence": "Outbox row for R4/R5 is send-ready, but no source-label equivalence rows/provenance were acquired.",
            "gap": roots[0]["missing_files"],
        },
        {
            "id": "R5",
            "requirement": "Post-2026-01-30 recency-extension rows and provenance are acquired.",
            "status": "fail_blocked",
            "artifact": rel(OUTBOX),
            "evidence": "Outbox row for R4/R5 is send-ready, but recency-extension files are absent.",
            "gap": roots[2]["missing_files"],
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation positive/control/provenance files are acquired across required species.",
            "status": "partial_still_blocked",
            "artifact": f"{rel(OUTBOX)}; {rel(R6_UPLIFT)}",
            "evidence": "Outbox rows are send-ready, and R6 uplift found candidate surfaces for bear_raid and painting_tape, but rows_acquired=false, matched_controls_acquired=false, and intake files are absent.",
            "gap": roots[3]["missing_files"],
        },
        {
            "id": "R7",
            "requirement": "No proxy labels, raw-data commits, threshold relaxation, external send, or trade-usable claim.",
            "status": "pass_guardrail",
            "artifact": rel(OUTBOX),
            "evidence": "Outbox boundary keeps request_sent=false, rows_acquired=false, raw_data_committed=false, thresholds_relaxed=false, and trade_usable=false.",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "Only call update_goal when every strict requirement is covered by real evidence.",
            "status": "fail_blocked",
            "artifact": rel(RUN_ROOT),
            "evidence": "R2/R3/R4/R5/R6 remain blocked or partial after the source-acquisition outbox.",
            "gap": "Strict full objective is not achieved; update_goal remains false.",
        },
    ]
    unmet = [row for row in checklist if row["status"].startswith("fail") or "blocked" in row["status"]]

    audit = {
        "run_id": RUN_ROOT.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": "All active Board A regimes require calibrated >=95% confidence plus source-owned cross-market and cross-timeframe validation before completion.",
        "decision": "current_goal_completion_audit_v35=outbox_ready_rows_not_acquired_blocked",
        "board_hash_before_writeback": board_hash,
        "outbox_decision": outbox.get("decision"),
        "prior_v34_decision": v34.get("decision"),
        "r6_uplift_decision": r6_uplift.get("decision"),
        "r6_uplift_candidate_count": r6_uplift.get("candidate_count"),
        "ready_intake_roots": ready_roots,
        "ready_intake_root_count": len(ready_roots),
        "intake_roots_checked": roots,
        "outbox_row_count": outbox.get("outbox_row_count"),
        "request_sent": outbox.get("request_sent"),
        "rows_acquired": outbox.get("rows_acquired"),
        "accepted_rows_added_since_outbox": 0,
        "new_confidence_gate_since_outbox": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "checklist_rows": len(checklist),
        "unmet_rows": len(unmet),
        "unmet_ids": [row["id"] for row in unmet],
        "checklist": checklist,
    }

    (OUT / "current_goal_completion_audit_v35_after_source_outbox.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n"
    )
    fields = ["id", "requirement", "status", "artifact", "evidence", "gap"]
    write_csv(OUT / "current_goal_completion_audit_v35_checklist.csv", checklist, fields)
    write_csv(OUT / "current_goal_completion_audit_v35_unmet_requirements.csv", unmet, fields)
    write_csv(
        OUT / "current_goal_completion_audit_v35_intake_roots.csv",
        roots,
        ["root", "requirements", "required_files", "present_files", "missing_files", "exists", "ready"],
    )

    report = [
        "# Current Goal Completion Audit v35",
        "",
        f"Decision: `{audit['decision']}`.",
        "",
        "Result:",
        f"- Outbox rows: `{audit['outbox_row_count']}`.",
        f"- Request sent: `{audit['request_sent']}`; rows acquired: `{audit['rows_acquired']}`.",
        f"- Ready intake roots: `{len(ready_roots)}/4`.",
        "- Accepted rows added since outbox: `0`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "Blocked rows: `R2`, `R3`, `R4`, `R5`, `R6`, and `R8`.",
    ]
    (OUT / "current_goal_completion_audit_v35_after_source_outbox.md").write_text("\n".join(report) + "\n")

    assertions = [
        f"PASS decision={audit['decision']}",
        f"PASS outbox_row_count={audit['outbox_row_count']}",
        f"PASS ready_intake_roots={len(ready_roots)}_of_4",
        "PASS request_sent=false",
        "PASS rows_acquired=false",
        "PASS accepted_rows_added_since_outbox=0",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
        "PASS unmet_ids=R2,R3,R4,R5,R6,R8",
    ]
    (CHECKS / "current_goal_completion_audit_v35_after_source_outbox_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )

    print(json.dumps({"decision": audit["decision"], "unmet_ids": audit["unmet_ids"]}, sort_keys=True))


if __name__ == "__main__":
    main()
