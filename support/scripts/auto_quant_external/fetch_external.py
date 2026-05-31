"""
fetch_external.py — multi-asset data fetcher that emits canonical OHLCV CSV
consumable by `prepare_external.py`, plus option-chain and prediction-market
dumpers for use cases that don't fit FreqTrade's IStrategy model.

Providers (sub-commands):
  yahoo              OHLCV for stocks/ETFs/futures/forex/index/crypto via
                     Yahoo Finance chart API (no key).
                     Symbols: AAPL / SPY / ^GSPC / ES=F / EURUSD=X / BTC-USD.

  nse-options        Option-chain snapshot from NSE India (indices/equity);
                     needs Indian-routable IP (Akamai geofence).

  polygon            Stocks/ETFs/options/crypto/forex via Polygon.io REST
                     (requires POLYGON_API_KEY).

  hubble-kline       OHLCV via an opt-in Hubble V2 HTTP API endpoint.
                     Requires ICT_ENGINE_HUBBLE_BASE_URL.
                     ICT_ENGINE_HUBBLE_API_KEY optionally overrides the
                     upstream-compatible default key fallback.

  bybit-kline        OHLCV via Bybit V5 public REST. Categories: spot, linear
                     (USDT perps), inverse (coin-margined perps), option.
                     No API key; pagination-aware. Useful for crypto perps
                     and option-contract history.

  bybit-options      Bybit USDC option chain snapshot for BTC/ETH/SOL with
                     mark-IV and Greeks (delta/gamma/theta/vega).

  kraken-kline       OHLCV via Kraken public REST. Spot path covers crypto,
                     **xStocks tokenised U.S. equities (24/7)**, and fiat
                     forex with real volume; futures path covers crypto perps
                     and **PF_* equity-index perps** (PF_SPXUSD etc.) usable
                     as crypto-collateralised CFD substitutes.

  binance-kline      OHLCV via Binance Spot REST (`/api/v3/klines`),
                     pagination-aware. No API key.

  binance-options    Binance European option chain snapshot for BTC/ETH from
                     `/eapi`, including mark-IV and Greeks per contract.

  polymarket-markets List Polymarket prediction markets via Gamma API.

  polymarket-history Mid-price time series for a Polymarket CLOB token,
                     usable as alternative-data implied-probability series.

  ibkr-historical    OHLCV via local IB Gateway / TWS (single login session)
                     for stocks, ETFs, futures, indices, forex, options.
                     Opt-in feature (see support/scripts/ibkr_bridge/setup.py); reuses
                     the cross-process IbkrRateLimiter so concurrent bridge.py
                     traffic is correctly throttled against the same account
                     budget.

  ibkr-contract-details
                     Qualified IBKR contract details/secdef JSON packet for
                     preflight identity checks. Does not request historical
                     bars and is not promotion evidence by itself.

Architectural note: this script's job is FETCH + WRITE-CANONICAL-CSV (or wide
CSV for option chain / market list). Data cleaning, resampling, and feather
conversion live in prepare_external.py. Two stages, two tools, no entanglement.

Auth model: all sub-commands above use public read endpoints. Authenticated
features (account / order / portfolio) are intentionally out of scope here and
will be wired through env-var driven keys (e.g. BYBIT_API_KEY/SECRET,
KRAKEN_API_KEY/SECRET, BINANCE_API_KEY/SECRET) when the operator applies.
Hubble is also opt-in and credentialed: callers must supply their own endpoint
via ICT_ENGINE_HUBBLE_BASE_URL. ICT_ENGINE_HUBBLE_API_KEY is an optional
override; when absent, the fetcher falls back to the upstream-compatible
default key behavior. This script does not embed Hubble's sample endpoint.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import socket
import sys
import time
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

import requests


IBKR_GATEWAY_PORT_CANDIDATES = [
    ("TWS paper", 7497),
    ("TWS live", 7496),
    ("IB Gateway paper", 4002),
    ("IB Gateway live", 4001),
]
IBKR_GATEWAY_PROBE_TIMEOUT_SECONDS = 0.15


class _LazyPandasModule:
    """Import pandas only when a code path actually touches it.

    Some provider-only paths such as `ibkr-historical` do not need pandas at
    runtime. Delaying the import keeps those paths usable even when the local
    pandas runtime is slow or unhealthy.
    """

    _module = None

    def __getattr__(self, name: str):
        if self._module is None:
            import pandas as pandas_module  # noqa: WPS433

            self._module = pandas_module
        return getattr(self._module, name)


pd = _LazyPandasModule()

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

HUBBLE_BASE_URL_ENV = "ICT_ENGINE_HUBBLE_BASE_URL"
HUBBLE_API_KEY_ENV = "ICT_ENGINE_HUBBLE_API_KEY"
HUBBLE_DEFAULT_API_KEY = "123456"
HUBBLE_STOCK_INTERVAL_MAP = {
    "1d": "daily",
    "daily": "daily",
    "1w": "weekly",
    "weekly": "weekly",
    "1mo": "monthly",
    "1M": "monthly",
    "monthly": "monthly",
}
HUBBLE_CRYPTO_INTERVALS = {"1m", "5m", "15m", "1h", "4h", "1d", "1w"}

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
# Hubble V2 (opt-in; operator supplies endpoint + API key via env)


def _format_hubble_date(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.date().strftime("%Y%m%d")


def build_hubble_kline_request(
    market: str,
    symbol: str,
    interval: str,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int | None = None,
    exchange: str | None = None,
) -> tuple[str, dict[str, Any]]:
    market_key = (market or "").strip().lower()
    interval_key = (interval or "").strip()
    symbol_value = (symbol or "").strip()
    exchange_value = (exchange or "").strip().lower()
    if not symbol_value:
        raise ValueError("hubble symbol must not be empty")
    if limit is not None and limit <= 0:
        raise ValueError("hubble limit must be positive")
    if start and end and end < start:
        raise ValueError("hubble end must be greater than or equal to start")

    if market_key == "cn":
        mapped_interval = HUBBLE_STOCK_INTERVAL_MAP.get(interval_key)
        if mapped_interval is None:
            raise ValueError("hubble cn interval must be one of 1d, 1w, 1mo")
        if start is None and end is None and limit is None:
            raise ValueError("hubble cn fetch requires --start/--end or --limit")
        params: dict[str, Any] = {"symbol": symbol_value, "interval": mapped_interval}
        if start is not None:
            params["startDate"] = _format_hubble_date(start)
        if end is not None:
            params["endDate"] = _format_hubble_date(end)
        if limit is not None:
            params["limit"] = limit
        return "/api/v2/cnstock/stocks", params

    if market_key == "hk":
        if interval_key not in ("1d", "daily"):
            raise ValueError("hubble hk interval currently supports 1d only")
        if limit is not None:
            raise ValueError("hubble hk fetch does not support --limit; use --start and --end")
        if start is None or end is None:
            raise ValueError("hubble hk fetch requires both --start and --end")
        return "/api/v2/hkstock/stocks", {
            "symbol": symbol_value,
            "startDate": _format_hubble_date(start),
            "endDate": _format_hubble_date(end),
        }

    if market_key == "us":
        if interval_key not in ("1d", "daily"):
            raise ValueError("hubble us interval currently supports 1d only")
        if start is None and end is None and limit is None:
            raise ValueError("hubble us fetch requires --start/--end or --limit")
        params = {"symbol": symbol_value}
        if start is not None:
            params["startDate"] = _format_hubble_date(start)
        if end is not None:
            params["endDate"] = _format_hubble_date(end)
        if limit is not None:
            params["limit"] = limit
        return "/api/v2/usstock/stocks", params

    if market_key == "crypto":
        if interval_key not in HUBBLE_CRYPTO_INTERVALS:
            raise ValueError("hubble crypto interval must be one of 1m, 5m, 15m, 1h, 4h, 1d, 1w")
        if not exchange_value:
            raise ValueError("hubble crypto fetch requires --exchange")
        if limit is None and not (start is not None and end is not None):
            raise ValueError("hubble crypto fetch requires --limit or both --start and --end")
        params = {
            "exchange": exchange_value,
            "symbol": symbol_value,
            "interval": interval_key,
        }
        if limit is not None:
            params["limit"] = limit
        # Some Hubble deployments accept explicit date bounds on crypto klines.
        if start is not None:
            params["startDate"] = _format_hubble_date(start)
        if end is not None:
            params["endDate"] = _format_hubble_date(end)
        return "/api/v2/crypto/klines", params

    raise ValueError("hubble market must be one of cn, hk, us, crypto")


def _extract_hubble_kline_rows(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    candidates = [payload.get("data"), payload.get("list"), payload.get("rows"), payload.get("items")]
    for candidate in candidates:
        if isinstance(candidate, list):
            return candidate
        if isinstance(candidate, dict):
            for key in ("data", "list", "rows", "items", "candles"):
                nested = candidate.get(key)
                if isinstance(nested, list):
                    return nested
    result = payload.get("result")
    if isinstance(result, dict):
        for key in ("data", "list", "rows", "items", "candles"):
            nested = result.get(key)
            if isinstance(nested, list):
                return nested
    return []


def _parse_hubble_timestamp(value: Any) -> pd.Timestamp:
    if value is None:
        raise ValueError("missing timestamp")
    if isinstance(value, (int, float)):
        numeric = int(value)
        unit = "ms" if abs(numeric) >= 1_000_000_000_000 else "s"
        return pd.to_datetime(numeric, unit=unit, utc=True)
    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("empty timestamp")
        if trimmed.isdigit():
            if len(trimmed) >= 13:
                return pd.to_datetime(int(trimmed), unit="ms", utc=True)
            if len(trimmed) >= 10:
                return pd.to_datetime(int(trimmed), unit="s", utc=True)
            if len(trimmed) == 8:
                return pd.to_datetime(trimmed, format="%Y%m%d", utc=True)
        return pd.to_datetime(trimmed, utc=True)
    raise ValueError(f"unsupported timestamp type: {type(value).__name__}")


def _hubble_row_to_record(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        ts_value = (
            row.get("time")
            or row.get("timestamp")
            or row.get("ts")
            or row.get("tradeDate")
            or row.get("date")
        )
        open_value = row.get("open")
        high_value = row.get("high")
        low_value = row.get("low")
        close_value = row.get("close")
        volume_value = row.get("volume", row.get("vol", 0))
    elif isinstance(row, (list, tuple)) and len(row) >= 6:
        ts_value, open_value, high_value, low_value, close_value, volume_value = row[:6]
    else:
        raise ValueError(f"unsupported row shape: {row!r}")

    open_price = _to_float_or_none(open_value)
    high_price = _to_float_or_none(high_value)
    low_price = _to_float_or_none(low_value)
    close_price = _to_float_or_none(close_value)
    if None in (open_price, high_price, low_price, close_price):
        raise ValueError(f"incomplete OHLC row: {row!r}")

    return {
        "date": _parse_hubble_timestamp(ts_value),
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,
        "volume": _to_float_or_none(volume_value) or 0.0,
    }


def parse_hubble_kline_payload(payload: Any) -> pd.DataFrame:
    rows = _extract_hubble_kline_rows(payload)
    if not rows:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    records = [_hubble_row_to_record(row) for row in rows]
    return (
        pd.DataFrame(records)
        .drop_duplicates(subset=["date"])
        .sort_values("date")
        .reset_index(drop=True)
    )


class HubbleFetcher:
    """Fetch OHLCV from an operator-supplied Hubble V2 deployment."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": YAHOO_DEFAULT_UA,
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-API-Key": api_key,
            }
        )
        self.timeout = timeout

    @classmethod
    def from_env(cls, timeout: float = 30.0) -> "HubbleFetcher":
        base_url = os.environ.get(HUBBLE_BASE_URL_ENV, "").strip()
        api_key = os.environ.get(HUBBLE_API_KEY_ENV, "").strip() or HUBBLE_DEFAULT_API_KEY
        if not base_url:
            raise ValueError(
                f"{HUBBLE_BASE_URL_ENV} must be set for hubble-kline; {HUBBLE_API_KEY_ENV} is optional"
            )
        return cls(base_url=base_url, api_key=api_key, timeout=timeout)

    def _get(self, path: str, params: dict[str, Any], max_retries: int = 5) -> Any:
        url = f"{self.base_url}{path}"
        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
            except (requests.exceptions.SSLError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as exc:
                wait = min(60, 5 * (2 ** (attempt - 1)))
                print(
                    f"  hubble {path}: {type(exc).__name__}, retry in {wait}s "
                    f"({attempt}/{max_retries})",
                    file=sys.stderr,
                )
                time.sleep(wait)
                continue
            if resp.status_code == 200:
                payload = resp.json()
                rows = _extract_hubble_kline_rows(payload)
                if rows:
                    return payload
                if isinstance(payload, dict):
                    code = payload.get("code")
                    if code not in (None, 0, "0", 200, "200", True):
                        msg = payload.get("msg") or payload.get("message") or "unknown"
                        raise RuntimeError(f"hubble {path}: code {code!r} {msg!r}")
                return payload
            if resp.status_code in (429, 500, 502, 503, 504):
                wait = min(60, 5 * (2 ** (attempt - 1)))
                print(
                    f"  hubble {path}: HTTP {resp.status_code}, retry in {wait}s "
                    f"({attempt}/{max_retries})",
                    file=sys.stderr,
                )
                time.sleep(wait)
                continue
            raise RuntimeError(f"hubble {path}: HTTP {resp.status_code} {resp.text[:200]!r}")
        raise RuntimeError(f"hubble {path}: retries exhausted")

    def kline(
        self,
        market: str,
        symbol: str,
        interval: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
        exchange: str | None = None,
    ) -> pd.DataFrame:
        path, params = build_hubble_kline_request(
            market=market,
            symbol=symbol,
            interval=interval,
            start=start,
            end=end,
            limit=limit,
            exchange=exchange,
        )
        payload = self._get(path, params)
        return parse_hubble_kline_payload(payload)


def cmd_hubble_kline(args: argparse.Namespace) -> int:
    try:
        start = datetime.fromisoformat(args.start) if args.start else None
        end = datetime.fromisoformat(args.end) if args.end else None
        fetcher = HubbleFetcher.from_env()
        df = fetcher.kline(
            market=args.market,
            symbol=args.symbol,
            interval=args.interval,
            start=start,
            end=end,
            limit=args.limit,
            exchange=args.exchange,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if df.empty:
        print(
            f"ERROR: hubble returned no rows for {args.market}/{args.symbol}",
            file=sys.stderr,
        )
        return 3
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    label = args.symbol
    if args.market == "crypto" and args.exchange:
        label = f"{args.exchange}:{label}"
    print(
        f"hubble {args.market} {label} {args.interval}: {len(df):,} rows "
        f"({df['date'].min()} -> {df['date'].max()}) -> {out}"
    )
    return 0


# ---------------------------------------------------------------------------
# Bybit V5 (public read; key-pluggable later via BYBIT_API_KEY/SECRET)


def _to_float_or_none(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


class BybitFetcher:
    """Fetch OHLCV and option chain from Bybit V5 public REST.

    Endpoints:
      GET /v5/market/kline?category=&symbol=&interval=&start=&end=&limit=1000
      GET /v5/market/instruments-info?category=option&baseCoin=
      GET /v5/market/tickers?category=option&baseCoin=
    """

    BASE = "https://api.bybit.com"
    INTERVAL_MAP = {
        "1m": "1", "3m": "3", "5m": "5", "15m": "15", "30m": "30",
        "1h": "60", "2h": "120", "4h": "240", "6h": "360", "12h": "720",
        "1d": "D", "1w": "W", "1M": "M",
    }
    PAGE_LIMIT = 1000

    def __init__(self, timeout: float = 30.0) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": YAHOO_DEFAULT_UA, "Accept": "application/json"})
        self.timeout = timeout

    def _get(self, path: str, params: dict, max_retries: int = 5) -> dict:
        url = f"{self.BASE}{path}"
        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
            except (requests.exceptions.SSLError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as exc:
                wait = min(60, 5 * (2 ** (attempt - 1)))
                print(f"  bybit {path}: {type(exc).__name__}, retry in {wait}s "
                      f"({attempt}/{max_retries})", file=sys.stderr)
                time.sleep(wait)
                continue
            if resp.status_code == 200:
                payload = resp.json()
                if payload.get("retCode") == 0:
                    return payload
                msg = payload.get("retMsg") or "unknown"
                raise RuntimeError(f"bybit {path}: retCode {payload.get('retCode')} {msg!r}")
            if resp.status_code in (429, 500, 502, 503, 504):
                wait = min(60, 5 * (2 ** (attempt - 1)))
                print(f"  bybit {path}: HTTP {resp.status_code}, retry in {wait}s "
                      f"({attempt}/{max_retries})", file=sys.stderr)
                time.sleep(wait)
                continue
            raise RuntimeError(f"bybit {path}: HTTP {resp.status_code} {resp.text[:200]!r}")
        raise RuntimeError(f"bybit {path}: retries exhausted")

    def kline(self, category: str, symbol: str, interval: str,
              start: datetime, end: datetime) -> pd.DataFrame:
        if interval not in self.INTERVAL_MAP:
            raise ValueError(f"unsupported bybit interval {interval!r}")
        bybit_interval = self.INTERVAL_MAP[interval]
        cursor = int(start.replace(tzinfo=timezone.utc).timestamp() * 1000)
        end_ms = int(end.replace(tzinfo=timezone.utc).timestamp() * 1000)
        rows: list[dict] = []
        while cursor < end_ms:
            params = {
                "category": category,
                "symbol": symbol,
                "interval": bybit_interval,
                "start": cursor,
                "end": end_ms,
                "limit": self.PAGE_LIMIT,
            }
            payload = self._get("/v5/market/kline", params)
            kl = payload.get("result", {}).get("list") or []
            if not kl:
                break
            kl = list(reversed(kl))  # bybit returns DESC
            for row in kl:
                rows.append({
                    "date": pd.to_datetime(int(row[0]), unit="ms", utc=True),
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5]),
                })
            last_ms = int(kl[-1][0])
            if last_ms <= cursor:
                break
            cursor = last_ms + 1
            if len(kl) < self.PAGE_LIMIT:
                break
            time.sleep(0.2)
        if not rows:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
        return (pd.DataFrame(rows)
                .drop_duplicates(subset=["date"])
                .sort_values("date")
                .reset_index(drop=True))

    def option_chain(self, base: str) -> pd.DataFrame:
        inst = self._get("/v5/market/instruments-info",
                         {"category": "option", "baseCoin": base})
        instruments = inst.get("result", {}).get("list") or []
        ticks = self._get("/v5/market/tickers",
                          {"category": "option", "baseCoin": base})
        tickers = {t["symbol"]: t for t in ticks.get("result", {}).get("list") or []}
        snapshot = datetime.now(timezone.utc)
        rows = []
        for it in instruments:
            sym = it.get("symbol", "")
            parts = sym.split("-")
            # Bybit V5 symbol forms:
            #   BASE-EXPIRY-STRIKE-{C|P}              (legacy USDC-settled)
            #   BASE-EXPIRY-STRIKE-{C|P}-{USDT|USDC}  (current; settle suffix)
            if len(parts) == 4:
                _, expiry_str, strike_str, side = parts
                settle = it.get("settleCoin") or it.get("quoteCoin") or "USDC"
            elif len(parts) == 5:
                _, expiry_str, strike_str, side, settle = parts
            else:
                continue
            t = tickers.get(sym, {})
            rows.append({
                "snapshot_utc": snapshot.isoformat(),
                "underlying": base,
                "symbol": sym,
                "expiry": expiry_str,
                "strike": _to_float_or_none(strike_str),
                "side": side,
                "settle": settle,
                "mark_price": _to_float_or_none(t.get("markPrice")),
                "mark_iv": _to_float_or_none(t.get("markIv")),
                "delta": _to_float_or_none(t.get("delta")),
                "gamma": _to_float_or_none(t.get("gamma")),
                "theta": _to_float_or_none(t.get("theta")),
                "vega": _to_float_or_none(t.get("vega")),
                "open_interest": _to_float_or_none(t.get("openInterest")),
                "volume_24h": _to_float_or_none(t.get("volume24h")),
                "bid_price": _to_float_or_none(t.get("bid1Price")),
                "ask_price": _to_float_or_none(t.get("ask1Price")),
                "underlying_price": _to_float_or_none(t.get("underlyingPrice")),
            })
        return pd.DataFrame(rows)


def cmd_bybit_kline(args: argparse.Namespace) -> int:
    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end)
    fetcher = BybitFetcher()
    df = fetcher.kline(args.category, args.symbol, args.interval, start, end)
    if df.empty:
        print(f"ERROR: bybit returned no rows for {args.category}/{args.symbol}", file=sys.stderr)
        return 3
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"bybit {args.category} {args.symbol} {args.interval}: {len(df):,} rows "
          f"({df['date'].min()} -> {df['date'].max()}) -> {out}")
    return 0


