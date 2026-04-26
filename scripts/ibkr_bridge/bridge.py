"""IBKR live data bridge — single producer, Redis Streams fan-out.

Connects to TWS / IB Gateway via ``ib_async``, subscribes to instruments
listed in a YAML config, and publishes every bar / tick / snapshot to local
Redis as Streams + Hash entries. Multiple consumers (Auto-Quant strategies,
ict-engine research scripts, ad-hoc notebooks) read from Redis without
touching IBKR directly.

Redis key layout
----------------

    ibkr:bars:{symbol}:5sec        Stream  — 5-second OHLCV bars
    ibkr:ticks:{symbol}            Stream  — bid/ask/last quote ticks
    ibkr:snapshot:{symbol}         Hash    — latest known values
    ibkr:bridge:status             Hash    — bridge liveness for consumers

Consumers should call ``XREAD`` with cursor IDs for streams and ``HGETALL``
for snapshots. See ``consumer.py`` for the canonical helper.

The bridge respects ``IbkrRateLimiter`` for every IBKR API call (so that
``fetch_external.py ibkr-historical`` running in parallel cannot accidentally
exceed the account budget).
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import math
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import redis
import yaml
from ib_async import (
    IB,
    Contract,
    Forex,
    Future,
    Stock,
    Index,
    Option,
    RealTimeBar,
)

from .account_prober import probe_account
from .consent import require_ibkr_enabled
from .rate_limiter import (
    CAPABILITIES_PATH,
    IbkrCapabilities,
    IbkrRateLimiter,
)

DEFAULT_REDIS_URL = "redis://localhost:6379"
DEFAULT_GATEWAY_HOST = "127.0.0.1"
DEFAULT_GATEWAY_PORT = 7497
DEFAULT_BRIDGE_CLIENT_ID = 20
DEFAULT_STREAM_MAXLEN = 10000

RECONNECT_BACKOFF_S = [5, 15, 45, 120]


# ---------------------------------------------------------------------------
# Config


@dataclass
class SubscriptionSpec:
    symbol: str
    sec_type: str = "STK"
    exchange: str = "SMART"
    currency: str = "USD"
    feed: list[str] = field(default_factory=lambda: ["real_time_bars"])
    # Optional contract qualifiers
    last_trade_date: str | None = None      # FUT, OPT
    strike: float | None = None             # OPT
    right: str | None = None                # OPT 'C'/'P'
    multiplier: str | None = None           # FUT, OPT
    primary_exchange: str | None = None     # STK with disambiguation


@dataclass
class GatewayConfig:
    host: str = DEFAULT_GATEWAY_HOST
    port: int = DEFAULT_GATEWAY_PORT
    client_id: int = DEFAULT_BRIDGE_CLIENT_ID


@dataclass
class RedisConfig:
    url: str = DEFAULT_REDIS_URL


@dataclass
class PublishingConfig:
    stream_maxlen: int = DEFAULT_STREAM_MAXLEN
    snapshot_ttl_sec: int = 0  # 0 = no expire


@dataclass
class BridgeConfig:
    gateway: GatewayConfig = field(default_factory=GatewayConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    publishing: PublishingConfig = field(default_factory=PublishingConfig)
    subscriptions: list[SubscriptionSpec] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> "BridgeConfig":
        if not path.exists():
            raise FileNotFoundError(f"bridge config not found at {path}")
        raw = yaml.safe_load(path.read_text()) or {}
        gw = GatewayConfig(**(raw.get("gateway") or {}))
        rd = RedisConfig(**(raw.get("redis") or {}))
        pb = PublishingConfig(**(raw.get("publishing") or {}))
        subs = [SubscriptionSpec(**s) for s in (raw.get("subscriptions") or [])]
        return cls(gateway=gw, redis=rd, publishing=pb, subscriptions=subs)


# ---------------------------------------------------------------------------
# Contract construction


def _build_contract(spec: SubscriptionSpec) -> Contract:
    """Translate a SubscriptionSpec into an ib_async Contract."""
    sec = spec.sec_type.upper()
    if sec == "STK":
        c = Stock(spec.symbol, spec.exchange, spec.currency)
        if spec.primary_exchange:
            c.primaryExchange = spec.primary_exchange
        return c
    if sec == "CASH":
        return Forex(spec.symbol)  # 'EURUSD' style
    if sec == "FUT":
        return Future(spec.symbol, spec.last_trade_date or "",
                       spec.exchange, currency=spec.currency,
                       multiplier=spec.multiplier or "")
    if sec == "IND":
        return Index(spec.symbol, spec.exchange, spec.currency)
    if sec == "OPT":
        if spec.last_trade_date is None or spec.strike is None or spec.right is None:
            raise ValueError(
                f"OPT subscription for {spec.symbol!r} needs "
                "last_trade_date, strike, and right"
            )
        return Option(spec.symbol, spec.last_trade_date, spec.strike,
                       spec.right, spec.exchange, currency=spec.currency,
                       multiplier=spec.multiplier or "100")
    raise ValueError(f"unsupported sec_type {spec.sec_type!r} for {spec.symbol!r}")


# ---------------------------------------------------------------------------
# Bridge


class IbkrBridge:
    """Owns the persistent IBKR connection and the Redis publisher.

    Lifecycle:
        b = IbkrBridge(config)
        await b.start()       # connects, subscribes, runs until cancelled
        await b.stop()        # graceful disconnect, line release, save caps
    """

    def __init__(self, config: BridgeConfig,
                 capabilities_path: Path = CAPABILITIES_PATH) -> None:
        self.config = config
        self.ib = IB()
        self._capabilities_path = capabilities_path
        self._redis = redis.Redis.from_url(config.redis.url, decode_responses=True)
        self._limiter = IbkrRateLimiter(redis_url=config.redis.url,
                                          capabilities_path=capabilities_path)
        self._active_subscriptions: dict[str, dict[str, Any]] = {}
        self._stop_event = asyncio.Event()

        # Wire IBKR error -> rate-limiter feedback
        self.ib.errorEvent += self._on_ib_error
        self.ib.disconnectedEvent += self._on_disconnected

    # ----- Public lifecycle ----------------------------------------------

    async def start(self) -> None:
        """Run forever: connect, subscribe, pump events, reconnect on drop."""
        self._publish_status("starting")
        attempt = 0
        while not self._stop_event.is_set():
            try:
                await self._connect_and_subscribe()
                attempt = 0
                self._publish_status("running")
                await self._run_until_disconnect()
            except asyncio.CancelledError:
                break
            except (ConnectionError, RuntimeError, OSError) as exc:
                wait = RECONNECT_BACKOFF_S[min(attempt, len(RECONNECT_BACKOFF_S) - 1)]
                attempt += 1
                self._publish_status(f"reconnecting in {wait}s")
                self._log(f"connect/subscribe error: {exc}; retry in {wait}s "
                          f"(attempt {attempt})")
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=wait)
                except asyncio.TimeoutError:
                    pass

    async def stop(self) -> None:
        """Graceful shutdown — release lines, disconnect, save caps."""
        self._stop_event.set()
        self._publish_status("stopping")
        for symbol, sub in list(self._active_subscriptions.items()):
            try:
                self._cancel_subscription(symbol, sub)
            except Exception as exc:  # noqa: BLE001
                self._log(f"unsubscribe {symbol} failed: {exc}")
        self._limiter.reset_streaming_lines()
        if self.ib.isConnected():
            self.ib.disconnect()
        self._limiter.caps.save(self._capabilities_path)
        self._publish_status("stopped")

    # ----- Connection + subscription -------------------------------------

    async def _connect_and_subscribe(self) -> None:
        cfg = self.config
        self._log(f"connecting to {cfg.gateway.host}:{cfg.gateway.port} "
                  f"as clientId={cfg.gateway.client_id}")
        await self._limiter.wait_for_outbound_msg()
        await self.ib.connectAsync(host=cfg.gateway.host,
                                    port=cfg.gateway.port,
                                    clientId=cfg.gateway.client_id,
                                    readonly=True)

        # First-connect probe if capabilities are unknown
        if self._limiter.caps.account_type == "unknown":
            try:
                managed = list(self.ib.managedAccounts() or [])
                if not managed:
                    await asyncio.sleep(1.0)
                    managed = list(self.ib.managedAccounts() or [])
                if managed:
                    from .account_prober import _classify
                    self._limiter.caps.account_type = _classify(managed, cfg.gateway.port)
                    self._limiter.caps.n_subaccounts = len(managed)
                    self._limiter.caps.save(self._capabilities_path)
                    self._log(f"detected account_type={self._limiter.caps.account_type} "
                              f"n_subaccounts={self._limiter.caps.n_subaccounts}")
            except Exception as exc:  # noqa: BLE001
                self._log(f"managed-accounts probe skipped: {exc}")

        if not cfg.subscriptions:
            self._log("no subscriptions configured (idle bridge)")
            return

        # Subscribe in priority order (config order), respecting line cap
        for spec in cfg.subscriptions:
            if not self._limiter.acquire_streaming_line(spec.symbol):
                self._log(f"line cap reached; skipping {spec.symbol}")
                continue
            try:
                await self._subscribe_one(spec)
            except Exception as exc:  # noqa: BLE001
                self._limiter.release_streaming_line(spec.symbol)
                self._log(f"subscribe {spec.symbol} failed: {exc}")

    async def _subscribe_one(self, spec: SubscriptionSpec) -> None:
        contract = _build_contract(spec)
        await self._limiter.wait_for_outbound_msg()
        qualified = await self.ib.qualifyContractsAsync(contract)
        if not qualified:
            raise RuntimeError(f"contract not resolved: {spec.symbol}")
        contract = qualified[0]

        active: dict[str, Any] = {"contract": contract, "feeds": {}}
        feeds = [f.lower() for f in (spec.feed or ["real_time_bars"])]

        if "real_time_bars" in feeds:
            await self._limiter.wait_for_outbound_msg()
            bars = self.ib.reqRealTimeBars(contract, 5, "TRADES", useRTH=False)
            bars.updateEvent += self._make_bar_handler(spec.symbol)
            active["feeds"]["real_time_bars"] = bars

        if "market_data" in feeds:
            await self._limiter.wait_for_outbound_msg()
            ticker = self.ib.reqMktData(contract, "", snapshot=False,
                                          regulatorySnapshot=False)
            ticker.updateEvent += self._make_tick_handler(spec.symbol)
            active["feeds"]["market_data"] = ticker

        self._active_subscriptions[spec.symbol] = active
        self._log(f"subscribed {spec.symbol} feeds={list(active['feeds'])}")

    def _cancel_subscription(self, symbol: str, sub: dict[str, Any]) -> None:
        feeds = sub.get("feeds", {})
        bars = feeds.get("real_time_bars")
        if bars is not None:
            with contextlib.suppress(Exception):
                self.ib.cancelRealTimeBars(bars)
        ticker = feeds.get("market_data")
        if ticker is not None and "contract" in sub:
            with contextlib.suppress(Exception):
                self.ib.cancelMktData(sub["contract"])
        self._limiter.release_streaming_line(symbol)
        self._active_subscriptions.pop(symbol, None)

    async def _run_until_disconnect(self) -> None:
        """Pump events until either user signals stop or IBKR disconnects."""
        while self.ib.isConnected() and not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

    # ----- Event handlers (publish to Redis) -----------------------------

    def _make_bar_handler(self, symbol: str):
        publish = self._publish_bar
        def _handler(bars, hasNewBar) -> None:  # noqa: ANN001
            if not hasNewBar or not bars:
                return
            bar = bars[-1]
            publish(symbol, bar)
        return _handler

    def _publish_bar(self, symbol: str, bar: RealTimeBar) -> None:
        ts = bar.time
        if hasattr(ts, "timestamp"):
            ts_val = ts.timestamp()
        else:
            ts_val = float(ts)
        fields = {
            "ts": f"{ts_val:.3f}",
            "open": str(bar.open_),
            "high": str(bar.high),
            "low": str(bar.low),
            "close": str(bar.close),
            "volume": str(bar.volume),
            "wap": str(getattr(bar, "wap", "")),
            "count": str(getattr(bar, "count", "")),
        }
        key = f"ibkr:bars:{symbol}:5sec"
        try:
            self._redis.xadd(key, fields,
                             maxlen=self.config.publishing.stream_maxlen,
                             approximate=True)
            self._update_snapshot(symbol, {"last_bar_close": fields["close"],
                                            "last_bar_ts": fields["ts"]})
        except redis.exceptions.RedisError as exc:
            self._log(f"redis xadd bars/{symbol} failed: {exc}")

    def _make_tick_handler(self, symbol: str):
        publish = self._publish_tick
        def _handler(ticker) -> None:  # noqa: ANN001
            publish(symbol, ticker)
        return _handler

    def _publish_tick(self, symbol: str, ticker) -> None:  # noqa: ANN001
        # ticker.marketDataType ∈ {1=live, 2=frozen, 3=delayed, 4=delayed-frozen}
        mdt = getattr(ticker, "marketDataType", None)
        if mdt is not None:
            self._limiter.observe_market_data_type(symbol, mdt)
        bid = _safe(ticker.bid)
        ask = _safe(ticker.ask)
        last = _safe(ticker.last)
        bid_size = _safe(getattr(ticker, "bidSize", None))
        ask_size = _safe(getattr(ticker, "askSize", None))
        last_size = _safe(getattr(ticker, "lastSize", None))
        ts_val = time.time()
        fields = {
            "ts": f"{ts_val:.3f}",
            "bid": _fmt(bid),
            "ask": _fmt(ask),
            "last": _fmt(last),
            "bid_size": _fmt(bid_size),
            "ask_size": _fmt(ask_size),
            "last_size": _fmt(last_size),
            "market_data_type": str(mdt) if mdt is not None else "",
        }
        key = f"ibkr:ticks:{symbol}"
        try:
            self._redis.xadd(key, fields,
                             maxlen=self.config.publishing.stream_maxlen,
                             approximate=True)
            self._update_snapshot(symbol, fields)
        except redis.exceptions.RedisError as exc:
            self._log(f"redis xadd ticks/{symbol} failed: {exc}")

    def _update_snapshot(self, symbol: str, fields: dict[str, str]) -> None:
        key = f"ibkr:snapshot:{symbol}"
        try:
            self._redis.hset(key, mapping=fields)
            ttl = self.config.publishing.snapshot_ttl_sec
            if ttl > 0:
                self._redis.expire(key, ttl)
        except redis.exceptions.RedisError as exc:
            self._log(f"redis snapshot/{symbol} failed: {exc}")

    # ----- IBKR error / disconnect handling ------------------------------

    def _on_ib_error(self, reqId, errorCode, errorString, contract) -> None:  # noqa: ANN001
        # Non-fatal informational codes
        if errorCode in (2104, 2106, 2158, 2107, 2103):
            return
        contract_label = None
        if contract is not None and getattr(contract, "symbol", None):
            contract_label = f"{contract.symbol}/{contract.secType}"
        self._log(f"IBKR error code={errorCode} reqId={reqId} "
                  f"contract={contract_label} msg={errorString!r}")
        self._limiter.observe_error(errorCode, errorString or "", contract_label)

    def _on_disconnected(self) -> None:
        self._publish_status("disconnected")
        self._log("disconnected from IBKR")

    # ----- Misc ----------------------------------------------------------

    def _publish_status(self, state: str) -> None:
        try:
            self._redis.hset("ibkr:bridge:status", mapping={
                "state": state,
                "ts": f"{time.time():.3f}",
                "client_id": str(self.config.gateway.client_id),
                "subscriptions_active": str(len(self._active_subscriptions)),
            })
        except redis.exceptions.RedisError:
            pass

    def _log(self, msg: str) -> None:
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        print(f"[{ts}] [bridge] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Helpers


def _safe(v: Any) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _fmt(v: float | None) -> str:
    return "" if v is None else f"{v:.6f}"


# ---------------------------------------------------------------------------
# CLI entry


async def _amain(args: argparse.Namespace) -> int:
    require_ibkr_enabled()
    cfg = BridgeConfig.from_yaml(Path(args.config))
    bridge = IbkrBridge(cfg)

    loop = asyncio.get_running_loop()
    stop = asyncio.Event()

    def _signal() -> None:
        stop.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _signal)

    runner = asyncio.create_task(bridge.start())
    await stop.wait()
    await bridge.stop()
    runner.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await runner
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ibkr_bridge.bridge",
        description="IBKR live data producer publishing to Redis Streams",
    )
    p.add_argument("--config", required=True,
                    help="Path to YAML config (see example_config.yaml)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return asyncio.run(_amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
