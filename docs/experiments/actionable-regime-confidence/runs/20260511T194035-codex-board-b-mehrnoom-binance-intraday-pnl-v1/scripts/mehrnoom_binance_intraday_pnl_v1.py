#!/usr/bin/env python3
"""Mehrnoom direct-event Binance intraday PnL bridge.

This additive Board B artifact reconstructs executable 1h entry/exit returns
for accepted Mehrnoom Telegram pump-event rows using Binance OHLCV via ccxt.
It does not modify ict-engine runtime code, Auto-Quant strategies, or raw
source data.
"""

from __future__ import annotations

import csv
import json
import math
import random
import time
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import ccxt


RUN_ID = "20260511T194035+0800-codex-board-b-mehrnoom-binance-intraday-pnl-v1"
RUN_SLUG = "20260511T194035-codex-board-b-mehrnoom-binance-intraday-pnl-v1"

RAW_ROOT = Path("/private/tmp/ict-regime-mehrnoom-pump-dump")
COIN_PUMP = RAW_ROOT / "Telegram/classified/coin-pump.csv"

SUPPORTED_COIN_HINTS = [
    "BTC",
    "ETH",
    "XRP",
    "ADA",
    "ETC",
    "TRX",
    "OMG",
    "LSK",
    "XLM",
    "BAT",
    "ZRX",
    "LTC",
    "DASH",
    "NEO",
    "XEM",
    "SC",
    "DGB",
    "STORJ",
    "WAVES",
]

QUOTE_PREFERENCE = {
    "BTC": ["BTC/USDT", "BTC/BUSD", "BTC/FDUSD"],
    "ETH": ["ETH/USDT", "ETH/BTC"],
}

ENTRY_DELAY_HOURS = 1
PRIMARY_EXIT_HOURS = 6
SECONDARY_EXIT_HOURS = 24
CONTROL_EXCLUSION_HOURS = 24
FETCH_START = "2017-05-01T00:00:00Z"
FETCH_END = "2018-08-15T00:00:00Z"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_SLUG
OUT_DIR = RUN_ROOT / "mehrnoom-binance-intraday-pnl"
CHECK_DIR = RUN_ROOT / "checks"
CACHE_DIR = OUT_DIR / "ohlcv-cache"

REPORT_JSON = OUT_DIR / "mehrnoom_binance_intraday_pnl_v1.json"
REPORT_MD = OUT_DIR / "mehrnoom_binance_intraday_pnl_v1.md"
ROWS_CSV = OUT_DIR / "mehrnoom_binance_intraday_pnl_rows_v1.csv"
COVERAGE_CSV = OUT_DIR / "mehrnoom_binance_intraday_coin_coverage_v1.csv"
ASSERTIONS = CHECK_DIR / "mehrnoom_binance_intraday_pnl_v1_assertions.out"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def clean_coin(value: object) -> str:
    return str(value).strip().upper().replace("$", "")


def parse_dt(date_text: str, time_text: str) -> datetime | None:
    raw = f"{date_text} {time_text}"
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def dt_to_ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def ms_to_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


def next_entry_boundary(value: datetime) -> datetime:
    floored = value.replace(minute=0, second=0, microsecond=0)
    return floored + timedelta(hours=ENTRY_DELAY_HOURS)


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(out) or math.isinf(out):
        return default
    return out


def load_positive_events() -> list[dict[str, Any]]:
    if not COIN_PUMP.exists():
        raise RuntimeError(f"missing Mehrnoom coin pump CSV: {COIN_PUMP}")
    events: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    with COIN_PUMP.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            coin = clean_coin(row.get("Coin", ""))
            dt = parse_dt(str(row.get("Date", "")), str(row.get("Time", "")))
            if not coin or dt is None:
                continue
            key = (str(row.get("Channel ID", "")), str(row.get("Message ID", "")), dt.isoformat(), coin)
            if key in seen:
                continue
            seen.add(key)
            events.append(
                {
                    "channel_id": str(row.get("Channel ID", "")),
                    "message_id": str(row.get("Message ID", "")),
                    "coin": coin,
                    "dt": dt,
                    "source": "Mehrnoom_Mirtaheri_Telegram_coin_pump_csv",
                    "label_source": "classified_telegram_pump_attempt",
                    "target": 1,
                }
            )
    return events


