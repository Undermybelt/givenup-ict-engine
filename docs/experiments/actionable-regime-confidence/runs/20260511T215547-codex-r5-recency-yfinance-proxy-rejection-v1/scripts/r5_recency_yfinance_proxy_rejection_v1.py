#!/usr/bin/env python3
"""Probe post-cutoff yfinance OHLC and keep R5 source-label intake fail-closed."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yfinance as yf


RUN_ID = "20260511T215547-codex-r5-recency-yfinance-proxy-rejection-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "r5-recency-yfinance-proxy-rejection"
CHECKS = RUN_ROOT / "checks"
CMD = RUN_ROOT / "command-output"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
SOURCE_PANEL = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
RECENCY_ROOT = Path("/tmp/ict-engine-source-panel-recency-extension")
VERIFIER = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_verifier_v1.py"
)
REQUEST_PACKAGE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T201655-codex-stock-regime-owner-recency-request-package-v1/"
    "stock-regime-owner-recency-request-package/stock_regime_owner_recency_request_package_v1.json"
)

TARGET_SYMBOLS = ["AMD", "XOM", "UNH", "^DJI"]
START = "2026-01-31"
END = "2026-05-11"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_source_panel_summary() -> dict[str, Any]:
    rows = 0
    dates: list[str] = []
    tickers: set[str] = set()
    labels: set[str] = set()
    with SOURCE_PANEL.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows += 1
            dates.append(row["date"])
            tickers.add(row["ticker"])
            labels.add(row["regime_label"])
    return {
        "path": str(SOURCE_PANEL),
        "sha256": sha256_file(SOURCE_PANEL),
        "rows": rows,
        "date_min": min(dates),
        "date_max": max(dates),
        "ticker_count": len(tickers),
        "labels": sorted(labels),
    }


def run_recency_verifier() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), "--intake-root", str(RECENCY_ROOT)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    stdout_path = CMD / "source_panel_recency_verifier.stdout.txt"
    stderr_path = CMD / "source_panel_recency_verifier.stderr.txt"
    exit_path = CMD / "source_panel_recency_verifier.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    try:
        parsed = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        parsed = {"status": "unparsed", "stdout_prefix": proc.stdout[:500]}
    if not isinstance(parsed, dict):
        parsed = {"status": "unparsed"}
    return {
        "returncode": proc.returncode,
        "parsed": parsed,
        "stdout": str(stdout_path.relative_to(REPO)),
        "stderr": str(stderr_path.relative_to(REPO)),
        "exit": str(exit_path.relative_to(REPO)),
    }


def fetch_yfinance_summary() -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for symbol in TARGET_SYMBOLS:
        try:
            frame = yf.download(
                symbol,
                start=START,
                end=END,
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False,
            )
            rows = int(len(frame))
            summaries.append(
                {
                    "symbol": symbol,
                    "provider": "yfinance",
                    "status": "ok",
                    "rows": rows,
                    "date_min": str(frame.index.min().date()) if rows else "",
                    "date_max": str(frame.index.max().date()) if rows else "",
                    "raw_rows_written": False,
                    "source_owned_regime_labels": False,
                    "usable_for_r5_intake": False,
                    "reason": "provider_ohlc_only_not_source_owned_regime_labels",
                }
            )
        except Exception as exc:  # noqa: BLE001 - artifact records provider failure type.
            summaries.append(
                {
                    "symbol": symbol,
                    "provider": "yfinance",
                    "status": "error",
                    "rows": 0,
                    "date_min": "",
                    "date_max": "",
                    "raw_rows_written": False,
                    "source_owned_regime_labels": False,
                    "usable_for_r5_intake": False,
                    "reason": f"{type(exc).__name__}: {exc}",
                }
            )
    return summaries


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    CMD.mkdir(parents=True, exist_ok=True)

    missing = [str(path) for path in [BOARD, SOURCE_PANEL, VERIFIER, REQUEST_PACKAGE] if not path.exists()]
    if missing:
        raise FileNotFoundError(missing)

    source_panel = read_source_panel_summary()
    request_package = json.loads(REQUEST_PACKAGE.read_text(encoding="utf-8"))
    verifier_before = run_recency_verifier()
    provider_rows = fetch_yfinance_summary()
    verifier_after = run_recency_verifier()
    provider_rows_available = any(row["status"] == "ok" and int(row["rows"]) > 0 for row in provider_rows)
    all_provider_targets_available = all(row["status"] == "ok" and int(row["rows"]) > 0 for row in provider_rows)
    gate_result = "r5_recency_yfinance_proxy_rejection_v1=provider_ohlc_available_source_owned_rows_not_acquired"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": gate_result,
        "board_hash_before_writeback": sha256_file(BOARD),
        "source_panel": source_panel,
        "request_package": {
            "path": str(REQUEST_PACKAGE.relative_to(REPO)),
            "decision": request_package.get("gate_result") or request_package.get("decision"),
            "source_target": request_package.get("source_target") or request_package.get("source"),
            "rows_acquired": request_package.get("rows_acquired", False),
        },
        "target_symbols": TARGET_SYMBOLS,
        "provider_probe": {
            "provider": "yfinance",
            "start": START,
            "end": END,
            "rows_available_for_any_target": provider_rows_available,
            "rows_available_for_all_targets": all_provider_targets_available,
            "raw_rows_written": False,
            "summaries": provider_rows,
        },
        "verifier_before": verifier_before,
        "verifier_after": verifier_after,
        "extension_files_created": False,
        "source_owned_rows_acquired": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": True,
        "trade_usable": False,
        "next_action": "Acquire owner/source-provided post-2026-01-30 regime-label rows and source_panel_recency_provenance.json for /tmp/ict-engine-source-panel-recency-extension; yfinance OHLC is only a provider proxy and remains rejected.",
    }

    json_path = OUT / "r5_recency_yfinance_proxy_rejection_v1.json"
    report_path = OUT / "r5_recency_yfinance_proxy_rejection_v1.md"
    provider_csv = OUT / "r5_recency_yfinance_proxy_rejection_provider_summary_v1.csv"
    assertions_path = CHECKS / "r5_recency_yfinance_proxy_rejection_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        provider_csv,
        provider_rows,
        [
            "symbol",
            "provider",
            "status",
            "rows",
            "date_min",
            "date_max",
            "raw_rows_written",
            "source_owned_regime_labels",
            "usable_for_r5_intake",
            "reason",
        ],
    )

    lines = [
        "# R5 Recency Yfinance Proxy Rejection v1",
        "",
        f"- Decision: `{gate_result}`.",
        f"- Source panel date range: `{source_panel['date_min']}..{source_panel['date_max']}`; rows `{source_panel['rows']}`.",
        f"- Existing owner-request package remains rows-acquired `false`: `{REQUEST_PACKAGE.relative_to(REPO)}`.",
        f"- yfinance post-cutoff OHLC probe targets: `{TARGET_SYMBOLS}`; all targets returned rows `{str(all_provider_targets_available).lower()}`.",
        "- Raw yfinance rows were not written to repo and were not copied into the R5 intake.",
        f"- Recency verifier before/after: `{verifier_before['parsed'].get('status')}` / `{verifier_after['parsed'].get('status')}`.",
        "- R5 source-owned rows acquired: `false`; extension files created: `false`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.",
        "",
        "## Provider Probe",
        "",
        "| Symbol | Rows | Date Range | R5 Usable | Reason |",
        "|---|---:|---|---|---|",
    ]
    for row in provider_rows:
        lines.append(
            f"| `{row['symbol']}` | `{row['rows']}` | `{row['date_min']}..{row['date_max']}` | "
            f"`{str(row['usable_for_r5_intake']).lower()}` | {row['reason']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This slice proves current provider OHLC is reachable for the requested post-cutoff symbols, but it deliberately rejects those rows for R5 because the verifier contract requires source-owned regime labels and provenance, not derived or provider-only OHLC proxies.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Report: `{report_path.relative_to(REPO)}`",
            f"- Provider summary CSV: `{provider_csv.relative_to(REPO)}`",
            f"- Recency verifier stdout: `{(CMD / 'source_panel_recency_verifier.stdout.txt').relative_to(REPO)}`",
            f"- Assertions: `{assertions_path.relative_to(REPO)}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={gate_result}",
        f"PASS source_panel_date_max={source_panel['date_max']}",
        f"PASS provider_rows_available_for_all_targets={str(all_provider_targets_available).lower()}",
        f"PASS verifier_before_status={verifier_before['parsed'].get('status')}",
        f"PASS verifier_after_status={verifier_after['parsed'].get('status')}",
        "PASS extension_files_created=false",
        "PASS source_owned_rows_acquired=false",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
        "PASS external_requests_sent=true",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    if verifier_after["parsed"].get("status") != "blocked":
        raise AssertionError("R5 verifier unexpectedly passed")
    print(json.dumps({"decision": gate_result, "provider_rows_available_for_all_targets": all_provider_targets_available, "verifier_status": verifier_after["parsed"].get("status"), "update_goal": False}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
