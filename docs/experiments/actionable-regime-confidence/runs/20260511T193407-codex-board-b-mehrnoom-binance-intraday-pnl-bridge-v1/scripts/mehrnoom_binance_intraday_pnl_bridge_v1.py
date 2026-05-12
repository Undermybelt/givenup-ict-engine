#!/usr/bin/env python3
"""Mehrnoom direct-event intraday PnL bridge.

This additive Board B diagnostic uses source-extracted Telegram buy levels
as candidate entries and Binance public 1h candles as provider-reconstructed
intraday exits. It is a bridge artifact, not a downstream promotion.
"""

from __future__ import annotations

import ast
import csv
import json
import math
import random
import time
from bisect import bisect_left
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd
import requests


RUN_ID = "20260511T193407+0800-codex-board-b-mehrnoom-binance-intraday-pnl-bridge-v1"
RUN_SLUG = "20260511T193407-codex-board-b-mehrnoom-binance-intraday-pnl-bridge-v1"

HORIZON_HOURS = 6
MIN_BUY_OPEN_RATIO = 0.50
MAX_BUY_OPEN_RATIO = 1.50
MAX_SYMBOLS = 20
MIN_EVENTS_PER_SYMBOL = 50


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_SLUG
OUT_DIR = RUN_ROOT / "mehrnoom-binance-intraday-pnl-bridge"
CHECK_DIR = RUN_ROOT / "checks"

RAW_ROOT = Path("/private/tmp/ict-regime-mehrnoom-pumpdump-sparse")
if not (RAW_ROOT / "Telegram/classified/price_extract.csv").exists():
    RAW_ROOT = Path("/private/tmp/ict-regime-mehrnoom-pump-dump")

PRICE_EXTRACT = RAW_ROOT / "Telegram/classified/price_extract.csv"
COIN_PUMP = RAW_ROOT / "Telegram/classified/coin-pump.csv"

REPORT_JSON = OUT_DIR / "mehrnoom_binance_intraday_pnl_bridge_v1.json"
REPORT_MD = OUT_DIR / "mehrnoom_binance_intraday_pnl_bridge_v1.md"
ROWS_CSV = OUT_DIR / "mehrnoom_binance_intraday_pnl_rows_v1.csv"
SYMBOL_CSV = OUT_DIR / "mehrnoom_binance_symbol_coverage_v1.csv"
PROVIDER_JSON = OUT_DIR / "mehrnoom_binance_provider_probe_v1.json"
ASSERTIONS = CHECK_DIR / "mehrnoom_binance_intraday_pnl_bridge_v1_assertions.out"

BINANCE_EXCHANGE_INFO = "https://api.binance.com/api/v3/exchangeInfo"
BINANCE_KLINES = "https://api.binance.com/api/v3/klines"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def clean_coin(value: object) -> str:
    return str(value).strip().upper().replace("$", "")


def parse_buy_levels(value: object) -> list[float]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    text = str(value).strip()
    if not text or text == "[]":
        return []
    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return []
    if not isinstance(parsed, list):
        parsed = [parsed]
    levels: list[float] = []
    for item in parsed:
        try:
            number = float(item)
        except (TypeError, ValueError):
            continue
        if 0.0 < number < 1.0:
            levels.append(number)
    return levels


def load_price_events() -> pd.DataFrame:
    df = pd.read_csv(PRICE_EXTRACT)
    required = ["Channel ID", "Message ID", "Date", "Time", "Coin", "Buy"]
    missing = [item for item in required if item not in df.columns]
    if missing:
        raise RuntimeError(f"price_extract.csv missing columns: {missing}")
    df = df[required].copy()
    df["coin"] = df["Coin"].map(clean_coin)
    df["event_dt"] = pd.to_datetime(
        df["Date"].astype(str) + " " + df["Time"].astype(str),
        errors="coerce",
        utc=True,
    )
    df["buy_levels"] = df["Buy"].map(parse_buy_levels)
    df = df[df["event_dt"].notna() & df["coin"].ne("")]
    df = df[df["buy_levels"].map(bool)]
    df = df.drop_duplicates(["Channel ID", "Message ID", "event_dt", "coin"])
    df = df.rename(columns={"Channel ID": "channel_id", "Message ID": "message_id"})
    return df[["channel_id", "message_id", "coin", "event_dt", "buy_levels"]]