def cmd_bybit_options(args: argparse.Namespace) -> int:
    fetcher = BybitFetcher()
    df = fetcher.option_chain(args.base)
    if args.expiry:
        df = df[df["expiry"] == args.expiry]
    if df.empty:
        print(f"WARN: bybit option chain empty for {args.base}"
              + (f" expiry {args.expiry}" if args.expiry else ""), file=sys.stderr)
        return 3
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    n_expiries = df["expiry"].nunique()
    print(f"bybit options {args.base}: {len(df):,} contracts across "
          f"{n_expiries} expiries -> {out}")
    return 0


# ---------------------------------------------------------------------------
# Kraken (public read; spot via api.kraken.com, futures via futures.kraken.com)


class KrakenFetcher:
    """Fetch OHLC from Kraken public REST.

    Spot endpoints (api.kraken.com):
      GET /0/public/AssetPairs                    catalogue (resolves wsname)
      GET /0/public/OHLC?pair=&interval=          last ~720 OHLC bars
        interval is in MINUTES: 1, 5, 15, 30, 60, 240, 1440, 10080, 21600.
        Spot covers crypto + tokenised U.S. equities (xStocks, e.g. AAPLx)
        + fiat forex.

    Futures public charts (futures.kraken.com):
      GET /api/charts/v1/{tickType}/{symbol}/{resolution}?from=&to=
        tickType in {trade, mark, spot, index}
        resolution in {1m, 5m, 15m, 30m, 1h, 4h, 12h, 1d, 1w}
        Symbol examples: PF_XBTUSD (BTC perp), PF_SPXUSD (S&P 500 perp),
                         PF_AAPLXUSD (AAPL equity perp), FI_XBTUSD_260327.
    """

    SPOT_BASE = "https://api.kraken.com"
    FUTURES_CHARTS = "https://futures.kraken.com/api/charts/v1"
    SPOT_INTERVAL_MAP = {
        "1m": 1, "5m": 5, "15m": 15, "30m": 30,
        "1h": 60, "4h": 240, "1d": 1440, "1w": 10080, "15d": 21600,
    }
    FUTURES_INTERVAL_MAP = {
        "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
        "1h": "1h", "4h": "4h", "12h": "12h", "1d": "1d", "1w": "1w",
    }

    def __init__(self, timeout: float = 30.0) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": YAHOO_DEFAULT_UA, "Accept": "application/json"})
        self.timeout = timeout

    def _get(self, url: str, params: dict, max_retries: int = 5) -> dict:
        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
            except (requests.exceptions.SSLError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as exc:
                wait = min(60, 5 * (2 ** (attempt - 1)))
                print(f"  kraken {url}: {type(exc).__name__}, retry in {wait}s "
                      f"({attempt}/{max_retries})", file=sys.stderr)
                time.sleep(wait)
                continue
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (429, 500, 502, 503, 504):
                wait = min(60, 5 * (2 ** (attempt - 1)))
                print(f"  kraken {url}: HTTP {resp.status_code}, retry in {wait}s "
                      f"({attempt}/{max_retries})", file=sys.stderr)
                time.sleep(wait)
                continue
            raise RuntimeError(f"kraken {url}: HTTP {resp.status_code} {resp.text[:200]!r}")
        raise RuntimeError(f"kraken {url}: retries exhausted")

    def spot_ohlc(self, pair: str, interval: str,
                  asset_class: str | None = None) -> pd.DataFrame:
        if interval not in self.SPOT_INTERVAL_MAP:
            raise ValueError(f"unsupported kraken-spot interval {interval!r}")
        params: dict[str, Any] = {"pair": pair, "interval": self.SPOT_INTERVAL_MAP[interval]}
        if asset_class:
            # Required for non-crypto pairs (tokenized_asset for xStocks; forex for fiat).
            params["asset_class"] = asset_class
        data = self._get(f"{self.SPOT_BASE}/0/public/OHLC", params)
        if data.get("error"):
            raise RuntimeError(f"kraken-spot {pair}: error {data['error']}")
        result = data.get("result") or {}
        pair_key = next((k for k in result if k != "last"), None)
        if not pair_key:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
        rows = result[pair_key]
        df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "vwap", "volume", "count"])
        df["date"] = pd.to_datetime(df["ts"].astype(int), unit="s", utc=True)
        for c in ["open", "high", "low", "close", "volume"]:
            df[c] = df[c].astype(float)
        return df[["date", "open", "high", "low", "close", "volume"]]

    def futures_ohlc(self, symbol: str, interval: str,
                     start: datetime | None = None, end: datetime | None = None) -> pd.DataFrame:
        if interval not in self.FUTURES_INTERVAL_MAP:
            raise ValueError(f"unsupported kraken-futures interval {interval!r}")
        url = f"{self.FUTURES_CHARTS}/trade/{symbol}/{self.FUTURES_INTERVAL_MAP[interval]}"
        params: dict[str, Any] = {}
        if start is not None:
            params["from"] = int(start.replace(tzinfo=timezone.utc).timestamp())
        if end is not None:
            params["to"] = int(end.replace(tzinfo=timezone.utc).timestamp())
        data = self._get(url, params)
        candles = data.get("candles") or []
        if not candles:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
        df = pd.DataFrame(candles)
        df["date"] = pd.to_datetime(df["time"].astype("int64"), unit="ms", utc=True)
        for c in ["open", "high", "low", "close", "volume"]:
            df[c] = df[c].astype(float)
        return df[["date", "open", "high", "low", "close", "volume"]]


