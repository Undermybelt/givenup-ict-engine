#!/usr/bin/env python3
"""Settle the raw 073231 Board A objective-audit command outputs."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = RUN_ROOT.parents[0] / "20260512T073231+0800-codex-current-objective-audit-after-073142-v1"
SOURCE_CMD = SOURCE_ROOT / "command-output"
OUT_DIR = RUN_ROOT / "current-objective-audit-readback-after-073231-v1"
CHECK_DIR = RUN_ROOT / "checks"


def read_text(name: str) -> str:
    path = SOURCE_CMD / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_json_stdout(name: str) -> dict:
    text = read_text(name)
    if not text.strip():
        return {}
    return json.loads(text)


def read_exit(name: str) -> int | None:
    text = read_text(name)
    if not text.strip():
        return None
    return int(text.strip())


def root_statuses() -> dict:
    statuses = {}
    for line in read_text("root_presence.stdout").splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            statuses[parts[0]] = parts[1]
    return statuses


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    exits = {
        "provider_status_agent": read_exit("provider_status_agent.exit"),
        "auto_quant_status": read_exit("auto_quant_status.exit"),
        "pre_bayes_status_nq": read_exit("pre_bayes_status_nq.exit"),
        "workflow_status_nq_agent": read_exit("workflow_status_nq_agent.exit"),
        "export_structural_path_ranking_target_nq": read_exit("export_structural_path_ranking_target_nq.exit"),
        "root_presence": read_exit("root_presence.exit"),
        "board_sha256": read_exit("board_sha256.exit"),
    }
    provider = read_json_stdout("provider_status_agent.stdout")
    auto_quant = read_json_stdout("auto_quant_status.stdout")
    workflow = read_json_stdout("workflow_status_nq_agent.stdout")
    path_target = read_json_stdout("export_structural_path_ranking_target_nq.stdout")
    roots = root_statuses()

    checklist = [
        {
            "requirement": "Every required regime reaches >=95% confidence",
            "evidence": "No valid source/control unlock; Board A source roots remain blocked.",
            "status": "blocked",
        },
        {
            "requirement": "Cross-market and cross-timeframe validation remains valid",
            "evidence": "No source-owned R5 post-cutoff MainRegimeV2 rows, no verifier-native R3 Crisis labels, and no R6 owner/export controls.",
            "status": "blocked",
        },
        {
            "requirement": "Operate ict-engine provider / AutoQuant / Pre-Bayes / workflow readbacks",
            "evidence": "Raw 073231 commands exited 0 for provider-status, auto-quant-status, pre-bayes-status, workflow-status, and export-structural-path-ranking-target.",
            "status": "readback_pass_non_promoting",
        },
        {
            "requirement": "Do not run gated direct verifier / split calibration / canonical merge / downstream promotion without unlock",
            "evidence": "Current roots show R6 and R5 absent; workflow remains blocked by user_selected_historical_data_missing; path ranking has 0 mature/calibrated rows.",
            "status": "guard_preserved",
        },
        {
            "requirement": "Use IBKR, TradingViewRemix, yfinance, Kraken where available",
            "evidence": f"Provider summary: {provider.get('summary_line')}; yfinance and kraken_cli ready; IBKR/TradingView paths unhealthy or dependency-blocked.",
            "status": "partial_provider_readback",
        },
        {
            "requirement": "No update_goal until actual completion",
            "evidence": "Checklist still has blocked requirements and no valid unlock.",
            "status": "not_complete",
        },
    ]

    r6_absent = roots.get("/tmp/ict-engine-board-a-r6-owner-export-v1") == "absent"
    r5_absent = roots.get("/tmp/ict-engine-source-panel-recency-extension") == "absent"
    r3_present_non_promoting = roots.get("/tmp/ict-engine-native-subhour-source-label-intake") == "exists"
    valid_unlock = False

    payload = {
        "run_root": str(RUN_ROOT),
        "source_root": str(SOURCE_ROOT),
        "gate": "current_objective_audit_readback_after_073231_v1",
        "gate_result": "not_complete_required_source_control_unlock_absent_no_downstream",
        "exits": exits,
        "root_statuses": roots,
        "provider_summary_line": provider.get("summary_line"),
        "auto_quant_status": auto_quant.get("status"),
        "auto_quant_healthy": auto_quant.get("healthy"),
        "workflow_blocking_status": workflow.get("blocking_status"),
        "workflow_blocking_reason": workflow.get("blocking_reason"),
        "workflow_next_action": (workflow.get("next_step") or {}).get("action_type"),
        "source_reliability_status": (((workflow.get("structural_validation_summary") or {}).get("source_reliability") or {}).get("status")),
        "path_target_rows": path_target.get("rows"),
        "path_target_mature_rows": path_target.get("mature_rows"),
        "path_target_calibrated_rows": path_target.get("rows_with_calibrated_path_prob"),
        "checklist": checklist,
        "decision": {
            "accepted_rows_added": 0,
            "r6_owner_export_unlock": False,
            "r5_recency_unlock": False,
            "r3_native_subhour_unlock": False,
            "valid_required_root_unlock": valid_unlock,
            "source_control_evidence_acquired": False,
            "direct_verifier_run": False,
            "split_calibration_run": False,
            "canonical_merge": False,
            "provider_autoquant_promotion": False,
            "downstream_promotion_rerun": False,
            "strict_full_objective": False,
            "trade_usable": False,
            "update_goal": False,
        },
    }

    json_path = OUT_DIR / "current_objective_audit_readback_after_073231_v1.json"
    csv_path = OUT_DIR / "prompt_to_artifact_checklist_after_073231_v1.csv"
    md_path = OUT_DIR / "current_objective_audit_readback_after_073231_v1.md"
    assertions_path = CHECK_DIR / "current_objective_audit_readback_after_073231_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["requirement", "status", "evidence"])
        writer.writeheader()
        writer.writerows(checklist)

    md_lines = [
        "# Current Objective Audit Readback After 073231 v1",
        "",
        "## Decision",
        "",
        "- Gate result: `not_complete_required_source_control_unlock_absent_no_downstream`",
        "- Accepted rows added: `0`",
        "- Valid required-root unlock: `false`",
        "- Source/control evidence acquired: `false`",
        "- Direct verifier / split calibration / canonical merge / downstream promotion: `false`",
        "- `update_goal`: `false`",
        "",
        "## Raw Command Readback",
        "",
        f"- Command exits: `{exits}`",
        f"- Provider summary: `{provider.get('summary_line')}`",
        f"- AutoQuant status: `{auto_quant.get('status')}`, healthy `{auto_quant.get('healthy')}`",
        f"- Workflow blocking status: `{workflow.get('blocking_status')}` / `{workflow.get('blocking_reason')}`",
        f"- Workflow next action: `{(workflow.get('next_step') or {}).get('action_type')}`",
        f"- Source reliability status: `{payload['source_reliability_status']}`",
        f"- Structural path target rows: `{path_target.get('rows')}`, mature `{path_target.get('mature_rows')}`, calibrated `{path_target.get('rows_with_calibrated_path_prob')}`",
        "",
        "## Required Roots",
        "",
    ]
    for root, status in roots.items():
        md_lines.append(f"- `{root}`: `{status}`")
    md_lines.extend(
        [
            "",
            "## Prompt-To-Artifact Checklist",
            "",
        ]
    )
    for item in checklist:
        md_lines.append(f"- `{item['status']}` - {item['requirement']}: {item['evidence']}")
    md_lines.extend(
        [
            "",
            "## Next",
            "",
            "Continue source/control acquisition only. Do not run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion until explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export exists.",
            "",
        ]
    )
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    assertions = {
        "gate_result": payload["gate_result"],
        "raw_command_exit_failures": sum(1 for value in exits.values() if value not in (0, None)),
        "r6_root_absent": r6_absent,
        "r5_root_absent": r5_absent,
        "r3_root_present_non_promoting": r3_present_non_promoting,
        "valid_required_root_unlock": valid_unlock,
        "source_control_evidence_acquired": False,
        "path_target_rows": path_target.get("rows"),
        "path_target_mature_rows": path_target.get("mature_rows"),
        "path_target_calibrated_rows": path_target.get("rows_with_calibrated_path_prob"),
        "strict_full_objective": False,
        "update_goal": False,
    }
    assertions_path.write_text(
        "\n".join(f"{key}={str(value).lower() if isinstance(value, bool) else value}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(assertions, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
