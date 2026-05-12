#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T124600+0800-codex-targeted-calibration-overlap-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T124600-codex-targeted-calibration-overlap-v1"
OUT_DIR = RUN_ROOT / "calibration-overlap"
CHECK_DIR = RUN_ROOT / "checks"
CACHE_DIR = Path("/private/tmp/ict-regime-targeted-calibration-overlap-v1")

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
UNIFIED_PANEL = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T124000-codex-unified-source-label-panel-v1/unified-panel/unified_source_label_panel_v1.csv"
CURRENT_DATE = date(2026, 5, 11)

INTERVAL_BY_TIMEFRAME = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "1h",
    "1mo": "1mo",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def load_or_download(instrument: str, timeframe: str) -> pd.Series:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe = instrument.replace("^", "idx_").replace("=", "_")
    cache_path = CACHE_DIR / f"{safe}_{timeframe}.csv"
    if cache_path.exists():
        df = pd.read_csv(cache_path, parse_dates=["ts"])
        return pd.Series(df["close"].to_numpy(float), index=pd.DatetimeIndex(df["ts"]))

    interval = INTERVAL_BY_TIMEFRAME[timeframe]
    data = yf.download(
        instrument,
        period="max",
        interval=interval,
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    if data.empty:
        close = pd.Series(dtype=float)
    else:
        if isinstance(data.columns, pd.MultiIndex):
            close = data["Close"][instrument].dropna().astype(float)
        else:
            close = data["Close"].dropna().astype(float)
    if timeframe == "4h" and not close.empty:
        close = close.resample("4h").last().dropna()
    pd.DataFrame({"ts": close.index, "close": close.to_numpy(float)}).to_csv(cache_path, index=False)
    return close


def parse_day(value: str) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def month_key(d: date) -> tuple[int, int]:
    return d.year, d.month


def parse_month(value: str) -> tuple[int, int]:
    y, m = value.split("-")
    return int(y), int(m)


def count_overlap(row: dict[str, str], close: pd.Series) -> tuple[int, str, str]:
    if close.empty:
        return 0, "", ""
    dates = [ts.date() for ts in close.index]
    granularity = row["date_granularity"]
    if granularity == "month":
        start = parse_month(row["start_date"])
        end = parse_month(row["end_date"])
        selected = [d for d in dates if start <= month_key(d) <= end]
    else:
        start_day = parse_day(row["start_date"])
        end_day = parse_day(row["end_date"]) or CURRENT_DATE
        selected = [d for d in dates if start_day and start_day <= d <= end_day]
    if not selected:
        return 0, "", ""
    return len(selected), str(min(selected)), str(max(selected))


def write_rows(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_csv(UNIFIED_PANEL)
    crosswalk_rows = [r for r in rows if r["source_type"] == "source_window_crosswalk"]
    sideways_rows = [r for r in rows if r["source_type"] == "sideways_scoped_dated_window"]

    close_cache: dict[tuple[str, str], pd.Series] = {}
    overlap_rows: list[dict[str, str]] = []
    for row in crosswalk_rows:
        key = (row["instrument"], row["timeframe"])
        if key not in close_cache:
            close_cache[key] = load_or_download(*key)
        bars, first, last = count_overlap(row, close_cache[key])
        overlap_rows.append({
            "label_window_id": row["label_window_id"],
            "provider": row["provider"],
            "instrument": row["instrument"],
            "timeframe": row["timeframe"],
            "root": row["root"],
            "source_type": row["source_type"],
            "scope_tier": row["scope_tier"],
            "source_start_date": row["start_date"],
            "source_end_date": row["end_date"],
            "bar_overlap_count": str(bars),
            "overlap_first_date": first,
            "overlap_last_date": last,
            "overlap_status": "overlap_ready" if bars > 0 else "no_bar_overlap",
        })

    for row in sideways_rows:
        overlap_rows.append({
            "label_window_id": row["label_window_id"],
            "provider": row["provider"],
            "instrument": row["instrument"],
            "timeframe": row["timeframe"],
            "root": row["root"],
            "source_type": row["source_type"],
            "scope_tier": row["scope_tier"],
            "source_start_date": row["start_date"],
            "source_end_date": row["end_date"],
            "bar_overlap_count": row["notes"].split("row_count=", 1)[1].split(";", 1)[0],
            "overlap_first_date": row["start_date"],
            "overlap_last_date": row["end_date"],
            "overlap_status": "overlap_ready_existing_sideways_gate",
        })

    fields = [
        "label_window_id",
        "provider",
        "instrument",
        "timeframe",
        "root",
        "source_type",
        "scope_tier",
        "source_start_date",
        "source_end_date",
        "bar_overlap_count",
        "overlap_first_date",
        "overlap_last_date",
        "overlap_status",
    ]
    overlap_csv = OUT_DIR / "targeted_calibration_overlap_v1.csv"
    write_rows(overlap_csv, overlap_rows, fields)

    overlap_ready = [r for r in overlap_rows if int(r["bar_overlap_count"]) > 0]
    no_overlap = [r for r in overlap_rows if int(r["bar_overlap_count"]) == 0]
    by_root_ready = Counter(r["root"] for r in overlap_ready)
    by_root_no = Counter(r["root"] for r in no_overlap)
    bars_by_root = defaultdict(int)
    for row in overlap_ready:
        bars_by_root[row["root"]] += int(row["bar_overlap_count"])

    downloaded = []
    for (instrument, timeframe), series in sorted(close_cache.items()):
        downloaded.append({
            "instrument": instrument,
            "timeframe": timeframe,
            "bars": int(len(series)),
            "first_ts": str(series.index.min()) if len(series) else "",
            "last_ts": str(series.index.max()) if len(series) else "",
        })

    package = {
        "run_id": RUN_ID,
        "artifact_type": "targeted_calibration_overlap_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "board": str(BOARD.relative_to(REPO)),
            "board_sha256_at_run": sha256(BOARD),
            "unified_panel": str(UNIFIED_PANEL.relative_to(REPO)),
            "unified_panel_sha256": sha256(UNIFIED_PANEL),
        },
        "provider_fetch": {
            "cache_dir": str(CACHE_DIR),
            "downloaded_or_cached_series": downloaded,
            "raw_data_committed": False,
        },
        "overlap": {
            "csv": str(overlap_csv.relative_to(REPO)),
            "total_label_windows_checked": len(overlap_rows),
            "overlap_ready_windows": len(overlap_ready),
            "no_bar_overlap_windows": len(no_overlap),
            "overlap_ready_by_root": dict(sorted(by_root_ready.items())),
            "no_bar_overlap_by_root": dict(sorted(by_root_no.items())),
            "bar_overlap_by_root": dict(sorted(bars_by_root.items())),
        },
        "decision": {
            "calibration_preflight": "overlap_ready",
            "confidence_gate_claimed": False,
            "full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "next_action": "Run held-out calibration only on overlap-ready windows; abstain no-overlap windows instead of counting them as failures.",
        },
        "guardrails": {
            "targeted_approved_instruments_only": True,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "proxy_promoted_beyond_declared_crosswalk": False,
            "shared_board_modified": False,
        },
    }

    json_path = OUT_DIR / "targeted_calibration_overlap_v1.json"
    json_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")

    md = [
        "# Targeted Calibration Overlap v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Label windows checked: `{len(overlap_rows)}`.",
        f"- Overlap-ready windows: `{len(overlap_ready)}`.",
        f"- No-overlap windows abstained: `{len(no_overlap)}`.",
        f"- Overlap-ready by root: `{dict(sorted(by_root_ready.items()))}`.",
        f"- Bar overlap by root: `{dict(sorted(bars_by_root.items()))}`.",
        "- Full objective gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.",
        "",
        "## Policy",
        "",
        "This run is a targeted calibration preflight. It does not count no-overlap cells as model failures and it does not claim 95% confidence. It narrows the next calibration to windows where source labels and bars actually overlap.",
        "",
        "## Guardrails",
        "",
        "- Only approved S&P 500 crosswalk instruments/timeframes were fetched.",
        "- Raw provider data stayed under `/private/tmp`.",
        "- No runtime code changed; no thresholds relaxed; no trade usability claimed.",
        "",
        "## Artifacts",
        "",
        "- `targeted_calibration_overlap_v1.json`",
        "- `targeted_calibration_overlap_v1.csv`",
        "- `../checks/targeted_calibration_overlap_v1_assertions.out`",
        "",
    ]
    (OUT_DIR / "targeted_calibration_overlap_v1.md").write_text("\n".join(md))

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={package['inputs']['board_sha256_at_run']}",
        f"total_label_windows_checked={len(overlap_rows)}",
        f"overlap_ready_windows={len(overlap_ready)}",
        f"no_bar_overlap_windows={len(no_overlap)}",
        f"overlap_ready_by_root={dict(sorted(by_root_ready.items()))}",
        f"bar_overlap_by_root={dict(sorted(bars_by_root.items()))}",
        "confidence_gate_claimed=false",
        "full_objective_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    (CHECK_DIR / "targeted_calibration_overlap_v1_assertions.out").write_text("\n".join(assertions) + "\n")

    assert len(overlap_rows) == 839
    assert len(overlap_ready) > 0
    assert bars_by_root["Sideways"] >= 4049
    assert package["decision"]["confidence_gate_claimed"] is False


if __name__ == "__main__":
    main()
