#!/usr/bin/env python3
"""Probe the ready IBKR lane and record exact Board A disposition.

Raw IBKR CSV output stays under /private/tmp. Repo artifacts are compact
summaries only. A successful bar fetch is provider availability evidence, not
accepted MainRegimeV2 confidence without independent root labels.
"""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T080720+0800-codex-ibkr-ready-lane-operator-probe"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T080720-codex-ibkr-ready-lane-operator-probe"
OUT_DIR = RUN_ROOT / "ibkr-ready-lane"
CHECK_DIR = RUN_ROOT / "checks"
RAW_ROOT = Path("/private/tmp/ict-regime-ibkr-ready-lane-20260511T080720")
FETCH_EXTERNAL = REPO / "scripts/auto_quant_external/fetch_external.py"
PUBLIC_CRYPTO_DISPOSITION = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260511T073200-codex-public-crypto-disposition-refresh"
    / "coverage-disposition/public_crypto_disposition_refresh.json"
)

UV_PACKAGES = ["requests", "pandas", "ib_async", "redis", "PyYAML"]

IBKR_CONTRACTS: dict[str, dict[str, str]] = {
    "DIA": {"symbol": "DIA", "sec_type": "STK", "exchange": "SMART", "currency": "USD", "primary_exchange": "ARCA"},
    "DJI": {"symbol": "DJI", "sec_type": "IND", "exchange": "CBOE", "currency": "USD"},
    "GLD": {"symbol": "GLD", "sec_type": "STK", "exchange": "SMART", "currency": "USD", "primary_exchange": "ARCA"},
    "NDX": {"symbol": "NDX", "sec_type": "IND", "exchange": "NASDAQ", "currency": "USD"},
    "QQQ": {"symbol": "QQQ", "sec_type": "STK", "exchange": "SMART", "currency": "USD", "primary_exchange": "NASDAQ"},
    "SPX": {"symbol": "SPX", "sec_type": "IND", "exchange": "CBOE", "currency": "USD"},
    "SPY": {"symbol": "SPY", "sec_type": "STK", "exchange": "SMART", "currency": "USD", "primary_exchange": "ARCA"},
    "USO": {"symbol": "USO", "sec_type": "STK", "exchange": "SMART", "currency": "USD", "primary_exchange": "ARCA"},
    "VIX": {"symbol": "VIX", "sec_type": "IND", "exchange": "CBOE", "currency": "USD"},
    "XAUUSD": {"symbol": "XAUUSD", "sec_type": "CASH", "exchange": "IDEALPRO", "currency": "USD"},
}

TIMEFRAME_TO_IBKR = {
    "1m": ("1 min", "7 D"),
    "5m": ("5 mins", "30 D"),
    "15m": ("15 mins", "60 D"),
    "30m": ("30 mins", "60 D"),
    "1h": ("1 hour", "6 M"),
    "4h": ("4 hours", "1 Y"),
    "1d": ("1 day", "5 Y"),
    "1w": ("1 week", "5 Y"),
    "1mo": ("1 month", "5 Y"),
}

ATTEMPT_SYMBOLS = {"SPY", "QQQ"}
ATTEMPT_TIMEFRAMES = {"1h", "1d"}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def truncate(text: str, limit: int = 1200) -> str:
    return text.strip()[-limit:]


def run_cmd(cmd: list[str], timeout: int = 90) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            cmd,
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None


def csv_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"rows": 0, "first_ts": "", "last_ts": ""}
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        ts_col = "date" if "date" in (reader.fieldnames or []) else "ts"
        count = 0
        first_ts = ""
        last_ts = ""
        for row in reader:
            count += 1
            value = row.get(ts_col, "")
            if count == 1:
                first_ts = value
            last_ts = value
    return {"rows": count, "first_ts": first_ts, "last_ts": last_ts}


def build_fetch_command(symbol: str, timeframe: str, output: Path) -> list[str]:
    contract = IBKR_CONTRACTS[symbol]
    bar_size, duration = TIMEFRAME_TO_IBKR[timeframe]
    cmd = ["uv", "run"]
    for package in UV_PACKAGES:
        cmd.extend(["--with", package])
    cmd.extend(
        [
            "python",
            str(FETCH_EXTERNAL),
            "ibkr-historical",
            "--symbol",
            contract["symbol"],
            "--sec-type",
            contract["sec_type"],
            "--exchange",
            contract["exchange"],
            "--currency",
            contract["currency"],
            "--bar-size",
            bar_size,
            "--duration",
            duration,
            "--output",
            str(output),
        ]
    )
    if contract.get("primary_exchange"):
        cmd.extend(["--primary-exchange", contract["primary_exchange"]])
    return cmd


