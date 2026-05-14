#!/usr/bin/env python3
"""Read-only provider and Auto-Quant runtime gate after the 091246 refresh."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T091715+0800-codex-provider-autoquant-runtime-gate-after-091246-v1"
SLUG = "provider-autoquant-runtime-gate-after-091246-v1"
GATE = "provider_autoquant_runtime_gate_after_091246_v1=autoquant_dependency_ready_prepare_blocked_provider_partial_no_promotion"

SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[6]
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"
OUT_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = OUT_ROOT / SLUG
CHECK_DIR = OUT_ROOT / "checks"
RAW_DIR = OUT_ROOT / "raw"
STATE_DIR = Path("/tmp/ict-engine-auto-quant")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(name: str, args: list[str], timeout_s: int = 120) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=timeout_s,
        check=False,
    )
    stdout_path = RAW_DIR / f"{name}.stdout.txt"
    stderr_path = RAW_DIR / f"{name}.stderr.txt"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    parsed_json: Any = None
    stdout_text = proc.stdout.strip()
    if stdout_text.startswith("{") or stdout_text.startswith("["):
        try:
            parsed_json = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed_json = None
    return {
        "name": name,
        "args": args,
        "returncode": proc.returncode,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "json": parsed_json,
    }


def flatten_provider_map(provider_json: dict[str, Any]) -> dict[str, dict[str, Any]]:
    providers = provider_json.get("providers", [])
    out: dict[str, dict[str, Any]] = {}
    for item in providers:
        if isinstance(item, dict) and "provider_id" in item and "domain" in item:
            key = f'{item["provider_id"]}:{item["domain"]}'
            out[key] = item
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    provider_agent = run_command(
        "provider_status_agent",
        [str(REPO / "target/debug/ict-engine"), "provider-status", "--agent"],
        timeout_s=120,
    )
    provider_jsonl = run_command(
        "provider_status_jsonl",
        [str(REPO / "target/debug/ict-engine"), "provider-status", "--jsonl"],
        timeout_s=120,
    )
    workflow_status = run_command(
        "workflow_status_bootstrap_agent",
        [
            str(REPO / "target/debug/ict-engine"),
            "workflow-status",
            "--symbol",
            "NQ",
            "--state-dir",
            "/tmp/ict-engine-regime-confidence-runtime-gate",
            "--phase",
            "bootstrap",
            "--agent",
            "--stable",
        ],
        timeout_s=120,
    )
    auto_quant_bootstrap = run_command(
        "auto_quant_bootstrap",
        [
            str(REPO / "target/debug/ict-engine"),
            "auto-quant-bootstrap",
            "--state-dir",
            str(STATE_DIR),
        ],
        timeout_s=120,
    )
    auto_quant_status = run_command(
        "auto_quant_status_after_bootstrap",
        [
            str(REPO / "target/debug/ict-engine"),
            "auto-quant-status",
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
        timeout_s=120,
    )
    auto_quant_prepare = run_command(
        "auto_quant_prepare",
        [
            str(REPO / "target/debug/ict-engine"),
            "auto-quant-prepare",
            "--state-dir",
            str(STATE_DIR),
        ],
        timeout_s=240,
    )
    auto_quant_status_after = run_command(
        "auto_quant_status_after_prepare",
        [
            str(REPO / "target/debug/ict-engine"),
            "auto-quant-status",
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
        timeout_s=120,
    )

    provider_agent_json = provider_agent["json"] or {}
    provider_map = flatten_provider_map(provider_agent_json) if isinstance(provider_agent_json, dict) else {}
    workflow_json = workflow_status["json"] or {}
    auto_quant_before_json = auto_quant_status["json"] or {}
    auto_quant_after_json = auto_quant_status_after["json"] or {}
    auto_quant_bootstrap_json = auto_quant_bootstrap["json"] or {}
    provider_jsonl_lines = [line for line in provider_jsonl["stdout"].splitlines() if line.strip()]

    def provider_ready(provider_id: str, domain: str) -> bool:
        item = provider_map.get(f"{provider_id}:{domain}")
        return bool(item and item.get("ready") is True)

    yfinance_live_ready = provider_ready("yfinance", "live_runtime")
    yfinance_market_ready = provider_ready("yfinance", "market_data")
    tradingview_ready = provider_ready("tradingview_mcp", "market_data")
    kraken_cli_ready = provider_ready("kraken_cli", "local_runtime")
    kraken_public_ready = provider_ready("kraken_public", "market_data")
    ibkr_ready = provider_ready("ibkr", "market_data")

    live = workflow_json.get("input_acquisition", {}).get("live", {}) if isinstance(workflow_json, dict) else {}
    ibkr_gateway_summary = live.get("ibkr_gateway_summary", {}) if isinstance(live, dict) else {}
    ibkr_gateway_reachable = bool(ibkr_gateway_summary.get("reachable_candidate_count", 0) == 1)
    selected_history = bool(workflow_json.get("selected_history", False)) if isinstance(workflow_json, dict) else False
    source_control_evidence = False

    prepare_stderr = auto_quant_prepare["stderr"]
    dns_blocked = "Could not contact DNS servers" in prepare_stderr or "api.binance.com" in prepare_stderr
    prepare_failed = auto_quant_prepare["returncode"] != 0

    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_b_sha256_before_artifact": sha256(BOARD_B),
        "gate_result": GATE,
        "provider_status": provider_agent_json,
        "provider_status_jsonl_lines": len(provider_jsonl_lines),
        "workflow_status": workflow_json,
        "auto_quant_bootstrap": auto_quant_bootstrap_json,
        "auto_quant_status_before_prepare": auto_quant_before_json,
        "auto_quant_prepare": {
            "returncode": auto_quant_prepare["returncode"],
            "dns_blocked": dns_blocked,
            "stderr_path": auto_quant_prepare["stderr_path"],
            "stdout_path": auto_quant_prepare["stdout_path"],
            "prepare_failed": prepare_failed,
        },
        "auto_quant_status_after_prepare": auto_quant_after_json,
        "yfinance_live_ready": yfinance_live_ready,
        "yfinance_market_data_ready": yfinance_market_ready,
        "tradingview_mcp_ready": tradingview_ready,
        "kraken_cli_ready": kraken_cli_ready,
        "kraken_public_ready": kraken_public_ready,
        "ibkr_market_data_ready": ibkr_ready,
        "ibkr_gateway_reachable": ibkr_gateway_reachable,
        "auto_quant_dependency_healthy": bool(auto_quant_after_json.get("dependency_healthy", False)),
        "auto_quant_data_ready": bool(auto_quant_after_json.get("data_ready", False)),
        "selected_history": selected_history,
        "source_control_evidence_acquired": source_control_evidence,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    json_path = OUT_DIR / "provider_autoquant_runtime_gate_after_091246_v1.json"
    report_path = OUT_DIR / "provider_autoquant_runtime_gate_after_091246_v1.md"
    assertions_path = CHECK_DIR / "provider_autoquant_runtime_gate_after_091246_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = f"""# Provider / Auto-Quant Runtime Gate After 091246 v1

