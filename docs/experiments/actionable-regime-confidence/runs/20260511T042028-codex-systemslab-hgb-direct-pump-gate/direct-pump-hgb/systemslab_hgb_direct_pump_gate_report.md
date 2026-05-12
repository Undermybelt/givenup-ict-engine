# SystemsLab HGB Direct Pump/Dump Gate

Run ID: `20260511T042028+0800-codex-systemslab-hgb-direct-pump-gate`.

This is a direct-input `Manipulation` probe using labeled pump/dump exchange-transaction features.
It is not an OHLCV/session/liquidity proxy acceptance path.

## Decision

- Gate: `blocked_systemslab_hgb_direct_pump_below_95`
- Accepted 95: `false`
- Best model: `25S` / `hgb_sampled`
- Calibration Wilson95 / precision / support / coverage: `0.863904` / `0.943662` / `71` / `0.000736`
- Test Wilson95 / precision / support / coverage: `0.832241` / `0.923077` / `65` / `0.000674`
- Blocker: held-out Wilson95 and coverage remain below Board A acceptance thresholds.

## Policy

- Features used: `std_rush_order, avg_rush_order, std_trades, std_volume, avg_volume, std_price, avg_price, avg_price_max`
- Blocked predictors: `date, pump_index, symbol, gt, hour_sin, hour_cos, minute_sin, minute_cos`
- Runtime code changed: false
- Thresholds relaxed: false
- Raw data committed to repo: false
