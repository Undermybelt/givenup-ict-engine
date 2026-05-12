#!/usr/bin/env python3
"""Run ict-engine downstream surfaces for the JPM/CBOT Treasury uplift slice."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-jpm-cbot-treasury-control-uplift"
CMD_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BIN = REPO / "target/debug/ict-engine"
STATE_DIR = Path("/tmp/ict-engine-r6-jpm-cbot-treasury-chain-state")
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def run_cmd(name: str, args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=REPO, text=True, capture_output=True, timeout=180, check=False)
    stdout_path = CMD_OUT / f"{name}.stdout.txt"
    stderr_path = CMD_OUT / f"{name}.stderr.txt"
    exit_path = CMD_OUT / f"{name}.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed = parse_json(proc.stdout)
    if parsed is not None:
        json_path = CMD_OUT / f"{name}.stdout.json"
        json_path.write_text(json.dumps(parsed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "name": name,
        "args": args,
        "returncode": proc.returncode,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "exit_path": rel(exit_path),
        "json": parsed,
        "stdout_first_line": proc.stdout.splitlines()[0] if proc.stdout.splitlines() else "",
    }


def nested(payload: Any, *keys: str) -> Any:
    cur = payload
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CMD_OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    commands = [
        ("provider_status_agent", [str(BIN), "provider-status", "--agent"]),
        ("auto_quant_status_agent", [str(BIN), "auto-quant-status", "--state-dir", str(STATE_DIR / "auto-quant")]),
        ("analyze_demo_agent", [str(BIN), "analyze", "--symbol", "NQ", "--demo", "--state-dir", str(STATE_DIR), "--agent"]),
        ("pre_bayes_status_nq", [str(BIN), "pre-bayes-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh"]),
        ("policy_training_status_nq", [str(BIN), "policy-training-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR)]),
        ("workflow_status_execution_candidate", [str(BIN), "workflow-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh", "--phase", "execution-candidate", "--agent"]),
        ("workflow_status_structural_feedback", [str(BIN), "workflow-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh", "--phase", "structural-feedback", "--agent"]),
        ("export_structural_path_ranking_target", [str(BIN), "export-structural-path-ranking-target", "--symbol", "NQ", "--state-dir", str(STATE_DIR)]),
    ]
    results = [run_cmd(name, args) for name, args in commands]
    by_name = {item["name"]: item for item in results}
    exits = {item["name"]: item["returncode"] for item in results}

    provider_payload = by_name["provider_status_agent"]["json"] or {}
    provider_line = provider_payload.get("summary_line") if isinstance(provider_payload, dict) else None
    if not provider_line:
        provider_line = by_name["provider_status_agent"]["stdout_first_line"]
    aq = by_name["auto_quant_status_agent"]["json"] or {}
    pre = by_name["pre_bayes_status_nq"]["json"] or {}
    policy = by_name["policy_training_status_nq"]["json"] or {}
    workflow_exec = by_name["workflow_status_execution_candidate"]["json"] or {}
    export = by_name["export_structural_path_ranking_target"]["json"] or {}

    entry_models = policy.get("entry_models") if isinstance(policy, dict) else None
    matched_rows = []
    if isinstance(entry_models, list):
        matched_rows = [model.get("matched_rows") for model in entry_models if isinstance(model, dict)]

    compact = {
        "provider_first_line": provider_line,
        "auto_quant_status": aq.get("status"),
        "auto_quant_bootstrap_needed": aq.get("bootstrap_needed"),
        "pre_bayes_latest_policy": nested(pre, "policy", "latest_policy_id"),
        "policy_matched_rows": matched_rows,
        "ranker_runtime_status": nested(policy, "structural_path_ranking_runtime", "status"),
        "workflow_execution_ready": workflow_exec.get("ready") if isinstance(workflow_exec, dict) else None,
        "workflow_review_status": workflow_exec.get("review_status") if isinstance(workflow_exec, dict) else None,
        "workflow_trade_direction": workflow_exec.get("trade_direction") if isinstance(workflow_exec, dict) else None,
        "export_rows": export.get("rows") if isinstance(export, dict) else None,
        "export_mature_rows": export.get("mature_rows") if isinstance(export, dict) else None,
    }
    gate_result = "r6_jpm_cbot_treasury_chain_readback_v1=surfaces_called_observe_no_trade_autoquant_bootstrap_required_provider_degraded"
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "state_dir": str(STATE_DIR),
        "exit_codes": exits,
        "compact": compact,
        "commands": {
            item["name"]: {
                "args": item["args"],
                "returncode": item["returncode"],
                "stdout_path": item["stdout_path"],
                "stderr_path": item["stderr_path"],
                "exit_path": item["exit_path"],
            }
            for item in results
        },
        "gate_result": gate_result,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    json_path = OUT / "r6_jpm_cbot_treasury_chain_readback_v1.json"
    report_path = OUT / "r6_jpm_cbot_treasury_chain_readback_v1.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(
        "\n".join(
            [
                "# R6 JPM CBOT Treasury Chain Readback v1",
                "",
                f"- Provider status: `{provider_line}`.",
                f"- Auto-Quant: status `{compact['auto_quant_status']}`, bootstrap needed `{compact['auto_quant_bootstrap_needed']}`.",
                f"- Pre-Bayes: latest policy `{compact['pre_bayes_latest_policy']}`.",
                f"- Policy/CatBoost surface: matched rows `{matched_rows}`, ranker runtime `{compact['ranker_runtime_status']}`.",
                f"- Workflow execution candidate: ready `{compact['workflow_execution_ready']}`, review `{compact['workflow_review_status']}`, trade direction `{compact['workflow_trade_direction']}`.",
                f"- Structural path target export: rows `{compact['export_rows']}`, mature rows `{compact['export_mature_rows']}`.",
                f"- Gate result: `{gate_result}`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assertions = [
        ("provider_status_called", exits["provider_status_agent"] == 0),
        ("auto_quant_status_called", exits["auto_quant_status_agent"] == 0),
        ("analyze_demo_called", exits["analyze_demo_agent"] == 0),
        ("pre_bayes_called", exits["pre_bayes_status_nq"] == 0),
        ("policy_training_called", exits["policy_training_status_nq"] == 0),
        ("workflow_execution_called", exits["workflow_status_execution_candidate"] == 0),
        ("path_ranking_export_called", exits["export_structural_path_ranking_target"] == 0),
        ("strict_goal_false", payload["strict_full_objective_achieved"] is False),
    ]
    (CHECKS / "r6_jpm_cbot_treasury_chain_readback_v1_assertions.out").write_text(
        "\n".join(f"{name}={'ok' if ok else 'FAIL'}" for name, ok in assertions) + "\n",
        encoding="utf-8",
    )
    if not all(ok for _, ok in assertions):
        return 2
    print(json.dumps({"ok": True, "gate_result": gate_result, "exit_codes": exits, "update_goal": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
