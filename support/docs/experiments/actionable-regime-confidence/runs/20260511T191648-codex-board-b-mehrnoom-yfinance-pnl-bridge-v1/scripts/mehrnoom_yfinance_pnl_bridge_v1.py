#!/usr/bin/env python3
"""Mehrnoom direct-event yfinance daily PnL bridge.

This additive Board B diagnostic reconstructs daily close-to-next-close
returns for accepted Mehrnoom Telegram pump-event rows where yfinance has
historical crypto coverage. It is not promotion-grade RC-SPA evidence because
the source itself does not provide executable entry/exit PnL and the provider
bridge is daily, not intraday.
"""

from __future__ import annotations

import csv
import json
import math
import random
from bisect import bisect_left
from collections import Counter
from datetime import timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf


RUN_ID = "20260511T191648+0800-codex-board-b-mehrnoom-yfinance-pnl-bridge-v1"
RUN_SLUG = "20260511T191648-codex-board-b-mehrnoom-yfinance-pnl-bridge-v1"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_SLUG
OUT_DIR = RUN_ROOT / "mehrnoom-yfinance-pnl-bridge"
CHECK_DIR = RUN_ROOT / "checks"

RAW_ROOT = Path("/private/tmp/ict-regime-mehrnoom-pump-dump")
COIN_PUMP = RAW_ROOT / "Telegram/classified/coin-pump.csv"

REPORT_JSON = OUT_DIR / "mehrnoom_yfinance_pnl_bridge_v1.json"
REPORT_MD = OUT_DIR / "mehrnoom_yfinance_pnl_bridge_v1.md"
ROWS_CSV = OUT_DIR / "mehrnoom_yfinance_pnl_rows_v1.csv"
COIN_CSV = OUT_DIR / "mehrnoom_yfinance_coin_coverage_v1.csv"
ASSERTIONS = CHECK_DIR / "mehrnoom_yfinance_pnl_bridge_v1_assertions.out"

COIN_TO_YF = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "XRP": "XRP-USD",
    "ADA": "ADA-USD",
    "ETC": "ETC-USD",
    "TRX": "TRX-USD",
    "OMG": "OMG-USD",
    "LSK": "LSK-USD",
    "XLM": "XLM-USD",
    "BAT": "BAT-USD",
    "ZRX": "ZRX-USD",
    "LTC": "LTC-USD",
    "DASH": "DASH-USD",
    "NEO": "NEO-USD",
    "XEM": "XEM-USD",
    "SC": "SC-USD",
    "DGB": "DGB-USD",
    "STORJ": "STORJ-USD",
    "WAVES": "WAVES-USD",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def clean_coin(value: object) -> str:
    return str(value).strip().upper().replace("$", "")


def load_positive_events() -> pd.DataFrame:
    df = pd.read_csv(COIN_PUMP)
    required = ["Channel ID", "Message ID", "Date", "Time", "Coin"]
    missing = [item for item in required if item not in df.columns]
    if missing:
        raise RuntimeError(f"coin-pump.csv missing columns: {missing}")
    df = df[required].copy()
    df["coin"] = df["Coin"].map(clean_coin)
    df["dt"] = pd.to_datetime(df["Date"].astype(str) + " " + df["Time"].astype(str), errors="coerce")
    df = df[df["dt"].notna() & df["coin"].ne("")]
    df = df.drop_duplicates(["Channel ID", "Message ID", "dt", "coin"])
    df = df.rename(columns={"Channel ID": "channel_id", "Message ID": "message_id"})
    df["source"] = "Mehrnoom_Mirtaheri_Telegram_coin_pump_csv"
    df["label_source"] = "classified_telegram_pump_attempt"
    df["target"] = 1
    return df[["channel_id", "message_id", "coin", "dt", "source", "label_source", "target"]]


