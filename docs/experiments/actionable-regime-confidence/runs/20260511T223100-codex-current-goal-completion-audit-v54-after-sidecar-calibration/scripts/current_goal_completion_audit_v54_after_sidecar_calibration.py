#!/usr/bin/env python3
"""Strict current-goal audit after R6 sidecar broad-normal calibration."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T223100+0800-codex-current-goal-completion-audit-v54-after-sidecar-calibration"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T223100-codex-current-goal-completion-audit-v54-after-sidecar-calibration"
OUT = RUN_ROOT / "completion-audit"
CHECKS = RUN_ROOT / "checks"
CMD_OUT = RUN_ROOT / "command-output"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
SOURCE_LABEL_VERIFIER = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T182922-codex-source-label-equivalence-intake-verifier-v1/equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
DIRECT_VERIFIER = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
RECENCY_VERIFIER = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T165405-codex-source-panel-recency-extension-manifest-v1/source-panel-recency/source_panel_recency_extension_verifier_v1.py"
SOURCE_CONFIDENCE_JSON = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T214328-codex-source-label-equivalence-confidence-calibration-v1/source-label-equivalence-confidence-calibration/source_label_equivalence_confidence_calibration_v1.json"
SIDECAR_CALIBRATION_JSON = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T222828-codex-r6-sidecar-broad-normal-calibration-v2/r6-sidecar-broad-normal-calibration/r6_sidecar_broad_normal_calibration_v2.json"

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


def wilson_lcb(successes: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = z * z
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return (centre - margin) / denom


def run_json(name: str, args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=str(REPO), text=True, capture_output=True, check=False)
    stdout_path = CMD_OUT / f"{name}.stdout.txt"
    stderr_path = CMD_OUT / f"{name}.stderr.txt"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"parse_failed": True, "stdout_sample": result.stdout[:1000]}
    return {"name": name, "returncode": result.returncode, "stdout_path": repo_rel(stdout_path), "stderr_path": repo_rel(stderr_path), "payload": payload}


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)

    source_label = run_json("source_label_equivalence_verifier", ["python3", str(SOURCE_LABEL_VERIFIER), "--intake-root", str(SOURCE_LABEL_ROOT)])
    direct = run_json("direct_manipulation_row_intake_verifier", ["python3", str(DIRECT_VERIFIER), "--intake-root", str(DIRECT_ROOT)])
    recency = run_json("source_panel_recency_extension_verifier", ["python3", str(RECENCY_VERIFIER), "--intake-root", str(RECENCY_ROOT)])
    source_confidence = json.loads(SOURCE_CONFIDENCE_JSON.read_text(encoding="utf-8"))
    sidecar = json.loads(SIDECAR_CALIBRATION_JSON.read_text(encoding="utf-8"))

    accepted_source_labels = source_confidence.get("accepted_source_confidence_95_labels", [])
    direct_positive = int(direct["payload"].get("positive_rows", 0) or 0)
    direct_negative = int(direct["payload"].get("matched_negative_rows", 0) or 0)
    direct_min_lcb = min(wilson_lcb(direct_positive, direct_positive), wilson_lcb(direct_negative, direct_negative))
    support_50 = direct_positive >= 50 and direct_negative >= 50
    native_ready = NATIVE_SUBHOUR_ROOT.exists()
    sidecar_decision = sidecar["decision"]

    gates = [
        {"gate": "source_label_schema", "status": "pass", "evidence": f"status={source_label['payload'].get('status')}; rows={source_label['payload'].get('row_count')}"},
        {"gate": "source_label_confidence_95", "status": "fail", "evidence": f"accepted={len(accepted_source_labels)}/4"},
        {"gate": "r5_source_panel_recency", "status": "fail", "evidence": f"status={recency['payload'].get('status')}; reason={recency['payload'].get('reason')}"},
        {"gate": "r3_native_subhour", "status": "fail", "evidence": f"exists={native_ready}; path={NATIVE_SUBHOUR_ROOT}"},
        {"gate": "r6_direct_schema", "status": "pass", "evidence": f"status={direct['payload'].get('status')}; positives={direct_positive}; controls={direct_negative}"},
        {"gate": "r6_direct_support_50_50", "status": "pass" if support_50 else "fail", "evidence": f"{direct_positive}/{direct_negative}"},
        {"gate": "r6_direct_wilson95", "status": "pass" if direct_min_lcb >= 0.95 else "fail", "evidence": f"min_lcb={direct_min_lcb:.6f}"},
        {"gate": "r6_independent_broad_normal_sidecar", "status": "pass" if sidecar_decision["sidecar_control_axis_pass"] else "fail", "evidence": f"rows={sidecar_decision['sidecar_broad_normal_control_rows']}; lcb={sidecar['metrics'][2]['wilson95_lcb']}"},
        {"gate": "r6_direct_species_closed", "status": "fail", "evidence": "non-spoofing direct species still missing"},
        {"gate": "strict_full_objective", "status": "fail", "evidence": "source labels 0/4 accepted; R3/R5 missing; R6 positive Wilson95/species gates open"},
    ]
    write_csv(OUT / "current_goal_completion_audit_v54_gates.csv", gates, ["gate", "status", "evidence"])

    audit = {
        "run_id": RUN_ID,
        "artifact_type": "current_goal_completion_audit_v54_after_sidecar_calibration",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": repo_rel(BOARD),
        "board_sha256_at_run": sha256(BOARD),
        "source_label_verifier": source_label,
        "direct_verifier": direct,
        "recency_verifier": recency,
        "source_confidence": {
            "path": repo_rel(SOURCE_CONFIDENCE_JSON),
            "accepted_source_confidence_95_labels": accepted_source_labels,
        },
        "sidecar_calibration": {
            "path": repo_rel(SIDECAR_CALIBRATION_JSON),
            "gate_result": sidecar_decision["gate_result"],
            "sidecar_control_axis_pass": sidecar_decision["sidecar_control_axis_pass"],
            "sidecar_broad_normal_control_rows": sidecar_decision["sidecar_broad_normal_control_rows"],
            "additional_positive_rows_needed_for_pooled_wilson95_if_all_correct": sidecar_decision["additional_positive_rows_needed_for_pooled_wilson95_if_all_correct"],
        },
        "r6": {
            "positive_rows": direct_positive,
            "matched_negative_rows": direct_negative,
            "matched_group_count": direct["payload"].get("matched_group_count"),
            "wilson95_min_lcb": round(direct_min_lcb, 6),
            "support_50_50": support_50,
            "independent_broad_normal_sidecar_axis": sidecar_decision["sidecar_control_axis_pass"],
            "direct_species_closed": False,
        },
        "decision": {
            "gate_result": "current_goal_completion_audit_v54_after_sidecar_calibration=broad_normal_axis_passed_positive_confidence_still_blocked",
            "board_state": "blocked",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "strict_full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "external_requests_sent": False,
            "trade_usable": False,
        },
        "next_action": "Acquire at least 16 additional owner-approved direct positive rows across missing non-spoofing species, then rerun R6 calibration; keep source-confidence, R3, and R5 blockers fail-closed.",
    }
    json_path = OUT / "current_goal_completion_audit_v54_after_sidecar_calibration.json"
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# Current Goal Completion Audit v54 After Sidecar Calibration",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Source-label equivalence: `{source_label['payload'].get('status')}` with rows `{source_label['payload'].get('row_count')}`; accepted source-confidence labels `{len(accepted_source_labels)}/4`.",
        f"- R5 recency: `{recency['payload'].get('status')}` / `{recency['payload'].get('reason')}`.",
        f"- R3 native sub-hour root: `{'present' if native_ready else 'missing'}`.",
        f"- R6 direct: `{direct['payload'].get('status')}`, positives `{direct_positive}`, matched negatives `{direct_negative}`, matched groups `{direct['payload'].get('matched_group_count')}`.",
        f"- R6 support `50/50`: `{str(support_50).lower()}`; direct Wilson95 min LCB `{direct_min_lcb:.6f}`.",
        f"- Independent broad-normal sidecar axis: `{str(sidecar_decision['sidecar_control_axis_pass']).lower()}` with rows `{sidecar_decision['sidecar_broad_normal_control_rows']}`.",
        f"- Additional all-correct positive rows needed for pooled Wilson95 `>=0.95`: `{sidecar_decision['additional_positive_rows_needed_for_pooled_wilson95_if_all_correct']}`.",
        "- Gate result: `current_goal_completion_audit_v54_after_sidecar_calibration=broad_normal_axis_passed_positive_confidence_still_blocked`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
    ]
    report_path = OUT / "current_goal_completion_audit_v54_after_sidecar_calibration.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    failures = []
    if direct_min_lcb >= 0.95:
        failures.append("unexpected_r6_positive_wilson95_closed")
    if len(accepted_source_labels) != 0:
        failures.append("unexpected_source_confidence_acceptance")
    if recency["payload"].get("status") != "blocked":
        failures.append("unexpected_r5_status")
    if not sidecar_decision["sidecar_control_axis_pass"]:
        failures.append("sidecar_axis_unexpectedly_failed")
    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={audit['board_sha256_at_run']}",
        f"source_label_rows={source_label['payload'].get('row_count')}",
        f"accepted_source_confidence_95_labels={len(accepted_source_labels)}/4",
        f"r5_status={recency['payload'].get('status')}",
        f"native_subhour_root_exists={str(native_ready).lower()}",
        f"r6_positive_rows={direct_positive}",
        f"r6_matched_negative_rows={direct_negative}",
        f"r6_wilson95_min_lcb={direct_min_lcb:.6f}",
        f"r6_independent_broad_normal_sidecar_axis={str(sidecar_decision['sidecar_control_axis_pass']).lower()}",
        f"additional_positive_rows_needed={sidecar_decision['additional_positive_rows_needed_for_pooled_wilson95_if_all_correct']}",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        f"assertion_status={'FAIL' if failures else 'PASS'}",
    ]
    if failures:
        assertions.append("failures=" + ",".join(failures))
    (CHECKS / "current_goal_completion_audit_v54_after_sidecar_calibration_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
