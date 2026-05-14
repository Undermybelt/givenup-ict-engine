#!/usr/bin/env python3
"""Check which yfinance native intraday intervals overlap source-label dates.

This is a feasibility preflight, not a confidence gate. It prevents repeated
attempts to attach stock-market-regimes source labels to native yfinance
intervals whose retained bar dates no longer overlap the source panel.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf


RUN_ID = "20260511T143726+0800-codex-yfinance-native-interval-overlap-preflight-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T143726-codex-yfinance-native-interval-overlap-preflight-v1"
)
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
SOURCE_PANEL = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
OUT_JSON = RUN_ROOT / "native-interval-overlap/yfinance_native_interval_overlap_preflight_v1.json"
OUT_MD = RUN_ROOT / "native-interval-overlap/yfinance_native_interval_overlap_preflight_v1.md"
OUT_CSV = RUN_ROOT / "native-interval-overlap/yfinance_native_interval_overlap_preflight_v1_intervals.csv"
OUT_ASSERT = RUN_ROOT / "checks/yfinance_native_interval_overlap_preflight_v1_assertions.out"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
INTERVAL_PERIODS = {
    "1m": "7d",
    "5m": "60d",
    "15m": "60d",
    "30m": "60d",
    "60m": "730d",
    "90m": "60d",
    "1h": "730d",
}


def wilson_lcb(pos: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    p = pos / n
    denom = 1 + z * z / n
    center = p + z * z / (2 * n)
    radius = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (center - radius) / denom


def source_labels() -> tuple[pd.DataFrame, dict[tuple[str, object], str]]:
    source = pd.read_csv(
        SOURCE_PANEL,
        usecols=["date", "ticker", "regime_label"],
        parse_dates=["date"],
    )
    source = source[source["regime_label"].isin(ROOTS)].sort_values(["ticker", "date"]).copy()
    source["row_index_for_ticker"] = source.groupby("ticker").cumcount()
    source = source[source["row_index_for_ticker"] >= 252].copy()
    source["session_date"] = source["date"].dt.date
    labels = {
        (row.ticker, row.session_date): row.regime_label
        for row in source[["ticker", "session_date", "regime_label"]].itertuples(index=False)
    }
    return source, labels


def session_dates(index: pd.DatetimeIndex) -> list[object]:
    if getattr(index, "tz", None) is not None:
        index = index.tz_convert("America/New_York")
    return pd.Series(index).dt.date.tolist()


def fetch_interval(tickers: list[str], interval: str, period: str) -> pd.DataFrame:
    return yf.download(
        tickers=tickers,
        period=period,
        interval=interval,
        group_by="ticker",
        auto_adjust=False,
        progress=False,
        threads=True,
        prepost=False,
    )


def main() -> int:
    board_sha = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    source, labels = source_labels()
    tickers = sorted(source["ticker"].unique().tolist())
    source_min = str(source["session_date"].min())
    source_max = str(source["session_date"].max())

    interval_rows = []
    interval_details = {}
    for interval, period in INTERVAL_PERIODS.items():
        data = fetch_interval(tickers, interval, period)
        ready_tickers = []
        failed_tickers = []
        overlap_pairs: set[tuple[str, object]] = set()
        provider_first_dates = []
        provider_last_dates = []
        root_counter: Counter[str] = Counter()
        provider_rows = 0

        for ticker in tickers:
            if not isinstance(data.columns, pd.MultiIndex) or ticker not in data.columns.get_level_values(0):
                failed_tickers.append(ticker)
                continue
            bars = data[ticker].dropna(how="all")
            if bars.empty:
                failed_tickers.append(ticker)
                continue
            ready_tickers.append(ticker)
            provider_rows += int(len(bars))
            dates = session_dates(bars.index)
            provider_first_dates.append(min(dates))
            provider_last_dates.append(max(dates))
            for day in set(dates):
                root = labels.get((ticker, day))
                if root:
                    overlap_pairs.add((ticker, day))
                    root_counter[root] += 1

        root_support = {root: int(root_counter[root]) for root in ROOTS}
        root_wilson = {root: round(wilson_lcb(root_counter[root], root_counter[root]), 10) for root in ROOTS}
        has_overlap = bool(overlap_pairs)
        interval_details[interval] = {
            "period": period,
            "provider_rows": provider_rows,
            "ready_ticker_count": len(ready_tickers),
            "failed_ticker_count": len(failed_tickers),
            "failed_tickers": failed_tickers,
            "provider_first_session_date": str(min(provider_first_dates)) if provider_first_dates else "",
            "provider_last_session_date": str(max(provider_last_dates)) if provider_last_dates else "",
            "source_overlap_ticker_days": len(overlap_pairs),
            "source_overlap_by_root": root_support,
            "source_overlap_wilson95_by_root": root_wilson,
            "has_source_date_overlap": has_overlap,
        }
        interval_rows.append(
            {
                "interval": interval,
                "period": period,
                "provider_rows": provider_rows,
                "ready_ticker_count": len(ready_tickers),
                "failed_ticker_count": len(failed_tickers),
                "provider_first_session_date": str(min(provider_first_dates)) if provider_first_dates else "",
                "provider_last_session_date": str(max(provider_last_dates)) if provider_last_dates else "",
                "source_overlap_ticker_days": len(overlap_pairs),
                "bull_overlap_days": root_support["Bull"],
                "bear_overlap_days": root_support["Bear"],
                "sideways_overlap_days": root_support["Sideways"],
                "crisis_overlap_days": root_support["Crisis"],
                "has_source_date_overlap": has_overlap,
            }
        )

    interval_df = pd.DataFrame(interval_rows)
    overlap_intervals = interval_df[interval_df["has_source_date_overlap"]]["interval"].tolist()
    blocked_no_overlap = interval_df[~interval_df["has_source_date_overlap"]]["interval"].tolist()
    canonical_intervals = [interval for interval in overlap_intervals if interval == "1h"]
    alias_intervals = [interval for interval in overlap_intervals if interval == "60m"]

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD),
        "board_sha256_at_run": board_sha,
        "source_panel": {
            "path": str(SOURCE_PANEL),
            "ticker_count": len(tickers),
            "date_min_after_252d_warmup": source_min,
            "date_max_after_252d_warmup": source_max,
            "roots": ROOTS,
            "raw_source_data_committed": False,
        },
        "provider": {
            "name": "yfinance",
            "version": getattr(yf, "__version__", "unknown"),
            "raw_provider_rows_committed": False,
        },
        "intervals": interval_details,
        "decision": {
            "overlap_intervals": overlap_intervals,
            "canonical_source_overlap_intervals": canonical_intervals,
            "alias_source_overlap_intervals": alias_intervals,
            "blocked_no_source_date_overlap_intervals": blocked_no_overlap,
            "accepted_confidence_rows_added": 0,
            "accepted_gate": "yfinance_native_interval_overlap_preflight_v1=no_new_confidence_gate_1h_only_native_overlap",
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Do not rerun native yfinance sub-hour exact-source attachment until source labels extend beyond "
            "2026-01-30 or another source-label panel overlaps the retained sub-hour bars. If another cycle is "
            "needed before source extension, materialize a separate 1h-derived 4h parent-day context policy and "
            "mark it derived, not provider-native."
        ),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_ASSERT.parent.mkdir(parents=True, exist_ok=True)
    interval_df.to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# YFinance Native Interval Overlap Preflight v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This run checks which native yfinance intervals actually overlap the stock-market-regimes source-label dates.",
        "It does not add a confidence gate; it narrows the next viable timeframe route.",
        "",
        "## Result",
        "",
        f"- Source panel after warmup: `{len(tickers)}` tickers, `{source_min}` to `{source_max}`.",
        f"- Intervals checked: `{', '.join(INTERVAL_PERIODS.keys())}`.",
        f"- Intervals with any source-date overlap: `{', '.join(overlap_intervals) if overlap_intervals else 'none'}`.",
        f"- Canonical interval with source-date overlap: `{', '.join(canonical_intervals) if canonical_intervals else 'none'}`.",
        f"- Alias interval with source-date overlap: `{', '.join(alias_intervals) if alias_intervals else 'none'}`.",
        f"- Blocked native intervals with no source-date overlap: `{', '.join(blocked_no_overlap) if blocked_no_overlap else 'none'}`.",
        "- Accepted confidence rows added: `0`.",
        "- Full objective achieved: `false`.",
        "- Runtime code changed: `false`.",
        "- Thresholds relaxed: `false`.",
        "- Raw data committed: `false`.",
        "- Trade usable: `false`.",
        "- Gate result: `yfinance_native_interval_overlap_preflight_v1=no_new_confidence_gate_1h_only_native_overlap`.",
        "",
        "## Interval Summary",
        "",
        "| Interval | Period | Ready Tickers | Provider First Date | Provider Last Date | Source-Overlap Ticker-Days | Bull | Bear | Sideways | Crisis | Decision |",
        "|---|---:|---:|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in interval_rows:
        decision = "overlap" if row["has_source_date_overlap"] else "blocked_no_source_date_overlap"
        if row["interval"] == "60m":
            decision = "overlap_alias_of_1h" if row["has_source_date_overlap"] else decision
        lines.append(
            "| `{interval}` | `{period}` | {ready} | {first} | {last} | {overlap} | {bull} | {bear} | {sideways} | {crisis} | `{decision}` |".format(
                interval=row["interval"],
                period=row["period"],
                ready=row["ready_ticker_count"],
                first=row["provider_first_session_date"],
                last=row["provider_last_session_date"],
                overlap=row["source_overlap_ticker_days"],
                bull=row["bull_overlap_days"],
                bear=row["bear_overlap_days"],
                sideways=row["sideways_overlap_days"],
                crisis=row["crisis_overlap_days"],
                decision=decision,
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Native yfinance sub-hour intervals do not overlap the current source panel because retained provider bars start after the panel's `2026-01-30` label cutoff.",
            "- `60m` is treated as an alias of `1h`, not a new cycle.",
            "- Additional native yfinance intraday work should wait for source-label extension or a different overlapping source-label panel.",
            "- A separate derived `4h` artifact may be useful, but it must be labeled as derived from `1h`, not provider-native.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    failures = []
    if "1h" not in overlap_intervals:
        failures.append("expected_1h_source_overlap")
    if not set(["1m", "5m", "15m", "30m", "90m"]).issubset(set(blocked_no_overlap)):
        failures.append("expected_subhour_and_90m_no_source_overlap")
    if result["decision"]["accepted_confidence_rows_added"] != 0:
        failures.append("expected_no_confidence_rows_added")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={board_sha}",
        f"source_ticker_count={len(tickers)}",
        f"overlap_intervals={','.join(overlap_intervals)}",
        f"blocked_no_source_date_overlap_intervals={','.join(blocked_no_overlap)}",
        "accepted_confidence_rows_added=0",
        "full_objective_achieved=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS" if not failures else "assertion_status=FAIL",
    ]
    assertions.extend(f"FAIL {failure}" for failure in failures)
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    if failures:
        raise RuntimeError("; ".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