def load_coin_pump_events() -> pd.DataFrame:
    df = pd.read_csv(COIN_PUMP)
    required = ["Channel ID", "Message ID", "Date", "Time", "Coin"]
    missing = [item for item in required if item not in df.columns]
    if missing:
        raise RuntimeError(f"coin-pump.csv missing columns: {missing}")
    df = df[required].copy()
    df["coin"] = df["Coin"].map(clean_coin)
    df["event_dt"] = pd.to_datetime(
        df["Date"].astype(str) + " " + df["Time"].astype(str),
        errors="coerce",
        utc=True,
    )
    df = df[df["event_dt"].notna() & df["coin"].ne("")]
    return df.rename(columns={"Channel ID": "channel_id", "Message ID": "message_id"})[
        ["channel_id", "message_id", "coin", "event_dt"]
    ]


def binance_btc_symbols() -> set[str]:
    response = requests.get(BINANCE_EXCHANGE_INFO, timeout=30)
    response.raise_for_status()
    payload = response.json()
    return {
        item["symbol"]
        for item in payload.get("symbols", [])
        if item.get("status") == "TRADING" and str(item.get("symbol", "")).endswith("BTC")
    }


def choose_symbols(events: pd.DataFrame, symbols: set[str]) -> list[dict[str, Any]]:
    counts = Counter(events["coin"])
    candidates: list[dict[str, Any]] = []
    for coin, count in counts.most_common():
        symbol = f"{coin}BTC"
        if symbol in symbols and count >= MIN_EVENTS_PER_SYMBOL:
            candidates.append({"coin": coin, "symbol": symbol, "source_buy_rows": int(count)})
        if len(candidates) >= MAX_SYMBOLS:
            break
    return candidates


