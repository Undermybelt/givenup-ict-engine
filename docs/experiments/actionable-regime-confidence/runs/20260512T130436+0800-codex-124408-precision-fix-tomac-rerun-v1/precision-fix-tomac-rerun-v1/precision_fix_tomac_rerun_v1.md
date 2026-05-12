# 124408 Precision-Fix TOMAC Rerun v1

Generated: 2026-05-12T13:04:36+0800

Source run root: `docs/experiments/actionable-regime-confidence/runs/20260512T124408+0800-codex-123227-tomac-trade-density-iteration-v1`

Diagnostic parent: `docs/experiments/actionable-regime-confidence/runs/20260512T125232+0800-codex-124408-signal-export-diagnostic-v1`

## Scope

Run the same selected-history BTC/USD TOMAC strategy/data path after applying the diagnostic precision fix in an isolated wrapper. The wrapper changes only the synthetic market amount tick size in memory (`precision.amount=1e-8`) and leaves repo runtime code plus the original `124408` state untouched.

## Readback

- Wrapper exited `0`.
- Pair/timeframe/timerange: `BTC/USD`, `1h`, `20260401-20260512`.
- Informative timeframe: `4h`.
- Total measured trades after precision fix: `144`.
- Strategy metrics:
  - `TomacAggressiveBE`: `94` trades, total profit `2.72%`, win rate `24.4681%`, Sharpe `3.1752`, profit factor `1.4726`.
  - `TomacKillzoneBreakout`: `49` trades, total profit `-2.25%`, win rate `20.4082%`, Sharpe `-2.4522`, profit factor `0.6450`.
  - `TomacRRWinRate`: `1` trade, total profit `0.00%`, win rate `0.0000%`, Sharpe `-100.0000`, profit factor `0.0000`.
- Best measured candidate for downstream validation is `TomacAggressiveBE`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T130436+0800-codex-124408-precision-fix-tomac-rerun-v1/precision-fix-tomac-rerun-v1/precision_fix_tomac_rerun_v1.json`
- Strategy metrics CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T130436+0800-codex-124408-precision-fix-tomac-rerun-v1/precision-fix-tomac-rerun-v1/strategy_metrics_v1.csv`
- Trade exports: `docs/experiments/actionable-regime-confidence/runs/20260512T130436+0800-codex-124408-precision-fix-tomac-rerun-v1/trade-exports/`
- Wrapper: `docs/experiments/actionable-regime-confidence/runs/20260512T130436+0800-codex-124408-precision-fix-tomac-rerun-v1/scripts/precision_fix_tomac_rerun_v1.py`

## Decision

- Gate: `precision_fix_tomac_measured_candidate_downstream_required`.
- This root converts the previous zero-trade TOMAC blocker into a measured BTC-only candidate package.
- It does not satisfy Board A by itself: no cross-instrument validation, no non-1h acceptance, no calibrated `>=95%` regime posterior, no Pre-Bayes/BBN lift, no CatBoost/path-ranker mature-row promotion, and no execution-tree readiness.
- `production_likelihood_mutation=false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Use the `TomacAggressiveBE` trade CSV as the candidate package for the ordered downstream chain: Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree. Keep the decision fail-closed until that chain produces calibrated per-regime confidence and cross-context validation.

