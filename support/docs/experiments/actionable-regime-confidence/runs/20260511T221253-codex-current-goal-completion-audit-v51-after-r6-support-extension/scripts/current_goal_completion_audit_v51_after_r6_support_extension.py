#!/usr/bin/env python3
"""Strict readback after the R6 direct support extension."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T221253+0800-codex-current-goal-completion-audit-v51-after-r6-support-extension"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T221253-codex-current-goal-completion-audit-v51-after-r6-support-extension"
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
R6_EXTENSION_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T220755-codex-r6-official-rowlevel-support-extension-v1/"
    "r6-official-rowlevel-support-extension/r6_official_rowlevel_support_extension_v1.json"
)

SOURCE_LABEL_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
DIRECT_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
RECENCY_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
NATIVE_SUBHOUR_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_absolute() and path.is_relative_to(REPO) else str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def wilson_all_success(n: int) -> float:
    if n <= 0:
        return 0.0
    z = 1.959963984540054
    return n / (n + z * z)


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
    r6_extension = json.loads(R6_EXTENSION_JSON.read_text(encoding="utf-8"))

    direct_positive = int(direct["payload"].get("positive_rows", 0) or 0)
    direct_negative = int(direct["payload"].get("matched_negative_rows", 0) or 0)
    direct_ready = direct["payload"].get("status") == "schema_ready_unscored"
    source_label_ready = source_label["payload"].get("status") == "schema_ready_unscored"
    recency_ready = recency["payload"].get("status") == "schema_ready_unscored"
    native_ready = NATIVE_SUBHOUR_ROOT.exists()
    accepted_source_labels = source_confidence.get("accepted_source_confidence_95_labels", [])

    positive_lcb = wilson_all_success(direct_positive)
    negative_lcb = wilson_all_success(direct_negative)
    min_lcb = min(positive_lcb, negative_lcb)
    support_ok = direct_positive >= 50 and direct_negative >= 50
    broad_normal_sample = False
    direct_species_closed = False
    new_confidence_gate = support_ok and min_lcb >= 0.95 and broad_normal_sample and direct_species_closed
    ready_roots = sum([source_label_ready, direct_ready, recency_ready, native_ready])

    gates = [
        {"gate": "source_label_equivalence_schema", "status": "pass" if source_label_ready else "fail", "evidence": f"status={source_label['payload'].get('status')}; rows={source_label['payload'].get('row_count')}"},
        {"gate": "source_label_equivalence_confidence", "status": "fail", "evidence": f"accepted_source_confidence_95_labels={len(accepted_source_labels)}/4"},
        {"gate": "native_subhour_source_label_root", "status": "pass" if native_ready else "fail", "evidence": f"path={NATIVE_SUBHOUR_ROOT}; exists={native_ready}"},
        {"gate": "source_panel_recency_extension_root", "status": "pass" if recency_ready else "fail", "evidence": f"status={recency['payload'].get('status')}; reason={recency['payload'].get('reason')}"},
        {"gate": "direct_manipulation_schema", "status": "pass" if direct_ready else "fail", "evidence": f"status={direct['payload'].get('status')}; positives={direct_positive}; matched_negatives={direct_negative}"},
        {"gate": "direct_manipulation_support", "status": "pass" if support_ok else "fail", "evidence": f"positives={direct_positive}; matched_negatives={direct_negative}; required_min=50/50"},
        {"gate": "direct_manipulation_wilson95", "status": "pass" if min_lcb >= 0.95 else "fail", "evidence": f"min_lcb={min_lcb:.6f}; required>=0.95"},
        {"gate": "direct_manipulation_broad_normal_sample", "status": "fail", "evidence": f"broad_normal_sample={broad_normal_sample}; controls are same-source genuine-order seeds"},
        {"gate": "direct_manipulation_species_coverage", "status": "fail", "evidence": f"direct_species_closed={direct_species_closed}"},
        {"gate": "strict_full_objective", "status": "fail", "evidence": "source confidence accepted 0/4 labels; R3 native sub-hour missing; R5 recency missing; R6 Wilson95/broad-normal/direct-species gates incomplete"},
    ]
    write_csv(OUT_DIR / "current_goal_completion_audit_v51_gates.csv", gates, ["gate", "status", "evidence"])
    write_csv(
        OUT_DIR / "current_goal_completion_audit_v51_checklist.csv",
        [
            {"requirement": "source_owned_or_owner_approved_95_confidence_all_active_regimes", "status": "fail", "evidence": "accepted_source_confidence_95_labels=0/4"},
            {"requirement": "direct_manipulation_support", "status": "pass", "evidence": f"direct={direct_positive}/{direct_negative}; min 50/50"},
            {"requirement": "direct_manipulation_wilson95", "status": "fail", "evidence": f"min_lcb={min_lcb:.6f}; required >=0.95"},
            {"requirement": "direct_manipulation_controls", "status": "fail", "evidence": "broad normal-market sample false; same-event genuine legs only"},
            {"requirement": "cross_cycle_timeframe_validation", "status": "fail", "evidence": "native sub-hour root absent; R5 recency root blocked"},
            {"requirement": "no_threshold_relaxation_or_proxy_promotion", "status": "pass", "evidence": "R6 rows are source-backed public CFTC direct event rows; no OHLCV proxy promotion"},
        ],
        ["requirement", "status", "evidence"],
    )

    decision = {
        "gate_result": "current_goal_completion_audit_v51_after_r6_support_extension=support_closed_confidence_still_blocked",
        "board_state": "blocked",
        "accepted_rows_added": 0,
        "new_confidence_gate": new_confidence_gate,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }
    audit = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": repo_rel(BOARD),
        "board_sha256_at_run": sha256(BOARD),
        "source_label_verifier": source_label,
        "direct_manipulation_verifier": direct,
        "source_panel_recency_verifier": recency,
        "native_subhour_root_exists": native_ready,
        "source_confidence": {"path": repo_rel(SOURCE_CONFIDENCE_JSON), "accepted_source_confidence_95_labels": accepted_source_labels},
        "r6_extension": {
            "path": repo_rel(R6_EXTENSION_JSON),
            "gate_result": r6_extension["decision"]["gate_result"],
            "positive_rows_added_this_run": r6_extension["positive_rows_added_this_run"],
            "matched_negative_rows_added_this_run": r6_extension["matched_negative_rows_added_this_run"],
        },
        "ready_roots": {"ready": ready_roots, "total": 4},
        "r6_direct": {
            "positive_rows": direct_positive,
            "matched_negative_rows": direct_negative,
            "matched_group_count": direct["payload"].get("matched_group_count"),
            "support_50x50": support_ok,
            "positive_wilson95_lcb": positive_lcb,
            "matched_negative_wilson95_lcb": negative_lcb,
            "min_wilson95_lcb": min_lcb,
            "broad_normal_sample": broad_normal_sample,
            "direct_species_closed": direct_species_closed,
        },
        "gates": gates,
        "decision": decision,
        "blocker": (
            "R6 support is now 62/62, but Wilson95 min LCB remains below 0.95 and broad normal/direct-species gates are still open; "
            "source-confidence labels remain 0/4 accepted, native sub-hour root is absent, and R5 recency verifier remains blocked."
        ),
        "next_action": "Acquire independent broad normal-market order-lifecycle controls and enough additional direct rows for Wilson95 >=0.95; keep R5 blocked until source-owner post-cutoff source-panel rows exist.",
    }
    (OUT_DIR / "current_goal_completion_audit_v51_after_r6_support_extension.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# Current Goal Completion Audit v51 After R6 Support Extension",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Ready roots: `{ready_roots}/4`.",
        f"- Source-label equivalence: `{source_label['payload'].get('status')}`, rows `{source_label['payload'].get('row_count')}`, accepted source-confidence labels `{len(accepted_source_labels)}/4`.",
        f"- R5 recency: `{recency['payload'].get('status')}` / `{recency['payload'].get('reason')}`.",
        f"- R3 native sub-hour root: `{'present' if native_ready else 'missing'}`.",
        f"- R6 direct: `{direct['payload'].get('status')}`, positives `{direct_positive}`, matched negatives `{direct_negative}`, matched groups `{direct['payload'].get('matched_group_count')}`.",
        f"- R6 support `50/50`: `{str(support_ok).lower()}`; Wilson95 min LCB `{min_lcb:.6f}`.",
        "- R6 broad normal sample: `false`; direct species closed: `false`.",
        f"- Gate result: `{decision['gate_result']}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Next",
        "",
        "Acquire independent broad normal-market order-lifecycle controls and enough additional direct rows for Wilson95 `>=0.95`; keep R5 blocked until source-owner post-cutoff source-panel rows exist.",
    ]
    (OUT_DIR / "current_goal_completion_audit_v51_after_r6_support_extension.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    failures = []
    if ready_roots != 2:
        failures.append(f"unexpected_ready_roots_{ready_roots}")
    if len(accepted_source_labels) != 0:
        failures.append("unexpected_source_confidence_acceptance")
    if not support_ok:
        failures.append("r6_support_not_closed")
    if min_lcb >= 0.95:
        failures.append("unexpected_r6_wilson_pass")
    if recency["payload"].get("status") != "blocked":
        failures.append("unexpected_recency_status")
    if native_ready:
        failures.append("unexpected_native_subhour_present")
    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={audit['board_sha256_at_run']}",
        f"ready_roots={ready_roots}/4",
        f"accepted_source_confidence_95_labels={len(accepted_source_labels)}/4",
        f"r5_status={recency['payload'].get('status')}",
        f"native_subhour_root_exists={str(native_ready).lower()}",
        f"r6_positive_rows={direct_positive}",
        f"r6_matched_negative_rows={direct_negative}",
        f"r6_support_50x50={str(support_ok).lower()}",
        f"r6_wilson95_min_lcb={min_lcb:.6f}",
        f"r6_broad_normal_sample={str(broad_normal_sample).lower()}",
        f"r6_direct_species_closed={str(direct_species_closed).lower()}",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
        f"assertion_status={'FAIL' if failures else 'PASS'}",
    ]
    if failures:
        assertions.append("failures=" + ",".join(failures))
    (CHECK_DIR / "current_goal_completion_audit_v51_after_r6_support_extension_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision["gate_result"], "r6_positive_rows": direct_positive, "r6_matched_negative_rows": direct_negative, "r6_wilson95_min_lcb": round(min_lcb, 6)}, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