def near_event(times: list[datetime], trial: datetime, seconds: int) -> bool:
    index = bisect_left(times, trial)
    if index < len(times) and abs((times[index] - trial).total_seconds()) <= seconds:
        return True
    if index > 0 and abs((trial - times[index - 1]).total_seconds()) <= seconds:
        return True
    return False


def build_negative_controls(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rng = random.Random(20260511194035)
    by_coin_times: dict[str, list[datetime]] = defaultdict(list)
    for row in events:
        by_coin_times[row["coin"]].append(row["dt"])
    for rows in by_coin_times.values():
        rows.sort()
    global_min = min(row["dt"] for row in events)
    global_max = max(row["dt"] for row in events)
    offsets_hours = [72, -72, 168, -168, 336, -336, 24, -24, 720, -720]
    controls: list[dict[str, Any]] = []
    exclusion_seconds = CONTROL_EXCLUSION_HOURS * 3600
    span_seconds = max(1, int((global_max - global_min).total_seconds()))
    for idx, row in enumerate(events):
        candidate: datetime | None = None
        for hours in offsets_hours:
            trial = row["dt"] + timedelta(hours=hours)
            if trial < global_min or trial > global_max:
                continue
            if not near_event(by_coin_times[row["coin"]], trial, exclusion_seconds):
                candidate = trial
                break
        if candidate is None:
            for _ in range(32):
                trial = global_min + timedelta(seconds=rng.randrange(span_seconds))
                if not near_event(by_coin_times[row["coin"]], trial, exclusion_seconds):
                    candidate = trial
                    break
        if candidate is None:
            continue
        controls.append(
            {
                "channel_id": row["channel_id"],
                "message_id": f"negative_control_for_{row['message_id']}_{idx}",
                "coin": row["coin"],
                "dt": candidate,
                "source": "synthetic_same_coin_non_event_control",
                "label_source": "no_classified_telegram_pump_attempt_within_24h",
                "target": 0,
            }
        )
    return controls


def resolve_symbol(coin: str, markets: dict[str, Any]) -> str | None:
    candidates = QUOTE_PREFERENCE.get(coin, [])
    candidates.extend([f"{coin}/BTC", f"{coin}/USDT", f"{coin}/ETH", f"{coin}/BNB"])
    for symbol in candidates:
        if symbol in markets:
            return symbol
    return None


def cache_path(symbol: str) -> Path:
    return CACHE_DIR / f"{symbol.replace('/', '_')}_1h.csv"


def read_cached_ohlcv(symbol: str) -> list[list[float]]:
    path = cache_path(symbol)
    if not path.exists():
        return []
    rows: list[list[float]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                [
                    int(row["timestamp_ms"]),
                    safe_float(row["open"]),
                    safe_float(row["high"]),
                    safe_float(row["low"]),
                    safe_float(row["close"]),
                    safe_float(row["volume"]),
                ]
            )
    return rows


def write_cached_ohlcv(symbol: str, rows: list[list[float]]) -> None:
    path = cache_path(symbol)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["timestamp_ms", "iso_ts", "open", "high", "low", "close", "volume"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "timestamp_ms": int(row[0]),
                    "iso_ts": ms_to_iso(int(row[0])),
                    "open": row[1],
                    "high": row[2],
                    "low": row[3],
                    "close": row[4],
                    "volume": row[5],
                }
            )