def build_negative_controls(pos: pd.DataFrame) -> pd.DataFrame:
    rng = random.Random(20260511191648)
    by_coin_times = {
        coin: sorted(group["dt"].dt.to_pydatetime())
        for coin, group in pos.groupby("coin")
    }

    def near_event(times: list[Any], trial: Any, seconds: int = 24 * 3600) -> bool:
        index = bisect_left(times, trial)
        if index < len(times) and abs((times[index] - trial).total_seconds()) <= seconds:
            return True
        if index > 0 and abs((trial - times[index - 1]).total_seconds()) <= seconds:
            return True
        return False

    global_min = pos["dt"].min().to_pydatetime()
    global_max = pos["dt"].max().to_pydatetime()
    offsets_hours = [72, -72, 168, -168, 336, -336, 24, -24, 720, -720]
    rows: list[dict[str, Any]] = []
    for idx, row in pos.iterrows():
        base_dt = row["dt"].to_pydatetime()
        coin_times = by_coin_times[row["coin"]]
        candidate = None
        for hours in offsets_hours:
            trial = base_dt + timedelta(hours=hours)
            if trial < global_min or trial > global_max:
                continue
            if not near_event(coin_times, trial):
                candidate = trial
                break
        if candidate is None:
            for _ in range(24):
                span = int((global_max - global_min).total_seconds())
                trial = global_min + timedelta(seconds=rng.randrange(max(span, 1)))
                if not near_event(coin_times, trial):
                    candidate = trial
                    break
        if candidate is None:
            continue
        rows.append(
            {
                "channel_id": int(row["channel_id"]),
                "message_id": f"negative_control_for_{int(row['message_id'])}_{idx}",
                "coin": row["coin"],
                "dt": pd.Timestamp(candidate),
                "source": "synthetic_same_coin_non_event_control",
                "label_source": "no_classified_telegram_pump_attempt_within_24h",
                "target": 0,
            }
        )
    return pd.DataFrame(rows)


def normalized_download(ticker: str) -> pd.DataFrame:
    data = yf.download(
        ticker,
        start="2017-05-01",
        end="2018-08-15",
        interval="1d",
        progress=False,
        auto_adjust=False,
        threads=False,
    )
    if data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]
    required = {"Open", "Close"}
    if not required.issubset(set(data.columns)):
        return pd.DataFrame()
    out = data.reset_index().rename(columns={"Date": "date"})
    out["date"] = pd.to_datetime(out["date"]).dt.tz_localize(None).dt.normalize()
    out = out[["date", "Open", "Close"]].dropna()
    out = out.sort_values("date").reset_index(drop=True)
    return out