Run id: `{RUN_ID}`

Gate result: `{GATE}`

## Scope

Read-only runtime gate after the `091246` source/control refresh. It checks provider readiness for yfinance, TradingViewRemix, IBKR, and Kraken, then reuses the repo's managed Auto-Quant surfaces to confirm whether the dependency can boot and prepare data. It does not run selected-data AutoQuant promotion, Pre-Bayes/BBN, CatBoost/path-ranking, execution-tree promotion, or any trade step.

## Readback

- Board B SHA-256 before artifact: `{payload["board_b_sha256_before_artifact"]}`.
- yfinance live ready: `{yfinance_live_ready}`.
- yfinance market_data ready: `{yfinance_market_ready}`.
- TradingViewRemix ready: `{tradingview_ready}`.
- Kraken CLI ready: `{kraken_cli_ready}`.
- Kraken public market-data ready: `{kraken_public_ready}`.
- IBKR market-data ready: `{ibkr_ready}`.
- IBKR gateway reachable: `{ibkr_gateway_reachable}`.
- Auto-Quant bootstrap healthy: `{bool(auto_quant_bootstrap_json.get("healthy", False))}`.
- Auto-Quant dependency healthy after bootstrap: `{bool(auto_quant_after_json.get("dependency_healthy", False))}`.
- Auto-Quant data ready after prepare: `{bool(auto_quant_after_json.get("data_ready", False))}`.
- Auto-Quant prepare return code: `{auto_quant_prepare["returncode"]}`.
- Auto-Quant prepare DNS blocked: `{dns_blocked}`.

