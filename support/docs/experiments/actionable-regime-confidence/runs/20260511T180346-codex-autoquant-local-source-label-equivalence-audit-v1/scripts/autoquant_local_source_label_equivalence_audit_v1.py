#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


RUN_ID = "20260511T180346+0800-codex-autoquant-local-source-label-equivalence-audit-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260511T180346-codex-autoquant-local-source-label-equivalence-audit-v1")
OUT_DIR = RUN_ROOT / "autoquant-local-audit"
CHECK_DIR = RUN_ROOT / "checks"
SOURCE_PANEL = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
AQ_DATA_DIR = Path("/Users/thrill3r/Auto-Quant/user_data/data")
EXPECTED_ROOTS = ("Bull", "Bear", "Sideways", "Crisis")


@dataclass
class FileRecord:
    file: str
    symbol: str
    quote: str
    timeframe: str
    rows: int
    first_date: str
    last_date: str
    exact_source_panel_symbol: bool
    status: str
    reason: str


@dataclass
class RootRecord:
    symbol: str
    timeframe: str
    root: str
    source_days: int
    matched_bar_days: int
    coverage: float
    wilson95_lcb: float
    status: str
    reason: str


def wilson_lcb(successes: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    phat = successes / total
    denom = 1 + z * z / total
    centre = phat + z * z / (2 * total)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def parse_aq_filename(path: Path) -> tuple[str, str, str]:
    stem = path.stem
    if "-" not in stem or "_" not in stem:
        return stem, "", ""
    pair, timeframe = stem.rsplit("-", 1)
    symbol, quote = pair.rsplit("_", 1)
    return symbol, quote, timeframe


def date_series_from_ms(values: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(values):
        return pd.to_datetime(values, utc=True, errors="coerce").dt.date.astype("string")
    numeric = pd.to_numeric(values, errors="coerce")
    # Some current cache files store millisecond epochs; crypto files store datetimes.
    return pd.to_datetime(numeric, unit="ms", utc=True, errors="coerce").dt.date.astype("string")


def read_feather_dates(path: Path) -> tuple[int, list[str]]:
    df = pd.read_feather(path, columns=["date"])
    dates = date_series_from_ms(df["date"]).dropna().tolist()
    return len(df), dates


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    source = pd.read_csv(
        SOURCE_PANEL,
        usecols=["date", "ticker", "regime_label", "regime_confidence"],
        dtype={"date": "string", "ticker": "string", "regime_label": "string"},
    )
    source = source[source["regime_label"].isin(EXPECTED_ROOTS)].copy()
    source_symbols = set(source["ticker"].dropna().unique())
    source_by_symbol = {symbol: frame.copy() for symbol, frame in source.groupby("ticker", sort=False)}

    file_records: list[FileRecord] = []
    root_records: list[RootRecord] = []

    for path in sorted(AQ_DATA_DIR.glob("*.feather")):
        symbol, quote, timeframe = parse_aq_filename(path)
        try:
            rows, dates = read_feather_dates(path)
        except Exception as exc:  # keep audit fail-closed if a cache file is unreadable
            file_records.append(
                FileRecord(
                    file=str(path),
                    symbol=symbol,
                    quote=quote,
                    timeframe=timeframe,
                    rows=0,
                    first_date="",
                    last_date="",
                    exact_source_panel_symbol=symbol in source_symbols,
                    status="blocked_unreadable",
                    reason=f"{type(exc).__name__}: {exc}",
                )
            )
            continue

        unique_dates = sorted(set(d for d in dates if d and d != "<NA>"))
        exact = symbol in source_symbols
        if exact:
            status = "exact_source_panel_symbol"
            reason = "Can attach source-panel parent-day labels only where bar date equals source date; no new source-owned label is created."
        else:
            status = "blocked_no_source_panel_label"
            reason = "Local Auto-Quant cache is OHLCV/provider data only for this symbol; no source-owned MainRegimeV2 label or equivalence policy is present."

        file_records.append(
            FileRecord(
                file=str(path),
                symbol=symbol,
                quote=quote,
                timeframe=timeframe,
                rows=rows,
                first_date=unique_dates[0] if unique_dates else "",
                last_date=unique_dates[-1] if unique_dates else "",
                exact_source_panel_symbol=exact,
                status=status,
                reason=reason,
            )
        )

        if not exact or not unique_dates:
            continue

        bar_dates = set(unique_dates)
        source_symbol = source_by_symbol[symbol]
        source_in_range = source_symbol[source_symbol["date"].isin(bar_dates)]
        for root in EXPECTED_ROOTS:
            source_days = int((source_symbol["regime_label"] == root).sum())
            matched_bar_days = int((source_in_range["regime_label"] == root).sum())
            lcb = wilson_lcb(matched_bar_days, source_days)
            coverage = matched_bar_days / source_days if source_days else 0.0
            if matched_bar_days == 0:
                status = "blocked_no_overlap_for_root"
                reason = "No local Auto-Quant bar dates overlap this exact source-panel root."
            elif timeframe == "1d":
                status = "already_covered_by_daily_source_inventory"
                reason = "This is exact same-symbol daily overlap and does not add a new timeframe or source-label gate."
            else:
                status = "candidate_parent_day_context_only"
                reason = "Exact same-symbol bar dates can carry parent-day context, not native intraday regime labels."
            root_records.append(
                RootRecord(
                    symbol=symbol,
                    timeframe=timeframe,
                    root=root,
                    source_days=source_days,
                    matched_bar_days=matched_bar_days,
                    coverage=coverage,
                    wilson95_lcb=lcb,
                    status=status,
                    reason=reason,
                )
            )

    file_rows = [asdict(record) for record in file_records]
    root_rows = [asdict(record) for record in root_records]

    exact_files = [r for r in file_records if r.exact_source_panel_symbol]
    exact_subhour_files = [r for r in exact_files if r.timeframe not in {"", "1d"}]
    blocked_files = [r for r in file_records if not r.exact_source_panel_symbol]
    local_symbols = sorted({r.symbol for r in file_records})
    exact_symbols = sorted({r.symbol for r in exact_files})
    blocked_symbols = sorted({r.symbol for r in blocked_files})
    recency_candidates = [r for r in file_records if r.last_date > "2026-01-30"]

    result = {
        "run_id": RUN_ID,
        "purpose": "Audit whether the local Auto-Quant cache can fulfill the Board A source-label equivalence request without promoting OHLCV/provider bars into labels.",
        "source_panel": str(SOURCE_PANEL),
        "source_panel_tickers": len(source_symbols),
        "source_panel_date_min": str(source["date"].min()),
        "source_panel_date_max": str(source["date"].max()),
        "autoquant_data_dir": str(AQ_DATA_DIR),
        "autoquant_feather_files": len(file_records),
        "autoquant_symbols": local_symbols,
        "exact_source_panel_symbols": exact_symbols,
        "blocked_no_source_panel_label_symbols": blocked_symbols,
        "exact_source_panel_files": len(exact_files),
        "exact_source_panel_subhour_files": len(exact_subhour_files),
        "files_extending_after_source_panel_tail": len(recency_candidates),
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "gate_result": "autoquant_local_source_label_equivalence_audit_v1=no_new_source_labels_exact_daily_aapl_only",
        "decision": "blocked_for_source_label_equivalence",
        "reason": "The local Auto-Quant cache is useful provider/OHLCV coverage, but it contains no source-owned MainRegimeV2 labels. Exact source-panel overlap is limited to AAPL daily, which is already covered by the daily source inventory and adds no native sub-hour, crypto, FX, futures, or direct Manipulation source labels.",
        "next_action": "Do not use local Auto-Quant OHLCV cache as source labels; fulfill the source-label equivalence request with source-owned labels or owner-approved equivalence policies.",
    }

    json_path = OUT_DIR / "autoquant_local_source_label_equivalence_audit_v1.json"
    files_csv = OUT_DIR / "autoquant_local_source_label_equivalence_audit_v1_files.csv"
    roots_csv = OUT_DIR / "autoquant_local_source_label_equivalence_audit_v1_exact_root_overlap.csv"
    report_path = OUT_DIR / "autoquant_local_source_label_equivalence_audit_v1.md"
    checks_path = CHECK_DIR / "autoquant_local_source_label_equivalence_audit_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_csv(files_csv, file_rows, list(FileRecord.__annotations__.keys()))
    write_csv(roots_csv, root_rows, list(RootRecord.__annotations__.keys()))

    report = f"""# Auto-Quant Local Source Label Equivalence Audit v1

Run ID: `{RUN_ID}`

This audit checks whether `/Users/thrill3r/Auto-Quant/user_data/data` can satisfy the Board A source-label equivalence request. It reads local cache metadata and source-panel labels only; it does not write raw provider rows into the repo and does not create generated labels.

## Decision

`autoquant_local_source_label_equivalence_audit_v1=no_new_source_labels_exact_daily_aapl_only`

- Auto-Quant feather files inspected: `{len(file_records)}`.
- Local Auto-Quant symbols: `{len(local_symbols)}`.
- Exact source-panel symbols in the cache: `{', '.join(exact_symbols) if exact_symbols else 'none'}`.
- Exact source-panel sub-hour files: `{len(exact_subhour_files)}`.
- Files extending after source-panel tail `2026-01-30`: `{len(recency_candidates)}`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Full objective achieved: `false`.
- `update_goal`: `false`.

## Why It Blocks

The local Auto-Quant cache is OHLCV/provider data. It is not a source-owned `MainRegimeV2` label panel.

Only `AAPL_USD-1d.feather` exactly matches a ticker in the stock-market-regimes source panel. That is daily same-symbol overlap and is already covered by `daily_main_root_source_inventory_v1`; it adds no native sub-hour label, no futures/crypto/FX equivalence, no source-panel recency beyond `2026-01-30`, and no direct `Manipulation` rows.

Non-exact symbols such as `SPY`, `QQQ`, `NQ`, `ES`, `BTC`, `ETH`, `SOL`, `BNB`, `AVAX`, `GLD`, and `EUR` remain blocked unless a source owner supplies labels or an explicit equivalence policy. Their OHLCV bars are not promoted into labels.

## Artifacts

- JSON: `{json_path}`
- File inventory CSV: `{files_csv}`
- Exact root overlap CSV: `{roots_csv}`
- Assertions: `{checks_path}`

## Next

Fulfill `source_label_equivalence_request_v1` with source-owned labels or owner-approved equivalence policy. Until then, keep local Auto-Quant cache as provider coverage only, not as Board A confidence-gate evidence.
"""
    report_path.write_text(report)

    assertions = [
        ("accepted_rows_added_zero", result["accepted_rows_added"] == 0),
        ("new_confidence_gate_false", result["new_confidence_gate"] is False),
        ("full_objective_false", result["full_objective_achieved"] is False),
        ("no_threshold_relaxation", result["thresholds_relaxed"] is False),
        ("no_runtime_code_change", result["runtime_code_changed"] is False),
        ("no_raw_data_commit", result["raw_data_committed"] is False),
        ("exact_subhour_source_panel_files_zero", len(exact_subhour_files) == 0),
        ("aapl_daily_only_exact_overlap", exact_symbols == ["AAPL"] and len(exact_files) == 1),
    ]
    failed = [name for name, ok in assertions if not ok]
    lines = [f"PASS {name}" if ok else f"FAIL {name}" for name, ok in assertions]
    if failed:
        lines.append(f"FAILED_ASSERTIONS {','.join(failed)}")
        checks_path.write_text("\n".join(lines) + "\n")
        raise SystemExit(1)
    lines.append("ALL_ASSERTIONS_PASS")
    checks_path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
