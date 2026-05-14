# SystemsLab Event-Rank Manipulation Gate

Run id: `20260511T043321+0800-codex-systemslab-event-rank-manipulation-gate`.

## Decision

- Gate result: `blocked_systemslab_event_rank_below_95`
- Accepted 95 Manipulation: `false`
- Runtime code changed: `false`
- Thresholds relaxed: `false`
- Trade usable: `false`

## Best Held-Out Result

- Timeframe: `15S`
- Selected rank features: `std_rush_order, avg_rush_order, avg_price_max`
- Calibration support/successes/Wilson95: `63` / `58` / `0.827297`
- Test support/successes/Wilson95: `64` / `61` / `0.871003`

## Interpretation

This is direct event/social manipulation evidence with explicit positive pump rows and same-event negative controls. It still fails the unchanged 95% gate on held-out event ranking, so it is negative evidence only.
