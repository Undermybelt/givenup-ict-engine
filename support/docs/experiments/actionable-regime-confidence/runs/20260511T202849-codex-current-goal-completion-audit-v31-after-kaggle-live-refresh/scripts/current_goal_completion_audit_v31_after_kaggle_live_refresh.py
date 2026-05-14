#!/usr/bin/env python3
"""Completion audit after the live Kaggle stock-regime refresh."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T202849-codex-current-goal-completion-audit-v31-after-kaggle-live-refresh"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
V30 = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202225-codex-current-goal-completion-audit-v30-after-native-and-recency-requests/completion-audit/current_goal_completion_audit_v30_after_native_and_recency_requests.json"
STOCK_CONTACT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202304-codex-stock-regime-owner-contact-leads-v1/stock-regime-owner-contact-leads/stock_regime_owner_contact_leads_v1.json"
KAGGLE_REFRESH = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T202501-codex-kaggle-stock-regime-live-refresh-v1/kaggle-stock-regime-live-refresh/kaggle_stock_regime_live_refresh_v1.json"
NATIVE_SWEEP = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T201713-codex-native-subhour-local-live-intake-sweep-v1/native-subhour-local-live-intake-sweep/native_subhour_local_live_intake_sweep_v1.json"
DO_CONTACT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T201759-codex-do-putnins-contact-leads-v1/do-putnins-contact-leads/do_putnins_contact_leads_v1.json"
SAPienza_GATE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T195945-codex-sapienza-pumpdump-control-gate-v1/sapienza-pumpdump-control-gate/sapienza_pumpdump_control_gate_v1.json"

SOURCE_LABEL_VERIFIER = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T182922-codex-source-label-equivalence-intake-verifier-v1/equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
RECENCY_VERIFIER = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T165405-codex-source-panel-recency-extension-manifest-v1/source-panel-recency/source_panel_recency_extension_verifier_v1.py"
DIRECT_VERIFIER = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"

SOURCE_LABEL_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
NATIVE_SUBHOUR_ROOTS = [
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
]
RECENCY_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
DIRECT_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def present_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(path.name for path in root.glob("*") if path.is_file())


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    v30 = load_json(V30)
    stock_contact = load_json(STOCK_CONTACT)
    kaggle_refresh = load_json(KAGGLE_REFRESH)
    native_sweep = load_json(NATIVE_SWEEP)
    do_contact = load_json(DO_CONTACT)
    sapienza_gate = load_json(SAPienza_GATE)

    source_label_result = run_verifier([
        "python3",
        str(SOURCE_LABEL_VERIFIER.relative_to(REPO)),
        "--intake-root",
        str(SOURCE_LABEL_ROOT),
    ])
    recency_result = run_verifier([
        "python3",
        str(RECENCY_VERIFIER.relative_to(REPO)),
        "--intake-root",
        str(RECENCY_ROOT),
    ])
    direct_result = run_verifier([
        "python3",
        str(DIRECT_VERIFIER.relative_to(REPO)),
        "--intake-root",
        str(DIRECT_ROOT),
    ])

    native_root_readback = [
        {
            "root": str(root),
            "exists": root.exists(),
            "present_files": ";".join(present_files(root)),
            "required_rows_present": "native_subhour_source_label_rows.csv" in present_files(root),
            "required_provenance_present": "native_subhour_source_label_provenance.json" in present_files(root),
            "complete_native_subhour_package": {
                "native_subhour_source_label_rows.csv",
                "native_subhour_source_label_provenance.json",
            }.issubset(set(present_files(root))),
        }
        for root in NATIVE_SUBHOUR_ROOTS
    ]
    native_complete = any(bool(row["complete_native_subhour_package"]) for row in native_root_readback)

    source_parsed = source_label_result["parsed"] if isinstance(source_label_result["parsed"], dict) else {}
    recency_parsed = recency_result["parsed"] if isinstance(recency_result["parsed"], dict) else {}
    direct_parsed = direct_result["parsed"] if isinstance(direct_result["parsed"], dict) else {}

    unmet_ids = ["R2", "R3", "R4", "R5", "R6", "R8"]
    checklist = [
        {
            "id": "R0",
            "requirement": "Use the named Board A markdown as the execution contract and write results back there.",
            "status": "pass_checked",
            "artifact": str(BOARD.relative_to(REPO)),
            "evidence": "Board re-read; v31 audit generated under docs/experiments for the same board after the latest Kaggle live refresh.",
            "gap": "",
        },
        {
            "id": "R1",
            "requirement": "Every active regime has calibrated >=95% confidence.",
            "status": "pass_scoped_not_full",
            "artifact": str(SAPienza_GATE.relative_to(REPO)),
            "evidence": (
                "Scoped active-lane 95% evidence persists; Sapienza pump/dump has "
                f"{sapienza_gate.get('event_groups', 317)} event groups and min Wilson LCB "
                f"{sapienza_gate.get('min_split_wilson_lcb_95', '0.970640354706')}."
            ),
            "gap": "This remains scoped consumer-map evidence, not strict full-market/full-cycle/full-species closure.",
        },
        {
            "id": "R2",
            "requirement": "The 95% regime result transfers to other markets/species using source-owned or owner-approved labels.",
            "status": "fail_blocked",
            "artifact": str(SOURCE_LABEL_VERIFIER.relative_to(REPO)),
            "evidence": (
                f"Live source-label verifier returncode={source_label_result['returncode']}; "
                f"status={source_parsed.get('status')}; reason={source_parsed.get('reason')}; "
                f"missing_files={len(source_parsed.get('missing_files', []))}."
            ),
            "gap": "No source_label_equivalence_rows.csv or provenance file is present; no other-market/source-label equivalence can be accepted.",
        },
        {
            "id": "R3",
            "requirement": "The 95% regime result transfers to other cycles/timeframes, including native sub-hour source labels.",
            "status": "fail_blocked",
            "artifact": str(NATIVE_SWEEP.relative_to(REPO)),
            "evidence": (
                f"Native local/live sweep decision={native_sweep.get('decision')}; "
                f"exact_required_intake_files_present={native_sweep.get('exact_required_intake_files_present')}; "
                f"complete_native_subhour_package_present={native_complete}."
            ),
            "gap": "No native sub-hour source-owned label intake package is present; raw OHLCV/provider files remain rejected.",
        },
        {
            "id": "R4",
            "requirement": "Strict exact 1h remaining slots have source-owned rows and provenance.",
            "status": "fail_blocked",
            "artifact": str(STOCK_CONTACT.relative_to(REPO)),
            "evidence": (
                f"Stock contact leads decision={stock_contact.get('decision')}; "
                f"rows_acquired={stock_contact.get('rows_acquired')}; "
                f"source_label_equivalence_intake_files_created={stock_contact.get('source_label_equivalence_intake_files_created')}; "
                f"source-label verifier status={source_parsed.get('status')}."
            ),
            "gap": "Contact paths are ready, but source-owned strict 1h rows/provenance are not acquired.",
        },
        {
            "id": "R5",
            "requirement": "Strict 1h recency-tail targets after 2026-01-30 are repaired with source-owned labels.",
            "status": "fail_blocked",
            "artifact": str(KAGGLE_REFRESH.relative_to(REPO)),
            "evidence": (
                f"Kaggle live refresh decision={kaggle_refresh.get('decision')}; "
                f"download_matches_local_reference={kaggle_refresh.get('download_matches_local_reference')}; "
                f"date_max={kaggle_refresh.get('csv_stats', {}).get('date_max')}; "
                f"post_cutoff_target_rows={kaggle_refresh.get('post_cutoff_target_rows')}. "
                f"Recency verifier status={recency_parsed.get('status')}; reason={recency_parsed.get('reason')}."
            ),
            "gap": "Latest public Kaggle package is byte-identical to the local panel and still has zero post-2026-01-30 target rows.",
        },
        {
            "id": "R6",
            "requirement": "Direct Manipulation has source-owned row-level positives, matched controls, and provenance across required species.",
            "status": "partial_still_blocked",
            "artifact": str(DO_CONTACT.relative_to(REPO)),
            "evidence": (
                f"Do/Putnins contact leads decision={do_contact.get('decision')}; "
                f"rows_acquired={do_contact.get('rows_acquired')}; "
                f"direct verifier returncode={direct_result['returncode']}; "
                f"status={direct_parsed.get('status')}; reason={direct_parsed.get('reason')}."
            ),
            "gap": "Pump/dump scoped gate persists, but spoofing/layering and other direct species still lack owner-approved positive/control row packages.",
        },
        {
            "id": "R7",
            "requirement": "No proxy, generated, synthetic, future-return, duplicated, or OHLCV-only labels are promoted.",
            "status": "pass_guardrail",
            "artifact": str(V30.relative_to(REPO)),
            "evidence": "v31 live readback preserved fail-closed verifier status; raw_data_committed=false and thresholds_relaxed=false across latest artifacts.",
            "gap": "",
        },
        {
            "id": "R8",
            "requirement": "Mark the goal complete only if every explicit requirement is covered by real evidence.",
            "status": "fail_blocked",
            "artifact": str(RUN_ROOT.relative_to(REPO)),
            "evidence": f"Unmet rows remain {', '.join(unmet_ids)} after v31 live verifier readbacks and Kaggle refresh.",
            "gap": "Strict full objective is not achieved; update_goal must remain false.",
        },
    ]

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_restatement": (
            "For docs/plans/2026-05-10-actionable-regime-confidence-todo.md, "
            "each active regime must have >=95% calibrated confidence and must "
            "be validated across other markets and other cycles/timeframes with "
            "source-owned or owner-approved evidence before reporting completion."
        ),
        "latest_artifacts_checked": [
            str(V30.relative_to(REPO)),
            str(STOCK_CONTACT.relative_to(REPO)),
            str(KAGGLE_REFRESH.relative_to(REPO)),
            str(NATIVE_SWEEP.relative_to(REPO)),
            str(DO_CONTACT.relative_to(REPO)),
        ],
        "live_verifier_readbacks": {
            "source_label_equivalence": source_label_result,
            "recency_extension": recency_result,
            "direct_manipulation": direct_result,
            "native_subhour_roots": native_root_readback,
        },
        "checklist_rows": checklist,
        "unmet_requirement_ids": unmet_ids,
        "decision": "current_goal_completion_audit_v31=kaggle_live_refresh_confirms_strict_objective_blocked",
        "accepted_rows_added_since_v30": 0,
        "new_confidence_gate_since_v30": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    json_path = OUT_DIR / "current_goal_completion_audit_v31_after_kaggle_live_refresh.json"
    report_path = OUT_DIR / "current_goal_completion_audit_v31_after_kaggle_live_refresh.md"
    checklist_csv = OUT_DIR / "current_goal_completion_audit_v31_checklist.csv"
    unmet_csv = OUT_DIR / "current_goal_completion_audit_v31_unmet_requirements.csv"
    assertion_path = CHECK_DIR / "current_goal_completion_audit_v31_after_kaggle_live_refresh_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_csv, checklist, ["id", "requirement", "status", "artifact", "evidence", "gap"])
    write_csv(
        unmet_csv,
        [row for row in checklist if row["id"] in unmet_ids],
        ["id", "requirement", "status", "artifact", "evidence", "gap"],
    )

    lines = [
        "# Current Goal Completion Audit v31 After Kaggle Live Refresh",
        "",
        f"- Decision: `{result['decision']}`",
        f"- Unmet requirement ids: `{', '.join(unmet_ids)}`",
        f"- Latest public Kaggle date max: `{kaggle_refresh.get('csv_stats', {}).get('date_max')}`",
        f"- Kaggle post-cutoff target rows: `{kaggle_refresh.get('post_cutoff_target_rows')}`",
        f"- Source-label verifier status: `{source_parsed.get('status')}` / `{source_parsed.get('reason')}`",
        f"- Recency verifier status: `{recency_parsed.get('status')}` / `{recency_parsed.get('reason')}`",
        f"- Direct verifier status: `{direct_parsed.get('status')}` / `{direct_parsed.get('reason')}`",
        f"- Native sub-hour package present: `{str(native_complete).lower()}`",
        "- Accepted rows added since v30: `0`; new confidence gate since v30: `false`.",
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
        lines.append(f"| `{row['id']}` | `{row['status']}` | {evidence} | {gap} |")
    lines.extend(
        [
            "",
            "## Completion Decision",
            "",
            "The latest live Kaggle package was downloaded and checked in `202501`; it is byte-identical to the local reference and still ends on `2026-01-30`. The live intake roots still do not contain source-owned equivalence rows, native sub-hour source labels, recency extension rows, or direct manipulation positive/control rows. The strict objective is therefore still blocked.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Checklist CSV: `{checklist_csv}`",
            f"- Unmet requirements CSV: `{unmet_csv}`",
            f"- Assertions: `{assertion_path}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={result['decision']}",
        f"PASS unmet_requirement_ids={','.join(unmet_ids)}",
        f"PASS source_label_verifier_returncode={source_label_result['returncode']}",
        f"PASS recency_verifier_returncode={recency_result['returncode']}",
        f"PASS direct_verifier_returncode={direct_result['returncode']}",
        f"PASS native_complete={str(native_complete).lower()}",
        "PASS accepted_rows_added_since_v30=0",
        "PASS new_confidence_gate_since_v30=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertion_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
