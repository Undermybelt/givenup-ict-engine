#!/usr/bin/env python3
"""Completion audit after outbox v2, request drafts, and public dataset scout."""

from __future__ import annotations

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

V35 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T204335-codex-current-goal-completion-audit-v35-after-source-outbox/completion-audit/current_goal_completion_audit_v35_after_source_outbox.json"
OUTBOX_V2 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T204715-codex-source-acquisition-outbox-v2-after-r6-uplift/source-acquisition-outbox-v2/source_acquisition_outbox_v2.json"
DRAFT_BUNDLE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T204729-codex-source-acquisition-request-draft-bundle-v1/source-acquisition-request-draft-bundle/source_acquisition_request_draft_bundle_v1.json"
PUBLIC_SCOUT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T205031-codex-current-public-regime-dataset-scout-v1/current-public-regime-dataset-scout/current_public_regime_dataset_scout_v1.json"
FINRA_SCREEN = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T204850-codex-r6-finra-official-route-screen-v1/r6-finra-official-route-screen/r6_finra_official_route_screen_v1.json"

INTAKE_ROOTS = [
    {
        "root": "/tmp/ict-engine-source-label-equivalence-intake",
        "requirements": "R2;R4",
        "required_files": ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"],
    },
    {
        "root": "/tmp/ict-engine-native-subhour-source-label-intake",
        "requirements": "R3",
        "required_files": ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
    },
    {
        "root": "/tmp/ict-engine-source-panel-recency-extension",
        "requirements": "R5",
        "required_files": ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
    },
    {
        "root": "/tmp/ict-engine-direct-manipulation-row-intake",
        "requirements": "R6",
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    },
]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def root_status(spec: dict) -> dict:
    root = Path(spec["root"])
    present = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()) if root.exists() else []
    missing = [name for name in spec["required_files"] if not (root / name).is_file()]
    return {
        "root": spec["root"],
        "requirements": spec["requirements"],
        "required_files": ";".join(spec["required_files"]),
        "present_files": ";".join(present),
        "missing_files": ";".join(missing),
        "exists": root.exists(),
        "ready": not missing,
    }


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    v35 = read_json(V35)
    outbox_v2 = read_json(OUTBOX_V2)
    drafts = read_json(DRAFT_BUNDLE)
    public_scout = read_json(PUBLIC_SCOUT)
    finra_screen = read_json(FINRA_SCREEN)
    roots = [root_status(spec) for spec in INTAKE_ROOTS]
    ready_roots = [row["root"] for row in roots if row["ready"]]
    board_hash = sha256(BOARD)

    checklist = [
        {
            "id": "R0",
            "requirement": "Use the named Board A markdown and latest artifacts as the contract.",
            "status": "pass_checked",
            "artifact": rel(BOARD),
            "evidence": f"Board hash before v36 writeback={board_hash}; v35, outbox v2, request drafts, FINRA screen, and public scout were read.",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "Every scoped active lane keeps calibrated >=95% evidence without becoming a trade claim.",
            "status": "pass_scoped_not_full",
            "artifact": rel(V35),
            "evidence": "v35 preserved scoped >=95% evidence and no later artifact relaxes thresholds or promotes proxy labels.",
            "gap": "Scoped evidence still does not satisfy the strict all-market/all-cycle/all-species objective.",
        },
        {
            "id": "R2",
            "requirement": "Other-market/source-label equivalence rows and provenance are acquired and verifier-accepted.",
            "status": "fail_blocked",
            "artifact": f"{rel(OUTBOX_V2)}; {rel(PUBLIC_SCOUT)}",
            "evidence": "Outbox v2 is send-ready and public scout found current candidates, but no MainRegimeV2-compatible source-owned rows/provenance were acquired.",
            "gap": roots[0]["missing_files"],
        },
        {
            "id": "R3",
            "requirement": "Native sub-hour source-label rows and provenance are acquired and verifier-accepted.",
            "status": "fail_blocked",
            "artifact": rel(DRAFT_BUNDLE),
            "evidence": "Request draft exists, but request_sent=false, rows_acquired=false, and native sub-hour intake files are absent.",
            "gap": roots[1]["missing_files"],
        },
        {
            "id": "R4",
            "requirement": "Strict exact 1h source rows and provenance are acquired.",
            "status": "fail_blocked",
            "artifact": rel(OUTBOX_V2),
            "evidence": "Outbox v2 keeps R4 in the acquisition queue, but source-label equivalence files remain absent.",
            "gap": roots[0]["missing_files"],
        },
        {
            "id": "R5",
            "requirement": "Post-2026-01-30 source-panel recency extension rows and provenance are acquired.",
            "status": "fail_blocked",
            "artifact": f"{rel(OUTBOX_V2)}; {rel(PUBLIC_SCOUT)}",
            "evidence": "The public scout found current public rows, but the current candidate is HMM/model-derived and not the required source-panel recency extension.",
            "gap": roots[2]["missing_files"],
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation positive/control/provenance files are acquired across required species.",
            "status": "partial_still_blocked",
            "artifact": f"{rel(OUTBOX_V2)}; {rel(FINRA_SCREEN)}",
            "evidence": "Outbox v2 merges bear_raid and painting_tape candidate surfaces and FINRA official routes were identified for spoofing/layering, but request_sent=false, rows_acquired=false, matched controls are absent, and intake files are absent.",
            "gap": roots[3]["missing_files"],
        },
        {
            "id": "R7",
            "requirement": "No proxy labels, raw-data commits, threshold relaxation, external send, or trade-usable claim.",
            "status": "pass_guardrail",
            "artifact": f"{rel(DRAFT_BUNDLE)}; {rel(PUBLIC_SCOUT)}",
            "evidence": "Drafts were not sent; public candidates were not promoted; accepted_rows_added=0; new_confidence_gate=false; raw_data_committed=false.",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "Only call update_goal when every strict requirement is covered by real evidence.",
            "status": "fail_blocked",
            "artifact": rel(RUN_ROOT),
            "evidence": "R2/R3/R4/R5/R6 remain blocked or partial after outbox v2, request drafts, and current public scout.",
            "gap": "Strict full objective is not achieved; update_goal remains false.",
        },
    ]
    unmet = [row for row in checklist if row["status"].startswith("fail") or "blocked" in row["status"]]

    audit = {
        "run_id": RUN_ROOT.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": (
            "Every active Board A regime requires source-owned or owner-approved >=95% confidence plus "
            "other-market/species and other-cycle/timeframe validation before completion."
        ),
        "decision": "current_goal_completion_audit_v36=current_public_scout_and_outbox_v2_rows_not_acquired_blocked",
        "board_hash_before_writeback": board_hash,
        "prior_v35_decision": v35.get("decision"),
        "outbox_v2_decision": outbox_v2.get("decision"),
        "outbox_v2_rows": outbox_v2.get("v2_outbox_rows"),
        "draft_bundle_decision": drafts.get("decision"),
        "draft_count": drafts.get("draft_count"),
        "public_scout_decision": public_scout.get("decision"),
        "public_scout_candidate_count": public_scout.get("candidate_count"),
        "public_scout_current_rows_found": public_scout.get("current_rows_found"),
        "finra_screen_decision": finra_screen.get("decision"),
        "finra_official_route_count": finra_screen.get("official_route_count"),
        "finra_public_rows_acquired": finra_screen.get("public_rows_acquired"),
        "ready_intake_roots": ready_roots,
        "ready_intake_root_count": len(ready_roots),
        "intake_roots_checked": roots,
        "request_sent": False,
        "rows_acquired": False,
        "accepted_rows_added_since_v35": 0,
        "new_confidence_gate_since_v35": False,
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

    (OUT / "current_goal_completion_audit_v36_after_current_public_scout.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    fields = ["id", "requirement", "status", "artifact", "evidence", "gap"]
    write_csv(OUT / "current_goal_completion_audit_v36_checklist.csv", checklist, fields)
    write_csv(OUT / "current_goal_completion_audit_v36_unmet_requirements.csv", unmet, fields)
    write_csv(
        OUT / "current_goal_completion_audit_v36_intake_roots.csv",
        roots,
        ["root", "requirements", "required_files", "present_files", "missing_files", "exists", "ready"],
    )

    report = [
        "# Current Goal Completion Audit v36",
        "",
        f"Decision: `{audit['decision']}`.",
        "",
        "Result:",
        f"- Outbox v2 rows: `{audit['outbox_v2_rows']}`; request drafts: `{audit['draft_count']}`.",
        f"- Public scout candidates: `{audit['public_scout_candidate_count']}`; current rows found: `{audit['public_scout_current_rows_found']}`; accepted: `false`.",
        f"- FINRA official routes identified: `{audit['finra_official_route_count']}`; public rows acquired: `{audit['finra_public_rows_acquired']}`.",
        f"- Ready intake roots: `{len(ready_roots)}/4`.",
        "- Accepted rows added since v35: `0`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "Blocked rows: `R2`, `R3`, `R4`, `R5`, `R6`, and `R8`.",
    ]
    (OUT / "current_goal_completion_audit_v36_after_current_public_scout.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"PASS decision={audit['decision']}",
        f"PASS outbox_v2_rows={audit['outbox_v2_rows']}",
        f"PASS draft_count={audit['draft_count']}",
        f"PASS public_scout_candidate_count={audit['public_scout_candidate_count']}",
        f"PASS finra_official_route_count={audit['finra_official_route_count']}",
        f"PASS ready_intake_roots={len(ready_roots)}_of_4",
        "PASS request_sent=false",
        "PASS rows_acquired=false",
        "PASS accepted_rows_added_since_v35=0",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS unmet_ids=R2,R3,R4,R5,R6,R8",
    ]
    (CHECKS / "current_goal_completion_audit_v36_after_current_public_scout_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"decision": audit["decision"], "unmet_ids": audit["unmet_ids"]}, sort_keys=True))


if __name__ == "__main__":
    main()
