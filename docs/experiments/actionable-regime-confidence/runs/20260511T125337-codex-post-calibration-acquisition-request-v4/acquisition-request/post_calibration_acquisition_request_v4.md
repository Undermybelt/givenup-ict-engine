# Post-Calibration Acquisition Request v4

Run ID: `20260511T125337+0800-codex-post-calibration-acquisition-request-v4`

This request follows the `124107` targeted source-window calibration result: accepted crosswalk slots added `0`.

## Why This Exists

The current bottleneck is no longer taxonomy or source-window bookkeeping. The blocker is evidence with enough support to survive held-out calibration:

- `Bull/Bear/Crisis` source-window projections did not pass calibration.
- Intraday source-window slots do not have enough historical overlap in the current local cache.
- `Sideways` is accepted only in the scoped Yahoo `1d`/`1w` lane.
- `Manipulation` direct evidence remains variety-limited.

## Requests

1. Exact `MainRegimeV2` label panel for `Bull/Bear/Sideways/Crisis` by provider, instrument, timeframe, and root.
2. Historical bar overlap for approved S&P 500 source-window labels if that route remains active.
3. Expanded dated `Sideways` windows or an explicit adjudication protocol beyond the current Yahoo `1d`/`1w` scope.
4. Direct `Manipulation` rows across more varieties: spoofing, layering, quote stuffing, order lifecycle, wash/self-trade, with matched negatives.

## Gate

This is an acquisition request, not a confidence pass.

Next loop should acquire or attach one of these inputs, then run chronological calibration/test. If support or labels are still missing, the correct result is an explicit abstain cell, not another projection.

Safety:
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.
- Goal complete: false.
