#!/usr/bin/env python3
"""Restore the registered 021008 closure packet from 020037 command outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ID = "20260512T021008-codex-readonly-runtime-chain-output-closure-after-020037-v1"
SOURCE_RUN_ID = "20260512T020037-codex-readonly-runtime-chain-refresh-after-015533-v1"
GATE_RESULT = "readonly_runtime_chain_output_closure_after_020037_v1=runtime_surfaces_callable_source_roots_absent_no_promotion"
REPO_ROOT = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "readonly-runtime-chain-output-closure-after-020037-v1"
CHECKS = RUN_ROOT / "checks"
SOURCE = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / SOURCE_RUN_ID
COMMANDS = SOURCE / "command-output"
ROOTS = [
    ("r6_owner_export", "/tmp/ict-engine-board-a-r6-owner-export-v1"),
    ("r3_native_subhour", "/tmp/ict-engine-native-subhour-source-label-intake"),
    ("r5_recency_extension", "/tmp/ict-engine-source-panel-recency-extension"),
    ("source_label_equivalence", "/tmp/ict-engine-source-label-equivalence-intake"),
]


def load_json(name: str) -> dict:
    return json.loads((COMMANDS / f"{name}.stdout.txt").read_text(encoding="utf-8"))


def command_rows() -> list[dict]:
    rows = []
    for exit_path in sorted(COMMANDS.glob("*.exit")):
        name = exit_path.name.removesuffix(".exit")
        stdout = COMMANDS / f"{name}.stdout.txt"
        stderr = COMMANDS / f"{name}.stderr.txt"
        rows.append(
            {
                "command": name,
                "exit": int(exit_path.read_text(encoding="utf-8").strip()),
                "stderr_bytes": stderr.stat().st_size,
                "stdout_bytes": stdout.stat().st_size,
            }
        )
    return rows


def provider(provider_status: dict, provider_id: str, domain: str | None = None) -> dict:
    for row in provider_status.get("providers", []):
        if row.get("provider_id") == provider_id and (domain is None or row.get("domain") == domain):
            return row
    return {}


def root_rows() -> list[dict]:
    rows = []
    for name, raw in ROOTS:
        path = Path(raw)
        files = sum(1 for child in path.iterdir() if child.is_file()) if path.exists() else 0
        rows.append({"name": name, "path": raw, "present": path.exists(), "file_count": files})
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    commands = command_rows()
    provider_status = load_json("provider_status_agent")
    tv_status = load_json("provider_status_tradingview_mcp")
    auto_quant = load_json("auto_quant_status_json")
    pre_bayes = load_json("pre_bayes_status_json")
    policy = load_json("policy_training_status_json")
    target = load_json("export_structural_path_ranking_target")
    bundle = load_json("workflow_status_structural_path_bundle_agent")
    candidate = load_json("workflow_status_execution_candidate_agent")
    workflow = load_json("workflow_status_full_json")

    yfinance = provider(provider_status, "yfinance", "live_runtime")
    kraken = provider(provider_status, "kraken_cli", "local_runtime")
    ibkr = provider(provider_status, "ibkr", "market_data")
    tv = (tv_status.get("providers") or [{}])[0]
    roots = root_rows()
    all_zero = all(row["exit"] == 0 for row in commands)
    all_stderr_empty = all(row["stderr_bytes"] == 0 for row in commands)

    packet = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "source_run_root": str(SOURCE.relative_to(REPO_ROOT)),
        "gate_result": GATE_RESULT,
        "command_exit_count": len(commands),
        "all_command_exits_zero": all_zero,
        "all_command_stderr_empty": all_stderr_empty,
        "commands": commands,
        "provider_summary_line": provider_status.get("summary_line"),
        "yfinance_ready": bool(yfinance.get("ready")),
        "kraken_cli_ready": bool(kraken.get("ready")),
        "ibkr_market_data_ready": bool(ibkr.get("ready")),
        "ibkr_market_data_reason": ibkr.get("reason"),
        "tradingview_mcp_ready": bool(tv.get("ready")),
        "tradingview_mcp_reason": tv.get("reason"),
        "auto_quant_status": auto_quant.get("status"),
        "auto_quant_healthy": auto_quant.get("healthy"),
        "auto_quant_data_ready": auto_quant.get("data_ready"),
        "pre_bayes_gate_status": pre_bayes.get("latest_gate_status"),
        "pre_bayes_structural_confidence": pre_bayes.get("latest_canonical_structural_confidence"),
        "pre_bayes_active_regime": pre_bayes.get("latest_canonical_structural_active_regime"),
        "policy_entry_models_ready": [
            row.get("entry_model_id") for row in policy.get("entry_models", []) if row.get("ready")
        ],
        "policy_entry_models_pending": [
            row.get("entry_model_id") for row in policy.get("entry_models", []) if not row.get("ready")
        ],
        "structural_path_ranking_runtime_ready": (policy.get("structural_path_ranking_runtime") or {}).get("ready"),
        "structural_path_ranking_runtime_summary": policy.get("structural_path_ranking_runtime_summary"),
        "structural_target_rows": target.get("rows"),
        "structural_target_mature_rows": target.get("mature_rows"),
        "structural_target_summary_line": target.get("summary_line"),
        "structural_bundle_path_id": bundle.get("path_id"),
        "structural_bundle_direction": bundle.get("direction"),
        "structural_bundle_selected_path_probability": bundle.get("selected_path_probability"),
        "execution_candidate_actionable": candidate.get("actionable"),
        "execution_candidate_ready": candidate.get("ready"),
        "execution_candidate_status": candidate.get("candidate_status"),
        "execution_gate_status": candidate.get("execution_gate_status"),
        "workflow_consumed_trend_status": (workflow.get("artifact_decision_summary") or {}).get("consumed_trend_status"),
        "source_roots": roots,
        "source_roots_required_absent": all(not row["present"] for row in roots[:3]),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_r5_r6_roots_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_vendor_contact_sent": False,
        "trade_usable": False,
    }

    (OUT / "readonly_runtime_chain_output_closure_after_020037_v1.json").write_text(
        json.dumps(packet, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    with (OUT / "readonly_runtime_chain_command_summary_after_020037_v1.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["command", "exit", "stderr_bytes", "stdout_bytes"])
        writer.writeheader()
        writer.writerows(commands)

    with (OUT / "readonly_runtime_chain_provider_summary_after_020037_v1.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["provider", "ready", "reason", "status"])
        writer.writeheader()
        writer.writerows(
            [
                {"provider": "yfinance", "ready": packet["yfinance_ready"], "reason": yfinance.get("reason"), "status": yfinance.get("status")},
                {"provider": "kraken_cli", "ready": packet["kraken_cli_ready"], "reason": kraken.get("reason"), "status": kraken.get("status")},
                {"provider": "ibkr", "ready": packet["ibkr_market_data_ready"], "reason": packet["ibkr_market_data_reason"], "status": ibkr.get("status")},
                {"provider": "tradingview_mcp", "ready": packet["tradingview_mcp_ready"], "reason": packet["tradingview_mcp_reason"], "status": tv.get("status")},
            ]
        )

    report = f"""# Readonly Runtime Chain Output Closure After 020037 v1

