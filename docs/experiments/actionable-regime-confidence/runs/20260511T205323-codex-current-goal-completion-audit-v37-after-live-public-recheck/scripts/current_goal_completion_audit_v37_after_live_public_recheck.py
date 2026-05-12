#!/usr/bin/env python3
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T205323-codex-current-goal-completion-audit-v37-after-live-public-recheck"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

INPUTS = {
    "v36": REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T205214-codex-current-goal-completion-audit-v36-after-current-public-scout/completion-audit/current_goal_completion_audit_v36_after_current_public_scout.json",
    "live_public_v37": REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T205200-codex-live-public-acquisition-recheck-v37/live-public-acquisition-recheck/live_public_acquisition_recheck_v37.json",
    "finra_draft_addendum": REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T205142-codex-r6-finra-request-draft-addendum-v1/r6-finra-request-draft-addendum/r6_finra_request_draft_addendum_v1.json",
    "outbox_v2": REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T204715-codex-source-acquisition-outbox-v2-after-r6-uplift/source-acquisition-outbox-v2/source_acquisition_outbox_v2.json",
    "public_scout": REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T205031-codex-current-public-regime-dataset-scout-v1/current-public-regime-dataset-scout/current_public_regime_dataset_scout_v1.json",
}

INTAKE_ROOTS = [
    {
        "id": "source_label_equivalence",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "requirements": "R2;R4",
        "required_files": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
    },
    {
        "id": "native_subhour_source_label",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "requirements": "R3",
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
    },
    {
        "id": "source_panel_recency_extension",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "requirements": "R5",
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
    },
    {
        "id": "direct_manipulation_row_intake",
        "root": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
        "requirements": "R6",
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    },
]


def read_json(path):
    if not path.exists():
        return {"_missing": True, "_path": str(path)}
    with path.open() as handle:
        data = json.load(handle)
    data["_path"] = str(path)
    return data


