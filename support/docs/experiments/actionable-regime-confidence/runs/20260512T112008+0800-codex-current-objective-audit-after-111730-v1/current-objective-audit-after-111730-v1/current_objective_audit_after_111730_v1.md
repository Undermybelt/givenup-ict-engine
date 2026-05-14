# Current Objective Audit After 111730 v1

## Objective

Train profitability factors from regime-rooted branches, preserve `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`, and carry real evidence through Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution tree with provider authority across IBKR, TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, and Bybit.

## Decision

The objective is not achieved. Do not call `update_goal`.

Current state remains `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.

## What Improved

- `111403` repaired the ingest/state-dir bridge for the `105014` BTC pullback replay.
- `111403` now preserves `Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1` into structural target columns and selects the exact branch in structural bundle / execution candidate.
- `111403` reached observation validation `146/30`.
- `111602` made the old TVR `429` blocker stale for provider-layer reachability: TVR status ready and QQQ `1d` rows present.
- `111538` narrowed IBKR from inactive-farm confusion to provider-health-only SPY evidence with `2` rows returned.

## Remaining Blockers

- No same-root six-provider AQ packet exists.
- No cross-provider positive branch survived.
- `111403` still has Pre-Bayes policy absent.
- `111403` still has CatBoost/path-ranker `raw_scored_mature=0/30`, `production_validation=0/30`, trainer artifact missing, and runtime selection disabled.
- Execution tree still returns `ready=false`, `actionable=false`, and `fail_closed`.
- Selected-history and source/control gates remain closed.

## Next

Do not repeat `111403`, `111538`, or `111602`. Continue only from:

- a fresh provider-matrix AQ packet using current TVR reachability and exact IBKR contract rows in the same workflow, or
- a branch-preserved `111403` continuation that trains/registers a path-ranker/CatBoost artifact, produces production validation, and reruns the ordered workflow through execution-tree release.