def cmd_kraken_kline(args: argparse.Namespace) -> int:
    fetcher = KrakenFetcher()
    if args.market == "spot":
        df = fetcher.spot_ohlc(args.pair, args.interval, asset_class=args.asset_class)
    elif args.market == "futures":
        start = datetime.fromisoformat(args.start) if args.start else None
        end = datetime.fromisoformat(args.end) if args.end else None
        df = fetcher.futures_ohlc(args.pair, args.interval, start, end)
    else:
        print(f"ERROR: unknown kraken market {args.market!r}", file=sys.stderr)
        return 2
    if df.empty:
        print(f"ERROR: kraken-{args.market} {args.pair}: empty result", file=sys.stderr)
        return 3
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"kraken {args.market} {args.pair} {args.interval}: {len(df):,} rows "
          f"({df['date'].min()} -> {df['date'].max()}) -> {out}")
    return 0


# ---------------------------------------------------------------------------
# Binance (Spot REST + European Options REST; both public read)


class BinanceFetcher:
    """Fetch OHLCV / option chain from Binance public REST.

    Spot:
      GET /api/v3/klines?symbol=&interval=&startTime=&endTime=&limit=1000

    European Options (`/eapi`):
      GET /eapi/v1/exchangeInfo               option universe per underlying
      GET /eapi/v1/klines?symbol=&interval=   per-contract OHLC
      GET /eapi/v1/mark[?symbol=]             mark IV + Greeks (no symbol = all)
    """

    SPOT_BASE = "https://api.binance.com"
    OPTIONS_BASE = "https://eapi.binance.com"
    INTERVAL_MAP = {
        "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
        "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h",
        "12h": "12h", "1d": "1d", "3d": "3d", "1w": "1w", "1M": "1M",
    }
    PAGE_LIMIT = 1000

    def __init__(self, timeout: float = 30.0) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": YAHOO_DEFAULT_UA, "Accept": "application/json"})
        self.timeout = timeout

    def _get(self, base: str, path: str, params: dict, max_retries: int = 5) -> Any:
        url = f"{base}{path}"
        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
            except (requests.exceptions.SSLError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as exc:
                wait = min(60, 5 * (2 ** (attempt - 1)))
                print(f"  binance {path}: {type(exc).__name__}, retry in {wait}s "
                      f"({attempt}/{max_retries})", file=sys.stderr)
                time.sleep(wait)
                continue
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (418, 429, 500, 502, 503, 504):
                wait = min(60, 5 * (2 ** (attempt - 1)))
                print(f"  binance {path}: HTTP {resp.status_code}, retry in {wait}s "
                      f"({attempt}/{max_retries})", file=sys.stderr)
                time.sleep(wait)
                continue
            raise RuntimeError(f"binance {path}: HTTP {resp.status_code} {resp.text[:200]!r}")
        raise RuntimeError(f"binance {path}: retries exhausted")

    def spot_klines(self, symbol: str, interval: str,
                    start: datetime, end: datetime) -> pd.DataFrame:
        if interval not in self.INTERVAL_MAP:
            raise ValueError(f"unsupported binance interval {interval!r}")
        cursor = int(start.replace(tzinfo=timezone.utc).timestamp() * 1000)
        end_ms = int(end.replace(tzinfo=timezone.utc).timestamp() * 1000)
        rows: list[dict] = []
        while cursor < end_ms:
            params = {
                "symbol": symbol,
                "interval": self.INTERVAL_MAP[interval],
                "startTime": cursor,
                "endTime": end_ms,
                "limit": self.PAGE_LIMIT,
            }
            kl = self._get(self.SPOT_BASE, "/api/v3/klines", params)
            if not kl:
                break
            for row in kl:
                rows.append({
                    "date": pd.to_datetime(int(row[0]), unit="ms", utc=True),
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5]),
                })
            last_ms = int(kl[-1][0])
            if last_ms <= cursor:
                break
            cursor = last_ms + 1
            if len(kl) < self.PAGE_LIMIT:
                break
            time.sleep(0.1)
        if not rows:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
        return (pd.DataFrame(rows)
                .drop_duplicates(subset=["date"])
                .sort_values("date")
                .reset_index(drop=True))

    def options_chain(self, underlying: str) -> pd.DataFrame:
        info = self._get(self.OPTIONS_BASE, "/eapi/v1/exchangeInfo", {})
        contracts = [
            c for c in info.get("optionSymbols", [])
            if c.get("underlying", "").upper().startswith(underlying.upper())
        ]
        marks_list = self._get(self.OPTIONS_BASE, "/eapi/v1/mark", {})
        marks = {m.get("symbol"): m for m in marks_list}
        snapshot = datetime.now(timezone.utc)
        rows = []
        for c in contracts:
            sym = c.get("symbol", "")
            m = marks.get(sym, {})
            expiry_ms = c.get("expiryDate")
            expiry_iso = (
                datetime.fromtimestamp(int(expiry_ms) / 1000, tz=timezone.utc).date().isoformat()
                if expiry_ms is not None else None
            )
            rows.append({
                "snapshot_utc": snapshot.isoformat(),
                "underlying": c.get("underlying", ""),
                "symbol": sym,
                "expiry": expiry_iso,
                "strike": _to_float_or_none(c.get("strikePrice")),
                "side": c.get("side"),  # CALL / PUT
                "mark_price": _to_float_or_none(m.get("markPrice")),
                "mark_iv": _to_float_or_none(m.get("markIV")),
                "delta": _to_float_or_none(m.get("delta")),
                "gamma": _to_float_or_none(m.get("gamma")),
                "theta": _to_float_or_none(m.get("theta")),
                "vega": _to_float_or_none(m.get("vega")),
                "high_price_limit": _to_float_or_none(m.get("highPriceLimit")),
                "low_price_limit": _to_float_or_none(m.get("lowPriceLimit")),
            })
        return pd.DataFrame(rows)


