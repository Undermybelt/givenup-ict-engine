from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260512T165415+0800-codex-board-a-provider-max-window-capability-probe-v1")
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
CSV_DIR = ROOT / "provider-csv"
SUMMARY_DIR = ROOT / "summaries"
CONFIG_DIR = ROOT / "config"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def run(label: str, cmd: list[str], *, env: dict[str, str] | None = None, timeout: int = 900) -> int:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    write(OUT_DIR / f"{label}.cmd", " ".join(cmd) + "\n")
    proc = subprocess.run(
        cmd,
        cwd=Path.cwd(),
        env=merged,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    write(OUT_DIR / f"{label}.stdout", proc.stdout)
    write(OUT_DIR / f"{label}.stderr", proc.stderr)
    write(CHECK_DIR / f"{label}.exit", f"{proc.returncode}\n")
    return proc.returncode


def csv_profile(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"rows": 0, "first": None, "last": None}
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames or []
        time_key = next((k for k in ("timestamp", "date", "datetime", "open_time", "time") if k in fields), fields[0] if fields else None)
        rows = 0
        first = None
        last = None
        for row in reader:
            rows += 1
            value = row.get(time_key, "") if time_key else ""
            if rows == 1:
                first = value
            last = value
    return {"rows": rows, "first": first, "last": last}


def write_ibkr_config() -> Path:
    config = CONFIG_DIR / "ibkr_btc_paxos_aggtrades_1y_client77.yaml"
    write(
        config,
        "\n".join(
            [
                "gateway:",
                "  host: 127.0.0.1",
                "  port: 4002",
                "  client_id: 77",
                "output:",
                f"  directory: {CSV_DIR}",
                "  filename_template: '{symbol}_{bar_suffix}_{what}_client77.csv'",
                "  force: true",
                "defaults:",
                "  bar_size: '1 hour'",
                "  duration: '1 Y'",
                "  what_to_show: AGGTRADES",
                "  rth: false",
                "  exchange: PAXOS",
                "  currency: USD",
                "symbols:",
                "  - symbol: BTC",
                "    sec_type: CRYPTO",
                "    exchange: PAXOS",
                "    currency: USD",
                "    what_to_show: AGGTRADES",
                "    rth: false",
                "    bar_sizes: ['1 hour']",
                "    duration: '1 Y'",
                "",
            ]
        ),
    )
    return config


def main() -> int:
    rows: list[dict[str, Any]] = []

    yf_csv = CSV_DIR / "yfinance_btc_usd_1h_20240513_20260512.csv"
    yf_label = "01b_yfinance_btc_usd_1h_730d_fallback"
    yf_exit = run(
        yf_label,
        [
            "uv",
            "run",
            "--with",
            "yfinance",
            "--with",
            "pandas",
            "scripts/auto_quant_external/fetch_external.py",
            "yahoo",
            "--symbol",
            "BTC-USD",
            "--interval",
            "1h",
            "--start",
            "2024-05-13",
            "--end",
            "2026-05-12",
            "--output",
            str(yf_csv),
        ],
        timeout=1200,
    )
    yf_profile = csv_profile(yf_csv)
    rows.append(
        {
            "provider": "yfinance/YF",
            "label": yf_label,
            "requested_history_span": "2024-05-13_to_2026-05-12_730d_1h_cap_fallback",
            "returned_first": yf_profile["first"],
            "returned_last": yf_profile["last"],
            "timeframe": "1h",
            "kline_rows": yf_profile["rows"],
            "exit": yf_exit,
            "status": "current_row_ready" if yf_exit == 0 and yf_profile["rows"] > 0 else "fail_closed",
        }
    )

    ibkr_label = "06b_ibkr_btc_paxos_aggtrades_1y_client77"
    ibkr_config = write_ibkr_config()
    ibkr_exit = run(
        ibkr_label,
        [
            "/Users/thrill3r/Auto-Quant/.venv/bin/python",
            "scripts/auto_quant_external/fetch_external.py",
            "ibkr-bulk",
            "--config",
            str(ibkr_config),
            "--force",
        ],
        env={"PYTHONPATH": f"{Path.cwd() / 'scripts'}:{Path.cwd()}"},
        timeout=1200,
    )
    alternatives = sorted(CSV_DIR.glob("BTC_*AGGTRADES_client77.csv"))
    ibkr_csv = alternatives[0] if alternatives else CSV_DIR / "BTC_1h_AGGTRADES_client77.csv"
    ibkr_profile = csv_profile(ibkr_csv)
    rows.append(
        {
            "provider": "IBKR",
            "label": ibkr_label,
            "requested_history_span": "1Y_duration_via_ibkr_bulk_client77",
            "returned_first": ibkr_profile["first"],
            "returned_last": ibkr_profile["last"],
            "timeframe": "1h",
            "kline_rows": ibkr_profile["rows"],
            "exit": ibkr_exit,
            "status": "current_row_ready" if ibkr_exit == 0 and ibkr_profile["rows"] > 0 else "fail_closed",
        }
    )

    payload = {
        "fallback_rows": rows,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write(SUMMARY_DIR / "provider_max_window_fallbacks_v1.json", json.dumps(payload, indent=2, sort_keys=True) + "\n")
    matrix = SUMMARY_DIR / "provider_max_window_fallbacks_v1.csv"
    with matrix.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
