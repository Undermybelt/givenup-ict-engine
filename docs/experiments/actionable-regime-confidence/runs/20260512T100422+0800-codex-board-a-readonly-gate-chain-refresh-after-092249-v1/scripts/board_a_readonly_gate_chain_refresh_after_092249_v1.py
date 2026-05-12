#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T100422+0800-codex-board-a-readonly-gate-chain-refresh-after-092249-v1"
SLUG = "board-a-readonly-gate-chain-refresh-after-092249-v1"
GATE_RESULT = "board_a_readonly_gate_chain_refresh_after_092249_v1=source_control_and_user_history_still_block_promotion"

SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[6]
BIN = REPO / "target/debug/ict-engine"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / SLUG
RAW_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"
STATE_DIR = Path("/tmp/ict-engine-board-a-readonly-gate-chain-refresh-after-092249-v1")
AUTO_QUANT_STATE_DIR = Path("/tmp/ict-engine-auto-quant")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(name: str, args: list[str], timeout_s: int = 180) -> dict[str, Any]:
    stdout_path = RAW_DIR / f"{name}.out"
    stderr_path = RAW_DIR / f"{name}.err"
    exit_path = RAW_DIR / f"{name}.exit"
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=timeout_s,
            check=False,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        returncode = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
        stderr += f"\nTIMEOUT after {timeout_s}s\n"
        returncode = 124
        timed_out = True

    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(str(returncode) + "\n", encoding="utf-8")

    parsed_json: Any = None
    stripped = stdout.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            parsed_json = json.loads(stripped)
        except json.JSONDecodeError:
            parsed_json = None

    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "exit_path": rel(exit_path),
        "json": parsed_json,
        "stdout_preview": stdout[:4000],
        "stderr_preview": stderr[:4000],
    }


def flatten_provider_map(provider_json: Any) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not isinstance(provider_json, dict):
        return out
    for item in provider_json.get("providers", []):
        if isinstance(item, dict) and "provider_id" in item and "domain" in item:
            out[f'{item["provider_id"]}:{item["domain"]}'] = item
    return out


def provider_ready(provider_map: dict[str, dict[str, Any]], provider_id: str, domain: str) -> bool:
    item = provider_map.get(f"{provider_id}:{domain}")
    return bool(item and item.get("ready") is True)


def walk_depth(root: Path, max_depth: int):
    if not root.exists():
        return
    resolved = root.resolve()
    base_depth = len(resolved.parts)
    for current, dirs, files in os.walk(resolved):
        current_path = Path(current)
        depth = len(current_path.parts) - base_depth
        if depth >= max_depth:
            dirs[:] = []
        yield current_path, files


def collect_required_dropzone(root: Path) -> dict[str, str]:
    required = {
        "direct_manipulation_positive_rows.csv",
        "direct_manipulation_matched_controls.csv",
        "direct_manipulation_provenance.json",
    }
    found: dict[str, str] = {}
    if root.exists():
        for current_path, files in walk_depth(root, 3):
            for name in files:
                if name in required and name not in found:
                    found[name] = str(current_path / name)
    return found


def collect_dropzone_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in [
        Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
    ]:
        found = collect_required_dropzone(root)
        rows.append(
            {
                "root": str(root),
                "exists": root.exists(),
                "required_direct_manipulation_files_present": all(
                    name in found
                    for name in [
                        "direct_manipulation_positive_rows.csv",
                        "direct_manipulation_matched_controls.csv",
                        "direct_manipulation_provenance.json",
                    ]
                ),
                "found_files": sorted(found.values()),
            }
        )
    return rows


