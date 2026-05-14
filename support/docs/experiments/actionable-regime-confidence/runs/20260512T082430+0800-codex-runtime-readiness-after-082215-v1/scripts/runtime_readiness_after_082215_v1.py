#!/usr/bin/env python3
"""Non-promoting runtime readiness readback after the latest Board B source/control gates."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[6]
OUT_DIR = RUN_ROOT / "runtime-readiness-after-082215-v1"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
TMP_STATE = Path("/tmp/ict-engine-board-b-runtime-readiness-20260512T082430")
ICT = REPO / "target/debug/ict-engine"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"


def run_command(name: str, args: list[str], timeout: int = 60) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    proc = subprocess.run(args, cwd=REPO, text=True, capture_output=True, timeout=timeout)
    (CMD_DIR / f"{name}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (CMD_DIR / f"{name}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (CMD_DIR / f"{name}.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    return {
        "name": name,
        "args": args,
        "started_at": started,
        "exit_code": proc.returncode,
        "stdout_path": str((CMD_DIR / f"{name}.stdout.txt").relative_to(REPO)),
        "stderr_path": str((CMD_DIR / f"{name}.stderr.txt").relative_to(REPO)),
        "exit_path": str((CMD_DIR / f"{name}.exit").relative_to(REPO)),
        "stdout_preview": proc.stdout[:2000],
        "stderr_preview": proc.stderr[:2000],
    }


def contains_any(text: str, needles: list[str]) -> bool:
    lower = text.lower()
    return any(needle.lower() in lower for needle in needles)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    TMP_STATE.mkdir(parents=True, exist_ok=True)

    commands = [
        (
            "provider_status_agent",
            [str(ICT), "provider-status", "--agent"],
        ),
        (
            "provider_status_market_data_agent",
            [str(ICT), "provider-status", "--domain", "market_data", "--agent"],
        ),
        (
            "provider_status_live_runtime_agent",
            [str(ICT), "provider-status", "--domain", "live_runtime", "--agent"],
        ),
        (
            "auto_quant_status_json",
            [str(ICT), "auto-quant-status", "--state-dir", str(TMP_STATE), "--output-format", "json"],
        ),
        (
            "pre_bayes_status_nq_json",
            [str(ICT), "pre-bayes-status", "--symbol", "NQ", "--state-dir", str(TMP_STATE), "--refresh", "--output-format", "json"],
        ),
        (
            "policy_training_status_nq_agent",
            [str(ICT), "policy-training-status", "--symbol", "NQ", "--state-dir", str(TMP_STATE), "--output-format", "agent"],
        ),
        (
            "workflow_status_nq_agent",
            [str(ICT), "workflow-status", "--symbol", "NQ", "--state-dir", str(TMP_STATE), "--agent"],
        ),
        (
            "workflow_status_nq_execution_candidate_agent",
            [str(ICT), "workflow-status", "--symbol", "NQ", "--state-dir", str(TMP_STATE), "--phase", "execution-candidate", "--agent"],
        ),
        (
            "export_structural_path_ranking_target_nq",
            [str(ICT), "export-structural-path-ranking-target", "--symbol", "NQ", "--state-dir", str(TMP_STATE)],
        ),
    ]

    command_rows = []
    for name, args in commands:
        command_rows.append(run_command(name, args))

    provider_text = "\n".join(
        (CMD_DIR / f"{row['name']}.stdout.txt").read_text(encoding="utf-8")
        + "\n"
        + (CMD_DIR / f"{row['name']}.stderr.txt").read_text(encoding="utf-8")
        for row in command_rows
        if row["name"].startswith("provider_status")
    )
    provider_mentions = {
        "ibkr": contains_any(provider_text, ["ibkr", "interactive brokers", "ib_async"]),
        "tradingviewremix": contains_any(provider_text, ["tradingviewremix", "tradingview_mcp", "tradingview", "tv_remix"]),
        "yfinance": contains_any(provider_text, ["yfinance", "yahoo"]),
        "kraken": contains_any(provider_text, ["kraken"]),
    }

    board_text = BOARD_B.read_text(encoding="utf-8")
    required_markers = [
        "count_once:082113_board_b_current_objective_audit_after_081705",
        "count_once:082215_r6_recap_novel_pdf_single_retry_after_081323",
    ]
    missing_board_markers = [marker for marker in required_markers if marker not in board_text]
    all_commands_exit0 = all(row["exit_code"] == 0 for row in command_rows)
    provider_surface_mentions_all = all(provider_mentions.values())

    metrics = {
        "run_id": "20260512T082430+0800-codex-runtime-readiness-after-082215-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate_result": "runtime_readiness_after_082215_v1=readiness_observed_but_source_control_and_selected_history_gates_block_promotion",
        "tmp_state_dir": str(TMP_STATE),
        "commands_run": len(command_rows),
        "commands_exit0": sum(1 for row in command_rows if row["exit_code"] == 0),
        "all_commands_exit0": all_commands_exit0,
        "provider_mentions": provider_mentions,
        "provider_surface_mentions_all": provider_surface_mentions_all,
        "missing_board_markers": missing_board_markers,
        "accepted_rows_added": 0,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "explicit_user_selected_history": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    checklist = [
        {
            "requirement": "Run real provider status surfaces including IBKR, TradingViewRemix, yfinance, and Kraken visibility",
            "status": "covered_non_promoting" if provider_surface_mentions_all else "partial_non_promoting",
            "evidence": "provider_status_agent/provider_status_market_data_agent/provider_status_live_runtime_agent command outputs",
            "blocker": "" if provider_surface_mentions_all else "one_or_more_provider_names_not_visible_in_provider_status_output",
        },
        {
            "requirement": "Run Auto-Quant readiness surface",
            "status": "covered_non_promoting",
            "evidence": "auto_quant_status_json command output",
            "blocker": "selected-data AutoQuant promotion still blocked by source/control and selected-history gates",
        },
        {
            "requirement": "Run filter / Pre-Bayes readiness surface",
            "status": "covered_non_promoting",
            "evidence": "pre_bayes_status_nq_json command output",
            "blocker": "no canonical source/control merge input",
        },
        {
            "requirement": "Run BBN / policy-training / CatBoost-path-ranking readiness surfaces",
            "status": "covered_non_promoting",
            "evidence": "policy_training_status_nq_agent and export_structural_path_ranking_target_nq command outputs",
            "blocker": "no accepted source/control root and no selected historical path",
        },
        {
            "requirement": "Run execution-tree/workflow branch surfaces",
            "status": "covered_non_promoting",
            "evidence": "workflow_status_nq_agent and workflow_status_nq_execution_candidate_agent command outputs",
            "blocker": "promotion remains fail-closed before downstream rerun",
        },
        {
            "requirement": "Preserve branch order main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor",
            "status": "blocked",
            "evidence": "No selected-data promotion or canonical merge was allowed in this slice",
            "blocker": "source/control unlock and selected-history gates are false",
        },
        {
            "requirement": "Do not use proxy runtime readiness as completion proof",
            "status": "covered_fail_closed",
            "evidence": "This artifact records readiness only and keeps promotion_allowed=false",
            "blocker": "",
        },
    ]

    with (OUT_DIR / "runtime_readiness_commands_v1.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["name", "exit_code", "stdout_path", "stderr_path", "exit_path"],
        )
        writer.writeheader()
        for row in command_rows:
            writer.writerow({key: row[key] for key in ["name", "exit_code", "stdout_path", "stderr_path", "exit_path"]})

    with (OUT_DIR / "runtime_readiness_checklist_v1.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["requirement", "status", "evidence", "blocker"])
        writer.writeheader()
        writer.writerows(checklist)

    payload = {
        "metrics": metrics,
        "commands": command_rows,
        "checklist": checklist,
    }
    (OUT_DIR / "runtime_readiness_after_082215_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    checklist_md = "\n".join(
        f"| `{row['requirement']}` | `{row['status']}` | {row['evidence']} | {row['blocker']} |"
        for row in checklist
    )
    command_md = "\n".join(
        f"| `{row['name']}` | `{row['exit_code']}` | `{row['stdout_path']}` | `{row['stderr_path']}` |"
        for row in command_rows
    )
    (OUT_DIR / "runtime_readiness_after_082215_v1.md").write_text(
        f"""# Runtime Readiness After 082215 v1