def cmd_binance_kline(args: argparse.Namespace) -> int:
    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end)
    fetcher = BinanceFetcher()
    df = fetcher.spot_klines(args.symbol, args.interval, start, end)
    if df.empty:
        print(f"ERROR: binance returned no rows for {args.symbol}", file=sys.stderr)
        return 3
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"binance spot {args.symbol} {args.interval}: {len(df):,} rows "
          f"({df['date'].min()} -> {df['date'].max()}) -> {out}")
    return 0


def cmd_binance_options(args: argparse.Namespace) -> int:
    fetcher = BinanceFetcher()
    df = fetcher.options_chain(args.underlying)
    if args.expiry:
        df = df[df["expiry"] == args.expiry]
    if df.empty:
        print(f"WARN: binance options chain empty for {args.underlying}"
              + (f" expiry {args.expiry}" if args.expiry else ""), file=sys.stderr)
        return 3
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    n_expiries = df["expiry"].nunique()
    print(f"binance options {args.underlying}: {len(df):,} contracts across "
          f"{n_expiries} expiries -> {out}")
    return 0


# ---------------------------------------------------------------------------
# Polymarket (Gamma API for discovery; CLOB API for time-series mid prices)


class PolymarketFetcher:
    """Browse Polymarket prediction markets and fetch CLOB price history.

    Endpoints:
      GET https://gamma-api.polymarket.com/markets       ?limit=&offset=&active=&closed=&order=&tag_id=
      GET https://gamma-api.polymarket.com/events        ?limit=&offset=&active=&closed=&order=&tag_id=
      GET https://clob.polymarket.com/prices-history     ?market=<tokenId>&startTs=&endTs=&interval=&fidelity=

    Note on token IDs: a Polymarket "market" is an outcome pair; each side has
    a numeric `clobTokenId`. The price-history endpoint is keyed by this ID,
    not by the market slug. Use `polymarket-markets` first to discover token
    IDs, then `polymarket-history` for the time series.
    """

    GAMMA_BASE = "https://gamma-api.polymarket.com"
    CLOB_BASE = "https://clob.polymarket.com"
    INTERVAL_OPTIONS = {"1m", "1h", "6h", "1d", "1w", "max"}

    def __init__(self, timeout: float = 30.0) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": YAHOO_DEFAULT_UA, "Accept": "application/json"})
        self.timeout = timeout

    def _get(self, url: str, params: dict, max_retries: int = 5) -> Any:
        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
            except (requests.exceptions.SSLError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as exc:
                wait = min(60, 5 * (2 ** (attempt - 1)))
                print(f"  polymarket {url}: {type(exc).__name__}, retry in {wait}s "
                      f"({attempt}/{max_retries})", file=sys.stderr)
                time.sleep(wait)
                continue
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (429, 500, 502, 503, 504):
                wait = min(60, 5 * (2 ** (attempt - 1)))
                print(f"  polymarket {url}: HTTP {resp.status_code}, retry in {wait}s "
                      f"({attempt}/{max_retries})", file=sys.stderr)
                time.sleep(wait)
                continue
            raise RuntimeError(f"polymarket {url}: HTTP {resp.status_code} {resp.text[:200]!r}")
        raise RuntimeError(f"polymarket {url}: retries exhausted")

    def markets(self, limit: int = 20, active: bool | None = None,
                closed: bool | None = None, tag: str | None = None,
                order: str | None = None, offset: int = 0) -> list[dict]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if active is not None:
            params["active"] = "true" if active else "false"
        if closed is not None:
            params["closed"] = "true" if closed else "false"
        if tag:
            params["tag_id"] = tag
        if order:
            params["order"] = order
        data = self._get(f"{self.GAMMA_BASE}/markets", params)
        if isinstance(data, list):
            return data
        return data.get("markets", []) if isinstance(data, dict) else []

    def price_history(self, token_id: str, interval: str,
                      days: int = 30, fidelity: int | None = None) -> pd.DataFrame:
        if interval not in self.INTERVAL_OPTIONS:
            raise ValueError(f"polymarket interval must be one of {sorted(self.INTERVAL_OPTIONS)}")
        end_ts = int(datetime.now(timezone.utc).timestamp())
        start_ts = end_ts - days * 86400
        params: dict[str, Any] = {
            "market": token_id,
            "startTs": start_ts,
            "endTs": end_ts,
            "interval": interval,
        }
        if fidelity is not None:
            params["fidelity"] = fidelity
        data = self._get(f"{self.CLOB_BASE}/prices-history", params)
        history = data.get("history") or []
        if not history:
            return pd.DataFrame(columns=["date", "price"])
        df = pd.DataFrame(history)
        df["date"] = pd.to_datetime(df["t"].astype(int), unit="s", utc=True)
        df["price"] = df["p"].astype(float)
        return df[["date", "price"]]


def cmd_polymarket_markets(args: argparse.Namespace) -> int:
    fetcher = PolymarketFetcher()
    active = None
    if args.active is not None:
        active = args.active.lower() == "true"
    closed = None
    if args.closed is not None:
        closed = args.closed.lower() == "true"
    rows = fetcher.markets(
        limit=args.limit, active=active, closed=closed,
        tag=args.tag, order=args.order, offset=args.offset,
    )
    if not rows:
        print("WARN: polymarket markets returned no rows", file=sys.stderr)
        return 3
    flat = []
    for m in rows:
        flat.append({
            "id": m.get("id"),
            "slug": m.get("slug"),
            "question": m.get("question"),
            "active": m.get("active"),
            "closed": m.get("closed"),
            "volume_num": m.get("volumeNum"),
            "liquidity_num": m.get("liquidityNum"),
            "outcome_prices": m.get("outcomePrices"),
            "clob_token_ids": m.get("clobTokenIds"),
            "end_date": m.get("endDate"),
            "tags": m.get("tags"),
        })
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "json":
        out.write_text(json.dumps(flat, indent=2, default=str))
    else:
        pd.DataFrame(flat).to_csv(out, index=False)
    print(f"polymarket markets: {len(flat)} rows -> {out}")
    return 0


def cmd_polymarket_history(args: argparse.Namespace) -> int:
    fetcher = PolymarketFetcher()
    df = fetcher.price_history(args.token, args.interval, args.days, args.fidelity)
    if df.empty:
        print(f"WARN: polymarket price-history empty for token {args.token}", file=sys.stderr)
        return 3
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"polymarket history token {args.token} {args.interval} ({args.days}d): "
          f"{len(df):,} rows -> {out}")
    return 0


# ---------------------------------------------------------------------------
# IBKR historical (short-lived connection sharing IbkrRateLimiter with bridge)


@dataclass(frozen=True)
class _IbkrHistoricalChunk:
    duration: str


_IBKR_DURATION_UNIT_DAYS = {
    "D": 1,
    "W": 7,
    "M": 30,
    "Y": 365,
}

_IBKR_BAR_SIZE_MAX_CHUNK = {
    "1 min": ("1 D", 1),
    "2 mins": ("1 W", 7),
    "3 mins": ("1 W", 7),
    "5 mins": ("1 W", 7),
    "10 mins": ("1 W", 7),
    "15 mins": ("1 W", 7),
    "20 mins": ("1 M", 30),
    "30 mins": ("1 M", 30),
    "1 hour": ("1 M", 30),
    "2 hours": ("1 M", 30),
    "3 hours": ("1 M", 30),
    "4 hours": ("1 M", 30),
    "8 hours": ("1 M", 30),
}


def _ibkr_duration_days(duration: str) -> int | None:
    parts = duration.strip().split()
    if len(parts) != 2:
        return None
    try:
        qty = int(parts[0])
    except ValueError:
        return None
    unit_days = _IBKR_DURATION_UNIT_DAYS.get(parts[1].upper())
    if unit_days is None:
        return None
    return qty * unit_days


def _ibkr_normalize_bar_size(bar_size: str) -> str:
    return " ".join(bar_size.strip().lower().split())


