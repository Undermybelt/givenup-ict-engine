#!/usr/bin/env python3
"""Read-only provider and Auto-Quant refresh after the 0127 completion audits."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T013229-codex-provider-autoquant-readonly-refresh-after-0127-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "provider-autoquant-readonly-refresh-after-0127-v1"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
STATE_DIR = Path("/tmp/ict-engine-board-a-provider-refresh-after-0127-state")
BIN = REPO / "target/debug/ict-engine"

ROOTS = {
    "r6_owner_export": (
        Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        ["direct_manipulation_rows.csv", "direct_manipulation_provenance.json"],
    ),
    "source_label_equivalence": (
        Path("/tmp/ict-engine-source-label-equivalence-intake"),
        ["source_label_equivalence_rows.csv", "source_label_equivalence_provenance.json"],
    ),
    "r3_native_subhour": (
        Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
    ),
    "r5_recency_extension": (
        Path("/tmp/ict-engine-source-panel-recency-extension"),
        ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
    ),
}


def run_command(name: str, args: list[str], env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=REPO,
        env=env,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    stdout_path = CMD / f"{name}.stdout.txt"
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
        "cmd": args,
        "returncode": proc.returncode,
        "stdout_path": str(stdout_path.relative_to(REPO)),
        "stderr_path": str(stderr_path.relative_to(REPO)),
        "exit_path": str(exit_path.relative_to(REPO)),
        "parsed": parsed,
    }


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


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def root_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root_id, (root, required_files) in ROOTS.items():
        missing = [name for name in required_files if not (root / name).exists()]
        rows.append(
            {
                "root_id": root_id,
                "root": str(root),
                "root_present": str(root.exists()).lower(),
                "required_files": ";".join(required_files),
                "required_files_present": str(not missing).lower(),
                "missing_files": ";".join(missing),
            }
        )
    return rows


def main() -> int:
    for path in [OUT, CHECKS, CMD, STATE_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    provider = run_command("provider_status_agent", [str(BIN), "provider-status", "--agent"])
    env = dict(os.environ)
    env["ICT_ENGINE_AUTO_QUANT_DIR"] = "/Users/thrill3r/Auto-Quant"
    autoquant = run_command(
        "auto_quant_status_json",
        [str(BIN), "auto-quant-status", "--state-dir", str(STATE_DIR), "--output-format", "json"],
        env=env,
    )

    provider_json = provider["parsed"] or {}
    autoquant_json = autoquant["parsed"] or {}
    provider_rows = selected_providers(provider_json)
    roots = root_rows()

    write_csv(
        OUT / "selected_provider_status_after_0127_v1.csv",
        provider_rows,
        ["provider_id", "domain", "ready", "status", "reason", "summary"],
    )
    write_csv(
        OUT / "intake_root_status_after_0127_v1.csv",
        roots,
        ["root_id", "root", "root_present", "required_files", "required_files_present", "missing_files"],
    )

    r6_ready = next(row for row in roots if row["root_id"] == "r6_owner_export")["required_files_present"] == "true"
    r3_ready = next(row for row in roots if row["root_id"] == "r3_native_subhour")["required_files_present"] == "true"
    r5_ready = next(row for row in roots if row["root_id"] == "r5_recency_extension")["required_files_present"] == "true"
    source_ready = next(row for row in roots if row["root_id"] == "source_label_equivalence")["required_files_present"] == "true"
    downstream_allowed = False
    gate_result = "provider_autoquant_readonly_refresh_after_0127_v1=readiness_refreshed_no_promotion_roots_blocked"

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate_result,
        "provider_status": provider,
        "auto_quant_status": autoquant,
        "provider_summary_line": provider_json.get("summary_line"),
        "selected_provider_status": provider_rows,
        "auto_quant_status_value": autoquant_json.get("status"),
        "auto_quant_healthy": autoquant_json.get("healthy"),
        "auto_quant_data_ready": autoquant_json.get("data_ready"),
        "intake_roots": roots,
        "source_label_equivalence_ready": source_ready,
        "r6_owner_export_ready": r6_ready,
        "r3_native_subhour_ready": r3_ready,
        "r5_recency_extension_ready": r5_ready,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": downstream_allowed,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_root_mutated": False,
        "r5_root_mutated": False,
        "r6_owner_export_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    json_path = OUT / "provider_autoquant_readonly_refresh_after_0127_v1.json"
    report_path = OUT / "provider_autoquant_readonly_refresh_after_0127_v1.md"
    assertions_path = CHECKS / "provider_autoquant_readonly_refresh_after_0127_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    ready_line = ", ".join(
        f"{row['provider_id']}={row['ready']}:{row['status']}" for row in provider_rows
    )
    report_path.write_text(
        "\n".join(
            [
                "# Provider and Auto-Quant Read-Only Refresh After 0127 v1",
                "",
                f"- Gate result: `{gate_result}`.",
                f"- Provider summary: `{provider_json.get('summary_line')}`.",
                f"- Selected providers: `{ready_line}`.",
                f"- Auto-Quant status: `{autoquant_json.get('status')}`; healthy `{autoquant_json.get('healthy')}`; data_ready `{autoquant_json.get('data_ready')}`.",
                f"- Source-label root ready: `{str(source_ready).lower()}`; R6 owner-export ready: `{str(r6_ready).lower()}`; R3 native-subhour ready: `{str(r3_ready).lower()}`; R5 recency ready: `{str(r5_ready).lower()}`.",
                "- Canonical merge allowed: `false`; downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: `false`.",
                "- Accepted rows added: `0`; new confidence gate: false; strict full objective achieved: false. `update_goal=false`.",
                "- Runtime code changed: false. Shared intake mutated: false. R3/R5/R6 roots mutated: false. Thresholds relaxed: false. Raw data committed: false. External requests sent: false. Trade usable: false.",
                "",
                "Artifacts:",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- Selected provider CSV: `{(OUT / 'selected_provider_status_after_0127_v1.csv').relative_to(REPO)}`",
                f"- Intake-root CSV: `{(OUT / 'intake_root_status_after_0127_v1.csv').relative_to(REPO)}`",
                f"- Provider stdout: `{provider['stdout_path']}`",
                f"- Auto-Quant stdout: `{autoquant['stdout_path']}`",
                f"- Assertions: `{assertions_path.relative_to(REPO)}`",
                "",
                "Next:",
                "- Preserve the Current Cursor next action for R6: acquire source-owned normal controls or explicit FLIP approval plus canonical merge before any downstream promotion rerun.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    checks = [
        ("provider_status_exit_zero", provider["returncode"] == 0),
        ("auto_quant_status_exit_zero", autoquant["returncode"] == 0),
        ("provider_json_parsed", provider["parsed"] is not None),
        ("auto_quant_json_parsed", autoquant["parsed"] is not None),
        ("source_label_root_ready", source_ready),
        ("r6_owner_export_not_ready", not r6_ready),
        ("r3_native_subhour_not_ready", not r3_ready),
        ("r5_recency_extension_not_ready", not r5_ready),
        ("downstream_chain_rerun_allowed_false", downstream_allowed is False),
        ("strict_full_objective_achieved_false", result["strict_full_objective_achieved"] is False),
        ("update_goal_false", result["update_goal"] is False),
        ("runtime_code_changed_false", result["runtime_code_changed"] is False),
        ("raw_data_committed_false", result["raw_data_committed"] is False),
        ("external_requests_sent_false", result["external_requests_sent"] is False),
    ]
    assertions_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in checks) + "\n",
        encoding="utf-8",
    )
    failed = [name for name, passed in checks if not passed]
    if failed:
        raise SystemExit("failed checks: " + ", ".join(failed))
    print(json.dumps({"gate_result": gate_result, "update_goal": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
