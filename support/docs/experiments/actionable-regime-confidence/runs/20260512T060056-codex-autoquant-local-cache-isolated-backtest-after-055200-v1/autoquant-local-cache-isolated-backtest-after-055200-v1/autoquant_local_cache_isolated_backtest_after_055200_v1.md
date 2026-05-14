# AutoQuant Local Cache Isolated Backtest After 055200 v1

Run id: `20260512T060056-codex-autoquant-local-cache-isolated-backtest-after-055200-v1`

Gate result: `autoquant_local_cache_isolated_backtest_after_055200_v1=isolated_local_cache_backtest_succeeded_status_data_missing_no_promotion`

## Scope

Non-promoting readback after the 055200 Auto-Quant local-reuse probe ended at Binance DNS/data-missing. This run clones local Auto-Quant into `/tmp`, overlays only selected repo-side external runner/strategy sources and cached `NQ_USD` feathers, and runs FreqTrade backtests without preparing/downloading new network data.

## Inputs

- Isolated clone: `/tmp/ict-engine-board-a-autoquant-local-cache-20260512T060056/auto-quant`
- Runner/config overlay: `scripts/auto_quant_external/run_tomac.py`, `scripts/auto_quant_external/config.tomac.json`
- Strategies copied:
  - `TomacNQ_KillzoneBreakout.py`
  - `TomacNQ_RegimePersistenceCluster.py`
  - `TomacNQ_RegimeTransitionHazard.py`
- Cached data copied:
  - `NQ_USD-1h.feather` rows `89250` range `2011-01-02T23:00:00+00:00` to `2025-12-31T21:00:00+00:00` (`epoch_ms`)
  - `NQ_USD-4h.feather` rows `23879` range `2011-01-02T20:00:00+00:00` to `2025-12-31T20:00:00+00:00` (`epoch_ms`)

## Backtest Result

- Strategies succeeded: `3`; failed: `0`; total trades: `26`.
- Best bounded Sharpe in this slice: `TomacNQ_RegimeTransitionHazard` Sharpe `0.1722`, trades `2`, win rate `100.0`.

| Strategy | Sharpe | Trades | Win % | Profit % | Max DD % | Profit factor |
|---|---:|---:|---:|---:|---:|---:|
| TomacNQ_KillzoneBreakout | -0.0192 | 5 | 60.0 | -1.31 | -2.7549 | 0.6185 |
| TomacNQ_RegimePersistenceCluster | 0.0954 | 19 | 57.8947 | 4.26 | -1.7998 | 1.9146 |
| TomacNQ_RegimeTransitionHazard | 0.1722 | 2 | 100.0 | 2.52 | -0.0 | 0.0 |

## Decision

- Local cache reuse is operational for a bounded sidecar Auto-Quant/FreqTrade readback; the `055200` blocker is narrowed from generic dependency/data failure to canonical-prepare/readiness mismatch plus source/control absence.
- ict-engine `auto-quant-status` over the isolated clone reports dependency healthy `True` but status `dependency_ready_data_missing` and data_ready `False`.
- This does not unlock Board A promotion: no source/control evidence was acquired, target roots remain absent, canonical merge is not allowed, and downstream rerun remains blocked.

## Next

Preserve the Current Cursor next action. Continue only after explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows, or source-owned R3 native sub-hour labels unlock a required target root; then rerun direct verifier, split calibration, canonical merge, providers, Auto-Quant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.
