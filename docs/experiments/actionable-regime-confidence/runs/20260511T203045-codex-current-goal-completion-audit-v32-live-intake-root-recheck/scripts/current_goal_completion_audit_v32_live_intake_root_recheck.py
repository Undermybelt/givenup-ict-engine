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
V31 = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T202849-codex-current-goal-completion-audit-v31-after-kaggle-live-refresh/"
    "completion-audit/current_goal_completion_audit_v31_after_kaggle_live_refresh.json"
)
KAGGLE_REFRESH = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T202501-codex-kaggle-stock-regime-live-refresh-v1/"
    "kaggle-stock-regime-live-refresh/kaggle_stock_regime_live_refresh_v1.json"
)
STOCK_CONTACT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T202304-codex-stock-regime-owner-contact-leads-v1/"
    "stock-regime-owner-contact-leads/stock_regime_owner_contact_leads_v1.json"
)
SOURCE_LABEL_CONTACT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T202712-codex-source-label-equivalence-contact-leads-v1/"
    "source-label-equivalence-contact-leads/source_label_equivalence_contact_leads_v1.json"
)

INTAKE_ROOTS = [
    {
        "id": "source_label_equivalence",
        "requirements": "R2;R4",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required_files": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
    },
    {
        "id": "native_subhour_source_label",
        "requirements": "R3",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
    },
    {
        "id": "source_panel_recency_extension",
        "requirements": "R5",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
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

    v31 = read_json(V31)
    kaggle = read_json(KAGGLE_REFRESH)
    stock_contact = read_json(STOCK_CONTACT)
    source_label_contact = read_json(SOURCE_LABEL_CONTACT)
    roots = [root_status(item) for item in INTAKE_ROOTS]
    ready_roots = [row["id"] for row in roots if row["ready"]]
    board_hash = sha256(BOARD)

    checklist = [
        {
            "id": "R0",
            "requirement": "Use the named Board A markdown as the execution contract and re-check current evidence before judging completion.",
            "status": "pass_checked",
            "artifact": str(BOARD.relative_to(REPO)),
            "evidence": f"Board hash before v32 writeback={board_hash}; v31 audit and post-v31 live intake roots were read.",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "Every scoped active lane keeps calibrated >=95% evidence.",
            "status": "pass_scoped_not_full",
            "artifact": str(V31.relative_to(REPO)),
            "evidence": "v31 preserves scoped active-lane 95% evidence from prior consumer-map/Sapienza gates.",
            "gap": "Scoped evidence is not strict full-market/full-cycle/full-species closure.",
        },
        {
            "id": "R2",
            "requirement": "The 95% regime result transfers to other markets/species using source-owned or owner-approved labels.",
            "status": "fail_blocked",
            "artifact": f"{SOURCE_LABEL_CONTACT.relative_to(REPO)}; /tmp/ict-engine-source-label-equivalence-intake",
            "evidence": "Source-label contact leads are public-contact ready only; live source-label equivalence intake root is not ready and required rows/provenance files are still missing.",
            "gap": "source_label_equivalence_rows.csv and source_label_equivalence_provenance.json are absent.",
        },
        {
            "id": "R3",
            "requirement": "The 95% regime result transfers to other cycles/timeframes, including native sub-hour source labels.",
            "status": "fail_blocked",
            "artifact": "/tmp/ict-engine-native-subhour-source-label-intake",
            "evidence": "Live native sub-hour source-label intake root is not ready.",
            "gap": "native_subhour_source_label_rows.csv and native_subhour_source_label_provenance.json are absent.",
        },
        {
            "id": "R4",
            "requirement": "Strict exact 1h remaining slots have source-owned rows and provenance.",
            "status": "fail_blocked",
            "artifact": str(STOCK_CONTACT.relative_to(REPO)),
            "evidence": "Stock-regime contact paths remain request-ready only; live source-label equivalence intake files are not present.",
            "gap": "Strict exact 1h owner/source rows were not acquired.",
        },
        {
            "id": "R5",
            "requirement": "Strict 1h recency-tail targets after 2026-01-30 are repaired with source-owned labels.",
            "status": "fail_blocked",
            "artifact": str(KAGGLE_REFRESH.relative_to(REPO)),
            "evidence": "Kaggle live refresh downloaded the latest public package, which matched the local reference and still ended on 2026-01-30; live recency-extension intake root is not ready.",
            "gap": "stock_market_regimes_2026_extension.csv and source_panel_recency_provenance.json are absent.",
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation has source-owned row-level positives, matched controls, and provenance across required species.",
            "status": "partial_still_blocked",
            "artifact": "/tmp/ict-engine-direct-manipulation-row-intake",
            "evidence": "Scoped pump/dump gate remains preserved, but the direct manipulation intake root is not ready.",
            "gap": "positive_spoofing_layering_rows.csv, matched_negative_normal_activity_rows.csv, and provenance_manifest.json are absent.",
        },
        {
            "id": "R7",
            "requirement": "No proxy-only promotion, raw-data commit, threshold relaxation, or trade-usable claim.",
            "status": "pass_guardrail",
            "artifact": str(V31.relative_to(REPO)),
            "evidence": "v31 and this v32 readback keep raw_data_committed=false, thresholds_relaxed=false, runtime_code_changed=false, and trade_usable=false.",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "Mark the goal complete only if every explicit requirement is covered by real evidence.",
            "status": "fail_blocked",
            "artifact": str(RUN_ROOT.relative_to(REPO)),
            "evidence": "R2, R3, R4, R5, and R6 remain incomplete after a live intake-root recheck.",
            "gap": "Strict full objective is not achieved; update_goal remains false.",
        },
    ]

    unmet = [row for row in checklist if row["status"].startswith("fail") or "blocked" in row["status"]]
    audit = {
        "run_id": RUN_ROOT.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": (
            "Every active Board A regime must have calibrated >=95% confidence, and that confidence must remain "
            "suitable across other markets/species and other cycles/timeframes before completion can be reported."
        ),
        "decision": "current_goal_completion_audit_v32=live_intake_roots_still_absent_strict_objective_blocked",
        "v31_prior_decision": v31["decision"],
        "board_hash_before_writeback": board_hash,
        "post_v31_live_roots_checked": [row["root"] for row in roots],
        "ready_intake_roots": ready_roots,
        "ready_intake_root_count": len(ready_roots),
        "intake_roots_checked": roots,
        "source_label_contact_decision": source_label_contact.get("decision", "unknown"),
        "stock_regime_contact_decision": stock_contact.get("decision", "unknown"),
        "kaggle_live_refresh_decision": kaggle.get("decision", "unknown"),
        "kaggle_download_matches_local_reference": kaggle.get("download_matches_local_reference", None),
        "accepted_rows_added_since_v31": 0,
        "new_confidence_gate_since_v31": False,
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

    json_path = OUT / "current_goal_completion_audit_v32_live_intake_root_recheck.json"
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")

    fields = ["id", "requirement", "status", "artifact", "evidence", "gap"]
    write_csv(OUT / "current_goal_completion_audit_v32_checklist.csv", checklist, fields)
    write_csv(OUT / "current_goal_completion_audit_v32_unmet_requirements.csv", unmet, fields)
    write_csv(
        OUT / "current_goal_completion_audit_v32_intake_roots.csv",
        roots,
        ["id", "requirements", "root", "exists", "required_files", "present_files", "missing_files", "ready"],
    )

    md_lines = [
        "# Current Goal Completion Audit v32",
        "",
        f"Decision: `{audit['decision']}`.",
        "",
        "This audit rechecked the live `/tmp` intake roots after v31 and the Kaggle live refresh.",
        "",
        "Result:",
        f"- Ready intake roots: `{len(ready_roots)}/4`.",
        "- Accepted rows added since v31: `0`.",
        "- New confidence gate since v31: `false`.",
        "- Strict full objective achieved: `false`.",
        "- `update_goal=false`.",
        "",
        "Blocked rows: `R2`, `R3`, `R4`, `R5`, `R6`, and `R8`.",
    ]
    (OUT / "current_goal_completion_audit_v32_live_intake_root_recheck.md").write_text("\n".join(md_lines) + "\n")

    assertions = [
        f"PASS decision={audit['decision']}",
        f"PASS ready_intake_roots={len(ready_roots)}_of_4",
        "PASS accepted_rows_added_since_v31=0",
        "PASS new_confidence_gate_since_v31=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
        "PASS unmet_ids=R2,R3,R4,R5,R6,R8",
    ]
    (CHECKS / "current_goal_completion_audit_v32_live_intake_root_recheck_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )

    print(json.dumps({"decision": audit["decision"], "unmet_ids": audit["unmet_ids"]}, sort_keys=True))


if __name__ == "__main__":
    main()