def _ibkr_historical_chunk_plan(bar_size: str, duration: str) -> list[_IbkrHistoricalChunk]:
    total_days = _ibkr_duration_days(duration)
    chunk_spec = _IBKR_BAR_SIZE_MAX_CHUNK.get(_ibkr_normalize_bar_size(bar_size))
    if total_days is None or chunk_spec is None:
        return [_IbkrHistoricalChunk(duration=duration)]

    chunk_duration, chunk_days = chunk_spec
    if total_days <= chunk_days:
        return [_IbkrHistoricalChunk(duration=duration)]

    chunk_count = max(1, (total_days + chunk_days - 1) // chunk_days)
    return [_IbkrHistoricalChunk(duration=chunk_duration) for _ in range(chunk_count)]


def _ibkr_bar_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (TypeError, ValueError):
        return None


def _ibkr_end_before_bars(bars: list[Any]) -> str:
    if not bars:
        return ""
    dt = _ibkr_bar_datetime(getattr(bars[0], "date", None))
    if dt is None:
        return ""
    return (dt - timedelta(seconds=1)).strftime("%Y%m%d %H:%M:%S UTC")


def _import_ibkr_bridge() -> tuple:
    """Lazily resolve the sibling `ibkr_bridge` package and ib_async.

    The package may live as either:
        * <here>/../ibkr_bridge/   (ict-engine source layout)
        * <here>/support/scripts/ibkr_bridge/   (Auto-Quant deploy layout where
          fetch_external.py sits at repo root)

    Raises a clear error when not found so users know to run setup first.
    """
    here = Path(__file__).resolve().parent
    candidates = [here.parent, here / "scripts", Path.cwd() / "scripts"]
    for cand in candidates:
        if (cand / "ibkr_bridge" / "__init__.py").exists():
            if str(cand) not in sys.path:
                sys.path.insert(0, str(cand))
            break
    try:
        from ibkr_bridge.client_id import connect_with_client_id_fallback  # noqa: WPS433
        from ibkr_bridge.consent import require_ibkr_enabled  # noqa: WPS433
        from ibkr_bridge.rate_limiter import IbkrRateLimiter  # noqa: WPS433
    except ImportError as exc:
        raise SystemExit(
            "ibkr-historical requires the ibkr_bridge package. "
            "Make sure support/scripts/ibkr_bridge/ is reachable from sys.path "
            f"(searched: {[str(c) for c in candidates]}). "
            f"Underlying error: {exc}"
        )
    try:
        import ib_async  # noqa: WPS433  (lazy import keeps non-IBKR sub-commands light)
    except ImportError as exc:
        raise SystemExit(
            "ibkr-historical requires `ib_async`. Install via:\n"
            "    cd ~/Auto-Quant && uv add 'ib_async>=2.0,<3.0'\n"
            f"Underlying error: {exc}"
        )
    return require_ibkr_enabled, IbkrRateLimiter, connect_with_client_id_fallback, ib_async


def _probe_tcp_port(host: str, port: int, timeout: float = IBKR_GATEWAY_PROBE_TIMEOUT_SECONDS) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _reachable_ibkr_gateway_ports(host: str, probe=_probe_tcp_port) -> list[tuple[str, int]]:
    reachable = []
    for label, port in IBKR_GATEWAY_PORT_CANDIDATES:
        if probe(host, port):
            reachable.append((label, port))
    return reachable


def _resolve_ibkr_gateway_port(
    host: str,
    explicit_port: int | None,
    *,
    purpose: str,
    probe=_probe_tcp_port,
) -> int:
    if explicit_port is not None:
        return explicit_port

    reachable = _reachable_ibkr_gateway_ports(host, probe=probe)
    if not reachable:
        candidates = ", ".join(f"{label}:{port}" for label, port in IBKR_GATEWAY_PORT_CANDIDATES)
        raise SystemExit(
            f"{purpose}: no reachable local IBKR API port on {host}; "
            f"probed {candidates}. Launch TWS/IB Gateway with API enabled or pass --port explicitly."
        )

    selected_label, selected_port = reachable[0]
    if len(reachable) == 1:
        print(
            f"  {purpose}: auto-selected {selected_label} port {selected_port}",
            file=sys.stderr,
        )
    else:
        choices = ", ".join(f"{label}:{port}" for label, port in reachable)
        print(
            f"  {purpose}: multiple reachable IBKR ports ({choices}); "
            f"using {selected_label}:{selected_port}. Pass --port to override.",
            file=sys.stderr,
        )
    return selected_port


async def _ibkr_retry_empty_historical_request(
    request_once: Callable[[], Awaitable[Any]],
    reconnect_once: Callable[[], Awaitable[None]],
    *,
    should_retry: Callable[[], bool] | None = None,
    max_attempts: int = 2,
) -> tuple[Any, int]:
    bars = []
    for attempt in range(1, max_attempts + 1):
        bars = await request_once()
        if bars:
            return bars, attempt
        if should_retry is not None and not should_retry():
            return bars, attempt
        if attempt < max_attempts:
            await reconnect_once()
    return bars, max_attempts


@dataclass(frozen=True)
class _IbkrHistoricalRequestErrorClassification:
    category: str
    retryable: bool


def _ibkr_classify_historical_request_error(
    error_code: int,
    error_message: str,
) -> _IbkrHistoricalRequestErrorClassification:
    lowered = (error_message or "").lower()
    if "different ip address" in lowered:
        return _IbkrHistoricalRequestErrorClassification(
            category="broker_session_authority_blocked",
            retryable=False,
        )
    if error_code == 10197 or "competing live session" in lowered:
        return _IbkrHistoricalRequestErrorClassification(
            category="competing_live_session",
            retryable=False,
        )
    if error_code in {162, 165} and (
        "returned no data" in lowered
        or "no data" in lowered
        or "未返回数据" in error_message
    ):
        return _IbkrHistoricalRequestErrorClassification(
            category="historical_no_data",
            retryable=False,
        )
    if error_code == 200:
        return _IbkrHistoricalRequestErrorClassification(
            category="contract_resolution_failed",
            retryable=False,
        )
    return _IbkrHistoricalRequestErrorClassification(
        category="request_error",
        retryable=True,
    )


def _ibkr_contract_to_dict(contract: Any) -> dict[str, Any]:
    fields = [
        "conId",
        "symbol",
        "secType",
        "exchange",
        "primaryExchange",
        "currency",
        "lastTradeDateOrContractMonth",
        "multiplier",
        "localSymbol",
        "tradingClass",
        "strike",
        "right",
    ]
    return {field: getattr(contract, field, None) for field in fields}


def _ibkr_contract_detail_to_dict(detail: Any) -> dict[str, Any]:
    fields = [
        "marketName",
        "minTick",
        "orderTypes",
        "validExchanges",
        "priceMagnifier",
        "underConId",
        "longName",
        "contractMonth",
        "industry",
        "category",
        "subcategory",
        "timeZoneId",
        "tradingHours",
        "liquidHours",
        "marketRuleIds",
        "realExpirationDate",
        "lastTradeTime",
        "stockType",
        "minSize",
        "sizeIncrement",
        "suggestedSizeIncrement",
    ]
    out = {field: getattr(detail, field, None) for field in fields}
    out["contract"] = _ibkr_contract_to_dict(getattr(detail, "contract", None))
    return out


def _ibkr_contract_detail_packet(
    args: argparse.Namespace,
    qualified_contract: Any,
    details: list[Any],
    *,
    selected_client_id: int | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "ibkr-contract-details/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "request": {
            "symbol": args.symbol,
            "sec_type": args.sec_type,
            "exchange": args.exchange,
            "currency": args.currency,
            "primary_exchange": args.primary_exchange,
            "last_trade_date": args.last_trade_date,
            "multiplier": args.multiplier,
            "strike": args.strike,
            "right": args.right,
        },
        "selected_client_id": selected_client_id,
        "qualified_contract": _ibkr_contract_to_dict(qualified_contract),
        "contract_details_count": len(details),
        "contract_details": [_ibkr_contract_detail_to_dict(detail) for detail in details],
        "historical_fetch_launched": False,
        "promotion_evidence": False,
        "promotion_note": (
            "IBKR contract details can verify contract identity/session fields, "
            "but do not by themselves verify broker/exchange/regulatory cost model "
            "or practical trade usability."
        ),
    }


def _build_ibkr_contract(args: argparse.Namespace, ib_async_mod):
    def normalize_fut_contract_month(value: str | None) -> str:
        raw = (value or "").strip()
        if len(raw) == 8 and raw.isdigit():
            return raw[:6]
        return raw

    sec = args.sec_type.upper()
    if sec == "STK":
        c = ib_async_mod.Stock(args.symbol, args.exchange, args.currency)
        if args.primary_exchange:
            c.primaryExchange = args.primary_exchange
        return c
    if sec == "CASH":
        return ib_async_mod.Forex(args.symbol)
    if sec == "FUT":
        return ib_async_mod.Future(
            args.symbol,
            normalize_fut_contract_month(args.last_trade_date),
                                    args.exchange, currency=args.currency,
                                    multiplier=args.multiplier or "",
        )
    if sec == "IND":
        return ib_async_mod.Index(args.symbol, args.exchange, args.currency)
    if sec == "OPT":
        if args.last_trade_date is None or args.strike is None or args.right is None:
            raise SystemExit("OPT needs --last-trade-date, --strike, --right")
        return ib_async_mod.Option(args.symbol, args.last_trade_date, args.strike,
                                    args.right, args.exchange,
                                    currency=args.currency,
                                    multiplier=args.multiplier or "100")
    raise SystemExit(f"unsupported --sec-type {args.sec_type!r}")


async def _ibkr_contract_details_async(args: argparse.Namespace) -> int:
    require_ibkr_enabled, IbkrRateLimiter, connect_with_client_id_fallback, ib_async = _import_ibkr_bridge()
    require_ibkr_enabled()

    limiter = IbkrRateLimiter(redis_url=args.redis_url)
    contract = _build_ibkr_contract(args, ib_async)
    args.port = _resolve_ibkr_gateway_port(
        args.host,
        args.port,
        purpose="ibkr-contract-details",
    )

    ib = ib_async.IB()
    ib.RaiseRequestErrors = True
    selected_client_id: int | None = None
    try:
        await limiter.wait_for_outbound_msg()
        try:
            selected_client_id, attempted_conflicts = await connect_with_client_id_fallback(
                ib,
                host=args.host,
                port=args.port,
                preferred_client_id=args.client_id,
                readonly=True,
            )
            if attempted_conflicts:
                print(
                    f"  ibkr-contract-details: clientId fallback selected {selected_client_id} "
                    f"after conflicts {[client_id for client_id, _ in attempted_conflicts]}",
                    file=sys.stderr,
                )
        except (ConnectionError, OSError, RuntimeError) as exc:
            raise SystemExit(
                f"Cannot reach IBKR Gateway at {args.host}:{args.port} "
                f"(clientId={args.client_id}). Is IB Gateway / TWS running "
                f"and API enabled? Underlying error: {exc}"
            )

        await limiter.wait_for_outbound_msg()
        qualified = await ib.qualifyContractsAsync(contract)
        if not qualified or qualified[0] is None:
            raise SystemExit(f"contract not resolved: {args.symbol}")
        qualified_contract = qualified[0]

        await limiter.wait_for_outbound_msg()
        details = await ib.reqContractDetailsAsync(qualified_contract)
        packet = _ibkr_contract_detail_packet(
            args,
            qualified_contract,
            list(details or []),
            selected_client_id=selected_client_id,
        )
        out = Path(args.output).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
        print(
            f"ibkr contract-details {args.symbol} ({args.sec_type}): "
            f"{len(details or []):,} detail(s) -> {out}",
            file=sys.stderr,
        )
        return 0
    finally:
        try:
            if ib.isConnected():
                ib.disconnect()
        except Exception:
            pass


