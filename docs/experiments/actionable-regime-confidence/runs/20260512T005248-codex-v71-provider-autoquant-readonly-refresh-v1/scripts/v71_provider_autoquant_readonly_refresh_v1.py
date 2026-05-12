#!/usr/bin/env python3
"""Read-only provider and Auto-Quant refresh for the V71 Board A blocker.

This run satisfies the current provider/readiness readback need without
promoting R6 rows or rerunning downstream Pre-Bayes/BBN/CatBoost/execution
surfaces while source-owned controls are still absent.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T005248-codex-v71-provider-autoquant-readonly-refresh-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "v71-provider-autoquant-readonly-refresh"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
STATE_DIR = Path("/tmp/ict-engine-board-a-v71-provider-refresh-state")
BIN = REPO / "target/debug/ict-engine"


def run_command(name: str, args: list[str], env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=REPO,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    stdout_path = CMD / f"{name}.stdout.json"
    stderr_path = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
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
        "parsed": parsed,
    }


def selected_providers(provider_json: dict[str, Any]) -> list[dict[str, Any]]:
    wanted = {"ibkr", "ibkr_bridge", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"}
    rows = []
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    for path in [OUT, CHECKS, CMD, STATE_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    provider_cmd = run_command("provider_status_agent", [str(BIN), "provider-status", "--agent"])
    aq_env = dict(os.environ)
    aq_env["ICT_ENGINE_AUTO_QUANT_DIR"] = "/Users/thrill3r/Auto-Quant"
    autoquant_cmd = run_command(
        "auto_quant_status_agent",
        [
            str(BIN),
            "auto-quant-status",
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "agent",
        ],
        env=aq_env,
    )

    provider_json = provider_cmd["parsed"] or {}
    autoquant_json = autoquant_cmd["parsed"] or {}
    provider_rows = selected_providers(provider_json)
    provider_csv = OUT / "v71_provider_status_selected_v1.csv"
    write_csv(
        provider_csv,
        provider_rows,
        ["provider_id", "domain", "ready", "status", "reason", "summary"],
    )

    gate_result = "v71_provider_autoquant_readonly_refresh_v1=readiness_refreshed_no_promotion_source_control_blocked"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "state_dir": str(STATE_DIR),
        "provider_status": provider_cmd,
        "auto_quant_status": autoquant_cmd,
        "provider_summary_line": provider_json.get("summary_line"),
        "selected_provider_status": provider_rows,
        "auto_quant_status_value": autoquant_json.get("status"),
        "auto_quant_healthy": autoquant_json.get("healthy"),
        "auto_quant_data_ready": autoquant_json.get("data_ready"),
        "auto_quant_next_step": autoquant_json.get("next_step"),
        "canonical_merge_approved": False,
        "source_owned_controls_acquired": False,
        "downstream_chain_rerun": False,
        "gate_result": gate_result,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "owner_export_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }
    json_path = OUT / "v71_provider_autoquant_readonly_refresh_v1.json"
    report_path = OUT / "v71_provider_autoquant_readonly_refresh_v1.md"
    assertions_path = CHECKS / "v71_provider_autoquant_readonly_refresh_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(
        "\n".join(
            [
                "# V71 Provider and Auto-Quant Read-Only Refresh v1",
                "",
                f"- Run id: `{RUN_ID}`.",
                f"- Provider summary: `{provider_json.get('summary_line')}`.",
                f"- Auto-Quant status: `{autoquant_json.get('status')}`; healthy `{str(autoquant_json.get('healthy')).lower()}`; data ready `{str(autoquant_json.get('data_ready')).lower()}`.",
                "- Downstream Pre-Bayes/BBN/CatBoost/execution-tree rerun: `false`, because R6 source-owned controls or explicit FLIP approval are still absent.",
                f"- Gate result: `{gate_result}`.",
                "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; shared intake mutated: `false`; owner-export root mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
                "",
                "Artifacts:",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- Selected provider CSV: `{provider_csv.relative_to(REPO)}`",
                f"- Provider stdout: `{provider_cmd['stdout_path']}`",
                f"- Auto-Quant stdout: `{autoquant_cmd['stdout_path']}`",
                f"- Assertions: `{assertions_path.relative_to(REPO)}`",
                "",
                "Next:",
                "- Preserve the active V71 next action: acquire source-owned CME/Cboe controls or approve FLIP-as-control before any canonical merge or full-chain rerun.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assertions = [
        ("provider_status_exit_zero", provider_cmd["returncode"] == 0),
        ("auto_quant_status_exit_zero", autoquant_cmd["returncode"] == 0),
        ("provider_json_parsed", provider_cmd["parsed"] is not None),
        ("auto_quant_json_parsed", autoquant_cmd["parsed"] is not None),
        ("downstream_chain_not_rerun_without_source_controls", result["downstream_chain_rerun"] is False),
        ("accepted_rows_zero", result["accepted_rows_added"] == 0),
        ("update_goal_false", result["update_goal"] is False),
    ]
    assertions_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in assertions) + "\n",
        encoding="utf-8",
    )
    if not all(passed for _, passed in assertions):
        raise SystemExit(2)
    print(json.dumps({"gate_result": gate_result, "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
