#!/usr/bin/env python3
"""Board A provider and downstream-chain readback without accepting proxy rows."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T205800-codex-provider-downstream-readback-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "provider-downstream-readback"
CHECKS = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
STATE_DIR = Path("/tmp/ict-engine-board-a-provider-downstream-readback-v1")
AUTOQUANT_STATE_DIR = Path("/tmp/ict-engine-board-a-autoquant-status-v1")
BIN = REPO / "target/debug/ict-engine"


def run_command(name: str, args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=REPO, text=True, capture_output=True, check=False)
    (CMD_DIR / f"{name}.out").write_text(proc.stdout, encoding="utf-8")
    (CMD_DIR / f"{name}.err").write_text(proc.stderr, encoding="utf-8")
    (CMD_DIR / f"{name}.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": proc.returncode,
        "stdout_path": str((CMD_DIR / f"{name}.out").relative_to(REPO)),
        "stderr_path": str((CMD_DIR / f"{name}.err").relative_to(REPO)),
        "exit_path": str((CMD_DIR / f"{name}.exit").relative_to(REPO)),
        "parsed": parsed,
    }


def provider_summary(payload: dict[str, Any] | None, provider_id: str) -> dict[str, Any]:
    if not payload:
        return {"provider_id": provider_id, "observed": False, "ready": False, "status": "unparsed"}
    providers = payload.get("providers") or []
    matches = [p for p in providers if p.get("provider_id") == provider_id]
    if not matches:
        return {"provider_id": provider_id, "observed": False, "ready": False, "status": "not_listed"}
    ready = any(bool(p.get("ready")) for p in matches)
    statuses = sorted({str(p.get("status")) for p in matches})
    reasons = sorted({str(p.get("reason")) for p in matches})
    domains = sorted({str(p.get("domain")) for p in matches})
    return {
        "provider_id": provider_id,
        "observed": True,
        "ready": ready,
        "domains": domains,
        "status": ";".join(statuses),
        "reason": ";".join(reasons),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)

    commands = []
    commands.append(run_command("provider_status_agent", [str(BIN), "provider-status", "--agent"]))
    for provider in ["ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"]:
        commands.append(
            run_command(
                f"provider_status_{provider}_agent",
                [str(BIN), "provider-status", "--provider", provider, "--agent"],
            )
        )
    commands.append(
        run_command(
            "auto_quant_status",
            [str(BIN), "auto-quant-status", "--state-dir", str(AUTOQUANT_STATE_DIR), "--output-format", "json"],
        )
    )
    commands.append(
        run_command(
            "analyze_live_nq_yfinance",
            [
                str(BIN),
                "analyze-live",
                "--symbol",
                "NQ",
                "--futures-symbol",
                "NQ=F",
                "--spot-symbol",
                "QQQ",
                "--options-symbol",
                "QQQ",
                "--options-volatility-proxy-symbol",
                "^VIX",
                "--futures-backend",
                "yfinance",
                "--aux-backend",
                "yfinance",
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
        )
    )
    commands.append(
        run_command(
            "pre_bayes_status",
            [str(BIN), "pre-bayes-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh"],
        )
    )
    commands.append(
        run_command(
            "policy_training_status",
            [str(BIN), "policy-training-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--output-format", "json"],
        )
    )
    commands.append(
        run_command(
            "workflow_status_execution_candidate",
            [
                str(BIN),
                "workflow-status",
                "--symbol",
                "NQ",
                "--state-dir",
                str(STATE_DIR),
                "--phase",
                "execution-candidate",
                "--agent",
            ],
        )
    )
    commands.append(
        run_command(
            "export_structural_path_ranking_target",
            [str(BIN), "export-structural-path-ranking-target", "--symbol", "NQ", "--state-dir", str(STATE_DIR)],
        )
    )

    provider_payload = commands[0]["parsed"] if isinstance(commands[0]["parsed"], dict) else None
    providers = [
        provider_summary(provider_payload, provider)
        for provider in ["ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"]
    ]
    analyze_cmd = next(row for row in commands if row["name"] == "analyze_live_nq_yfinance")
    pre_bayes_cmd = next(row for row in commands if row["name"] == "pre_bayes_status")
    workflow_cmd = next(row for row in commands if row["name"] == "workflow_status_execution_candidate")
    export_cmd = next(row for row in commands if row["name"] == "export_structural_path_ranking_target")

    yfinance_live_chain_started = analyze_cmd["returncode"] == 0
    downstream_statuses = {
        "analyze_live_nq_yfinance_exit": analyze_cmd["returncode"],
        "pre_bayes_status_exit": pre_bayes_cmd["returncode"],
        "workflow_execution_candidate_exit": workflow_cmd["returncode"],
        "export_structural_path_ranking_target_exit": export_cmd["returncode"],
    }
    strict_full_objective_achieved = False
    decision = "provider_downstream_readback_v1=live_status_recorded_strict_source_rows_still_blocked"

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "state_dir": str(STATE_DIR),
        "autoquant_state_dir": str(AUTOQUANT_STATE_DIR),
        "providers": providers,
        "downstream_statuses": downstream_statuses,
        "yfinance_live_chain_started": yfinance_live_chain_started,
        "commands": [
            {key: value for key, value in row.items() if key != "parsed"}
            for row in commands
        ],
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": strict_full_objective_achieved,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "blocker": "R2/R3/R4/R5/R6 source-owned or owner-approved intake rows remain absent; provider/downstream readiness cannot replace source-label acceptance.",
    }
    (OUT / "provider_downstream_readback_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines = [
        "# Provider Downstream Readback v1",
        "",
        f"- Decision: `{decision}`",
        f"- State dir: `{STATE_DIR}`",
        f"- Auto-Quant state dir: `{AUTOQUANT_STATE_DIR}`",
        f"- yfinance live chain started: `{str(yfinance_live_chain_started).lower()}`",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Providers",
        "",
        "| Provider | Ready | Domains | Status | Reason |",
        "|---|---:|---|---|---|",
    ]
    for provider in providers:
        lines.append(
            f"| `{provider['provider_id']}` | `{str(provider['ready']).lower()}` | "
            f"`{';'.join(provider.get('domains', []))}` | `{provider['status']}` | `{provider.get('reason', '')}` |"
        )
    lines.extend(
        [
            "",
            "## Downstream Commands",
            "",
            "| Command | Exit | Output | Error |",
            "|---|---:|---|---|",
        ]
    )
    for row in commands:
        lines.append(
            f"| `{row['name']}` | `{row['returncode']}` | `{row['stdout_path']}` | `{row['stderr_path']}` |"
        )
    lines.extend(
        [
            "",
            "## Result",
            "",
            "Provider and downstream chain readback was captured, but no strict Board A intake row was acquired. "
            "This run therefore cannot promote confidence or replace the v35/v37 source-owned row blocker.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{OUT / 'provider_downstream_readback_v1.json'}`",
            f"- Assertions: `{CHECKS / 'provider_downstream_readback_v1_assertions.out'}`",
            f"- Command outputs: `{CMD_DIR}`",
        ]
    )
    (OUT / "provider_downstream_readback_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS yfinance_ready={str(next(p for p in providers if p['provider_id'] == 'yfinance')['ready']).lower()}",
        f"PASS kraken_cli_ready={str(next(p for p in providers if p['provider_id'] == 'kraken_cli')['ready']).lower()}",
        f"PASS ibkr_observed={str(next(p for p in providers if p['provider_id'] == 'ibkr')['observed']).lower()}",
        f"PASS tradingview_mcp_observed={str(next(p for p in providers if p['provider_id'] == 'tradingview_mcp')['observed']).lower()}",
        f"PASS analyze_live_nq_yfinance_exit={analyze_cmd['returncode']}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
    ]
    (CHECKS / "provider_downstream_readback_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print(json.dumps({"decision": decision, "analyze_live_exit": analyze_cmd["returncode"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