Run id: `{RUN_ID}`
Source run id: `{SOURCE_RUN_ID}`
Gate result: `{GATE_RESULT}`

Purpose:
- Restore the registered 021008 closure packet from the existing `020037` command outputs.
- Keep this as callability/readiness evidence only; it does not mutate source roots or rerun promotion.

Command evidence:
- Captured commands: `{len(commands)}`.
- All command exits zero: `{str(all_zero).lower()}`.
- All stderr files empty: `{str(all_stderr_empty).lower()}`.
- Covered surfaces: provider status, yfinance, TradingViewRemix MCP, Auto-Quant status, demo analyze, Pre-Bayes, policy/CatBoost-path status, structural bundle, execution candidate, full workflow, and structural path target export.

Runtime readback:
- Provider summary: `{packet['provider_summary_line']}`.
- yfinance ready: `{str(packet['yfinance_ready']).lower()}`.
- Kraken CLI ready: `{str(packet['kraken_cli_ready']).lower()}`.
- IBKR market-data ready: `{str(packet['ibkr_market_data_ready']).lower()}`; reason `{packet['ibkr_market_data_reason']}`.
- TradingViewRemix MCP ready: `{str(packet['tradingview_mcp_ready']).lower()}`; reason `{packet['tradingview_mcp_reason']}`.
- Auto-Quant status: `{packet['auto_quant_status']}`; healthy `{str(packet['auto_quant_healthy']).lower()}`; data_ready `{str(packet['auto_quant_data_ready']).lower()}`.
- Pre-Bayes gate: `{packet['pre_bayes_gate_status']}`; structural active regime `{packet['pre_bayes_active_regime']}`; confidence `{packet['pre_bayes_structural_confidence']}`.
- Policy/CatBoost entry models ready: `{','.join(packet['policy_entry_models_ready']) or 'none'}`; pending `{','.join(packet['policy_entry_models_pending']) or 'none'}`.
- Structural path ranking runtime ready: `{str(packet['structural_path_ranking_runtime_ready']).lower()}`; `{packet['structural_path_ranking_runtime_summary']}`.
- Structural target export rows: `{packet['structural_target_rows']}`; mature rows `{packet['structural_target_mature_rows']}`; `{packet['structural_target_summary_line']}`.
- Structural bundle selected path: `{packet['structural_bundle_path_id']}` with direction `{packet['structural_bundle_direction']}` and selected probability `{packet['structural_bundle_selected_path_probability']}`.
- Execution candidate actionable: `{str(packet['execution_candidate_actionable']).lower()}`; ready `{str(packet['execution_candidate_ready']).lower()}`; status `{packet['execution_candidate_status']}`; execution gate `{packet['execution_gate_status']}`.
- Full workflow consumed trend status: `{packet['workflow_consumed_trend_status']}`.

