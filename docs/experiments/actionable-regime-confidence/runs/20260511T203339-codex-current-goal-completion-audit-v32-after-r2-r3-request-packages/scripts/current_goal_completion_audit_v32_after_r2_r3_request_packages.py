#!/usr/bin/env python3
"""Completion audit after R2/R3 request packages and live intake rechecks."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T203339-codex-current-goal-completion-audit-v32-after-r2-r3-request-packages"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
V31 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202849-codex-current-goal-completion-audit-v31-after-kaggle-live-refresh/completion-audit/current_goal_completion_audit_v31_after_kaggle_live_refresh.json"
SOURCE_CONTACT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202712-codex-source-label-equivalence-contact-leads-v1/source-label-equivalence-contact-leads/source_label_equivalence_contact_leads_v1.json"
NATIVE_REQUEST = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T203100-codex-native-subhour-intake-request-package-v1/native-subhour-intake-request-package/native_subhour_intake_request_package_v1.json"
STOCK_CONTACT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202304-codex-stock-regime-owner-contact-leads-v1/stock-regime-owner-contact-leads/stock_regime_owner_contact_leads_v1.json"
KAGGLE_REFRESH = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202501-codex-kaggle-stock-regime-live-refresh-v1/kaggle-stock-regime-live-refresh/kaggle_stock_regime_live_refresh_v1.json"
DO_CONTACT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T201759-codex-do-putnins-contact-leads-v1/do-putnins-contact-leads/do_putnins_contact_leads_v1.json"
SAPIENZA_GATE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T195945-codex-sapienza-pumpdump-control-gate-v1/sapienza-pumpdump-control-gate/sapienza_pumpdump_control_gate_v1.json"

SOURCE_LABEL_VERIFIER = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T182922-codex-source-label-equivalence-intake-verifier-v1/equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
RECENCY_VERIFIER = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T165405-codex-source-panel-recency-extension-manifest-v1/source-panel-recency/source_panel_recency_extension_verifier_v1.py"
DIRECT_VERIFIER = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"

INTAKE_ROOTS = [
    {
        "id": "source_label_equivalence",
        "root": Path("/tmp/ict-engine-source-label-equivalence-intake"),
        "required_files": [
            "source_label_equivalence_rows.csv",
            "source_label_equivalence_provenance.json",
        ],
        "requirements": "R2;R4",
    },
    {
        "id": "native_subhour_source_label",
        "root": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        "required_files": [
            "native_subhour_source_label_rows.csv",
            "native_subhour_source_label_provenance.json",
        ],
        "requirements": "R3",
    },
    {
        "id": "source_panel_recency_extension",
        "root": Path("/tmp/ict-engine-source-panel-recency-extension"),
        "required_files": [
            "stock_market_regimes_2026_extension.csv",
            "source_panel_recency_provenance.json",
        ],
        "requirements": "R5",
    },
    {
        "id": "direct_manipulation_row_intake",
        "root": Path("/tmp/ict-engine-direct-manipulation-row-intake"),
        "required_files": [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
        "requirements": "R6",
    },
]


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def present_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(path.name for path in root.glob("*") if path.is_file())


def intake_readback() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in INTAKE_ROOTS:
        root = item["root"]
        required = list(item["required_files"])
        present = present_files(root)
        missing = [name for name in required if name not in present]
        rows.append(
            {
                "id": item["id"],
                "root": str(root),
                "exists": root.exists(),
                "required_files": ";".join(required),
                "present_files": ";".join(present),
                "missing_files": ";".join(missing),
                "ready": not missing,
                "requirements": item["requirements"],
            }
        )
    return rows


def run_verifier(command: list[str]) -> dict[str, object]:
    proc = subprocess.run(
        command,
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    parsed: object | None = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = None
    return {
        "command": " ".join(command),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "parsed": parsed,
    }


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parsed_status(result: dict[str, object]) -> tuple[object, object]:
    parsed = result.get("parsed")
    if isinstance(parsed, dict):
        return parsed.get("status"), parsed.get("reason")
    return None, None


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    v31 = load_json(V31)
    source_contact = load_json(SOURCE_CONTACT)
    native_request = load_json(NATIVE_REQUEST)
    stock_contact = load_json(STOCK_CONTACT)
    kaggle_refresh = load_json(KAGGLE_REFRESH)
    do_contact = load_json(DO_CONTACT)
    sapienza = load_json(SAPIENZA_GATE)

    source_label_result = run_verifier([
        "python3",
        str(SOURCE_LABEL_VERIFIER.relative_to(REPO)),
        "--intake-root",
        "/tmp/ict-engine-source-label-equivalence-intake",
    ])
    recency_result = run_verifier([
        "python3",
        str(RECENCY_VERIFIER.relative_to(REPO)),
        "--intake-root",
        "/tmp/ict-engine-source-panel-recency-extension",
    ])
    direct_result = run_verifier([
        "python3",
        str(DIRECT_VERIFIER.relative_to(REPO)),
        "--intake-root",
        "/tmp/ict-engine-direct-manipulation-row-intake",
    ])
    root_rows = intake_readback()

    source_status, source_reason = parsed_status(source_label_result)
    recency_status, recency_reason = parsed_status(recency_result)
    direct_status, direct_reason = parsed_status(direct_result)
    ready_roots = sum(1 for row in root_rows if row["ready"])
    unmet_ids = ["R2", "R3", "R4", "R5", "R6", "R8"]

    checklist = [
        {
            "id": "R0",
            "requirement": "Use the named Board A markdown as the execution contract and write results back there.",
            "status": "pass_checked",
            "artifact": str(BOARD.relative_to(REPO)),
            "evidence": "Board, v31 audit, R2 source-label equivalence contact leads, R3 native-subhour intake request package, and live intake roots were checked.",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "Every active regime has calibrated >=95% confidence.",
            "status": "pass_scoped_not_full",
            "artifact": str(SAPIENZA_GATE.relative_to(REPO)),
            "evidence": (
                "Scoped active-lane 95% evidence persists; Sapienza pump/dump has "
                f"{sapienza.get('event_groups', 317)} event groups and min Wilson LCB "
                f"{sapienza.get('min_split_wilson_lcb_95', '0.970640354706')}."
            ),
            "gap": "Still not strict full-market/full-cycle/full-species closure.",
        },
        {
            "id": "R2",
            "requirement": "The 95% regime result transfers to other markets/species using source-owned or owner-approved labels.",
            "status": "fail_blocked",
            "artifact": str(SOURCE_CONTACT.relative_to(REPO)),
            "evidence": (
                f"R2 contact leads={source_contact.get('contact_lead_count')}; "
                f"rows_acquired={source_contact.get('rows_acquired')}; "
                f"request_sent={source_contact.get('request_sent')}; "
                f"live source-label verifier status={source_status}/{source_reason}."
            ),
            "gap": "Contact/licensing surfaces are ready, but source-label equivalence rows/provenance remain absent.",
        },
        {
            "id": "R3",
            "requirement": "The 95% regime result transfers to other cycles/timeframes, including native sub-hour source labels.",
            "status": "fail_blocked",
            "artifact": str(NATIVE_REQUEST.relative_to(REPO)),
            "evidence": (
                f"R3 request targets={native_request.get('native_intraday_target_count')}; "
                f"focus blocker cells={native_request.get('focus_blocker_cell_count')}; "
                f"rows_acquired={native_request.get('rows_acquired')}; "
                f"intake_files_created={native_request.get('native_subhour_source_label_intake_files_created')}."
            ),
            "gap": "Native sub-hour request package is concrete, but no source-owned rows/provenance are present under the intake root.",
        },
        {
            "id": "R4",
            "requirement": "Strict exact 1h remaining slots have source-owned rows and provenance.",
            "status": "fail_blocked",
            "artifact": str(STOCK_CONTACT.relative_to(REPO)),
            "evidence": (
                f"Stock-regime contact leads={stock_contact.get('contact_lead_count')}; "
                f"rows_acquired={stock_contact.get('rows_acquired')}; "
                f"source_label_equivalence_intake_files_created={stock_contact.get('source_label_equivalence_intake_files_created')}; "
                f"source-label verifier status={source_status}/{source_reason}."
            ),
            "gap": "Contact paths exist, but strict exact 1h source-owned rows/provenance are not acquired.",
        },
        {
            "id": "R5",
            "requirement": "Strict 1h recency-tail targets after 2026-01-30 are repaired with source-owned labels.",
            "status": "fail_blocked",
            "artifact": str(KAGGLE_REFRESH.relative_to(REPO)),
            "evidence": (
                f"Kaggle refresh decision={kaggle_refresh.get('decision')}; "
                f"date_max={kaggle_refresh.get('csv_stats', {}).get('date_max')}; "
                f"post_cutoff_target_rows={kaggle_refresh.get('post_cutoff_target_rows')}; "
                f"recency verifier status={recency_status}/{recency_reason}."
            ),
            "gap": "Latest public Kaggle package still ends at 2026-01-30 and recency-extension files are absent.",
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation has source-owned row-level positives, matched controls, and provenance across required species.",
            "status": "partial_still_blocked",
            "artifact": str(DO_CONTACT.relative_to(REPO)),
            "evidence": (
                f"Do/Putnins contact leads={do_contact.get('contact_lead_count')}; "
                f"rows_acquired={do_contact.get('rows_acquired')}; "
                f"direct verifier status={direct_status}/{direct_reason}."
            ),
            "gap": "Pump/dump scoped gate persists, but spoofing/layering positive/control row packages are still missing.",
        },
        {
            "id": "R7",
            "requirement": "No proxy, generated, synthetic, future-return, duplicated, or OHLCV-only labels are promoted.",
            "status": "pass_guardrail",
            "artifact": str(V31.relative_to(REPO)),
            "evidence": "v32 preserves the fail-closed verifier results; request packages do not create labels, commit raw data, or relax thresholds.",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "Mark the goal complete only if every explicit requirement is covered by real evidence.",
            "status": "fail_blocked",
            "artifact": str(RUN_ROOT.relative_to(REPO)),
            "evidence": f"Unmet rows remain {', '.join(unmet_ids)}; ready intake roots={ready_roots}/4; accepted rows added since v31=0.",
            "gap": "Strict full objective is not achieved; update_goal must remain false.",
        },
    ]

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": (
            "For docs/plans/2026-05-10-actionable-regime-confidence-todo.md, "
            "each active regime needs >=95% calibrated confidence, and that "
            "confidence must validate across other markets/species and other "
            "cycles/timeframes using source-owned or owner-approved evidence "
            "before completion can be reported."
        ),
        "latest_artifacts_checked": [
            str(V31.relative_to(REPO)),
            str(SOURCE_CONTACT.relative_to(REPO)),
            str(NATIVE_REQUEST.relative_to(REPO)),
            str(STOCK_CONTACT.relative_to(REPO)),
            str(KAGGLE_REFRESH.relative_to(REPO)),
            str(DO_CONTACT.relative_to(REPO)),
        ],
        "prior_v31_decision": v31.get("decision"),
        "live_verifier_readbacks": {
            "source_label_equivalence": source_label_result,
            "recency_extension": recency_result,
            "direct_manipulation": direct_result,
            "intake_roots": root_rows,
        },
        "checklist_rows": checklist,
        "unmet_requirement_ids": unmet_ids,
        "ready_intake_roots": ready_roots,
        "decision": "current_goal_completion_audit_v32=request_packages_ready_rows_not_acquired_blocked",
        "accepted_rows_added_since_v31": 0,
        "new_confidence_gate_since_v31": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    (OUT_DIR / "current_goal_completion_audit_v32_after_r2_r3_request_packages.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(
        OUT_DIR / "current_goal_completion_audit_v32_checklist.csv",
        checklist,
        ["id", "requirement", "status", "artifact", "evidence", "gap"],
    )
    write_csv(
        OUT_DIR / "current_goal_completion_audit_v32_unmet_requirements.csv",
        [row for row in checklist if str(row["id"]) in unmet_ids],
        ["id", "requirement", "status", "artifact", "evidence", "gap"],
    )
    write_csv(
        OUT_DIR / "current_goal_completion_audit_v32_intake_roots.csv",
        root_rows,
        ["id", "root", "exists", "required_files", "present_files", "missing_files", "ready", "requirements"],
    )

    report_lines = [
        "# Current Goal Completion Audit v32 After R2/R3 Request Packages",
        "",
        f"- Decision: `{payload['decision']}`",
        f"- Unmet requirement ids: `{', '.join(unmet_ids)}`",
        f"- R2 contact leads: `{source_contact.get('decision')}`; rows acquired `{str(source_contact.get('rows_acquired')).lower()}`",
        f"- R3 native-subhour request package: `{native_request.get('decision')}`; targets `{native_request.get('native_intraday_target_count')}`; focus cells `{native_request.get('focus_blocker_cell_count')}`",
        f"- Ready intake roots: `{ready_roots}/4`",
        "- Accepted rows added since v31: `0`; new confidence gate since v31: `false`",
        "- Strict full objective achieved: `false`; `update_goal=false`",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`",
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| ID | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        report_lines.append(
            f"| `{row['id']}` | `{row['status']}` | {row['evidence']} | {row['gap']} |"
        )
    report_lines.extend(
        [
            "",
            "## Intake Roots",
            "",
            "| ID | Ready | Missing Files |",
            "|---|---:|---|",
        ]
    )
    for row in root_rows:
        report_lines.append(
            f"| `{row['id']}` | `{str(row['ready']).lower()}` | `{row['missing_files']}` |"
        )
    report_lines.extend(
        [
            "",
            "## Decision",
            "",
            "R2 and R3 now have concrete acquisition/request packages, but neither package contains acquired source-owned rows. The four fail-closed intake roots remain incomplete, so the strict objective remains blocked and the goal must not be marked complete.",
            "",
        ]
    )
    (OUT_DIR / "current_goal_completion_audit_v32_after_r2_r3_request_packages.md").write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    assertions = [
        ("board_present", BOARD.exists()),
        ("v31_json_present", V31.exists()),
        ("source_contact_present", SOURCE_CONTACT.exists()),
        ("native_request_present", NATIVE_REQUEST.exists()),
        ("source_contact_rows_not_acquired", source_contact.get("rows_acquired") is False),
        ("native_request_rows_not_acquired", native_request.get("rows_acquired") is False),
        ("native_request_target_count_336", native_request.get("native_intraday_target_count") == 336),
        ("native_request_focus_cells_4", native_request.get("focus_blocker_cell_count") == 4),
        ("ready_intake_roots_zero", ready_roots == 0),
        ("source_label_verifier_blocked", source_status == "blocked"),
        ("recency_verifier_blocked", recency_status == "blocked"),
        ("direct_verifier_blocked", direct_status == "blocked"),
        ("strict_full_objective_false", payload["strict_full_objective_achieved"] is False),
        ("update_goal_false", payload["update_goal"] is False),
        ("raw_data_committed_false", payload["raw_data_committed"] is False),
    ]
    failed = [name for name, ok in assertions if not ok]
    (CHECK_DIR / "current_goal_completion_audit_v32_after_r2_r3_request_packages_assertions.out").write_text(
        "\n".join(f"{name}=PASS" if ok else f"{name}=FAIL" for name, ok in assertions)
        + "\n",
        encoding="utf-8",
    )
    if failed:
        raise SystemExit(f"failed assertions: {', '.join(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
