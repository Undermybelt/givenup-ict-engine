#!/usr/bin/env python3
import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "provider-native-timeframe-acquisition-preflight-v1"
DATA_DIR = RUN_ROOT / "data" / "native"
CHECKS_DIR = RUN_ROOT / "checks"

REQUESTED_START = "2025-01-01T00:00:00Z"
REQUESTED_END = "2026-05-12T00:00:00Z"
REQUESTED_START_MS = int(datetime.fromisoformat(REQUESTED_START.replace("Z", "+00:00")).timestamp() * 1000)
REQUESTED_END_MS = int(datetime.fromisoformat(REQUESTED_END.replace("Z", "+00:00")).timestamp() * 1000)


def http_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ict-engine-board-a-provider-native-timeframe-preflight/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def iso_ms(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def write_csv(path, rows, fields):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fetch_yahoo_chart(symbol, interval):
    period1 = REQUESTED_START_MS // 1000
    period2 = REQUESTED_END_MS // 1000
    query = urllib.parse.urlencode(
        {
            "period1": period1,
            "period2": period2,
            "interval": interval,
            "includePrePost": "false",
            "events": "history",
        }
    )
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?{query}"
    payload = http_json(url)
    chart = payload.get("chart", {})
    err = chart.get("error")
    if err:
        raise RuntimeError(f"Yahoo chart error for {symbol} {interval}: {err}")
    result = (chart.get("result") or [None])[0]
    if not result:
        return []
    timestamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    rows = []
    for idx, ts in enumerate(timestamps):
        close = quote.get("close", [None] * len(timestamps))[idx]
        if close is None:
            continue
        rows.append(
            {
                "timestamp": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
                "open": quote.get("open", [None] * len(timestamps))[idx],
                "high": quote.get("high", [None] * len(timestamps))[idx],
                "low": quote.get("low", [None] * len(timestamps))[idx],
                "close": close,
                "volume": quote.get("volume", [None] * len(timestamps))[idx],
            }
        )
    return rows


def fetch_binance_klines(symbol, interval):
    rows = []
    start = REQUESTED_START_MS
    while start < REQUESTED_END_MS:
        params = urllib.parse.urlencode(
            {
                "symbol": symbol,
                "interval": interval,
                "startTime": start,
                "endTime": REQUESTED_END_MS,
                "limit": 1000,
            }
        )
        url = f"https://api.binance.com/api/v3/klines?{params}"
        batch = http_json(url)
        if not batch:
            break
        for item in batch:
            rows.append(
                {
                    "timestamp": iso_ms(int(item[0])),
                    "open": item[1],
                    "high": item[2],
                    "low": item[3],
                    "close": item[4],
                    "volume": item[5],
                    "close_time": iso_ms(int(item[6])),
                    "quote_volume": item[7],
                    "trades": item[8],
                }
            )
        next_start = int(batch[-1][0]) + 1
        if next_start <= start:
            break
        start = next_start
        time.sleep(0.15)
    return rows


def summarize_rows(provider, market, symbol, timeframe, rows, requested_span):
    first = rows[0]["timestamp"] if rows else None
    last = rows[-1]["timestamp"] if rows else None
    span_days = 0.0
    if first and last:
        dt1 = datetime.fromisoformat(first.replace("Z", "+00:00"))
        dt2 = datetime.fromisoformat(last.replace("Z", "+00:00"))
        span_days = round((dt2 - dt1).total_seconds() / 86400, 3)
    long_span = span_days >= 180 and len(rows) >= 90
    return {
        "provider": provider,
        "market": market,
        "symbol": symbol,
        "native_timeframe": timeframe,
        "requested_span": requested_span,
        "actual_first": first,
        "actual_last": last,
        "actual_span_days": span_days,
        "candle_rows": len(rows),
        "provider_native_timeframe_fetch": bool(rows),
        "long_span_candidate": long_span,
        "board_a_support": False,
        "support_reason": "data_preflight_only_no_auto_quant_pre_bayes_bbn_catboost_execution_tree",
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    requested_span = f"{REQUESTED_START}_to_{REQUESTED_END}"

    fetch_specs = [
        ("yfinance/YF", "equity", "SPY", "1d", lambda: fetch_yahoo_chart("SPY", "1d")),
        ("Binance", "crypto", "BTCUSDT", "4h", lambda: fetch_binance_klines("BTCUSDT", "4h")),
        ("Binance", "crypto", "BTCUSDT", "1d", lambda: fetch_binance_klines("BTCUSDT", "1d")),
    ]
    summaries = []
    errors = []
    for provider, market, symbol, timeframe, fetcher in fetch_specs:
        try:
            rows = fetcher()
            safe_name = f"{provider.replace('/', '_').replace(' ', '_').lower()}_{symbol.lower()}_{timeframe}_native.csv"
            fields = list(rows[0].keys()) if rows else ["timestamp", "open", "high", "low", "close", "volume"]
            write_csv(DATA_DIR / safe_name, rows, fields)
            summaries.append(summarize_rows(provider, market, symbol, timeframe, rows, requested_span))
        except Exception as exc:
            errors.append(
                {
                    "provider": provider,
                    "market": market,
                    "symbol": symbol,
                    "native_timeframe": timeframe,
                    "error": str(exc),
                }
            )
            summaries.append(
                {
                    "provider": provider,
                    "market": market,
                    "symbol": symbol,
                    "native_timeframe": timeframe,
                    "requested_span": requested_span,
                    "actual_first": None,
                    "actual_last": None,
                    "actual_span_days": 0.0,
                    "candle_rows": 0,
                    "provider_native_timeframe_fetch": False,
                    "long_span_candidate": False,
                    "board_a_support": False,
                    "support_reason": "fetch_failed_data_preflight_only",
                }
            )

    native_fetch_count = sum(1 for row in summaries if row["provider_native_timeframe_fetch"])
    long_span_count = sum(1 for row in summaries if row["long_span_candidate"])
    result = {
        "run_id": "20260512T195307+0800-codex-provider-native-timeframe-acquisition-preflight-v1",
        "gate": "preflight_only_not_board_a_support",
        "requested_start": REQUESTED_START,
        "requested_end": REQUESTED_END,
        "rows": summaries,
        "errors": errors,
        "native_fetch_count": native_fetch_count,
        "long_span_count": long_span_count,
        "accepted_95_contexts_added": 0,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "next_action": "Use these native timeframe rows only as upstream coverage evidence; rerun the full provider/AQ/Pre-Bayes/BBN/CatBoost/execution-tree chain only after feedback maturity can be generated honestly.",
    }

    summary_json = OUT_DIR / "provider_native_timeframe_acquisition_preflight_v1.json"
    summary_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_csv(
        OUT_DIR / "provider_native_timeframe_inventory_v1.csv",
        summaries,
        [
            "provider",
            "market",
            "symbol",
            "native_timeframe",
            "requested_span",
            "actual_first",
            "actual_last",
            "actual_span_days",
            "candle_rows",
            "provider_native_timeframe_fetch",
            "long_span_candidate",
            "board_a_support",
            "support_reason",
        ],
    )
    md = [
        "# Provider-Native Timeframe Acquisition Preflight v1",
        "",
        f"- Requested span: `{requested_span}`.",
        f"- Provider-native timeframe fetches: `{native_fetch_count}/3`.",
        f"- Long-span native candidates: `{long_span_count}/3`.",
        "- Accepted 95 contexts added: `0`.",
        "- Promotion allowed: `false`.",
        "- Trade usable: `false`.",
        "",
        "## Rows",
        "",
        "| Provider | Symbol | Native TF | Actual First | Actual Last | Rows | Span Days | Native Fetch | Long Span |",
        "|---|---|---:|---|---|---:|---:|---|---|",
    ]
    for row in summaries:
        md.append(
            f"| `{row['provider']}` | `{row['symbol']}` | `{row['native_timeframe']}` | "
            f"`{row['actual_first']}` | `{row['actual_last']}` | {row['candle_rows']} | "
            f"{row['actual_span_days']} | {row['provider_native_timeframe_fetch']} | {row['long_span_candidate']} |"
        )
    md += [
        "",
        "## Interpretation",
        "",
        "- This root is data preflight only. It does not run Auto-Quant, Pre-Bayes, BBN, CatBoost/path-ranker, or execution-tree admission.",
        "- Native timeframe coverage can remove one blocker from `193417`, but it does not prove per-regime calibrated `>=95%` confidence.",
        "- Board A remains fail-closed until the full chain has enough mature feedback/target rows and execution candidates leave observe/no-trade.",
    ]
    if errors:
        md += ["", "## Fetch Errors", ""]
        for err in errors:
            md.append(f"- `{err['provider']} {err['symbol']} {err['native_timeframe']}`: `{err['error']}`")
    (OUT_DIR / "provider_native_timeframe_acquisition_preflight_v1.md").write_text("\n".join(md) + "\n")

    assertions = [
        f"PASS native_timeframe_fetches={native_fetch_count}_of_3" if native_fetch_count else "FAIL_CLOSED native_timeframe_fetches=0_of_3",
        f"PASS long_span_native_candidates={long_span_count}_of_3" if long_span_count else "FAIL_CLOSED long_span_native_candidates=0_of_3",
        "PASS accepted_95_contexts_added=0",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECKS_DIR / "provider_native_timeframe_acquisition_preflight_v1_assertions.out").write_text("\n".join(assertions) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
