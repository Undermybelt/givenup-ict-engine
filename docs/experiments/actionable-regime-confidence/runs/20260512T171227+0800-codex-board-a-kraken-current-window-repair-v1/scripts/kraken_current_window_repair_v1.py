from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path
from typing import Any


RUN_ID = "20260512T171227+0800-codex-board-a-kraken-current-window-repair-v1"
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
CSV_DIR = ROOT / "provider-csv"
SUMMARY_DIR = ROOT / "summaries"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def run(label: str, cmd: list[str], *, timeout: int = 900) -> int:
    write(OUT_DIR / f"{label}.cmd", " ".join(cmd) + "\n")
    proc = subprocess.run(
        cmd,
        cwd=Path.cwd(),
        env=os.environ.copy(),
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
        return {"rows": 0, "first": None, "last": None, "columns": []}
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        columns = reader.fieldnames or []
        time_key = next(
            (key for key in ("timestamp", "date", "datetime", "open_time", "time") if key in columns),
            columns[0] if columns else None,
        )
        rows = 0
        first = None
        last = None
        for row in reader:
            rows += 1
            value = row.get(time_key, "") if time_key else ""
            if rows == 1:
                first = value
            last = value
    return {"rows": rows, "first": first, "last": last, "columns": columns}


def current_ready(profile: dict[str, Any], exit_code: int) -> bool:
    last = str(profile.get("last") or "")
    return exit_code == 0 and int(profile.get("rows") or 0) > 0 and last >= "2026-05-01"


def main() -> int:
    for path in (OUT_DIR, CHECK_DIR, CSV_DIR, SUMMARY_DIR):
        path.mkdir(parents=True, exist_ok=True)
    write(ROOT / "run_id.txt", RUN_ID + "\n")

    attempts: list[tuple[str, str, str, str, Path, list[str]]] = [
        (
            "01_kraken_futures_pfxbtusd_1h_recent_20260301_20260512",
            "futures",
            "PF_XBTUSD",
            "2026-03-01_to_2026-05-12",
            CSV_DIR / "kraken_futures_pfxbtusd_1h_20260301_20260512.csv",
            [
                "uv",
                "run",
                "--with",
                "pandas",
                "scripts/auto_quant_external/fetch_external.py",
                "kraken-kline",
                "--market",
                "futures",
                "--pair",
                "PF_XBTUSD",
                "--interval",
                "1h",
                "--start",
                "2026-03-01",
                "--end",
                "2026-05-12",
            ],
        ),
        (
            "02_kraken_futures_pfxbtusd_1h_1y_20250512_20260512",
            "futures",
            "PF_XBTUSD",
            "2025-05-12_to_2026-05-12",
            CSV_DIR / "kraken_futures_pfxbtusd_1h_20250512_20260512.csv",
            [
                "uv",
                "run",
                "--with",
                "pandas",
                "scripts/auto_quant_external/fetch_external.py",
                "kraken-kline",
                "--market",
                "futures",
                "--pair",
                "PF_XBTUSD",
                "--interval",
                "1h",
                "--start",
                "2025-05-12",
                "--end",
                "2026-05-12",
            ],
        ),
        (
            "03_kraken_spot_xbtusd_1h_default",
            "spot",
            "XBTUSD",
            "spot_default_last_ohlc_window",
            CSV_DIR / "kraken_spot_xbtusd_1h_default.csv",
            [
                "uv",
                "run",
                "--with",
                "pandas",
                "scripts/auto_quant_external/fetch_external.py",
                "kraken-kline",
                "--market",
                "spot",
                "--pair",
                "XBTUSD",
                "--interval",
                "1h",
            ],
        ),
    ]

    rows: list[dict[str, Any]] = []
    for label, market, pair, requested_span, output_path, cmd_prefix in attempts:
        cmd = [*cmd_prefix, "--output", str(output_path)]
        exit_code = run(label, cmd)
        profile = csv_profile(output_path)
        rows.append(
            {
                "provider": "Kraken",
                "label": label,
                "market": market,
                "pair": pair,
                "requested_history_span": requested_span,
                "returned_first": profile["first"],
                "returned_last": profile["last"],
                "timeframe": "1h",
                "kline_rows": profile["rows"],
                "exit": exit_code,
                "current_window_ready": current_ready(profile, exit_code),
                "portable_to_consumer": True,
                "local_file_runtime_dependency": False,
            }
        )

    payload = {
        "run_id": RUN_ID,
        "source_gap": "165415_kraken_broad_request_returned_stale_2022_slice",
        "attempts": rows,
        "current_window_ready_any": any(row["current_window_ready"] for row in rows),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write(SUMMARY_DIR / "kraken_current_window_repair_v1.json", json.dumps(payload, indent=2, sort_keys=True) + "\n")
    matrix = SUMMARY_DIR / "kraken_current_window_repair_v1.csv"
    with matrix.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    if any(row["current_window_ready"] for row in rows):
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
