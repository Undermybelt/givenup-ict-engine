# IBKR 3M timeframe ladder blocker + cache replay

Session lesson from an options/profit-factor ladder run where the user asked to pull a three-month window and run 1m upward through Auto-Quant and tree handoff.

## Observed pattern

- `provider-status --provider ibkr --agent` can report ready while direct historical fetches return empty/timeouts.
- In this session, fresh `QQQ` `3 M` fetches for `1 min`, `5 mins`, `15 mins`, `30 mins`, and `1 hour` returned no usable rows (`exit=3` or fetch failure).
- A feasible-window retry also returned no usable fresh rows for the tested QQQ lanes.
- The only retained real IBKR cache available from prior artifacts was `5m` and `30m` across `SPY`, `QQQ`, `IWM`, `XLK`, `SMH`, `NVDA`.

## Correct handling

1. Classify fresh all-lane failure as `provider-window blocker`, not factor failure.
2. Enumerate requested vs retained frames:
   - requested: `1m`, `5m`, `15m`, `30m`, `1h`
   - retained: only frames actually present on disk
   - missing: every requested frame absent from retained cache
3. If using retained cache, mark every artifact clearly:
   - `local_cache_replay=true`
   - `provider=IBKR_CACHE_REPLAY` or equivalent
   - `fresh_ibkr_status=blocked_empty_timeout...`
4. Do not upsample/downsample retained frames to pretend missing `1m`/`15m`/`1h` existed.
5. Run only real retained frames through Auto-Quant/real-trade/BBN/CatBoost/tree mechanics.
6. Gate language:
   - `tree handoff visible` or `candidate-only` if CatBoost/runtime is enabled but validation rows are short.
   - not `live-ready` until `raw_scored_mature`, `production_validation`, and `observation_validation` meet threshold.

## Schema pitfall

`auto-quant-results-import` rejects free-form string entries in strategy-library `validation_errors`:

```text
invalid type: string ..., expected struct StrategyLibraryValidationError
```

Put provider-window notes in run summaries or strategy metadata, or emit proper structured validation error objects if the schema is known.

## Example outcome shape

- Fresh IBKR 3M ladder: blocked all lanes.
- Cache replay retained frames: `5m`, `30m` only.
- Best cache lane: `5m` with positive PF but fewer than 30 mature validation rows.
- Tree handoff: CatBoost runtime can be enabled, but result remains `candidate-only` when maturity rows are short.
