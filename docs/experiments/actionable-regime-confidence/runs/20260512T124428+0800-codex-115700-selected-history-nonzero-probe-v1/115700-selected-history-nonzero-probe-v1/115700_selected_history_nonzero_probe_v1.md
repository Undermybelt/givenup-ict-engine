# 115700 Selected-History Nonzero Probe v1

Run id: `20260512T124428+0800-codex-115700-selected-history-nonzero-probe-v1`

## Scope

Diagnostic selected-history Auto-Quant strategy probe over the already-counted `115700 -> 121347` BTC line. The probe used the repaired selected-window pair config from `122600` and a run-local strategy file:

`strategies_external/B2R115700SelectedHistoryMomentumProbeV1.py`

This is not runtime code, not an accepted strategy, and not a production BBN/CatBoost/execution-tree update.

## Command Evidence

- Command: `command-output/run_nonzero_probe.cmd`
- stdout: `command-output/run_nonzero_probe.out`
- stderr: `command-output/run_nonzero_probe.err`
- exit: `command-output/run_nonzero_probe.exit`

## Readback

- Exit code: `0`.
- Strategy: `B2R115700SelectedHistoryMomentumProbeV1`.
- Pair: `B2RSAMEROOTSIXPROVIDER1HAQ115700/USD`.
- Backtest window: `2026-04-02 06:00:00 -> 2026-05-11 23:00:00`.
- Trades: `0`.
- Total profit percent: `0.0000`.
- Win rate percent: `0.0000`.
- Profit factor: `0.0000`.

## Decision

- Gate: `selected_history_nonzero_probe_zero_trades_no_promotion`.
- The relaxed diagnostic recipe did not create nonzero selected-history observations.
- No RC-SPA surface, branch-conditioned win-rate packet, Pre-Bayes/BBN lift, CatBoost/path-ranker mature rows, or execution-tree promotion can be derived from this probe.
- `production_likelihood_mutation=false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Do not repeat this selected-history BTC nonzero-probe shape as a promotion candidate. The next useful work must change one of the remaining gaps: provider-provenanced non-BTC data beyond local cache, nonzero trade-dense Auto-Quant candidates, calibrated Pre-Bayes/BBN evidence toward `>=95%`, CatBoost/path-ranker mature rows, or non-observe execution readiness.