def fetch_ohlcv(exchange: Any, symbol: str) -> list[list[float]]:
    cached = read_cached_ohlcv(symbol)
    if cached:
        return cached
    since = exchange.parse8601(FETCH_START)
    end_ms = exchange.parse8601(FETCH_END)
    rows: list[list[float]] = []
    seen: set[int] = set()
    while since is not None and since < end_ms:
        batch = exchange.fetch_ohlcv(symbol, timeframe="1h", since=since, limit=1000)
        if not batch:
            break
        advanced = False
        for item in batch:
            ts = int(item[0])
            if ts >= end_ms:
                continue
            if ts not in seen:
                rows.append([ts, *[safe_float(x) for x in item[1:6]]])
                seen.add(ts)
            if ts >= since:
                advanced = True
        next_since = int(batch[-1][0]) + 60 * 60 * 1000
        if not advanced or next_since <= since:
            break
        since = next_since
        time.sleep(max(float(getattr(exchange, "rateLimit", 50)) / 1000.0, 0.05))
    rows.sort(key=lambda item: item[0])
    write_cached_ohlcv(symbol, rows)
    return rows


def attach_returns(events: list[dict[str, Any]], symbol_by_coin: dict[str, str], bars_by_symbol: dict[str, list[list[float]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    row_id = 0
    ts_by_symbol = {symbol: [int(row[0]) for row in bars] for symbol, bars in bars_by_symbol.items()}
    for event in sorted(events, key=lambda item: item["dt"]):
        symbol = symbol_by_coin.get(event["coin"])
        if not symbol:
            continue
        bars = bars_by_symbol.get(symbol, [])
        timestamps = ts_by_symbol.get(symbol, [])
        if not bars or not timestamps:
            continue
        entry_ms = dt_to_ms(next_entry_boundary(event["dt"]))
        idx = bisect_left(timestamps, entry_ms)
        if idx >= len(bars) or timestamps[idx] != entry_ms:
            continue
        primary_exit_idx = idx + PRIMARY_EXIT_HOURS
        secondary_exit_idx = idx + SECONDARY_EXIT_HOURS
        if secondary_exit_idx >= len(bars):
            continue
        entry_open = safe_float(bars[idx][1])
        exit_close = safe_float(bars[primary_exit_idx][4])
        exit_close_24h = safe_float(bars[secondary_exit_idx][4])
        if entry_open <= 0.0 or exit_close <= 0.0 or exit_close_24h <= 0.0:
            continue
        target = int(event["target"])
        primary_return = exit_close / entry_open - 1.0
        secondary_return = exit_close_24h / entry_open - 1.0
        row_id += 1
        quote = symbol.split("/", 1)[1] if "/" in symbol else ""
        rows.append(
            {
                "row_id": row_id,
                "run_id": RUN_ID,
                "coin": event["coin"],
                "provider_symbol": symbol,
                "quote": quote,
                "event_dt": event["dt"].isoformat(),
                "entry_ts": ms_to_iso(timestamps[idx]),
                "exit_ts_6h": ms_to_iso(timestamps[primary_exit_idx]),
                "exit_ts_24h": ms_to_iso(timestamps[secondary_exit_idx]),
                "entry_open": entry_open,
                "exit_close_6h": exit_close,
                "exit_close_24h": exit_close_24h,
                "return_6h": primary_return,
                "return_24h": secondary_return,
                "is_manipulation_positive": target == 1,
                "target": target,
                "label_source": event["label_source"],
                "source": event["source"],
                "provider": "ccxt.binance",
                "bridge_precision": "intraday_1h_next_bar_open_to_6h_close_with_24h_secondary",
                "parent_regime_root": "Manipulation(scoped)" if target == 1 else "Control(non_event)",
                "regime_profit_branch_path": (
                    "Manipulation(scoped) -> DirectEventOverlay -> "
                    "TelegramPumpEventBinanceIntraday6hPnlBridge -> provider_reconstructed_entry_exit"
                    if target == 1
                    else "Control(non_event) -> SameCoinNonEvent -> BinanceIntraday6hPnlBridge -> baseline"
                ),
            }
        )
    return rows


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(math.floor((len(ordered) - 1) * ratio))))
    return float(ordered[index])


def bootstrap_lcb(values: list[float], samples: int = 1000) -> float:
    if not values:
        return 0.0
    rng = random.Random(20260511194101)
    n = len(values)
    means: list[float] = []
    for _ in range(samples):
        means.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    return percentile(means, 0.05)


def bootstrap_diff_lcb(pos: list[float], neg: list[float], samples: int = 1000) -> float:
    if not pos or not neg:
        return 0.0
    rng = random.Random(20260511194102)
    diffs: list[float] = []
    for _ in range(samples):
        pos_mean = sum(pos[rng.randrange(len(pos))] for _ in range(len(pos))) / len(pos)
        neg_mean = sum(neg[rng.randrange(len(neg))] for _ in range(len(neg))) / len(neg)
        diffs.append(pos_mean - neg_mean)
    return percentile(diffs, 0.05)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def summarize(rows: list[dict[str, Any]], coverage: list[dict[str, Any]]) -> dict[str, Any]:
    pos = [row for row in rows if row["is_manipulation_positive"]]
    neg = [row for row in rows if not row["is_manipulation_positive"]]
    pos_returns = [float(row["return_6h"]) for row in pos]
    neg_returns = [float(row["return_6h"]) for row in neg]
    pos_returns_24h = [float(row["return_24h"]) for row in pos]
    neg_returns_24h = [float(row["return_24h"]) for row in neg]
    folds = sorted({str(row["entry_ts"])[:7] for row in pos})
    fold_diffs: list[float] = []
    for fold in folds:
        fold_pos = [float(row["return_6h"]) for row in pos if str(row["entry_ts"]).startswith(fold)]
        fold_neg = [float(row["return_6h"]) for row in neg if str(row["entry_ts"]).startswith(fold)]
        if fold_pos and fold_neg:
            fold_diffs.append(mean(fold_pos) - mean(fold_neg))
    fold_positive_rate = sum(1 for value in fold_diffs if value > 0.0) / len(fold_diffs) if fold_diffs else 0.0
    positive_mean = mean(pos_returns)
    control_mean = mean(neg_returns)
    diff = positive_mean - control_mean
    diff_lcb = bootstrap_diff_lcb(pos_returns, neg_returns)
    enough_rows = len(pos) >= 500 and len(neg) >= 500
    enough_folds = len(fold_diffs) >= 6
    edge_pass = diff > 0.0 and diff_lcb > 0.0 and fold_positive_rate >= 0.60
    direct_rows_ready = enough_rows and enough_folds and edge_pass
    blockers: list[str] = []
    if not enough_rows:
        blockers.append("reject_min_positive_or_control_rows_lt500")
    if not enough_folds:
        blockers.append("reject_monthly_folds_lt6")
    if diff <= 0.0:
        blockers.append("reject_positive_underperforms_control")
    if diff_lcb <= 0.0:
        blockers.append("reject_bootstrap_diff_lcb_nonpositive")
    if fold_positive_rate < 0.60:
        blockers.append("reject_fold_positive_rate_lt60pct")
    if direct_rows_ready:
        gate_result = "partial_repair:direct_manipulation_intraday_pnl_rows_ready"
    else:
        gate_result = "fail:direct_manipulation_intraday_pnl_bridge_not_accepted"
    return {
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "promotion_allowed_for_full_board_b": False,
        "direct_manipulation_rows_ready_for_future_rc_spa": direct_rows_ready,
        "positive_rows": len(pos),
        "control_rows": len(neg),
        "coins_with_rows": sum(1 for row in coverage if int(row["positive_rows"]) > 0),
        "provider": "ccxt.binance",
        "bridge_precision": "intraday_1h_next_bar_open_to_6h_close",
        "positive_mean_6h_return": positive_mean,
        "control_mean_6h_return": control_mean,
        "positive_minus_control_6h_return": diff,
        "positive_bootstrap_lcb_5pct_6h": bootstrap_lcb(pos_returns),
        "positive_minus_control_bootstrap_lcb_5pct_6h": diff_lcb,
        "positive_mean_24h_return": mean(pos_returns_24h),
        "control_mean_24h_return": mean(neg_returns_24h),
        "positive_minus_control_24h_return": mean(pos_returns_24h) - mean(neg_returns_24h),
        "monthly_folds": len(fold_diffs),
        "fold_positive_rate_vs_control": fold_positive_rate,
        "blockers": blockers,
        "downstream_consumption": "not_started:full_board_b_still_blocked_by_required_root_branch_rc_spa",
        "next_action": (
            "B2R-repeat: if reused, feed these direct Manipulation intraday rows into a fresh "
            "all-root RC-SPA matrix with non-overlapping artifact names; full Board B remains "
            "blocked until Bull/Bear/Sideways/Crisis also pass."
            if direct_rows_ready
            else "B2R-repeat: direct Manipulation still needs stronger intraday/source-owned PnL rows; "
            "do not promote downstream."
        ),
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(summary: dict[str, Any], coverage: list[dict[str, Any]]) -> None:
    lines = [
        "# Mehrnoom Binance Intraday PnL Bridge v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"- Gate result: `{summary['gate_result']}`",
        f"- Direct rows ready for future RC-SPA: `{summary['direct_manipulation_rows_ready_for_future_rc_spa']}`",
        f"- Full Board B promotion allowed: `{summary['promotion_allowed_for_full_board_b']}`",
        f"- Provider rows: `{summary['positive_rows'] + summary['control_rows']}`",
        f"- Positive event rows: `{summary['positive_rows']}`",
        f"- Control rows: `{summary['control_rows']}`",
        f"- Positive mean 6h return: `{summary['positive_mean_6h_return']:.6f}`",
        f"- Control mean 6h return: `{summary['control_mean_6h_return']:.6f}`",
        f"- Positive-control 6h mean diff: `{summary['positive_minus_control_6h_return']:.6f}`",
        f"- Positive-control 6h bootstrap LCB 5%: `{summary['positive_minus_control_bootstrap_lcb_5pct_6h']:.6f}`",
        f"- Monthly folds: `{summary['monthly_folds']}`",
        f"- Fold positive rate vs control: `{summary['fold_positive_rate_vs_control']:.4f}`",
        f"- Blockers: `{';'.join(summary['blockers']) if summary['blockers'] else 'none_for_direct_branch_rows'}`",
        f"- Downstream consumption: `{summary['downstream_consumption']}`",
        "",
        "## Protocol",
        "",
        "- Positive rows come from accepted Mehrnoom Telegram pump events.",
        "- Controls are same-coin non-event timestamps at least 24h away from a classified pump event.",
        "- Entry is the next 1h bar open after the event timestamp; primary exit is the 6h close; 24h return is recorded as secondary context.",
        "- This is provider-reconstructed intraday PnL, not source-owned sell/exit rows.",
        "- Even if the direct branch is repairable, full Board B remains blocked until every required root branch passes RC-SPA.",
        "",
        "## Coin Coverage",
        "",
        "| Coin | Symbol | Events | Controls | Bars | Positive Rows | Control Rows | Status |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in coverage:
        lines.append(
            f"| `{row['coin']}` | `{row['symbol']}` | {row['positive_events']} | {row['control_events']} | "
            f"{row['bars']} | {row['positive_rows']} | {row['control_rows']} | `{row['status']}` |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(REPORT_JSON)}`",
            f"- Rows CSV: `{rel(ROWS_CSV)}`",
            f"- Coin coverage CSV: `{rel(COVERAGE_CSV)}`",
            f"- Assertions: `{rel(ASSERTIONS)}`",
            "",
            "## Next",
            "",
            f"- {summary['next_action']}",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    positives_all = load_positive_events()
    positives = [row for row in positives_all if row["coin"] in SUPPORTED_COIN_HINTS]
    controls = build_negative_controls(positives)
    counts_pos = Counter(row["coin"] for row in positives)
    counts_neg = Counter(row["coin"] for row in controls)

    exchange = ccxt.binance({"enableRateLimit": True})
    markets = exchange.load_markets()
    symbol_by_coin = {
        coin: symbol
        for coin in SUPPORTED_COIN_HINTS
        if (symbol := resolve_symbol(coin, markets)) is not None and counts_pos[coin] > 0
    }

    bars_by_symbol: dict[str, list[list[float]]] = {}
    fetch_errors: dict[str, str] = {}
    for coin, symbol in symbol_by_coin.items():
        try:
            bars_by_symbol[symbol] = fetch_ohlcv(exchange, symbol)
        except Exception as exc:  # noqa: BLE001 - artifact records provider failure
            fetch_errors[coin] = f"{type(exc).__name__}: {exc}"
            bars_by_symbol[symbol] = []

    all_labeled = positives + controls
    rows = attach_returns(all_labeled, symbol_by_coin, bars_by_symbol)
    counts_row_pos = Counter(row["coin"] for row in rows if row["is_manipulation_positive"])
    counts_row_neg = Counter(row["coin"] for row in rows if not row["is_manipulation_positive"])

    coverage: list[dict[str, Any]] = []
    for coin in SUPPORTED_COIN_HINTS:
        symbol = symbol_by_coin.get(coin, "")
        bars = bars_by_symbol.get(symbol, []) if symbol else []
        status = "ready" if counts_row_pos[coin] > 0 and counts_row_neg[coin] > 0 else "no_reconstructed_rows"
        if coin in fetch_errors:
            status = f"provider_error:{fetch_errors[coin][:80]}"
        elif not symbol:
            status = "unsupported_symbol"
        elif not bars:
            status = "no_provider_bars"
        coverage.append(
            {
                "coin": coin,
                "symbol": symbol,
                "positive_events": counts_pos[coin],
                "control_events": counts_neg[coin],
                "bars": len(bars),
                "positive_rows": counts_row_pos[coin],
                "control_rows": counts_row_neg[coin],
                "status": status,
            }
        )

    summary = summarize(rows, coverage)
    report = {
        **summary,
        "accepted_source": "mehrnoom_telegram_pump_events",
        "source_artifact": str(COIN_PUMP),
        "coverage": coverage,
        "artifacts": {
            "report_json": rel(REPORT_JSON),
            "report_md": rel(REPORT_MD),
            "rows_csv": rel(ROWS_CSV),
            "coverage_csv": rel(COVERAGE_CSV),
            "assertions": rel(ASSERTIONS),
        },
    }

    row_fields = [
        "row_id",
        "run_id",
        "coin",
        "provider_symbol",
        "quote",
        "event_dt",
        "entry_ts",
        "exit_ts_6h",
        "exit_ts_24h",
        "entry_open",
        "exit_close_6h",
        "exit_close_24h",
        "return_6h",
        "return_24h",
        "is_manipulation_positive",
        "target",
        "label_source",
        "source",
        "provider",
        "bridge_precision",
        "parent_regime_root",
        "regime_profit_branch_path",
    ]
    coverage_fields = [
        "coin",
        "symbol",
        "positive_events",
        "control_events",
        "bars",
        "positive_rows",
        "control_rows",
        "status",
    ]
    write_csv(ROWS_CSV, rows, row_fields)
    write_csv(COVERAGE_CSV, coverage, coverage_fields)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(summary, coverage)
    ASSERTIONS.write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                f"provider=ccxt.binance",
                f"positive_rows={summary['positive_rows']}",
                f"control_rows={summary['control_rows']}",
                f"monthly_folds={summary['monthly_folds']}",
                f"positive_minus_control_6h_return={summary['positive_minus_control_6h_return']:.10f}",
                f"positive_minus_control_bootstrap_lcb_5pct_6h={summary['positive_minus_control_bootstrap_lcb_5pct_6h']:.10f}",
                f"gate_result={summary['gate_result']}",
                f"direct_manipulation_rows_ready_for_future_rc_spa={summary['direct_manipulation_rows_ready_for_future_rc_spa']}",
                f"promotion_allowed_for_full_board_b={summary['promotion_allowed_for_full_board_b']}",
                f"artifacts_exist={REPORT_JSON.exists() and REPORT_MD.exists() and ROWS_CSV.exists() and COVERAGE_CSV.exists()}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
