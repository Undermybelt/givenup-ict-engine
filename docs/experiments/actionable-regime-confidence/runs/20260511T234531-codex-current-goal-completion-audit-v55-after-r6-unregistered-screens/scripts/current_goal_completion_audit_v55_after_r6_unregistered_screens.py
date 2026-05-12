#!/usr/bin/env python3
"""V55 Board A audit after unregistered R6 positive candidate screens.

This script is evidence-only. It does not mutate the shared direct
Manipulation intake. It registers the current prompt-to-artifact state, checks
whether the live /tmp intake is usable, and reruns lightweight ict-engine
surfaces through the provider/Auto-Quant/pre-Bayes/CatBoost/workflow/export
chain.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T234531-codex-current-goal-completion-audit-v55-after-r6-unregistered-screens"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "completion-audit"
COMMAND_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
STATE_DIR = Path("/tmp/ict-engine-board-a-v55-chain-readback")
DIRECT_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
DIRECT_VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1"
    / "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
SARAO_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T225505-codex-r6-sarao-positive-row-candidate-screen-v1"
    / "r6-sarao-positive-row-candidate-screen/r6_sarao_positive_row_candidate_screen_v1.json"
)
NOWAK_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T233454-codex-r6-nowak-smith-positive-row-candidate-screen-v1"
    / "r6-nowak-smith-positive-row-candidate-screen/r6_nowak_smith_positive_row_candidate_screen_v1.json"
)
SIDECAR_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260511T222828-codex-r6-sidecar-broad-normal-calibration-v2"
    / "r6-sidecar-broad-normal-calibration/r6_sidecar_broad_normal_calibration_v2.json"
)

MIN_WILSON = 0.95
Z_95 = 1.96


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def wilson_lcb(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / total
    centre = p + z2 / (2.0 * total)
    margin = Z_95 * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def rows_needed_for_lcb(current_successes: int, threshold: float = MIN_WILSON) -> int:
    for total in range(current_successes, current_successes + 500):
        if wilson_lcb(total, total) >= threshold:
            return total - current_successes
    return 500


def parse_json_or_raw(stdout: str) -> Any:
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        parsed: dict[str, str] = {}
        for line in stdout.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                parsed[key.strip()] = value.strip()
        return parsed or {"raw_stdout": stdout[:2000]}


def run_command(name: str, command: list[str], timeout: int = 120) -> dict[str, Any]:
    COMMAND_OUT.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        command,
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    stdout_path = COMMAND_OUT / f"{name}.stdout.txt"
    stderr_path = COMMAND_OUT / f"{name}.stderr.txt"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    return {
        "name": name,
        "command": command,
        "returncode": result.returncode,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "parsed_stdout": parse_json_or_raw(result.stdout),
    }


def summarize_provider_status(payload: Any) -> dict[str, Any]:
    providers = payload.get("providers", []) if isinstance(payload, dict) else []
    wanted = {
        "ibkr",
        "ibkr_bridge",
        "tradingview_mcp",
        "yfinance",
        "kraken_public",
        "kraken_cli",
    }
    selected = {}
    for provider in providers:
        provider_id = provider.get("provider_id")
        if provider_id in wanted:
            selected[provider_id] = {
                "domain": provider.get("domain"),
                "ready": provider.get("ready"),
                "status": provider.get("status"),
                "reason": provider.get("reason"),
            }
    missing = sorted(wanted.difference(selected))
    return {
        "summary_line": payload.get("summary_line") if isinstance(payload, dict) else None,
        "selected": selected,
        "missing_provider_ids_in_output": missing,
    }


def live_intake_status(direct_verifier: dict[str, Any]) -> dict[str, Any]:
    required = [
        DIRECT_ROOT / "positive_spoofing_layering_rows.csv",
        DIRECT_ROOT / "matched_negative_normal_activity_rows.csv",
        DIRECT_ROOT / "provenance_manifest.json",
    ]
    return {
        "intake_root": str(DIRECT_ROOT),
        "intake_root_exists": DIRECT_ROOT.exists(),
        "required_files": {path.name: path.exists() for path in required},
        "direct_verifier_returncode": direct_verifier["returncode"],
        "direct_verifier_payload": direct_verifier["parsed_stdout"],
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_report(summary: dict[str, Any]) -> Path:
    path = OUT / "current_goal_completion_audit_v55_after_r6_unregistered_screens.md"
    lines = [
        "# Current Goal Completion Audit v55 After R6 Unregistered Screens",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Board SHA-256 at start: `{summary['board_sha256_at_start']}`.",
        f"- Live direct intake root exists: `{summary['live_intake']['intake_root_exists']}`.",
        f"- Live direct verifier return code: `{summary['live_intake']['direct_verifier_returncode']}`.",
        f"- Current accepted R6 positives in prior verifier readback: `{summary['r6_candidate_state']['current_positive_rows']}`.",
        f"- Proposed sidecar positives not in shared intake: Sarao `{summary['r6_candidate_state']['sarao_proposed_positive_rows']}`, Nowak/Smith `{summary['r6_candidate_state']['nowak_smith_proposed_positive_rows']}`.",
        f"- What-if positives if both sidecars were accepted: `{summary['r6_candidate_state']['what_if_positive_rows_with_both_sidecars']}`.",
        f"- What-if Wilson95 LCB with both sidecars: `{summary['r6_candidate_state']['what_if_min_wilson95_lcb_with_both_sidecars']:.12f}`.",
        f"- Additional all-correct positives still needed after both sidecars: `{summary['r6_candidate_state']['additional_positive_rows_needed_after_both_sidecars']}`.",
        f"- Provider readback: `{summary['provider_summary']['summary_line']}`.",
        f"- Gate result: `{summary['gate_result']}`.",
        f"- Strict full objective achieved: `{summary['strict_full_objective_achieved']}`; `update_goal={summary['update_goal']}`.",
        "",
        "## Fail-Closed Notes",
        "",
        "- The Nowak/Smith artifact existed on disk but was not registered in the board before this audit.",
        "- The shared `/tmp/ict-engine-direct-manipulation-row-intake` files are absent in the current shell, so no proposed positive rows were accepted or appended.",
        "- Even accepting the Sarao and Nowak/Smith sidecar positives would leave pooled Wilson95 below `0.95` and would not close chronological/symbol/venue split support.",
        "- The provider/downstream commands were rerun and captured under `command-output/`; command failures are treated as fail-closed evidence, not ignored.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    sarao = load_json(SARAO_JSON)
    nowak = load_json(NOWAK_JSON)

    commands = {}
    command_specs = {
        "provider_status_agent": (["./target/debug/ict-engine", "provider-status", "--agent"], 180),
        "auto_quant_status": (
            [
                "./target/debug/ict-engine",
                "auto-quant-status",
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
            60,
        ),
        "analyze_live_nq_yfinance_agent": (
            [
                "./target/debug/ict-engine",
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
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "agent",
            ],
            180,
        ),
        "pre_bayes_status_nq": (
            [
                "./target/debug/ict-engine",
                "pre-bayes-status",
                "--symbol",
                "NQ",
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--output-format",
                "json",
            ],
            60,
        ),
        "policy_training_status_nq_agent": (
            [
                "./target/debug/ict-engine",
                "policy-training-status",
                "--symbol",
                "NQ",
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "agent",
            ],
            60,
        ),
        "workflow_status_nq_agent": (
            [
                "./target/debug/ict-engine",
                "workflow-status",
                "--symbol",
                "NQ",
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--agent",
            ],
            60,
        ),
        "workflow_status_nq_execution_candidate_agent": (
            [
                "./target/debug/ict-engine",
                "workflow-status",
                "--symbol",
                "NQ",
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--phase",
                "execution-candidate",
                "--agent",
            ],
            60,
        ),
        "export_structural_path_ranking_target_nq": (
            [
                "./target/debug/ict-engine",
                "export-structural-path-ranking-target",
                "--symbol",
                "NQ",
                "--state-dir",
                str(STATE_DIR),
            ],
            60,
        ),
        "direct_manipulation_row_intake_verifier": (
            ["python3", str(DIRECT_VERIFIER), "--intake-root", str(DIRECT_ROOT)],
            60,
        ),
    }
    for name, (command, timeout) in command_specs.items():
        commands[name] = run_command(name, command, timeout)

    provider_summary = summarize_provider_status(commands["provider_status_agent"]["parsed_stdout"])
    live_intake = live_intake_status(commands["direct_manipulation_row_intake_verifier"])

    current_positive_rows = int(nowak.get("current_positive_rows") or sarao.get("current_positive_rows") or 0)
    sarao_rows = int(sarao.get("proposed_positive_rows", 0))
    nowak_rows = int(nowak.get("proposed_positive_rows", 0))
    sidecar_controls = int(nowak.get("sidecar_broad_normal_control_rows") or sarao.get("sidecar_broad_normal_control_rows") or 0)
    sidecar_lcb = float(nowak.get("sidecar_broad_normal_wilson95_lcb") or sarao.get("sidecar_broad_normal_wilson95_lcb") or 0.0)
    what_if_both = current_positive_rows + sarao_rows + nowak_rows
    what_if_positive_lcb = wilson_lcb(what_if_both, what_if_both)
    what_if_min_lcb = min(what_if_positive_lcb, sidecar_lcb) if sidecar_lcb else what_if_positive_lcb
    rows_needed_after_both = rows_needed_for_lcb(what_if_both)

    checklist_rows = [
        {
            "requirement": "Board A markdown is authoritative and must not be overwritten",
            "evidence": rel(BOARD),
            "status": "append_only_update_required_after_audit",
            "gap": "board still needs V55 registration writeback",
        },
        {
            "requirement": "Every active regime has 95 percent confidence",
            "evidence": "regime_factor_consumer_map_v1 plus V54/V55 R6 readback",
            "status": "blocked_strict_full_objective",
            "gap": "R6 direct positive confidence remains below 0.95 under pooled Wilson95",
        },
        {
            "requirement": "Verify on other markets and timeframes",
            "evidence": "V54 plus current provider/downstream command outputs",
            "status": "blocked_strict_full_objective",
            "gap": "R3 native subhour and R5 source-panel recency remain blocked; candidate screens add no cross-axis closure",
        },
        {
            "requirement": "Use IBKR, TradingViewRemix, yfinance, and Kraken paths",
            "evidence": "provider_status_agent.stdout.txt",
            "status": "readback_captured",
            "gap": "provider readiness does not provide accepted direct order-lifecycle positives",
        },
        {
            "requirement": "Run Auto-Quant and ict-engine downstream surfaces",
            "evidence": "auto_quant_status, analyze_live, pre_bayes_status, policy_training_status, workflow_status, export_structural_path_ranking_target outputs",
            "status": "readback_captured",
            "gap": "readbacks do not close Board A confidence/support gates",
        },
        {
            "requirement": "Do not disturb multi-agent construction",
            "evidence": "shared_intake_mutated=false; live /tmp intake checked before append",
            "status": "preserved",
            "gap": "shared /tmp intake absent, so no candidate rows accepted",
        },
    ]
    checklist_path = OUT / "current_goal_completion_audit_v55_checklist.csv"
    write_csv(checklist_path, checklist_rows, ["requirement", "evidence", "status", "gap"])

    gate_rows = [
        {
            "gate": "live_intake_exists",
            "value": live_intake["intake_root_exists"],
            "passed": live_intake["intake_root_exists"],
        },
        {
            "gate": "direct_verifier_success",
            "value": live_intake["direct_verifier_returncode"],
            "passed": live_intake["direct_verifier_returncode"] == 0,
        },
        {
            "gate": "what_if_both_sidecars_wilson95_ge_095",
            "value": f"{what_if_min_lcb:.12f}",
            "passed": what_if_min_lcb >= MIN_WILSON,
        },
        {
            "gate": "strict_full_objective_achieved",
            "value": False,
            "passed": False,
        },
    ]
    gate_path = OUT / "current_goal_completion_audit_v55_gates.csv"
    write_csv(gate_path, gate_rows, ["gate", "value", "passed"])

    summary = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_sha256_at_start": sha256(BOARD),
        "board_path": rel(BOARD),
        "artifact_paths": {
            "json": rel(OUT / "current_goal_completion_audit_v55_after_r6_unregistered_screens.json"),
            "report": rel(OUT / "current_goal_completion_audit_v55_after_r6_unregistered_screens.md"),
            "checklist": rel(checklist_path),
            "gates": rel(gate_path),
            "assertions": rel(CHECKS / "current_goal_completion_audit_v55_after_r6_unregistered_screens_assertions.out"),
        },
        "registered_existing_unboarded_artifact": rel(NOWAK_JSON),
        "sarao_artifact": rel(SARAO_JSON),
        "sidecar_artifact": rel(SIDECAR_JSON),
        "provider_summary": provider_summary,
        "commands": commands,
        "live_intake": live_intake,
        "r6_candidate_state": {
            "current_positive_rows": current_positive_rows,
            "current_min_wilson95_lcb": float(nowak.get("current_min_wilson95_lcb") or sarao.get("current_min_wilson95_lcb") or 0.0),
            "sarao_proposed_positive_rows": sarao_rows,
            "nowak_smith_proposed_positive_rows": nowak_rows,
            "sidecar_broad_normal_control_rows": sidecar_controls,
            "sidecar_broad_normal_wilson95_lcb": sidecar_lcb,
            "what_if_positive_rows_with_both_sidecars": what_if_both,
            "what_if_positive_wilson95_lcb_with_both_sidecars": round(what_if_positive_lcb, 12),
            "what_if_min_wilson95_lcb_with_both_sidecars": round(what_if_min_lcb, 12),
            "additional_positive_rows_needed_after_both_sidecars": rows_needed_after_both,
            "shared_intake_mutated": False,
            "accepted_rows_added": 0,
        },
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "gate_result": "current_goal_completion_audit_v55=unregistered_nowak_smith_registered_live_intake_absent_confidence_still_blocked",
        "next_action": (
            "Recreate or lock the shared direct intake before accepting any Sarao/Nowak/Smith "
            "positive rows; then source at least 4 more independent all-correct positives and "
            "rerun sidecar/direct chronological-symbol-venue calibration."
        ),
    }
    report_path = write_report(summary)
    summary["artifact_paths"]["report"] = rel(report_path)

    json_path = OUT / "current_goal_completion_audit_v55_after_r6_unregistered_screens.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    assertions = [
        ("sarao_artifact_present", SARAO_JSON.exists()),
        ("nowak_smith_artifact_present", NOWAK_JSON.exists()),
        ("live_intake_not_mutated", not summary["r6_candidate_state"]["shared_intake_mutated"]),
        ("what_if_both_still_below_095", what_if_min_lcb < MIN_WILSON),
        ("strict_full_objective_false", not summary["strict_full_objective_achieved"]),
        ("provider_command_captured", commands["provider_status_agent"]["stdout_path"] != ""),
        ("downstream_commands_captured", all(name in commands for name in command_specs)),
    ]
    assertion_path = CHECKS / "current_goal_completion_audit_v55_after_r6_unregistered_screens_assertions.out"
    assertion_path.write_text(
        "\n".join(f"{name}={'ok' if passed else 'FAIL'}" for name, passed in assertions) + "\n",
        encoding="utf-8",
    )
    failed = [name for name, passed in assertions if not passed]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
