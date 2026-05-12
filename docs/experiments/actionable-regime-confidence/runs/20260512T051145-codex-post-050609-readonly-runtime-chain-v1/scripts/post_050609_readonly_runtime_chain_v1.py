#!/usr/bin/env python3
"""Read-only Board A runtime-chain refresh after the 050609 non-promotion."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T051145-codex-post-050609-readonly-runtime-chain-v1"
SLUG = "post-050609-readonly-runtime-chain-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / SLUG
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
BIN = REPO / "target/debug/ict-engine"
STATE_DIR = REPO / "state"
AQ_STATE_DIR = Path("/tmp/ict-engine-board-a-post-050609-autoquant-status-state")
PATH_EXPORT_ROOT = RUN_ROOT / "structural-path-ranking-target"
SYMBOL = "NQ"


def run_command(name: str, args: list[str], env: dict[str, str] | None = None, timeout: int = 120) -> dict[str, Any]:
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
    cmd_path = CMD / f"{name}.cmd"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    cmd_path.write_text(" ".join(args) + "\n", encoding="utf-8")
    parsed: Any = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": proc.returncode,
        "stdout_path": str(stdout_path.relative_to(REPO)),
        "stderr_path": str(stderr_path.relative_to(REPO)),
        "exit_path": str(exit_path.relative_to(REPO)),
        "cmd_path": str(cmd_path.relative_to(REPO)),
        "stdout_bytes": len(proc.stdout.encode("utf-8")),
        "stderr_bytes": len(proc.stderr.encode("utf-8")),
        "parsed": parsed,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def selected_providers(provider_json: dict[str, Any]) -> list[dict[str, Any]]:
    wanted = {"ibkr", "ibkr_bridge", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"}
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


def workflow_phase_summary(command: dict[str, Any]) -> dict[str, Any]:
    parsed = command.get("parsed")
    if isinstance(parsed, dict):
        return {
            "keys": sorted(parsed.keys()),
            "empty": not bool(parsed),
            "hard_block_count": len(parsed.get("hard_blocks", [])) if isinstance(parsed.get("hard_blocks"), list) else None,
            "actionable_count": len(parsed.get("actionable", [])) if isinstance(parsed.get("actionable"), list) else None,
        }
    return {"keys": [], "empty": True, "hard_block_count": None, "actionable_count": None}


def main() -> int:
    for path in [OUT, CHECKS, CMD, AQ_STATE_DIR, PATH_EXPORT_ROOT]:
        path.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["ICT_ENGINE_AUTO_QUANT_DIR"] = "/Users/thrill3r/Auto-Quant"
    commands = [
        run_command("provider_status_agent", [str(BIN), "provider-status", "--agent"]),
        run_command(
            "auto_quant_status_agent",
            [str(BIN), "auto-quant-status", "--state-dir", str(AQ_STATE_DIR), "--output-format", "json"],
            env=env,
        ),
        run_command(
            "pre_bayes_status_nq_json",
            [str(BIN), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"],
        ),
        run_command(
            "policy_training_status_nq_agent",
            [str(BIN), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "agent"],
        ),
        run_command(
            "workflow_status_structural_recommended_path_bundle_agent",
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
            "workflow_status_structural_feedback_agent",
            [
                str(BIN),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--phase",
                "structural-feedback",
                "--output-format",
                "agent",
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
            "export_structural_path_ranking_target",
            [str(BIN), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
        ),
    ]

    provider_json = commands[0]["parsed"] or {}
    autoquant_json = commands[1]["parsed"] or {}
    provider_rows = selected_providers(provider_json if isinstance(provider_json, dict) else {})
    selected_provider_csv = OUT / "selected_provider_status_v1.csv"
    write_csv(
        selected_provider_csv,
        provider_rows,
        ["provider_id", "domain", "ready", "status", "reason", "summary"],
    )

    command_rows = [
        {
            "name": item["name"],
            "returncode": item["returncode"],
            "stdout_bytes": item["stdout_bytes"],
            "stderr_bytes": item["stderr_bytes"],
            "stdout_path": item["stdout_path"],
            "stderr_path": item["stderr_path"],
        }
        for item in commands
    ]
    command_csv = OUT / "command_status_v1.csv"
    write_csv(
        command_csv,
        command_rows,
        ["name", "returncode", "stdout_bytes", "stderr_bytes", "stdout_path", "stderr_path"],
    )

    phase_rows = [
        {"phase": item["name"], **workflow_phase_summary(item)}
        for item in commands
        if item["name"].startswith("workflow_status_")
    ]
    phase_csv = OUT / "workflow_phase_summary_v1.csv"
    write_csv(phase_csv, phase_rows, ["phase", "keys", "empty", "hard_block_count", "actionable_count"])

    command_failures = [row for row in command_rows if row["returncode"] != 0]
    target_roots = [
        Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        Path("/tmp/ict-engine-source-panel-recency-extension"),
    ]
    target_root_rows = [
        {"path": str(path), "exists": str(path.exists()).lower(), "is_dir": str(path.is_dir()).lower()}
        for path in target_roots
    ]
    target_root_csv = OUT / "target_root_readback_v1.csv"
    write_csv(target_root_csv, target_root_rows, ["path", "exists", "is_dir"])

    gate_result = "post_050609_readonly_runtime_chain_v1=runtime_readback_no_source_unlock_no_promotion"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "symbol": SYMBOL,
        "state_dir": str(STATE_DIR.relative_to(REPO)),
        "auto_quant_state_dir": str(AQ_STATE_DIR),
        "gate_result": gate_result,
        "commands": commands,
        "command_failures": command_failures,
        "provider_summary_line": provider_json.get("summary_line") if isinstance(provider_json, dict) else None,
        "selected_provider_status": provider_rows,
        "auto_quant_status": autoquant_json.get("status") if isinstance(autoquant_json, dict) else None,
        "auto_quant_healthy": autoquant_json.get("healthy") if isinstance(autoquant_json, dict) else None,
        "auto_quant_data_ready": autoquant_json.get("data_ready") if isinstance(autoquant_json, dict) else None,
        "target_roots": target_root_rows,
        "accepted_rows_added": 0,
        "accepted_regime_confidence_labels": 0,
        "source_control_evidence_acquired": False,
        "new_confidence_gate": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }
    json_path = OUT / "post_050609_readonly_runtime_chain_v1.json"
    report_path = OUT / "post_050609_readonly_runtime_chain_v1.md"
    assertions_path = CHECKS / "post_050609_readonly_runtime_chain_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report_lines = [
        "# Post-050609 Read-Only Runtime Chain v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate_result}`",
        "",
        "## Readback",
        "",
        f"- Provider summary: `{result['provider_summary_line']}`.",
        f"- Auto-Quant status: `{result['auto_quant_status']}`; healthy `{str(result['auto_quant_healthy']).lower()}`; data ready `{str(result['auto_quant_data_ready']).lower()}`.",
        f"- Commands executed: `{len(commands)}`; command failures: `{len(command_failures)}`.",
        "- Pre-Bayes, policy-training/CatBoost-facing status, workflow phases, and structural path-ranking export were read-only.",
        "- Required source/control target roots remain absent.",
        "- No canonical merge or downstream promotion rerun was authorized.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Command status CSV: `{command_csv.relative_to(REPO)}`",
        f"- Provider status CSV: `{selected_provider_csv.relative_to(REPO)}`",
        f"- Workflow phase summary CSV: `{phase_csv.relative_to(REPO)}`",
        f"- Target root readback CSV: `{target_root_csv.relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        "",
        "## Boundary",
        "",
        "This packet is runtime readback only. It does not create accepted regime-confidence labels, source/control evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.",
    ]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    assertions = [
        ("all_commands_exit_zero", not command_failures),
        ("source_control_evidence_acquired_false", result["source_control_evidence_acquired"] is False),
        ("target_roots_absent", all(row["exists"] == "false" for row in target_root_rows)),
        ("canonical_merge_false", result["canonical_merge"] is False),
        ("downstream_promotion_rerun_false", result["downstream_promotion_rerun"] is False),
        ("strict_full_objective_false", result["strict_full_objective"] is False),
        ("trade_usable_false", result["trade_usable"] is False),
        ("update_goal_false", result["update_goal"] is False),
    ]
    assertions_path.write_text("\n".join(f"{name}={'PASS' if ok else 'FAIL'}" for name, ok in assertions) + "\n", encoding="utf-8")

    print(json.dumps({"gate_result": gate_result, "command_failures": len(command_failures), "update_goal": False}, sort_keys=True))
    return 0 if all(ok for _, ok in assertions) else 2


if __name__ == "__main__":
    raise SystemExit(main())
