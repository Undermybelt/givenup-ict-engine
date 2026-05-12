"""Diagnostic synthetic-market shim for an offline Auto-Quant probe.

This is intentionally non-promoting. It does not edit Auto-Quant run.py or
config.json. It only supplies Freqtrade with minimal spot market metadata for
the five configured crypto pairs so local OHLCV/strategy execution can be
tested when the sandbox cannot resolve Binance market metadata.
"""

from freqtrade.resolvers.exchange_resolver import ExchangeResolver

_original_load_exchange = ExchangeResolver.load_exchange

_PAIRS = ("BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "AVAX/USDT")


def _market(pair: str) -> dict:
    base, quote = pair.split("/")
    return {
        "id": f"{base}{quote}",
        "symbol": pair,
        "base": base,
        "quote": quote,
        "baseId": base,
        "quoteId": quote,
        "type": "spot",
        "spot": True,
        "margin": False,
        "swap": False,
        "future": False,
        "option": False,
        "active": True,
        "contract": False,
        "linear": None,
        "inverse": None,
        "precision": {"amount": 8, "price": 8, "cost": 8},
        "limits": {
            "amount": {"min": 0.0, "max": None},
            "price": {"min": 0.0, "max": None},
            "cost": {"min": 0.0, "max": None},
        },
        "info": {},
    }


_MARKETS = {pair: _market(pair) for pair in _PAIRS}


def _load_exchange_with_synthetic_markets(
    config,
    *,
    exchange_config=None,
    validate=True,
    load_leverage_tiers=False,
):
    exchange = _original_load_exchange(
        config,
        exchange_config=exchange_config,
        validate=False,
        load_leverage_tiers=False,
    )
    exchange._markets = dict(_MARKETS)
    exchange._api.markets = dict(_MARKETS)
    exchange._api_async.markets = dict(_MARKETS)
    exchange._api.markets_by_id = {m["id"]: [m] for m in _MARKETS.values()}
    exchange._api_async.markets_by_id = {m["id"]: [m] for m in _MARKETS.values()}
    return exchange


ExchangeResolver.load_exchange = staticmethod(_load_exchange_with_synthetic_markets)