Source-root readback:
""" + "\n".join(
        f"- `{row['name']}`: present `{str(row['present']).lower()}`, file_count `{row['file_count']}`, root `{row['path']}`."
        for row in roots
    ) + """

Decision:
- The 020037 command outputs prove runtime surface callability only.
- They do not prove Board A acceptance because R6/R3/R5 source roots are absent, Auto-Quant is not bootstrapped in that isolated state, policy/CatBoost-path training is not ready, structural target rows are immature, and execution candidate remains observe-only.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- `update_goal=false`.

No mutation claims:
- Runtime code changed: `false`.
- Shared intake mutated: `false`.
- R3/R5/R6 roots mutated: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- External vendor/contact sent: `false`.
- Trade usable: `false`.

Next:
- Preserve the Current Cursor next action for R6. Treat `020037`/`021008` as callability evidence only. Continue from the v4 owner/operator request packet, explicit `FLIP` approval, or verifier-native source/control roots before any canonical merge or downstream promotion rerun.
"""
    (OUT / "readonly_runtime_chain_output_closure_after_020037_v1.md").write_text(report, encoding="utf-8")

    assertions = [
        f"gate_result={GATE_RESULT}",
        f"source_run_id={SOURCE_RUN_ID}",
        f"command_exit_count={len(commands)}",
        f"all_command_exits_zero={str(all_zero).lower()}",
        f"all_command_stderr_empty={str(all_stderr_empty).lower()}",
        f"source_roots_required_absent={str(packet['source_roots_required_absent']).lower()}",
        f"auto_quant_status={packet['auto_quant_status']}",
        f"pre_bayes_gate_status={packet['pre_bayes_gate_status']}",
        f"policy_entry_models_ready={len(packet['policy_entry_models_ready'])}",
        f"structural_target_rows={packet['structural_target_rows']}",
        f"structural_target_mature_rows={packet['structural_target_mature_rows']}",
        f"execution_candidate_actionable={str(packet['execution_candidate_actionable']).lower()}",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "canonical_merge_allowed=false",
        "downstream_chain_rerun_allowed=false",
        "strict_full_objective_achieved=false",
        "update_goal=false",
    ]
    (CHECKS / "readonly_runtime_chain_output_closure_after_020037_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )

    assert all_zero
    assert all_stderr_empty
    assert packet["source_roots_required_absent"]
    assert packet["auto_quant_status"] == "missing_dependency"
    assert not packet["execution_candidate_actionable"]
    print(json.dumps({"run_id": RUN_ID, "gate_result": GATE_RESULT, "command_exit_count": len(commands)}, indent=2))


if __name__ == "__main__":
    main()