Gate result: `{metrics["gate_result"]}`.

This is a non-promoting live local command readback after the latest Board B
source/control checks. It uses `/tmp` state and does not mutate repo runtime
code, select historical data, run selected-data AutoQuant promotion, or rerun
the downstream promotion chain.

## Command Evidence

| Command | Exit | Stdout | Stderr |
|---|---:|---|---|
{command_md}

## Prompt-to-Artifact Checklist

| Requirement | Status | Evidence | Blocker |
|---|---|---|---|
{checklist_md}

## Decision

- Provider surface mentions: `{metrics["provider_mentions"]}`.
- Commands exit zero: `{metrics["commands_exit0"]}/{metrics["commands_run"]}`.
- Accepted rows added: `0`.
- Valid required-root unlock: `false`.
- Source/control evidence acquired: `false`.
- Explicit user-selected history: `false`.
- Canonical merge: `false`.
- Selected-data AutoQuant promotion: `false`.
- Downstream promotion rerun: `false`.
- Strict full objective: `false`.
- Trade usable: `false`.
- Promotion allowed: `false`.
- `update_goal=false`.

## Next

Continue source/control acquisition or obtain exactly one explicit user-selected
historical path (`HTF`, `MTF`, or `LTF`). Do not run selected-data AutoQuant or
the ordered filter / Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree
promotion chain until both gates are satisfied.
""",
        encoding="utf-8",
    )

    assertion_lines = [
        f"gate_result={metrics['gate_result']}",
        f"commands_run={metrics['commands_run']}",
        f"commands_exit0={metrics['commands_exit0']}",
        f"all_commands_exit0={str(metrics['all_commands_exit0']).lower()}",
        f"provider_ibkr_visible={str(provider_mentions['ibkr']).lower()}",
        f"provider_tradingviewremix_visible={str(provider_mentions['tradingviewremix']).lower()}",
        f"provider_yfinance_visible={str(provider_mentions['yfinance']).lower()}",
        f"provider_kraken_visible={str(provider_mentions['kraken']).lower()}",
        f"provider_surface_mentions_all={str(provider_surface_mentions_all).lower()}",
        f"missing_board_markers={','.join(missing_board_markers) if missing_board_markers else 'none'}",
        "accepted_rows_added=0",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "explicit_user_selected_history=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "runtime_readiness_after_082215_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n",
        encoding="utf-8",
    )
    print("\n".join(assertion_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
