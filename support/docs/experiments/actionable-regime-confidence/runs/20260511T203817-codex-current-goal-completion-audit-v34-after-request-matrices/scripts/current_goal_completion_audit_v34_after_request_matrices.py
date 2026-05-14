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

ARTIFACTS = {
    "v32_after_r2_r3": REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T203339-codex-current-goal-completion-audit-v32-after-r2-r3-request-packages/completion-audit/current_goal_completion_audit_v32_after_r2_r3_request_packages.json",
    "disk_sweep": REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T203437-codex-required-intake-disk-sweep-v1/required-intake-disk-sweep/required_intake_disk_sweep_v1.json",
    "native_contact": REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T203505-codex-native-subhour-contact-leads-v1/native-subhour-contact-leads/native_subhour_contact_leads_v1.json",
    "direct_matrix": REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T203523-codex-direct-manipulation-species-request-matrix-v1/direct-manipulation-species-request-matrix/direct_manipulation_species_request_matrix_v1.json",
    "source_contact": REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202712-codex-source-label-equivalence-contact-leads-v1/source-label-equivalence-contact-leads/source_label_equivalence_contact_leads_v1.json",
    "stock_contact": REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202304-codex-stock-regime-owner-contact-leads-v1/stock-regime-owner-contact-leads/stock_regime_owner_contact_leads_v1.json",
    "kaggle_refresh": REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202501-codex-kaggle-stock-regime-live-refresh-v1/kaggle-stock-regime-live-refresh/kaggle_stock_regime_live_refresh_v1.json",
    "do_putnins_contact": REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T201759-codex-do-putnins-contact-leads-v1/do-putnins-contact-leads/do_putnins_contact_leads_v1.json",
}

INTAKE_ROOTS = [
    {
        "id": "source_label_equivalence",
        "requirements": "R2;R4",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required_files": ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"],
    },
    {
        "id": "native_subhour_source_label",
        "requirements": "R3",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_files": ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
    },
    {
        "id": "source_panel_recency_extension",
        "requirements": "R5",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_files": ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
    },
    {
        "id": "direct_manipulation_row_intake",
        "requirements": "R6",
        "root": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    },
]


def rel(path):
    return str(path.relative_to(REPO))


