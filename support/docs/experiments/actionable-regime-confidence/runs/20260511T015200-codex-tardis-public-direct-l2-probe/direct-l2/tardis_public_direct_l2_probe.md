# Tardis Public Direct L2 Probe

Run id: `20260511T015200+0800-codex-tardis-public-direct-l2-probe`

Tardis documentation says first-day-of-month historical CSV datasets can be downloaded without an API key. This probe sampled public direct order-book URLs without saving full raw datasets into the repo.

Accessible direct sources: bitmex_xbtusd_book_snapshot_5_2020_09_01, binance_futures_btcusdt_book_snapshot_5_2020_09_01, deribit_btc_perpetual_incremental_book_l2_2020_04_01.

Decision: `blocked_direct_l2_probe_only`. Manipulation input state: `direct_l2_accessible_but_unlabeled_not_calibration_grade`. Blocker: Public Tardis first-day data provides direct L2/order-book inputs, but this probe is unlabeled, partial, and not yet a multi-period manipulation calibration set.