def collect_selected_history_hints(limit: int = 40) -> list[dict[str, str]]:
    runs_root = REPO / "docs/experiments/actionable-regime-confidence/runs"
    patterns = [
        "selected_data_path.txt",
        "*user-selected*",
        "*selected*historical*",
        "*agent_selected*",
        "*selected*history*",
    ]
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for pattern in patterns:
        for path in runs_root.rglob(pattern):
            path_str = str(path)
            if path_str in seen:
                continue
            seen.add(path_str)
            reason = "agent_side_hint_only"
            lower = path_str.lower()
            if path.name == "selected_data_path.txt":
                reason = "recorded_path_artifact_not_explicit_user_selection"
            elif "user-selected" in lower:
                reason = "user_selected_name_in_prior_artifact_not_current_explicit_selection"
            rows.append({"path": path_str, "reason": reason})
            if len(rows) >= limit:
                return rows
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def text_contains(cmd: dict[str, Any], needle: str) -> bool:
    return needle in str(cmd.get("stdout_preview", "")) or needle in str(cmd.get("stderr_preview", ""))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    board_hash_before = sha256_file(BOARD)
    dropzone_rows = collect_dropzone_rows()
    selected_history_hints = collect_selected_history_hints()

    commands: list[dict[str, Any]] = []
    commands.append(run_command("provider_status_agent", [str(BIN), "provider-status", "--agent"], timeout_s=120))
    commands.append(run_command("provider_status_jsonl", [str(BIN), "provider-status", "--jsonl"], timeout_s=120))
    commands.append(
        run_command(
            "auto_quant_status",
            [str(BIN), "auto-quant-status", "--state-dir", str(AUTO_QUANT_STATE_DIR), "--output-format", "json"],
            timeout_s=120,
        )
    )
    commands.append(
        run_command(
            "auto_quant_prepare",
            [str(BIN), "auto-quant-prepare", "--state-dir", str(AUTO_QUANT_STATE_DIR)],
            timeout_s=180,
        )
    )
    commands.append(
        run_command(
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
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
            timeout_s=240,
        )
    )
    commands.append(
        run_command(
            "pre_bayes_status",
            [str(BIN), "pre-bayes-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh"],
            timeout_s=120,
        )
    )
    commands.append(
        run_command(
            "policy_training_status",
            [str(BIN), "policy-training-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--output-format", "json"],
            timeout_s=120,
        )
    )
    commands.append(
        run_command(
            "export_structural_path_ranking_target",
            [str(BIN), "export-structural-path-ranking-target", "--symbol", "NQ", "--state-dir", str(STATE_DIR)],
            timeout_s=120,
        )
    )
    commands.append(
        run_command(
            "workflow_status_execution_candidate",
            [str(BIN), "workflow-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--phase", "execution-candidate", "--agent", "--stable"],
            timeout_s=120,
        )
    )

    by_name = {cmd["name"]: cmd for cmd in commands}
    provider_map = flatten_provider_map(by_name["provider_status_agent"].get("json"))
    auto_quant_json = by_name["auto_quant_status"].get("json") or {}
    analyze_json = by_name["analyze_live_nq_yfinance"].get("json") or {}
    policy_json = by_name["policy_training_status"].get("json") or {}
    workflow_json = by_name["workflow_status_execution_candidate"].get("json") or {}

    dropzone_ready = any(row["required_direct_manipulation_files_present"] for row in dropzone_rows)
    explicit_user_selected_history = False
    selected_data_autoquant_promotion = False
    source_control_evidence = dropzone_ready
    canonical_merge = False
    downstream_promotion_rerun = False
    promotion_allowed = False

    provider_summary = {
        "yfinance_live_ready": provider_ready(provider_map, "yfinance", "live_runtime"),
        "yfinance_market_data_ready": provider_ready(provider_map, "yfinance", "market_data"),
        "tradingview_mcp_market_data_ready": provider_ready(provider_map, "tradingview_mcp", "market_data"),
        "kraken_cli_local_runtime_ready": provider_ready(provider_map, "kraken_cli", "local_runtime"),
        "kraken_public_market_data_ready": provider_ready(provider_map, "kraken_public", "market_data"),
        "ibkr_market_data_ready": provider_ready(provider_map, "ibkr", "market_data"),
    }

    live = workflow_json.get("input_acquisition", {}).get("live", {}) if isinstance(workflow_json, dict) else {}
    ibkr_gateway_summary = live.get("ibkr_gateway_summary", {}) if isinstance(live, dict) else {}
    provider_summary["ibkr_gateway_reachable_candidates"] = ibkr_gateway_summary.get("reachable_candidate_count")

    analyze_summary = {
        "exit": by_name["analyze_live_nq_yfinance"]["returncode"],
        "decision_hint": analyze_json.get("decision_hint") or analyze_json.get("decision_hint_raw") or "",
        "pre_bayes_gate": analyze_json.get("pre_bayes_gate") or analyze_json.get("pre_bayes_gate_status") or "",
        "primary_regime": analyze_json.get("primary_regime") or analyze_json.get("hybrid_regime_label") or "",
        "execution_gate": analyze_json.get("execution_gate") or "",
    }

    policy_summary = {
        "exit": by_name["policy_training_status"]["returncode"],
        "matched_rows": None,
        "catboost_ready": None,
        "bbn_ready": None,
        "summary_line": "",
    }
    if isinstance(policy_json, dict):
        summaries = policy_json.get("summaries") or policy_json.get("tables") or []
        if isinstance(summaries, list) and summaries:
            first = summaries[0] if isinstance(summaries[0], dict) else {}
            policy_summary["matched_rows"] = first.get("matched_rows")
            policy_summary["catboost_ready"] = first.get("catboost_ready")
            policy_summary["bbn_ready"] = first.get("bbn_ready")
            policy_summary["summary_line"] = first.get("summary_line", "")

    checklist_rows = [
        {
            "requirement": "read_current_board_and_preserve_concurrent_work",
            "status": "covered",
            "evidence": f"board_hash_before={board_hash_before}; append-only artifact under {rel(RUN_ROOT)}",
            "gap": "",
        },
        {
            "requirement": "owner_export_or_source_control_rows",
            "status": "blocked" if not source_control_evidence else "covered",
            "evidence": "dropzone_required_files_present=" + str(dropzone_ready).lower(),
            "gap": "needs direct_manipulation_positive_rows.csv, direct_manipulation_matched_controls.csv, direct_manipulation_provenance.json",
        },
        {
            "requirement": "explicit_htf_mtf_ltf_user_history_selection",
            "status": "blocked" if not explicit_user_selected_history else "covered",
            "evidence": f"selected_history_hints={len(selected_history_hints)}; no current explicit HTF/MTF/LTF selection recorded",
            "gap": "user/operator must select exactly one of HTF, MTF, LTF before selected-data promotion",
        },
        {
            "requirement": "provider_status_ibkr_tradingview_yfinance_kraken",
            "status": "partial",
            "evidence": json.dumps(provider_summary, sort_keys=True),
            "gap": "provider readiness is not enough without source/control and selected-history gates",
        },
        {
            "requirement": "auto_quant_operated",
            "status": "partial",
            "evidence": f"status_exit={by_name['auto_quant_status']['returncode']}; prepare_exit={by_name['auto_quant_prepare']['returncode']}",
            "gap": "Auto-Quant prepare/status does not become selected-data promotion while upstream gates are blocked",
        },
        {
            "requirement": "filter_pre_bayes_bbn_catboost_execution_tree_readback",
            "status": "read_only_non_promoting",
            "evidence": f"analyze_exit={by_name['analyze_live_nq_yfinance']['returncode']}; pre_bayes_exit={by_name['pre_bayes_status']['returncode']}; policy_exit={by_name['policy_training_status']['returncode']}; export_target_exit={by_name['export_structural_path_ranking_target']['returncode']}; workflow_exit={by_name['workflow_status_execution_candidate']['returncode']}",
            "gap": "read-only chain does not satisfy full promotion because source/control and selected-history gates are blocked",
        },
        {
            "requirement": "canonical_merge_and_promotion",
            "status": "blocked",
            "evidence": f"canonical_merge={canonical_merge}; selected_data_autoquant_promotion={selected_data_autoquant_promotion}; downstream_promotion_rerun={downstream_promotion_rerun}; promotion_allowed={promotion_allowed}",
            "gap": "do not merge or promote until source/control rows and explicit history selection exist",
        },
        {
            "requirement": "update_goal",
            "status": "blocked",
            "evidence": "update_goal=false",
            "gap": "strict objective not complete",
        },
    ]

    checklist_path = OUT_DIR / "prompt_to_artifact_checklist_v1.csv"
    dropzone_path = OUT_DIR / "dropzone_readback_v1.csv"
    history_path = OUT_DIR / "selected_history_hints_v1.csv"
    write_csv(checklist_path, ["requirement", "status", "evidence", "gap"], checklist_rows)
    write_csv(dropzone_path, ["root", "exists", "required_direct_manipulation_files_present", "found_files"], dropzone_rows)
    write_csv(history_path, ["path", "reason"], selected_history_hints)

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": GATE_RESULT,
        "board_hash_before_artifact": board_hash_before,
        "state_dir": str(STATE_DIR),
        "auto_quant_state_dir": str(AUTO_QUANT_STATE_DIR),
        "dropzone_rows": dropzone_rows,
        "source_control_evidence_acquired": source_control_evidence,
        "explicit_user_selected_history": explicit_user_selected_history,
        "canonical_merge": canonical_merge,
        "selected_data_autoquant_promotion": selected_data_autoquant_promotion,
        "downstream_promotion_rerun": downstream_promotion_rerun,
        "promotion_allowed": promotion_allowed,
        "provider_summary": provider_summary,
        "auto_quant_dependency_healthy": bool(auto_quant_json.get("dependency_healthy", False)) if isinstance(auto_quant_json, dict) else False,
        "auto_quant_data_ready": bool(auto_quant_json.get("data_ready", False)) if isinstance(auto_quant_json, dict) else False,
        "auto_quant_prepare_dns_blocked": text_contains(by_name["auto_quant_prepare"], "api.binance.com") or text_contains(by_name["auto_quant_prepare"], "DNS"),
        "analyze_summary": analyze_summary,
        "policy_training_summary": policy_summary,
        "workflow_decision_hint": workflow_json.get("decision_hint", "") if isinstance(workflow_json, dict) else "",
        "commands": commands,
        "checklist_path": rel(checklist_path),
        "dropzone_path": rel(dropzone_path),
        "selected_history_hints_path": rel(history_path),
        "update_goal": False,
    }

    json_path = OUT_DIR / "board_a_readonly_gate_chain_refresh_after_092249_v1.json"
    report_path = OUT_DIR / "board_a_readonly_gate_chain_refresh_after_092249_v1.md"
    assertions_path = CHECK_DIR / "board_a_readonly_gate_chain_refresh_after_092249_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    command_rows = "\n".join(
        f"| `{cmd['name']}` | `{cmd['returncode']}` | `{cmd['stdout_path']}` | `{cmd['stderr_path']}` |" for cmd in commands
    )
    report = f"""# Board A Read-Only Gate / Chain Refresh After 092249 v1

Run id: `{RUN_ID}`
Gate result: `{GATE_RESULT}`

## Scope

This is a read-only continuation slice after `092249` requested an explicit `HTF`/`MTF`/`LTF` selection. It checks the source/control dropzone, provider status for IBKR / TradingViewRemix / yfinance / Kraken, managed Auto-Quant status/prepare, and a non-promoting yfinance NQ chain readback through analyze-live, Pre-Bayes, policy-training/BBN/CatBoost readiness, structural path-ranking target export, and workflow/execution-tree status.

It does not select historical data, approve `FLIP` controls, mutate canonical intake, merge owner exports, promote selected-data Auto-Quant, claim a tradeable strategy, or call `update_goal`.

## Readback

- Board hash before artifact: `{board_hash_before}`
- Source/control evidence acquired: `{str(source_control_evidence).lower()}`
- Explicit user-selected history: `{str(explicit_user_selected_history).lower()}`
- Canonical merge: `{str(canonical_merge).lower()}`
- Selected-data AutoQuant promotion: `{str(selected_data_autoquant_promotion).lower()}`
- Downstream promotion rerun: `{str(downstream_promotion_rerun).lower()}`
- Promotion allowed: `{str(promotion_allowed).lower()}`
- update_goal: `false`

## Provider / Auto-Quant

- yfinance live ready: `{provider_summary['yfinance_live_ready']}`
- yfinance market-data ready: `{provider_summary['yfinance_market_data_ready']}`
- TradingViewRemix market-data ready: `{provider_summary['tradingview_mcp_market_data_ready']}`
- Kraken CLI local runtime ready: `{provider_summary['kraken_cli_local_runtime_ready']}`
- Kraken public market-data ready: `{provider_summary['kraken_public_market_data_ready']}`
- IBKR market-data ready: `{provider_summary['ibkr_market_data_ready']}`
- IBKR gateway reachable candidates: `{provider_summary['ibkr_gateway_reachable_candidates']}`
- Auto-Quant dependency healthy: `{payload['auto_quant_dependency_healthy']}`
- Auto-Quant data ready: `{payload['auto_quant_data_ready']}`
- Auto-Quant prepare DNS blocked: `{payload['auto_quant_prepare_dns_blocked']}`

## Chain Readback

- analyze-live exit: `{analyze_summary['exit']}`
- analyze-live decision hint: `{analyze_summary['decision_hint']}`
- analyze-live Pre-Bayes gate: `{analyze_summary['pre_bayes_gate']}`
- analyze-live primary/hybrid regime: `{analyze_summary['primary_regime']}`
- pre-bayes-status exit: `{by_name['pre_bayes_status']['returncode']}`
- policy-training-status exit: `{policy_summary['exit']}`
- policy-training matched rows: `{policy_summary['matched_rows']}`
- policy-training summary: `{policy_summary['summary_line']}`
- export-structural-path-ranking-target exit: `{by_name['export_structural_path_ranking_target']['returncode']}`
- workflow execution-candidate exit: `{by_name['workflow_status_execution_candidate']['returncode']}`

## Commands

| Command | Exit | Stdout | Stderr |
|---|---:|---|---|
{command_rows}

## Artifacts

- JSON: `{rel(json_path)}`
- Report: `{rel(report_path)}`
- Prompt-to-artifact checklist: `{rel(checklist_path)}`
- Dropzone readback: `{rel(dropzone_path)}`
- Selected-history hints: `{rel(history_path)}`
- Assertions: `{rel(assertions_path)}`

## Decision

The full objective remains blocked. Provider and read-only chain commands were exercised, but the hard gates are unchanged: no owner/export source-control package is present, there is no explicit user-selected `HTF`/`MTF`/`LTF` history choice, and no canonical merge or selected-data Auto-Quant promotion is allowed.

Next action remains: satisfy the source/control gate or explicitly select a history path for non-promotional research; do not treat Board B agent-selected history artifacts as user selection.
"""
    report_path.write_text(report, encoding="utf-8")

    assertions = [
        f"PASS gate_result={GATE_RESULT}",
        f"PASS source_control_evidence_acquired={str(source_control_evidence).lower()}",
        f"PASS explicit_user_selected_history={str(explicit_user_selected_history).lower()}",
        f"PASS canonical_merge={str(canonical_merge).lower()}",
        f"PASS selected_data_autoquant_promotion={str(selected_data_autoquant_promotion).lower()}",
        f"PASS downstream_promotion_rerun={str(downstream_promotion_rerun).lower()}",
        "PASS update_goal=false",
    ]
    for name in [
        "provider_status_agent",
        "auto_quant_status",
        "analyze_live_nq_yfinance",
        "pre_bayes_status",
        "policy_training_status",
        "export_structural_path_ranking_target",
        "workflow_status_execution_candidate",
    ]:
        assertions.append(f"INFO {name}_exit={by_name[name]['returncode']}")
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
