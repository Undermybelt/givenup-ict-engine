# 123227 TOMAC Trade-Density Iteration v1

Run id: `20260512T124408+0800-codex-123227-tomac-trade-density-iteration-v1`

## Scope

Readback over the settled `123227` local Auto-Quant BTC alias workspace after
the data-ready blocker was resolved. This run tests whether the seeded TOMAC
strategies produce nonzero trade density on the selected BTC/USD window.

This does not mutate ict-engine runtime code, BBN CPDs, CatBoost models, or
execution-tree gates.

## Evidence

- Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T123227+0800-codex-115700-selected-history-btc-alias-aq-v1`
- Command stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T124408+0800-codex-123227-tomac-trade-density-iteration-v1/command-output/01_run_tomac_trade_density.out`
- Command stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T124408+0800-codex-123227-tomac-trade-density-iteration-v1/command-output/01_run_tomac_trade_density.err`
- Command exit: `docs/experiments/actionable-regime-confidence/runs/20260512T124408+0800-codex-123227-tomac-trade-density-iteration-v1/command-output/01_run_tomac_trade_density.exit`
- Strategy file list: `docs/experiments/actionable-regime-confidence/runs/20260512T124408+0800-codex-123227-tomac-trade-density-iteration-v1/original_strategy_files.txt`

## Readback

- `01_run_tomac_trade_density` exited `0`.
- `TomacAggressiveBE`, `TomacKillzoneBreakout`, and `TomacRRWinRate` all ran.
- Result: `3` succeeded, `0` failed.
- All three strategies produced `0` trades.
- Total profit, win rate, and profit factor all stayed `0.0`.

## Gate

- `fail_closed:tomac_trade_density_iteration_zero_trades`.
- `production_likelihood_mutation=false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Do not repeat the same BTC/USD TOMAC trade-density iteration as a promotion
candidate. The next useful Auto-Quant slice needs a materially different data
window or strategy family that produces nonzero mature rooted observations
before Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree can
be rerun for acceptance.
