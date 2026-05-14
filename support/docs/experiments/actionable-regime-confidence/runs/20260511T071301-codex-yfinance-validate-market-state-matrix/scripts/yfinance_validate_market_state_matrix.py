#!/usr/bin/env python3
"""Run repo-native validate-market-state over the yfinance full matrix."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
BIN = REPO / "target/debug/ict-engine"
RUN_ID = "20260511T071301+0800-codex-yfinance-validate-market-state-matrix"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T071301-codex-yfinance-validate-market-state-matrix"
OUT_DIR = RUN_ROOT / "validator-matrix"
CHECK_DIR = RUN_ROOT / "checks"
TMP_ROOT = Path("/tmp/ict-yfinance-validate-market-state-matrix-20260511T071301")
MANIFEST = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T070440-codex-provider-universe-manifest-readback/provider-universe-manifest/provider_universe_manifest_readback.json"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

PERIOD_BY_INTERVAL = {
    "1m": "5d",
    "5m": "60d",
    "15m": "60d",
    "30m": "60d",
    "1h": "730d",
    "4h": "730d",
    "1d": "5y",
    "1w": "10y",
    "1mo": "max",
}
YF_INTERVAL = {"1w": "1wk"}
SUMMARY_RE = re.compile(
    r"samples=(?P<samples>\d+) avg_confidence=(?P<avg>[0-9.]+)% "
    r"high_confidence=(?P<high>[0-9.]+)% tradeable=(?P<tradeable>[0-9.]+)% "
    r"primary_top=(?P<primary>[^ ]+) secondary_top=(?P<secondary>.+)$"
)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.=-]+", "_", value)


def download_csv(symbol: str, interval: str) -> tuple[Path | None, int, str | None]:
    yf_interval = YF_INTERVAL.get(interval, interval)
    period = PERIOD_BY_INTERVAL[interval]
    try:
        frame = yf.download(symbol, period=period, interval=yf_interval, progress=False, auto_adjust=False, threads=False)
    except Exception as exc:  # noqa: BLE001
        return None, 0, f"download_error:{type(exc).__name__}:{str(exc)[:300]}"
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = [str(col[0]) for col in frame.columns]
    if frame.empty:
        return None, 0, "download_empty"
    frame = frame.rename_axis("timestamp").reset_index()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"]).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    frame.columns = [str(col).lower().replace(" ", "_") for col in frame.columns]
    keep = [col for col in ["timestamp", "open", "high", "low", "close", "volume"] if col in frame.columns]
    frame = frame[keep].dropna(subset=["open", "high", "low", "close"])
    if len(frame) < 120:
        return None, int(len(frame)), "rows_below_120"
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = TMP_ROOT / f"{safe_name(symbol)}_{safe_name(interval)}.csv"
    frame.to_csv(path, index=False)
    return path, int(len(frame)), None


def parse_summary(stdout: str) -> dict[str, Any]:
    text = stdout.strip().splitlines()[-1] if stdout.strip() else ""
    match = SUMMARY_RE.search(text)
    if not match:
        return {"parse_ok": False, "raw": stdout.strip()[:500]}
    return {
        "parse_ok": True,
        "samples": int(match.group("samples")),
        "avg_confidence_pct": float(match.group("avg")),
        "high_confidence_pct": float(match.group("high")),
        "tradeable_pct": float(match.group("tradeable")),
        "primary_top": match.group("primary"),
        "secondary_top": match.group("secondary"),
    }


def validate_cell(symbol: str, interval: str) -> dict[str, Any]:
    csv_path, rows, fetch_error = download_csv(symbol, interval)
    cell: dict[str, Any] = {
        "symbol": symbol,
        "interval": interval,
        "yf_interval": YF_INTERVAL.get(interval, interval),
        "period": PERIOD_BY_INTERVAL[interval],
        "rows": rows,
        "tmp_csv": str(csv_path) if csv_path else None,
    }
    if fetch_error:
        cell.update({"status": "fetch_blocked", "error": fetch_error})
        return cell
    assert csv_path is not None
    step_size = max(1, rows // 30)
    cmd = [
        str(BIN),
        "validate-market-state",
        "--data",
        str(csv_path),
        "--window-size",
        "100",
        "--step-size",
        str(step_size),
        "--compact",
        "--profile",
        "high_confidence",
    ]
    proc = subprocess.run(cmd, cwd=str(REPO), text=True, capture_output=True, check=False)
    cell.update(
        {
            "status": "ok" if proc.returncode == 0 else "validator_error",
            "returncode": proc.returncode,
            "step_size": step_size,
            "stdout": proc.stdout.strip()[:1000],
            "stderr": proc.stderr.strip()[:1000],
        }
    )
    if proc.returncode == 0:
        cell.update(parse_summary(proc.stdout))
    return cell


def main() -> None:
    manifest = load_json(MANIFEST)
    inputs = manifest["yfinance_first_matrix_inputs"]
    symbols = inputs["symbols"]
    intervals = inputs["timeframe_ladder"]
    cells = [validate_cell(symbol, interval) for symbol in symbols for interval in intervals]
    ok_cells = [cell for cell in cells if cell["status"] == "ok" and cell.get("parse_ok")]
    blocked_cells = [cell for cell in cells if cell not in ok_cells]
    high_conf_95_cells = [cell for cell in ok_cells if cell.get("high_confidence_pct", 0.0) >= 95.0]
    avg_conf_95_cells = [cell for cell in ok_cells if cell.get("avg_confidence_pct", 0.0) >= 95.0]
    report = {
        "run_id": RUN_ID,
        "objective": str(BOARD) + " yfinance full-matrix repo-native validator smoke",
        "source_manifest": rel(MANIFEST),
        "tmp_root": str(TMP_ROOT),
        "raw_ohlcv_committed": False,
        "symbols": symbols,
        "intervals": intervals,
        "cells": cells,
        "summary": {
            "total_cells": len(cells),
            "ok_cells": len(ok_cells),
            "blocked_cells": len(blocked_cells),
            "high_confidence_pct_ge_95_cells": len(high_conf_95_cells),
            "avg_confidence_pct_ge_95_cells": len(avg_conf_95_cells),
        },
        "goal_achieved": False,
        "why_not_complete": [
            "validate-market-state returns market-state/sub-regime confidence summaries, not MainRegimeV2 root calibration acceptance.",
            "No active root reached a full-matrix accepted 95% calibration gate in this smoke.",
            "Non-yfinance provider cells and direct Manipulation varieties remain pending or blocked.",
        ],
        "next_action": "Turn this yfinance validator matrix into a MainRegimeV2 root-labeled calibration table and evaluate Bull/Bear/Sideways/Crisis gates without relaxing thresholds.",
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "yfinance_validate_market_state_matrix.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    lines = [
        "# YFinance Validate-Market-State Matrix",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Goal achieved: `{str(report['goal_achieved']).lower()}`",
        f"Raw OHLCV committed: `{str(report['raw_ohlcv_committed']).lower()}`",
        "",
        "## Summary",
        "",
        f"- Total cells: `{len(cells)}`",
        f"- OK cells: `{len(ok_cells)}`",
        f"- Blocked cells: `{len(blocked_cells)}`",
        f"- Cells with high-confidence window share >=95%: `{len(high_conf_95_cells)}`",
        f"- Cells with average confidence >=95%: `{len(avg_conf_95_cells)}`",
        "",
        "## Interval Coverage",
        "",
        "| Interval | OK | Blocked | Avg Confidence Median |",
        "|---|---:|---:|---:|",
    ]
    for interval in intervals:
        rows = [cell for cell in cells if cell["interval"] == interval]
        oks = [cell for cell in rows if cell in ok_cells]
        med = pd.Series([cell.get("avg_confidence_pct", 0.0) for cell in oks]).median() if oks else 0.0
        lines.append(f"| `{interval}` | {len(oks)} | {len(rows) - len(oks)} | {med:.2f}% |")
    lines.extend([
        "",
        "Result: validator matrix is a live data/readback smoke only; MainRegimeV2 root calibration remains pending.",
        "",
    ])
    (OUT_DIR / "yfinance_validate_market_state_matrix.md").write_text("\n".join(lines))

    assertion_lines = [
        "goal_achieved=false",
        f"total_cells={len(cells)}",
        f"ok_cells={len(ok_cells)}",
        f"blocked_cells={len(blocked_cells)}",
        f"avg_confidence_pct_ge_95_cells={len(avg_conf_95_cells)}",
        f"high_confidence_pct_ge_95_cells={len(high_conf_95_cells)}",
        "mainregimev2_root_calibration_executed=false",
        "raw_ohlcv_committed=false",
        "thresholds_relaxed=false",
        "runtime_code_changed=false",
        "trade_usable=false",
    ]
    (CHECK_DIR / "yfinance_validate_market_state_matrix_assertions.out").write_text("\n".join(assertion_lines) + "\n")
    print(json.dumps({"goal_achieved": False, "summary": report["summary"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
