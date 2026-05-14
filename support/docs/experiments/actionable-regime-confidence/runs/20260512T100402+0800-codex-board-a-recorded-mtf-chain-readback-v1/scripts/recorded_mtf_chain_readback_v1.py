#!/usr/bin/env python3
"""Run-local recorded-MTF chain readback.

This script is intentionally scoped to the existing 100402 run root. It captures
read-only provider/AQ/downstream command outputs and writes a compact evidence
packet without mutating repo runtime code or shared intake roots.
"""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = RUN_ROOT.parents[4]
STATE_DIR = RUN_ROOT / "state_recorded_mtf_chain_readback_v1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
OUT = RUN_ROOT / "command-output"
PACKET = RUN_ROOT / "recorded-mtf-chain-readback-v1"
CHECKS = RUN_ROOT / "checks"
BIN = REPO / "target/debug/ict-engine"


def run_command(name: str, args: list[str], timeout: int = 120) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    cmd_path = OUT / f"{name}.cmd"
    out_path = OUT / f"{name}.out"
    err_path = OUT / f"{name}.err"
    exit_path = OUT / f"{name}.exit"
    cmd_path.write_text(" ".join(args) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        code = 124
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{code}\n", encoding="utf-8")
    return {
        "name": name,
        "args": args,
        "exit": code,
        "stdout_path": str(out_path.relative_to(REPO)),
        "stderr_path": str(err_path.relative_to(REPO)),
        "cmd_path": str(cmd_path.relative_to(REPO)),
        "exit_path": str(exit_path.relative_to(REPO)),
        "stdout": stdout,
        "stderr": stderr,
    }


def parse_jsonish(text: str) -> Any:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        lines = []
        for line in stripped.splitlines():
            try:
                lines.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return lines or None


def walk_find(obj: Any, keys: set[str], found: dict[str, Any]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in keys and key not in found:
                found[key] = value
            walk_find(value, keys, found)
    elif isinstance(obj, list):
        for item in obj:
            walk_find(item, keys, found)


def summarize_provider(records: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(records, dict) and isinstance(records.get("providers"), list):
        records = records["providers"]
    elif not isinstance(records, list):
        records = [records] if isinstance(records, dict) else []
    for item in records:
        if not isinstance(item, dict) or not item.get("provider_id"):
            continue
        rows.append(
            {
                "provider_id": item.get("provider_id"),
                "domain": item.get("domain"),
                "ready": item.get("ready"),
                "status": item.get("status"),
                "reason": item.get("reason"),
                "user_access": item.get("user_access"),
            }
        )
    return rows


def main() -> int:
    PACKET.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    commands = [
        (
            "10_provider_status_agent",
            [str(BIN), "provider-status", "--agent"],
            120,
        ),
        (
            "11_provider_status_yfinance",
            [str(BIN), "provider-status", "--provider", "yfinance", "--agent"],
            90,
        ),
        (
            "12_provider_status_tradingview_mcp",
            [str(BIN), "provider-status", "--provider", "tradingview_mcp", "--agent"],
            90,
        ),
        (
            "13_provider_status_ibkr",
            [str(BIN), "provider-status", "--provider", "ibkr", "--agent"],
            90,
        ),
        (
            "14_provider_status_ibkr_bridge",
            [str(BIN), "provider-status", "--provider", "ibkr_bridge", "--agent"],
            90,
        ),
        (
            "15_provider_status_kraken_public",
            [str(BIN), "provider-status", "--provider", "kraken_public", "--agent"],
            90,
        ),
        (
            "16_provider_status_kraken_cli",
            [str(BIN), "provider-status", "--provider", "kraken_cli", "--agent"],
            90,
        ),
        (
            "17_provider_status_binance_public",
            [str(BIN), "provider-status", "--provider", "binance_public", "--agent"],
            90,
        ),
        (
            "18_provider_status_bybit_public",
            [str(BIN), "provider-status", "--provider", "bybit_public", "--agent"],
            90,
        ),
        (
            "20_auto_quant_status_json",
            [
                str(BIN),
                "auto-quant-status",
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
            90,
        ),
        (
            "30_pre_bayes_status_json",
            [
                str(BIN),
                "pre-bayes-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--output-format",
                "json",
            ],
            90,
        ),
        (
            "40_policy_training_status_json",
            [
                str(BIN),
                "policy-training-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
            90,
        ),
        (
            "50_workflow_structural_bundle_json",
            [
                str(BIN),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--phase",
                "structural-recommended-path-bundle",
                "--output-format",
                "json",
            ],
            90,
        ),
        (
            "51_workflow_execution_candidate_json",
            [
                str(BIN),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--phase",
                "execution-candidate",
                "--output-format",
                "json",
            ],
            90,
        ),
        (
            "52_workflow_full_json",
            [
                str(BIN),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--output-format",
                "json",
            ],
            90,
        ),
        (
            "60_export_structural_path_ranking_target",
            [
                str(BIN),
                "export-structural-path-ranking-target",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
            ],
            90,
        ),
        (
            "70_harness_yfinance_qqq_1d",
            [
                str(BIN),
                "market-data-harness",
                "--action",
                "fetch",
                "--market",
                "recorded-mtf-yfinance-qqq-1d",
                "--interval",
                "1d",
                "--role",
                "etf_reference",
                "--provider",
                "etf_reference=yfinance",
                "--symbol-spec",
                "etf_reference=QQQ",
            ],
            120,
        ),
        (
            "71_harness_tradingview_qqq_1d",
            [
                str(BIN),
                "market-data-harness",
                "--action",
                "fetch",
                "--market",
                "recorded-mtf-tradingview-qqq-1d",
                "--interval",
                "1d",
                "--role",
                "etf_reference",
                "--provider",
                "etf_reference=tradingview_mcp",
                "--symbol-spec",
                "etf_reference=NASDAQ:QQQ",
            ],
            120,
        ),
    ]

    results = [run_command(name, args, timeout) for name, args, timeout in commands]
    parsed = {item["name"]: parse_jsonish(item["stdout"]) for item in results}

    provider_rows = summarize_provider(parsed.get("10_provider_status_agent"))
    provider_csv = PACKET / "provider_matrix_v1.csv"
    with provider_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "provider_id",
                "domain",
                "ready",
                "status",
                "reason",
                "user_access",
            ],
        )
        writer.writeheader()
        writer.writerows(provider_rows)

    key_fields: dict[str, Any] = {}
    for name in [
        "30_pre_bayes_status_json",
        "40_policy_training_status_json",
        "50_workflow_structural_bundle_json",
        "51_workflow_execution_candidate_json",
        "52_workflow_full_json",
    ]:
        found: dict[str, Any] = {}
        walk_find(
            parsed.get(name),
            {
                "regime_profit_branch_path",
                "branch_path",
                "path_ranker_runtime_source",
                "path_ranker_raw_score",
                "pre_bayes_gate_status",
                "execution_readiness",
                "candidate_status",
                "review_status",
                "ready",
                "actionable",
                "closed_loop_confidence",
                "closed_loop_branch_admission",
            },
            found,
        )
        key_fields[name] = found

    required_provider_ids = {
            "yfinance",
            "tradingview_mcp",
            "ibkr",
            "ibkr_bridge",
            "kraken_public",
            "kraken_cli",
            "binance_public",
            "bybit_public",
        }
    provider_ready = {pid: [row for row in provider_rows if row.get("provider_id") == pid] for pid in required_provider_ids}

    def any_ready(provider_id: str) -> bool:
        return any(row.get("ready") is True for row in provider_ready.get(provider_id, []))

    def reasons(provider_id: str) -> list[Any]:
        return [row.get("reason") for row in provider_ready.get(provider_id, [])]

    all_exits_zero = all(item["exit"] == 0 for item in results[:16])
    yfinance_ready = any_ready("yfinance")
    tradingview_ready = any_ready("tradingview_mcp")
    kraken_cli_ready = any_ready("kraken_cli")
    ibkr_ready = any_ready("ibkr")
    workflow_text = json.dumps(key_fields, sort_keys=True)
    by_name = {item["name"]: item for item in results}
    tradingview_fetch_error = by_name.get("71_harness_tradingview_qqq_1d", {}).get("stderr", "")
    tradingview_fetch_error = tradingview_fetch_error.strip().splitlines()[0] if tradingview_fetch_error.strip() else ""
    harness_readback = {
        "yfinance_qqq_1d_exit": by_name.get("70_harness_yfinance_qqq_1d", {}).get("exit"),
        "tradingview_mcp_qqq_1d_exit": by_name.get("71_harness_tradingview_qqq_1d", {}).get("exit"),
        "tradingview_mcp_qqq_1d_error": tradingview_fetch_error,
    }
    promotion_allowed = False
    update_goal = False

    summary = {
        "run_id": "20260512T100402+0800-codex-board-a-recorded-mtf-chain-readback-v1",
        "mode": "incubation_only_readback",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "symbol": SYMBOL,
        "state_dir": str(STATE_DIR.relative_to(REPO)),
        "command_results": [
            {
                key: item[key]
                for key in [
                    "name",
                    "exit",
                    "cmd_path",
                    "stdout_path",
                    "stderr_path",
                    "exit_path",
                ]
            }
            for item in results
        ],
        "provider_matrix": provider_rows,
        "provider_readiness_summary": {
            "yfinance_ready": yfinance_ready,
            "tradingview_mcp_ready": tradingview_ready,
            "kraken_cli_ready": kraken_cli_ready,
            "ibkr_ready": ibkr_ready,
            "ibkr_bridge_ready": any_ready("ibkr_bridge"),
            "kraken_public_ready": any_ready("kraken_public"),
            "binance_public_ready": any_ready("binance_public"),
            "bybit_public_ready": any_ready("bybit_public"),
            "ibkr_reasons": reasons("ibkr"),
            "tradingview_mcp_reasons": reasons("tradingview_mcp"),
            "kraken_public_reasons": reasons("kraken_public"),
            "binance_public_reasons": reasons("binance_public"),
            "bybit_public_reasons": reasons("bybit_public"),
        },
        "harness_readback": harness_readback,
        "downstream_key_fields": key_fields,
        "promotion_allowed": promotion_allowed,
        "update_goal": update_goal,
        "gate": "incubation_only_recorded_mtf_chain_readback_no_promotion",
        "blockers": [
            "explicit_selected_history_approval_absent",
            "board_a_source_control_unlock_absent",
            "pre_bayes_or_execution_readiness_not_promoting",
            "production_promotion_chain_not_authorized",
        ],
    }

    json_path = PACKET / "recorded_mtf_chain_readback_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = PACKET / "recorded_mtf_chain_readback_v1.md"
    md = [
        "# Recorded MTF Chain Readback v1",
        "",
        f"Run id: `{summary['run_id']}`",
        "",
        "Mode: `incubation_only_readback`.",
        "",
        "## Provider Readback",
        "",
        f"- yfinance ready: `{yfinance_ready}`.",
        f"- TradingViewRemix/MCP ready: `{tradingview_ready}`.",
        f"- Kraken CLI ready: `{kraken_cli_ready}`.",
        f"- IBKR market-data ready: `{ibkr_ready}`.",
        f"- yfinance QQQ 1d harness fetch exit: `{harness_readback['yfinance_qqq_1d_exit']}`.",
        f"- TradingViewRemix QQQ 1d harness fetch exit: `{harness_readback['tradingview_mcp_qqq_1d_exit']}`.",
        f"- TradingViewRemix fetch error: `{harness_readback['tradingview_mcp_qqq_1d_error'][:220]}`.",
        f"- Provider matrix CSV: `{provider_csv.relative_to(REPO)}`.",
        "",
        "## Downstream Readback",
        "",
        f"- Commands captured: `{len(results)}`.",
        f"- Provider/AQ/downstream core exits all zero: `{all_exits_zero}`.",
        f"- Key fields: `{workflow_text[:1200]}`.",
        "",
        "## Decision",
        "",
        "- Gate: `incubation_only_recorded_mtf_chain_readback_no_promotion`.",
        "- Promotion allowed: `false`.",
        "- `update_goal=false`.",
        "- This packet does not select `HTF`, `MTF`, or `LTF`; it does not approve source/control evidence; it does not mutate canonical intake.",
        "",
        "## Next",
        "",
        "Keep production gates fail-closed. The next qualifying move still needs explicit selected-history approval plus real Board A source/control unlock, or a new non-promoting recorded-history slice that improves execution readiness without reusing closed LTF/TOMAC dead ends.",
        "",
    ]
    md_path.write_text("\n".join(md), encoding="utf-8")

    assertion_path = CHECKS / "recorded_mtf_chain_readback_v1_assertions.out"
    assertions = {
        "report_exists": md_path.exists(),
        "json_exists": json_path.exists(),
        "provider_csv_exists": provider_csv.exists(),
        "provider_matrix_includes_required": all(
            provider_ready.get(provider_id) for provider_id in required_provider_ids
        ),
        "yfinance_ready": yfinance_ready,
        "tradingview_mcp_status_recorded": bool(provider_ready.get("tradingview_mcp")),
        "kraken_cli_ready": kraken_cli_ready,
        "promotion_allowed_false": promotion_allowed is False,
        "update_goal_false": update_goal is False,
        "workflow_mentions_observe_or_not_ready": ("observe" in workflow_text.lower())
        or ("false" in workflow_text.lower()),
    }
    ok = all(assertions.values())
    assertion_path.write_text(
        "\n".join(f"{key}={value}" for key, value in assertions.items()) + f"\nall={ok}\n",
        encoding="utf-8",
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
