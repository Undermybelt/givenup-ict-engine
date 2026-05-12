#!/usr/bin/env python3
"""Audit the active Board A objective against current concrete artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


RUN_ID = "20260512T012616-codex-current-objective-completion-audit-after-012318-v1"
REPO = Path(__file__).resolve().parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = OUT_ROOT / "current-objective-completion-audit-after-012318-v1"
CHECK_DIR = OUT_ROOT / "checks"

R6_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
SOURCE_LABEL_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
R3_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")

ARTIFACTS = {
    "source_label_arrival_calibration": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T011954-codex-source-label-equivalence-arrival-calibration-v1/source-label-equivalence-arrival-calibration/source_label_equivalence_arrival_calibration_v1.json",
    "source_label_gap_decomposition": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T011529-codex-source-label-confidence-gap-decomposition-v1/source-label-confidence-gap-decomposition-v1/source_label_confidence_gap_decomposition_v1.json",
    "source_label_candidate": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T012231-codex-source-label-qualifying-condition-candidate-v1/source-label-qualifying-condition-candidate-v1/source_label_qualifying_condition_candidate_v1.json",
    "source_label_qualifying_probe": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T012318-codex-source-label-high-confidence-qualifying-condition-probe-v1/source-label-high-confidence-qualifying-condition-probe-v1/source_label_high_confidence_qualifying_condition_probe_v1.json",
    "source_label_failclosed_conditions": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T012425-codex-source-label-qualifying-condition-failclosed-v1/source-label-qualifying-condition-failclosed-v1/source_label_qualifying_condition_failclosed_v1.json",
    "r3_target_check": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T012000-codex-r3-target-cell-check-against-source-label-root-v1/r3-target-cell-check-against-source-label-root-v1/r3_target_cell_check_against_source_label_root_v1.json",
    "r3_public_web_screen": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T012139-codex-r3-native-subhour-public-web-source-screen-v1/r3-native-subhour-public-web-source-screen-v1/r3_native_subhour_public_web_source_screen_v1.json",
    "r5_recency_disambiguation": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T012104-codex-r5-recency-provenance-date-disambiguation-v1/r5-recency-provenance-date-disambiguation-v1/r5_recency_provenance_date_disambiguation_v1.json",
    "r6_access_route": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T010212-codex-r6-owner-export-access-route-preflight-v1/r6-owner-export-access-route-preflight-v1/r6_owner_export_access_route_preflight_v1.json",
    "r6_local_owner_scan": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T011812-codex-local-owner-export-candidate-scan-v1/local-owner-export-candidate-scan-v1/local_owner_export_candidate_scan_v1.json",
    "provider_chain_readback": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T212339-codex-post-cleanup-provider-chain-readback-v1/post-cleanup-provider-chain-readback/post_cleanup_provider_chain_readback_v1.md",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def cursor_value(field: str) -> str:
    prefix = f"| {field} |"
    for line in BOARD.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            parts = [part.strip() for part in line.strip("|").split("|")]
            return parts[1] if len(parts) > 1 else ""
    return ""


def root_status(root: Path, files: list[str]) -> dict[str, object]:
    present = root.exists()
    file_status = {name: (root / name).exists() for name in files}
    return {
        "root": str(root),
        "root_present": present,
        "required_files": ";".join(files),
        "required_files_present": all(file_status.values()),
        "missing_files": ";".join(name for name, exists in file_status.items() if not exists),
    }


def status_value(passed: bool, partial: bool = False) -> str:
    if passed:
        return "pass"
    if partial:
        return "partial"
    return "blocked"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    source_arrival = read_json(ARTIFACTS["source_label_arrival_calibration"])
    source_candidate = read_json(ARTIFACTS["source_label_candidate"])
    source_probe = read_json(ARTIFACTS["source_label_qualifying_probe"])
    r3_target = read_json(ARTIFACTS["r3_target_check"])
    r3_web = read_json(ARTIFACTS["r3_public_web_screen"])
    r5 = read_json(ARTIFACTS["r5_recency_disambiguation"])
    r6_route = read_json(ARTIFACTS["r6_access_route"])
    r6_local = read_json(ARTIFACTS["r6_local_owner_scan"])

    roots = [
        {"id": "r6_owner_export", **root_status(R6_ROOT, ["direct_manipulation_rows.csv", "direct_manipulation_provenance.json"])},
        {"id": "source_label_equivalence", **root_status(SOURCE_LABEL_ROOT, ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"])},
        {"id": "r3_native_subhour", **root_status(R3_ROOT, ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"])},
        {"id": "r5_recency_extension", **root_status(R5_ROOT, ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"])},
    ]

    artifact_rows = []
    for artifact_id, path in ARTIFACTS.items():
        artifact_rows.append(
            {
                "artifact_id": artifact_id,
                "path": str(path.relative_to(REPO)),
                "present": path.exists(),
                "sha256": sha256(path) if path.exists() and path.is_file() else "",
            }
        )

    accepted_source_labels = (
        source_arrival.get("accepted_source_confidence_labels")
        or source_arrival.get("accepted_labels")
        or []
    )
    candidate_labels = source_candidate.get("candidate_labels", [])
    blocked_labels = source_candidate.get("blocked_labels", {})
    probe_timeframe_ready = bool(source_probe.get("candidate_timeframe_variety_ready"))

    r6_controls_ready = R6_ROOT.exists() and (R6_ROOT / "direct_manipulation_rows.csv").exists()
    r3_ready = bool(r3_target.get("all_r3_targets_satisfied")) and bool(r3_web.get("ready_source_native_exports_found", 0))
    r5_ready = bool(r5.get("all_r5_targets_satisfied"))
    source_all_regimes_ready = len(accepted_source_labels) >= 4
    source_candidate_partial = set(candidate_labels) == {"Bull", "Sideways"}
    artifact_present_count = sum(1 for row in artifact_rows if row["present"])
    all_artifacts_present = artifact_present_count == len(artifact_rows)

    checklist = [
        {
            "id": "objective_board_file",
            "requirement": "Use the named Board A markdown as the authoritative plan/status file.",
            "evidence": str(BOARD.relative_to(REPO)),
            "status": "pass",
            "gap": "",
        },
        {
            "id": "every_regime_95",
            "requirement": "Every active MainRegimeV2 regime reaches 95% confidence.",
            "evidence": f"accepted_source_labels={accepted_source_labels}; candidate_labels={candidate_labels}; blocked_labels={json.dumps(blocked_labels, sort_keys=True)}",
            "status": status_value(source_all_regimes_ready, source_candidate_partial),
            "gap": "No accepted labels. Bull/Sideways are only candidates; Bear/Crisis remain blocked.",
        },
        {
            "id": "other_market_other_cycle_validation",
            "requirement": "Validate with suitable confidence on other markets and other cycles/timeframes.",
            "evidence": f"candidate_timeframe_variety_ready={probe_timeframe_ready}; r3_all_targets_satisfied={r3_target.get('all_r3_targets_satisfied')}; r5_all_targets_satisfied={r5.get('all_r5_targets_satisfied')}",
            "status": "blocked",
            "gap": "Bull/Sideways candidates are daily-only; R3 native sub-hour and R5 recency roots are absent.",
        },
        {
            "id": "direct_manipulation_r6",
            "requirement": "R6 direct Manipulation has source-owned positives and normal controls or explicit FLIP approval.",
            "evidence": f"r6_owner_export_ready={r6_controls_ready}; route_gate={r6_route.get('gate_result')}; local_scan={r6_local.get('gate_result')}",
            "status": "blocked",
            "gap": "Owner-export files and source-owned normal controls are absent; local Databento/Tomac archive is OHLCV-only.",
        },
        {
            "id": "provider_autoquant_chain",
            "requirement": "Operate providers, Auto-Quant, filter/pre-Bayes, BBN, CatBoost/path-ranking, and execution tree before reporting completion.",
            "evidence": f"provider_chain_artifact_present={ARTIFACTS['provider_chain_readback'].exists()}; downstream_allowed={source_arrival.get('downstream_chain_rerun_allowed')}",
            "status": "blocked",
            "gap": "Prior chain readback exists but is non-promoting; rerun is disallowed until accepted source/control roots and canonical merge exist.",
        },
        {
            "id": "provider_set",
            "requirement": "Remember IBKR, TradingViewRemix, yfinance, and Kraken provider paths.",
            "evidence": "Provider chain/readiness artifacts exist, but current accepted source/control blockers prevent promotion rerun.",
            "status": "partial",
            "gap": "Provider path awareness is present; provider output cannot substitute for source labels or controls.",
        },
        {
            "id": "multi_agent_safety",
            "requirement": "Do not disturb concurrent agents' board work.",
            "evidence": "This audit is append-only and does not edit Current Cursor or other run roots.",
            "status": "pass",
            "gap": "",
        },
        {
            "id": "no_proxy_completion",
            "requirement": "No imagined completion; only real artifacts and verifiers count.",
            "evidence": f"artifacts_present={artifact_present_count}/{len(artifact_rows)}; roots={json.dumps(roots, sort_keys=True)}",
            "status": "pass" if all_artifacts_present else "partial",
            "gap": "" if all_artifacts_present else "One board-referenced supporting artifact is absent on disk; do not treat that reference as verified evidence.",
        },
    ]

    passed = sum(1 for row in checklist if row["status"] == "pass")
    partial = sum(1 for row in checklist if row["status"] == "partial")
    blocked = sum(1 for row in checklist if row["status"] == "blocked")
    strict_complete = blocked == 0 and partial == 0

    summary = {
        "run_id": RUN_ID,
        "board": str(BOARD.relative_to(REPO)),
        "board_sha256_at_run": sha256(BOARD),
        "current_cursor_observed": cursor_value("last_loop_id"),
        "board_state_observed": cursor_value("board_state"),
        "objective_restatement": "Each active regime must reach 95% confidence and validate across other markets/cycles/timeframes; the result must be grounded in real ict-engine/Auto-Quant/provider/pre-Bayes/BBN/CatBoost/execution-tree artifacts without disrupting concurrent board work.",
        "checklist_total": len(checklist),
        "checklist_pass": passed,
        "checklist_partial": partial,
        "checklist_blocked": blocked,
        "roots": roots,
        "artifact_count": len(artifact_rows),
        "artifact_present_count": artifact_present_count,
        "accepted_source_labels": accepted_source_labels,
        "candidate_labels": candidate_labels,
        "blocked_labels": blocked_labels,
        "strict_full_objective_achieved": strict_complete,
        "update_goal": False,
        "gate_result": "current_objective_completion_audit_after_012318_v1=not_complete_r6_r3_r5_bear_crisis_timeframe_downstream_blocked",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    write_csv(
        OUT_DIR / "prompt_to_artifact_checklist_after_012318_v1.csv",
        checklist,
        ["id", "requirement", "evidence", "status", "gap"],
    )
    write_csv(
        OUT_DIR / "artifact_presence_after_012318_v1.csv",
        artifact_rows,
        ["artifact_id", "path", "present", "sha256"],
    )
    write_csv(
        OUT_DIR / "intake_root_status_after_012318_v1.csv",
        roots,
        ["id", "root", "root_present", "required_files", "required_files_present", "missing_files"],
    )
    (OUT_DIR / "current_objective_completion_audit_after_012318_v1.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    checklist_md = "\n".join(
        f"- `{row['id']}`: `{row['status']}` - {row['gap'] or row['evidence']}"
        for row in checklist
    )
    (OUT_DIR / "current_objective_completion_audit_after_012318_v1.md").write_text(
        "\n".join(
            [
                "# Current Objective Completion Audit After 012318 v1",
                "",
                f"Run id: `{RUN_ID}`",
                f"Gate result: `{summary['gate_result']}`",
                "",
                "Objective restatement:",
                summary["objective_restatement"],
                "",
                "Checklist:",
                checklist_md,
                "",
                "Result:",
                f"- Checklist: pass `{passed}`, partial `{partial}`, blocked `{blocked}` of `{len(checklist)}`.",
                f"- Accepted source labels: `{accepted_source_labels}`.",
                f"- Candidate labels only: `{candidate_labels}`.",
                "- R6, R3, R5, Bear/Crisis, timeframe diversity, and downstream promotion remain blocked.",
                "- `update_goal=false`.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assertions = {
        "strict_full_objective_achieved_false": summary["strict_full_objective_achieved"] is False,
        "update_goal_false": summary["update_goal"] is False,
        "blocked_requirements_present": blocked > 0,
        "r6_root_not_ready": not roots[0]["required_files_present"],
        "r3_root_not_ready": not roots[2]["required_files_present"],
        "r5_root_not_ready": not roots[3]["required_files_present"],
    }
    (CHECK_DIR / "current_objective_completion_audit_after_012318_v1_assertions.out").write_text(
        "\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
