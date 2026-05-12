#!/usr/bin/env python3
"""Read-only provider and Auto-Quant refresh for the V65 Board A blocker.

This deliberately does not run the downstream Pre-Bayes/BBN/CatBoost/execution
chain, because the current V65 cursor has not approved a canonical R6 row merge.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T003800-codex-v65-provider-autoquant-readonly-refresh-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "v65-provider-autoquant-readonly-refresh"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
STATE_DIR = Path("/tmp/ict-engine-board-a-v65-provider-refresh-state")
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


def provider_by_id(provider_json: dict[str, Any], provider_id: str) -> list[dict[str, Any]]:
    return [
        provider
        for provider in provider_json.get("providers", [])
        if provider.get("provider_id") == provider_id
    ]


def main() -> int:
    for path in [OUT, CHECKS, CMD]:
        path.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

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
    selected = {
        "ibkr": provider_by_id(provider_json, "ibkr"),
        "ibkr_bridge": provider_by_id(provider_json, "ibkr_bridge"),
        "tradingview_mcp": provider_by_id(provider_json, "tradingview_mcp"),
        "yfinance": provider_by_id(provider_json, "yfinance"),
        "kraken_public": provider_by_id(provider_json, "kraken_public"),
        "kraken_cli": provider_by_id(provider_json, "kraken_cli"),
    }
    provider_rows = []
    for provider_id, entries in selected.items():
        for entry in entries:
            provider_rows.append(
                {
                    "provider_id": provider_id,
                    "domain": entry.get("domain", ""),
                    "ready": str(entry.get("ready", False)).lower(),
                    "status": entry.get("status", ""),
                    "reason": entry.get("reason", ""),
                    "summary": entry.get("summary", ""),
                }
            )
    provider_csv = OUT / "v65_provider_status_selected_v1.csv"
    with provider_csv.open("w", encoding="utf-8") as handle:
        handle.write("provider_id,domain,ready,status,reason,summary\n")
        for row in provider_rows:
            handle.write(
                ",".join(
                    json.dumps(str(row[field]))[1:-1]
                    for field in ["provider_id", "domain", "ready", "status", "reason", "summary"]
                )
                + "\n"
            )

    canonical_merge_approved = False
    downstream_chain_rerun = False
    gate_result = (
        "v65_provider_autoquant_readonly_refresh_v1=readiness_refreshed_no_promotion_policy_blocked"
    )
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_path": str(BOARD.relative_to(REPO)),
        "state_dir": str(STATE_DIR),
        "provider_status": provider_cmd,
        "auto_quant_status": autoquant_cmd,
        "selected_provider_status": selected,
        "provider_summary_line": provider_json.get("summary_line"),
        "auto_quant_status_value": autoquant_json.get("status"),
        "auto_quant_healthy": autoquant_json.get("healthy"),
        "auto_quant_data_ready": autoquant_json.get("data_ready"),
        "auto_quant_next_step": autoquant_json.get("next_step"),
        "canonical_merge_approved": canonical_merge_approved,
        "downstream_chain_rerun": downstream_chain_rerun,
        "gate_result": gate_result,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": "Preserve V65: approve RECAP/PACER provenance plus FLIP-control contract, or supply source-owned normal controls, before rerunning downstream chain.",
    }
    json_path = OUT / "v65_provider_autoquant_readonly_refresh_v1.json"
    md_path = OUT / "v65_provider_autoquant_readonly_refresh_v1.md"
    assertions_path = CHECKS / "v65_provider_autoquant_readonly_refresh_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# V65 Provider and Auto-Quant Read-Only Refresh v1",
        "",
        f"- Provider summary: `{provider_json.get('summary_line')}`.",
        f"- Auto-Quant status: `{autoquant_json.get('status')}`; healthy `{str(autoquant_json.get('healthy')).lower()}`; data ready `{str(autoquant_json.get('data_ready')).lower()}`.",
        "- Downstream Pre-Bayes/BBN/CatBoost/execution-tree rerun: `false`, because canonical R6 merge is still policy-blocked.",
        f"- Gate result: `{gate_result}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Provider stdout: `{provider_cmd['stdout_path']}`",
        f"- Auto-Quant stdout: `{autoquant_cmd['stdout_path']}`",
        f"- Selected provider CSV: `{provider_csv.relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        ("provider_status_exit_zero", provider_cmd["returncode"] == 0),
        ("auto_quant_status_exit_zero", autoquant_cmd["returncode"] == 0),
        ("provider_json_parsed", provider_cmd["parsed"] is not None),
        ("auto_quant_json_parsed", autoquant_cmd["parsed"] is not None),
        ("downstream_chain_not_rerun_without_canonical_merge", downstream_chain_rerun is False),
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
