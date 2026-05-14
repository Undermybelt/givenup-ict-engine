#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260512T084809+0800-codex-current-objective-audit-after-083559-083703-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "current-objective-audit-after-083559-083703-v1"
CHECK_DIR = RUN_ROOT / "checks"

BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"

ASSERTION_FILES = {
    "082430_runtime_readiness": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T082430+0800-codex-runtime-readiness-after-082215-v1/checks/runtime_readiness_after_082215_v1_assertions.out",
    "083108_arrival_poll": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T083108+0800-codex-source-control-arrival-poll-after-082720-v1/checks/source_control_arrival_poll_after_082720_v1_assertions.out",
    "083447_current_objective_audit": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T083447+0800-codex-current-objective-audit-after-083108-v1/checks/current_objective_audit_after_083108_v1_assertions.out",
    "083545_dispatch_channel": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T083545+0800-codex-r6-approved-dispatch-channel-readback-after-083108-v1/checks/r6_approved_dispatch_channel_readback_after_083108_v1_assertions.out",
    "083559_source_sweep": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T083559+0800-codex-local-order-lifecycle-source-sweep-after-083108-v1/checks/local_order_lifecycle_source_sweep_after_083108_v1_assertions.out",
    "083618_tomac_header_inventory": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T083618+0800-codex-tomac-futures-header-inventory-after-083108-v1/checks/tomac_futures_header_inventory_after_083108_v1_assertions.out",
    "083703_zip_header_sweep": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T083703+0800-codex-local-order-lifecycle-zip-header-sweep-after-083450-v1/checks/local_order_lifecycle_zip_header_sweep_after_083450_v1_assertions.out",
}


