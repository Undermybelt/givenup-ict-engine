#!/usr/bin/env python3
"""Provider and downstream-chain readback after canonical R6 intake restoration."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T235910-codex-r6-canonical-intake-v57-materialization-v1"
READBACK_ID = "r6_post_canonical_provider_chain_readback_v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-post-canonical-provider-chain-readback"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
STATE_DIR = Path("/tmp/ict-engine-board-a-r6-post-canonical-chain-v1")
AUTOQUANT_STATE_DIR = Path("/tmp/ict-engine-board-a-r6-post-canonical-autoquant-v1")
BIN = REPO / "target/debug/ict-engine"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
DIRECT_INTAKE = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
V57_JSON = RUN_ROOT / "r6-canonical-intake-v57-materialization/r6_canonical_intake_v57_materialization.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(name: str, args: list[str], timeout_seconds: int = 90) -> dict[str, Any]:
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
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout_seconds}s\n"
        returncode = 124
        timed_out = True
    out_path = CMD / f"{READBACK_ID}_{name}.out"
    err_path = CMD / f"{READBACK_ID}_{name}.err"
    exit_path = CMD / f"{READBACK_ID}_{name}.exit"
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout_path": str(out_path.relative_to(REPO)),
        "stderr_path": str(err_path.relative_to(REPO)),
        "exit_path": str(exit_path.relative_to(REPO)),
        "parsed": parsed,
    }


def provider_summary(payload: dict[str, Any] | None, provider_id: str) -> dict[str, Any]:
    if not payload:
        return {"provider_id": provider_id, "observed": False, "ready": False, "status": "unparsed", "reason": ""}
    matches = [row for row in payload.get("providers", []) if row.get("provider_id") == provider_id]
    if not matches:
        return {"provider_id": provider_id, "observed": False, "ready": False, "status": "not_listed", "reason": ""}
    return {
        "provider_id": provider_id,
        "observed": True,
        "ready": any(bool(row.get("ready")) for row in matches),
        "domains": sorted({str(row.get("domain")) for row in matches}),
        "status": ";".join(sorted({str(row.get("status")) for row in matches})),
        "reason": ";".join(sorted({str(row.get("reason")) for row in matches})),
    }


def read_csv_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def main() -> int:
    for path in [OUT, CHECKS, CMD, STATE_DIR, AUTOQUANT_STATE_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    commands: list[dict[str, Any]] = [
        run_command("direct_manipulation_verifier", [sys.executable, str(DIRECT_VERIFIER), "--intake-root", str(DIRECT_INTAKE)]),
        run_command("provider_status_agent", [str(BIN), "provider-status", "--agent"]),
    ]
    for provider in ["ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"]:
        commands.append(run_command(f"provider_status_{provider}_agent", [str(BIN), "provider-status", "--provider", provider, "--agent"]))
    commands.extend(
        [
            run_command("auto_quant_status", [str(BIN), "auto-quant-status", "--state-dir", str(AUTOQUANT_STATE_DIR), "--output-format", "json"]),
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
                timeout_seconds=150,
            ),
            run_command("pre_bayes_status", [str(BIN), "pre-bayes-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh"]),
            run_command("policy_training_status", [str(BIN), "policy-training-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--output-format", "json"]),
            run_command("workflow_status_execution_candidate", [str(BIN), "workflow-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--phase", "execution-candidate", "--agent"]),
            run_command("export_structural_path_ranking_target", [str(BIN), "export-structural-path-ranking-target", "--symbol", "NQ", "--state-dir", str(STATE_DIR)]),
        ]
    )
    by_name = {row["name"]: row for row in commands}
    direct_payload = by_name["direct_manipulation_verifier"]["parsed"]
    if not isinstance(direct_payload, dict):
        direct_payload = {"status": "unparsed"}
    provider_payload = by_name["provider_status_agent"]["parsed"]
    providers = [
        provider_summary(provider_payload if isinstance(provider_payload, dict) else None, provider)
        for provider in ["ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"]
    ]
    v57 = json.loads(V57_JSON.read_text(encoding="utf-8"))
    decision = "r6_post_canonical_provider_chain_readback_v1=runtime_chain_checked_canonical_intake_schema_ready_but_split_species_blocked"
    result = {
        "run_id": RUN_ID,
        "readback_id": READBACK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "state_dir": str(STATE_DIR),
        "autoquant_state_dir": str(AUTOQUANT_STATE_DIR),
        "direct_intake_root": str(DIRECT_INTAKE),
        "direct_verifier": direct_payload,
        "direct_positive_rows_csv": read_csv_count(DIRECT_INTAKE / "positive_spoofing_layering_rows.csv"),
        "direct_matched_negative_rows_csv": read_csv_count(DIRECT_INTAKE / "matched_negative_normal_activity_rows.csv"),
        "v57_gate_result": v57.get("gate_result"),
        "v57_pooled_wilson95_gate": v57.get("pooled_wilson95_gate"),
        "v57_chronological_split_gate": v57.get("chronological_split_gate"),
        "v57_heldout_symbol_gate": v57.get("heldout_symbol_gate"),
        "v57_heldout_venue_gate": v57.get("heldout_venue_gate"),
        "v57_direct_species_closed": v57.get("direct_species_closed"),
        "providers": providers,
        "commands": [{key: value for key, value in row.items() if key != "parsed"} for row in commands],
        "downstream_statuses": {
            "auto_quant_status_exit": by_name["auto_quant_status"]["returncode"],
            "analyze_live_nq_yfinance_exit": by_name["analyze_live_nq_yfinance"]["returncode"],
            "pre_bayes_status_exit": by_name["pre_bayes_status"]["returncode"],
            "policy_training_status_exit": by_name["policy_training_status"]["returncode"],
            "workflow_execution_candidate_exit": by_name["workflow_status_execution_candidate"]["returncode"],
            "export_structural_path_ranking_target_exit": by_name["export_structural_path_ranking_target"]["returncode"],
        },
        "decision": decision,
        "accepted_rows_added": 0,
        "new_confidence_gate": bool(v57.get("pooled_wilson95_gate")),
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "blocker": "Canonical intake is schema-ready and pooled Wilson95 passes, but chronological, heldout-symbol, heldout-venue, and direct-species closure gates are still false.",
        "next_action": "Source or remap enough direct rows to satisfy chronological/symbol/venue split support and add non-spoofing direct species coverage before any Board A acceptance claim.",
    }
    json_path = OUT / f"{READBACK_ID}.json"
    md_path = OUT / f"{READBACK_ID}.md"
    assertions_path = CHECKS / f"{READBACK_ID}_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# R6 Post-Canonical Provider Chain Readback v1",
        "",
        f"- Decision: `{decision}`.",
        f"- Direct verifier status: `{direct_payload.get('status', 'unparsed')}`.",
        f"- Direct rows: positives `{result['direct_positive_rows_csv']}`, matched negatives `{result['direct_matched_negative_rows_csv']}`.",
        f"- V57 pooled Wilson95 gate: `{str(result['v57_pooled_wilson95_gate']).lower()}`.",
        f"- V57 split gates: chronological `{str(result['v57_chronological_split_gate']).lower()}`, symbol `{str(result['v57_heldout_symbol_gate']).lower()}`, venue `{str(result['v57_heldout_venue_gate']).lower()}`, species `{str(result['v57_direct_species_closed']).lower()}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Providers",
        "",
        "| Provider | Ready | Status | Reason |",
        "|---|---:|---|---|",
    ]
    for provider in providers:
        lines.append(f"| `{provider['provider_id']}` | `{str(provider['ready']).lower()}` | `{provider['status']}` | `{provider['reason']}` |")
    lines.extend(["", "## Commands", "", "| Command | Exit | Output | Error |", "|---|---:|---|---|"])
    for row in commands:
        lines.append(f"| `{row['name']}` | `{row['returncode']}` | `{row['stdout_path']}` | `{row['stderr_path']}` |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = {
        "direct_verifier_schema_ready": direct_payload.get("status") == "schema_ready_unscored",
        "canonical_positive_rows_73": result["direct_positive_rows_csv"] == 73,
        "canonical_matched_negative_rows_73": result["direct_matched_negative_rows_csv"] == 73,
        "providers_checked": all(provider["observed"] for provider in providers),
        "pooled_gate_true": result["v57_pooled_wilson95_gate"] is True,
        "chronological_gate_false": result["v57_chronological_split_gate"] is False,
        "symbol_gate_false": result["v57_heldout_symbol_gate"] is False,
        "venue_gate_false": result["v57_heldout_venue_gate"] is False,
        "direct_species_false": result["v57_direct_species_closed"] is False,
        "strict_full_objective_not_complete": result["strict_full_objective_achieved"] is False,
    }
    assertions_path.write_text(
        "\n".join(f"{name}={'ok' if passed else 'FAIL'}" for name, passed in assertions.items()) + "\n",
        encoding="utf-8",
    )
    if not all(assertions.values()):
        raise SystemExit(2)
    print(json.dumps({"decision": decision, "direct_status": direct_payload.get("status"), "commands": len(commands)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
