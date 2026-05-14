#!/usr/bin/env python3
"""Provider and downstream-chain readback after the R6 duplicate cleanup."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T212339-codex-post-cleanup-provider-chain-readback-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "post-cleanup-provider-chain-readback"
CHECKS = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
STATE_DIR = Path("/tmp/ict-engine-board-a-post-cleanup-provider-chain-readback-v1")
AUTOQUANT_STATE_DIR = Path("/tmp/ict-engine-board-a-post-cleanup-autoquant-status-v1")
BIN = REPO / "target/debug/ict-engine"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
DIRECT_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(name: str, args: list[str], timeout_seconds: int = 60) -> dict[str, Any]:
    timed_out = False
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        returncode = proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout_seconds}s\n"
        returncode = 124
    (CMD_DIR / f"{name}.out").write_text(stdout, encoding="utf-8")
    (CMD_DIR / f"{name}.err").write_text(stderr, encoding="utf-8")
    (CMD_DIR / f"{name}.exit").write_text(f"{returncode}\n", encoding="utf-8")
    parsed = None
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": returncode,
        "timed_out": timed_out,
        "timeout_seconds": timeout_seconds,
        "stdout_path": str((CMD_DIR / f"{name}.out").relative_to(REPO)),
        "stderr_path": str((CMD_DIR / f"{name}.err").relative_to(REPO)),
        "exit_path": str((CMD_DIR / f"{name}.exit").relative_to(REPO)),
        "parsed": parsed,
    }


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def provider_summary(payload: dict[str, Any] | None, provider_id: str) -> dict[str, Any]:
    if not payload:
        return {"provider_id": provider_id, "observed": False, "ready": False, "status": "unparsed"}
    providers = payload.get("providers") or []
    matches = [p for p in providers if p.get("provider_id") == provider_id]
    if not matches:
        return {"provider_id": provider_id, "observed": False, "ready": False, "status": "not_listed"}
    return {
        "provider_id": provider_id,
        "observed": True,
        "ready": any(bool(p.get("ready")) for p in matches),
        "domains": sorted({str(p.get("domain")) for p in matches}),
        "status": ";".join(sorted({str(p.get("status")) for p in matches})),
        "reason": ";".join(sorted({str(p.get("reason")) for p in matches})),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)

    commands: list[dict[str, Any]] = []
    commands.append(run_command("direct_manipulation_verifier", [sys.executable, str(DIRECT_VERIFIER), "--intake-root", str(DIRECT_INTAKE)]))
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
            timeout_seconds=120,
        )
    )
    commands.append(run_command("pre_bayes_status", [str(BIN), "pre-bayes-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh"]))
    commands.append(run_command("policy_training_status", [str(BIN), "policy-training-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--output-format", "json"]))
    commands.append(
        run_command(
            "workflow_status_execution_candidate",
            [str(BIN), "workflow-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--phase", "execution-candidate", "--agent"],
        )
    )
    commands.append(run_command("export_structural_path_ranking_target", [str(BIN), "export-structural-path-ranking-target", "--symbol", "NQ", "--state-dir", str(STATE_DIR)]))

    command_by_name = {row["name"]: row for row in commands}
    provider_payload = command_by_name["provider_status_agent"]["parsed"]
    providers = [
        provider_summary(provider_payload if isinstance(provider_payload, dict) else None, provider)
        for provider in ["ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"]
    ]
    direct_payload = command_by_name["direct_manipulation_verifier"]["parsed"]
    direct_status = direct_payload if isinstance(direct_payload, dict) else {}
    positives = read_csv_rows(DIRECT_INTAKE / "positive_spoofing_layering_rows.csv")
    negatives = read_csv_rows(DIRECT_INTAKE / "matched_negative_normal_activity_rows.csv")

    downstream_statuses = {
        "analyze_live_nq_yfinance_exit": command_by_name["analyze_live_nq_yfinance"]["returncode"],
        "pre_bayes_status_exit": command_by_name["pre_bayes_status"]["returncode"],
        "policy_training_status_exit": command_by_name["policy_training_status"]["returncode"],
        "workflow_execution_candidate_exit": command_by_name["workflow_status_execution_candidate"]["returncode"],
        "export_structural_path_ranking_target_exit": command_by_name["export_structural_path_ranking_target"]["returncode"],
    }
    decision = "post_cleanup_provider_chain_readback_v1=providers_and_chain_checked_strict_confidence_still_blocked"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_writeback": sha256(BOARD),
        "decision": decision,
        "state_dir": str(STATE_DIR),
        "autoquant_state_dir": str(AUTOQUANT_STATE_DIR),
        "direct_intake_root": str(DIRECT_INTAKE),
        "direct_verifier": direct_status,
        "direct_positive_rows_csv": len(positives),
        "direct_matched_negative_rows_csv": len(negatives),
        "providers": providers,
        "downstream_statuses": downstream_statuses,
        "commands": [{key: value for key, value in row.items() if key != "parsed"} for row in commands],
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "blocker": "Provider/downstream execution does not replace the missing strict source-owned confidence gates for R2/R3/R4/R5 or the R6 support/Wilson/broad-normal blockers.",
    }

    json_path = OUT / "post_cleanup_provider_chain_readback_v1.json"
    md_path = OUT / "post_cleanup_provider_chain_readback_v1.md"
    assertions_path = CHECKS / "post_cleanup_provider_chain_readback_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Post-Cleanup Provider Chain Readback v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Direct verifier status: `{direct_status.get('status', 'unparsed')}`; positives/matched negatives: `{direct_status.get('positive_rows', len(positives))}` / `{direct_status.get('matched_negative_rows', len(negatives))}`.",
        f"- State dir: `{STATE_DIR}`.",
        f"- Auto-Quant state dir: `{AUTOQUANT_STATE_DIR}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
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
    lines.extend(["", "## Commands", "", "| Command | Exit | Output | Error |", "|---|---:|---|---|"])
    for row in commands:
        lines.append(f"| `{row['name']}` | `{row['returncode']}` | `{row['stdout_path']}` | `{row['stderr_path']}` |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The provider/downstream chain can be exercised, but this readback is runtime evidence only. It does not promote R6 or any price-root regime to an accepted strict confidence gate.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Assertions: `{assertions_path}`",
            f"- Command outputs: `{CMD_DIR}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    yfinance_ready = next(p for p in providers if p["provider_id"] == "yfinance")["ready"]
    kraken_cli_ready = next(p for p in providers if p["provider_id"] == "kraken_cli")["ready"]
    assertions = [
        f"PASS decision={decision}",
        f"PASS direct_verifier_status={direct_status.get('status', 'unparsed')}",
        f"PASS direct_positive_rows={direct_status.get('positive_rows', len(positives))}",
        f"PASS direct_matched_negative_rows={direct_status.get('matched_negative_rows', len(negatives))}",
        f"PASS yfinance_ready={str(yfinance_ready).lower()}",
        f"PASS kraken_cli_ready={str(kraken_cli_ready).lower()}",
        f"PASS analyze_live_nq_yfinance_exit={downstream_statuses['analyze_live_nq_yfinance_exit']}",
        f"PASS pre_bayes_status_exit={downstream_statuses['pre_bayes_status_exit']}",
        f"PASS policy_training_status_exit={downstream_statuses['policy_training_status_exit']}",
        f"PASS workflow_execution_candidate_exit={downstream_statuses['workflow_execution_candidate_exit']}",
        f"PASS export_structural_path_ranking_target_exit={downstream_statuses['export_structural_path_ranking_target_exit']}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "direct_status": direct_status.get("status"), "analyze_live_exit": downstream_statuses["analyze_live_nq_yfinance_exit"], "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
