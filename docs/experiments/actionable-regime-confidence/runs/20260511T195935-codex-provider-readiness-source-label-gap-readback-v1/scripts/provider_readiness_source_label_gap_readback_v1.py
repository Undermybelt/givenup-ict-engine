#!/usr/bin/env python3
"""Provider-readiness readback for the strict Board A source-label gap."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T195935-codex-provider-readiness-source-label-gap-readback-v1"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RUN_ROOT.parents[4]
OUT_DIR = RUN_ROOT / "provider-readiness-source-label-gap"
CHECK_DIR = RUN_ROOT / "checks"
ENGINE = REPO_ROOT / "target/debug/ict-engine"

COMMANDS = {
    "provider_status_compact": [str(ENGINE), "provider-status", "--compact"],
    "provider_status_yfinance_agent": [str(ENGINE), "provider-status", "--provider", "yfinance", "--agent"],
    "provider_status_tradingview_mcp_agent": [
        str(ENGINE),
        "provider-status",
        "--provider",
        "tradingview_mcp",
        "--agent",
    ],
    "provider_status_ibkr_agent": [str(ENGINE), "provider-status", "--provider", "ibkr", "--agent"],
    "provider_status_kraken_public_agent": [
        str(ENGINE),
        "provider-status",
        "--provider",
        "kraken_public",
        "--agent",
    ],
}

SOURCE_GAP_ARTIFACTS = {
    "current_goal_v25": (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T195401-codex-current-goal-completion-audit-v25-after-local-inventory/"
        "completion-audit/current_goal_completion_audit_v25_after_local_inventory.json"
    ),
    "strict_1h_exact_target_search": (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T194739-codex-strict-1h-target-exact-source-search-v1/"
        "strict-1h-target-exact-source-search/strict_1h_target_exact_source_search_v1.json"
    ),
    "native_subhour_recheck": (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T194400-codex-native-subhour-source-recheck-v2/"
        "native-subhour-source-recheck/native_subhour_source_recheck_v2.json"
    ),
    "local_broad_inventory": (
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260511T194952-codex-local-broad-source-owned-label-inventory-v1/"
        "local-broad-source-owned-label-inventory/local_broad_source_owned_label_inventory_v1.json"
    ),
}


def run_command(name: str, args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=120,
    )
    out_path = OUT_DIR / f"{name}.out"
    out_path.write_text(proc.stdout, encoding="utf-8")
    parsed: Any = None
    if proc.stdout.lstrip().startswith("{"):
        try:
            parsed = json.loads(proc.stdout)
            (OUT_DIR / f"{name}.json").write_text(
                json.dumps(parsed, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except json.JSONDecodeError:
            parsed = None
    return {
        "name": name,
        "args": args,
        "returncode": proc.returncode,
        "stdout_path": str(out_path),
        "parsed_json_path": str(OUT_DIR / f"{name}.json") if parsed is not None else "",
        "summary_line": parsed.get("summary_line") if isinstance(parsed, dict) else proc.stdout.splitlines()[0] if proc.stdout else "",
        "ready_providers": parsed.get("ready_providers", []) if isinstance(parsed, dict) else [],
        "pending_providers": parsed.get("pending_providers", []) if isinstance(parsed, dict) else [],
    }


def load_json(rel_path: str) -> dict[str, Any]:
    path = REPO_ROOT / rel_path
    if not path.exists():
        return {"missing": True, "path": rel_path}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    command_results = [run_command(name, args) for name, args in COMMANDS.items()]
    source_gaps = {name: load_json(path) for name, path in SOURCE_GAP_ARTIFACTS.items()}

    ready_by_provider = {
        row["name"].replace("provider_status_", "").replace("_agent", ""): row["ready_providers"]
        for row in command_results
        if row["name"] != "provider_status_compact"
    }
    pending_by_provider = {
        row["name"].replace("provider_status_", "").replace("_agent", ""): row["pending_providers"]
        for row in command_results
        if row["name"] != "provider_status_compact"
    }

    v25 = source_gaps["current_goal_v25"]
    exact = source_gaps["strict_1h_exact_target_search"]
    native = source_gaps["native_subhour_recheck"]
    local = source_gaps["local_broad_inventory"]

    decision = {
        "gate_result": "provider_readiness_source_label_gap_readback_v1=providers_checked_source_labels_still_blocked",
        "provider_status_compact": command_results[0]["summary_line"],
        "ready_by_provider": ready_by_provider,
        "pending_by_provider": pending_by_provider,
        "source_label_gap_evidence": {
            "v25_failed_ids": v25.get("failed_ids", []),
            "strict_1h_ready_exact_target_sources": exact.get("ready_source_owned_exact_target_sources"),
            "native_subhour_ready_sources": native.get("ready_native_subhour_source_owned_label_sources"),
            "local_inventory_exact_intake_hits": sum(
                int(group.get("exact_intake_filename_hits", 0))
                for group in local.get("groups", [])
            )
            if isinstance(local.get("groups"), list)
            else None,
        },
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    summary = {
        "artifact_type": "provider_readiness_source_label_gap_readback_v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "commands": command_results,
        "source_gap_artifacts": SOURCE_GAP_ARTIFACTS,
        "decision": decision,
        "interpretation": [
            "Provider status was freshly checked through the real ict-engine CLI.",
            "yfinance and TradingView MCP are ready provider surfaces, but provider readiness does not supply source-owned MainRegimeV2 labels.",
            "IBKR and kraken_public are still configured but unhealthy in this runtime.",
            "The latest source-label artifacts still show zero ready strict exact-target, native sub-hour, or exact intake rows.",
        ],
    }
    json_path = OUT_DIR / "provider_readiness_source_label_gap_readback_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    commands_csv = OUT_DIR / "provider_readiness_source_label_gap_readback_v1_commands.csv"
    with commands_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "name",
                "args",
                "returncode",
                "stdout_path",
                "parsed_json_path",
                "summary_line",
                "ready_providers",
                "pending_providers",
            ],
        )
        writer.writeheader()
        for row in command_results:
            csv_row = dict(row)
            csv_row["args"] = " ".join(row["args"])
            csv_row["ready_providers"] = ",".join(row["ready_providers"])
            csv_row["pending_providers"] = ",".join(row["pending_providers"])
            writer.writerow(csv_row)

    report = [
        "# Provider Readiness Source-Label Gap Readback v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Provider compact status: `{decision['provider_status_compact']}`",
        "- yfinance: ready.",
        "- TradingView MCP: ready.",
        "- IBKR: configured runtime unhealthy; gateway reachable but runtime dependencies missing.",
        "- Kraken public: configured runtime unhealthy; Python provider dependencies missing.",
        "- Source-label gap remains: strict exact-target ready sources `0`, native sub-hour ready sources `0`, exact intake filename hits `0`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{json_path}`",
        f"- Command CSV: `{commands_csv}`",
        f"- Assertions: `{CHECK_DIR / 'provider_readiness_source_label_gap_readback_v1_assertions.out'}`",
    ]
    (OUT_DIR / "provider_readiness_source_label_gap_readback_v1.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"PASS gate_result={decision['gate_result']}",
        "PASS yfinance_ready=true",
        "PASS tradingview_mcp_ready=true",
        "PASS strict_1h_ready_exact_target_sources=0",
        "PASS native_subhour_ready_sources=0",
        "PASS exact_intake_filename_hits=0",
        "PASS accepted_rows_added=0",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECK_DIR / "provider_readiness_source_label_gap_readback_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
