# IBKR high-window reclaim 1m MTF Gate pattern

Use when continuing a 30m high-window / quarter-high reclaim branch into the user's preferred low-timeframe ladder.

## Durable lesson

A 30m cross-symbol high-window reclaim Gate 1 pass is not enough to promote. The next concrete step is a rooted 1m-origin MTF lane that keeps the same regime branch and explicitly requests/fetches the user's preferred ladder:

- `1m`: IBKR `7 D` first when `1 M` is likely to timeout
- `5m`: IBKR `1 M`
- `15m`: IBKR `3 M` when feasible, downgrade to `1 M` if blocked
- `30m`: IBKR `3 M`
- `1h`: IBKR `3 M`

The branch path should remain rooted, e.g.:

`TrendExpansion -> BreakoutPersistence -> high_window_reclaim_1m_mtf -> ibkr_qqq_high_window_reclaim_1m_mtf_v1`

## Procedure

1. Start from provider-status but do not treat readiness as fetch proof.
2. Fetch fresh IBKR per timeframe where feasible.
3. If a lane times out, downgrade that lane only; preserve successful real lanes.
4. Build an Auto-Quant agent-material package with:
   - `base_timeframe=1m`
   - `context_timeframes=[5m,15m,30m,1h]`
   - `training_timeframe=1m`
   - `neutralization_timeframe=30m`
   - `confirmation_timeframe=1h`
   - full `main_regime/sub_regime/sub_sub_regime_or_profit_factor/profit_factor` fields.
5. Run `auto-quant-agent-material-batch`, `dispatch`, then `rank`.
6. Permit Pre-Bayes/BBN only if AQ has nonzero profitable density and enough trades for the row to be meaningful.
7. Keep `catboost_allowed=false`, `execution_tree_allowed=false`, `promotion_allowed=false`, and `trade_usable=false` until the downstream gates actually run and pass.

## Pitfalls

- Do not flatten the branch to `high_window_reclaim`; preserve the regime-rooted path through every material and rank artifact.
- Do not let a 30m positive run skip the 1m-origin ladder.
- Do not call an IBKR-ready status a live-ready factor; the per-timeframe fetch rows are the evidence.
- Do not fabricate missing MTF frames from one dataframe unless the script labels that as derived context only; fetched provider rows and derived/resampled context are different evidence classes.
- If Auto-Quant rank is still running, report the process/session id and stop rather than claiming a verdict.
