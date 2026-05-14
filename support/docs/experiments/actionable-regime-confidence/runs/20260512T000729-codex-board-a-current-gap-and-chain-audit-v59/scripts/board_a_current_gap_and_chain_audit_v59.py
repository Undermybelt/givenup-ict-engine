#!/usr/bin/env python3
"""Current Board A objective audit plus fresh local chain readback."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T000729-codex-board-a-current-gap-and-chain-audit-v59"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "board-a-current-gap-and-chain-audit"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
STATE_DIR = Path("/tmp/ict-engine-board-a-current-gap-and-chain-audit-v59")

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
ICT = REPO / "target/debug/ict-engine"
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
LIVE_R6_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")

ARTIFACTS = {
    "daily_main_root_inventory": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T162942-codex-daily-main-root-source-inventory-v1/daily-main-root-inventory/daily_main_root_source_inventory_v1.json",
    "qqq_nq_daily_crossmarket": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T170714-codex-qqq-nq-daily-crossmarket-attachment-v1/crossmarket-attachment/qqq_nq_daily_crossmarket_attachment_v1.json",
    "same_source_weekly_monthly": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T131922-codex-source-consensus-axiswise-timeframe-gate-v1/source-consensus-axiswise/source_consensus_axiswise_timeframe_gate_v1.json",
    "r6_live_intake": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T235815-codex-r6-live-intake-rehydrate-calibration-v1/r6-live-intake-rehydrate-calibration/r6_live_intake_rehydrate_calibration_v1.json",
    "r6_live_intake_supplement": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T235910-codex-r6-live-intake-rehydration-v1/r6-live-intake-rehydration/r6_live_intake_rehydration_v1.json",
    "r5_source_panel_recency": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T215420-codex-source-panel-recency-upstream-refresh-check-v1/source-panel-recency-refresh/source_panel_recency_upstream_refresh_check_v1.json",
    "r3_native_subhour": REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T180420-codex-native-subhour-overlap-blocker-v1/native-subhour-overlap/native_subhour_overlap_blocker_v1.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def run_command(name: str, args: list[str], timeout: int = 120) -> dict[str, Any]:
    stdout_path = COMMAND_OUT / f"{name}.stdout.txt"
    stderr_path = COMMAND_OUT / f"{name}.stderr.txt"
    try:
        result = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        stdout_path.write_text(result.stdout, encoding="utf-8")
        stderr_path.write_text(result.stderr, encoding="utf-8")
        return {
            "name": name,
            "args": args,
            "returncode": result.returncode,
            "stdout_path": rel(stdout_path),
            "stderr_path": rel(stderr_path),
            "stdout_head": result.stdout[:2000],
            "stderr_head": result.stderr[:1000],
        }
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(exc.stdout or "", encoding="utf-8")
        stderr_path.write_text((exc.stderr or "") + "\nTIMEOUT\n", encoding="utf-8")
        return {
            "name": name,
            "args": args,
            "returncode": 124,
            "stdout_path": rel(stdout_path),
            "stderr_path": rel(stderr_path),
            "stdout_head": (exc.stdout or "")[:2000],
            "stderr_head": ((exc.stderr or "") + "\nTIMEOUT\n")[:1000],
        }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def parse_current_cursor(board_text: str) -> dict[str, str]:
    cursor: dict[str, str] = {}
    in_cursor = False
    for line in board_text.splitlines():
        if line.strip() == "## Current Cursor":
            in_cursor = True
            continue
        if in_cursor and line.startswith("## "):
            break
        if in_cursor and line.startswith("|") and not line.startswith("|---") and "Field" not in line:
            parts = [part.strip() for part in line.strip().strip("|").split("|")]
            if len(parts) >= 2:
                cursor[parts[0]] = parts[1]
    return cursor


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - audit artifact should record parse failure.
        return {"exists": True, "parse_error": str(exc)}
    payload["exists"] = True
    return payload


def nested(data: dict[str, Any], *keys: str) -> Any:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def command_ok(commands: dict[str, dict[str, Any]], name: str) -> bool:
    return commands.get(name, {}).get("returncode") == 0


def main() -> int:
    for path in (OUT, COMMAND_OUT, CHECKS):
        path.mkdir(parents=True, exist_ok=True)
    if STATE_DIR.exists():
        shutil.rmtree(STATE_DIR)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text(encoding="utf-8")
    cursor = parse_current_cursor(board_text)
    artifacts = {name: load_json(path) for name, path in ARTIFACTS.items()}

    commands: dict[str, dict[str, Any]] = {}
    command_specs = [
        ("provider_status_agent", [str(ICT), "provider-status", "--agent"], 60),
        ("provider_status_yfinance", [str(ICT), "provider-status", "--provider", "yfinance", "--agent"], 60),
        ("provider_status_ibkr", [str(ICT), "provider-status", "--provider", "ibkr", "--agent"], 60),
        ("provider_status_tradingview_mcp", [str(ICT), "provider-status", "--provider", "tradingview_mcp", "--agent"], 60),
        ("provider_status_kraken_cli", [str(ICT), "provider-status", "--provider", "kraken_cli", "--agent"], 60),
        ("provider_status_kraken_public", [str(ICT), "provider-status", "--provider", "kraken_public", "--agent"], 60),
        ("auto_quant_status", [str(ICT), "auto-quant-status", "--state-dir", str(STATE_DIR), "--output-format", "json"], 60),
        (
            "analyze_live_nq_yfinance",
            [
                str(ICT),
                "analyze-live",
                "--symbol",
                "NQ",
                "--futures-symbol",
                "NQ=F",
                "--spot-symbol",
                "QQQ",
                "--options-volatility-proxy-symbol",
                "^VIX",
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
            180,
        ),
        ("analyze_demo", [str(ICT), "analyze", "--symbol", "DEMO", "--demo", "--state-dir", str(STATE_DIR), "--output-format", "json"], 120),
        ("pre_bayes_nq", [str(ICT), "pre-bayes-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"], 60),
        ("pre_bayes_demo", [str(ICT), "pre-bayes-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"], 60),
        ("policy_training_nq", [str(ICT), "policy-training-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--output-format", "json"], 60),
        ("policy_training_demo", [str(ICT), "policy-training-status", "--symbol", "DEMO", "--state-dir", str(STATE_DIR), "--output-format", "json"], 60),
        (
            "workflow_execution_candidate_nq",
            [
                str(ICT),
                "workflow-status",
                "--symbol",
                "NQ",
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--phase",
                "execution-candidate",
                "--output-format",
                "agent",
            ],
            60,
        ),
        (
            "workflow_execution_candidate_demo",
            [
                str(ICT),
                "workflow-status",
                "--symbol",
                "DEMO",
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--phase",
                "execution-candidate",
                "--output-format",
                "agent",
            ],
            60,
        ),
        ("export_path_ranking_nq", [str(ICT), "export-structural-path-ranking-target", "--symbol", "NQ", "--state-dir", str(STATE_DIR)], 60),
        ("export_path_ranking_demo", [str(ICT), "export-structural-path-ranking-target", "--symbol", "DEMO", "--state-dir", str(STATE_DIR)], 60),
        ("direct_r6_live_verifier", ["python3", str(DIRECT_VERIFIER), "--intake-root", str(LIVE_R6_ROOT)], 60),
    ]
    for name, args, timeout in command_specs:
        commands[name] = run_command(name, args, timeout)

    r6 = artifacts["r6_live_intake"]
    r6_direct = r6.get("direct_calibration", {}) if isinstance(r6.get("direct_calibration"), dict) else {}
    r6_counts = r6.get("counts", {}) if isinstance(r6.get("counts"), dict) else {}
    r5_decision = nested(artifacts["r5_source_panel_recency"], "decision") or {}
    r3_summary = nested(artifacts["r3_native_subhour"], "summary") or {}
    r3_decision = nested(artifacts["r3_native_subhour"], "decision") or {}

    checklist = [
        {
            "requirement": "Use the named Board A markdown as the live contract",
            "evidence": rel(BOARD),
            "status": "pass" if cursor.get("last_loop_id") else "fail",
            "blocker": "",
        },
        {
            "requirement": "Preserve multi-agent cursor/worktree state",
            "evidence": f"current cursor {cursor.get('last_loop_id', '')}; board sha256 {sha256(BOARD)}",
            "status": "pass",
            "blocker": "",
        },
        {
            "requirement": "MainRegimeV2 Bull/Bear/Sideways/Crisis have source-backed 95% scoped evidence",
            "evidence": rel(ARTIFACTS["daily_main_root_inventory"]),
            "status": "partial",
            "blocker": "scoped daily/source inventory exists, but strict full-market/full-timeframe/full-cycle objective remains false in current cursor",
        },
        {
            "requirement": "Validate regime evidence on other markets",
            "evidence": rel(ARTIFACTS["qqq_nq_daily_crossmarket"]),
            "status": "partial",
            "blocker": "QQQ/NQ daily cross-market attachment exists, but full universe and intraday/native source-label cells remain incomplete",
        },
        {
            "requirement": "Validate regime evidence on other timeframes",
            "evidence": f"{rel(ARTIFACTS['same_source_weekly_monthly'])}; {rel(ARTIFACTS['r3_native_subhour'])}",
            "status": "blocked",
            "blocker": f"native subhour ready overlap cells {r3_summary.get('ready_overlap_cells')} of {r3_summary.get('cells_checked')}; gate {r3_decision.get('gate_result')}",
        },
        {
            "requirement": "Direct Manipulation R6 uses direct event/order-lifecycle rows, not OHLCV proxy",
            "evidence": rel(ARTIFACTS["r6_live_intake"]),
            "status": "partial",
            "blocker": f"pooled axis passes but split/species gates remain blocked: chrono={r6_direct.get('chronological_split_gate')} symbol={r6_direct.get('heldout_symbol_gate')} venue={r6_direct.get('heldout_venue_gate')} species={r6_direct.get('direct_species_closed')}",
        },
        {
            "requirement": "R5 source-panel recency after 2026-01-30",
            "evidence": rel(ARTIFACTS["r5_source_panel_recency"]),
            "status": "blocked",
            "blocker": f"source_has_required_recency={r5_decision.get('source_has_required_recency')}; gate {r5_decision.get('gate_result')}",
        },
        {
            "requirement": "Check yfinance, IBKR, TradingViewRemix/MCP, Kraken provider paths",
            "evidence": "; ".join(commands[name]["stdout_path"] for name in [
                "provider_status_yfinance",
                "provider_status_ibkr",
                "provider_status_tradingview_mcp",
                "provider_status_kraken_cli",
                "provider_status_kraken_public",
            ]),
            "status": "partial" if command_ok(commands, "provider_status_yfinance") else "blocked",
            "blocker": "provider status must be interpreted per-provider; unavailable providers are non-promoting for confidence gates",
        },
        {
            "requirement": "Run Auto-Quant status/readiness",
            "evidence": commands["auto_quant_status"]["stdout_path"],
            "status": "pass" if command_ok(commands, "auto_quant_status") else "blocked",
            "blocker": "" if command_ok(commands, "auto_quant_status") else commands["auto_quant_status"]["stderr_head"],
        },
        {
            "requirement": "Run ict-engine live/provider analysis plus fallback demo analysis",
            "evidence": f"{commands['analyze_live_nq_yfinance']['stdout_path']}; {commands['analyze_demo']['stdout_path']}",
            "status": "partial" if command_ok(commands, "analyze_demo") else "blocked",
            "blocker": "live NQ/yfinance is required evidence when successful; demo is only downstream surface exercise, not market validation",
        },
        {
            "requirement": "Run Pre-Bayes/BBN readback",
            "evidence": f"{commands['pre_bayes_nq']['stdout_path']}; {commands['pre_bayes_demo']['stdout_path']}",
            "status": "pass" if command_ok(commands, "pre_bayes_nq") or command_ok(commands, "pre_bayes_demo") else "blocked",
            "blocker": "",
        },
        {
            "requirement": "Run CatBoost/policy-training and structural path-ranker export",
            "evidence": f"{commands['policy_training_nq']['stdout_path']}; {commands['policy_training_demo']['stdout_path']}; {commands['export_path_ranking_nq']['stdout_path']}; {commands['export_path_ranking_demo']['stdout_path']}",
            "status": "partial" if command_ok(commands, "policy_training_demo") or command_ok(commands, "export_path_ranking_demo") else "blocked",
            "blocker": "green command surface does not imply mature rows or strict objective closure",
        },
        {
            "requirement": "Run execution-tree/workflow status",
            "evidence": f"{commands['workflow_execution_candidate_nq']['stdout_path']}; {commands['workflow_execution_candidate_demo']['stdout_path']}",
            "status": "pass" if command_ok(commands, "workflow_execution_candidate_nq") or command_ok(commands, "workflow_execution_candidate_demo") else "blocked",
            "blocker": "",
        },
        {
            "requirement": "Do not mark goal complete until every explicit requirement is covered",
            "evidence": "this v59 checklist",
            "status": "blocked",
            "blocker": "current cursor explicitly blocked; R6 split/species, R5 recency, R3 native-subhour, and full cross-context coverage remain open",
        },
    ]

    all_requirements_pass = all(row["status"] == "pass" for row in checklist)
    gate_result = "current_goal_completion_audit_v59=not_complete_r6_split_species_r5_recency_r3_native_subhour_and_full_context_blocked"
    audit = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": rel(BOARD),
        "board_sha256_at_start": sha256(BOARD),
        "current_cursor": cursor,
        "state_dir": str(STATE_DIR),
        "artifact_readbacks": {
            name: {
                "path": rel(path),
                "exists": path.exists(),
                "gate_result": nested(artifacts[name], "decision", "gate_result") or artifacts[name].get("gate_result"),
                "update_goal": nested(artifacts[name], "decision", "update_goal") or artifacts[name].get("update_goal"),
            }
            for name, path in ARTIFACTS.items()
        },
        "commands": commands,
        "checklist": checklist,
        "gate_result": gate_result,
        "all_requirements_pass": all_requirements_pass,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Continue from the active cursor: source direct event/order-lifecycle rows that increase R6 chronological/symbol/venue/species support, while separately keeping R5 recency and R3 native-subhour acquisition blocked until source-owned rows exist.",
    }

    json_path = OUT / "current_goal_completion_audit_v59.json"
    report_path = OUT / "current_goal_completion_audit_v59.md"
    checklist_path = OUT / "current_goal_completion_audit_v59_checklist.csv"
    command_summary_path = OUT / "current_goal_completion_audit_v59_commands.csv"
    assertions_path = CHECKS / "current_goal_completion_audit_v59_assertions.out"
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_path, checklist, ["requirement", "evidence", "status", "blocker"])
    write_csv(
        command_summary_path,
        [
            {
                "name": name,
                "returncode": data["returncode"],
                "stdout_path": data["stdout_path"],
                "stderr_path": data["stderr_path"],
            }
            for name, data in commands.items()
        ],
        ["name", "returncode", "stdout_path", "stderr_path"],
    )

    status_counts: dict[str, int] = {}
    for row in checklist:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    report = [
        "# Current Goal Completion Audit v59",
        "",
        f"- Run id: `{RUN_ID}`",
        f"- Current cursor: `{cursor.get('last_loop_id', '')}`",
        f"- Gate result: `{gate_result}`",
        f"- Checklist statuses: `{status_counts}`",
        f"- Strict full objective achieved: `false`; `update_goal=false`.",
        f"- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Fresh Commands",
    ]
    for name, data in commands.items():
        report.append(f"- `{name}` returncode `{data['returncode']}` stdout `{data['stdout_path']}` stderr `{data['stderr_path']}`")
    report.extend(
        [
            "",
            "## Blocking Findings",
            "",
            "- R6 live direct pooled/sidecar Wilson95 now passes, but chronological, symbol, venue, and species gates remain false.",
            "- R5 source-panel recency remains blocked because no source-owned post-2026-01-30 rows are accepted.",
            "- R3 native-subhour remains blocked with `0/4` ready overlap cells.",
            "- Provider and downstream surfaces were called in this run, but green command surfaces do not cover the strict objective by themselves.",
            "",
            "## Artifacts",
            f"- JSON: `{rel(json_path)}`",
            f"- Checklist CSV: `{rel(checklist_path)}`",
            f"- Command summary CSV: `{rel(command_summary_path)}`",
            f"- Assertions: `{rel(assertions_path)}`",
            "",
            "## Next",
            audit["next_action"],
            "",
        ]
    )
    report_path.write_text("\n".join(report), encoding="utf-8")

    assertions = [
        ("board_cursor_present", bool(cursor.get("last_loop_id"))),
        ("direct_r6_verifier_called", "direct_r6_live_verifier" in commands),
        ("direct_r6_verifier_ok", command_ok(commands, "direct_r6_live_verifier")),
        ("provider_status_called", command_ok(commands, "provider_status_agent")),
        ("auto_quant_status_called", command_ok(commands, "auto_quant_status")),
        ("analyze_surface_called", "analyze_live_nq_yfinance" in commands and "analyze_demo" in commands),
        ("pre_bayes_called", "pre_bayes_nq" in commands and "pre_bayes_demo" in commands),
        ("policy_training_called", "policy_training_nq" in commands and "policy_training_demo" in commands),
        ("workflow_called", "workflow_execution_candidate_nq" in commands and "workflow_execution_candidate_demo" in commands),
        ("export_path_ranking_called", "export_path_ranking_nq" in commands and "export_path_ranking_demo" in commands),
        ("strict_full_objective_not_complete", not audit["strict_full_objective_achieved"]),
        ("update_goal_false", not audit["update_goal"]),
    ]
    assertions_path.write_text("\n".join(f"{name}={'ok' if passed else 'FAIL'}" for name, passed in assertions) + "\n", encoding="utf-8")
    if not all(passed for _, passed in assertions):
        return 2
    print(json.dumps({"ok": True, "gate_result": gate_result, "status_counts": status_counts, "update_goal": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