async def _ibkr_historical_async(args: argparse.Namespace) -> int:
    require_ibkr_enabled, IbkrRateLimiter, connect_with_client_id_fallback, ib_async = _import_ibkr_bridge()
    require_ibkr_enabled()

    limiter = IbkrRateLimiter(redis_url=args.redis_url)
    contract = _build_ibkr_contract(args, ib_async)
    args.port = _resolve_ibkr_gateway_port(
        args.host,
        args.port,
        purpose="ibkr-historical",
    )

    # Use the symbol as a stable identifier for the per-contract 6.5s lock.
    # (conId would be more precise but requires qualifying first, which itself
    # costs an outbound msg; the symbol-level lock is good enough for fetch.)
    rl_id = f"{args.symbol}:{args.sec_type}"
    chunk_plan = _ibkr_historical_chunk_plan(args.bar_size, args.duration)
    all_bars = []
    current_end = args.end or ""
    if len(chunk_plan) > 1:
        print(
            f"  ibkr-historical: split {args.bar_size} {args.duration} into "
            f"{len(chunk_plan)} request chunk(s) of {chunk_plan[0].duration}",
            file=sys.stderr,
        )

    def new_ib_client():
        client = ib_async.IB()
        client.RaiseRequestErrors = True
        return client

    ib = new_ib_client()

    async def connect_and_qualify() -> None:
        nonlocal contract
        await limiter.wait_for_outbound_msg()
        try:
            selected_client_id, attempted_conflicts = await connect_with_client_id_fallback(
                ib,
                host=args.host,
                port=args.port,
                preferred_client_id=args.client_id,
                readonly=True,
            )
            if attempted_conflicts:
                print(
                    f"  ibkr-historical: clientId fallback selected {selected_client_id} "
                    f"after conflicts {[client_id for client_id, _ in attempted_conflicts]}",
                    file=sys.stderr,
                )
        except (ConnectionError, OSError, RuntimeError) as exc:
            raise SystemExit(
                f"Cannot reach IBKR Gateway at {args.host}:{args.port} "
                f"(clientId={args.client_id}). Is IB Gateway / TWS running "
                f"and API enabled? Underlying error: {exc}"
            )

        if args.market_data_type != 1:
            await limiter.wait_for_outbound_msg()
            ib.reqMarketDataType(args.market_data_type)
        await limiter.wait_for_outbound_msg()
        qualified = await ib.qualifyContractsAsync(_build_ibkr_contract(args, ib_async))
        if not qualified or qualified[0] is None:
            raise SystemExit(f"contract not resolved: {args.symbol}")
        contract = qualified[0]

    async def reconnect_and_requalify() -> None:
        nonlocal ib
        ib.disconnect()
        ib = new_ib_client()
        print(
            f"  ibkr-historical: empty historical response for {args.symbol}; reconnecting and retrying once",
            file=sys.stderr,
        )
        await connect_and_qualify()

    try:
        await connect_and_qualify()

        for index, chunk in enumerate(chunk_plan, 1):
            last_request_error: _IbkrHistoricalRequestErrorClassification | None = None

            async def request_chunk():
                nonlocal last_request_error
                last_request_error = None
                await limiter.wait_for_historical(rl_id, args.bar_size, args.what_to_show)
                await limiter.acquire_historical_slot()
                try:
                    await limiter.wait_for_outbound_msg()
                    try:
                        return await ib.reqHistoricalDataAsync(
                            contract,
                            endDateTime=current_end,
                            durationStr=chunk.duration,
                            barSizeSetting=args.bar_size,
                            whatToShow=args.what_to_show,
                            useRTH=bool(args.rth),
                            formatDate=2,           # epoch seconds, easier downstream
                            keepUpToDate=False,
                            timeout=args.request_timeout,
                        )
                    except ib_async.RequestError as exc:
                        last_request_error = _ibkr_classify_historical_request_error(exc.code, exc.message)
                        print(
                            f"WARN: ibkr historical request error for {args.symbol} "
                            f"({args.bar_size} {chunk.duration} {args.what_to_show}; "
                            f"code={exc.code}; category={last_request_error.category}): "
                            f"{exc.message}",
                            file=sys.stderr,
                        )
                        if not last_request_error.retryable:
                            print(
                                f"  ibkr-historical: not retrying {args.symbol} after "
                                f"{last_request_error.category}",
                                file=sys.stderr,
                            )
                        return []
                finally:
                    limiter.release_historical_slot()

            chunk_bars, used_attempts = await _ibkr_retry_empty_historical_request(
                request_chunk,
                reconnect_and_requalify,
                should_retry=lambda: last_request_error is None or last_request_error.retryable,
            )
            if not chunk_bars:
                print(
                    f"WARN: ibkr historical chunk empty for {args.symbol} "
                    f"({args.bar_size} {chunk.duration} {args.what_to_show}; "
                    f"chunk {index}/{len(chunk_plan)}; attempts={used_attempts})",
                    file=sys.stderr,
                )
                break
            if used_attempts > 1:
                print(
                    f"  ibkr-historical: recovered {args.symbol} {args.bar_size} "
                    f"{chunk.duration} after reconnect retry",
                    file=sys.stderr,
                )
            all_bars.extend(chunk_bars)
            current_end = _ibkr_end_before_bars(chunk_bars)
            if not current_end:
                break
    finally:
        ib.disconnect()

    if not all_bars:
        print(f"WARN: ibkr historical empty for {args.symbol} "
              f"({args.bar_size} {args.duration} {args.what_to_show})",
              file=sys.stderr)
        return 3

    rows = []
    seen_ts = set()
    for b in all_bars:
        ts = getattr(b, "date", None)
        # ib_async timestamp shapes:
        #   * daily / weekly / monthly  -> datetime.date (no tz)
        #   * intraday w/ formatDate=2  -> datetime.datetime (UTC, may lack tzinfo)
        #   * occasional epoch seconds  -> int
        # Normalise everything to a tz-aware UTC ISO-8601 string.
        if isinstance(ts, datetime):
            ts_iso = ts.isoformat() if ts.tzinfo else ts.replace(tzinfo=timezone.utc).isoformat()
        elif hasattr(ts, "isoformat"):  # datetime.date — no time, no tz
            ts_iso = datetime(ts.year, ts.month, ts.day, tzinfo=timezone.utc).isoformat()
        else:
            try:
                ts_iso = datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
            except (TypeError, ValueError):
                ts_iso = str(ts)
        if ts_iso in seen_ts:
            continue
        seen_ts.add(ts_iso)
        rows.append({
            "ts": ts_iso,
            "open": getattr(b, "open", None),
            "high": getattr(b, "high", None),
            "low": getattr(b, "low", None),
            "close": getattr(b, "close", None),
            "volume": getattr(b, "volume", None),
            "wap": getattr(b, "average", None),
            "count": getattr(b, "barCount", None),
        })
    rows.sort(key=lambda row: row["ts"])

    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["ts", "open", "high", "low", "close", "volume", "wap", "count"]
    with out.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    first_ts = rows[0]["ts"]
    last_ts = rows[-1]["ts"]
    print(f"ibkr historical {args.symbol} ({args.sec_type}) {args.bar_size} "
          f"{args.duration} {args.what_to_show}: {len(rows):,} rows "
          f"({first_ts} -> {last_ts}) -> {out}")
    return 0


def cmd_ibkr_historical(args: argparse.Namespace) -> int:
    import asyncio
    return asyncio.run(_ibkr_historical_async(args))


def cmd_ibkr_contract_details(args: argparse.Namespace) -> int:
    import asyncio
    return asyncio.run(_ibkr_contract_details_async(args))


# ---------------------------------------------------------------------------
# ibkr-bulk : back-fill many (symbol, bar_size, what_to_show) into CSVs.
#
# Designed for backtest-dataset construction:
#   * one Gateway connection used for the whole batch (efficient)
#   * one CSV per output triple, idempotent (skip if file exists)
#   * full pacing-aware via the cross-process IbkrRateLimiter
#   * resilient: a single failed request does not abort the batch
# ---------------------------------------------------------------------------


_BAR_SIZE_FILE_SUFFIX = {
    "1 secs": "1sec", "5 secs": "5sec", "10 secs": "10sec",
    "15 secs": "15sec", "30 secs": "30sec",
    "1 min": "1min", "2 mins": "2min", "3 mins": "3min",
    "5 mins": "5min", "10 mins": "10min", "15 mins": "15min",
    "20 mins": "20min", "30 mins": "30min",
    "1 hour": "1h", "2 hours": "2h", "3 hours": "3h",
    "4 hours": "4h", "8 hours": "8h",
    "1 day": "1d", "1W": "1w", "1M": "1mo",
}


def _bulk_bar_suffix(bar_size: str) -> str:
    return _BAR_SIZE_FILE_SUFFIX.get(
        bar_size, bar_size.lower().replace(" ", "")
    )


def _bulk_render_path(template: str, output_dir: Path, symbol: str,
                        bar_size: str, what_to_show: str) -> Path:
    name = template.format(
        symbol=symbol,
        bar_suffix=_bulk_bar_suffix(bar_size),
        bar_size=bar_size.replace(" ", "_"),
        what=what_to_show.lower(),
    )
    return (output_dir / name).resolve()


def _bulk_write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["ts", "open", "high", "low", "close", "volume", "wap", "count"]
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _bulk_bars_to_rows(bars: list) -> list[dict]:
    out = []
    for b in bars:
        ts = getattr(b, "date", None)
        if isinstance(ts, datetime):
            ts_iso = (ts.isoformat() if ts.tzinfo
                       else ts.replace(tzinfo=timezone.utc).isoformat())
        elif hasattr(ts, "isoformat"):
            ts_iso = datetime(ts.year, ts.month, ts.day,
                                tzinfo=timezone.utc).isoformat()
        else:
            try:
                ts_iso = datetime.fromtimestamp(float(ts),
                                                   tz=timezone.utc).isoformat()
            except (TypeError, ValueError):
                ts_iso = str(ts)
        out.append({
            "ts": ts_iso,
            "open": getattr(b, "open", None),
            "high": getattr(b, "high", None),
            "low": getattr(b, "low", None),
            "close": getattr(b, "close", None),
            "volume": getattr(b, "volume", None),
            "wap": getattr(b, "average", None),
            "count": getattr(b, "barCount", None),
        })
    return out


