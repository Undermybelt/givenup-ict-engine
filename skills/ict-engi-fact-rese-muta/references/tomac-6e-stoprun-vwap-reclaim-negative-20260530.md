# TOMAC 6E Stop-Run VWAP Reclaim Negative, 2026-05-30

## Scope

- Repo packet: `support/docs/experiments/actionable-regime-confidence/20260530T022419+0800-codex-6e-eth-stoprun-vwap-reclaim-mtf-screen.md`
- Run root: `/tmp/ict-engine-6e-eth-stoprun-vwap-reclaim-mtf-screen-20260530T022419+0800`
- Repo reference root: `support/docs/experiments/actionable-regime-confidence/runs/20260530T022419+0800-codex-6e-eth-stoprun-vwap-reclaim-mtf-screen-v1`
- Branch: `Transition -> LiquiditySweep -> StopRunVwapReclaim -> local_6e_csv_transition_stoprun_vwap_reclaim_v1`
- Session target: `ETH/full_retained_session`, `rth_filter_applied=false`
- Runtime: local CSV screen only, `--skip-aq`; no Auto-Quant, provider, IBKR, paper, or lifecycle launch.

## Evidence

The local GLBX 6E/EUR `1m` screen retained `1,746,944` outright positive-price
rows from `2021-01-03T23:00:00Z` to `2025-12-31T21:59:00Z` and filtered
`285,238` spread rows. The synthesized ladder contained:

- `1m=1746944`
- `5m=356987`
- `15m=119868`
- `30m=60585`
- `1h=30941`
- `4h=8002`
- `1d=1556`

The filtered family set was only `transition_stoprun_vwap_reclaim`. The screen
produced `21` rows, `0` 2bps survivors, and `0` 5bps survivors. No AQ materials
were selected and no AQ rank rows were generated.

The best stress-positive row was a sparse higher-timeframe artifact:

`local-6e-csv-transition_stoprun_vwap_reclaim-dense-1d-v1`: `5` trades,
`0.003213` trades/day, raw `+1.951282%`, `2bps=+1.751282%`,
`5bps=+1.451282%`.

All `1m` variants had `0` trades.

## Decision

Decision: `drop_gate1_no_cost_density`.

This exact 6E/EUR ETH/full-session stop-run VWAP reclaim branch is a negative
local screen. Do not launch AQ/provider/downstream unchanged. Future 6E work
must use a materially different root or first verify exact IBKR 6E contract
economics and produce non-sparse origin evidence.

## Cost Note

The same-turn cost source check saw IBKR CME FX futures exchange fee recovery
for Forex Futures, including `EUR`, at `USD 1.60/side`, plus the all-products
regulatory row at `USD 0.02/side`. IBKR secdef search for root `6E` returned
`No symbol found` from this host context, so exact multiplier/tick and broker
contract mapping were not verified. Keep `cost_model_status=cost_model_unverified`.

Any `5bps/side` output here is stress-only and cannot prove futures commission
survival, promotion, paper readiness, trade usability, or goal completion.
