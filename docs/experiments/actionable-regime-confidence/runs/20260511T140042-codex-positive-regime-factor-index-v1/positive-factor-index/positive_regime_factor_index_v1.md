# Positive Regime Factor Index v1

Run ID: `20260511T140042+0800-codex-positive-regime-factor-index-v1`

This artifact is a positive supply index, not another negative source scan. It says which MainRegimeV2 factors are already accepted at 95, and which doomed lanes should not be repeated.

## Accepted Supply

- Price roots with accepted daily parent-root factors: `Bear, Bull, Crisis, Sideways` (`4/4`).
- Same-source weekly/monthly source-consensus cells accepted: `8/8`.
- Exact intraday parent-day context rows accepted: `36/48`.
- Direct `Manipulation` scoped varieties accepted: `5` (`pump_dump_telegram_event, dex_self_trade_order_lifecycle, dex_consecutive_self_trade_order_lifecycle, midsummer_bsc_wash_maker, midsummer_multichain_wash_maker`).

## Support Algebra

- Wilson95 lower bound `>= 0.95` needs at least `73` all-correct observations in a split.
- Exact `^GSPC/^DJI` intraday `Crisis` has only `28` calibration source-days and `2` heldout-time source-days, so more tuning in that lane cannot pass.
- ES/NQ crosswalk already proved the support/policy bottleneck: accepted only scoped ES Bull rows; NQ needs a Nasdaq-100-grade source relation before promotion.

## Do Not Repeat

- Do not run more OHLCV/HMM/generated-label searches for direct `Manipulation`.
- Do not rerun local filename searches for FINRA/native labels without a new row-export location.
- Do not treat provider bars as labels; use them only for session/date overlap after source labels exist.

## Decision

- Per price-root factor supply is present for `Bull`, `Bear`, `Sideways`, and `Crisis` in the scoped daily source panel.
- `Manipulation` has scoped direct-event/order-lifecycle/on-chain accepted supply, but full variety coverage is still incomplete.
- Full objective achieved: `false`.
- Gate result: `positive_regime_factor_index_v1_per_root_supply_present_full_goal_still_blocked`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Next

Use this index as the Board A factor-supply map. Further Board A completion requires new independent source-label panels or direct positive/negative manipulation rows, not more provider-bar proxy scans.
