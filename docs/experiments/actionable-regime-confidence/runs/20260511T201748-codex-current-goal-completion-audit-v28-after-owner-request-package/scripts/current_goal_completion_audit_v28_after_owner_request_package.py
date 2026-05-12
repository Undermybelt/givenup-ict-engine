#!/usr/bin/env python3
"""Completion audit after the Do/Putnins owner-request package."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T201748-codex-current-goal-completion-audit-v28-after-owner-request-package"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
REPO_ROOT = Path.cwd()

V27 = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T201254-codex-current-goal-completion-audit-v27-after-live-intake-and-tail-rechecks/completion-audit/current_goal_completion_audit_v27_after_live_intake_and_tail_rechecks.json"
OWNER_PACKAGE = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T201352-codex-do-putnins-owner-request-package-v1/do-putnins-owner-request-package/do_putnins_owner_request_package_v1.json"


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

    v27 = load(V27)
    owner = load(OWNER_PACKAGE)
    checklist = [dict(row) for row in v27["checklist"]]
    for row in checklist:
        if row["id"] == "R6":
            row["artifact"] = f"{row['artifact']}; {rel(OWNER_PACKAGE)}"
            row["evidence"] = (
                f"{row['evidence']} Owner request package={owner['decision']}; "
                f"required_files={len(owner['required_files'])}; required_fields={len(owner['required_fields'])}; "
                f"accepted_rows_added={owner['accepted_rows_added']}."
            )
            row["gap"] = (
                "Owner-request package is ready, but no owner-approved rows have been acquired; "
                "spoofing/layering, quote stuffing, pinging, bear raid, and painting tape remain uncovered."
            )
        if row["id"] == "R8":
            row["evidence"] = "R2, R3, R4, R5, and R6 remain uncovered or partial after the v27 audit plus the owner-request package."
            row["gap"] = "Strict full objective is not achieved; update_goal must remain false."

    unmet = [row for row in checklist if row["status"] in {"fail_blocked", "partial_still_blocked"}]
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": v27["objective_restatement"],
        "decision": "current_goal_completion_audit_v28=owner_request_ready_rows_not_acquired_strict_objective_blocked",
        "checklist_rows": len(checklist),
        "unmet_rows": len(unmet),
        "unmet_ids": [row["id"] for row in unmet],
        "post_v27_artifacts_checked": [rel(OWNER_PACKAGE)],
        "v27_prior_decision": v27["decision"],
        "owner_request_decision": owner["decision"],
        "owner_request_required_files": owner["required_files"],
        "owner_request_required_fields": owner["required_fields"],
        "new_confidence_gate_since_v27": False,
        "accepted_rows_added_since_v27": 0,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "checklist": checklist,
    }

    (OUT_DIR / "current_goal_completion_audit_v28_after_owner_request_package.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    write_csv(
        OUT_DIR / "current_goal_completion_audit_v28_checklist.csv",
        checklist,
        ["id", "requirement", "status", "artifact", "evidence", "gap"],
    )
    write_csv(
        OUT_DIR / "current_goal_completion_audit_v28_unmet_requirements.csv",
        unmet,
        ["id", "requirement", "status", "artifact", "evidence", "gap"],
    )

    md_lines = [
        "# Current Goal Completion Audit v28 After Owner Request Package",
        "",
        f"- Decision: `{result['decision']}`",
        f"- Checklist rows: `{len(checklist)}`",
        f"- Unmet rows: `{len(unmet)}`",
        f"- Unmet ids: `{', '.join(result['unmet_ids'])}`",
        f"- Owner request package: `{owner['decision']}`",
        "- New confidence gate since v27: `false`",
        "- Accepted rows added since v27: `0`",
        "- Strict full objective achieved: `false`; `update_goal=false`",
        "",
        "## Objective Restatement",
        "",
        result["objective_restatement"],
        "",
        "## Post-v27 Evidence Checked",
        "",
        f"- `{rel(OWNER_PACKAGE)}`",
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
            "The owner-request package turns the closest spoofing/layering source target into concrete acquisition fields, but it adds no rows and no confidence gate. The strict full objective remains blocked until the required source-label equivalence and direct-manipulation intake files are actually present and pass their fail-closed verifiers.",
        ]
    )
    (OUT_DIR / "current_goal_completion_audit_v28_after_owner_request_package.md").write_text(
        "\n".join(md_lines) + "\n"
    )

    assert owner["decision"] == "do_putnins_owner_request_package_v1=owner_request_ready_rows_not_acquired"
    assert len(owner["required_files"]) == 3
    assert len(owner["required_fields"]) == 17
    assert result["new_confidence_gate_since_v27"] is False
    assert result["accepted_rows_added_since_v27"] == 0
    assert result["strict_full_objective_achieved"] is False
    assert result["update_goal"] is False
    assert set(result["unmet_ids"]) == {"R2", "R3", "R4", "R5", "R6", "R8"}

    (CHECK_DIR / "current_goal_completion_audit_v28_after_owner_request_package_assertions.out").write_text(
        "\n".join(
            [
                "PASS owner_request_ready_rows_not_acquired",
                "PASS owner_required_files=3",
                "PASS owner_required_fields=17",
                "PASS new_confidence_gate_since_v27=false",
                "PASS accepted_rows_added_since_v27=0",
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
