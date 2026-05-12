#!/usr/bin/env python3
import csv
import json
from pathlib import Path


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T015922-codex-board-b-220646-execution-tree-trace-parity-v1"
)
SLICE = RUN_ROOT / "board-b-220646-execution-tree-trace-parity-v1"
CHECKS = RUN_ROOT / "checks"
COMMAND_OUTPUT = SLICE / "command-output"
STATE = SLICE / "state_trace_parity_v1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
BRANCH_PATH = (
    "Sideways -> RangeCarry -> StopManagedRangeCarry -> "
    "SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12"
)


def read_exit(name: str):
    path = COMMAND_OUTPUT / f"{name}.exit"
    if not path.exists():
        return None
    return int(path.read_text().strip())


def read_json(path: Path):
    return json.loads(path.read_text())


def provider_summary():
    data = read_json(COMMAND_OUTPUT / "00_provider_status.out")
    wanted = {}
    for provider in data.get("providers", []):
        pid = provider.get("provider_id", "")
        if pid in {
            "ibkr_bridge",
            "tradingview_mcp",
            "yfinance",
            "kraken_cli",
            "kraken_public",
        }:
            wanted[pid] = {
                "ready": provider.get("ready"),
                "status": provider.get("status"),
                "reason": provider.get("reason"),
            }
    return {
        "summary_line": data.get("summary_line"),
        "providers": wanted,
    }


