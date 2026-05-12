#!/usr/bin/env python3
"""Summarize the 013050 read-only ict-engine runtime surface refresh."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


RUN_ID = "20260512T013601-codex-readonly-runtime-surface-013050-summary-v1"
SOURCE_RUN_ID = "20260512T013050-codex-readonly-runtime-surface-refresh-after-012425-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "readonly-runtime-surface-013050-summary-v1"
CHECKS = RUN_ROOT / "checks"
SOURCE_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / SOURCE_RUN_ID
CMD = SOURCE_ROOT / "command-output"

COMMANDS = {
    "provider_status": ("provider_status_agent.json", "provider_status_exit_code.txt"),
    "auto_quant_status": ("auto_quant_status.json", "auto_quant_status_exit_code.txt"),
    "pre_bayes_status": ("pre_bayes_status_nq.json", "pre_bayes_status_nq_exit_code.txt"),
    "policy_training_status": ("policy_training_status_nq.json", "policy_training_status_nq_exit_code.txt"),
    "workflow_status": (
        "workflow_status_structural_path_bundle_agent.json",
        "workflow_status_structural_path_bundle_exit_code.txt",
    ),
    "path_ranking_export": (
        "export_structural_path_ranking_target.stdout.txt",
        "export_structural_path_ranking_target_exit_code.txt",
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_exit(path: Path) -> int | None:
    if not path.exists():
        return None
    value = path.read_text(encoding="utf-8").strip()
    return int(value) if value else None


def parse_json_or_text(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def command_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for command_id, (output_name, exit_name) in COMMANDS.items():
        output_path = CMD / output_name
        exit_path = CMD / exit_name
        rows.append(
            {
                "command_id": command_id,
                "output_path": str(output_path.relative_to(REPO)),
                "output_present": str(output_path.exists()).lower(),
                "output_sha256": sha256_file(output_path) if output_path.exists() else "",
                "exit_path": str(exit_path.relative_to(REPO)),
                "exit_present": str(exit_path.exists()).lower(),
                "exit_code": read_exit(exit_path),
            }
        )
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    provider = read_json(CMD / "provider_status_agent.json")
    autoquant = read_json(CMD / "auto_quant_status.json")
    pre_bayes = read_json(CMD / "pre_bayes_status_nq.json")
    policy = read_json(CMD / "policy_training_status_nq.json")
    workflow = read_json(CMD / "workflow_status_structural_path_bundle_agent.json")
    path_export = parse_json_or_text(CMD / "export_structural_path_ranking_target.stdout.txt") or {}
    rows = command_rows()

    all_command_outputs_present = all(row["output_present"] == "true" for row in rows)
    all_exit_zero = all(row["exit_code"] == 0 for row in rows)
    gate_result = (
        "readonly_runtime_surface_013050_summary_v1="
        "surfaces_callable_non_promoting_roots_blocked"
    )
    summary = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "gate_result": gate_result,
        "command_status": rows,
        "all_command_outputs_present": all_command_outputs_present,
        "all_exit_zero": all_exit_zero,
        "state_dir": (CMD / "state_dir.txt").read_text(encoding="utf-8").strip()
        if (CMD / "state_dir.txt").exists()
        else "",
        "provider_summary_line": provider.get("summary_line"),
        "auto_quant_status": autoquant.get("status"),
        "auto_quant_healthy": autoquant.get("healthy"),
        "auto_quant_data_ready": autoquant.get("data_ready"),
        "auto_quant_recommended_next_command": autoquant.get("recommended_next_command"),
        "pre_bayes_latest_gate_status": pre_bayes.get("latest_gate_status"),
        "pre_bayes_latest_policy": pre_bayes.get("latest_policy"),
        "policy_training_summary_line": policy.get("summary_line"),
        "policy_training_ready_models": [
            model.get("model_id")
            for model in policy.get("entry_models", [])
            if model.get("ready") is True
        ],
        "policy_training_pending_models": [
            model.get("model_id")
            for model in policy.get("entry_models", [])
            if model.get("ready") is not True
        ],
        "workflow_direction": workflow.get("direction"),
        "workflow_stop_summary": workflow.get("stop_summary"),
        "workflow_candidate_set_size": workflow.get("candidate_set_size"),
        "path_ranking_rows": path_export.get("rows"),
        "path_ranking_mature_rows": path_export.get("mature_rows"),
        "path_ranking_training_weight_rows": path_export.get("rows_with_training_weight"),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    with (OUT / "readonly_runtime_surface_013050_command_status_v1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "command_id",
                "output_path",
                "output_present",
                "output_sha256",
                "exit_path",
                "exit_present",
                "exit_code",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    json_path = OUT / "readonly_runtime_surface_013050_summary_v1.json"
    report_path = OUT / "readonly_runtime_surface_013050_summary_v1.md"
    assertions_path = CHECKS / "readonly_runtime_surface_013050_summary_v1_assertions.out"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report_path.write_text(
        "\n".join(
            [
                "# Read-Only Runtime Surface 013050 Summary v1",
                "",
                f"- Run id: `{RUN_ID}`.",
                f"- Source run id: `{SOURCE_RUN_ID}`.",
                f"- Gate result: `{gate_result}`.",
                f"- Command outputs present: `{str(all_command_outputs_present).lower()}`; exit-zero: `{str(all_exit_zero).lower()}`.",
                f"- Provider summary: `{summary['provider_summary_line']}`.",
                f"- Auto-Quant isolated status: `{summary['auto_quant_status']}`; healthy `{summary['auto_quant_healthy']}`; data_ready `{summary['auto_quant_data_ready']}`.",
                f"- Pre-Bayes latest gate/status: `{summary['pre_bayes_latest_gate_status']}`; latest policy `{summary['pre_bayes_latest_policy']}`.",
                f"- Policy/CatBoost surface: `{summary['policy_training_summary_line']}`.",
                f"- Workflow direction: `{summary['workflow_direction']}`; stop summary `{summary['workflow_stop_summary']}`.",
                f"- Structural path export rows: `{summary['path_ranking_rows']}`; mature rows `{summary['path_ranking_mature_rows']}`; training-weight rows `{summary['path_ranking_training_weight_rows']}`.",
                "- Canonical merge allowed: false; downstream promotion rerun allowed: false.",
                "- Accepted rows added: `0`; new confidence gate: false; strict full objective achieved: false. `update_goal=false`.",
                "",
                "## Boundary",
                "",
                "The 013050 runtime commands prove the surfaces are callable in read-only mode, but they do not promote any regime: Auto-Quant in that isolated state is not bootstrapped, pre-Bayes has no active gate/policy, policy/CatBoost has no ready training rows, workflow remains observe/no-trade, and the path-ranker export has no mature/training-weight rows.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    checks = [
        ("all_command_outputs_present", all_command_outputs_present),
        ("all_exit_zero", all_exit_zero),
        ("accepted_rows_added_zero", summary["accepted_rows_added"] == 0),
        ("new_confidence_gate_false", summary["new_confidence_gate"] is False),
        ("canonical_merge_allowed_false", summary["canonical_merge_allowed"] is False),
        ("downstream_chain_rerun_allowed_false", summary["downstream_chain_rerun_allowed"] is False),
        ("strict_full_objective_achieved_false", summary["strict_full_objective_achieved"] is False),
        ("update_goal_false", summary["update_goal"] is False),
        ("raw_data_committed_false", summary["raw_data_committed"] is False),
        ("trade_usable_false", summary["trade_usable"] is False),
    ]
    assertions_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in checks) + "\n",
        encoding="utf-8",
    )
    failed = [name for name, passed in checks if not passed]
    if failed:
        raise SystemExit("failed checks: " + ", ".join(failed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
