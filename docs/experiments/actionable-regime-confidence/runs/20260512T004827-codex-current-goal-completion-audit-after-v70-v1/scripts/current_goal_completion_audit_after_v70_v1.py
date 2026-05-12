#!/usr/bin/env python3
"""Post-V70 Board A completion audit.

Read-only evidence packet. It reruns fail-closed local verifiers plus
lightweight provider/Auto-Quant/ict-engine status surfaces, then maps the
user objective to concrete artifacts. It does not mutate shared intakes,
canonical roots, thresholds, runtime code, or provider caches.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T004827-codex-current-goal-completion-audit-after-v70-v1"
AUDIT_ID = "current_goal_completion_audit_after_v70_v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "current-goal-completion-audit-after-v70"
CMD_OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BIN = REPO / "target/debug/ict-engine"
LOCAL_AUTO_QUANT = Path("/Users/thrill3r/Auto-Quant")

STATE = Path("/tmp/ict-engine-board-a-v70-chain")
AQ_STATE = Path("/tmp/ict-engine-board-a-v70-autoquant")

SOURCE_LABEL_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
R3_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
R6_LIVE_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
R6_OWNER_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")

SOURCE_LABEL_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)
R5_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
R6_VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/"
    "direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py"
)
SOURCE_CONFIDENCE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T214328-codex-source-label-equivalence-confidence-calibration-v1/"
    "source-label-equivalence-confidence-calibration/source_label_equivalence_confidence_calibration_v1.json"
)
R6_EXTERNAL_SCAN = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T004322-codex-r6-oystacher-external-control-source-scan-v1/"
    "r6-oystacher-external-control-source-scan/r6_oystacher_external_control_source_scan_v1.json"
)
R6_PUBLIC_PROBE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1/"
    "r6-oystacher-public-normal-control-source-probe/r6_oystacher_public_normal_control_source_probe_v1.json"
)
R6_SOURCE_OWNER_ROUTE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T004022-codex-r6-oystacher-source-owner-control-route-v1/"
    "r6-oystacher-source-owner-control-route/r6_oystacher_source_owner_control_route_v1.json"
)

R3_REQUIRED = [
    "native_subhour_source_label_rows.csv",
    "native_subhour_source_label_provenance.json",
]
R5_REQUIRED = [
    "stock_market_regimes_2026_extension.csv",
    "source_panel_recency_provenance.json",
]
R6_OWNER_REQUIRED = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]


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


def parse_json(text: str) -> Any | None:
    try:
        return json.loads(text) if text.strip() else None
    except json.JSONDecodeError:
        return None


def run_cmd(name: str, args: list[str], timeout: int = 180, env_extra: dict[str, str] | None = None) -> dict[str, Any]:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        code = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"
        code = 124
        timed_out = True

    stdout_path = CMD_OUT / f"{name}.stdout.txt"
    stderr_path = CMD_OUT / f"{name}.stderr.txt"
    exit_path = CMD_OUT / f"{name}.exit"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{code}\n", encoding="utf-8")
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": code,
        "timed_out": timed_out,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "exit_path": rel(exit_path),
        "parsed": parse_json(stdout),
    }


def current_cursor(board_text: str) -> str:
    match = re.search(r"\| last_loop_id \| ([^|]+) \|", board_text)
    return match.group(1).strip() if match else "unknown"


def required_file_status(root: Path, names: list[str]) -> dict[str, Any]:
    present = {name: (root / name).exists() for name in names}
    return {
        "root": str(root),
        "root_exists": root.exists(),
        "present_count": sum(1 for value in present.values() if value),
        "required": present,
        "missing": [name for name, value in present.items() if not value],
    }


def provider_row(payload: Any, provider_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"provider_id": provider_id, "ready": False, "status": "unparsed", "reason": ""}
    rows = [row for row in payload.get("providers", []) if row.get("provider_id") == provider_id]
    if not rows:
        return {"provider_id": provider_id, "ready": False, "status": "not_listed", "reason": ""}
    return {
        "provider_id": provider_id,
        "ready": any(bool(row.get("ready")) for row in rows),
        "status": ";".join(sorted({str(row.get("status", "")) for row in rows})),
        "reason": ";".join(sorted({str(row.get("reason", "")) for row in rows})),
    }


def active_strategy_count() -> int:
    strategies = LOCAL_AUTO_QUANT / "user_data/strategies"
    if not strategies.exists():
        return 0
    return len([path for path in strategies.glob("*.py") if path.is_file() and not path.name.startswith("_")])


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def compact_commands(commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "name": row["name"],
            "returncode": row["returncode"],
            "timed_out": row["timed_out"],
            "stdout_path": row["stdout_path"],
            "stderr_path": row["stderr_path"],
            "exit_path": row["exit_path"],
        }
        for row in commands
    ]


def command_seen(commands: list[dict[str, Any]], name: str) -> bool:
    return any(row["name"] == name and row["returncode"] != 124 for row in commands)


def main() -> int:
    for path in (OUT, CMD_OUT, CHECKS, STATE, AQ_STATE):
        path.mkdir(parents=True, exist_ok=True)
    for required in (
        BOARD,
        BIN,
        SOURCE_LABEL_VERIFIER,
        R5_VERIFIER,
        R6_VERIFIER,
        SOURCE_CONFIDENCE,
        R6_EXTERNAL_SCAN,
        R6_PUBLIC_PROBE,
        R6_SOURCE_OWNER_ROUTE,
    ):
        if not required.exists():
            raise FileNotFoundError(required)

    board_text = BOARD.read_text(encoding="utf-8")
    source_confidence = load_json(SOURCE_CONFIDENCE)
    r6_external = load_json(R6_EXTERNAL_SCAN)
    r6_public = load_json(R6_PUBLIC_PROBE)
    r6_route = load_json(R6_SOURCE_OWNER_ROUTE)

    commands = [
        run_cmd("source_label_equivalence_verifier", [sys.executable, str(SOURCE_LABEL_VERIFIER), "--intake-root", str(SOURCE_LABEL_ROOT)]),
        run_cmd("source_panel_recency_verifier", [sys.executable, str(R5_VERIFIER), "--intake-root", str(R5_ROOT)]),
        run_cmd("direct_manipulation_verifier_live", [sys.executable, str(R6_VERIFIER), "--intake-root", str(R6_LIVE_ROOT)]),
        run_cmd("direct_manipulation_verifier_owner_export", [sys.executable, str(R6_VERIFIER), "--intake-root", str(R6_OWNER_ROOT)]),
        run_cmd("provider_status_agent", [str(BIN), "provider-status", "--agent"]),
    ]
    for provider in ("ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"):
        commands.append(run_cmd(f"provider_status_{provider}", [str(BIN), "provider-status", "--provider", provider, "--agent"]))
    commands.extend(
        [
            run_cmd(
                "auto_quant_status_local",
                [str(BIN), "auto-quant-status", "--state-dir", str(AQ_STATE), "--output-format", "json"],
                env_extra={"ICT_ENGINE_AUTO_QUANT_DIR": str(LOCAL_AUTO_QUANT)},
            ),
            run_cmd("analyze_nq_demo_agent", [str(BIN), "analyze", "--symbol", "NQ", "--demo", "--state-dir", str(STATE), "--agent"]),
            run_cmd("pre_bayes_status_nq", [str(BIN), "pre-bayes-status", "--symbol", "NQ", "--state-dir", str(STATE), "--refresh", "--output-format", "json"]),
            run_cmd("policy_training_status_nq", [str(BIN), "policy-training-status", "--symbol", "NQ", "--state-dir", str(STATE), "--output-format", "json"]),
            run_cmd("workflow_status_nq", [str(BIN), "workflow-status", "--symbol", "NQ", "--state-dir", str(STATE), "--refresh", "--agent"]),
            run_cmd("workflow_status_nq_execution_candidate", [str(BIN), "workflow-status", "--symbol", "NQ", "--state-dir", str(STATE), "--phase", "execution-candidate", "--agent"]),
            run_cmd("export_structural_path_ranking_target_nq", [str(BIN), "export-structural-path-ranking-target", "--symbol", "NQ", "--state-dir", str(STATE)]),
        ]
    )
    by_name = {row["name"]: row for row in commands}

    source_label = by_name["source_label_equivalence_verifier"]["parsed"] or {}
    source_panel = by_name["source_panel_recency_verifier"]["parsed"] or {}
    r6_live = by_name["direct_manipulation_verifier_live"]["parsed"] or {}
    r6_owner = by_name["direct_manipulation_verifier_owner_export"]["parsed"] or {}
    providers = [
        provider_row(by_name["provider_status_agent"]["parsed"], provider)
        for provider in ("ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli")
    ]
    auto_quant = by_name["auto_quant_status_local"]["parsed"] or {}

    r3_files = required_file_status(R3_ROOT, R3_REQUIRED)
    r5_files = required_file_status(R5_ROOT, R5_REQUIRED)
    r6_owner_files = required_file_status(R6_OWNER_ROOT, R6_OWNER_REQUIRED)
    accepted_source_labels = source_confidence.get("accepted_source_confidence_95_labels") or []

    checklist = [
        {
            "requirement": "Use the named Board A markdown and preserve concurrent work.",
            "status": "pass",
            "evidence": rel(BOARD),
            "gap": "",
        },
        {
            "requirement": "Every active regime/root reaches >=95% calibrated confidence.",
            "status": "fail",
            "evidence": f"source_confidence_labels={len(accepted_source_labels)}/4; direct_r6={r6_live.get('status')}",
            "gap": "Source-confidence labels remain 0/4 and direct R6 is schema-ready/unscored, not promoted.",
        },
        {
            "requirement": "Validate across other markets, timeframes, and periods.",
            "status": "fail",
            "evidence": f"R3_files={r3_files['present_count']}/{len(R3_REQUIRED)}; R5_files={r5_files['present_count']}/{len(R5_REQUIRED)}",
            "gap": "Native sub-hour source labels and post-2026-01-30 source-panel rows are absent.",
        },
        {
            "requirement": "Direct Manipulation/R6 has source-owned positives plus normal controls.",
            "status": "fail",
            "evidence": f"external_controls={r6_external.get('verifier_ready_source_owned_normal_controls_found')}; public_controls={r6_public.get('valid_public_source_owned_normal_controls')}; owner_files={r6_owner_files['present_count']}/{len(R6_OWNER_REQUIRED)}",
            "gap": "No verifier-ready source-owned normal controls or FLIP-control approval exists.",
        },
        {
            "requirement": "Operate provider, Auto-Quant, Pre-Bayes/BBN, CatBoost/policy, and execution-tree surfaces.",
            "status": "partial",
            "evidence": rel(CMD_OUT),
            "gap": "Read-only surfaces ran; promotion chain is deferred because canonical R6/source-label inputs are missing.",
        },
        {
            "requirement": "Check IBKR, TradingViewRemix/MCP, yfinance, Kraken, and local Auto-Quant.",
            "status": "partial",
            "evidence": f"providers={[(row['provider_id'], row['ready']) for row in providers]}; auto_quant={auto_quant.get('status')}",
            "gap": "Provider readiness is not acceptance evidence; missing source/control inputs still block.",
        },
        {
            "requirement": "Avoid proxy acceptance and shared-intake pollution.",
            "status": "pass",
            "evidence": "No intake files created; no canonical merge; raw data not committed.",
            "gap": "",
        },
    ]

    gate_result = "current_goal_completion_audit_after_v70_v1=not_complete_r6_controls_r3_r5_source_labels_downstream_blocked"
    result = {
        "run_id": RUN_ID,
        "audit_id": AUDIT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_cursor_observed": current_cursor(board_text),
        "board_sha256_at_start": sha256(BOARD),
        "objective_restatement": [
            "Every active Board A regime/root must have at least 95% calibrated confidence.",
            "Evidence must validate across other markets and other cycles/timeframes.",
            "Provider, Auto-Quant, Pre-Bayes/BBN, CatBoost/policy, and execution-tree surfaces must be operated with concrete artifacts.",
            "No concurrent board work may be overwritten and no proxy/OHLCV evidence may be promoted as source labels or direct normal controls.",
        ],
        "checklist": checklist,
        "source_label_equivalence": {
            "verifier_status": source_label.get("status"),
            "accepted_source_confidence_95_labels": accepted_source_labels,
        },
        "r3_native_subhour": r3_files,
        "r5_source_panel_recency": {
            **r5_files,
            "verifier_status": source_panel.get("status"),
            "verifier_reason": source_panel.get("reason"),
        },
        "r6_direct": {
            "live_status": r6_live.get("status"),
            "live_positive_rows": r6_live.get("positive_rows"),
            "live_matched_negative_rows": r6_live.get("matched_negative_rows"),
            "owner_export_required": r6_owner_files,
            "owner_export_status": r6_owner.get("status"),
            "external_control_scan": r6_external,
            "public_normal_control_probe": r6_public,
            "source_owner_route": r6_route,
        },
        "providers": providers,
        "auto_quant": {
            "status": auto_quant.get("status"),
            "healthy": auto_quant.get("healthy"),
            "data_ready": auto_quant.get("data_ready"),
            "managed_dir": auto_quant.get("managed_dir"),
            "active_strategy_count": active_strategy_count(),
        },
        "commands": compact_commands(commands),
        "gate_result": gate_result,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": (
            "Supply source-owned normal controls for the 17 Oystacher cells through mapped CME/Cboe routes, "
            "or explicitly approve the same-exhibit FLIP-as-control exception; then copy verifier-native files "
            "under a shared lock and rerun direct verifier, split calibration, provider, Auto-Quant, "
            "Pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback while keeping R3/R5 blocked "
            "until their source-label intakes are present."
        ),
    }

    json_path = OUT / f"{AUDIT_ID}.json"
    report_path = OUT / f"{AUDIT_ID}.md"
    checklist_path = OUT / f"{AUDIT_ID}_checklist.csv"
    commands_path = OUT / f"{AUDIT_ID}_commands.csv"
    assertions_path = CHECKS / f"{AUDIT_ID}_assertions.out"

    write_csv(checklist_path, checklist, ["requirement", "status", "evidence", "gap"])
    write_csv(commands_path, compact_commands(commands), ["name", "returncode", "timed_out", "stdout_path", "stderr_path", "exit_path"])
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Current Goal Completion Audit After V70 v1",
        "",
        f"- Gate result: `{gate_result}`.",
        f"- Board cursor observed: `{result['board_cursor_observed']}`.",
        f"- Source-confidence accepted labels: `{len(accepted_source_labels)}/4`.",
        f"- R3 native-subhour files: `{r3_files['present_count']}/{len(R3_REQUIRED)}`.",
        f"- R5 source-panel-recency files: `{r5_files['present_count']}/{len(R5_REQUIRED)}`; verifier `{source_panel.get('status')}` / `{source_panel.get('reason')}`.",
        f"- R6 live verifier: `{r6_live.get('status')}` with positives `{r6_live.get('positive_rows')}` and controls `{r6_live.get('matched_negative_rows')}`.",
        f"- R6 owner-export files: `{r6_owner_files['present_count']}/{len(R6_OWNER_REQUIRED)}`; verifier `{r6_owner.get('status')}` / `{r6_owner.get('reason')}`.",
        f"- R6 external verifier-ready controls: `{r6_external.get('verifier_ready_source_owned_normal_controls_found')}`.",
        f"- Auto-Quant: `{auto_quant.get('status')}`, healthy `{auto_quant.get('healthy')}`, data_ready `{auto_quant.get('data_ready')}`, active strategies `{active_strategy_count()}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Prompt To Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Gap |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        lines.append(f"| {row['requirement']} | `{row['status']}` | `{row['evidence']}` | {row['gap']} |")
    lines.extend(["", "## Providers", "", "| Provider | Ready | Status | Reason |", "|---|---:|---|---|"])
    for row in providers:
        lines.append(f"| `{row['provider_id']}` | `{str(row['ready']).lower()}` | `{row['status']}` | `{row['reason']}` |")
    lines.extend(["", "## Commands", "", "| Command | Exit | Output | Error |", "|---|---:|---|---|"])
    for row in compact_commands(commands):
        lines.append(f"| `{row['name']}` | `{row['returncode']}` | `{row['stdout_path']}` | `{row['stderr_path']}` |")
    lines.extend(
        [
            "",
            "## Next",
            "",
            result["next_action"],
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(json_path)}`",
            f"- Report: `{rel(report_path)}`",
            f"- Checklist CSV: `{rel(checklist_path)}`",
            f"- Command CSV: `{rel(commands_path)}`",
            f"- Assertions: `{rel(assertions_path)}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = {
        "board_cursor_observed": result["board_cursor_observed"] != "unknown",
        "source_label_verifier_ran": command_seen(commands, "source_label_equivalence_verifier"),
        "r3_required_files_missing": r3_files["present_count"] == 0,
        "r5_required_files_missing": r5_files["present_count"] == 0,
        "r6_owner_required_files_missing": r6_owner_files["present_count"] == 0,
        "r6_external_controls_zero": r6_external.get("verifier_ready_source_owned_normal_controls_found") == 0,
        "provider_status_ran": command_seen(commands, "provider_status_agent"),
        "auto_quant_checked": command_seen(commands, "auto_quant_status_local"),
        "downstream_status_surfaces_ran": all(
            command_seen(commands, name)
            for name in (
                "pre_bayes_status_nq",
                "policy_training_status_nq",
                "workflow_status_nq_execution_candidate",
                "export_structural_path_ranking_target_nq",
            )
        ),
        "strict_objective_false": result["strict_full_objective_achieved"] is False,
        "update_goal_false": result["update_goal"] is False,
    }
    assertions_path.write_text(
        "\n".join(f"{name}={'PASS' if passed else 'FAIL'}" for name, passed in assertions.items()) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"gate_result": gate_result, "assertions_passed": all(assertions.values())}, sort_keys=True))
    return 0 if all(assertions.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