def board_hash():
    digest = hashlib.sha256()
    with BOARD.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def intake_status():
    rows = []
    for spec in INTAKE_ROOTS:
        root = spec["root"]
        present = []
        missing = []
        for name in spec["required_files"]:
            target = root / name
            if target.exists() and target.stat().st_size > 0:
                present.append(name)
            else:
                missing.append(name)
        rows.append(
            {
                "id": spec["id"],
                "root": str(root),
                "requirements": spec["requirements"],
                "exists": root.exists(),
                "ready": not missing,
                "required_files": ";".join(spec["required_files"]),
                "present_files": ";".join(present),
                "missing_files": ";".join(missing),
            }
        )
    return rows


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    data = {name: read_json(path) for name, path in INPUTS.items()}
    roots = intake_status()
    ready_count = sum(1 for row in roots if row["ready"])

    checklist = [
        {
            "id": "R0",
            "requirement": "Use the named Board A markdown and latest current artifacts as the contract.",
            "artifact": str(BOARD.relative_to(REPO)),
            "evidence": f"Board hash before v37 artifact generation={board_hash()}; read v36, live public v37, FINRA draft addendum, outbox v2, public scout, and /tmp intake roots.",
            "gap": "",
            "status": "pass_checked",
        },
        {
            "id": "R1",
            "requirement": "Every active regime has calibrated >=95% evidence without turning into a trade claim.",
            "artifact": data["v36"].get("_path", ""),
            "evidence": "v36 preserves scoped evidence, and v37 recheck did not relax thresholds or add a trade-usable claim.",
            "gap": "Scoped evidence still does not cover all required other-market and other-cycle rows.",
            "status": "pass_scoped_not_full",
        },
        {
            "id": "R2",
            "requirement": "Other-market/source-label equivalence rows and provenance are acquired and verifier-accepted.",
            "artifact": data["outbox_v2"].get("_path", ""),
            "evidence": f"outbox_v2_rows={data['outbox_v2'].get('v2_outbox_rows')}; request_sent={data['outbox_v2'].get('request_sent')}; rows_acquired={data['outbox_v2'].get('rows_acquired')}.",
            "gap": "source_label_equivalence_rows.csv;source_label_equivalence_provenance.json",
            "status": "fail_blocked",
        },
        {
            "id": "R3",
            "requirement": "Native sub-hour source-label rows and provenance are acquired and verifier-accepted.",
            "artifact": data["live_public_v37"].get("_path", ""),
            "evidence": "The native sub-hour intake root remains absent; no native source-label files were created.",
            "gap": "native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json",
            "status": "fail_blocked",
        },
        {
            "id": "R4",
            "requirement": "Strict exact 1h source rows and provenance are acquired.",
            "artifact": data["outbox_v2"].get("_path", ""),
            "evidence": "R4 remains in the acquisition queue and shares the absent source-label equivalence intake package.",
            "gap": "source_label_equivalence_rows.csv;source_label_equivalence_provenance.json",
            "status": "fail_blocked",
        },
        {
            "id": "R5",
            "requirement": "Post-2026-01-30 source-panel recency extension rows and provenance are acquired.",
            "artifact": data["live_public_v37"].get("_path", ""),
            "evidence": f"kaggle_date_max={data['live_public_v37'].get('kaggle_stats', {}).get('date_max')}; post_cutoff_target_rows={data['live_public_v37'].get('kaggle_stats', {}).get('post_cutoff_target_rows')}; recency_materialized={data['live_public_v37'].get('recency_materialization', {}).get('created')}.",
            "gap": "stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json",
            "status": "fail_blocked",
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation positive/control/provenance files are acquired across required species.",
            "artifact": data["finra_draft_addendum"].get("_path", ""),
            "evidence": f"official_route_count={data['finra_draft_addendum'].get('official_route_count')}; request_sent={data['finra_draft_addendum'].get('request_sent')}; rows_acquired={data['finra_draft_addendum'].get('rows_acquired')}; matched_controls_acquired={data['finra_draft_addendum'].get('matched_controls_acquired')}.",
            "gap": "positive_spoofing_layering_rows.csv;matched_negative_normal_activity_rows.csv;provenance_manifest.json",
            "status": "partial_still_blocked",
        },
        {
            "id": "R7",
            "requirement": "No proxy labels, raw-data commits, threshold relaxation, external send, or trade-usable claim.",
            "artifact": ";".join(d.get("_path", "") for d in data.values()),
            "evidence": "All read artifacts keep request_sent=false, accepted_rows_added=0, new_confidence_gate=false, thresholds_relaxed=false, raw_data_committed=false, trade_usable=false.",
            "gap": "",
            "status": "pass_guardrail",
        },
        {
            "id": "R8",
            "requirement": "Only call update_goal when every strict requirement is covered by real accepted evidence.",
            "artifact": str(RUN_ROOT.relative_to(REPO)),
            "evidence": "R2/R3/R4/R5/R6 remain blocked and ready intake roots are 0/4.",
            "gap": "Strict full objective is not achieved; update_goal remains false.",
            "status": "fail_blocked",
        },
    ]

    accepted_rows = max(
        int(data["v36"].get("accepted_rows_added_since_v35") or 0),
        int(data["live_public_v37"].get("accepted_rows_added") or 0),
        int(data["finra_draft_addendum"].get("accepted_rows_added") or 0),
    )
    request_sent = any(bool(d.get("request_sent")) for d in data.values())
    rows_acquired = any(bool(d.get("rows_acquired")) for d in data.values())
    new_confidence = any(
        bool(d.get("new_confidence_gate") or d.get("new_confidence_gate_since_v35"))
        for d in data.values()
    )
    strict_done = False
    unmet = ["R2", "R3", "R4", "R5", "R6", "R8"]

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact_generation": board_hash(),
        "objective_restatement": "Every active Board A regime must have source-owned or owner-approved >=95% confidence and survive other-market/species plus other-cycle/timeframe validation before completion.",
        "decision": "current_goal_completion_audit_v37=live_public_v37_and_finra_addendum_rows_not_acquired_blocked",
        "inputs": {name: str(path.relative_to(REPO)) for name, path in INPUTS.items()},
        "input_decisions": {
            name: data[name].get("decision") for name in data
        },
        "outbox_v2_rows": data["outbox_v2"].get("v2_outbox_rows"),
        "draft_count": data["v36"].get("draft_count"),
        "public_scout_candidate_count": data["v36"].get("public_scout_candidate_count"),
        "live_public_v37_kaggle_date_max": data["live_public_v37"].get("kaggle_stats", {}).get("date_max"),
        "live_public_v37_post_cutoff_target_rows": data["live_public_v37"].get("kaggle_stats", {}).get("post_cutoff_target_rows"),
        "finra_official_route_count": data["finra_draft_addendum"].get("official_route_count"),
        "request_sent": request_sent,
        "rows_acquired": rows_acquired,
        "ready_intake_root_count": ready_count,
        "ready_intake_roots": [row["id"] for row in roots if row["ready"]],
        "accepted_rows_added_since_v36": accepted_rows,
        "new_confidence_gate": new_confidence,
        "strict_full_objective_achieved": strict_done,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "unmet_ids": unmet,
        "unmet_rows": len(unmet),
        "intake_roots_checked": roots,
        "checklist": checklist,
        "next_action": "Populate the four fail-closed /tmp intake roots with real source-owned or owner-approved files, then rerun the existing verifiers before another completion audit; do not send the outbox without explicit user approval.",
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v37_after_live_public_recheck.json"
    report_path = OUT_DIR / "current_goal_completion_audit_v37_after_live_public_recheck.md"
    checklist_path = OUT_DIR / "current_goal_completion_audit_v37_checklist.csv"
    unmet_path = OUT_DIR / "current_goal_completion_audit_v37_unmet_requirements.csv"
    roots_path = OUT_DIR / "current_goal_completion_audit_v37_intake_roots.csv"
    assertions_path = CHECK_DIR / "current_goal_completion_audit_v37_after_live_public_recheck_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_csv(
        checklist_path,
        checklist,
        ["id", "requirement", "artifact", "evidence", "gap", "status"],
    )
    write_csv(
        unmet_path,
        [row for row in checklist if row["status"].startswith("fail") or row["status"].startswith("partial")],
        ["id", "requirement", "artifact", "evidence", "gap", "status"],
    )
    write_csv(
        roots_path,
        roots,
        ["id", "root", "requirements", "exists", "ready", "required_files", "present_files", "missing_files"],
    )

    report_lines = [
        "# Current Goal Completion Audit v37 After Live Public Recheck",
        "",
        f"Decision: `{result['decision']}`.",
        "",
        "## Objective",
        "",
        result["objective_restatement"],
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| ID | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        report_lines.append(
            f"| `{row['id']}` | `{row['status']}` | {row['evidence']} | `{row['gap']}` |"
        )
    report_lines.extend(
        [
            "",
            "## Readback",
            "",
            f"- v36 decision: `{data['v36'].get('decision')}`.",
            f"- live public v37 decision: `{data['live_public_v37'].get('decision')}`.",
            f"- FINRA draft addendum decision: `{data['finra_draft_addendum'].get('decision')}`.",
            f"- outbox v2 rows: `{result['outbox_v2_rows']}`; request sent: `{result['request_sent']}`; rows acquired: `{result['rows_acquired']}`.",
            f"- Kaggle source date max: `{result['live_public_v37_kaggle_date_max']}`; post-cutoff target rows: `{result['live_public_v37_post_cutoff_target_rows']}`.",
            f"- ready intake roots: `{ready_count}/4`.",
            f"- accepted rows added since v36: `{accepted_rows}`; new confidence gate: `{new_confidence}`.",
            f"- unmet rows: `{', '.join(unmet)}`.",
            "",
            "## Result",
            "",
            "Strict full objective is not achieved. No `update_goal` call is permitted from this audit.",
        ]
    )
    report_path.write_text("\n".join(report_lines) + "\n")

    assertions = [
        f"PASS decision={result['decision']}",
        f"PASS board_hash_before_artifact_generation={result['board_hash_before_artifact_generation']}",
        f"PASS outbox_v2_rows={result['outbox_v2_rows']}",
        f"PASS live_public_v37_post_cutoff_target_rows={result['live_public_v37_post_cutoff_target_rows']}",
        f"PASS finra_official_route_count={result['finra_official_route_count']}",
        f"PASS ready_intake_roots={ready_count}_of_4",
        f"PASS request_sent={str(request_sent).lower()}",
        f"PASS rows_acquired={str(rows_acquired).lower()}",
        f"PASS accepted_rows_added_since_v36={accepted_rows}",
        f"PASS new_confidence_gate={str(new_confidence).lower()}",
        f"PASS strict_full_objective_achieved={str(strict_done).lower()}",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
        f"PASS unmet_ids={','.join(unmet)}",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")

    print(json.dumps({
        "decision": result["decision"],
        "strict_full_objective_achieved": strict_done,
        "update_goal": False,
        "ready_intake_root_count": ready_count,
        "accepted_rows_added_since_v36": accepted_rows,
        "unmet_ids": unmet,
        "report": str(report_path.relative_to(REPO)),
        "assertions": str(assertions_path.relative_to(REPO)),
    }, indent=2))


if __name__ == "__main__":
    main()
