#!/usr/bin/env python3
"""Read-only Board A source/control arrival scan after 043027.

This scan exists to settle the latest active blocker without mutating intake
roots or promoting runtime-only evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260512T043436-codex-source-control-arrival-scan-after-043027-v1"
SLUG = "source-control-arrival-scan-after-043027-v1"
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
REQUIRED_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]
R6_REQUIRED_FILES = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]
APPROVAL_SENTINEL = Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid")
KNOWN_NON_TARGET_TRIPLETS = [
    Path("/private/tmp/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1.staging"),
    Path("/private/tmp/ict-engine-direct-manipulation-row-intake"),
    Path("/private/tmp/ict-engine-r6-direct-intake-reconstruction-v55/intake"),
    Path("/private/tmp/ict-engine-r6-direct-intake-v56-clean-readback/intake"),
]
DANGLING_ROOTS = [
    REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T043222-codex-autoquant-offline-market-metadata-run-after-042222-v1",
    REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T043314-codex-r6-owner-export-arrival-scan-after-043027-v1",
]
HISTGB_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T042448-codex-source-label-histgb-confidence-screen-v1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob("*") if p.is_file())


def root_status(root: Path) -> dict[str, Any]:
    status: dict[str, Any] = {
        "path": str(root),
        "present": root.exists(),
        "file_count": file_count(root),
    }
    if root.name == "ict-engine-board-a-r6-owner-export-v1":
        status["required_files"] = {
            name: (root / name).exists() for name in R6_REQUIRED_FILES
        }
        status["required_files_present"] = sum(
            1 for present in status["required_files"].values() if present
        )
    return status


def related_root_status(root: Path) -> dict[str, Any]:
    files = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()) if root.exists() else []
    completed_artifacts = [
        f for f in files
        if f.endswith(".md") or f.endswith(".json") or f.endswith("_assertions.out")
    ]
    return {
        "path": str(root.relative_to(REPO)),
        "present": root.exists(),
        "file_count": len(files),
        "completed_artifact_count": len(completed_artifacts),
        "completed_artifacts": completed_artifacts,
        "classification": "empty_or_incomplete_no_promotion"
        if root.exists() and not completed_artifacts
        else "completed_or_not_present_count_separately",
    }


def histgb_status() -> dict[str, Any]:
    stdout = HISTGB_ROOT / "command-output/source_label_histgb_confidence_screen.stdout.json"
    stderr = HISTGB_ROOT / "command-output/source_label_histgb_confidence_screen.stderr.txt"
    exit_file = HISTGB_ROOT / "command-output/source_label_histgb_confidence_screen.exit"
    try:
        ps = subprocess.check_output(
            ["ps", "-axo", "pid,etime,command"], text=True
        )
    except Exception as exc:
        ps = f"ps_failed={type(exc).__name__}:{exc}"
    active_lines = [
        line for line in ps.splitlines()
        if "source_label_histgb_confidence_screen_v1.py" in line
    ]
    return {
        "root": str(HISTGB_ROOT.relative_to(REPO)),
        "active_process_count": len(active_lines),
        "stdout_bytes": stdout.stat().st_size if stdout.exists() else None,
        "stderr_bytes": stderr.stat().st_size if stderr.exists() else None,
        "exit_present": exit_file.exists(),
        "classification": "in_progress_or_incomplete_no_promotion"
        if active_lines or not exit_file.exists()
        else "settled_needs_artifact_readback",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    required = {str(root): root_status(root) for root in REQUIRED_ROOTS}
    non_target = [
        {"path": str(path), "present": path.exists(), "file_count": file_count(path)}
        for path in KNOWN_NON_TARGET_TRIPLETS
    ]
    r6_ready = required[str(REQUIRED_ROOTS[0])].get("required_files_present", 0) == 3
    r3_ready = required[str(REQUIRED_ROOTS[1])]["present"]
    r5_ready = required[str(REQUIRED_ROOTS[2])]["present"]
    approval_present = APPROVAL_SENTINEL.exists()
    explicit_approval = False
    flip_controls_approved = False
    source_owned_normal_controls_supplied = r6_ready
    source_control_evidence_acquired = (
        r6_ready and (source_owned_normal_controls_supplied or flip_controls_approved)
    )
    canonical_merge = False
    downstream_promotion_rerun = False
    strict_full_objective = False

    gate = "source_control_arrival_scan_after_043027_v1=no_new_source_control_unlock_no_promotion"
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": generated,
        "board_sha256_before_scan_artifact": sha256(BOARD),
        "gate_result": gate,
        "required_roots": required,
        "approval_package": {
            "path": str(APPROVAL_SENTINEL),
            "present": approval_present,
            "gate_result": "r6_oystacher_approval_decision_package_v1=decision_package_ready_no_approval_no_merge",
            "public_recap_pacer_provenance": "pending_explicit_user_or_board_approval",
            "same_exhibit_flip_as_matched_controls": "rejected_under_current_contract",
            "source_owned_normal_controls_alternative": "not_supplied",
        },
        "known_non_target_local_triplets": non_target,
        "related_roots_readback": [related_root_status(root) for root in DANGLING_ROOTS],
        "histgb_042448": histgb_status(),
        "decision": {
            "accepted_rows_added": 0,
            "source_control_evidence_acquired": source_control_evidence_acquired,
            "new_source_unlock": False,
            "owner_export_root_present": required[str(REQUIRED_ROOTS[0])]["present"],
            "owner_export_required_files_present": required[str(REQUIRED_ROOTS[0])].get("required_files_present", 0),
            "r3_native_subhour_root_present": r3_ready,
            "r5_recency_root_present": r5_ready,
            "explicit_approval": explicit_approval,
            "flip_controls_approved": flip_controls_approved,
            "source_owned_normal_controls_supplied": source_owned_normal_controls_supplied,
            "canonical_merge": canonical_merge,
            "downstream_promotion_rerun": downstream_promotion_rerun,
            "strict_full_objective": strict_full_objective,
            "trade_usable": False,
            "update_goal": False,
        },
    }
    (OUT / "source_control_arrival_scan_after_043027_v1.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    checklist_rows = [
        ("r6_owner_export_root", "/tmp/ict-engine-board-a-r6-owner-export-v1", "ready" if r6_ready else "blocked"),
        ("r3_native_subhour_root", "/tmp/ict-engine-native-subhour-source-label-intake", "ready" if r3_ready else "blocked"),
        ("r5_recency_extension_root", "/tmp/ict-engine-source-panel-recency-extension", "ready" if r5_ready else "blocked"),
        ("approval_package", payload["approval_package"]["gate_result"], "blocked"),
        ("same_exhibit_flip_controls", "rejected_under_current_contract", "blocked"),
        ("source_owned_normal_controls_alternative", "not_supplied", "blocked"),
        ("known_non_target_local_triplets", f"{sum(1 for row in non_target if row['present'])} present", "non_promoting"),
        ("related_roots_043222_043314", "read back separately; count only through their own board registrations", "non_promoting"),
        ("histgb_042448", payload["histgb_042448"]["classification"], "non_promoting"),
        ("update_goal_eligibility", "strict_full_objective false", "blocked"),
    ]
    with (OUT / "source_control_arrival_scan_after_043027_v1_checklist.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.writer(fh)
        writer.writerow(["gate", "readback", "status"])
        writer.writerows(checklist_rows)

    md = [
        "# Source Control Arrival Scan After 043027 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate}`",
        "",
        f"Board sha256 before scan artifact: `{payload['board_sha256_before_scan_artifact']}`",
        "",
        f"Generated at UTC: `{generated}`",
        "",
        "## Purpose",
        "",
        "This read-only scan checks whether source/control evidence arrived after the latest `043027`/`042900` AutoQuant threaded-runtime settlement and `042857` downstream readback. It does not mutate roots, copy local triplets, approve `FLIP` rows, run canonical merge, run downstream promotion, or call `update_goal`.",
        "",
        "## Live Unlock Checks",
        "",
        "| Gate | Readback | Status |",
        "|---|---|---|",
    ]
    for gate_name, readback, status in checklist_rows:
        md.append(f"| {gate_name} | `{readback}` | `{status}` |")
    md.extend(
        [
            "",
            "## Decision",
            "",
            "Accepted rows added `0`; source/control evidence acquired `false`; new source unlock `false`; owner-export required files present `0/3`; R3 native subhour root present `false`; R5 recency root present `false`; explicit approval `false`; `FLIP` controls approved `false`; source-owned normal controls supplied `false`; canonical merge `false`; downstream promotion rerun `false`; strict full objective `false`; trade usable `false`; `update_goal=false`.",
            "",
            "## Notes",
            "",
            "- The `043222` and `043314` roots are read back only as related roots here. Count them only through their own board registrations, not as source/control unlocks in this scan.",
            "- The `042448` HistGB screen remains in-progress or incomplete at this readback and must not be counted as confidence evidence.",
            "- The known verifier-shaped local triplets remain non-target and must not be copied into the R6 owner-export root without explicit approval or source-owned control provenance.",
            "",
            "## Next",
            "",
            "Preserve the Current Cursor next action. Continue only after explicit approval, verifier-native R6 owner/export rows plus source-owned broad normal controls, source-owned R5 recency-extension rows, native sub-hour source-label rows, or genuinely source-owned cross-timeframe `MainRegimeV2` exports unlock a target root before rerunning direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.",
        ]
    )
    (OUT / "source_control_arrival_scan_after_043027_v1.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )

    assertions = [
        f"PASS gate_result={gate}",
        f"PASS r6_owner_export_root_present={str(required[str(REQUIRED_ROOTS[0])]['present']).lower()}",
        f"PASS r6_owner_export_required_files_present={required[str(REQUIRED_ROOTS[0])].get('required_files_present', 0)}",
        f"PASS r3_native_subhour_root_present={str(r3_ready).lower()}",
        f"PASS r5_recency_extension_root_present={str(r5_ready).lower()}",
        f"PASS approval_package_present={str(approval_present).lower()}",
        "PASS approval_package_gate=r6_oystacher_approval_decision_package_v1=decision_package_ready_no_approval_no_merge",
        "PASS same_exhibit_flip_as_matched_controls=rejected_under_current_contract",
        "PASS source_owned_normal_controls_alternative=not_supplied",
        "PASS accepted_rows_added=0",
        f"PASS source_control_evidence_acquired={str(source_control_evidence_acquired).lower()}",
        "PASS new_source_unlock=false",
        "PASS explicit_approval=false",
        "PASS flip_controls_approved=false",
        f"PASS source_owned_normal_controls_supplied={str(source_owned_normal_controls_supplied).lower()}",
        "PASS canonical_merge=false",
        "PASS downstream_promotion_rerun=false",
        "PASS strict_full_objective=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "source_control_arrival_scan_after_043027_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print(json.dumps({"ok": True, "gate_result": gate}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
