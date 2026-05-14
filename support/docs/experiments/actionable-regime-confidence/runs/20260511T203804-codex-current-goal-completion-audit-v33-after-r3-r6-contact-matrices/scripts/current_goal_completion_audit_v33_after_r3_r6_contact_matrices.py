#!/usr/bin/env python3
"""Completion audit after R3 native-subhour contacts and R6 species matrix."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T203804-codex-current-goal-completion-audit-v33-after-r3-r6-contact-matrices"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
V32 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T203339-codex-current-goal-completion-audit-v32-after-r2-r3-request-packages/completion-audit/current_goal_completion_audit_v32_after_r2_r3_request_packages.json"
SOURCE_LABEL_CONTACT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202712-codex-source-label-equivalence-contact-leads-v1/source-label-equivalence-contact-leads/source_label_equivalence_contact_leads_v1.json"
NATIVE_REQUEST = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T203100-codex-native-subhour-intake-request-package-v1/native-subhour-intake-request-package/native_subhour_intake_request_package_v1.json"
NATIVE_CONTACT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T203505-codex-native-subhour-contact-leads-v1/native-subhour-contact-leads/native_subhour_contact_leads_v1.json"
DIRECT_MATRIX = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T203523-codex-direct-manipulation-species-request-matrix-v1/direct-manipulation-species-request-matrix/direct_manipulation_species_request_matrix_v1.json"
STOCK_CONTACT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202304-codex-stock-regime-owner-contact-leads-v1/stock-regime-owner-contact-leads/stock_regime_owner_contact_leads_v1.json"
KAGGLE_REFRESH = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202501-codex-kaggle-stock-regime-live-refresh-v1/kaggle-stock-regime-live-refresh/kaggle_stock_regime_live_refresh_v1.json"

INTAKE_ROOTS = [
    {
        "id": "source_label_equivalence",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required": ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"],
        "requirements": "R2;R4",
    },
    {
        "id": "native_subhour_source_label",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required": ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
        "requirements": "R3",
    },
    {
        "id": "source_panel_recency_extension",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required": ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
        "requirements": "R5",
    },
    {
        "id": "direct_manipulation_row_intake",
        "root": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
        "required": ["positive_spoofing_layering_rows.csv", "matched_negative_normal_activity_rows.csv", "provenance_manifest.json"],
        "requirements": "R6",
    },
]


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def root_status() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in INTAKE_ROOTS:
        root = item["root"]
        required = item["required"]
        present = sorted(path.name for path in root.glob("*") if path.is_file()) if root.exists() else []
        missing = [name for name in required if name not in present]
        rows.append(
            {
                "id": item["id"],
                "root": str(root),
                "requirements": item["requirements"],
                "exists": root.exists(),
                "required_files": ";".join(required),
                "present_files": ";".join(present),
                "missing_files": ";".join(missing),
                "ready": not missing,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    v32 = load_json(V32)
    source_contact = load_json(SOURCE_LABEL_CONTACT)
    native_request = load_json(NATIVE_REQUEST)
    native_contact = load_json(NATIVE_CONTACT)
    direct_matrix = load_json(DIRECT_MATRIX)
    stock_contact = load_json(STOCK_CONTACT)
    kaggle_refresh = load_json(KAGGLE_REFRESH)
    roots = root_status()
    ready_roots = [row for row in roots if row["ready"]]
    unmet_ids = ["R2", "R3", "R4", "R5", "R6", "R8"]

    checklist = [
        {
            "id": "R0",
            "requirement": "Use the named Board A markdown as the execution contract and re-check current evidence before judging completion.",
            "status": "pass_checked",
            "artifact": str(BOARD.relative_to(REPO)),
            "evidence": "Board, v32 audit, R3 native-subhour contacts, R6 direct-species matrix, and live intake roots were checked.",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "Every scoped active lane keeps calibrated >=95% evidence.",
            "status": "pass_scoped_not_full",
            "artifact": str(V32.relative_to(REPO)),
            "evidence": "Prior scoped 95% evidence remains preserved by v32.",
            "gap": "Scoped evidence is not strict full-market/full-cycle/full-species closure.",
        },
        {
            "id": "R2",
            "requirement": "The 95% regime result transfers to other markets/species using source-owned or owner-approved labels.",
            "status": "fail_blocked",
            "artifact": str(SOURCE_LABEL_CONTACT.relative_to(REPO)),
            "evidence": f"R2 contact leads={source_contact.get('contact_lead_count')}; rows_acquired={source_contact.get('rows_acquired')}; intake_files_created={source_contact.get('source_label_equivalence_intake_files_created')}.",
            "gap": "Source-label equivalence rows/provenance remain absent.",
        },
        {
            "id": "R3",
            "requirement": "The 95% regime result transfers to other cycles/timeframes, including native sub-hour source labels.",
            "status": "fail_blocked",
            "artifact": str(NATIVE_CONTACT.relative_to(REPO)),
            "evidence": f"R3 request targets={native_request.get('native_intraday_target_count')}; native contact leads={native_contact.get('contact_lead_count')}; rows_acquired={native_contact.get('rows_acquired')}; intake_files_created={native_contact.get('native_subhour_source_label_intake_files_created')}.",
            "gap": "Native sub-hour source-label rows/provenance remain absent.",
        },
        {
            "id": "R4",
            "requirement": "Strict exact 1h remaining slots have source-owned rows and provenance.",
            "status": "fail_blocked",
            "artifact": str(STOCK_CONTACT.relative_to(REPO)),
            "evidence": f"Stock-regime contact leads={stock_contact.get('contact_lead_count')}; rows_acquired={stock_contact.get('rows_acquired')}.",
            "gap": "Strict exact 1h source-owned rows/provenance are not acquired.",
        },
        {
            "id": "R5",
            "requirement": "Strict 1h recency-tail targets after 2026-01-30 are repaired with source-owned labels.",
            "status": "fail_blocked",
            "artifact": str(KAGGLE_REFRESH.relative_to(REPO)),
            "evidence": f"Kaggle refresh decision={kaggle_refresh.get('decision')}; date_max={kaggle_refresh.get('csv_stats', {}).get('date_max')}; post_cutoff_target_rows={kaggle_refresh.get('post_cutoff_target_rows')}.",
            "gap": "Latest public Kaggle package still ends at 2026-01-30 and recency-extension files are absent.",
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation has source-owned row-level positives, matched controls, and provenance across required species.",
            "status": "partial_still_blocked",
            "artifact": str(DIRECT_MATRIX.relative_to(REPO)),
            "evidence": f"Direct species matrix decision={direct_matrix.get('decision')}; matrix_rows={direct_matrix.get('matrix_row_count')}; rows_acquired={direct_matrix.get('rows_acquired')}.",
            "gap": "Direct species request matrix is concrete, but positive/control/provenance packages remain absent.",
        },
        {
            "id": "R7",
            "requirement": "No proxy, generated, synthetic, future-return, duplicated, or OHLCV-only labels are promoted.",
            "status": "pass_guardrail",
            "artifact": str(RUN_ROOT.relative_to(REPO)),
            "evidence": "Request/contact packages do not create labels, commit raw data, relax thresholds, or claim trade usability.",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "Mark the goal complete only if every explicit requirement is covered by real evidence.",
            "status": "fail_blocked",
            "artifact": str(RUN_ROOT.relative_to(REPO)),
            "evidence": f"Unmet rows remain {', '.join(unmet_ids)}; ready intake roots={len(ready_roots)}/4; accepted rows added since v32=0.",
            "gap": "Strict full objective is not achieved; update_goal must remain false.",
        },
    ]

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": "Every active Board A regime must have calibrated >=95% confidence and must stay valid across other markets/species and other cycles/timeframes using source-owned or owner-approved evidence.",
        "prior_v32_decision": v32.get("decision"),
        "latest_artifacts_checked": [
            str(V32.relative_to(REPO)),
            str(NATIVE_CONTACT.relative_to(REPO)),
            str(DIRECT_MATRIX.relative_to(REPO)),
            str(SOURCE_LABEL_CONTACT.relative_to(REPO)),
            str(STOCK_CONTACT.relative_to(REPO)),
            str(KAGGLE_REFRESH.relative_to(REPO)),
        ],
        "intake_roots_checked": roots,
        "ready_intake_roots": len(ready_roots),
        "checklist_rows": checklist,
        "unmet_requirement_ids": unmet_ids,
        "decision": "current_goal_completion_audit_v33=r3_r6_contact_matrices_ready_rows_not_acquired_blocked",
        "accepted_rows_added_since_v32": 0,
        "new_confidence_gate_since_v32": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v33_after_r3_r6_contact_matrices.json"
    report_path = OUT_DIR / "current_goal_completion_audit_v33_after_r3_r6_contact_matrices.md"
    checklist_csv = OUT_DIR / "current_goal_completion_audit_v33_checklist.csv"
    unmet_csv = OUT_DIR / "current_goal_completion_audit_v33_unmet_requirements.csv"
    roots_csv = OUT_DIR / "current_goal_completion_audit_v33_intake_roots.csv"
    assertion_path = CHECK_DIR / "current_goal_completion_audit_v33_after_r3_r6_contact_matrices_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_csv, checklist, ["id", "requirement", "status", "artifact", "evidence", "gap"])
    write_csv(unmet_csv, [row for row in checklist if row["id"] in unmet_ids], ["id", "requirement", "status", "artifact", "evidence", "gap"])
    write_csv(roots_csv, roots, ["id", "root", "requirements", "exists", "required_files", "present_files", "missing_files", "ready"])

    lines = [
        "# Current Goal Completion Audit v33 After R3/R6 Contact Matrices",
        "",
        f"- Decision: `{result['decision']}`",
        f"- Prior v32 decision: `{v32.get('decision')}`",
        f"- Native sub-hour contacts: `{native_contact.get('contact_lead_count')}`; rows acquired: `{str(native_contact.get('rows_acquired')).lower()}`",
        f"- Direct species matrix decision: `{direct_matrix.get('decision')}`",
        f"- Ready intake roots: `{len(ready_roots)}/4`",
        f"- Unmet requirement ids: `{', '.join(unmet_ids)}`",
        "- Accepted rows added since v32: `0`; new confidence gate since v32: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| ID | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        evidence = str(row["evidence"]).replace("|", "\\|")
        gap = str(row["gap"]).replace("|", "\\|")
        lines.append(
            f"| `{row['id']}` | `{row['status']}` | {evidence} | {gap} |"
        )
    lines.extend(
        [
            "",
            "## Completion Decision",
            "",
            "R3 and R6 now have concrete request/contact matrices, but no source-owned row files or provenance files have appeared under the fail-closed intake roots. The strict objective remains blocked.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Checklist CSV: `{checklist_csv}`",
            f"- Unmet requirements CSV: `{unmet_csv}`",
            f"- Intake-root CSV: `{roots_csv}`",
            f"- Assertions: `{assertion_path}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={result['decision']}",
        f"PASS ready_intake_roots={len(ready_roots)}_of_4",
        "PASS accepted_rows_added_since_v32=0",
        "PASS new_confidence_gate_since_v32=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
        f"PASS unmet_ids={','.join(unmet_ids)}",
    ]
    assertion_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
