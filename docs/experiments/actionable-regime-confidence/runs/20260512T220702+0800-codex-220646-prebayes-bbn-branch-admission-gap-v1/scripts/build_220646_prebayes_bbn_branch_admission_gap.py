#!/usr/bin/env python3
"""Build a read-only admission-gap packet for the closed 220646 branch root."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT.parents[0]
SOURCE_ROOT = RUNS / "20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
B5 = SOURCE_ROOT / "b5-branch-feedback-calibration-v1"
SRC_STATE = B5 / "state_branch_feedback_v1" / "SRC_ROOT_CARRY_LONG_220646"
NQ_STATE = SOURCE_ROOT / "state" / "NQ"

OUT_PACKET = ROOT / "materials/220646_prebayes_bbn_branch_admission_gap_packet.json"
OUT_ROWS = ROOT / "summaries/220646_prebayes_bbn_branch_admission_gap_rows.csv"


def load_json(path: Path):
    return json.loads(path.read_text())


def maybe_json(path: Path):
    return load_json(path) if path.exists() else None


def read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def pre_bayes_flags(status: dict | None) -> dict:
    status = status or {}
    return {
        "policy_present": status.get("latest_policy") is not None,
        "gate_status": status.get("latest_gate_status"),
        "soft_evidence_present": bool(status.get("latest_soft_evidence")),
        "bridge_present": status.get("latest_bridge") is not None,
        "policy_versions": ((status.get("latest_policy_lineage") or {}).get("total_versions") or 0),
    }


def main() -> None:
    nq_pre_bayes = (
        maybe_json(ROOT / "command-output" / "07_ict_engine_pre_bayes_status_nq.out")
        or maybe_json(SOURCE_ROOT / "ict-engine" / "06_pre_bayes_status_after_bbn_apply.json")
    )
    src_pre_bayes = (
        maybe_json(ROOT / "command-output" / "08_ict_engine_pre_bayes_status_src_root.out")
        or maybe_json(B5 / "command-output" / "27_py313_pre_bayes_status_final.out")
    )
    execution_candidate = maybe_json(ROOT / "command-output" / "10_ict_engine_workflow_execution_candidate_src_root.out")
    learning_state = load_json(SRC_STATE / "learning_state.json")
    bbn_probe_rows = read_csv_rows(SOURCE_ROOT / "downstream-chain" / "root_bbn_probe_summary_v1.csv")
    target_summary = load_json(SRC_STATE / "policy_training" / "structural_path_ranking_target_summary.json")
    runtime_selection = maybe_json(SRC_STATE / "policy_training" / "structural_path_ranking_runtime_selection.json") or {}
    target_rows = read_csv_rows(SRC_STATE / "policy_training" / "structural_path_ranking_target.csv")

    feedback_rows = learning_state.get("feedback_history", [])
    branch_paths = sorted({
        ((row.get("structural_feedback") or {}).get("branch_id") or "")
        for row in feedback_rows
        if (row.get("structural_feedback") or {}).get("branch_id")
    })
    realized = [row.get("realized_outcome") for row in feedback_rows]
    wins = sum(1 for item in realized if item == "win")
    losses = sum(1 for item in realized if item == "loss")
    pnls = [float(row.get("pnl", 0.0)) for row in feedback_rows if row.get("pnl") is not None]

    bbn_applied = sum(1 for row in bbn_probe_rows if row.get("bbn_evidence_applied") == "True")
    bbn_skipped = sum(1 for row in bbn_probe_rows if row.get("bbn_evidence_skipped_no_supported_label") == "True")

    nq_flags = pre_bayes_flags(nq_pre_bayes)
    src_flags = pre_bayes_flags(src_pre_bayes)

    current_candidate_rows = [row for row in target_rows if row.get("candidate_set_id", "").startswith("structural-candidates:")]
    mature_rows = [row for row in target_rows if row.get("maturity_mask") == "true"]
    rows_with_branch_path = [row for row in target_rows if " -> " in row.get("path_id", "")]
    raw_scored_mature_rows = target_summary.get("raw_scored_mature_rows")
    if raw_scored_mature_rows is None:
        raw_scored_mature_rows = sum(1 for row in mature_rows if row.get("raw_path_score") not in {"", None})

    gap_reasons: list[str] = []
    if not src_flags["policy_present"]:
        gap_reasons.append("src_root_pre_bayes_policy_absent")
    if src_flags["gate_status"] == "blocked":
        gap_reasons.append("src_root_pre_bayes_gate_blocked")
    if nq_flags["policy_present"] and not src_flags["policy_present"]:
        gap_reasons.append("pre_bayes_state_exists_for_NQ_not_SRC_ROOT")
    if bbn_skipped:
        gap_reasons.append("bbn_probe_skipped_unsupported_label")
    execution_gate_status = (execution_candidate or {}).get("execution_gate_status")
    execution_readiness = (execution_candidate or {}).get("execution_readiness")
    if execution_gate_status != "execution_admitted":
        gap_reasons.append("execution_tree_not_admitted")

    packet = {
        "protocol_version": "board-b-220646-prebayes-bbn-branch-admission-gap-v1",
        "source_root": str(SOURCE_ROOT.relative_to(RUNS.parents[1])),
        "symbol_under_test": "SRC_ROOT_CARRY_LONG_220646",
        "control_symbol_with_pre_bayes": "NQ",
        "branch_feedback": {
            "feedback_rows": len(feedback_rows),
            "branch_path_count": len(branch_paths),
            "branch_paths": branch_paths,
            "wins": wins,
            "losses": losses,
            "win_rate": (wins / len(feedback_rows)) if feedback_rows else None,
            "expectancy": mean(pnls) if pnls else None,
        },
        "pre_bayes_filter": {
            "nq_state": nq_flags,
            "src_root_state": src_flags,
            "branch_keyed_pre_bayes_admitted": bool(src_flags["policy_present"] and src_flags["soft_evidence_present"]),
        },
        "bbn": {
            "probe_rows": len(bbn_probe_rows),
            "applied_rows": bbn_applied,
            "skipped_unsupported_label_rows": bbn_skipped,
            "learning_satisfied": bool(src_flags["policy_present"] and bbn_applied == len(bbn_probe_rows) and bbn_probe_rows),
        },
        "catboost_path_ranker": {
            "rows": target_summary.get("rows"),
            "mature_rows": target_summary.get("mature_rows"),
            "history_mature_rows": target_summary.get("history_mature_rows"),
            "raw_scored_mature_rows": raw_scored_mature_rows,
            "runtime_selection_status": runtime_selection.get("status"),
            "score_model_family": runtime_selection.get("score_model_family"),
            "current_candidate_rows": len(current_candidate_rows),
            "rows_with_branch_path": len(rows_with_branch_path),
        },
        "execution_tree": {
            "candidate_present": execution_candidate is not None,
            "candidate_status": (execution_candidate or {}).get("candidate_status"),
            "execution_gate_status": execution_gate_status,
            "execution_readiness": execution_readiness,
            "pre_bayes_gate_status": (execution_candidate or {}).get("pre_bayes_gate_status"),
            "path_id": (execution_candidate or {}).get("path_id"),
            "admitted": execution_gate_status == "execution_admitted",
            "reason": "workflow execution-candidate is present but blocked; this packet does not mutate execution state",
        },
        "gate": {
            "branch_path_preserved": len(branch_paths) >= 4 and len(rows_with_branch_path) > 0,
            "pre_bayes_filter_satisfied": bool(src_flags["policy_present"] and src_flags["soft_evidence_present"]),
            "bbn_learning_satisfied": bool(src_flags["policy_present"] and bbn_applied == len(bbn_probe_rows) and bbn_probe_rows),
            "catboost_path_ranker_satisfied": bool(raw_scored_mature_rows >= 30),
            "execution_tree_admitted": execution_gate_status == "execution_admitted",
            "full_chain_satisfied": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "fail_closed_reasons": gap_reasons,
        },
    }

    OUT_PACKET.parent.mkdir(parents=True, exist_ok=True)
    OUT_PACKET.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    rows = [
        {"check": "branch_feedback_rows", "value": len(feedback_rows), "status": "pass" if feedback_rows else "fail"},
        {"check": "branch_path_count", "value": len(branch_paths), "status": "pass" if len(branch_paths) >= 4 else "fail"},
        {"check": "nq_pre_bayes_policy_present", "value": nq_flags["policy_present"], "status": "info"},
        {"check": "src_root_pre_bayes_policy_present", "value": src_flags["policy_present"], "status": "fail" if not src_flags["policy_present"] else "pass"},
        {"check": "bbn_probe_applied_rows", "value": bbn_applied, "status": "partial" if bbn_applied else "fail"},
        {"check": "bbn_probe_skipped_rows", "value": bbn_skipped, "status": "fail" if bbn_skipped else "pass"},
        {"check": "catboost_raw_scored_mature_rows", "value": raw_scored_mature_rows, "status": "pass" if raw_scored_mature_rows >= 30 else "fail"},
        {"check": "execution_tree_admitted", "value": execution_gate_status == "execution_admitted", "status": "fail" if execution_gate_status != "execution_admitted" else "pass"},
    ]
    with OUT_ROWS.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check", "value", "status"])
        writer.writeheader()
        writer.writerows(rows)

    print(
        "220646_prebayes_bbn_gap=pass "
        f"feedback_rows={len(feedback_rows)} "
        f"branch_paths={len(branch_paths)} "
        f"src_pre_bayes={src_flags['policy_present']} "
        f"bbn_applied={bbn_applied}/{len(bbn_probe_rows)} "
        f"catboost_raw_scored={raw_scored_mature_rows} "
        "full_chain=false"
    )


if __name__ == "__main__":
    main()
