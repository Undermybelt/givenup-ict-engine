# Crypto Label Source Preflight

Run id: `20260511T081101+0800-codex-crypto-label-source-preflight`

## Source

Kaggle: `adamcimbora/crypto-multi-exchange-ohlcv-indicators-labels`

Raw zip stayed under `/private/tmp/ict-regime-crypto-multiexchange-label-preflight/` and was not committed.

## What It Covers

- Exchanges in metadata: `binance`, `okx`, `kraken`
- Bases in metadata: `BTC`, `ETH`, `SOL`
- Timeframes in metadata: `15m`, `1h`, `1d`
- Rows in metadata: `32635`
- Date span in metadata: `2025-07-10` to `2025-10-08`

## Why It Does Not Close Board A

The source is useful as crypto/provider coverage evidence, but it is not an independent MainRegimeV2 regime-label panel.

The README defines labels as:

- `+1`: future price increase greater than `+1%`
- `0`: neutral move within `+/-1%`
- `-1`: future price decrease less than `-1%`

Columns visible from the embedded parquet schema include `y_cls_1h`, `y_cls_4h`, `y_cls_24h`, and `Signal`.

Mapping those labels into `Bull`, `Bear`, or `Sideways` would be a future-return/OHLCV proxy, not an independent regime label. `Crisis` is absent. `Manipulation` direct-event/order-flow/order-lifecycle evidence is absent.

Gate result: `blocked_crypto_multiexchange_labels_are_future_return_proxy_not_mainregimev2_source_labels`.

Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

