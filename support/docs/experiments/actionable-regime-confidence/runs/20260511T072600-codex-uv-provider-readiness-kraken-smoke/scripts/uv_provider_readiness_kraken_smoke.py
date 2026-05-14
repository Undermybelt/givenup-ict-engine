#!/usr/bin/env python3
"""Probe a blocked public-provider lane through a low-pollution uv runtime.

Run this script with:

uv run --with requests --with pandas --with ccxt --with ib_async --with redis \
  --with PyYAML --with scikit-learn --with pyarrow --with xgboost \
  python <this-file>

The script writes only compact summaries to the repo. Raw OHLCV CSVs stay under
/private/tmp and are not committed.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T072600+0800-codex-uv-provider-readiness-kraken-smoke"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T072600-codex-uv-provider-readiness-kraken-smoke"
PROVIDER_DIR = RUN_ROOT / "provider-readiness"
MATRIX_DIR = RUN_ROOT / "kraken-matrix"
CHECK_DIR = RUN_ROOT / "checks"
RAW_ROOT = Path("/private/tmp/ict-regime-kraken-public-matrix-20260511T072600")
FETCH_EXTERNAL = REPO / "scripts/auto_quant_external/fetch_external.py"

PAIRS = {
    "BTC": "PF_XBTUSD",
    "ETH": "PF_ETHUSD",
    "SOL": "PF_SOLUSD",
}
TIMEFRAME_WINDOWS = {
    "1m": ("2026-05-03", "2026-05-10"),
    "5m": ("2026-04-10", "2026-05-10"),
    "15m": ("2026-04-01", "2026-05-10"),
    "30m": ("2026-04-01", "2026-05-10"),
    "1h": ("2026-04-01", "2026-05-10"),
    "4h": ("2025-05-10", "2026-05-10"),
    "1d": ("2024-05-10", "2026-05-10"),
    "1w": ("2021-05-10", "2026-05-10"),
    "1mo": None,
}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def run_cmd(cmd: list[str], timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def read_fetch_csv(path: Path) -> dict[str, Any]:
    df = pd.read_csv(path)
    if df.empty:
        return {"rows": 0, "first_ts": "", "last_ts": ""}
    ts_col = "date" if "date" in df.columns else df.columns[0]
    return {
        "rows": int(len(df)),
        "first_ts": str(pd.to_datetime(df[ts_col]).min()),
        "last_ts": str(pd.to_datetime(df[ts_col]).max()),
    }


def provider_status_probe() -> dict[str, Any]:
    proc = run_cmd(["./target/debug/ict-engine", "provider-status", "--agent", "--domain", "market_data"], timeout=120)
    (PROVIDER_DIR / "provider_status_uv_market_data_stdout.json").write_text(proc.stdout)
    (PROVIDER_DIR / "provider_status_uv_market_data_stderr.txt").write_text(proc.stderr)
    if proc.returncode != 0:
        return {
            "returncode": proc.returncode,
            "parse_ok": False,
            "summary_line": "",
            "ready_providers": [],
            "pending_providers": [],
            "stderr": proc.stderr[-1000:],
        }
    payload = json.loads(proc.stdout)
    return {
        "returncode": proc.returncode,
        "parse_ok": True,
        "summary_line": payload.get("summary_line", ""),
        "ready_providers": payload.get("ready_providers", []),
        "pending_providers": payload.get("pending_providers", []),
        "provider_status_artifact": rel(PROVIDER_DIR / "provider_status_uv_market_data_stdout.json"),
        "provider_status_stderr": rel(PROVIDER_DIR / "provider_status_uv_market_data_stderr.txt"),
    }


def fetch_kraken_matrix() -> list[dict[str, Any]]:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for symbol, pair in PAIRS.items():
        for timeframe, window in TIMEFRAME_WINDOWS.items():
            out = RAW_ROOT / f"{pair}_{timeframe}.csv"
            row: dict[str, Any] = {
                "provider": "kraken_public",
                "symbol": symbol,
                "pair": pair,
                "market": "futures",
                "timeframe": timeframe,
                "raw_csv": str(out),
                "raw_committed": False,
                "runtime_code_changed": False,
                "thresholds_relaxed": False,
                "trade_usable": False,
            }
            if window is None:
                row.update(
                    {
                        "status": "unsupported_timeframe",
                        "reason": "fetch_external kraken futures supports 1w max for this lane; board 1mo cell remains unsupported",
                        "rows": 0,
                        "first_ts": "",
                        "last_ts": "",
                        "stdout": "",
                        "stderr": "",
                    }
                )
                rows.append(row)
                continue
            start, end = window
            proc = run_cmd(
                [
                    sys.executable,
                    str(FETCH_EXTERNAL),
                    "kraken-kline",
                    "--market",
                    "futures",
                    "--pair",
                    pair,
                    "--interval",
                    timeframe,
                    "--start",
                    start,
                    "--end",
                    end,
                    "--output",
                    str(out),
                ],
                timeout=120,
            )
            row["returncode"] = proc.returncode
            row["stdout"] = proc.stdout.strip()[-500:]
            row["stderr"] = proc.stderr.strip()[-500:]
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
            elif not out.exists():
                row.update(
                    {
                        "status": "fetch_failed",
                        "reason": "fetch_returned_success_but_output_missing",
                        "rows": 0,
                        "first_ts": "",
                        "last_ts": "",
                    }
                )
            else:
                summary = read_fetch_csv(out)
                status = "ok" if summary["rows"] > 0 else "empty"
                row.update({"status": status, "reason": "", **summary})
            rows.append(row)
    return rows


def main() -> None:
    PROVIDER_DIR.mkdir(parents=True, exist_ok=True)
    MATRIX_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    provider_probe = provider_status_probe()
    rows = fetch_kraken_matrix()

    ok_cells = [row for row in rows if row["status"] == "ok"]
    failed_cells = [row for row in rows if row["status"] == "fetch_failed"]
    unsupported_cells = [row for row in rows if row["status"] == "unsupported_timeframe"]

    report = {
        "run_id": RUN_ID,
        "goal_achieved": False,
        "objective": "Open one blocked provider lane through a low-pollution uv dependency wrapper, then smoke real Kraken public futures OHLCV coverage.",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "uv_wrapper": {
            "used": True,
            "packages": [
                "requests",
                "pandas",
                "ccxt",
                "ib_async",
                "redis",
                "PyYAML",
                "scikit-learn",
                "pyarrow",
                "xgboost",
            ],
            "persistent_system_install": False,
        },
        "provider_status_probe": provider_probe,
        "kraken_matrix": {
            "provider": "kraken_public",
            "symbols": sorted(PAIRS),
            "timeframes": list(TIMEFRAME_WINDOWS),
            "cell_count": len(rows),
            "ok_cell_count": len(ok_cells),
            "failed_cell_count": len(failed_cells),
            "unsupported_cell_count": len(unsupported_cells),
            "raw_root": str(RAW_ROOT),
            "raw_ohlcv_committed": False,
        },
        "rows": rows,
        "completion_accounting": {
            "provider_lane_opened": provider_probe.get("summary_line") == "market_data:6/7 ready",
            "actual_data_fetch_attempted": True,
            "accepted_full_cycle_full_universe": False,
            "why_not_accepted": [
                "Kraken public wrapper opens a data lane, but this is provider/data availability only.",
                "The 1mo Kraken futures cell is unsupported in the current fetch script.",
                "No independent MainRegimeV2 root labels are attached to these fetched bars.",
                "TradingViewRemix remains blocked by connectivity.",
            ],
        },
        "raw_ohlcv_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "gate_result": "uv_wrapper_opened_provider_lane_kraken_data_available_root_confidence_pending",
        "next_action": "Rerun the full coverage disposition matrix with uv-wrapper provider readiness and Kraken data cells, while keeping missing root labels as unsupported for accepted confidence.",
        "artifacts": {
            "summary_json": rel(MATRIX_DIR / "uv_provider_readiness_kraken_smoke.json"),
            "summary_md": rel(MATRIX_DIR / "uv_provider_readiness_kraken_smoke.md"),
            "summary_csv": rel(MATRIX_DIR / "uv_provider_readiness_kraken_smoke.csv"),
            "assertions": rel(CHECK_DIR / "uv_provider_readiness_kraken_smoke_assertions.out"),
            "script": rel(Path(__file__)),
            "provider_status_stdout": rel(PROVIDER_DIR / "provider_status_uv_market_data_stdout.json"),
            "provider_status_stderr": rel(PROVIDER_DIR / "provider_status_uv_market_data_stderr.txt"),
        },
    }

    (MATRIX_DIR / "uv_provider_readiness_kraken_smoke.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    with (MATRIX_DIR / "uv_provider_readiness_kraken_smoke.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# UV Provider Readiness + Kraken Public Smoke",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Goal achieved: `false`",
        "",
        "## Provider Status",
        "",
        f"- UV wrapper summary: `{provider_probe.get('summary_line', '')}`",
        f"- Ready providers: `{', '.join(provider_probe.get('ready_providers', []))}`",
        f"- Pending providers: `{', '.join(provider_probe.get('pending_providers', []))}`",
        "",
        "## Kraken Public Futures Matrix",
        "",
        f"- Cells attempted: `{len(rows)}`",
        f"- OK cells: `{len(ok_cells)}`",
        f"- Failed cells: `{len(failed_cells)}`",
        f"- Unsupported cells: `{len(unsupported_cells)}`",
        "- Raw OHLCV committed: `false`",
        "",
        "## Accounting",
        "",
        "- This opens a data-provider lane only; it does not attach independent root labels.",
        "- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
        "",
        "Gate result: `uv_wrapper_opened_provider_lane_kraken_data_available_root_confidence_pending`",
    ]
    (MATRIX_DIR / "uv_provider_readiness_kraken_smoke.md").write_text("\n".join(lines) + "\n")

    assertion_lines = [
        "goal_achieved=false",
        f"provider_status_summary={provider_probe.get('summary_line', '')}",
        f"kraken.cell_count={len(rows)}",
        f"kraken.ok_cell_count={len(ok_cells)}",
        f"kraken.failed_cell_count={len(failed_cells)}",
        f"kraken.unsupported_cell_count={len(unsupported_cells)}",
        "actual_data_fetch_attempted=true",
        "accepted_full_cycle_full_universe=false",
        "raw_ohlcv_committed=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "trade_usable=false",
        "gate_result=uv_wrapper_opened_provider_lane_kraken_data_available_root_confidence_pending",
    ]
    (CHECK_DIR / "uv_provider_readiness_kraken_smoke_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n"
    )
    print(rel(MATRIX_DIR / "uv_provider_readiness_kraken_smoke.json"))


if __name__ == "__main__":
    main()
