#!/usr/bin/env python3
"""Strict completion audit after the R5 upstream refresh check."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T215732+0800-codex-current-goal-completion-audit-v49-after-r5-upstream-refresh-check"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T215732-codex-current-goal-completion-audit-v49-after-r5-upstream-refresh-check"
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
SOURCE_LABEL_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
DIRECT_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
RECENCY_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
SOURCE_CONFIDENCE_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T214328-codex-source-label-equivalence-confidence-calibration-v1/"
    "source-label-equivalence-confidence-calibration/source_label_equivalence_confidence_calibration_v1.json"
)
R5_REFRESH_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T215420-codex-source-panel-recency-upstream-refresh-check-v1/"
    "source-panel-recency-refresh/source_panel_recency_upstream_refresh_check_v1.json"
)
R5_SCREEN_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T215539-codex-r5-source-panel-recency-extension-acquisition-screen-v1/"
    "r5-source-panel-recency-extension-acquisition-screen/r5_source_panel_recency_extension_acquisition_screen_v1.json"
)

SOURCE_LABEL_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
DIRECT_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
RECENCY_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
NATIVE_SUBHOUR_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_json_command(name: str, args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=str(REPO), text=True, capture_output=True, check=False)
    stdout_path = CMD_DIR / f"{name}.stdout.txt"
    stderr_path = CMD_DIR / f"{name}.stderr.txt"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"parse_failed": True, "stdout_sample": result.stdout[:1000]}
    return {
        "name": name,
        "args": args,
        "returncode": result.returncode,
        "stdout_path": repo_rel(stdout_path),
        "stderr_path": repo_rel(stderr_path),
        "payload": payload,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)

    source_label = run_json_command(
        "source_label_equivalence_verifier",
        ["python3", str(SOURCE_LABEL_VERIFIER), "--intake-root", str(SOURCE_LABEL_ROOT)],
    )
    direct = run_json_command(
        "direct_manipulation_row_intake_verifier",
        ["python3", str(DIRECT_VERIFIER), "--intake-root", str(DIRECT_ROOT)],
    )
    recency = run_json_command(
        "source_panel_recency_extension_verifier",
        ["python3", str(RECENCY_VERIFIER), "--intake-root", str(RECENCY_ROOT)],
    )
    source_confidence = json.loads(SOURCE_CONFIDENCE_JSON.read_text(encoding="utf-8"))
    r5_refresh = json.loads(R5_REFRESH_JSON.read_text(encoding="utf-8"))
    r5_screen = json.loads(R5_SCREEN_JSON.read_text(encoding="utf-8"))

    source_label_ready = source_label["payload"].get("status") == "schema_ready_unscored"
    direct_ready = direct["payload"].get("status") == "schema_ready_unscored"
    recency_ready = recency["payload"].get("status") == "schema_ready_unscored"
    native_ready = NATIVE_SUBHOUR_ROOT.exists()

    direct_positive = int(direct["payload"].get("positive_rows", 0) or 0)
    direct_negative = int(direct["payload"].get("matched_negative_rows", 0) or 0)
    accepted_source_labels = source_confidence.get("accepted_source_confidence_95_labels", [])

    gates = [
        {
            "gate": "source_label_equivalence_schema",
            "status": "pass" if source_label_ready else "fail",
            "evidence": f"status={source_label['payload'].get('status')}; rows={source_label['payload'].get('row_count')}",
        },
        {
            "gate": "source_label_equivalence_confidence",
            "status": "fail",
            "evidence": f"accepted_source_confidence_95_labels={len(accepted_source_labels)}/4; decision={source_confidence.get('decision')}",
        },
        {
            "gate": "native_subhour_source_label_root",
            "status": "pass" if native_ready else "fail",
            "evidence": f"path={NATIVE_SUBHOUR_ROOT}; exists={native_ready}",
        },
        {
            "gate": "source_panel_recency_extension_root",
            "status": "pass" if recency_ready else "fail",
            "evidence": (
                f"status={recency['payload'].get('status')}; reason={recency['payload'].get('reason')}; "
                f"r5_screen={r5_screen['decision']}; r5_refresh={r5_refresh['decision']['gate_result']}"
            ),
        },
        {
            "gate": "direct_manipulation_schema",
            "status": "pass" if direct_ready else "fail",
            "evidence": f"status={direct['payload'].get('status')}; positives={direct_positive}; matched_negatives={direct_negative}",
        },
        {
            "gate": "direct_manipulation_support",
            "status": "pass" if direct_positive >= 50 and direct_negative >= 50 else "fail",
            "evidence": f"positives={direct_positive}; matched_negatives={direct_negative}; required_min=50/50",
        },
        {
            "gate": "strict_full_objective",
            "status": "fail",
            "evidence": "source confidence accepted 0/4 labels; R3 native sub-hour missing; R5 recency missing; R6 direct support and broad normal controls incomplete",
        },
    ]
    intake_roots = [
        {"root": "source_label_equivalence", "path": str(SOURCE_LABEL_ROOT), "ready": source_label_ready, "status": source_label["payload"].get("status", "")},
        {"root": "direct_manipulation_row_intake", "path": str(DIRECT_ROOT), "ready": direct_ready, "status": direct["payload"].get("status", "")},
        {"root": "native_subhour_source_label", "path": str(NATIVE_SUBHOUR_ROOT), "ready": native_ready, "status": "present" if native_ready else "missing"},
        {"root": "source_panel_recency_extension", "path": str(RECENCY_ROOT), "ready": recency_ready, "status": recency["payload"].get("status", "missing")},
    ]
    ready_roots = sum(1 for row in intake_roots if row["ready"])

    write_csv(OUT_DIR / "current_goal_completion_audit_v49_gates.csv", gates, ["gate", "status", "evidence"])
    write_csv(OUT_DIR / "current_goal_completion_audit_v49_intake_roots.csv", intake_roots, ["root", "path", "ready", "status"])
    write_csv(
        OUT_DIR / "current_goal_completion_audit_v49_checklist.csv",
        [
            {"requirement": "source_owned_or_owner_approved_95_confidence_all_active_regimes", "status": "fail", "evidence": "accepted_source_confidence_95_labels=0/4"},
            {"requirement": "cross_market_species_validation", "status": "partial", "evidence": "daily source-label schema rows present; native sub-hour and direct Manipulation species incomplete"},
            {"requirement": "cross_cycle_timeframe_validation", "status": "fail", "evidence": "native sub-hour root absent; R5 recency root blocked"},
            {"requirement": "direct_manipulation_controls", "status": "fail", "evidence": f"direct={direct_positive}/{direct_negative}; min 50/50 and broad-normal/direct species gates still open"},
            {"requirement": "no_threshold_relaxation_or_proxy_promotion", "status": "pass", "evidence": "R5 refresh check explicitly rejected OHLCV-derived labels for source-panel recency"},
        ],
        ["requirement", "status", "evidence"],
    )

    audit = {
        "run_id": RUN_ID,
        "artifact_type": "current_goal_completion_audit_v49_after_r5_upstream_refresh_check",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": repo_rel(BOARD),
        "board_sha256_at_run": sha256(BOARD),
        "source_label_verifier": source_label,
        "direct_manipulation_verifier": direct,
        "source_panel_recency_verifier": recency,
        "native_subhour_root_exists": native_ready,
        "r5_refresh_check": {
            "path": repo_rel(R5_REFRESH_JSON),
            "decision": r5_refresh["decision"],
            "kaggle_last_updated": r5_refresh["kaggle"]["list"]["last_updated"],
            "local_source_panel_date_max": r5_refresh["source_panel_local"]["date_max"],
        },
        "r5_acquisition_screen": {
            "path": repo_rel(R5_SCREEN_JSON),
            "decision": r5_screen["decision"],
            "candidate_count": r5_screen["candidate_count"],
            "accepted_candidate_count": r5_screen["accepted_candidate_count"],
            "accepted_extension_rows": r5_screen["accepted_extension_rows"],
            "verifier_status": r5_screen["verifier_status"],
        },
        "source_confidence_calibration": {
            "path": repo_rel(SOURCE_CONFIDENCE_JSON),
            "decision": source_confidence.get("decision"),
            "accepted_source_confidence_95_labels": accepted_source_labels,
            "label_counts": source_confidence.get("label_counts", {}),
        },
        "ready_roots": {"ready": ready_roots, "total": 4, "roots": intake_roots},
        "decision": {
            "gate_result": "current_goal_completion_audit_v49_after_r5_acquisition_screen=2of4_roots_still_blocked",
            "board_state": "blocked",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "external_requests_sent": True,
            "trade_usable": False,
        },
        "blocker": (
            "R5 owner source and bounded candidate screen found no acceptable post-cutoff source-panel rows; "
            "source-confidence labels remain 0/4 accepted; R3 native sub-hour root is absent; "
            f"R6 direct remains {direct_positive}/{direct_negative} with support below 50/50 and broad-normal/direct-species gates open."
        ),
        "next_action": "Switch to native sub-hour acquisition or expand R6 direct to 50/50 with broad normal controls and direct species coverage.",
    }
    (OUT_DIR / "current_goal_completion_audit_v49_after_r5_upstream_refresh_check.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Current Goal Completion Audit v49 After R5 Upstream Refresh Check",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Ready roots: `{ready_roots}/4`.",
        f"- Source-label equivalence: `{source_label['payload'].get('status')}`, rows `{source_label['payload'].get('row_count')}`, accepted source-confidence labels `{len(accepted_source_labels)}/4`.",
        f"- R5 recency: `{recency['payload'].get('status')}` / `{recency['payload'].get('reason')}`; acquisition screen candidates `{r5_screen['candidate_count']}`, accepted `{r5_screen['accepted_candidate_count']}`, extension rows `{r5_screen['accepted_extension_rows']}`.",
        f"- R6 direct: `{direct['payload'].get('status')}`, positives `{direct_positive}`, matched negatives `{direct_negative}`.",
        "- R3 native sub-hour root: `missing`.",
        "- Gate result: `current_goal_completion_audit_v49_after_r5_acquisition_screen=2of4_roots_still_blocked`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Next",
        "",
        "Switch to native sub-hour acquisition or expand R6 direct to `50/50` with broad normal controls and direct species coverage.",
    ]
    (OUT_DIR / "current_goal_completion_audit_v49_after_r5_upstream_refresh_check.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    failures = []
    if ready_roots != 2:
        failures.append(f"unexpected_ready_roots_{ready_roots}")
    if len(accepted_source_labels) != 0:
        failures.append("unexpected_source_confidence_acceptance")
    if recency["payload"].get("status") != "blocked":
        failures.append("unexpected_r5_status")
    if r5_screen["accepted_candidate_count"] != 0 or r5_screen["accepted_extension_rows"] != 0:
        failures.append("unexpected_r5_accepted_candidates")
    if native_ready:
        failures.append("unexpected_native_subhour_root_present")
    if direct_positive >= 50 and direct_negative >= 50:
        failures.append("unexpected_r6_support_closed")
    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={audit['board_sha256_at_run']}",
        f"ready_roots={ready_roots}/4",
        f"source_label_status={source_label['payload'].get('status')}",
        f"source_label_rows={source_label['payload'].get('row_count')}",
        f"accepted_source_confidence_95_labels={len(accepted_source_labels)}/4",
        f"r5_status={recency['payload'].get('status')}",
        f"r5_reason={recency['payload'].get('reason')}",
        f"r5_screen_candidates={r5_screen['candidate_count']}",
        f"r5_screen_accepted_candidates={r5_screen['accepted_candidate_count']}",
        f"r5_screen_accepted_extension_rows={r5_screen['accepted_extension_rows']}",
        f"native_subhour_root_exists={str(native_ready).lower()}",
        f"r6_positive_rows={direct_positive}",
        f"r6_matched_negative_rows={direct_negative}",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "external_requests_sent=true",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        f"assertion_status={'FAIL' if failures else 'PASS'}",
    ]
    if failures:
        assertions.append("failures=" + ",".join(failures))
    (CHECK_DIR / "current_goal_completion_audit_v49_after_r5_upstream_refresh_check_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
