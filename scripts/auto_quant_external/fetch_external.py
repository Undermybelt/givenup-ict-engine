"""
fetch_external.py — multi-asset data fetcher that emits canonical OHLCV CSV
consumable by `prepare_external.py`, plus an option-chain dumper for use cases
that don't fit FreqTrade's IStrategy model.

Providers (sub-commands):
  yahoo       OHLCV for stocks/ETFs/futures/forex/index/crypto via Yahoo Finance
              chart API (no API key, no extra deps beyond requests/pandas).
              Symbol cheat-sheet:
                stock/ETF       AAPL, SPY, QQQ, VTI
                index           ^GSPC, ^NDX, ^DJI, ^VIX
                US futures      ES=F (S&P), NQ=F (NDX), GC=F (gold), CL=F (oil)
                forex/CFD       EURUSD=X, GBPUSD=X, USDJPY=X
                crypto          BTC-USD, ETH-USD, SOL-USD

  nse-options Option-chain snapshot from NSE India (indices/equity).
              Distilled from VarunS2002/Python-NSE-Option-Chain-Analyzer's
              network layer; needs Indian-routable IP (Akamai geofence).
              Output is wide CSV: strike x [call_oi, call_iv, call_ltp,
              call_chng_oi, put_oi, put_iv, put_ltp, put_chng_oi] for one
              expiry snapshot. NOT directly backtestable by FreqTrade.

  polygon     Stocks/ETFs/options/crypto/forex via Polygon.io REST API.
              Requires POLYGON_API_KEY env var. Skeleton, not exercised
              by default demo because of the paid key requirement.

Architectural note: this script's job is FETCH + WRITE-CANONICAL-CSV.
Data cleaning, resampling, and feather conversion live in prepare_external.py.
Two stages, two tools, no entanglement.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"
YAHOO_INTERVAL_MAP = {
    "1m": "1m",
    "2m": "2m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "60m",
    "60m": "60m",
    "90m": "90m",
    "1d": "1d",
    "1wk": "1wk",
    "1mo": "1mo",
}
YAHOO_DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)
YAHOO_UA_ROTATION = [
    YAHOO_DEFAULT_UA,
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

NSE_HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    "accept-language": "en,gu;q=0.9,hi;q=0.8",
    "accept-encoding": "gzip, deflate, br",
    "accept": "*/*",
}
NSE_URL_HOME = "https://www.nseindia.com/option-chain"
NSE_URL_SYMBOLS = "https://www.nseindia.com/api/underlying-information"
NSE_URL_INDEX = "https://www.nseindia.com/api/option-chain-v3?type=Indices&symbol={symbol}&expiry={expiry}"
NSE_URL_EQUITY = "https://www.nseindia.com/api/option-chain-v3?type=Equity&symbol={symbol}&expiry={expiry}"


# ---------------------------------------------------------------------------
# Yahoo Finance


class YahooFinanceFetcher:
    """Fetch OHLCV from Yahoo Finance's public chart API.

    Coverage: stocks, ETFs, indices, US futures (=F suffix), forex (=X suffix),
    and crypto (-USD suffix). No API key required.

    Limits (server-imposed): 1m up to ~7 days, 1h up to ~730 days, 1d unlimited.
    For multi-year 1h pulls the caller should chunk by ~600 days.
    """

    def __init__(self, user_agent: str = YAHOO_DEFAULT_UA, timeout: float = 30.0) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept": "application/json"})
        self.timeout = timeout

    def fetch(
        self,
        symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
        max_retries: int = 5,
    ) -> pd.DataFrame:
        if interval not in YAHOO_INTERVAL_MAP:
            raise ValueError(
                f"unsupported yahoo interval {interval!r}; supported: {sorted(YAHOO_INTERVAL_MAP)}"
            )
        period1 = int(start.replace(tzinfo=timezone.utc).timestamp())
        period2 = int(end.replace(tzinfo=timezone.utc).timestamp())
        params = {
            "interval": YAHOO_INTERVAL_MAP[interval],
            "period1": period1,
            "period2": period2,
            "includePrePost": "false",
            "events": "div|split",
        }
        url = f"{YAHOO_BASE}/{symbol}"
        last_status = None
        last_text = ""
        for attempt in range(1, max_retries + 1):
            self.session.headers["User-Agent"] = YAHOO_UA_ROTATION[(attempt - 1) % len(YAHOO_UA_ROTATION)]
            resp = self.session.get(url, params=params, timeout=self.timeout)
            last_status = resp.status_code
            last_text = resp.text[:200] if resp.text else ""
            if resp.status_code == 200:
                return self._parse(resp.json(), symbol)
            if resp.status_code in (429, 500, 502, 503, 504):
                wait = min(60, 5 * (2 ** (attempt - 1)))
                print(
                    f"  yahoo {symbol}: HTTP {resp.status_code}, retrying in {wait}s "
                    f"(attempt {attempt}/{max_retries})",
                    file=sys.stderr,
                )
                time.sleep(wait)
                continue
            break
        raise RuntimeError(f"yahoo {symbol}: HTTP {last_status} {last_text!r}")

    def _parse(self, payload: dict, symbol: str) -> pd.DataFrame:
        chart = payload.get("chart") or {}
        if chart.get("error"):
            raise RuntimeError(f"yahoo {symbol}: error payload {chart['error']!r}")
        results = chart.get("result") or []
        if not results:
            raise RuntimeError(f"yahoo {symbol}: empty result")
        result = results[0]
        timestamps = result.get("timestamp") or []
        if not timestamps:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
        quotes_list = (result.get("indicators") or {}).get("quote") or []
        if not quotes_list:
            raise RuntimeError(f"yahoo {symbol}: no quote indicators")
        q = quotes_list[0]
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(timestamps, unit="s", utc=True),
                "open": q.get("open", []),
                "high": q.get("high", []),
                "low": q.get("low", []),
                "close": q.get("close", []),
                "volume": q.get("volume", []),
            }
        )
        return df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)


def _yahoo_chunked(
    fetcher: YahooFinanceFetcher,
    symbol: str,
    interval: str,
    start: datetime,
    end: datetime,
    chunk_days: int = 600,
) -> pd.DataFrame:
    if interval == "1d":
        return fetcher.fetch(symbol, interval, start, end)
    chunks: list[pd.DataFrame] = []
    cursor = start
    while cursor < end:
        nxt = min(end, cursor + pd.Timedelta(days=chunk_days).to_pytimedelta())
        df = fetcher.fetch(symbol, interval, cursor, nxt)
        if not df.empty:
            chunks.append(df)
        cursor = nxt
        time.sleep(2.0)
    if not chunks:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    return (
        pd.concat(chunks, ignore_index=True)
        .drop_duplicates(subset=["date"])
        .sort_values("date")
        .reset_index(drop=True)
    )


def cmd_yahoo(args: argparse.Namespace) -> int:
    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end)
    fetcher = YahooFinanceFetcher()
    df = _yahoo_chunked(fetcher, args.symbol, args.interval, start, end)
    if df.empty:
        print(f"ERROR: yahoo returned no rows for {args.symbol}", file=sys.stderr)
        return 3
    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(
        f"yahoo {args.symbol} {args.interval}: {len(df):,} rows "
        f"({df['date'].min()} -> {df['date'].max()}) -> {out_path}"
    )
    return 0


# ---------------------------------------------------------------------------
# NSE option chain (network adapter only; demo blocked by Akamai geofence)


class NseOptionChainFetcher:
    """Distilled NSE option-chain fetcher.

    Pattern is identical to VarunS2002/Python-NSE-Option-Chain-Analyzer's
    network layer (warmup -> cookies -> JSON), stripped of all GUI code.

    Endpoints (canonical):
      GET /option-chain                     -> warmup, sets Akamai cookies
      GET /api/underlying-information       -> {"data": {"IndexList":[...], "UnderlyingList":[...]}}
      GET /api/option-chain-v3?type=Indices&symbol=NIFTY&expiry=DD-MMM-YYYY
      GET /api/option-chain-v3?type=Equity&symbol=RELIANCE&expiry=DD-MMM-YYYY

    Akamai blocks non-Indian IPs at the edge with HTTP 403; this adapter is
    correct, but demonstration requires VPN/proxy with Indian routing.
    """

    def __init__(self, timeout: float = 8.0) -> None:
        self.session = requests.Session()
        self.session.headers.update(NSE_HEADERS)
        self.timeout = timeout
        self._warmed = False

    def warmup(self) -> None:
        resp = self.session.get(NSE_URL_HOME, timeout=self.timeout)
        if resp.status_code != 200:
            raise RuntimeError(
                f"NSE warmup failed: HTTP {resp.status_code} (likely Akamai geofence; "
                f"NSE blocks non-Indian IPs at the edge)"
            )
        self._warmed = True

    def list_symbols(self) -> dict[str, list[str]]:
        if not self._warmed:
            self.warmup()
        resp = self.session.get(NSE_URL_SYMBOLS, timeout=self.timeout)
        resp.raise_for_status()
        payload = resp.json().get("data") or {}
        indices = [it["symbol"] for it in payload.get("IndexList", []) if "symbol" in it]
        stocks = [it["symbol"] for it in payload.get("UnderlyingList", []) if "symbol" in it]
        return {"indices": indices, "stocks": stocks}

    def get_chain(self, symbol: str, expiry: str, kind: str = "Indices") -> dict:
        if kind not in ("Indices", "Equity"):
            raise ValueError(f"kind must be 'Indices' or 'Equity', got {kind!r}")
        if not self._warmed:
            self.warmup()
        url_template = NSE_URL_INDEX if kind == "Indices" else NSE_URL_EQUITY
        url = url_template.format(symbol=symbol, expiry=expiry)
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def chain_to_csv(chain_payload: dict, output_path: Path, snapshot_ts: datetime | None = None) -> int:
        snapshot_ts = snapshot_ts or datetime.now(timezone.utc)
        records = (chain_payload.get("records") or {}).get("data") or []
        rows: list[dict[str, Any]] = []
        for rec in records:
            strike = rec.get("strikePrice")
            expiry = rec.get("expiryDate")
            ce = rec.get("CE") or {}
            pe = rec.get("PE") or {}
            rows.append(
                {
                    "snapshot_utc": snapshot_ts.isoformat(),
                    "expiry": expiry,
                    "strike": strike,
                    "call_oi": ce.get("openInterest"),
                    "call_chng_oi": ce.get("changeinOpenInterest"),
                    "call_iv": ce.get("impliedVolatility"),
                    "call_ltp": ce.get("lastPrice"),
                    "call_volume": ce.get("totalTradedVolume"),
                    "put_oi": pe.get("openInterest"),
                    "put_chng_oi": pe.get("changeinOpenInterest"),
                    "put_iv": pe.get("impliedVolatility"),
                    "put_ltp": pe.get("lastPrice"),
                    "put_volume": pe.get("totalTradedVolume"),
                }
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
            writer.writeheader()
            writer.writerows(rows)
        return len(rows)


def cmd_nse_options(args: argparse.Namespace) -> int:
    fetcher = NseOptionChainFetcher()
    try:
        fetcher.warmup()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("hint: NSE blocks non-Indian IPs; route via VPN to mum/del exit.", file=sys.stderr)
        return 4
    if args.list_symbols:
        symbols = fetcher.list_symbols()
        print(json.dumps(symbols, indent=2))
        return 0
    if not args.symbol or not args.expiry:
        print("ERROR: --symbol and --expiry required (DD-MMM-YYYY format)", file=sys.stderr)
        return 2
    chain = fetcher.get_chain(args.symbol, args.expiry, kind=args.kind)
    out_path = Path(args.output).resolve()
    n = NseOptionChainFetcher.chain_to_csv(chain, out_path)
    print(f"NSE {args.kind} {args.symbol} {args.expiry}: {n:,} strike rows -> {out_path}")
    return 0


# ---------------------------------------------------------------------------
# Polygon (skeleton; requires paid API key)


def cmd_polygon(args: argparse.Namespace) -> int:
    api_key = os.environ.get("POLYGON_API_KEY", "")
    if not api_key:
        print("ERROR: POLYGON_API_KEY env var required", file=sys.stderr)
        return 2
    base = "https://api.polygon.io/v2/aggs/ticker"
    multiplier_map = {
        "1m": ("1", "minute"),
        "5m": ("5", "minute"),
        "15m": ("15", "minute"),
        "1h": ("1", "hour"),
        "4h": ("4", "hour"),
        "1d": ("1", "day"),
    }
    if args.interval not in multiplier_map:
        print(f"ERROR: unsupported interval {args.interval!r}", file=sys.stderr)
        return 2
    mult, span = multiplier_map[args.interval]
    url = f"{base}/{args.symbol}/range/{mult}/{span}/{args.start}/{args.end}"
    params = {"adjusted": "true", "sort": "asc", "limit": 50000, "apiKey": api_key}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    results = payload.get("results") or []
    if not results:
        print(f"WARN: polygon empty results for {args.symbol}", file=sys.stderr)
        return 3
    df = pd.DataFrame(results).rename(
        columns={"t": "date_ms", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"}
    )
    df["date"] = pd.to_datetime(df["date_ms"], unit="ms", utc=True)
    df = df[["date", "open", "high", "low", "close", "volume"]]
    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"polygon {args.symbol} {args.interval}: {len(df):,} rows -> {out_path}")
    return 0


# ---------------------------------------------------------------------------
# CLI


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Multi-asset data fetcher emitting canonical OHLCV CSV (or option-chain CSV)."
    )
    sub = p.add_subparsers(dest="provider", required=True)

    y = sub.add_parser("yahoo", help="OHLCV via Yahoo Finance (free, no key)")
    y.add_argument("--symbol", required=True, help="Yahoo symbol, e.g. AAPL, SPY, ES=F, EURUSD=X, BTC-USD")
    y.add_argument("--interval", default="1h", help="1m/5m/15m/30m/1h/1d (default 1h)")
    y.add_argument("--start", required=True, help="ISO start, e.g. 2023-01-01")
    y.add_argument("--end", required=True, help="ISO end, e.g. 2025-12-31")
    y.add_argument("--output", required=True, help="output CSV path")

    n = sub.add_parser("nse-options", help="NSE India option chain (Akamai geofenced; needs Indian IP)")
    n.add_argument("--symbol", help="e.g. NIFTY, BANKNIFTY, RELIANCE")
    n.add_argument("--expiry", help="DD-MMM-YYYY (e.g. 30-Apr-2026)")
    n.add_argument("--kind", default="Indices", choices=["Indices", "Equity"])
    n.add_argument("--list-symbols", action="store_true", help="dump available indices+stocks and exit")
    n.add_argument("--output", default="user_data/data/options/nse_chain.csv", help="output CSV path")

    pol = sub.add_parser("polygon", help="OHLCV via Polygon.io (needs POLYGON_API_KEY)")
    pol.add_argument("--symbol", required=True, help="e.g. AAPL, X:BTCUSD, C:EURUSD, O:SPY...")
    pol.add_argument("--interval", default="1h")
    pol.add_argument("--start", required=True, help="YYYY-MM-DD")
    pol.add_argument("--end", required=True, help="YYYY-MM-DD")
    pol.add_argument("--output", required=True)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.provider == "yahoo":
        return cmd_yahoo(args)
    if args.provider == "nse-options":
        return cmd_nse_options(args)
    if args.provider == "polygon":
        return cmd_polygon(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
