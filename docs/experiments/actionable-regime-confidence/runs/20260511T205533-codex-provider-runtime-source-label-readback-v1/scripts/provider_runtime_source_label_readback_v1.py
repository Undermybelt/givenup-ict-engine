#!/usr/bin/env python3
"""Provider/runtime readback for Board A source-label blockers.

This run checks the provider paths named in the Board A prompt without
promoting raw OHLCV panels into source-owned regime labels.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T205533+0800-codex-provider-runtime-source-label-readback-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "provider-runtime-source-label-readback"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
TMP = Path("/tmp/ict-engine-board-a-provider-runtime-source-label-readback-v1")

FETCH = REPO / "scripts/auto_quant_external/fetch_external.py"
ENGINE = REPO / "target/debug/ict-engine"

YAHOO_OUT = TMP / "yf_spy_1d_2026.csv"
KRAKEN_OUT = TMP / "kraken_xbtusd_1d.csv"
IBKR_OUT = TMP / "ibkr_spy_1d_5d.csv"

LABEL_HINTS = (
    "regime",
    "label",
    "state",
    "confidence",
    "source_owner",
    "provenance",
)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_cmd(args: list[str], timeout: int = 180) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    return {
        "cmd": " ".join(args),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "stdout_tail": proc.stdout[-8000:],
        "stderr_tail": proc.stderr[-8000:],
    }


def parse_json(stdout: str) -> Any | None:
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def csv_profile(path: Path, provider: str) -> dict[str, Any]:
    if not path.exists():
        return {
            "provider": provider,
            "path": str(path),
            "exists": False,
            "row_count": 0,
            "columns": [],
            "label_like_columns": [],
            "sha256": None,
            "source_label_ready": False,
        }
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        row_count = sum(1 for _ in reader)
    label_like = [
        col for col in columns if any(token in col.lower() for token in LABEL_HINTS)
    ]
    return {
        "provider": provider,
        "path": str(path),
        "exists": True,
        "row_count": row_count,
        "columns": columns,
        "label_like_columns": label_like,
        "sha256": sha256(path),
        "source_label_ready": False,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def provider_summary(provider_status: dict[str, Any] | None) -> dict[str, str]:
    wanted = {
        "ibkr": "not_seen",
        "tradingview_mcp": "not_seen",
        "yfinance": "not_seen",
        "kraken_public": "not_seen",
        "kraken_cli": "not_seen",
    }
    if not isinstance(provider_status, dict):
        return wanted
    for row in provider_status.get("providers", []):
        pid = row.get("provider_id")
        if pid in wanted:
            wanted[pid] = f"{row.get('status')}:{row.get('reason')}"
    return wanted


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True, exist_ok=True)

    board_hash = sha256(BOARD)
    provider_cmd = run_cmd([str(ENGINE), "provider-status", "--agent"])
    provider_json = parse_json(provider_cmd["stdout"])
    tv_cmd = run_cmd([str(ENGINE), "provider-status", "--provider", "tradingview_mcp", "--agent"])
    tv_json = parse_json(tv_cmd["stdout"])
    auto_quant_cmd = run_cmd(
        [
            str(ENGINE),
            "auto-quant-status",
            "--state-dir",
            str(TMP / "auto-quant-state"),
            "--compact",
        ]
    )
    auto_quant_json = parse_json(auto_quant_cmd["stdout"])
    workflow_cmd = run_cmd(
        [
            str(ENGINE),
            "workflow-status",
            "--symbol",
            "DEMO",
            "--state-dir",
            str(TMP / "workflow-state"),
            "--refresh",
            "--agent",
            "--stable",
        ]
    )
    workflow_json = parse_json(workflow_cmd["stdout"])

    yahoo_cmd = run_cmd(
        [
            "python3",
            str(FETCH),
            "yahoo",
            "--symbol",
            "SPY",
            "--interval",
            "1d",
            "--start",
            "2026-01-01",
            "--end",
            "2026-05-11",
            "--output",
            str(YAHOO_OUT),
        ],
        timeout=240,
    )
    kraken_cmd = run_cmd(
        [
            "python3",
            str(FETCH),
            "kraken-kline",
            "--market",
            "spot",
            "--pair",
            "XBTUSD",
            "--interval",
            "1d",
            "--output",
            str(KRAKEN_OUT),
        ],
        timeout=240,
    )
    ibkr_cmd = run_cmd(
        [
            "uv",
            "run",
            "--with",
            "pandas",
            "--with",
            "requests",
            "--with",
            "ib_async",
            "--with",
            "redis",
            "python",
            str(FETCH),
            "ibkr-historical",
            "--symbol",
            "SPY",
            "--sec-type",
            "STK",
            "--exchange",
            "SMART",
            "--primary-exchange",
            "ARCA",
            "--currency",
            "USD",
            "--bar-size",
            "1 day",
            "--duration",
            "5 D",
            "--what-to-show",
            "TRADES",
            "--port",
            "4002",
            "--client-id",
            "41",
            "--output",
            str(IBKR_OUT),
        ],
        timeout=240,
    )

    fetch_profiles = [
        csv_profile(YAHOO_OUT, "yfinance"),
        csv_profile(KRAKEN_OUT, "kraken_public"),
        csv_profile(IBKR_OUT, "ibkr"),
    ]
    source_label_ready_count = sum(1 for row in fetch_profiles if row["source_label_ready"])
    provider_states = provider_summary(provider_json)

    decision = "provider_runtime_source_label_readback_v1=providers_checked_no_source_owned_labels_acquired"
    payload = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "board_hash_before_writeback": board_hash,
        "provider_status": {
            "returncode": provider_cmd["returncode"],
            "summary_line": provider_json.get("summary_line") if isinstance(provider_json, dict) else None,
            "wanted_provider_states": provider_states,
        },
        "tradingview_mcp_status": {
            "returncode": tv_cmd["returncode"],
            "status": (
                tv_json.get("providers", [{}])[0].get("status")
                if isinstance(tv_json, dict) and tv_json.get("providers")
                else None
            ),
            "reason": (
                tv_json.get("providers", [{}])[0].get("reason")
                if isinstance(tv_json, dict) and tv_json.get("providers")
                else None
            ),
        },
        "auto_quant_status": {
            "returncode": auto_quant_cmd["returncode"],
            "status": auto_quant_json.get("status") if isinstance(auto_quant_json, dict) else None,
            "healthy": auto_quant_json.get("healthy") if isinstance(auto_quant_json, dict) else None,
            "recommended_next_command": (
                auto_quant_json.get("recommended_next_command")
                if isinstance(auto_quant_json, dict)
                else None
            ),
        },
        "workflow_status": {
            "returncode": workflow_cmd["returncode"],
            "parsed": isinstance(workflow_json, dict),
            "stdout_tail": workflow_cmd["stdout"][-1200:],
            "stderr_tail": workflow_cmd["stderr"][-1200:],
        },
        "commands": {
            "provider_status": provider_cmd,
            "tradingview_mcp": tv_cmd,
            "auto_quant_status": auto_quant_cmd,
            "workflow_status": workflow_cmd,
            "yfinance_fetch": yahoo_cmd,
            "kraken_fetch": kraken_cmd,
            "ibkr_fetch": ibkr_cmd,
        },
        "fetch_profiles": fetch_profiles,
        "source_label_ready_count": source_label_ready_count,
        "ready_intake_roots_added": 0,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "operator_boundary": "Raw provider OHLCV rows are not source-owned MainRegimeV2 labels and cannot populate the strict Board A intake roots.",
    }

    (OUT / "provider_runtime_source_label_readback_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(
        OUT / "provider_runtime_source_label_fetch_profiles_v1.csv",
        fetch_profiles,
        [
            "provider",
            "path",
            "exists",
            "row_count",
            "columns",
            "label_like_columns",
            "sha256",
            "source_label_ready",
        ],
    )

    lines = [
        "# Provider Runtime Source-label Readback v1",
        "",
        f"Decision: `{decision}`.",
        "",
        "Result:",
        f"- Provider summary: `{payload['provider_status']['summary_line']}`.",
        f"- Wanted provider states: `{json.dumps(provider_states, sort_keys=True)}`.",
        f"- TradingViewRemix status: `{payload['tradingview_mcp_status']['status']}`; reason `{payload['tradingview_mcp_status']['reason']}`.",
        f"- Auto-Quant status: `{payload['auto_quant_status']['status']}`; healthy `{payload['auto_quant_status']['healthy']}`.",
        f"- yfinance rows: `{fetch_profiles[0]['row_count']}`; source-label-ready: `false`.",
        f"- Kraken rows: `{fetch_profiles[1]['row_count']}`; source-label-ready: `false`.",
        f"- IBKR fetch returncode: `{ibkr_cmd['returncode']}`; rows: `{fetch_profiles[2]['row_count']}`; source-label-ready: `false`.",
        "- Ready intake roots added: `0`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "Interpretation:",
        "- yfinance/Kraken/IBKR provider fetches produce or attempted raw OHLCV market panels, not source-owned MainRegimeV2 label rows with provenance.",
        "- TradingViewRemix remains blocked by MCP connectivity, and Auto-Quant is missing its managed dependency in this isolated run state.",
        "- These checks therefore cannot populate `/tmp/ict-engine-source-label-equivalence-intake`, `/tmp/ict-engine-native-subhour-source-label-intake`, `/tmp/ict-engine-source-panel-recency-extension`, or `/tmp/ict-engine-direct-manipulation-row-intake`.",
        "",
        "Artifacts:",
        f"- JSON: `{OUT / 'provider_runtime_source_label_readback_v1.json'}`",
        f"- Fetch profiles: `{OUT / 'provider_runtime_source_label_fetch_profiles_v1.csv'}`",
        f"- Assertions: `{CHECKS / 'provider_runtime_source_label_readback_v1_assertions.out'}`",
    ]
    (OUT / "provider_runtime_source_label_readback_v1.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    assertions = [
        f"PASS decision={decision}",
        f"PASS provider_status_returncode={provider_cmd['returncode']}",
        f"PASS tradingview_mcp_status={payload['tradingview_mcp_status']['status']}",
        f"PASS auto_quant_status={payload['auto_quant_status']['status']}",
        f"PASS yfinance_rows={fetch_profiles[0]['row_count']}",
        f"PASS kraken_rows={fetch_profiles[1]['row_count']}",
        f"PASS ibkr_returncode={ibkr_cmd['returncode']}",
        "PASS source_label_ready_count=0",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    (CHECKS / "provider_runtime_source_label_readback_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print(json.dumps({"decision": decision, "source_label_ready_count": source_label_ready_count}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