def _bulk_expand_symbol_entry(entry: dict, defaults: dict) -> list[dict]:
    """Expand a single symbol YAML entry into one task per bar_size.

    A symbol may declare a single `bar_size` or a list `bar_sizes`. Other
    fields fall back to the global defaults block.
    """
    base = {
        "sec_type":          entry.get("sec_type", defaults.get("sec_type", "STK")),
        "exchange":          entry.get("exchange", defaults.get("exchange", "SMART")),
        "currency":          entry.get("currency", defaults.get("currency", "USD")),
        "primary_exchange":  entry.get("primary_exchange",
                                          defaults.get("primary_exchange")),
        "what_to_show":      entry.get("what_to_show",
                                          defaults.get("what_to_show", "TRADES")),
        "duration":          entry.get("duration",
                                          defaults.get("duration", "60 D")),
        "rth":               entry.get("rth", defaults.get("rth", True)),
        "last_trade_date":   entry.get("last_trade_date"),
        "strike":            entry.get("strike"),
        "right":             entry.get("right"),
        "multiplier":        entry.get("multiplier"),
    }
    if not entry.get("symbol"):
        raise ValueError(f"bulk symbol entry missing 'symbol': {entry!r}")

    bar_sizes = entry.get("bar_sizes") or [
        entry.get("bar_size", defaults.get("bar_size", "1 day"))
    ]
    return [{"symbol": entry["symbol"], "bar_size": bs, **base}
             for bs in bar_sizes]


def _bulk_build_contract(task: dict, ib_async_mod):
    def normalize_fut_contract_month(value: str | None) -> str:
        raw = (value or "").strip()
        if len(raw) == 8 and raw.isdigit():
            return raw[:6]
        return raw

    sec = task["sec_type"].upper()
    if sec == "STK":
        c = ib_async_mod.Stock(task["symbol"], task["exchange"], task["currency"])
        if task.get("primary_exchange"):
            c.primaryExchange = task["primary_exchange"]
        return c
    if sec == "CASH":
        return ib_async_mod.Forex(task["symbol"])
    if sec == "FUT":
        return ib_async_mod.Future(
            task["symbol"],
            normalize_fut_contract_month(task.get("last_trade_date")),
                                     task["exchange"], currency=task["currency"],
                                     multiplier=task.get("multiplier") or "",
        )
    if sec == "IND":
        return ib_async_mod.Index(task["symbol"], task["exchange"], task["currency"])
    if sec == "CRYPTO":
        return ib_async_mod.Crypto(task["symbol"], task["exchange"] or "PAXOS",
                                     task["currency"] or "USD")
    if sec == "OPT":
        if not (task.get("last_trade_date") and task.get("strike")
                and task.get("right")):
            raise ValueError(
                f"OPT bulk entry for {task['symbol']!r} requires "
                "last_trade_date + strike + right"
            )
        return ib_async_mod.Option(task["symbol"], task["last_trade_date"],
                                     task["strike"], task["right"],
                                     task["exchange"], currency=task["currency"],
                                     multiplier=task.get("multiplier") or "100")
    raise ValueError(f"unsupported sec_type {sec!r} for bulk task {task!r}")


async def _ibkr_bulk_async(args: argparse.Namespace) -> int:
    require_ibkr_enabled, IbkrRateLimiter, connect_with_client_id_fallback, ib_async = _import_ibkr_bridge()
    require_ibkr_enabled()

    try:
        import yaml  # noqa: WPS433
    except ImportError as exc:
        raise SystemExit(
            "ibkr-bulk requires PyYAML. Install via: uv add pyyaml. "
            f"Underlying error: {exc}"
        )

    config_path = Path(args.config).resolve()
    if not config_path.exists():
        raise SystemExit(f"bulk config not found: {config_path}")
    raw = yaml.safe_load(config_path.read_text()) or {}
    gw = raw.get("gateway") or {}
    gateway_host = gw.get("host", "127.0.0.1")
    gateway_port = _resolve_ibkr_gateway_port(
        gateway_host,
        int(gw["port"]) if gw.get("port") is not None else args.port,
        purpose="ibkr-bulk",
    )
    out = raw.get("output") or {}
    defaults = raw.get("defaults") or {}
    symbols = raw.get("symbols") or []
    if not symbols:
        raise SystemExit(f"bulk config has no `symbols`: {config_path}")

    output_dir = Path(out.get("directory") or args.output_dir or
                       "user_data/data/ibkr_bulk").resolve()
    template = out.get("filename_template") or "{symbol}_{bar_suffix}.csv"
    force = bool(out.get("force") if "force" in out else args.force)

    tasks: list[dict] = []
    for entry in symbols:
        tasks.extend(_bulk_expand_symbol_entry(entry, defaults))

    print(f"ibkr-bulk: {len(tasks)} task(s) -> {output_dir}",
          file=sys.stderr)

    limiter = IbkrRateLimiter(redis_url=args.redis_url)

    await limiter.wait_for_outbound_msg()
    ib = ib_async.IB()
    try:
        selected_client_id, attempted_conflicts = await connect_with_client_id_fallback(
            ib,
            host=gateway_host,
            port=gateway_port,
            preferred_client_id=int(gw.get("client_id", args.client_id)),
            readonly=True,
        )
        if attempted_conflicts:
            print(
                f"  ibkr-bulk: clientId fallback selected {selected_client_id} "
                f"after conflicts {[client_id for client_id, _ in attempted_conflicts]}",
                file=sys.stderr,
            )
    except (ConnectionError, OSError, RuntimeError) as exc:
        raise SystemExit(
            f"Cannot reach IBKR Gateway at "
            f"{gateway_host}:{gateway_port} "
            f"(clientId={gw.get('client_id', args.client_id)}). "
            f"Is IB Gateway / TWS running and API enabled? "
            f"Underlying error: {exc}"
        )

    n_ok = n_skip = n_empty = n_fail = 0
    try:
        for i, task in enumerate(tasks, 1):
            out_path = _bulk_render_path(template, output_dir, task["symbol"],
                                            task["bar_size"], task["what_to_show"])
            if out_path.exists() and not force:
                print(f"  [{i}/{len(tasks)}] skip (exists): {out_path.name}",
                      file=sys.stderr)
                n_skip += 1
                continue

            try:
                contract = _bulk_build_contract(task, ib_async)
            except ValueError as exc:
                print(f"  [{i}/{len(tasks)}] FAIL build_contract "
                      f"{task['symbol']}: {exc}", file=sys.stderr)
                n_fail += 1
                continue

            rl_id = f"{task['symbol']}:{task['sec_type']}"
            try:
                await limiter.wait_for_historical(rl_id, task["bar_size"],
                                                    task["what_to_show"])
                await limiter.acquire_historical_slot()
            except TimeoutError as exc:
                print(f"  [{i}/{len(tasks)}] FAIL pacing-gate "
                      f"{task['symbol']} {task['bar_size']}: {exc}",
                      file=sys.stderr)
                n_fail += 1
                continue

            try:
                await limiter.wait_for_outbound_msg()
                qualified = await ib.qualifyContractsAsync(contract)
                if not qualified or qualified[0] is None:
                    print(f"  [{i}/{len(tasks)}] FAIL qualify "
                          f"{task['symbol']}: contract not resolved",
                          file=sys.stderr)
                    n_fail += 1
                    continue
                contract = qualified[0]

                await limiter.wait_for_outbound_msg()
                bars = await ib.reqHistoricalDataAsync(
                    contract,
                    endDateTime="",
                    durationStr=task["duration"],
                    barSizeSetting=task["bar_size"],
                    whatToShow=task["what_to_show"],
                    useRTH=bool(task["rth"]),
                    formatDate=2,
                    keepUpToDate=False,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"  [{i}/{len(tasks)}] FAIL fetch "
                      f"{task['symbol']} {task['bar_size']}: "
                      f"{type(exc).__name__}: {exc}", file=sys.stderr)
                n_fail += 1
                continue
            finally:
                limiter.release_historical_slot()

            if not bars:
                print(f"  [{i}/{len(tasks)}] empty {task['symbol']} "
                      f"{task['bar_size']} {task['what_to_show']}",
                      file=sys.stderr)
                n_empty += 1
                continue

            rows = _bulk_bars_to_rows(bars)
            _bulk_write_csv(rows, out_path)
            print(f"  [{i}/{len(tasks)}] OK   {task['symbol']:8s} "
                  f"{task['bar_size']:8s} {task['what_to_show']:10s} "
                  f"{len(rows):6,} rows -> {out_path.name}",
                  file=sys.stderr)
            n_ok += 1
    finally:
        ib.disconnect()

    print(f"\nibkr-bulk done: ok={n_ok} skip={n_skip} empty={n_empty} "
          f"fail={n_fail}  ({len(tasks)} total)", file=sys.stderr)
    return 0 if n_fail == 0 else 4


