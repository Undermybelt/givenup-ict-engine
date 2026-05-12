#!/usr/bin/env python3
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T013050-codex-readonly-runtime-surface-refresh-after-012425-v1"
BASE = Path(__file__).resolve().parents[6]
RUN_ROOT = BASE / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
COMMAND_DIR = RUN_ROOT / "command-output"
OUT_DIR = RUN_ROOT / "readonly-runtime-surface-refresh-after-012425-v1"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = BASE / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"


def load_json(name: str) -> dict:
    return json.loads((COMMAND_DIR / name).read_text())


def read_exit(name: str) -> int:
    return int((COMMAND_DIR / name).read_text().strip())


def provider_map(provider_status: dict) -> dict:
    return {item.get("provider_id"): item for item in provider_status.get("providers", [])}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text()
    cursor_match = re.search(r"\| last_loop_id \| ([^|]+) \|", board_text)
    cursor = cursor_match.group(1).strip() if cursor_match else "missing"

    provider_status = load_json("provider_status_agent.json")
    auto_quant = load_json("auto_quant_status.json")
    pre_bayes = load_json("pre_bayes_status_nq.json")
    workflow = load_json("workflow_status_structural_path_bundle_agent.json")
    policy = load_json("policy_training_status_nq.json")
    providers = provider_map(provider_status)

    exit_codes = {
        "provider_status": read_exit("provider_status_exit_code.txt"),
        "auto_quant_status": read_exit("auto_quant_status_exit_code.txt"),
        "pre_bayes_status_nq": read_exit("pre_bayes_status_nq_exit_code.txt"),
        "workflow_status_structural_path_bundle": read_exit("workflow_status_structural_path_bundle_exit_code.txt"),
        "policy_training_status_nq": read_exit("policy_training_status_nq_exit_code.txt"),
        "export_structural_path_ranking_target": read_exit("export_structural_path_ranking_target_exit_code.txt"),
    }

    provider_rows = []
    for provider_id in ["yfinance", "ibkr", "ibkr_bridge", "kraken_cli", "kraken_public", "tradingview_mcp"]:
        item = providers.get(provider_id, {})
        provider_rows.append(
            {
                "provider_id": provider_id,
                "ready": str(item.get("ready", False)).lower(),
                "status": item.get("status", "missing"),
                "reason": item.get("reason", "missing"),
                "summary": item.get("summary", ""),
            }
        )

    policy_ready = any(model.get("ready") for model in policy.get("entry_models", []))
    catboost_rows = sum(int(model.get("matched_rows", 0)) for model in policy.get("entry_models", []))
    path_ranking_ready = bool(policy.get("structural_path_ranking_target", {}).get("export_ready"))
    structural_runtime_ready = bool(policy.get("structural_path_ranking_runtime", {}).get("ready"))
    pre_bayes_ready = pre_bayes.get("latest_bridge") is not None or pre_bayes.get("latest_policy") is not None
    auto_quant_ready = bool(auto_quant.get("healthy"))

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "current_cursor_observed": cursor,
        "decision": "readonly_runtime_surface_refresh_after_012425_v1=readiness_refreshed_no_promotion_source_control_blocked",
        "state_dir": (COMMAND_DIR / "state_dir.txt").read_text().strip(),
        "exit_codes": exit_codes,
        "provider_summary_line": provider_status.get("summary_line"),
        "provider_rows": provider_rows,
        "auto_quant_status": auto_quant.get("status"),
        "auto_quant_healthy": auto_quant_ready,
        "auto_quant_next_step": auto_quant.get("recommended_next_command"),
        "pre_bayes_ready": pre_bayes_ready,
        "workflow_path_label": workflow.get("path_label"),
        "workflow_stop": workflow.get("stop_summary"),
        "policy_training_ready": policy_ready,
        "policy_training_matched_rows": catboost_rows,
        "structural_path_ranking_export_ready": path_ranking_ready,
        "structural_path_ranking_runtime_ready": structural_runtime_ready,
        "r6_owner_export_root_present": Path("/tmp/ict-engine-board-a-r6-owner-export-v1").exists(),
        "r3_native_root_present": Path("/tmp/ict-engine-native-subhour-source-label-intake").exists(),
        "r5_recency_root_present": Path("/tmp/ict-engine-source-panel-recency-extension").exists(),
        "source_label_root_present": Path("/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv").exists(),
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    json_path = OUT_DIR / "readonly_runtime_surface_refresh_after_012425_v1.json"
    md_path = OUT_DIR / "readonly_runtime_surface_refresh_after_012425_v1.md"
    provider_csv = OUT_DIR / "provider_readiness_after_012425_v1.csv"
    assertions_path = CHECK_DIR / "readonly_runtime_surface_refresh_after_012425_v1_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    with provider_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["provider_id", "ready", "status", "reason", "summary"])
        writer.writeheader()
        writer.writerows(provider_rows)

    lines = [
        "# Read-only Runtime Surface Refresh After 012425 v1",
        "",
        f"- Decision: `{summary['decision']}`.",
        f"- Current cursor observed: `{cursor}`.",
        f"- Provider summary: `{summary['provider_summary_line']}`.",
        f"- Auto-Quant status: `{summary['auto_quant_status']}`; healthy `{str(auto_quant_ready).lower()}`; next command `{summary['auto_quant_next_step']}`.",
        f"- Pre-Bayes ready: `{str(pre_bayes_ready).lower()}`.",
        f"- Policy training ready: `{str(policy_ready).lower()}`; matched rows `{catboost_rows}`.",
        f"- Structural path ranking export ready: `{str(path_ranking_ready).lower()}`; runtime ready `{str(structural_runtime_ready).lower()}`.",
        f"- Workflow path: `{summary['workflow_path_label']}`; stop `{summary['workflow_stop']}`.",
        f"- Downstream chain rerun allowed: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Provider Readiness",
        "",
        "| Provider | Ready | Status | Reason |",
        "|---|---|---|---|",
    ]
    for row in provider_rows:
        lines.append(f"| `{row['provider_id']}` | `{row['ready']}` | `{row['status']}` | `{row['reason']}` |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This packet summarizes existing read-only command outputs only. It does not bootstrap Auto-Quant, fetch provider data, train BBN/CatBoost, export a structural target, mutate intake roots, or authorize provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(BASE)}`",
            f"- Provider CSV: `{provider_csv.relative_to(BASE)}`",
            f"- Assertions: `{assertions_path.relative_to(BASE)}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n")

    assertions = {
        "all_command_exit_codes_zero": all(code == 0 for code in exit_codes.values()),
        "yfinance_ready": providers.get("yfinance", {}).get("ready") is True,
        "kraken_cli_ready": providers.get("kraken_cli", {}).get("ready") is True,
        "ibkr_not_ready": providers.get("ibkr", {}).get("ready") is False,
        "tradingview_mcp_not_ready": providers.get("tradingview_mcp", {}).get("ready") is False,
        "auto_quant_not_ready": auto_quant_ready is False,
        "pre_bayes_not_ready": pre_bayes_ready is False,
        "policy_training_not_ready": policy_ready is False,
        "path_ranking_not_ready": path_ranking_ready is False and structural_runtime_ready is False,
        "downstream_chain_rerun_allowed_false": summary["downstream_chain_rerun_allowed"] is False,
        "strict_full_objective_achieved_false": summary["strict_full_objective_achieved"] is False,
        "update_goal_false": summary["update_goal"] is False,
        "raw_data_committed_false": summary["raw_data_committed"] is False,
        "trade_usable_false": summary["trade_usable"] is False,
    }
    assertions_path.write_text("\n".join(f"{key}={'PASS' if value else 'FAIL'}" for key, value in assertions.items()) + "\n")
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