def attempt_fetch(symbol: str, timeframe: str) -> dict[str, Any]:
    raw_path = RAW_ROOT / f"{symbol}_{timeframe}.csv"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    proc = run_cmd(build_fetch_command(symbol, timeframe, raw_path), timeout=90)
    row: dict[str, Any] = {
        "provider": "ibkr",
        "symbol": symbol,
        "timeframe": timeframe,
        "attempted": True,
        "raw_csv": str(raw_path),
        "raw_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "label_status": "missing_independent_root_labels",
        "accepted_for_confidence": False,
    }
    if proc is None:
        row.update(
            {
                "status": "fetch_timeout",
                "returncode": None,
                "reason": "uv_ibkr_fetch_timed_out_after_90s",
                "stdout": "",
                "stderr": "",
                "rows": 0,
                "first_ts": "",
                "last_ts": "",
            }
        )
        return row
    row["returncode"] = proc.returncode
    row["stdout"] = truncate(proc.stdout)
    row["stderr"] = truncate(proc.stderr)
    if proc.returncode != 0:
        row.update(
            {
                "status": "fetch_failed",
                "reason": f"returncode={proc.returncode}",
                "rows": 0,
                "first_ts": "",
                "last_ts": "",
            }
        )
        return row
    summary = csv_summary(raw_path)
    row.update(
        {
            "status": "ok" if summary["rows"] > 0 else "empty",
            "reason": "" if summary["rows"] > 0 else "fetch_succeeded_but_output_empty",
            **summary,
        }
    )
    return row


