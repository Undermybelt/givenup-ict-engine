#!/usr/bin/env python3
"""Completion audit after contact leads and recency-extension verifier recheck."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T202112-codex-current-goal-completion-audit-v29-after-contact-and-recency-verifier"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
REPO_ROOT = Path.cwd()

V28 = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T201748-codex-current-goal-completion-audit-v28-after-owner-request-package/completion-audit/current_goal_completion_audit_v28_after_owner_request_package.json"
CONTACT_LEADS = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T201759-codex-do-putnins-contact-leads-v1/do-putnins-contact-leads/do_putnins_contact_leads_v1.json"
RECENCY_VERIFIER = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T201728-codex-recency-extension-live-verifier-recheck-v1/recency-extension-live-verifier/recency_extension_live_verifier_recheck_v1.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    v28 = load(V28)
    contact = load(CONTACT_LEADS)
    recency = load(RECENCY_VERIFIER)
    checklist = [dict(row) for row in v28["checklist"]]
    for row in checklist:
        if row["id"] == "R5":
            row["artifact"] = f"{row['artifact']}; {rel(RECENCY_VERIFIER)}"
            row["evidence"] = (
                f"{row['evidence']} Recency-extension verifier={recency['decision']}; "
                f"intake_files_present={recency['intake_files_present']}; missing_files={len(recency['missing_files'])}."
            )
            row["gap"] = "No recency extension CSV/provenance is present; post-2026-01-30 source-owned tail rows remain absent."
        if row["id"] == "R6":
            row["artifact"] = f"{row['artifact']}; {rel(CONTACT_LEADS)}"
            row["evidence"] = (
                f"{row['evidence']} Contact leads={contact['decision']}; "
                f"contact_lead_count={contact['contact_lead_count']}; request_sent={contact['request_sent']}; rows_acquired={contact['rows_acquired']}."
            )
            row["gap"] = (
                "Contact paths are ready, but no request was sent by this run and no owner-approved rows were acquired; "
                "direct species coverage remains partial."
            )
        if row["id"] == "R8":
            row["evidence"] = "R2, R3, R4, R5, and R6 remain uncovered or partial after v28 plus contact-leads and recency-verifier readbacks."
            row["gap"] = "Strict full objective is not achieved; update_goal must remain false."

    unmet = [row for row in checklist if row["status"] in {"fail_blocked", "partial_still_blocked"}]
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": v28["objective_restatement"],
        "decision": "current_goal_completion_audit_v29=contact_paths_and_recency_verifier_ready_but_rows_not_acquired_blocked",
        "checklist_rows": len(checklist),
        "unmet_rows": len(unmet),
        "unmet_ids": [row["id"] for row in unmet],
        "post_v28_artifacts_checked": [rel(CONTACT_LEADS), rel(RECENCY_VERIFIER)],
        "v28_prior_decision": v28["decision"],
        "contact_leads_decision": contact["decision"],
        "recency_verifier_decision": recency["decision"],
        "new_confidence_gate_since_v28": False,
        "accepted_rows_added_since_v28": 0,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "checklist": checklist,
    }

    (OUT_DIR / "current_goal_completion_audit_v29_after_contact_and_recency_verifier.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    write_csv(
        OUT_DIR / "current_goal_completion_audit_v29_checklist.csv",
        checklist,
        ["id", "requirement", "status", "artifact", "evidence", "gap"],
    )
    write_csv(
        OUT_DIR / "current_goal_completion_audit_v29_unmet_requirements.csv",
        unmet,
        ["id", "requirement", "status", "artifact", "evidence", "gap"],
    )

    md_lines = [
        "# Current Goal Completion Audit v29 After Contact And Recency Verifier",
        "",
        f"- Decision: `{result['decision']}`",
        f"- Checklist rows: `{len(checklist)}`",
        f"- Unmet rows: `{len(unmet)}`",
        f"- Unmet ids: `{', '.join(result['unmet_ids'])}`",
        f"- Contact leads: `{contact['decision']}`",
        f"- Recency verifier: `{recency['decision']}`",
        "- New confidence gate since v28: `false`",
        "- Accepted rows added since v28: `0`",
        "- Strict full objective achieved: `false`; `update_goal=false`",
        "",
        "## Objective Restatement",
        "",
        result["objective_restatement"],
        "",
        "## Post-v28 Evidence Checked",
        "",
        f"- `{rel(CONTACT_LEADS)}`",
        f"- `{rel(RECENCY_VERIFIER)}`",
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| ID | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        md_lines.append(f"| `{row['id']}` | `{row['status']}` | {row['evidence']} | {row['gap']} |")
    md_lines.extend(
        [
            "",
            "## Decision",
            "",
            "The contact-leads package and recency-extension verifier clarify acquisition paths, but neither supplies rows. The strict full objective remains blocked until the required source-label equivalence, recency extension, and direct-manipulation intake files are present and pass their fail-closed verifiers.",
        ]
    )
    (OUT_DIR / "current_goal_completion_audit_v29_after_contact_and_recency_verifier.md").write_text(
        "\n".join(md_lines) + "\n"
    )

    assert contact["decision"] == "do_putnins_contact_leads_v1=public_contact_paths_ready_rows_not_acquired"
    assert contact["request_sent"] is False
    assert contact["rows_acquired"] is False
    assert recency["decision"] == "recency_extension_live_verifier_recheck_v1=missing_recency_extension_intake_files"
    assert recency["intake_files_present"] == 0
    assert result["new_confidence_gate_since_v28"] is False
    assert result["accepted_rows_added_since_v28"] == 0
    assert result["strict_full_objective_achieved"] is False
    assert result["update_goal"] is False
    assert set(result["unmet_ids"]) == {"R2", "R3", "R4", "R5", "R6", "R8"}

    (CHECK_DIR / "current_goal_completion_audit_v29_after_contact_and_recency_verifier_assertions.out").write_text(
        "\n".join(
            [
                "PASS contact_paths_ready_rows_not_acquired",
                "PASS contact_request_sent=false",
                "PASS contact_rows_acquired=false",
                "PASS recency_extension_missing_files",
                "PASS recency_intake_files_present=0",
                "PASS new_confidence_gate_since_v28=false",
                "PASS accepted_rows_added_since_v28=0",
                "PASS strict_full_objective_achieved=false",
                "PASS update_goal=false",
                "PASS unmet_ids=R2,R3,R4,R5,R6,R8",
            ]
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
