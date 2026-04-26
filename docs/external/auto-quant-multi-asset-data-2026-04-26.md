# 2026-04-26 auto-quant multi-asset data adapter

## Goal

Let Auto-Quant (FreqTrade-based) backtest non-crypto OHLCV data — stocks, ETFs,
futures, FX/CFDs — and ingest NSE option-chain snapshots, **without modifying
any FreqTrade source file**. Source-of-truth for the tooling lives here in
`ict-engine`; the Auto-Quant checkout is treated as a deploy target.

## Source-of-truth layout in this repo

```
scripts/auto_quant_external/
├── fetch_external.py          multi-source fetcher (yahoo / nse-options / polygon)
├── prepare_external.py        5-pass cleaner + CSV→feather adapter
├── run_tomac.py               runner with synthetic-market injection bypass
├── config.tomac.json          separate FreqTrade config (binance kept as ccxt placeholder)
└── strategies/
    └── TomacNQ_KillzoneBreakout.py    NQ futures example IStrategy
```

These files are intentionally **not** vendored under `src/` — they are operator
tooling, not part of the Rust binary surface. Treat them as a small companion
toolkit for whoever runs Auto-Quant locally.

## Deploy positions in an Auto-Quant checkout

Given an Auto-Quant checkout at `$AQ` (e.g. `~/Auto-Quant`):

```
$AQ/fetch_external.py                                ← scripts/auto_quant_external/fetch_external.py
$AQ/prepare_external.py                              ← scripts/auto_quant_external/prepare_external.py
$AQ/run_tomac.py                                     ← scripts/auto_quant_external/run_tomac.py
$AQ/config.tomac.json                                ← scripts/auto_quant_external/config.tomac.json
$AQ/user_data/strategies_external/                   ← scripts/auto_quant_external/strategies/
```

`strategies_external/` is intentionally a separate directory so that
`run_tomac.py` (which loads from it) never collides with Auto-Quant's master
`run.py` (which loads from `user_data/strategies/`). Both coexist with zero
edits to `run.py`, `prepare.py`, `config.json`, or any FreqTrade file.

A one-shot deploy is simply `cp -r` of the listed files; no symlinks required.

## End-to-end pipeline

1. **Fetch** raw OHLCV via `fetch_external.py yahoo --tickers ... --start ... --end ...`.
   Sub-commands: `yahoo`, `nse-options`, `polygon`. Yahoo path includes retry
   with exponential backoff and User-Agent rotation for 429/5xx mitigation.
2. **Clean + adapt** with `prepare_external.py --csv ... --pair NQ/USD --timeframes 1h,4h,1d`.
   The 5-pass cleaner handles: OHLC consistency, non-positive prices, negative
   volume, ghost bars, and configurable jump outliers. OTC instruments
   (forex/CFD where Yahoo reports volume=0 across the whole series) are
   detected by `median(volume) == 0` and the ghost-bar pass is skipped with a
   provenance note `ghost_bar_skipped: volume_series_all_zero_otc_instrument`.
   Output is FreqTrade feather under `user_data/data/{PAIR}-{TF}.feather`.
3. **Backtest** with `run_tomac.py`. The runner:
   - Loads `config.tomac.json` (whitelist contains pseudo-pairs like `NQ/USD`,
     exchange name kept as `binance` purely so CCXT validation passes).
   - Constructs the FreqTrade `Exchange` object **and then injects synthetic
     market entries** into `exchange._markets` matching the whitelist. This
     makes `IPairList._whitelist_for_active_markets` pass without contacting
     any real exchange and without touching FreqTrade source.
   - Hands the patched exchange to `Backtesting`, which accepts a
     pre-constructed exchange object (verified upstream behavior).

## Asset-class coverage (verified 2026-04-26 via Yahoo Finance free chart API)

| Class      | Symbol      | 1d bars | Range                       | Notes                      |
| ---------- | ----------- | ------- | --------------------------- | -------------------------- |
| stock      | `AAPL`      | 751     | 2023-01-03 .. 2025-12-30    |                            |
| etf        | `SPY`       | 751     | 2023-01-03 .. 2025-12-30    |                            |
| futures    | `ES=F`      | 754     | 2023-01-03 .. 2025-12-30    | continuous front-month     |
| cfd / fx   | `EURUSD=X`  | 779     | 2023-01-02 .. 2025-12-31    | OTC, volume=0 honored      |
| crypto     | `BTC-USD`   | 1096    | 2023-01-01 .. 2025-12-31    | full daily span            |

End-to-end backtest proof (previous session, databento NQ 1h+4h+1d feathers):
3 trades, win-rate 66.7%, sharpe 0.005, max-drawdown -1.10%, **0 FreqTrade
source modifications**.

## Option-chain coverage (NSE)

`fetch_external.py nse-options` implements the distilled NSE flow:

1. `GET /option-chain` warmup → cookies.
2. `GET /api/underlying-information` → list of indices + stocks.
3. `GET /api/option-chain-v3?type=...&expiry=...` → per-symbol chain.

Output is flattened to a wide CSV with columns:

```
snapshot_utc, expiry, strike,
call_oi, call_chng_oi, call_iv, call_ltp, call_volume,
put_oi,  put_chng_oi,  put_iv,  put_ltp,  put_volume
```

**Network constraint**: NSE's edge (Akamai) geofences non-Indian IPs and
returns 403/blocked HTML before reaching the API. Fetcher works as designed
when called from an Indian IP; from CN/elsewhere it requires VPN.

**Backtest constraint**: FreqTrade's `IStrategy` interface is single-instrument
OHLCV — it has no native dimension for strike, expiry, or Greeks. Option-chain
snapshots are therefore ingested as **context artifacts** (e.g. as features
for an underlying-asset strategy), not as a backtestable instrument. A
direct option-chain backtester would require a separate engine; this is out
of scope for the Auto-Quant integration.

## Why this lives in `ict-engine`, not in Auto-Quant

`docs/auto-quant-ictengine-integration-guide.md` mandates: ict-engine is the
canonical decision-maker, Auto-Quant is an external workspace whose source
must not be polluted with ict-engine's experimental tooling. Storing this
toolkit under `scripts/auto_quant_external/` keeps the source-of-truth
versioned in our repo while the Auto-Quant checkout stays a clean upstream
mirror that anyone can reset to HEAD.