def attach_returns(panel: pd.DataFrame, prices_by_coin: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    row_id = 0
    for _, event in panel.sort_values("dt").iterrows():
        coin = str(event["coin"])
        prices = prices_by_coin.get(coin)
        if prices is None or prices.empty:
            continue
        event_date = pd.Timestamp(event["dt"]).normalize()
        dates = list(prices["date"])
        pos = bisect_left(dates, event_date)
        if pos >= len(prices) or prices.iloc[pos]["date"] != event_date:
            continue
        exit_pos = pos + 1
        if exit_pos >= len(prices):
            continue
        entry_close = float(prices.iloc[pos]["Close"])
        exit_close = float(prices.iloc[exit_pos]["Close"])
        if entry_close <= 0.0 or math.isnan(entry_close) or math.isnan(exit_close):
            continue
        event_return = exit_close / entry_close - 1.0
        row_id += 1
        target = int(event["target"])
        rows.append(
            {
                "row_id": row_id,
                "run_id": RUN_ID,
                "coin": coin,
                "provider_symbol": COIN_TO_YF[coin],
                "event_dt": pd.Timestamp(event["dt"]).isoformat(),
                "event_date": event_date.date().isoformat(),
                "entry_date": prices.iloc[pos]["date"].date().isoformat(),
                "exit_date": prices.iloc[exit_pos]["date"].date().isoformat(),
                "entry_close": entry_close,
                "exit_close": exit_close,
                "event_next_day_return": event_return,
                "is_manipulation_positive": target == 1,
                "target": target,
                "label_source": event["label_source"],
                "source": event["source"],
                "provider": "yfinance",
                "bridge_precision": "daily_close_to_next_close_not_intraday",
                "parent_regime_root": "Manipulation(scoped)" if target == 1 else "Control(non_event)",
                "regime_profit_branch_path": (
                    "Manipulation(scoped) -> DirectEventOverlay -> "
                    "TelegramPumpEventYfinanceDailyPnlBridge -> suppress_or_abstain"
                    if target == 1
                    else "Control(non_event) -> SameCoinNonEvent -> YfinanceDailyPnlBridge -> baseline"
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


def bootstrap_lcb(values: list[float], samples: int = 2000) -> float:
    if not values:
        return 0.0
    state = 11
    means: list[float] = []
    n = len(values)
    for _ in range(samples):
        total = 0.0
        for _ in range(n):
            state = (1103515245 * state + 12345) % (2**31)
            total += values[state % n]
        means.append(total / n)
    return percentile(means, 0.05)


def summarize(rows: list[dict[str, Any]], coin_coverage: list[dict[str, Any]]) -> dict[str, Any]:
    pos = [row for row in rows if row["is_manipulation_positive"]]
    neg = [row for row in rows if not row["is_manipulation_positive"]]
    pos_returns = [float(row["event_next_day_return"]) for row in pos]
    neg_returns = [float(row["event_next_day_return"]) for row in neg]
    folds = sorted({str(row["entry_date"])[:7] for row in pos})
    fold_sums = []
    for fold in folds:
        vals = [float(row["event_next_day_return"]) for row in pos if str(row["entry_date"]).startswith(fold)]
        fold_sums.append(sum(vals))
    fold_positive_rate = sum(1 for value in fold_sums if value > 0.0) / len(fold_sums) if fold_sums else 0.0
    return {
        "positive_rows": len(pos),
        "control_rows": len(neg),
        "coins_with_price_rows": sum(1 for row in coin_coverage if row["download_rows"] > 0),
        "positive_mean_next_day_return": sum(pos_returns) / len(pos_returns) if pos_returns else 0.0,
        "control_mean_next_day_return": sum(neg_returns) / len(neg_returns) if neg_returns else 0.0,
        "positive_minus_control_mean_return": (
            (sum(pos_returns) / len(pos_returns)) - (sum(neg_returns) / len(neg_returns))
            if pos_returns and neg_returns
            else 0.0
        ),
        "positive_bootstrap_lcb_5pct": bootstrap_lcb(pos_returns),
        "positive_win_rate": sum(1 for value in pos_returns if value > 0.0) / len(pos_returns) if pos_returns else 0.0,
        "folds_monthly": len(folds),
        "fold_positive_rate_monthly": fold_positive_rate,
        "tail_loss_p95": abs(percentile(pos_returns, 0.05)) if pos_returns else 0.0,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_md(report: dict[str, Any]) -> None:
    decision = report["decision"]
    summary = report["summary"]
    lines = [
        "# Mehrnoom Yfinance PnL Bridge v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Provider rows: `{decision['provider_reconstructed_rows']}`",
        f"- Positive event rows: `{summary['positive_rows']}`",
        f"- Control rows: `{summary['control_rows']}`",
        f"- Positive mean next-day return: `{summary['positive_mean_next_day_return']:.6f}`",
        f"- Control mean next-day return: `{summary['control_mean_next_day_return']:.6f}`",
        f"- Monthly folds: `{summary['folds_monthly']}`",
        f"- Promotion allowed: `{decision['promotion_allowed']}`",
        "",
        "## Why It Stays Diagnostic",
        "",
        "- This uses yfinance daily close-to-next-close bars, not the source-owned Telegram price sidecar and not intraday execution prices.",
        "- It repairs provider-reconstructability for a subset of accepted direct events, but does not make the direct event source itself trade-usable.",
        "- Scoped Manipulation should still route to suppression/abstain until an executable entry/exit bridge is accepted.",
        "",
        "## Coin Coverage",
        "",
        "| Coin | Ticker | Events | Controls | Download Rows | Reconstructed Rows |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in report["coin_coverage"]:
        lines.append(
            f"| `{row['coin']}` | `{row['ticker']}` | {row['positive_events']} | "
            f"{row['control_events']} | {row['download_rows']} | {row['reconstructed_rows']} |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{rel(REPORT_JSON)}`",
            f"- Rows CSV: `{rel(ROWS_CSV)}`",
            f"- Coin coverage CSV: `{rel(COIN_CSV)}`",
            f"- Assertions: `{rel(ASSERTIONS)}`",
            "",
            "## Next",
            "",
            f"- {decision['next_action']}",
        ]
    )
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    if not COIN_PUMP.exists():
        raise FileNotFoundError(COIN_PUMP)

    pos = load_positive_events()
    neg = build_negative_controls(pos)
    panel = pd.concat([pos, neg], ignore_index=True, sort=False)
    top_counts = Counter(pos["coin"]).most_common(40)
    candidate_coins = [coin for coin, _ in top_counts if coin in COIN_TO_YF]

    prices_by_coin: dict[str, pd.DataFrame] = {}
    coin_coverage: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for coin in candidate_coins:
        ticker = COIN_TO_YF[coin]
        prices = normalized_download(ticker)
        prices_by_coin[coin] = prices
        partial_rows = attach_returns(panel[panel["coin"] == coin], {coin: prices})
        rows.extend(partial_rows)
        coin_coverage.append(
            {
                "coin": coin,
                "ticker": ticker,
                "positive_events": int((panel["coin"].eq(coin) & panel["target"].eq(1)).sum()),
                "control_events": int((panel["coin"].eq(coin) & panel["target"].eq(0)).sum()),
                "download_rows": int(len(prices)),
                "price_start": str(prices["date"].min().date()) if len(prices) else "",
                "price_end": str(prices["date"].max().date()) if len(prices) else "",
                "reconstructed_rows": int(len(partial_rows)),
            }
        )

    summary = summarize(rows, coin_coverage)
    decision = {
        "gate_result": "diagnostic_only:yfinance_daily_pnl_bridge_not_promotion_grade",
        "provider_reconstructed_rows": len(rows),
        "board_b_profitability_rows_added": 0,
        "promotion_allowed": False,
        "downstream_consumption": "not_started:daily_bridge_not_intraday_or_source_owned_pnl",
        "primary_blocker": "provider-reconstructed daily PnL is useful bridge evidence, but not source-owned/intraday execution PnL.",
        "next_action": "If this branch is reused, rebuild with intraday provider bars or source-owned entry/exit prices and then run branch RC-SPA with matched controls.",
    }
    report = {
        "schema_version": "board-b-mehrnoom-yfinance-pnl-bridge/v1",
        "run_id": RUN_ID,
        "source": {
            "raw_root": str(RAW_ROOT),
            "coin_pump_csv": str(COIN_PUMP),
            "direct_source": "Mehrnoom/Mirtaheri Telegram pump-event labels",
            "provider_bridge": "yfinance daily OHLCV",
        },
        "candidate_coins": candidate_coins,
        "coin_coverage": coin_coverage,
        "summary": summary,
        "decision": decision,
        "completion": {
            "runtime_code_changed": False,
            "auto_quant_checkout_changed": False,
            "raw_data_committed": False,
            "thresholds_relaxed": False,
            "board_b_cursor_superseded": False,
        },
        "artifacts": {
            "json": rel(REPORT_JSON),
            "md": rel(REPORT_MD),
            "rows_csv": rel(ROWS_CSV),
            "coin_csv": rel(COIN_CSV),
            "assertions": rel(ASSERTIONS),
        },
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    write_csv(ROWS_CSV, rows)
    write_csv(COIN_CSV, coin_coverage)
    write_md(report)
    assertions = [
        f"run_id={RUN_ID}",
        f"candidate_coins={len(candidate_coins)}",
        f"provider_reconstructed_rows={len(rows)}",
        f"positive_rows={summary['positive_rows']}",
        f"control_rows={summary['control_rows']}",
        f"gate_result={decision['gate_result']}",
        f"promotion_allowed={decision['promotion_allowed']}",
        f"report_md={rel(REPORT_MD)}",
    ]
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "decision": decision, "summary": summary, "report": rel(REPORT_MD)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