def manifest_ibkr_cells() -> list[dict[str, str]]:
    disposition = load_json(PUBLIC_CRYPTO_DISPOSITION)
    cells: list[dict[str, str]] = []
    for row in disposition["rows"]:
        if row.get("provider") == "ibkr" and row.get("cell_type") == "bar_root":
            cells.append({"symbol": row["symbol"], "timeframe": row["timeframe"]})
    return cells


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    RAW_ROOT.mkdir(parents=True, exist_ok=True)

    cells = manifest_ibkr_cells()
    attempted_cells = [
        cell
        for cell in cells
        if cell["symbol"] in ATTEMPT_SYMBOLS and cell["timeframe"] in ATTEMPT_TIMEFRAMES
    ]

    rows: list[dict[str, Any]] = []
    global_fetch_blocker = ""
    for index, cell in enumerate(attempted_cells):
        result = attempt_fetch(cell["symbol"], cell["timeframe"])
        rows.append(result)
        if index == 0 and result["status"] not in {"ok", "empty"}:
            global_fetch_blocker = f"{result['status']}:{result['reason']}:{result.get('stderr', '')[-300:]}"
            break

    attempted_keys = {(row["symbol"], row["timeframe"]) for row in rows}
    for cell in cells:
        key = (cell["symbol"], cell["timeframe"])
        if key in attempted_keys:
            continue
        if global_fetch_blocker:
            status = "not_attempted_after_operator_fetch_blocker"
            reason = global_fetch_blocker
        else:
            status = "ready_pending_bounded_loop_not_attempted"
            reason = "bounded Board A loop attempted two symbols x two timeframes first; no success extrapolated to remaining IBKR cells"
        rows.append(
            {
                "provider": "ibkr",
                "symbol": cell["symbol"],
                "timeframe": cell["timeframe"],
                "attempted": False,
                "status": status,
                "reason": reason,
                "rows": 0,
                "first_ts": "",
                "last_ts": "",
                "raw_csv": "",
                "raw_committed": False,
                "runtime_code_changed": False,
                "thresholds_relaxed": False,
                "trade_usable": False,
                "label_status": "missing_independent_root_labels",
                "accepted_for_confidence": False,
                "returncode": None,
                "stdout": "",
                "stderr": "",
            }
        )

    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    ok_count = status_counts.get("ok", 0)
    attempted_count = sum(1 for row in rows if row["attempted"])
    failed_count = sum(1 for row in rows if row["status"] in {"fetch_failed", "fetch_timeout"})

    if global_fetch_blocker:
        gate_result = "ibkr_ready_lane_blocked_by_operator_runtime_fetch"
        next_action = "Fix the concrete IBKR operator-runtime fetch blocker or use another independent source-label panel; do not treat IBKR ready status as fetched coverage."
    else:
        gate_result = "ibkr_ready_lane_bounded_probe_done_root_labels_missing"
        next_action = "Continue IBKR remaining cells only if source labels can attach; otherwise prioritize acquiring an independent MainRegimeV2 label panel."

    report = {
        "run_id": RUN_ID,
        "goal_achieved": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective": "Attempt the IBKR ready lane with a low-pollution uv wrapper and record exact Board A disposition.",
        "source_artifacts": {
            "public_crypto_disposition_refresh": rel(PUBLIC_CRYPTO_DISPOSITION),
        },
        "ibkr_manifest_cells": len(cells),
        "attempt_policy": {
            "symbols": sorted(ATTEMPT_SYMBOLS),
            "timeframes": sorted(ATTEMPT_TIMEFRAMES),
            "bounded_loop": True,
            "no_success_extrapolation": True,
        },
        "uv_wrapper": {
            "used": True,
            "packages": UV_PACKAGES,
            "persistent_system_install": False,
        },
        "raw_root": str(RAW_ROOT),
        "raw_ohlcv_committed": False,
        "attempted_count": attempted_count,
        "ok_count": ok_count,
        "failed_count": failed_count,
        "status_counts": status_counts,
        "rows": rows,
        "completion_accounting": {
            "accepted_full_cycle_full_universe": False,
            "accepted_confidence": False,
            "why_not_accepted": [
                "IBKR bar fetch results are provider/data coverage only, not independent MainRegimeV2 root labels.",
                "Every IBKR manifest cell still has label_status=missing_independent_root_labels.",
                "No proxy/OHLCV score is counted as accepted root confidence.",
                "Raw CSV output, if any, stays under /private/tmp and is not committed.",
            ],
        },
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "gate_result": gate_result,
        "next_action": next_action,
        "artifacts": {
            "summary_json": rel(OUT_DIR / "ibkr_ready_lane_operator_probe.json"),
            "summary_md": rel(OUT_DIR / "ibkr_ready_lane_operator_probe.md"),
            "summary_csv": rel(OUT_DIR / "ibkr_ready_lane_operator_probe.csv"),
            "assertions": rel(CHECK_DIR / "ibkr_ready_lane_operator_probe_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "ibkr_ready_lane_operator_probe.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    with (OUT_DIR / "ibkr_ready_lane_operator_probe.csv").open("w", newline="") as handle:
        fieldnames = [
            "provider",
            "symbol",
            "timeframe",
            "attempted",
            "status",
            "reason",
            "rows",
            "first_ts",
            "last_ts",
            "raw_csv",
            "raw_committed",
            "label_status",
            "accepted_for_confidence",
            "runtime_code_changed",
            "thresholds_relaxed",
            "trade_usable",
            "returncode",
            "stdout",
            "stderr",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    md_lines = [
        "# IBKR Ready Lane Operator Probe",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Goal achieved: `false`",
        "",
        f"- IBKR manifest cells: `{len(cells)}`",
        f"- Attempted cells: `{attempted_count}`",
        f"- OK cells: `{ok_count}`",
        f"- Failed/timeout cells: `{failed_count}`",
        f"- Raw OHLCV committed: `false`",
        "",
        "## Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in sorted(status_counts.items()):
        md_lines.append(f"| `{status}` | {count} |")
    md_lines.extend(
        [
            "",
            "## Accounting",
            "",
            "- IBKR bars are provider coverage only; every IBKR cell remains `missing_independent_root_labels`.",
            "- No threshold was relaxed and no runtime code changed.",
            f"- Gate result: `{gate_result}`",
            "",
            "## Next Action",
            "",
            next_action,
        ]
    )
    (OUT_DIR / "ibkr_ready_lane_operator_probe.md").write_text("\n".join(md_lines) + "\n")

    assertion_lines = [
        "goal_achieved=false",
        f"ibkr_manifest_cells={len(cells)}",
        f"attempted_count={attempted_count}",
        f"ok_count={ok_count}",
        f"failed_count={failed_count}",
        "accepted_full_cycle_full_universe=false",
        "raw_ohlcv_committed=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "trade_usable=false",
        f"gate_result={gate_result}",
    ]
    for status, count in sorted(status_counts.items()):
        assertion_lines.append(f"status.{status}={count}")
    (CHECK_DIR / "ibkr_ready_lane_operator_probe_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n"
    )
    print(rel(OUT_DIR / "ibkr_ready_lane_operator_probe.json"))


if __name__ == "__main__":
    main()