def main():
    SLICE.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    exits = {
        name: read_exit(name)
        for name in [
            "00_provider_status",
            "01_auto_quant_status",
            "02_analyze_recorded_data",
            "03_pre_bayes_status",
            "04_policy_training_status",
            "05_workflow_structural_bundle",
            "06_workflow_execution_candidate",
            "07_workflow_full",
        ]
    }
    auto_quant = read_json(COMMAND_OUTPUT / "01_auto_quant_status.out")
    pre_bayes = read_json(COMMAND_OUTPUT / "03_pre_bayes_status.out")
    policy = read_json(COMMAND_OUTPUT / "04_policy_training_status.out")
    structural_bundle = read_json(COMMAND_OUTPUT / "05_workflow_structural_bundle.out")
    execution_candidate = read_json(COMMAND_OUTPUT / "06_workflow_execution_candidate.out")
    workflow_full = read_json(COMMAND_OUTPUT / "07_workflow_full.out")
    trace = read_json(STATE / SYMBOL / "execution_tree_trace.json")

    score_line = next(
        (
            line
            for line in trace.get("output", {}).get("split_reason_lineage", [])
            if "ranker_score=path_id=" in line
        ),
        "",
    )
    closed_loop = workflow_full.get("closed_loop_branch_admission") or {}
    trace_closed_loop = trace.get("closed_loop_branch_admission")

    result = {
        "run_root": str(RUN_ROOT),
        "gate_result": (
            "board_b_220646_execution_tree_trace_parity_v1="
            "workflow_branch_fail_closed_visible_trace_parity_not_verified_analyze_interrupted"
        ),
        "command_exits": exits,
        "provider_status": provider_summary(),
        "auto_quant_status": {
            "status": auto_quant.get("status"),
            "healthy": auto_quant.get("healthy"),
            "data_ready": auto_quant.get("data_ready"),
            "managed_dir": auto_quant.get("managed_dir"),
        },
        "pre_bayes": {
            "latest_gate_status": pre_bayes.get("latest_gate_status"),
            "latest_filtered_assignments": pre_bayes.get("latest_filtered_assignments"),
        },
        "catboost_path_ranker": {
            "summary_line": policy.get("summary_line"),
            "runtime": policy.get("structural_path_ranking_runtime"),
            "validation": policy.get("structural_path_ranking_validation"),
        },
        "workflow_structural_bundle": {
            "path_id": structural_bundle.get("path_id"),
            "path_ranker_raw_score": structural_bundle.get("path_ranker_raw_score"),
            "path_ranker_calibrated_path_prob": structural_bundle.get(
                "path_ranker_calibrated_path_prob"
            ),
            "path_ranker_execution_gate_status": structural_bundle.get(
                "path_ranker_execution_gate_status"
            ),
        },
        "workflow_execution_candidate": {
            "source_phase": execution_candidate.get("source_phase"),
            "path_id": execution_candidate.get("path_id"),
            "pre_bayes_gate_status": execution_candidate.get("pre_bayes_gate_status"),
            "execution_gate_status": execution_candidate.get("execution_gate_status"),
            "ready": execution_candidate.get("ready"),
            "actionable": execution_candidate.get("actionable"),
        },
        "workflow_closed_loop_branch_admission": {
            "status": closed_loop.get("status"),
            "path_id": closed_loop.get("path_id"),
            "pre_bayes_gate_status": closed_loop.get("pre_bayes_gate_status"),
            "execution_gate_status": closed_loop.get("execution_gate_status"),
            "review_status": closed_loop.get("review_status"),
            "ready": closed_loop.get("ready"),
            "actionable": closed_loop.get("actionable"),
            "reason": closed_loop.get("reason"),
        },
        "execution_tree_trace": {
            "closed_loop_branch_admission_present": trace_closed_loop is not None,
            "closed_loop_branch_admission": trace_closed_loop,
            "score_line": score_line,
            "output_gate_status": trace.get("output", {}).get("gate_status"),
            "output_branch": trace.get("output", {}).get("branch"),
            "output_execution_bias": trace.get("output", {}).get("execution_bias"),
        },
        "rc_spa_rerun": False,
        "promotion_allowed": False,
        "current_cursor_changed": False,
        "runtime_code_changed_by_this_slice": False,
        "notes": [
            "analyze replay was interrupted with exit 143 after source drift was observed",
            "workflow-status preserves the exact Sideways branch and explicit fail-closed reason",
            "persisted execution_tree_trace.json still lacks closed_loop_branch_admission in this slice",
        ],
    }

    checks = [
        ("provider_status_exit0", exits["00_provider_status"] == 0),
        ("auto_quant_status_exit0", exits["01_auto_quant_status"] == 0),
        ("pre_bayes_status_exit0", exits["03_pre_bayes_status"] == 0),
        ("policy_training_status_exit0", exits["04_policy_training_status"] == 0),
        ("workflow_structural_bundle_exit0", exits["05_workflow_structural_bundle"] == 0),
        ("workflow_execution_candidate_exit0", exits["06_workflow_execution_candidate"] == 0),
        ("workflow_full_exit0", exits["07_workflow_full"] == 0),
        ("analyze_replay_interrupted", exits["02_analyze_recorded_data"] == 143),
        ("workflow_candidate_exact_branch", execution_candidate.get("path_id") == BRANCH_PATH),
        ("workflow_closed_loop_fail_closed", closed_loop.get("status") == "fail_closed"),
        ("workflow_closed_loop_exact_branch", closed_loop.get("path_id") == BRANCH_PATH),
        ("trace_contains_ranker_score_line", BRANCH_PATH in score_line),
        ("trace_closed_loop_missing", trace_closed_loop is None),
        ("promotion_allowed_false", result["promotion_allowed"] is False),
    ]
    result["check_counts"] = {
        "pass": sum(1 for _, ok in checks if ok),
        "fail": sum(1 for _, ok in checks if not ok),
    }

    json_path = SLICE / "board_b_220646_execution_tree_trace_parity_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    checklist_path = SLICE / "board_b_220646_execution_tree_trace_parity_checklist_v1.csv"
    with checklist_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["check", "pass"])
        for name, ok in checks:
            writer.writerow([name, str(ok).lower()])

    assertions_path = CHECKS / "board_b_220646_execution_tree_trace_parity_v1_assertions.out"
    assertions_path.write_text(
        "\n".join(f"{name}={str(ok).lower()}" for name, ok in checks) + "\n"
    )

    report_path = SLICE / "board_b_220646_execution_tree_trace_parity_v1.md"
    report_path.write_text(
        "\n".join(
            [
                "# Board B 220646 Execution-Tree Trace Parity v1",
                "",
                "Scope: copied-state, non-promoting readback for the exact Sideways branch.",
                "",
                f"Gate result: `{result['gate_result']}`.",
                "",
                "Command exits:",
                *[f"- `{name}`: `{code}`" for name, code in exits.items()],
                "",
                "Key readback:",
                f"- Provider summary: `{result['provider_status']['summary_line']}`.",
                f"- Auto-Quant status: `{result['auto_quant_status']['status']}`; healthy `{result['auto_quant_status']['healthy']}`; data_ready `{result['auto_quant_status']['data_ready']}`.",
                f"- Pre-Bayes gate: `{result['pre_bayes']['latest_gate_status']}` with branch `{result['pre_bayes']['latest_filtered_assignments'].get('regime_profit_branch_path')}`.",
                f"- Structural bundle path: `{result['workflow_structural_bundle']['path_id']}`; raw score `{result['workflow_structural_bundle']['path_ranker_raw_score']}`; calibrated `{result['workflow_structural_bundle']['path_ranker_calibrated_path_prob']}`; execution gate `{result['workflow_structural_bundle']['path_ranker_execution_gate_status']}`.",
                f"- Workflow execution-candidate source: `{result['workflow_execution_candidate']['source_phase']}`; ready `{result['workflow_execution_candidate']['ready']}`; actionable `{result['workflow_execution_candidate']['actionable']}`.",
                f"- Workflow closed-loop branch admission: `{result['workflow_closed_loop_branch_admission']['status']}`; reason `{result['workflow_closed_loop_branch_admission']['reason']}`; Pre-Bayes `{result['workflow_closed_loop_branch_admission']['pre_bayes_gate_status']}`; execution `{result['workflow_closed_loop_branch_admission']['execution_gate_status']}`.",
                f"- Execution-tree trace branch line present: `{BRANCH_PATH in score_line}`; trace closed-loop admission present: `{trace_closed_loop is not None}`.",
                "",
                "Result:",
                "- This slice confirms the workflow surfaces preserve the exact rooted branch and explicit fail-closed reason.",
                "- This slice does not close the current Board B blocker because the persisted `execution_tree_trace.json` still lacks `closed_loop_branch_admission` here.",
                "- The recorded-data analyze replay was interrupted with exit `143` after concurrent source drift was observed; no RC-SPA rerun, promotion, cursor update, or runtime-code edit was made by this slice.",
                "",
                "Next:",
                "- Use the freshly built execution-tree branch-admission path, or a later completed run, to produce an execution-tree trace with the same exact branch-level fail-closed record. Do not rerun RC-SPA and do not promote from workflow-only visibility.",
                "",
            ]
        )
    )


if __name__ == "__main__":
    main()