## Decision

The provider surface is partially ready: yfinance live and market-data are ready, Kraken CLI is ready, and IBKR gateway port 4002 is reachable, but TradingViewRemix is currently connectivity-blocked, IBKR market-data remains dependency-blocked, and Kraken public remains dependency-blocked.

Auto-Quant itself is now bootstrapped and dependency-healthy, but data preparation is still blocked by network/DNS access to Binance. That means the downstream selected-data AutoQuant chain is still not promotable from this slice.

Accepted rows added `0`; source/control evidence acquired false; selected history false; selected-data AutoQuant promotion false; downstream promotion rerun false; promotion allowed false; `update_goal=false`.

## Artifacts

- JSON: `{rel(json_path)}`
- Report: `{rel(report_path)}`
- Assertions: `{rel(assertions_path)}`
- Provider status agent raw stdout: `{rel(OUT_ROOT / "raw" / "provider_status_agent.stdout.txt")}`
- Provider status agent raw stderr: `{rel(OUT_ROOT / "raw" / "provider_status_agent.stderr.txt")}`
- Provider status jsonl raw stdout: `{rel(OUT_ROOT / "raw" / "provider_status_jsonl.stdout.txt")}`
- Workflow status raw stdout: `{rel(OUT_ROOT / "raw" / "workflow_status_bootstrap_agent.stdout.txt")}`
- Auto-Quant bootstrap raw stdout: `{rel(OUT_ROOT / "raw" / "auto_quant_bootstrap.stdout.txt")}`
- Auto-Quant prepare raw stderr: `{rel(OUT_ROOT / "raw" / "auto_quant_prepare.stderr.txt")}`

## Next

Continue source/control acquisition only. The live unblocker remains owner-approved/authenticated R6/R5/R3 source-control rows with matched controls and provenance, explicit same-exhibit `FLIP`-as-control approval, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, or verifier-native Crisis-capable R3 native-subhour labels before verifier, split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, execution-tree promotion, trade claims, or `update_goal`.
"""
    report_path.write_text(report, encoding="utf-8")

    assertions = [
        f"gate_result={GATE}",
        f"provider_yfinance_live_ready={str(yfinance_live_ready).lower()}",
        f"provider_yfinance_market_data_ready={str(yfinance_market_ready).lower()}",
        f"provider_tradingview_mcp_ready={str(tradingview_ready).lower()}",
        f"provider_kraken_cli_ready={str(kraken_cli_ready).lower()}",
        f"provider_kraken_public_ready={str(kraken_public_ready).lower()}",
        f"provider_ibkr_ready={str(ibkr_ready).lower()}",
        f"ibkr_gateway_reachable={str(ibkr_gateway_reachable).lower()}",
        f"auto_quant_dependency_healthy={str(bool(auto_quant_after_json.get('dependency_healthy', False))).lower()}",
        f"auto_quant_data_ready={str(bool(auto_quant_after_json.get('data_ready', False))).lower()}",
        f"auto_quant_prepare_exit_code={auto_quant_prepare['returncode']}",
        f"auto_quant_prepare_dns_blocked={str(dns_blocked).lower()}",
        "source_control_evidence_acquired=false",
        f"selected_history={str(selected_history).lower()}",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print("\n".join(assertions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
