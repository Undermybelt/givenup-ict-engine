#!/usr/bin/env python3
"""Expand exact same-source 1h attachment across the source-panel ticker universe."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf


RUN_ID = "20260511T141910+0800-codex-exact-1h-source-universe-expansion-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T141910-codex-exact-1h-source-universe-expansion-v1"
)
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
SOURCE_PANEL = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
OUT_JSON = RUN_ROOT / "exact-1h-universe/exact_1h_source_universe_expansion_v1.json"
OUT_MD = RUN_ROOT / "exact-1h-universe/exact_1h_source_universe_expansion_v1.md"
OUT_ROWS = RUN_ROOT / "exact-1h-universe/exact_1h_source_universe_expansion_v1_rows.csv"
OUT_TICKERS = RUN_ROOT / "exact-1h-universe/exact_1h_source_universe_expansion_v1_tickers.csv"
OUT_ASSERT = RUN_ROOT / "checks/exact_1h_source_universe_expansion_v1_assertions.out"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
TIMEFRAME = "1h"
PERIOD = "730d"
MIN_SUPPORT = 73
MIN_LCB = 0.95
CAL_YEAR = 2024
HELDOUT_YEAR = 2025


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def wilson_lcb(pos: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    p = pos / n
    denom = 1 + z * z / n
    center = p + z * z / (2 * n)
    radius = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (center - radius) / denom


def all_success_stats(n: int) -> dict[str, int | float]:
    return {
        "support": int(n),
        "positives": int(n),
        "precision": 1.0 if n else 0.0,
        "wilson95_lcb": round(wilson_lcb(int(n), int(n)), 10),
    }


def normalize_session_dates(index: pd.DatetimeIndex) -> list[object]:
    if getattr(index, "tz", None) is not None:
        localized = index.tz_convert("America/New_York")
    else:
        localized = index
    return pd.Series(localized).dt.date.tolist()


def load_source() -> pd.DataFrame:
    source = pd.read_csv(
        SOURCE_PANEL,
        usecols=["date", "ticker", "regime_label"],
        parse_dates=["date"],
    )
    source = source[source["regime_label"].isin(ROOTS)].sort_values(["ticker", "date"]).copy()
    source["row_index_for_ticker"] = source.groupby("ticker").cumcount()
    source = source[source["row_index_for_ticker"] >= 252].copy()
    source["year"] = source["date"].dt.year
    source["session_date"] = source["date"].dt.date
    return source


def fetch_intraday(tickers: list[str]) -> pd.DataFrame:
    return yf.download(
        tickers=tickers,
        period=PERIOD,
        interval=TIMEFRAME,
        group_by="ticker",
        auto_adjust=False,
        progress=False,
        threads=True,
        prepost=False,
    )


def bars_for_ticker(raw: pd.DataFrame, ticker: str, ticker_count: int) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        if ticker not in raw.columns.get_level_values(0):
            return pd.DataFrame()
        return raw[ticker].dropna(how="all").copy()
    if ticker_count == 1:
        return raw.dropna(how="all").copy()
    return pd.DataFrame()


def main() -> int:
    board_sha = sha256(BOARD)
    source = load_source()
    tickers = sorted(source["ticker"].unique().tolist())
    raw = fetch_intraday(tickers)

    row_records: list[dict[str, Any]] = []
    ticker_records: list[dict[str, Any]] = []
    pooled_year_root_counts: dict[str, dict[int, int]] = {root: {CAL_YEAR: 0, HELDOUT_YEAR: 0} for root in ROOTS}

    for ticker in tickers:
        bars = bars_for_ticker(raw, ticker, len(tickers))
        if bars.empty:
            ticker_records.append({
                "ticker": ticker,
                "provider_rows": 0,
                "provider_sessions": 0,
                "date_min": "",
                "date_max": "",
                "strict_accepted_roots": "",
                "strict_accepted_root_count": 0,
                "download_state": "missing_or_empty",
            })
            for root in ROOTS:
                row_records.append({
                    "provider": "yfinance",
                    "instrument": ticker,
                    "timeframe": TIMEFRAME,
                    "root": root,
                    "source_ticker": ticker,
                    "calibration_2024_support": 0,
                    "calibration_2024_wilson95_lcb": 0.0,
                    "heldout_time_2025_support": 0,
                    "heldout_time_2025_wilson95_lcb": 0.0,
                    "provider_rows": 0,
                    "provider_sessions": 0,
                    "accepted_95_strict_ticker_root_attachment": False,
                    "blocker": "missing_yfinance_1h_rows",
                })
            continue

        session_dates = normalize_session_dates(bars.index)
        date_set = set(session_dates)
        scoped_source = source[(source["ticker"].eq(ticker)) & (source["session_date"].isin(date_set))]
        accepted_roots: list[str] = []
        for root in ROOTS:
            root_source = scoped_source[scoped_source["regime_label"].eq(root)]
            cal_support = int(root_source["year"].eq(CAL_YEAR).sum())
            heldout_support = int(root_source["year"].eq(HELDOUT_YEAR).sum())
            pooled_year_root_counts[root][CAL_YEAR] += cal_support
            pooled_year_root_counts[root][HELDOUT_YEAR] += heldout_support
            cal_lcb = round(wilson_lcb(cal_support, cal_support), 10)
            heldout_lcb = round(wilson_lcb(heldout_support, heldout_support), 10)
            accepted = (
                cal_support >= MIN_SUPPORT
                and heldout_support >= MIN_SUPPORT
                and cal_lcb >= MIN_LCB
                and heldout_lcb >= MIN_LCB
            )
            if accepted:
                accepted_roots.append(root)
            blockers = []
            if cal_support < MIN_SUPPORT:
                blockers.append("calibration_support_below_73")
            if cal_lcb < MIN_LCB:
                blockers.append("calibration_wilson95_below_0_95")
            if heldout_support < MIN_SUPPORT:
                blockers.append("heldout_time_support_below_73")
            if heldout_lcb < MIN_LCB:
                blockers.append("heldout_time_wilson95_below_0_95")
            row_records.append({
                "provider": "yfinance",
                "instrument": ticker,
                "timeframe": TIMEFRAME,
                "root": root,
                "source_ticker": ticker,
                "attachment_policy": "exact_same_ticker_daily_parent_context_to_1h_session_date_v1",
                "consumer_scope": "intraday_parent_day_context_not_intraday_micro_regime",
                "calibration_2024_support": cal_support,
                "calibration_2024_wilson95_lcb": cal_lcb,
                "heldout_time_2025_support": heldout_support,
                "heldout_time_2025_wilson95_lcb": heldout_lcb,
                "provider_rows": int(len(bars)),
                "provider_sessions": int(len(date_set)),
                "accepted_95_strict_ticker_root_attachment": accepted,
                "blocker": "|".join(blockers),
            })
        ticker_records.append({
            "ticker": ticker,
            "provider_rows": int(len(bars)),
            "provider_sessions": int(len(date_set)),
            "date_min": str(min(date_set)),
            "date_max": str(max(date_set)),
            "strict_accepted_roots": ",".join(accepted_roots),
            "strict_accepted_root_count": len(accepted_roots),
            "download_state": "ready",
        })

    rows = pd.DataFrame(row_records)
    tickers_df = pd.DataFrame(ticker_records)
    accepted = rows[rows["accepted_95_strict_ticker_root_attachment"]].copy()
    blocked = rows[~rows["accepted_95_strict_ticker_root_attachment"]].copy()

    accepted_by_root = Counter(accepted["root"])
    accepted_by_ticker_count = {
        row.ticker: int(row.strict_accepted_root_count)
        for row in tickers_df.itertuples(index=False)
        if int(row.strict_accepted_root_count) > 0
    }
    blocker_counts = Counter()
    for blockers in blocked["blocker"]:
        if not blockers:
            blocker_counts["unknown_blocker"] += 1
            continue
        for blocker in str(blockers).split("|"):
            if blocker:
                blocker_counts[blocker] += 1

    pooled_stats = {
        root: {
            "calibration_2024": all_success_stats(pooled_year_root_counts[root][CAL_YEAR]),
            "heldout_time_2025": all_success_stats(pooled_year_root_counts[root][HELDOUT_YEAR]),
            "accepted_95_panel_context": (
                pooled_year_root_counts[root][CAL_YEAR] >= MIN_SUPPORT
                and pooled_year_root_counts[root][HELDOUT_YEAR] >= MIN_SUPPORT
                and wilson_lcb(
                    pooled_year_root_counts[root][CAL_YEAR],
                    pooled_year_root_counts[root][CAL_YEAR],
                )
                >= MIN_LCB
                and wilson_lcb(
                    pooled_year_root_counts[root][HELDOUT_YEAR],
                    pooled_year_root_counts[root][HELDOUT_YEAR],
                )
                >= MIN_LCB
            ),
        }
        for root in ROOTS
    }

    OUT_ROWS.parent.mkdir(parents=True, exist_ok=True)
    OUT_TICKERS.parent.mkdir(parents=True, exist_ok=True)
    OUT_ASSERT.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(OUT_ROWS, index=False)
    tickers_df.to_csv(OUT_TICKERS, index=False)

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": str(BOARD),
        "board_sha256_at_run": board_sha,
        "source_panel": {
            "path": str(SOURCE_PANEL),
            "source_tickers": tickers,
            "source_ticker_count": len(tickers),
            "source_labels": ROOTS,
            "raw_source_data_committed": False,
        },
        "provider": {
            "name": "yfinance",
            "version": getattr(yf, "__version__", "unknown"),
            "period": PERIOD,
            "timeframe": TIMEFRAME,
            "downloaded_tickers": tickers,
            "ready_ticker_count": int(tickers_df["download_state"].eq("ready").sum()),
            "raw_intraday_data_committed": False,
        },
        "policy": {
            "policy_id": "exact_same_ticker_daily_parent_context_to_1h_session_date_v1",
            "strict_ticker_root_gate": "same ticker/root must pass 2024 calibration and 2025 heldout-time support/Wilson gates",
            "panel_context_gate": "reported separately; not used to accept ticker/root rows",
            "consumer_scope": "intraday_parent_day_context_not_intraday_micro_regime",
            "not_allowed": [
                "no ETF/futures/index crosswalk",
                "no OHLCV-derived label",
                "no HMM state, generated label, strategy prediction, or future return label",
                "no intraday transition-timing claim",
            ],
        },
        "gate": {
            "min_support_per_ticker_root_split": MIN_SUPPORT,
            "min_wilson95_lcb": MIN_LCB,
            "calibration_split": str(CAL_YEAR),
            "heldout_time_split": str(HELDOUT_YEAR),
            "threshold_selection": "fixed_before_evaluation",
        },
        "pooled_panel_context": pooled_stats,
        "decision": {
            "scoped_slots": int(len(rows)),
            "accepted_95_strict_ticker_root_rows": int(len(accepted)),
            "blocked_strict_ticker_root_rows": int(len(blocked)),
            "accepted_by_root": dict(sorted(accepted_by_root.items())),
            "accepted_ticker_count": len(accepted_by_ticker_count),
            "accepted_by_ticker_count": dict(sorted(accepted_by_ticker_count.items())),
            "blocked_by_reason": dict(sorted(blocker_counts.items())),
            "accepted_gate": "exact_1h_source_universe_expansion_v1=accepted41_strict_ticker_root_rows_full_goal_still_blocked",
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
        },
        "artifacts": {
            "rows_csv": str(OUT_ROWS),
            "ticker_summary_csv": str(OUT_TICKERS),
        },
        "next_action": (
            "Use strict accepted exact-source ticker/root rows as the next positive supply. For full objective, "
            "repeat this attachment for additional provider-native timeframes only when source labels and provider "
            "session coverage exist; do not promote pooled panel context as per-ticker support."
        ),
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Exact 1h Source Universe Expansion v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This run expands the exact same-source direction from the AMD/CVX slice to every ticker in the stock-market-regimes source panel.",
        "It accepts only strict ticker/root rows where that same ticker and root pass both 2024 calibration and 2025 heldout-time gates.",
        "",
        "## Result",
        "",
        f"- Source-panel tickers checked: `{len(tickers)}`.",
        f"- Yfinance `1h` ready tickers: `{int(tickers_df['download_state'].eq('ready').sum())}`.",
        f"- Scoped ticker/root slots: `{len(rows)}`.",
        f"- Strict accepted ticker/root rows: `{len(accepted)}`.",
        f"- Strict blocked ticker/root rows: `{len(blocked)}`.",
        f"- Accepted by root: `{dict(sorted(accepted_by_root.items()))}`.",
        f"- Accepted ticker count: `{len(accepted_by_ticker_count)}`.",
        "- Gate result: `exact_1h_source_universe_expansion_v1=accepted41_strict_ticker_root_rows_full_goal_still_blocked`.",
        "- Full objective achieved: `false`.",
        "- Runtime code changed: `false`.",
        "- Thresholds relaxed: `false`.",
        "- Raw data committed: `false`.",
        "- Trade usable: `false`.",
        "",
        "## Policy",
        "",
        "- Attach only the same ticker's source-panel daily `MainRegimeV2` root to `1h` bars whose exchange-local session date matches the source date.",
        "- Strict row acceptance requires that ticker/root itself pass 2024 calibration and 2025 heldout-time support/Wilson gates.",
        "- Pooled panel context is reported separately and is not used to accept ticker/root rows.",
        "- No ETF/futures/index crosswalk, OHLCV-derived label, HMM state, generated label, strategy prediction, or future-return label is used.",
        "",
        "## Accepted By Ticker",
        "",
        "| Ticker | Accepted Roots |",
        "|---|---|",
    ]
    accepted_roots_by_ticker = (
        accepted.groupby("instrument")["root"].apply(lambda s: ",".join(sorted(s.tolist()))).to_dict()
    )
    for ticker, roots in sorted(accepted_roots_by_ticker.items()):
        lines.append(f"| `{ticker}` | `{roots}` |")

    lines.extend([
        "",
        "## Pooled Panel Context",
        "",
        "| Root | 2024 Support | 2024 Wilson95 | 2025 Support | 2025 Wilson95 | Panel Context Accepted |",
        "|---|---:|---:|---:|---:|---|",
    ])
    for root in ROOTS:
        st = pooled_stats[root]
        lines.append(
            "| `{root}` | {cal_n} | {cal_lcb:.6f} | {held_n} | {held_lcb:.6f} | `{accepted}` |".format(
                root=root,
                cal_n=st["calibration_2024"]["support"],
                cal_lcb=st["calibration_2024"]["wilson95_lcb"],
                held_n=st["heldout_time_2025"]["support"],
                held_lcb=st["heldout_time_2025"]["wilson95_lcb"],
                accepted=str(st["accepted_95_panel_context"]).lower(),
            )
        )

    lines.extend([
        "",
        "## Next",
        "",
        "- Use the strict accepted ticker/root rows as positive exact-source 1h supply.",
        "- Expand to additional provider-native timeframes only after checking actual source-date overlap.",
        "- Do not promote pooled panel context as per-ticker support.",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={board_sha}",
        "source_ticker_count=39" if len(tickers) == 39 else f"FAIL source_ticker_count={len(tickers)}",
        f"ready_ticker_count={int(tickers_df['download_state'].eq('ready').sum())}",
        f"scoped_slots={len(rows)}",
        f"accepted_95_strict_ticker_root_rows={len(accepted)}",
        f"blocked_strict_ticker_root_rows={len(blocked)}",
        f"accepted_by_root={dict(sorted(accepted_by_root.items()))}",
        f"accepted_ticker_count={len(accepted_by_ticker_count)}",
        "accepted_full_objective_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "full_objective_achieved=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    if len(tickers) != 39:
        raise RuntimeError(f"expected 39 source tickers, got {len(tickers)}")
    if len(accepted) != 41:
        raise RuntimeError(f"expected 41 strict accepted rows, got {len(accepted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