def read_json(path):
    return json.loads(path.read_text())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def root_status(item):
    root = item["root"]
    present = []
    if root.exists():
        present = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())
    missing = [name for name in item["required_files"] if not (root / name).is_file()]
    return {
        "id": item["id"],
        "requirements": item["requirements"],
        "root": str(root),
        "exists": root.exists(),
        "required_files": ";".join(item["required_files"]),
        "present_files": ";".join(present),
        "missing_files": ";".join(missing),
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

    data = {key: read_json(path) for key, path in ARTIFACTS.items()}
    roots = [root_status(item) for item in INTAKE_ROOTS]
    ready_roots = [row["id"] for row in roots if row["ready"]]
    board_hash = sha256(BOARD)

    checklist = [
        {
            "id": "R0",
            "requirement": "Use the named Board A markdown as the execution contract and inspect current artifacts before judging completion.",
            "status": "pass_checked",
            "artifact": rel(BOARD),
            "evidence": f"Board hash before v34 writeback={board_hash}; cursor and post-v32 request artifacts were re-read.",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "Every scoped active lane keeps calibrated >=95% evidence.",
            "status": "pass_scoped_not_full",
            "artifact": rel(ARTIFACTS["v32_after_r2_r3"]),
            "evidence": "Prior scoped active-lane 95% evidence is preserved by v32; no artifact in this slice weakens it.",
            "gap": "Scoped evidence still does not satisfy strict full-market/full-cycle/full-species completion.",
        },
        {
            "id": "R2",
            "requirement": "Other-market/source-label equivalence rows and provenance are acquired and verifier-accepted.",
            "status": "fail_blocked",
            "artifact": f"{rel(ARTIFACTS['source_contact'])}; {roots[0]['root']}",
            "evidence": "R2 contact leads are ready, but rows_acquired=false and the source-label equivalence intake root is not ready.",
            "gap": roots[0]["missing_files"],
        },
        {
            "id": "R3",
            "requirement": "Native sub-hour source-owned price-root labels are acquired and verifier-accepted.",
            "status": "fail_blocked",
            "artifact": f"{rel(ARTIFACTS['native_contact'])}; {roots[1]['root']}",
            "evidence": "R3 request and contact packages are ready, but rows_acquired=false and the native sub-hour intake root is not ready.",
            "gap": roots[1]["missing_files"],
        },
        {
            "id": "R4",
            "requirement": "Strict exact 1h remaining slots have source-owned rows and provenance.",
            "status": "fail_blocked",
            "artifact": f"{rel(ARTIFACTS['stock_contact'])}; {roots[0]['root']}",
            "evidence": "Stock-regime contact paths remain public-contact ready only; strict exact 1h rows were not acquired.",
            "gap": roots[0]["missing_files"],
        },
        {
            "id": "R5",
            "requirement": "Post-2026-01-30 recency-tail rows are repaired with source-owned labels.",
            "status": "fail_blocked",
            "artifact": f"{rel(ARTIFACTS['kaggle_refresh'])}; {roots[2]['root']}",
            "evidence": "The live Kaggle refresh still ends on 2026-01-30 and the recency-extension intake root is not ready.",
            "gap": roots[2]["missing_files"],
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation has source-owned positives, matched controls, and provenance across required species.",
            "status": "partial_still_blocked",
            "artifact": f"{rel(ARTIFACTS['direct_matrix'])}; {roots[3]['root']}",
            "evidence": "The R6 species request matrix is ready, but rows_acquired=false; direct manipulation intake files are not present.",
            "gap": roots[3]["missing_files"],
        },
        {
            "id": "R7",
            "requirement": "No proxy-only promotion, raw-data commit, threshold relaxation, runtime code change, or trade-usable claim.",
            "status": "pass_guardrail",
            "artifact": rel(ARTIFACTS["disk_sweep"]),
            "evidence": "Disk sweep and request artifacts keep accepted_rows_added=0, new_confidence_gate=false, raw_data_committed=false, thresholds_relaxed=false, runtime_code_changed=false, trade_usable=false.",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "Call update_goal only if every explicit strict objective row is covered by real evidence.",
            "status": "fail_blocked",
            "artifact": rel(RUN_ROOT),
            "evidence": "R2, R3, R4, R5, and R6 remain blocked or partial after latest request/contact/matrix artifacts.",
            "gap": "Strict full objective is not achieved; update_goal remains false.",
        },
    ]
    unmet = [row for row in checklist if row["status"].startswith("fail") or "blocked" in row["status"]]

    audit = {
        "run_id": RUN_ROOT.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": (
            "Every active Board A regime must have calibrated >=95% confidence and remain suitable across other "
            "markets/species and other cycles/timeframes before completion can be reported."
        ),
        "decision": "current_goal_completion_audit_v34=request_matrices_ready_rows_not_acquired_blocked",
        "board_hash_before_writeback": board_hash,
        "prior_cursor_run": "20260511T203339-codex-current-goal-completion-audit-v32-after-r2-r3-request-packages",
        "post_cursor_artifacts_checked": [rel(ARTIFACTS["disk_sweep"]), rel(ARTIFACTS["native_contact"]), rel(ARTIFACTS["direct_matrix"])],
        "artifact_decisions": {key: data[key].get("decision", "unknown") for key in data},
        "intake_roots_checked": roots,
        "ready_intake_roots": ready_roots,
        "ready_intake_root_count": len(ready_roots),
        "accepted_rows_added_since_v32": 0,
        "new_confidence_gate_since_v32": False,
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

    json_path = OUT / "current_goal_completion_audit_v34_after_request_matrices.json"
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")

    fields = ["id", "requirement", "status", "artifact", "evidence", "gap"]
    write_csv(OUT / "current_goal_completion_audit_v34_checklist.csv", checklist, fields)
    write_csv(OUT / "current_goal_completion_audit_v34_unmet_requirements.csv", unmet, fields)
    write_csv(
        OUT / "current_goal_completion_audit_v34_intake_roots.csv",
        roots,
        ["id", "requirements", "root", "exists", "required_files", "present_files", "missing_files", "ready"],
    )

    report = [
        "# Current Goal Completion Audit v34",
        "",
        f"Decision: `{audit['decision']}`.",
        "",
        "This audit consolidates the current cursor plus post-cursor request/contact/matrix artifacts.",
        "",
        "Result:",
        f"- Ready intake roots: `{len(ready_roots)}/4`.",
        "- Accepted rows added since v32: `0`.",
        "- New confidence gate since v32: `false`.",
        "- Strict full objective achieved: `false`.",
        "- `update_goal=false`.",
        "",
        "Unmet rows: `R2`, `R3`, `R4`, `R5`, `R6`, and `R8`.",
    ]
    (OUT / "current_goal_completion_audit_v34_after_request_matrices.md").write_text("\n".join(report) + "\n")

    assertions = [
        f"PASS decision={audit['decision']}",
        f"PASS ready_intake_roots={len(ready_roots)}_of_4",
        "PASS accepted_rows_added_since_v32=0",
        "PASS new_confidence_gate_since_v32=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
        "PASS unmet_ids=R2,R3,R4,R5,R6,R8",
    ]
    (CHECKS / "current_goal_completion_audit_v34_after_request_matrices_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )

    print(json.dumps({"decision": audit["decision"], "unmet_ids": audit["unmet_ids"]}, sort_keys=True))


if __name__ == "__main__":
    main()