def fetch_klines(symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.DataFrame, str]:
    rows: list[list[Any]] = []
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    interval_ms = 60 * 60 * 1000
    status = "ok"
    while start_ms < end_ms:
        params = {
            "symbol": symbol,
            "interval": "1h",
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": 1000,
        }
        try:
            response = requests.get(BINANCE_KLINES, params=params, timeout=30)
            response.raise_for_status()
            chunk = response.json()
        except Exception as exc:  # noqa: BLE001 - report provider failures.
            status = f"provider_error:{type(exc).__name__}:{str(exc)[:160]}"
            break
        if not isinstance(chunk, list) or not chunk:
            break
        rows.extend(chunk)
        last_open = int(chunk[-1][0])
        next_start = last_open + interval_ms
        if next_start <= start_ms:
            status = "blocked:non_advancing_provider_cursor"
            break
        start_ms = next_start
        time.sleep(0.035)
    if not rows:
        return pd.DataFrame(), status if status != "ok" else "no_rows"
    df = pd.DataFrame(
        rows,
        columns=[
            "open_time_ms",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time_ms",
            "quote_volume",
            "trade_count",
            "taker_base_volume",
            "taker_quote_volume",
            "ignore",
        ],
    )
    for column in ["open", "high", "low", "close", "volume"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["open_dt"] = pd.to_datetime(df["open_time_ms"], unit="ms", utc=True)
    df = df[["open_dt", "open", "high", "low", "close", "volume"]].dropna()
    df = df.drop_duplicates(["open_dt"]).sort_values("open_dt").reset_index(drop=True)
    return df, status


def ceil_hour(ts: pd.Timestamp) -> pd.Timestamp:
    rounded = ts.floor("h")
    if rounded == ts:
        return rounded
    return rounded + pd.Timedelta(hours=1)


def aligned_source_entry(buy_levels: list[float], provider_open: float) -> tuple[float | None, float | None, int]:
    aligned = [
        level
        for level in buy_levels
        if provider_open > 0.0 and MIN_BUY_OPEN_RATIO <= level / provider_open <= MAX_BUY_OPEN_RATIO
    ]
    if not aligned:
        return None, None, 0
    entry = float(median(aligned))
    return entry, entry / provider_open, len(aligned)


def attach_positive_rows(events: pd.DataFrame, prices_by_coin: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    row_id = 0
    for _, event in events.sort_values("event_dt").iterrows():
        coin = str(event["coin"])
        prices = prices_by_coin.get(coin)
        if prices is None or prices.empty:
            continue
        entry_dt = ceil_hour(pd.Timestamp(event["event_dt"]))
        open_times = list(prices["open_dt"])
        entry_index = bisect_left(open_times, entry_dt)
        exit_index = entry_index + HORIZON_HOURS - 1
        if entry_index >= len(prices) or exit_index >= len(prices):
            continue
        entry_bar = prices.iloc[entry_index]
        exit_bar = prices.iloc[exit_index]
        provider_entry = float(entry_bar["open"])
        provider_exit = float(exit_bar["close"])
        source_entry, alignment_ratio, aligned_count = aligned_source_entry(
            list(event["buy_levels"]),
            provider_entry,
        )
        if source_entry is None or alignment_ratio is None:
            continue
        row_id += 1
        provider_return = provider_exit / provider_entry - 1.0
        source_return = provider_exit / source_entry - 1.0
        rows.append(
            {
                "row_id": row_id,
                "run_id": RUN_ID,
                "row_type": "positive_direct_event",
                "coin": coin,
                "provider_symbol": f"{coin}BTC",
                "event_dt": pd.Timestamp(event["event_dt"]).isoformat(),
                "entry_dt": pd.Timestamp(entry_bar["open_dt"]).isoformat(),
                "exit_dt": pd.Timestamp(exit_bar["open_dt"]).isoformat(),
                "horizon_hours": HORIZON_HOURS,
                "source_entry_price_btc": source_entry,
                "provider_entry_open_btc": provider_entry,
                "provider_exit_close_btc": provider_exit,
                "source_buy_return": source_return,
                "provider_open_return": provider_return,
                "entry_alignment_ratio": alignment_ratio,
                "aligned_source_buy_levels": aligned_count,
                "is_manipulation_positive": True,
                "target": 1,
                "source": "Mehrnoom_Mirtaheri_Telegram_price_extract_buy_levels",
                "provider": "binance_public_api",
                "bridge_precision": "source_buy_to_provider_1h_exit_intraday",
                "parent_regime_root": "Manipulation(scoped)",
                "regime_profit_branch_path": (
                    "Manipulation(scoped) -> TelegramPumpEvent -> "
                    "SourceBuyBinanceIntradayExit -> pnl_bridge"
                ),
            }
        )
    return rows


def build_negative_controls(pos_events: pd.DataFrame, full_events: pd.DataFrame) -> pd.DataFrame:
    rng = random.Random(20260511193407)
    by_coin_times = {
        coin: sorted(group["event_dt"].dt.to_pydatetime())
        for coin, group in full_events.groupby("coin")
    }
    global_min = full_events["event_dt"].min().to_pydatetime()
    global_max = full_events["event_dt"].max().to_pydatetime()
    offsets = [72, -72, 168, -168, 336, -336, 720, -720, 24, -24]

    def near_event(times: list[datetime], trial: datetime, seconds: int = 24 * 3600) -> bool:
        index = bisect_left(times, trial)
        if index < len(times) and abs((times[index] - trial).total_seconds()) <= seconds:
            return True
        if index > 0 and abs((trial - times[index - 1]).total_seconds()) <= seconds:
            return True
        return False

    controls: list[dict[str, Any]] = []
    for idx, event in pos_events.iterrows():
        coin = str(event["coin"])
        base_dt = pd.Timestamp(event["event_dt"]).to_pydatetime()
        coin_times = by_coin_times.get(coin, [])
        candidate = None
        for hours in offsets:
            trial = base_dt + timedelta(hours=hours)
            if global_min <= trial <= global_max and not near_event(coin_times, trial):
                candidate = trial
                break
        if candidate is None:
            span = int((global_max - global_min).total_seconds())
            for _ in range(20):
                trial = global_min + timedelta(seconds=rng.randrange(max(span, 1)))
                if not near_event(coin_times, trial):
                    candidate = trial
                    break
        if candidate is None:
            continue
        controls.append(
            {
                "channel_id": int(event["channel_id"]),
                "message_id": f"negative_control_for_{int(event['message_id'])}_{idx}",
                "coin": coin,
                "event_dt": pd.Timestamp(candidate),
            }
        )
    return pd.DataFrame(controls)


def attach_control_rows(controls: pd.DataFrame, prices_by_coin: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    row_id = 0
    for _, control in controls.sort_values("event_dt").iterrows():
        coin = str(control["coin"])
        prices = prices_by_coin.get(coin)
        if prices is None or prices.empty:
            continue
        entry_dt = ceil_hour(pd.Timestamp(control["event_dt"]))
        open_times = list(prices["open_dt"])
        entry_index = bisect_left(open_times, entry_dt)
        exit_index = entry_index + HORIZON_HOURS - 1
        if entry_index >= len(prices) or exit_index >= len(prices):
            continue
        entry_bar = prices.iloc[entry_index]
        exit_bar = prices.iloc[exit_index]
        provider_entry = float(entry_bar["open"])
        provider_exit = float(exit_bar["close"])
        if provider_entry <= 0:
            continue
        row_id += 1
        rows.append(
            {
                "row_id": row_id,
                "run_id": RUN_ID,
                "row_type": "same_coin_non_event_control",
                "coin": coin,
                "provider_symbol": f"{coin}BTC",
                "event_dt": pd.Timestamp(control["event_dt"]).isoformat(),
                "entry_dt": pd.Timestamp(entry_bar["open_dt"]).isoformat(),
                "exit_dt": pd.Timestamp(exit_bar["open_dt"]).isoformat(),
                "horizon_hours": HORIZON_HOURS,
                "source_entry_price_btc": "",
                "provider_entry_open_btc": provider_entry,
                "provider_exit_close_btc": provider_exit,
                "source_buy_return": "",
                "provider_open_return": provider_exit / provider_entry - 1.0,
                "entry_alignment_ratio": "",
                "aligned_source_buy_levels": "",
                "is_manipulation_positive": False,
                "target": 0,
                "source": "synthetic_same_coin_non_event_control",
                "provider": "binance_public_api",
                "bridge_precision": "provider_open_to_provider_1h_exit_intraday_control",
                "parent_regime_root": "Control(non_event)",
                "regime_profit_branch_path": (
                    "Control(non_event) -> SameCoinNonEvent -> "
                    "BinanceIntradayExit -> baseline"
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
    state = 193407
    n = len(values)
    means: list[float] = []
    for _ in range(samples):
        total = 0.0
        for _ in range(n):
            state = (1103515245 * state + 12345) % (2**31)
            total += values[state % n]
        means.append(total / n)
    return percentile(means, 0.05)


def summarize(rows: list[dict[str, Any]], symbol_coverage: list[dict[str, Any]]) -> dict[str, Any]:
    positives = [row for row in rows if row["is_manipulation_positive"]]
    controls = [row for row in rows if not row["is_manipulation_positive"]]
    pos_source_returns = [float(row["source_buy_return"]) for row in positives]
    pos_provider_returns = [float(row["provider_open_return"]) for row in positives]
    control_returns = [float(row["provider_open_return"]) for row in controls]
    folds = sorted({str(row["event_dt"])[:7] for row in positives})
    edge_vs_control = (
        (sum(pos_provider_returns) / len(pos_provider_returns))
        - (sum(control_returns) / len(control_returns))
        if pos_provider_returns and control_returns
        else 0.0
    )
    positive_mean_source = sum(pos_source_returns) / len(pos_source_returns) if pos_source_returns else 0.0
    positive_mean_provider = (
        sum(pos_provider_returns) / len(pos_provider_returns) if pos_provider_returns else 0.0
    )
    control_mean = sum(control_returns) / len(control_returns) if control_returns else 0.0
    promotion_allowed = False
    if not positives:
        gate = "blocked:no_aligned_source_buy_intraday_rows"
    elif len(folds) < 4:
        gate = "blocked:insufficient_monthly_folds"
    elif edge_vs_control <= 0:
        gate = "diagnostic_only:intraday_rows_reconstructed_but_no_positive_edge_vs_controls"
    else:
        gate = "research_watch:intraday_rows_reconstructed_requires_branch_rc_spa_and_downstream"
    return {
        "run_id": RUN_ID,
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "recipe_id": "MehrnoomBinanceIntradayPnlBridgeV1",
        "gate_result": gate,
        "promotion_allowed": promotion_allowed,
        "downstream_consumption": "not_started:no_rc_spa_promotion",
        "bridge_precision": "source_buy_to_binance_public_1h_exit_intraday",
        "horizon_hours": HORIZON_HOURS,
        "positive_direct_event_rows": len(positives),
        "same_coin_control_rows": len(controls),
        "symbols_attempted": len(symbol_coverage),
        "symbols_with_rows": sum(1 for item in symbol_coverage if item["provider_rows"] > 0),
        "monthly_folds": len(folds),
        "positive_mean_source_buy_return": positive_mean_source,
        "positive_mean_provider_open_return": positive_mean_provider,
        "control_mean_provider_open_return": control_mean,
        "edge_vs_control_provider_open_return": edge_vs_control,
        "positive_source_return_lcb_5pct": bootstrap_lcb(pos_source_returns),
        "positive_provider_return_lcb_5pct": bootstrap_lcb(pos_provider_returns),
        "control_return_lcb_5pct": bootstrap_lcb(control_returns),
        "source_rows_are_trade_pnl_usable": bool(positives),
        "board_b_profitability_rows_added": len(positives) if positives else 0,
        "artifact_paths": {
            "json": rel(REPORT_JSON),
            "markdown": rel(REPORT_MD),
            "rows_csv": rel(ROWS_CSV),
            "symbol_coverage_csv": rel(SYMBOL_CSV),
            "provider_probe_json": rel(PROVIDER_JSON),
            "assertions": rel(ASSERTIONS),
        },
        "next_action": (
            "Use these intraday provider-reconstructed direct rows only as scoped "
            "Manipulation bridge input; run full branch RC-SPA and downstream checks "
            "only if combined root branches pass without relaxed gates."
        ),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(summary: dict[str, Any], symbol_coverage: list[dict[str, Any]]) -> None:
    REPORT_JSON.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    PROVIDER_JSON.write_text(
        json.dumps(
            {
                "provider": "binance_public_api",
                "source_root": str(RAW_ROOT),
                "price_extract": str(PRICE_EXTRACT),
                "symbols": symbol_coverage,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    symbol_rows = []
    for item in symbol_coverage:
        symbol_rows.append(
            {
                "coin": item["coin"],
                "symbol": item["symbol"],
                "source_buy_rows": item["source_buy_rows"],
                "provider_rows": item["provider_rows"],
                "first_provider_dt": item.get("first_provider_dt", ""),
                "last_provider_dt": item.get("last_provider_dt", ""),
                "status": item["status"],
            }
        )
    write_csv(SYMBOL_CSV, symbol_rows)
    lines = [
        "# Mehrnoom Binance Intraday PnL Bridge v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"- Gate result: `{summary['gate_result']}`",
        f"- Positive direct-event rows: `{summary['positive_direct_event_rows']}`",
        f"- Same-coin control rows: `{summary['same_coin_control_rows']}`",
        f"- Monthly folds: `{summary['monthly_folds']}`",
        f"- Source-buy mean return: `{summary['positive_mean_source_buy_return']:.6f}`",
        f"- Provider-open positive mean return: `{summary['positive_mean_provider_open_return']:.6f}`",
        f"- Provider-open control mean return: `{summary['control_mean_provider_open_return']:.6f}`",
        f"- Edge vs controls: `{summary['edge_vs_control_provider_open_return']:.6f}`",
        f"- Promotion allowed: `{summary['promotion_allowed']}`",
        "",
        "## Interpretation",
        "",
        "- This repairs the previous all-zero direct scoped `Manipulation` PnL-input blocker only as an additive bridge: source Telegram buy levels are used for entry alignment, and Binance public 1h candles provide intraday exits.",
        "- It does not promote downstream because this run is not a full RC-SPA candidate across all required roots, and it has not passed Pre-Bayes, BBN, CatBoost/path-ranker, or execution-tree consumption.",
        "- Rows with source buy levels that do not align to the provider entry open are rejected instead of coerced.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{rel(REPORT_JSON)}`",
        f"- Rows CSV: `{rel(ROWS_CSV)}`",
        f"- Symbol coverage CSV: `{rel(SYMBOL_CSV)}`",
        f"- Provider probe JSON: `{rel(PROVIDER_JSON)}`",
        f"- Assertions: `{rel(ASSERTIONS)}`",
        "",
        "## Next",
        "",
        f"- {summary['next_action']}",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    price_events = load_price_events()
    coin_events = load_coin_pump_events()
    symbols = binance_btc_symbols()
    selected = choose_symbols(price_events, symbols)
    if not selected:
        raise RuntimeError("no eligible Binance BTC symbols for source-buy rows")
    start = price_events["event_dt"].min() - pd.Timedelta(hours=HORIZON_HOURS + 2)
    end = price_events["event_dt"].max() + pd.Timedelta(hours=HORIZON_HOURS + 2)
    prices_by_coin: dict[str, pd.DataFrame] = {}
    symbol_coverage: list[dict[str, Any]] = []
    for item in selected:
        prices, status = fetch_klines(item["symbol"], start, end)
        if not prices.empty:
            prices_by_coin[item["coin"]] = prices
        symbol_coverage.append(
            {
                **item,
                "provider_rows": int(len(prices)),
                "first_provider_dt": prices["open_dt"].min().isoformat() if not prices.empty else "",
                "last_provider_dt": prices["open_dt"].max().isoformat() if not prices.empty else "",
                "status": status,
            }
        )
    eligible_events = price_events[price_events["coin"].isin(prices_by_coin.keys())].copy()
    positive_rows = attach_positive_rows(eligible_events, prices_by_coin)
    aligned_keys = {
        (row["coin"], row["event_dt"])
        for row in positive_rows
    }
    aligned_events = eligible_events[
        eligible_events.apply(
            lambda row: (str(row["coin"]), pd.Timestamp(row["event_dt"]).isoformat()) in aligned_keys,
            axis=1,
        )
    ].copy()
    controls = build_negative_controls(aligned_events, coin_events)
    control_rows = attach_control_rows(controls, prices_by_coin)
    all_rows = positive_rows + control_rows
    write_csv(ROWS_CSV, all_rows)
    summary = summarize(all_rows, symbol_coverage)
    write_report(summary, symbol_coverage)
    assertions = [
        f"positive_direct_event_rows={summary['positive_direct_event_rows']}",
        f"same_coin_control_rows={summary['same_coin_control_rows']}",
        f"monthly_folds={summary['monthly_folds']}",
        f"gate_result={summary['gate_result']}",
        f"promotion_allowed={summary['promotion_allowed']}",
        f"downstream_consumption={summary['downstream_consumption']}",
    ]
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