def parse_assertions(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        data["missing"] = "true"
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def file_sha1(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def bool_value(values: dict[str, str], key: str) -> bool:
    return values.get(key, "").lower() == "true"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    assertions = {name: parse_assertions(path) for name, path in ASSERTION_FILES.items()}
    missing_assertions = [name for name, values in assertions.items() if values.get("missing") == "true"]

    runtime = assertions["082430_runtime_readiness"]
    arrival = assertions["083108_arrival_poll"]
    prior_audit = assertions["083447_current_objective_audit"]
    dispatch = assertions["083545_dispatch_channel"]
    source_sweep = assertions["083559_source_sweep"]
    header_inventory = assertions["083618_tomac_header_inventory"]
    zip_sweep = assertions["083703_zip_header_sweep"]

    checklist = [
        {
            "requirement_id": "R1",
            "requirement": "Every active regime has calibrated confidence >=95 percent.",
            "status": "blocked",
            "evidence": rel(ASSERTION_FILES["083447_current_objective_audit"]),
            "finding": "Prior audit remains strict_full_objective=false and accepted_rows_added=0.",
            "gap": "No new accepted regime-confidence rows arrived after 083108.",
        },
        {
            "requirement_id": "R2",
            "requirement": "Accepted regimes transfer to other markets.",
            "status": "blocked",
            "evidence": rel(ASSERTION_FILES["083447_current_objective_audit"]),
            "finding": "Prior audit remains source_control_evidence_acquired=false.",
            "gap": "Other-market validation still lacks source-owned or owner-approved labels/controls.",
        },
        {
            "requirement_id": "R3",
            "requirement": "Accepted regimes transfer to other timeframes or cycles.",
            "status": "blocked",
            "evidence": rel(ASSERTION_FILES["083108_arrival_poll"]) + "; " + rel(ASSERTION_FILES["083559_source_sweep"]),
            "finding": "R3 native-subhour roots are present, and 083559 reports exact_required_packages=2, but both artifacts keep r3/native unlock and valid_required_root_unlock false.",
            "gap": "Native-subhour files remain non-promoting without accepted source/control package or approval.",
        },
        {
            "requirement_id": "R4",
            "requirement": "Use real Auto-Quant and ict-engine chain through filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution tree.",
            "status": "partial_blocked",
            "evidence": rel(ASSERTION_FILES["082430_runtime_readiness"]),
            "finding": "Runtime readiness ran 9/9 commands exit zero, but selected_data_autoquant_promotion=false and downstream_promotion_rerun=false.",
            "gap": "The ordered promotion chain is intentionally blocked until source/control and selected-history gates are true.",
        },
        {
            "requirement_id": "R5",
            "requirement": "Provider coverage includes IBKR, TradingViewRemix, yfinance, and Kraken.",
            "status": "covered_non_promoting",
            "evidence": rel(ASSERTION_FILES["082430_runtime_readiness"]),
            "finding": "provider_surface_mentions_all=true and all four provider names are visible.",
            "gap": "Provider visibility is readiness evidence only, not source/control evidence.",
        },
        {
            "requirement_id": "R6",
            "requirement": "R6 owner-export/source-control package supplies positives, matched normal controls, and provenance.",
            "status": "blocked",
            "evidence": rel(ASSERTION_FILES["083545_dispatch_channel"]) + "; " + rel(ASSERTION_FILES["083703_zip_header_sweep"]),
            "finding": "Dispatch drafts are present but not sent, no ticket/export/license provenance exists, and 083703 found exact_required_package_present=false.",
            "gap": "R6 owner/export roots remain absent and no matched normal controls are acquired.",
        },
        {
            "requirement_id": "R7",
            "requirement": "Local Tomac archives can unlock source/control if they contain verifier-native order-lifecycle rows.",
            "status": "blocked",
            "evidence": rel(ASSERTION_FILES["083559_source_sweep"]) + "; " + rel(ASSERTION_FILES["083618_tomac_header_inventory"]),
            "finding": "083559 found verifier_native_candidate_files=70 but valid_required_root_unlock=false; 083618 found order-lifecycle header hits=0 and source/control package hits=0.",
            "gap": "Local hits are symbology/OHLCV/header context, not accepted positive/control/provenance packages.",
        },
        {
            "requirement_id": "R8",
            "requirement": "Selected historical path exists before selected-data AutoQuant.",
            "status": "blocked",
            "evidence": rel(ASSERTION_FILES["083447_current_objective_audit"]) + "; " + rel(ASSERTION_FILES["082430_runtime_readiness"]),
            "finding": "explicit_user_selected_history=false in the current objective audit and runtime readiness readback.",
            "gap": "No HTF/MTF/LTF path has been explicitly selected for selected-data promotion.",
        },
        {
            "requirement_id": "R9",
            "requirement": "Do not disturb multi-agent board work and do not claim completion prematurely.",
            "status": "covered",
            "evidence": rel(BOARD_A) + "; " + rel(BOARD_B),
            "finding": "This audit is append-only, does not edit Current Cursor, and update_goal remains false.",
            "gap": "N/A",
        },
    ]

    blocked = sum(1 for row in checklist if row["status"] == "blocked")
    partial = sum(1 for row in checklist if row["status"] == "partial_blocked")
    covered = sum(1 for row in checklist if row["status"].startswith("covered"))

    summary = {
        "run_id": RUN_ID,
        "gate_result": "current_objective_audit_after_083559_083703_v1=not_complete_source_control_and_selected_history_absent_no_downstream_promotion",
        "objective": "Every regime reaches >=95% confidence and validates across other markets and timeframes/cycles, using real Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree evidence with IBKR, TradingViewRemix, yfinance, and Kraken visibility.",
        "board_a_sha1_before_artifact": file_sha1(BOARD_A),
        "board_b_sha1_before_artifact": file_sha1(BOARD_B),
        "missing_assertion_files": missing_assertions,
        "covered_requirements": covered,
        "partial_requirements": partial,
        "blocked_requirements": blocked,
        "accepted_rows_added": 0,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "explicit_user_selected_history": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
        "next_action": "Continue source/control acquisition only: send or satisfy the v5 CME/Cboe/CFE owner-export requests with ticket/export/license provenance and matched controls, or get explicit same-exhibit FLIP-as-control approval; then select exactly one historical path before any selected-data AutoQuant/downstream promotion.",
        "assertion_sources": {name: rel(path) for name, path in ASSERTION_FILES.items()},
        "key_readbacks": {
            "provider_surface_mentions_all": runtime.get("provider_surface_mentions_all"),
            "commands_run": runtime.get("commands_run"),
            "commands_exit0": runtime.get("commands_exit0"),
            "r6_owner_export_roots_present": arrival.get("r6_owner_export_roots_present"),
            "r5_recency_roots_present": arrival.get("r5_recency_roots_present"),
            "r3_native_subhour_roots_present": arrival.get("r3_native_subhour_roots_present"),
            "approved_dispatch_channel_present": dispatch.get("approved_dispatch_channel_present"),
            "dispatch_ticket_export_license_provenance_present": dispatch.get("dispatch_ticket_export_license_provenance_present"),
            "083559_exact_required_packages": source_sweep.get("exact_required_packages"),
            "083559_valid_required_root_unlock": source_sweep.get("valid_required_root_unlock"),
            "083703_order_lifecycle_candidate_rows": zip_sweep.get("order_lifecycle_candidate_rows"),
            "083703_exact_required_package_present": zip_sweep.get("exact_required_package_present"),
            "083618_order_lifecycle_header_hits": header_inventory.get("order_lifecycle_header_hits"),
        },
    }

    json_path = OUT_DIR / "current_objective_audit_after_083559_083703_v1.json"
    md_path = OUT_DIR / "current_objective_audit_after_083559_083703_v1.md"
    checklist_path = OUT_DIR / "prompt_to_artifact_checklist_after_083559_083703_v1.csv"
    assertion_roots_path = OUT_DIR / "counted_assertion_roots_after_083559_083703_v1.csv"
    assertions_path = CHECK_DIR / "current_objective_audit_after_083559_083703_v1_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with checklist_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["requirement_id", "requirement", "status", "evidence", "finding", "gap"],
        )
        writer.writeheader()
        writer.writerows(checklist)

    with assertion_roots_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "path", "exists", "gate_result"])
        writer.writeheader()
        for name, path in ASSERTION_FILES.items():
            writer.writerow(
                {
                    "id": name,
                    "path": rel(path),
                    "exists": path.exists(),
                    "gate_result": assertions[name].get("gate_result", ""),
                }
            )

    md_lines = [
        "# Current Objective Audit After 083559 / 083703 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{summary['gate_result']}`",
        "",
        "## Objective Restatement",
        "",
        summary["objective"],
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| id | status | evidence | finding | gap |",
        "|---|---|---|---|---|",
    ]
    for row in checklist:
        md_lines.append(
            f"| `{row['requirement_id']}` | `{row['status']}` | `{row['evidence']}` | {row['finding']} | {row['gap']} |"
        )
    md_lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Covered requirements: `{covered}`.",
            f"- Partial requirements: `{partial}`.",
            f"- Blocked requirements: `{blocked}`.",
            "- Accepted rows added: `0`.",
            "- Valid required-root unlock: `false`.",
            "- Source/control evidence acquired: `false`.",
            "- Explicit user-selected history: `false`.",
            "- Canonical merge: `false`.",
            "- Selected-data AutoQuant promotion: `false`.",
            "- Downstream promotion rerun: `false`.",
            "- Strict full objective: `false`.",
            "- Trade usable: `false`.",
            "- Promotion allowed: `false`.",
            "- `update_goal=false`.",
            "",
            "## Next",
            "",
            summary["next_action"],
        ]
    )
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"gate_result={summary['gate_result']}",
        f"covered_requirements={covered}",
        f"partial_requirements={partial}",
        f"blocked_requirements={blocked}",
        "accepted_rows_added=0",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "explicit_user_selected_history=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")

    print(f"wrote {rel(md_path)}")
    print(f"wrote {rel(json_path)}")
    print(f"wrote {rel(checklist_path)}")
    print(f"wrote {rel(assertion_roots_path)}")
    print(f"wrote {rel(assertions_path)}")


if __name__ == "__main__":
    main()
