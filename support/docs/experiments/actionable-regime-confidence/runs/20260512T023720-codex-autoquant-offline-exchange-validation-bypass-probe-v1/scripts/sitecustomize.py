"""Diagnostic offline shim for Auto-Quant backtest probes.

This leaves Auto-Quant's run.py and config.json untouched, but forces
Freqtrade's exchange resolver to skip startup market validation. The probe is
non-promoting: it only tests whether local data and strategies can execute when
network-only exchange metadata lookup is removed from the path.
"""

from freqtrade.resolvers.exchange_resolver import ExchangeResolver

_original_load_exchange = ExchangeResolver.load_exchange


def _load_exchange_without_startup_validation(
    config,
    *,
    exchange_config=None,
    validate=True,
    load_leverage_tiers=False,
):
    return _original_load_exchange(
        config,
        exchange_config=exchange_config,
        validate=False,
        load_leverage_tiers=False,
    )


ExchangeResolver.load_exchange = staticmethod(_load_exchange_without_startup_validation)