def cmd_ibkr_bulk(args: argparse.Namespace) -> int:
    import asyncio
    return asyncio.run(_ibkr_bulk_async(args))


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

    hb = sub.add_parser("hubble-kline", help="OHLCV via opt-in Hubble V2 HTTP API")
    hb.add_argument("--market", required=True, choices=["cn", "hk", "us", "crypto"])
    hb.add_argument("--symbol", required=True,
                    help="cn=000001.SZ hk=00700.HK us=AAPL crypto=BTCUSDT")
    hb.add_argument("--exchange", default=None,
                    help="required for crypto, e.g. binance")
    hb.add_argument("--interval", default="1d",
                    help="cn:1d/1w/1mo hk/us:1d crypto:1m/5m/15m/1h/4h/1d/1w")
    hb.add_argument("--start", help="ISO start, e.g. 2024-01-01")
    hb.add_argument("--end", help="ISO end, e.g. 2024-12-31")
    hb.add_argument("--limit", type=int, default=None,
                    help="optional row limit; hk disables it, crypto usually uses it")
    hb.add_argument("--output", required=True)

    bk = sub.add_parser("bybit-kline", help="OHLCV via Bybit V5 public REST")
    bk.add_argument("--category", required=True,
                    choices=["spot", "linear", "inverse", "option"])
    bk.add_argument("--symbol", required=True,
                    help="e.g. BTCUSDT (spot/linear), BTCUSD (inverse), BTC-26APR26-50000-C (option)")
    bk.add_argument("--interval", default="1h",
                    help="1m/3m/5m/15m/30m/1h/2h/4h/6h/12h/1d/1w/1M (default 1h)")
    bk.add_argument("--start", required=True, help="ISO start, e.g. 2024-01-01")
    bk.add_argument("--end", required=True, help="ISO end, e.g. 2025-12-31")
    bk.add_argument("--output", required=True)

    bo = sub.add_parser("bybit-options", help="Bybit USDC option chain snapshot (BTC/ETH/SOL)")
    bo.add_argument("--base", required=True, choices=["BTC", "ETH", "SOL"])
    bo.add_argument("--expiry", help="filter by expiry, e.g. 26APR26")
    bo.add_argument("--output", required=True)

    kk = sub.add_parser("kraken-kline", help="OHLCV via Kraken public REST (spot or futures)")
    kk.add_argument("--market", default="spot", choices=["spot", "futures"])
    kk.add_argument("--pair", required=True,
                    help="spot e.g. XBTUSD / AAPLxUSD / ZEURZUSD; futures e.g. PF_XBTUSD / PF_SPXUSD")
    kk.add_argument("--asset-class", choices=["tokenized_asset", "forex"], default=None,
                    help="REQUIRED for spot xStocks (tokenized_asset) and fiat forex (forex)")
    kk.add_argument("--interval", default="1h",
                    help="spot: 1m/5m/15m/30m/1h/4h/1d/1w/15d; futures: 1m/5m/15m/30m/1h/4h/12h/1d/1w")
    kk.add_argument("--start", help="ISO start (futures only)")
    kk.add_argument("--end", help="ISO end (futures only)")
    kk.add_argument("--output", required=True)

    bnk = sub.add_parser("binance-kline", help="OHLCV via Binance Spot REST")
    bnk.add_argument("--symbol", required=True, help="e.g. BTCUSDT, ETHUSDT, SOLUSDT")
    bnk.add_argument("--interval", default="1h",
                    help="1m/3m/5m/15m/30m/1h/2h/4h/6h/8h/12h/1d/3d/1w/1M (default 1h)")
    bnk.add_argument("--start", required=True, help="ISO start")
    bnk.add_argument("--end", required=True, help="ISO end")
    bnk.add_argument("--output", required=True)

    bno = sub.add_parser("binance-options", help="Binance European option chain snapshot (BTC/ETH)")
    bno.add_argument("--underlying", required=True,
                     help="prefix match against contract underlying, e.g. BTC, ETH")
    bno.add_argument("--expiry", help="filter by expiry ISO date, e.g. 2026-04-26")
    bno.add_argument("--output", required=True)

    pmm = sub.add_parser("polymarket-markets", help="List Polymarket prediction markets (Gamma API)")
    pmm.add_argument("--limit", type=int, default=20)
    pmm.add_argument("--offset", type=int, default=0)
    pmm.add_argument("--active", choices=["true", "false"], default=None)
    pmm.add_argument("--closed", choices=["true", "false"], default=None)
    pmm.add_argument("--tag", help="tag_id filter (e.g. 'politics' if API expects slug)")
    pmm.add_argument("--order", help="e.g. volume_num, liquidity_num")
    pmm.add_argument("--format", choices=["csv", "json"], default="csv")
    pmm.add_argument("--output", required=True)

    pmh = sub.add_parser("polymarket-history", help="Polymarket CLOB price history for one token")
    pmh.add_argument("--token", required=True, help="clobTokenId for one outcome side")
    pmh.add_argument("--interval", default="1d", choices=["1m", "1h", "6h", "1d", "1w", "max"])
    pmh.add_argument("--days", type=int, default=30, help="lookback in days from now")
    pmh.add_argument("--fidelity", type=int, help="optional sampling fidelity in resolution units")
    pmh.add_argument("--output", required=True)

    ibh = sub.add_parser("ibkr-historical",
                          help="OHLCV via local IBKR Gateway (opt-in; see support/scripts/ibkr_bridge/setup.py)")
    ibh.add_argument("--symbol", required=True,
                      help="e.g. AAPL (STK), EURUSD (CASH), ES (FUT), SPX (IND)")
    ibh.add_argument("--sec-type", default="STK",
                      choices=["STK", "CASH", "FUT", "IND", "OPT"])
    ibh.add_argument("--exchange", default="SMART",
                      help="STK=SMART, CASH=IDEALPRO, FUT=CME/NYMEX/etc., IND=CBOE/NASDAQ, OPT=SMART")
    ibh.add_argument("--currency", default="USD")
    ibh.add_argument("--primary-exchange", default=None,
                      help="STK only; e.g. NASDAQ, NYSE — disambiguates dual-listed tickers")
    ibh.add_argument("--bar-size", default="1 day",
                      help="IBKR bar size: '1 sec', '5 secs', '1 min', '5 mins', '1 hour', '1 day', '1 week', '1 month'")
    ibh.add_argument("--duration", default="1 Y",
                      help="IBKR duration: e.g. '60 D', '6 M', '1 Y', '5 Y'")
    ibh.add_argument("--what-to-show", default="TRADES",
                      choices=["TRADES", "MIDPOINT", "BID", "ASK", "BID_ASK",
                               "ADJUSTED_LAST", "HISTORICAL_VOLATILITY",
                               "OPTION_IMPLIED_VOLATILITY"])
    ibh.add_argument("--end", default="",
                      help="endDateTime in IBKR format 'YYYYMMDD HH:MM:SS UTC'; empty = now")
    ibh.add_argument("--rth", action="store_true",
                      help="Restrict to regular trading hours (default: include all sessions)")
    ibh.add_argument("--last-trade-date", default=None,
                      help="FUT/OPT contract month/expiry, e.g. '20260619'")
    ibh.add_argument("--strike", type=float, default=None, help="OPT strike")
    ibh.add_argument("--right", choices=["C", "P"], default=None, help="OPT side")
    ibh.add_argument("--multiplier", default=None, help="FUT/OPT contract multiplier")
    ibh.add_argument("--host", default="127.0.0.1")
    ibh.add_argument("--port", type=int, default=None,
                      help="Explicit local IBKR API port. When omitted, probes 7497, 7496, 4002, and 4001.")
    ibh.add_argument("--client-id", type=int, default=21,
                      help="Bridge uses 20; this defaults to 21 to avoid clash")
    ibh.add_argument("--market-data-type", type=int, default=1, choices=[1, 2, 3, 4],
                      help="1=live, 2=frozen, 3=delayed, 4=delayed-frozen; use 3 to test delayed fallback")
    ibh.add_argument("--request-timeout", type=float, default=180.0,
                      help="Seconds to wait for one IBKR reqHistoricalData response before treating it as empty")
    ibh.add_argument("--redis-url", default="redis://localhost:6379",
                      help="Cross-process IbkrRateLimiter coordinator")
    ibh.add_argument("--output", required=True)

    ibd = sub.add_parser("ibkr-contract-details",
                          help="Qualified contract details/secdef via local IBKR Gateway (no historical fetch)")
    ibd.add_argument("--symbol", required=True,
                      help="e.g. AAPL (STK), EURUSD (CASH), ES (FUT), SPX (IND)")
    ibd.add_argument("--sec-type", default="STK",
                      choices=["STK", "CASH", "FUT", "IND", "OPT"])
    ibd.add_argument("--exchange", default="SMART",
                      help="STK=SMART, CASH=IDEALPRO, FUT=CME/NYMEX/etc., IND=CBOE/NASDAQ, OPT=SMART")
    ibd.add_argument("--currency", default="USD")
    ibd.add_argument("--primary-exchange", default=None,
                      help="STK only; e.g. NASDAQ, NYSE — disambiguates dual-listed tickers")
    ibd.add_argument("--last-trade-date", default=None,
                      help="FUT/OPT contract month/expiry, e.g. '20260619'")
    ibd.add_argument("--strike", type=float, default=None, help="OPT strike")
    ibd.add_argument("--right", choices=["C", "P"], default=None, help="OPT side")
    ibd.add_argument("--multiplier", default=None, help="FUT/OPT contract multiplier")
    ibd.add_argument("--host", default="127.0.0.1")
    ibd.add_argument("--port", type=int, default=None,
                      help="Explicit local IBKR API port. When omitted, probes 7497, 7496, 4002, and 4001.")
    ibd.add_argument("--client-id", type=int, default=23,
                      help="Bridge uses 20; historical defaults to 21; contract details defaults to 23")
    ibd.add_argument("--redis-url", default="redis://localhost:6379",
                      help="Cross-process IbkrRateLimiter coordinator")
    ibd.add_argument("--output", required=True)

    ibb = sub.add_parser("ibkr-bulk",
                          help="Batch back-fill many (symbol, bar_size, what_to_show) "
                               "into one CSV per task — for backtest dataset construction.")
    ibb.add_argument("--config", required=True,
                      help="YAML with gateway/output/defaults/symbols sections; "
                           "see support/scripts/ibkr_bridge/examples/bulk_dataset.yaml")
    ibb.add_argument("--output-dir", default=None,
                      help="Override `output.directory` from YAML.")
    ibb.add_argument("--force", action="store_true",
                      help="Re-fetch even if the target CSV already exists.")
    ibb.add_argument("--host", default="127.0.0.1")
    ibb.add_argument("--port", type=int, default=None,
                      help="Used only if YAML doesn't specify gateway.port; omitted = auto-probe 7497, 7496, 4002, 4001.")
    ibb.add_argument("--client-id", type=int, default=22,
                      help="Bridge=20, fetch_external single=21; bulk defaults to 22")
    ibb.add_argument("--redis-url", default="redis://localhost:6379")

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
    if args.provider == "hubble-kline":
        return cmd_hubble_kline(args)
    if args.provider == "bybit-kline":
        return cmd_bybit_kline(args)
    if args.provider == "bybit-options":
        return cmd_bybit_options(args)
    if args.provider == "kraken-kline":
        return cmd_kraken_kline(args)
    if args.provider == "binance-kline":
        return cmd_binance_kline(args)
    if args.provider == "binance-options":
        return cmd_binance_options(args)
    if args.provider == "polymarket-markets":
        return cmd_polymarket_markets(args)
    if args.provider == "polymarket-history":
        return cmd_polymarket_history(args)
    if args.provider == "ibkr-historical":
        return cmd_ibkr_historical(args)
    if args.provider == "ibkr-contract-details":
        return cmd_ibkr_contract_details(args)
    if args.provider == "ibkr-bulk":
        return cmd_ibkr_bulk(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
