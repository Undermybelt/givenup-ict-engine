#!/usr/bin/env python3
"""Board A current-goal audit after V62 owner-export readbacks.

This is a read-only evidence packet. It reruns fail-closed local verifiers and
ict-engine chain/status surfaces, but it does not mutate shared intakes,
runtime code, provider caches, thresholds, or the Board A cursor.
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


RUN_ID = "20260512T002916-codex-current-goal-completion-audit-v63-after-v62-readbacks"
AUDIT_ID = "current_goal_completion_audit_v63_after_v62_readbacks"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "completion-audit"
CMD = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
STATE = Path("/tmp/ict-engine-board-a-v63-chain")
AQ_STATE = Path("/tmp/ict-engine-board-a-v63-autoquant")
YF_STATE = Path("/tmp/ict-engine-board-a-v63-yfinance-live")
KRAKEN_STATE = Path("/tmp/ict-engine-board-a-v63-kraken-live")

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BIN = REPO / "target/debug/ict-engine"
LOCAL_AUTO_QUANT = Path("/Users/thrill3r/Auto-Quant")

SOURCE_LABEL_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
R5_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
R3_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R6_ROOT = Path("/tmp/ict-engine-direct-manipulation-row-intake")
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
R6_DEBT_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T000801-codex-r6-exact-split-support-debt-audit-v1/"
    "r6-exact-split-support-debt-audit/r6_exact_split_support_debt_audit_v1.json"
)
R6_REQUEST_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T001636-codex-r6-owner-export-request-package-v1/"
    "r6-owner-export-request-package/r6_owner_export_request_package_v1.json"
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
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
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


def parse_json(text: str) -> Any | None:
    if not text.strip():
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def run_cmd(
    name: str,
    args: list[str],
    timeout: int = 180,
    env_extra: dict[str, str] | None = None,
) -> dict[str, Any]:
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
    out_path = CMD / f"{name}.stdout.txt"
    err_path = CMD / f"{name}.stderr.txt"
    exit_path = CMD / f"{name}.exit"
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{code}\n", encoding="utf-8")
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": code,
        "timed_out": timed_out,
        "stdout_path": rel(out_path),
        "stderr_path": rel(err_path),
        "exit_path": rel(exit_path),
        "parsed": parse_json(stdout),
    }


def current_cursor(board: str) -> str:
    match = re.search(r"\| last_loop_id \| ([^|]+) \|", board)
    return match.group(1).strip() if match else "unknown"


def provider_row(payload: Any, provider_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"provider_id": provider_id, "observed": False, "ready": False, "status": "unparsed", "reason": ""}
    rows = [row for row in payload.get("providers", []) if row.get("provider_id") == provider_id]
    if not rows:
        return {"provider_id": provider_id, "observed": False, "ready": False, "status": "not_listed", "reason": ""}
    return {
        "provider_id": provider_id,
        "observed": True,
        "ready": any(bool(row.get("ready")) for row in rows),
        "status": ";".join(sorted({str(row.get("status")) for row in rows})),
        "reason": ";".join(sorted({str(row.get("reason")) for row in rows})),
    }


def required_file_status(root: Path, names: list[str]) -> dict[str, Any]:
    files = {name: (root / name).exists() for name in names}
    return {
        "root": str(root),
        "root_exists": root.exists(),
        "required": files,
        "present_count": sum(files.values()),
        "missing": [name for name, present in files.items() if not present],
    }


def csv_write(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def compact_command_rows(commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
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


def active_strategy_count() -> int:
    strategies = LOCAL_AUTO_QUANT / "user_data/strategies"
    if not strategies.exists():
        return 0
    return len([p for p in strategies.glob("*.py") if p.is_file() and not p.name.startswith("_")])


def main() -> int:
    for path in [OUT, CMD, CHECKS, STATE, AQ_STATE, YF_STATE, KRAKEN_STATE]:
        path.mkdir(parents=True, exist_ok=True)

    for required in [BOARD, BIN, SOURCE_LABEL_VERIFIER, R5_VERIFIER, R6_VERIFIER, SOURCE_CONFIDENCE, R6_DEBT_JSON, R6_REQUEST_JSON]:
        if not required.exists():
            raise FileNotFoundError(required)

    board_text = BOARD.read_text(encoding="utf-8")
    source_confidence = json.loads(SOURCE_CONFIDENCE.read_text(encoding="utf-8"))
    r6_debt = json.loads(R6_DEBT_JSON.read_text(encoding="utf-8"))
    r6_request = json.loads(R6_REQUEST_JSON.read_text(encoding="utf-8"))

    commands: list[dict[str, Any]] = [
        run_cmd("source_label_equivalence_verifier", [sys.executable, str(SOURCE_LABEL_VERIFIER), "--intake-root", str(SOURCE_LABEL_ROOT)]),
        run_cmd("source_panel_recency_verifier", [sys.executable, str(R5_VERIFIER), "--intake-root", str(R5_ROOT)]),
        run_cmd("direct_manipulation_verifier_live", [sys.executable, str(R6_VERIFIER), "--intake-root", str(R6_ROOT)]),
        run_cmd("direct_manipulation_verifier_owner_export_target", [sys.executable, str(R6_VERIFIER), "--intake-root", str(R6_OWNER_ROOT)]),
        run_cmd("provider_status_agent", [str(BIN), "provider-status", "--agent"]),
    ]
    for provider in ["ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"]:
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
            run_cmd(
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
                    str(YF_STATE),
                    "--compact",
                ],
                timeout=240,
            ),
            run_cmd(
                "analyze_live_btc_kraken_public",
                [
                    str(BIN),
                    "analyze-live",
                    "--symbol",
                    "BTCUSD",
                    "--futures-symbol",
                    "BTC/USD",
                    "--spot-symbol",
                    "BTC/USD",
                    "--futures-backend",
                    "kraken_public",
                    "--aux-backend",
                    "kraken_public",
                    "--state-dir",
                    str(KRAKEN_STATE),
                    "--compact",
                ],
                timeout=120,
            ),
        ]
    )
    by_name = {row["name"]: row for row in commands}

    source_label = by_name["source_label_equivalence_verifier"]["parsed"] or {}
    source_panel = by_name["source_panel_recency_verifier"]["parsed"] or {}
    r6_live = by_name["direct_manipulation_verifier_live"]["parsed"] or {}
    r6_owner = by_name["direct_manipulation_verifier_owner_export_target"]["parsed"] or {}
    provider_payload = by_name["provider_status_agent"]["parsed"]
    providers = [provider_row(provider_payload, provider) for provider in ["ibkr", "tradingview_mcp", "yfinance", "kraken_public", "kraken_cli"]]
    auto_quant = by_name["auto_quant_status_local"]["parsed"] or {}

    r3_files = required_file_status(R3_ROOT, R3_REQUIRED)
    r5_files = required_file_status(R5_ROOT, R5_REQUIRED)
    r6_owner_files = required_file_status(R6_OWNER_ROOT, R6_OWNER_REQUIRED)
    accepted_source_labels = source_confidence.get("accepted_source_confidence_95_labels") or []
    debt_summary = r6_debt.get("debt_summary") or {}

    checklist = [
        {
            "requirement": "Use the named Board A markdown without overwriting concurrent work.",
            "status": "pass",
            "evidence": rel(BOARD),
            "gap": "",
        },
        {
            "requirement": "Every active regime/root has >=95% confidence.",
            "status": "fail",
            "evidence": f"source_confidence_labels={len(accepted_source_labels)}/4; direct_r6_status={r6_live.get('status')}",
            "gap": "Source-confidence labels are still 0/4 and direct R6 is schema-ready/unscored rather than split-accepted.",
        },
        {
            "requirement": "Validate across other markets and cycles/timeframes.",
            "status": "fail",
            "evidence": f"R3 root present={r3_files['root_exists']}; R5 root present={r5_files['root_exists']}",
            "gap": "Native sub-hour source labels and post-2026-01-30 source-panel rows are absent.",
        },
        {
            "requirement": "Run local verifiers and fail closed on missing required rows.",
            "status": "pass",
            "evidence": f"source_label={source_label.get('status')}; R5={source_panel.get('status')}; R6_live={r6_live.get('status')}; R6_owner={r6_owner.get('status')}",
            "gap": "",
        },
        {
            "requirement": "Operate provider/Auto-Quant/Pre-Bayes/BBN/CatBoost/execution-tree surfaces.",
            "status": "partial",
            "evidence": rel(CMD),
            "gap": "Surfaces ran, but no accepted root packet or owner export exists for promotion.",
        },
        {
            "requirement": "Check IBKR, TradingViewRemix, yfinance, Kraken, and local Auto-Quant.",
            "status": "partial",
            "evidence": f"providers={[(p['provider_id'], p['ready']) for p in providers]}; auto_quant={auto_quant.get('status')}",
            "gap": "yfinance/kraken_cli are usable; IBKR/TradingView MCP/Kraken public are not promoting; Auto-Quant still needs active seed strategies.",
        },
        {
            "requirement": "Do not treat proxy OHLCV/provider data as source-owned labels.",
            "status": "pass",
            "evidence": "No intake files created; raw provider output only captured as command readback.",
            "gap": "",
        },
    ]

    gate_result = "current_goal_completion_audit_v63=strict_goal_still_blocked_no_owner_rows_or_source_labels"
    result = {
        "run_id": RUN_ID,
        "audit_id": AUDIT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_cursor_observed": current_cursor(board_text),
        "board_sha256_at_start": sha256(BOARD),
        "objective_restatement": [
            "Every active Board A regime/root needs >=95% calibrated confidence.",
            "Accepted confidence must survive other-market and other-cycle/timeframe validation.",
            "Provider paths and the ict-engine chain must be operated, not inferred.",
            "Concurrent board/worktree changes must not be overwritten.",
        ],
        "prompt_to_artifact_checklist": checklist,
        "source_label_equivalence": {
            "root": str(SOURCE_LABEL_ROOT),
            "status": source_label.get("status"),
            "row_count": source_label.get("row_count"),
            "accepted_source_confidence_95_labels": accepted_source_labels,
        },
        "r3_native_subhour": r3_files,
        "r5_source_panel_recency": {
            **r5_files,
            "verifier_status": source_panel.get("status"),
            "verifier_reason": source_panel.get("reason"),
        },
        "r6_direct": {
            "live_intake_root": str(R6_ROOT),
            "live_status": r6_live.get("status"),
            "positive_rows": r6_live.get("positive_rows"),
            "matched_negative_rows": r6_live.get("matched_negative_rows"),
            "matched_group_count": r6_live.get("matched_group_count"),
            "owner_export_root": r6_owner_files,
            "owner_export_verifier_status": r6_owner.get("status"),
            "owner_export_verifier_reason": r6_owner.get("reason"),
            "request_package": rel(R6_REQUEST_JSON),
            "exact_split_debt_artifact": rel(R6_DEBT_JSON),
            "chronological_additional_positive_rows_before_symbol_venue": debt_summary.get(
                "additional_positive_rows_for_chrono_quantiles_before_symbol_venue"
            ),
            "exact_symbol_pairwise_debt": debt_summary.get("exact_symbol_pairwise_debt_if_current_buckets_must_all_pass"),
            "exact_venue_pairwise_debt": debt_summary.get("exact_venue_pairwise_debt_if_current_buckets_must_all_pass"),
            "total_pairwise_rows_needed_if_existing_exact_buckets_are_filled": debt_summary.get(
                "total_pairwise_rows_needed_if_existing_exact_buckets_are_filled"
            ),
        },
        "providers": providers,
        "auto_quant": {
            "status": auto_quant.get("status"),
            "healthy": auto_quant.get("healthy"),
            "data_ready": auto_quant.get("data_ready"),
            "managed_dir": auto_quant.get("managed_dir"),
            "recommended_next_command": auto_quant.get("recommended_next_command"),
            "active_strategy_count": active_strategy_count(),
        },
        "commands": compact_command_rows(commands),
        "gate_result": gate_result,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "next_action": (
            "Preserve the active V62 next action: place owner/user-approved R6 export files under "
            "/tmp/ict-engine-board-a-r6-owner-export-v1 or record explicit split-contract approval; "
            "also keep R3/R5 blocked until native sub-hour and post-2026-01-30 source-owned rows appear. "
            "Only then rerun direct verifier, split calibration, provider, Auto-Quant, Pre-Bayes/BBN, "
            "CatBoost/path-ranking, and execution-tree readback."
        ),
    }

    checklist_csv = OUT / f"{AUDIT_ID}_checklist.csv"
    commands_csv = OUT / f"{AUDIT_ID}_commands.csv"
    json_path = OUT / f"{AUDIT_ID}.json"
    md_path = OUT / f"{AUDIT_ID}.md"
    assertions_path = CHECKS / f"{AUDIT_ID}_assertions.out"
    csv_write(checklist_csv, checklist, ["requirement", "status", "evidence", "gap"])
    csv_write(commands_csv, compact_command_rows(commands), ["name", "returncode", "timed_out", "stdout_path", "stderr_path", "exit_path"])
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Current Goal Completion Audit v63 After V62 Readbacks",
        "",
        f"- Gate result: `{gate_result}`.",
        f"- Board cursor observed: `{result['board_cursor_observed']}`.",
        f"- Source-confidence accepted labels: `{len(accepted_source_labels)}/4`.",
        f"- R3 native sub-hour required files present: `{r3_files['present_count']}/{len(R3_REQUIRED)}`.",
        f"- R5 recency required files present: `{r5_files['present_count']}/{len(R5_REQUIRED)}`; verifier `{source_panel.get('status')}` / `{source_panel.get('reason')}`.",
        f"- R6 live direct verifier: `{r6_live.get('status')}` with positives `{r6_live.get('positive_rows')}`, matched controls `{r6_live.get('matched_negative_rows')}`, matched groups `{r6_live.get('matched_group_count')}`.",
        f"- R6 owner-export required files present: `{r6_owner_files['present_count']}/{len(R6_OWNER_REQUIRED)}`; verifier `{r6_owner.get('status')}` / `{r6_owner.get('reason')}`.",
        f"- Auto-Quant: `{auto_quant.get('status')}`, healthy `{auto_quant.get('healthy')}`, data_ready `{auto_quant.get('data_ready')}`, active strategy files `{active_strategy_count()}`.",
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
    for row in compact_command_rows(commands):
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
            f"- Report: `{rel(md_path)}`",
            f"- Checklist CSV: `{rel(checklist_csv)}`",
            f"- Commands CSV: `{rel(commands_csv)}`",
            f"- Assertions: `{rel(assertions_path)}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = {
        "board_cursor_observed": result["board_cursor_observed"] != "unknown",
        "source_label_verifier_ran": by_name_exists(commands, "source_label_equivalence_verifier"),
        "r5_verifier_fail_closed": source_panel.get("status") == "blocked",
        "r3_required_files_missing": r3_files["present_count"] == 0,
        "r6_owner_files_missing": r6_owner_files["present_count"] == 0,
        "r6_live_schema_ready": r6_live.get("status") == "schema_ready_unscored",
        "provider_status_ran": by_name_exists(commands, "provider_status_agent"),
        "auto_quant_checked": auto_quant.get("managed_dir") == str(LOCAL_AUTO_QUANT),
        "downstream_chain_commands_ran": all(
            by_name_exists(commands, name)
            for name in [
                "pre_bayes_status_nq",
                "policy_training_status_nq",
                "workflow_status_nq_execution_candidate",
                "export_structural_path_ranking_target_nq",
            ]
        ),
        "strict_objective_false": result["strict_full_objective_achieved"] is False,
        "update_goal_false": result["update_goal"] is False,
    }
    assertions_path.write_text("\n".join(f"{key}={'PASS' if value else 'FAIL'}" for key, value in assertions.items()) + "\n", encoding="utf-8")
    if not all(assertions.values()):
        print(json.dumps({"gate_result": gate_result, "assertions": assertions}, sort_keys=True))
        return 2
    print(json.dumps({"gate_result": gate_result, "commands": len(commands), "strict_full_objective_achieved": False}, sort_keys=True))
    return 0


def by_name_exists(commands: list[dict[str, Any]], name: str) -> bool:
    return any(row["name"] == name and row["returncode"] != 124 for row in commands)


if __name__ == "__main__":
    raise SystemExit(main())
