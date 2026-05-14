#!/usr/bin/env python3
"""Summarize the completed 015922 Board B trace root without editing it."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "board-b-015922-nonacceptance-readback-v1"
SOURCE_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T015922-codex-board-b-220646-execution-tree-trace-parity-v1/"
    "board-b-220646-execution-tree-trace-parity-v1"
)
CMD = SOURCE_ROOT / "command-output"


def read_exit(name: str) -> int:
    return int((CMD / f"{name}.exit").read_text().strip())


def read_json(name: str) -> dict | None:
    p = CMD / f"{name}.out"
    if not p.exists() or p.stat().st_size == 0:
        return None
    return json.loads(p.read_text())


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (ROOT / "checks").mkdir(parents=True, exist_ok=True)

    command_ids = [
        "00_provider_status",
        "01_auto_quant_status",
        "02_analyze_recorded_data",
        "03_pre_bayes_status",
        "04_policy_training_status",
        "05_workflow_structural_bundle",
        "06_workflow_execution_candidate",
        "07_workflow_full",
    ]
    exits = {name: read_exit(name) for name in command_ids}
    provider = read_json("00_provider_status") or {}
    auto_quant = read_json("01_auto_quant_status") or {}
    pre_bayes = read_json("03_pre_bayes_status") or {}
    policy = read_json("04_policy_training_status") or {}
    structural = read_json("05_workflow_structural_bundle") or {}
    execution = read_json("06_workflow_execution_candidate") or {}
    workflow = read_json("07_workflow_full") or {}

    entry_models = policy.get("entry_models", [])
    matched_rows = sum(int(m.get("matched_rows") or 0) for m in entry_models)
    ranker = policy.get("structural_path_ranking_runtime", {})
    ranker_validation = policy.get("structural_path_ranking_validation", {})
    artifact_summary = workflow.get("artifact_decision_summary", {})

    command_rows = [
        {
            "command_id": name,
            "exit_code": exits[name],
            "stdout_file": str(CMD / f"{name}.out"),
        }
        for name in command_ids
    ]
    write_csv(OUT / "board_b_015922_command_summary_v1.csv", command_rows)

    summary = {
        "run_id": "20260512T021241-codex-board-b-015922-nonacceptance-readback-v1",
        "source_run_root": str(SOURCE_ROOT.parent),
        "gate_result": "board_b_015922_nonacceptance_readback_v1=board_b_trace_not_board_a_acceptance_analyze_exit_143",
        "command_exit_codes": exits,
        "provider_status": provider.get("summary_line"),
        "auto_quant_status": auto_quant.get("status"),
        "auto_quant_healthy": auto_quant.get("healthy"),
        "analyze_recorded_data_exit": exits["02_analyze_recorded_data"],
        "analyze_recorded_data_stdout_bytes": (CMD / "02_analyze_recorded_data.out").stat().st_size,
        "pre_bayes_latest_gate_status": pre_bayes.get("latest_gate_status"),
        "policy_training_matched_rows": matched_rows,
        "policy_training_entry_models_ready": [m.get("ready") for m in entry_models],
        "ranker_runtime_status": ranker.get("status"),
        "ranker_active_match_count": ranker.get("active_match_count"),
        "ranker_production_validation_ready": ranker_validation.get("production_validation_ready"),
        "ranker_production_validation_rows": ranker_validation.get("production_validation_rows"),
        "structural_direction": structural.get("direction"),
        "execution_candidate_actionable": execution.get("actionable"),
        "execution_candidate_status": execution.get("candidate_status"),
        "execution_gate_status": execution.get("execution_gate_status"),
        "workflow_actionable_artifact_count": artifact_summary.get("actionable_artifact_count"),
        "workflow_consumed_targets": artifact_summary.get("consumed_target_kinds"),
        "workflow_consumed_trend_status": artifact_summary.get("consumed_trend_status"),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_promotion_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "source_root_mutated": False,
        "trade_usable": False,
    }
    (OUT / "board_b_015922_nonacceptance_readback_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    report = f"""# Board B 015922 Non-acceptance Readback v1

Gate result: `{summary["gate_result"]}`.

This packet reads the completed `015922` Board B trace-parity root without editing it. It exists only to prevent Board A from treating Board B copied state or trace-parity commands as regime-confidence acceptance evidence.

## Observations

- Provider status: `{summary["provider_status"]}`.
- Auto-Quant status: `{summary["auto_quant_status"]}`, healthy `{summary["auto_quant_healthy"]}`.
- Recorded-data analyze exit: `{summary["analyze_recorded_data_exit"]}` with stdout bytes `{summary["analyze_recorded_data_stdout_bytes"]}`.
- Pre-Bayes latest gate: `{summary["pre_bayes_latest_gate_status"]}`.
- Policy/CatBoost matched rows across entry models: `{summary["policy_training_matched_rows"]}`; entry-model readiness `{summary["policy_training_entry_models_ready"]}`.
- Structural path ranker runtime: `{summary["ranker_runtime_status"]}` with active matches `{summary["ranker_active_match_count"]}`.
- Ranker production validation ready: `{summary["ranker_production_validation_ready"]}` with rows `{summary["ranker_production_validation_rows"]}`.
- Structural bundle direction: `{summary["structural_direction"]}`.
- Execution candidate: actionable `{summary["execution_candidate_actionable"]}`, status `{summary["execution_candidate_status"]}`, gate `{summary["execution_gate_status"]}`.
- Workflow artifact summary: actionable artifacts `{summary["workflow_actionable_artifact_count"]}`, consumed targets `{summary["workflow_consumed_targets"]}`, consumed trend `{summary["workflow_consumed_trend_status"]}`.

## Acceptance

This is not Board A acceptance evidence. The source root is Board B trace-parity material, the recorded-data analyze command exited `143`, the execution candidate stayed observe-only, consumed validation targets are empty, and the root does not add source-owned MainRegimeV2 evidence, R6 owner controls, canonical merge, or trade-usable downstream promotion.
"""
    (OUT / "board_b_015922_nonacceptance_readback_v1.md").write_text(report)

    checks = [
        ("source_root_exists", SOURCE_ROOT.exists()),
        ("analyze_exit_not_success", exits["02_analyze_recorded_data"] != 0),
        ("execution_not_actionable", summary["execution_candidate_actionable"] is False),
        ("no_consumed_targets", summary["workflow_consumed_targets"] == []),
        ("no_accepted_rows", summary["accepted_rows_added"] == 0),
        ("no_goal_update", summary["update_goal"] is False),
    ]
    ok = True
    lines = []
    for name, passed in checks:
        ok = ok and bool(passed)
        lines.append(f"{name}: {'PASS' if passed else 'FAIL'}")
    lines.append(f"overall: {'PASS' if ok else 'FAIL'}")
    (ROOT / "checks" / "board_b_015922_nonacceptance_readback_v1_assertions.out").write_text(
        "\n".join(lines) + "\n"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
