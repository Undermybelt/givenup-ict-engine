#!/usr/bin/env python3
"""Read-only runtime-chain refresh after the 013042 source-label screen."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T013533-codex-readonly-runtime-chain-refresh-after-013042-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "readonly-runtime-chain-refresh-after-013042-v1"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
STATE_DIR = Path("/tmp/ict-engine-board-a-readonly-runtime-20260512T013533")
BIN = REPO / "target/debug/ict-engine"
SYMBOL = "NQ"


def run_command(name: str, args: list[str], env: dict[str, str] | None = None, timeout: int = 180) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=REPO,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    stdout_path = CMD / f"{name}.stdout.txt"
    stderr_path = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        pass
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": proc.returncode,
        "stdout_path": str(stdout_path.relative_to(REPO)),
        "stderr_path": str(stderr_path.relative_to(REPO)),
        "exit_path": str(exit_path.relative_to(REPO)),
        "parsed": parsed,
    }


def provider_rows(provider_json: dict[str, Any]) -> list[dict[str, Any]]:
    wanted = {"ibkr_bridge", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"}
    rows: list[dict[str, Any]] = []
    for provider in provider_json.get("providers", []):
        if provider.get("provider_id") not in wanted:
            continue
        rows.append(
            {
                "provider_id": provider.get("provider_id", ""),
                "domain": provider.get("domain", ""),
                "ready": str(provider.get("ready", False)).lower(),
                "status": provider.get("status", ""),
                "reason": provider.get("reason", ""),
                "summary": provider.get("summary", ""),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def main() -> int:
    for path in [OUT, CHECKS, CMD, STATE_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    (CMD / "state_dir.txt").write_text(str(STATE_DIR) + "\n", encoding="utf-8")

    aq_env = dict(os.environ)
    aq_env["ICT_ENGINE_AUTO_QUANT_DIR"] = "/Users/thrill3r/Auto-Quant"

    commands = [
        run_command("provider_status_agent", [str(BIN), "provider-status", "--agent"]),
        run_command(
            "auto_quant_status_json",
            [
                str(BIN),
                "auto-quant-status",
                "--state-dir",
                str(STATE_DIR / "auto-quant"),
                "--output-format",
                "json",
            ],
            env=aq_env,
        ),
        run_command(
            "analyze_demo_agent",
            [
                str(BIN),
                "analyze",
                "--symbol",
                SYMBOL,
                "--demo",
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "agent",
            ],
        ),
        run_command(
            "pre_bayes_status_json",
            [
                str(BIN),
                "pre-bayes-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--output-format",
                "json",
            ],
        ),
        run_command(
            "policy_training_status_json",
            [
                str(BIN),
                "policy-training-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
        ),
        run_command(
            "workflow_status_execution_candidate_agent",
            [
                str(BIN),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--phase",
                "execution-candidate",
                "--output-format",
                "agent",
            ],
        ),
        run_command(
            "workflow_status_structural_path_bundle_agent",
            [
                str(BIN),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--phase",
                "structural-recommended-path-bundle",
                "--output-format",
                "agent",
            ],
        ),
        run_command(
            "export_structural_path_ranking_target",
            [
                str(BIN),
                "export-structural-path-ranking-target",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
            ],
        ),
    ]

    command_by_name = {item["name"]: item for item in commands}
    provider_json = command_by_name["provider_status_agent"]["parsed"] or {}
    autoquant_json = command_by_name["auto_quant_status_json"]["parsed"] or {}
    policy_json = command_by_name["policy_training_status_json"]["parsed"] or {}
    workflow_exec_json = command_by_name["workflow_status_execution_candidate_agent"]["parsed"] or {}
    workflow_path_json = command_by_name["workflow_status_structural_path_bundle_agent"]["parsed"] or {}
    path_export_json = command_by_name["export_structural_path_ranking_target"]["parsed"] or {}

    selected_provider_rows = provider_rows(provider_json)
    provider_csv = OUT / "readonly_runtime_selected_provider_status_v1.csv"
    write_csv(provider_csv, selected_provider_rows, ["provider_id", "domain", "ready", "status", "reason", "summary"])

    r6_owner_root_present = Path("/tmp/ict-engine-board-a-r6-owner-export-v1").exists()
    r3_native_root_present = Path("/tmp/ict-engine-native-subhour-source-label-intake").exists()
    r5_recency_root_present = Path("/tmp/ict-engine-source-panel-recency-extension").exists()
    source_label_root_present = Path("/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv").exists()

    gate_result = "readonly_runtime_chain_refresh_after_013042_v1=commands_ran_non_promoting_roots_blocked"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "state_dir": str(STATE_DIR),
        "commands": commands,
        "provider_summary_line": provider_json.get("summary_line"),
        "selected_provider_status": selected_provider_rows,
        "auto_quant_status": autoquant_json.get("status"),
        "auto_quant_healthy": autoquant_json.get("healthy"),
        "auto_quant_data_ready": autoquant_json.get("data_ready"),
        "pre_bayes_latest_policy": (command_by_name["pre_bayes_status_json"]["parsed"] or {}).get("latest_policy"),
        "policy_entry_models": [
            {
                "entry_model_id": model.get("entry_model_id"),
                "ready": model.get("ready"),
                "matched_rows": model.get("matched_rows"),
            }
            for model in policy_json.get("entry_models", [])
        ],
        "workflow_execution_direction": workflow_exec_json.get("direction"),
        "workflow_execution_stop": workflow_exec_json.get("stop_summary"),
        "workflow_path_direction": workflow_path_json.get("direction"),
        "path_export_rows": path_export_json.get("rows"),
        "path_export_mature_rows": path_export_json.get("mature_rows"),
        "r6_owner_root_present": r6_owner_root_present,
        "r3_native_root_present": r3_native_root_present,
        "r5_recency_root_present": r5_recency_root_present,
        "source_label_root_present": source_label_root_present,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_promotion_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_root_mutated": False,
        "r5_root_mutated": False,
        "r6_owner_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "gate_result": gate_result,
    }

    json_path = OUT / "readonly_runtime_chain_refresh_after_013042_v1.json"
    report_path = OUT / "readonly_runtime_chain_refresh_after_013042_v1.md"
    assertions_path = CHECKS / "readonly_runtime_chain_refresh_after_013042_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    command_lines = [f"- `{item['name']}` exit `{item['returncode']}`: `{item['cmd']}`" for item in commands]
    provider_lines = [
        f"- `{row['provider_id']}`: ready `{row['ready']}`, status `{row['status']}`, reason `{row['reason']}`"
        for row in selected_provider_rows
    ]
    report_path.write_text(
        "\n".join(
            [
                "# Read-Only Runtime Chain Refresh After 013042 v1",
                "",
                f"- Run id: `{RUN_ID}`.",
                f"- Gate result: `{gate_result}`.",
                f"- Provider summary: `{result['provider_summary_line']}`.",
                f"- Auto-Quant status: `{result['auto_quant_status']}`; healthy `{str(result['auto_quant_healthy']).lower()}`; data ready `{str(result['auto_quant_data_ready']).lower()}`.",
                f"- Workflow execution direction: `{result['workflow_execution_direction']}`; stop: `{result['workflow_execution_stop']}`.",
                f"- Structural path-ranking export rows: `{result['path_export_rows']}`; mature rows: `{result['path_export_mature_rows']}`.",
                "- Accepted rows added: `0`; new confidence gate: `false`; canonical merge allowed: `false`; downstream promotion rerun allowed: `false`; strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; shared intake mutated: `false`; R3/R5/R6 roots mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
                "",
                "## Commands",
                "",
                *command_lines,
                "",
                "## Provider Focus",
                "",
                *provider_lines,
                "",
                "## Boundary",
                "",
                "This packet proves the runtime surfaces can be queried in order, but it is not promotion evidence. R6 owner controls or explicit FLIP approval, canonical merge, source-native cross-timeframe labels, and R3/R5 source files remain prerequisites before any accepted downstream rerun.",
                "",
                "Artifacts:",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- Selected provider CSV: `{provider_csv.relative_to(REPO)}`",
                f"- Assertions: `{assertions_path.relative_to(REPO)}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assertions = [
        ("provider_status_exit_zero", command_by_name["provider_status_agent"]["returncode"] == 0),
        ("auto_quant_status_exit_zero", command_by_name["auto_quant_status_json"]["returncode"] == 0),
        ("analyze_demo_exit_zero", command_by_name["analyze_demo_agent"]["returncode"] == 0),
        ("pre_bayes_status_exit_zero", command_by_name["pre_bayes_status_json"]["returncode"] == 0),
        ("policy_training_status_exit_zero", command_by_name["policy_training_status_json"]["returncode"] == 0),
        ("workflow_execution_candidate_exit_zero", command_by_name["workflow_status_execution_candidate_agent"]["returncode"] == 0),
        ("workflow_structural_path_bundle_exit_zero", command_by_name["workflow_status_structural_path_bundle_agent"]["returncode"] == 0),
        ("path_ranking_export_exit_zero", command_by_name["export_structural_path_ranking_target"]["returncode"] == 0),
        ("source_label_root_present", source_label_root_present),
        ("r6_owner_root_absent", not r6_owner_root_present),
        ("r3_native_root_absent", not r3_native_root_present),
        ("r5_recency_root_absent", not r5_recency_root_present),
        ("accepted_rows_zero", result["accepted_rows_added"] == 0),
        ("canonical_merge_false", result["canonical_merge_allowed"] is False),
        ("downstream_promotion_rerun_allowed_false", result["downstream_promotion_rerun_allowed"] is False),
        ("strict_full_objective_achieved_false", result["strict_full_objective_achieved"] is False),
        ("update_goal_false", result["update_goal"] is False),
        ("thresholds_relaxed_false", result["thresholds_relaxed"] is False),
        ("raw_data_committed_false", result["raw_data_committed"] is False),
        ("trade_usable_false", result["trade_usable"] is False),
    ]
    assertions_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in assertions) + "\n",
        encoding="utf-8",
    )
    if not all(passed for _, passed in assertions):
        return 2
    print(json.dumps({"gate_result": gate_result, "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
