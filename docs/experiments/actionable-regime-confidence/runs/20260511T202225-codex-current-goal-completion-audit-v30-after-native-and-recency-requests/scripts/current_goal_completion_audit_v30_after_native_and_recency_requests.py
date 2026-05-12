#!/usr/bin/env python3
"""Completion audit after native-subhour sweep and stock-regime recency request."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T202225-codex-current-goal-completion-audit-v30-after-native-and-recency-requests"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
REPO_ROOT = Path.cwd()

V29 = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T202112-codex-current-goal-completion-audit-v29-after-contact-and-recency-verifier/completion-audit/current_goal_completion_audit_v29_after_contact_and_recency_verifier.json"
STOCK_REQUEST = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T201655-codex-stock-regime-owner-recency-request-package-v1/stock-regime-owner-recency-request-package/stock_regime_owner_recency_request_package_v1.json"
NATIVE_SWEEP = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T201713-codex-native-subhour-local-live-intake-sweep-v1/native-subhour-local-live-intake-sweep/native_subhour_local_live_intake_sweep_v1.json"


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

    v29 = load(V29)
    stock = load(STOCK_REQUEST)
    native = load(NATIVE_SWEEP)
    checklist = [dict(row) for row in v29["checklist"]]
    for row in checklist:
        if row["id"] == "R3":
            row["artifact"] = f"{row['artifact']}; {rel(NATIVE_SWEEP)}"
            row["evidence"] = (
                f"{row['evidence']} Native sub-hour sweep={native['decision']}; "
                f"intake_roots_checked={native['intake_roots_checked']}; "
                f"exact_required_intake_files_present={native['exact_required_intake_files_present']}; "
                f"ready_sources={native['ready_native_subhour_source_owned_label_sources']}."
            )
            row["gap"] = "No native sub-hour source-owned label intake package is present; raw OHLCV/provider files remain rejected."
        if row["id"] == "R4":
            row["artifact"] = f"{row['artifact']}; {rel(STOCK_REQUEST)}"
            row["evidence"] = (
                f"{row['evidence']} Stock-regime owner request={stock['decision']}; "
                f"required_files={len(stock['required_files'])}; target_rows={len(stock['target_rows'])}; "
                f"r4_acquired={stock['r4_strict_1h_source_rows_acquired']}."
            )
            row["gap"] = "R4 request package is ready, but source-owned strict 1h rows/provenance are not acquired."
        if row["id"] == "R5":
            row["artifact"] = f"{row['artifact']}; {rel(STOCK_REQUEST)}"
            row["evidence"] = (
                f"{row['evidence']} Stock-regime owner request={stock['decision']}; "
                f"r5_recency_tail_repair_closed={stock['r5_recency_tail_repair_closed']}; "
                f"known_post_2026_01_30_rows={stock['known_current_gap']['post_2026_01_30_rows_for_targets']}."
            )
            row["gap"] = "R5 request package is ready, but no post-2026-01-30 source-owned target rows are acquired."
        if row["id"] == "R8":
            row["evidence"] = "R2, R3, R4, R5, and R6 remain uncovered or partial after v29 plus native-subhour and stock-regime owner-request readbacks."
            row["gap"] = "Strict full objective is not achieved; update_goal must remain false."

    unmet = [row for row in checklist if row["status"] in {"fail_blocked", "partial_still_blocked"}]
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": v29["objective_restatement"],
        "decision": "current_goal_completion_audit_v30=native_and_recency_requests_ready_rows_not_acquired_blocked",
        "checklist_rows": len(checklist),
        "unmet_rows": len(unmet),
        "unmet_ids": [row["id"] for row in unmet],
        "post_v29_artifacts_checked": [rel(STOCK_REQUEST), rel(NATIVE_SWEEP)],
        "v29_prior_decision": v29["decision"],
        "stock_request_decision": stock["decision"],
        "native_sweep_decision": native["decision"],
        "new_confidence_gate_since_v29": False,
        "accepted_rows_added_since_v29": 0,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "checklist": checklist,
    }

    (OUT_DIR / "current_goal_completion_audit_v30_after_native_and_recency_requests.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    write_csv(
        OUT_DIR / "current_goal_completion_audit_v30_checklist.csv",
        checklist,
        ["id", "requirement", "status", "artifact", "evidence", "gap"],
    )
    write_csv(
        OUT_DIR / "current_goal_completion_audit_v30_unmet_requirements.csv",
        unmet,
        ["id", "requirement", "status", "artifact", "evidence", "gap"],
    )

    md_lines = [
        "# Current Goal Completion Audit v30 After Native And Recency Requests",
        "",
        f"- Decision: `{result['decision']}`",
        f"- Checklist rows: `{len(checklist)}`",
        f"- Unmet rows: `{len(unmet)}`",
        f"- Unmet ids: `{', '.join(result['unmet_ids'])}`",
        f"- Stock-regime owner request: `{stock['decision']}`",
        f"- Native sub-hour sweep: `{native['decision']}`",
        "- New confidence gate since v29: `false`",
        "- Accepted rows added since v29: `0`",
        "- Strict full objective achieved: `false`; `update_goal=false`",
        "",
        "## Objective Restatement",
        "",
        result["objective_restatement"],
        "",
        "## Post-v29 Evidence Checked",
        "",
        f"- `{rel(STOCK_REQUEST)}`",
        f"- `{rel(NATIVE_SWEEP)}`",
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
            "The native-subhour sweep and stock-regime owner request convert more blockers into precise acquisition paths, but neither supplies accepted rows. The strict full objective remains blocked until the required intake files are present and accepted by the fail-closed verifiers.",
        ]
    )
    (OUT_DIR / "current_goal_completion_audit_v30_after_native_and_recency_requests.md").write_text(
        "\n".join(md_lines) + "\n"
    )

    assert stock["decision"] == "stock_regime_owner_recency_request_package_v1=owner_request_ready_rows_not_acquired"
    assert stock["r4_strict_1h_source_rows_acquired"] is False
    assert stock["r5_recency_tail_repair_closed"] is False
    assert native["decision"] == "native_subhour_local_live_intake_sweep_v1=no_native_subhour_source_owned_intake_package"
    assert native["exact_required_intake_files_present"] == 0
    assert result["new_confidence_gate_since_v29"] is False
    assert result["accepted_rows_added_since_v29"] == 0
    assert result["strict_full_objective_achieved"] is False
    assert result["update_goal"] is False
    assert set(result["unmet_ids"]) == {"R2", "R3", "R4", "R5", "R6", "R8"}

    (CHECK_DIR / "current_goal_completion_audit_v30_after_native_and_recency_requests_assertions.out").write_text(
        "\n".join(
            [
                "PASS stock_request_ready_rows_not_acquired",
                "PASS r4_strict_1h_source_rows_acquired=false",
                "PASS r5_recency_tail_repair_closed=false",
                "PASS native_subhour_package_absent",
                "PASS native_exact_required_intake_files_present=0",
                "PASS new_confidence_gate_since_v29=false",
                "PASS accepted_rows_added_since_v29=0",
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
