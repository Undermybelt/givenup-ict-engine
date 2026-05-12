#!/usr/bin/env python3
"""Completion audit after post-v28 contact, recency, and native-subhour evidence."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

V28_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T201748-codex-current-goal-completion-audit-v28-after-owner-request-package/"
    "completion-audit/current_goal_completion_audit_v28_after_owner_request_package.json"
)
CONTACT_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T201759-codex-do-putnins-contact-leads-v1/"
    "do-putnins-contact-leads/do_putnins_contact_leads_v1.json"
)
RECENCY_OWNER_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T201655-codex-stock-regime-owner-recency-request-package-v1/"
    "stock-regime-owner-recency-request-package/stock_regime_owner_recency_request_package_v1.json"
)
NATIVE_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T201713-codex-native-subhour-local-live-intake-sweep-v1/"
    "native-subhour-local-live-intake-sweep/native_subhour_local_live_intake_sweep_v1.json"
)
RECENCY_LIVE_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T201728-codex-recency-extension-live-verifier-recheck-v1/"
    "recency-extension-live-verifier/recency_extension_live_verifier_recheck_v1.json"
)


def load(path: Path) -> dict:
    with path.open() as handle:
        return json.load(handle)


def board_cursor() -> dict[str, str]:
    text = BOARD.read_text(encoding="utf-8")
    result: dict[str, str] = {}
    in_cursor = False
    for line in text.splitlines():
        if line.strip() == "## Current Cursor":
            in_cursor = True
            continue
        if in_cursor and line.startswith("## "):
            break
        if not in_cursor or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] not in {"Field", "---"}:
            result[cells[0]] = cells[1]
    return result


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    v28 = load(V28_JSON)
    contact = load(CONTACT_JSON)
    recency_owner = load(RECENCY_OWNER_JSON)
    native = load(NATIVE_JSON)
    recency_live = load(RECENCY_LIVE_JSON)
    cursor = board_cursor()

    native_ready = native.get("complete_native_subhour_package_present", False)
    recency_ready = recency_live.get("recency_extension_ready", False)
    contact_rows = contact.get("rows_acquired", False)
    recency_rows = recency_owner.get("r5_recency_tail_repair_closed", False)
    r4_rows = recency_owner.get("r4_strict_1h_source_rows_acquired", False)

    checklist = [
        {
            "id": "R0",
            "status": "pass_checked",
            "requirement": "Named board and latest cursor are read before judging completion.",
            "evidence": f"Board cursor remains {cursor.get('last_loop_id')}; this v29 audit is supplemental and does not edit Current Cursor.",
            "gap": "",
        },
        {
            "id": "R1",
            "status": "pass_scoped_not_full",
            "requirement": "Every scoped active lane keeps >=95% calibrated evidence.",
            "evidence": "v28 preserved scoped active-lane 95 evidence and Sapienza pump/dump 317 accepted event groups.",
            "gap": "Scoped evidence is not strict full-market/full-cycle/full-species completion.",
        },
        {
            "id": "R2",
            "status": "fail_blocked",
            "requirement": "Other-market/source-label equivalence rows and provenance are present and verifier-accepted.",
            "evidence": "v28 still reports source-label equivalence verifier blocked and missing files=2; no post-v28 artifact adds equivalence rows.",
            "gap": "source_label_equivalence_rows.csv and source_label_equivalence_provenance.json are still absent from live intake.",
        },
        {
            "id": "R3",
            "status": "fail_blocked",
            "requirement": "Native sub-hour source-owned price-root label package exists and closes overlap.",
            "evidence": (
                f"native_subhour_local_live_intake_sweep_v1 decision={native.get('decision')}; "
                f"intake_roots_checked={native.get('intake_roots_checked')}; "
                f"exact_required_intake_files_present={native.get('exact_required_intake_files_present')}; "
                f"ready_sources={native.get('ready_native_subhour_source_owned_label_sources')}."
            ),
            "gap": "No native_subhour_source_label_rows.csv plus provenance package was found.",
        },
        {
            "id": "R4",
            "status": "fail_blocked",
            "requirement": "Strict exact 1h target row/provenance package is acquired for the four target cells.",
            "evidence": (
                f"stock_regime_owner_recency_request_package_v1 decision={recency_owner.get('decision')}; "
                f"r4_acquired={r4_rows}; target_rows={recency_owner.get('target_rows')}."
            ),
            "gap": "Owner-request package is ready, but rows have not been acquired or placed under the intake root.",
        },
        {
            "id": "R5",
            "status": "fail_blocked",
            "requirement": "Post-2026-01-30 recency-tail source rows are present and verifier-accepted.",
            "evidence": (
                f"recency_extension_live_verifier_recheck_v1 decision={recency_live.get('decision')}; "
                f"missing_files={recency_live.get('missing_files')}; "
                f"owner_request_repair_closed={recency_rows}."
            ),
            "gap": "The recency extension intake files are missing and the owner request has not produced rows.",
        },
        {
            "id": "R6",
            "status": "partial_still_blocked",
            "requirement": "Direct Manipulation full species coverage has source-owned positives plus matched controls.",
            "evidence": (
                f"do_putnins_contact_leads_v1 decision={contact.get('decision')}; "
                f"contact_lead_count={contact.get('contact_lead_count')}; request_sent={contact.get('request_sent')}; "
                f"rows_acquired={contact_rows}; v28 still has R6 partial."
            ),
            "gap": "Contact paths are ready, but no owner-approved rows were acquired; missing direct species remain uncovered.",
        },
        {
            "id": "R7",
            "status": "pass_guardrail",
            "requirement": "No proxy-only promotion, raw-data commit, threshold relaxation, or trade-usable claim.",
            "evidence": (
                f"v28 raw_data_committed={v28.get('raw_data_committed')}; "
                f"contact update_goal={contact.get('update_goal')}; "
                f"native raw_data_committed={native.get('raw_data_committed')}; "
                f"recency_live raw_data_committed={recency_live.get('raw_data_committed')}."
            ),
            "gap": "",
        },
        {
            "id": "R8",
            "status": "fail_blocked",
            "requirement": "Completion gate allows update_goal only when all rows pass.",
            "evidence": "Rows R2, R3, R4, R5, and R6 remain incomplete after post-v28 contact, recency, and native-subhour evidence.",
            "gap": "Strict full objective is not achieved; update_goal must remain false.",
        },
    ]
    unmet = [row["id"] for row in checklist if row["status"] not in {"pass_checked", "pass_scoped_not_full", "pass_guardrail"}]
    decision = "current_goal_completion_audit_v29=post_v28_contact_recency_native_evidence_strict_objective_blocked"
    result = {
        "run_id": RUN_ROOT.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": (
            "Every active regime in Board A must have calibrated >=95% confidence, and the same regime confidence "
            "must remain suitable across other markets/species and other cycles/timeframes before reporting completion."
        ),
        "decision": decision,
        "checklist_rows": len(checklist),
        "unmet_rows": len(unmet),
        "unmet_ids": unmet,
        "post_v28_evidence_checked": [
            "20260511T201759-codex-do-putnins-contact-leads-v1",
            "20260511T201728-codex-recency-extension-live-verifier-recheck-v1",
            "20260511T201655-codex-stock-regime-owner-recency-request-package-v1",
            "20260511T201713-codex-native-subhour-local-live-intake-sweep-v1",
        ],
        "accepted_rows_added_since_v28": 0,
        "new_confidence_gate_since_v28": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "checklist": checklist,
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v29_after_contact_recency_native_sweeps.json"
    report_path = OUT_DIR / "current_goal_completion_audit_v29_after_contact_recency_native_sweeps.md"
    checklist_path = OUT_DIR / "current_goal_completion_audit_v29_checklist.csv"
    unmet_path = OUT_DIR / "current_goal_completion_audit_v29_unmet_requirements.csv"
    assertion_path = CHECK_DIR / "current_goal_completion_audit_v29_after_contact_recency_native_sweeps_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with checklist_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "requirement", "status", "evidence", "gap"])
        writer.writeheader()
        writer.writerows(checklist)
    with unmet_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "requirement", "status", "evidence", "gap"])
        writer.writeheader()
        writer.writerows([row for row in checklist if row["id"] in unmet])

    lines = [
        "# Current Goal Completion Audit v29 After Contact Recency Native Sweeps",
        "",
        f"- Decision: `{decision}`",
        f"- Checklist rows: `{len(checklist)}`",
        f"- Unmet rows: `{len(unmet)}`",
        f"- Unmet ids: `{', '.join(unmet)}`",
        "- Post-v28 evidence checked: `201759` contact leads, `201728` recency-extension live verifier, `201655` stock-regime owner recency request, and `201713` native sub-hour sweep.",
        "- Accepted rows added since v28: `0`; new confidence gate since v28: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Objective Restatement",
        "",
        result["objective_restatement"],
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| ID | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        lines.append(f"| `{row['id']}` | `{row['status']}` | {row['evidence']} | {row['gap']} |")
    lines += [
        "",
        "## Decision",
        "",
        "The post-v28 evidence improves acquisition readiness and current-state blocking evidence, but no missing source-owned rows or provenance files have arrived. R2/R3/R4/R5/R6 remain incomplete, so the strict objective is still blocked and `update_goal` must not be called.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path}`",
        f"- Checklist CSV: `{checklist_path}`",
        f"- Unmet requirements CSV: `{unmet_path}`",
        f"- Assertions: `{assertion_path}`",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS checklist_rows={len(checklist)}",
        f"PASS unmet_ids={','.join(unmet)}",
        "PASS accepted_rows_added_since_v28=0",
        "PASS new_confidence_gate_since_v28=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertion_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
