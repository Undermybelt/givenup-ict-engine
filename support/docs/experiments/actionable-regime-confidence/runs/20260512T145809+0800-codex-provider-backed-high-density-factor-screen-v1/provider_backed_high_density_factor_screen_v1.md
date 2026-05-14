# Provider-Backed High-Density Factor Screen v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T145809+0800-codex-provider-backed-high-density-factor-screen-v1/`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T143900+0800-codex-provider-backed-regime-validation-smoke-v1/`

## Purpose

Screen an unowned, provider-backed profitability-factor surface with materially higher trade density than the current TOMAC support samples, while preserving the Board B branch shape:

`main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`

This is a screening artifact only. It is not an Auto-Quant backtest, not a Pre-Bayes/BBN/CatBoost/execution-tree admission, not live-trade evidence, and not a promotion packet.

## Inputs

- Binance `BTCUSDT` 1h normalized provider data: `76429` rows, `2017-08-17 04:00:00+00:00` to `2026-05-12 00:00:00+00:00`.
- IBKR `SPY` 1h normalized provider data: `20034` rows, `2021-05-13T08:00:00+00:00` to `2026-05-11T23:00:00+00:00`.
- Yahoo `ES` 1h normalized provider data: `11383` rows, `2024-05-13 00:00:00+00:00` to `2026-05-11 23:00:00+00:00`.

## Artifacts

- Manifest: `summaries/provider_backed_high_density_factor_manifest.json`
- Summary: `summaries/provider_backed_high_density_factor_summary.csv`
- Trade rows: `summaries/provider_backed_high_density_factor_trades.csv`
- Assertions: `checks/provider_backed_high_density_factor_screen_v1_assertions.out`

## Readback

- The screen emitted `9388` provider-backed simulated factor observations across three portable rule families: `trend_pullback_resume_v1`, `volatility_breakout_follow_v1`, and `range_z_reversion_v1`.
- Every emitted observation carries branch fields: `main_regime`, `sub_regime`, `sub_sub_regime_or_profit_factor`, `profit_factor`, and `branch_path`.
- The strongest branch-level candidates were:
  - `trend_expansion -> normal_volatility -> down_or_flat_momentum -> trend_pullback_resume`: `384` trades, `60.4%` win rate, PF `1.356`, average return `0.00151`.
  - `trend_expansion -> high_volatility -> up_momentum -> volatility_breakout_follow`: `348` trades, `52.3%` win rate, PF `1.327`, average return `0.00245`.
  - `range_z_reversion_v1` on Yahoo `ES`: `557` trades, `53.0%` win rate, PF `1.197`, average return `0.00047`.
- Aggregate screens remain mixed or weak. This supports candidate selection for the next loop, not factor promotion.

## Gate

- `support_once:145809_provider_backed_high_density_factor_screen_v1`.
- `evidence_class:provider_backed_high_density_factor_screen_not_promotion`.
- `pass:provider_backed_rows_107846_total`.
- `pass:screen_trade_rows_9388`.
- `pass:branch_path_fields_present`.
- `pass:three_portable_factor_families_screened`.
- `partial:trend_pullback_branch_pf_1_356_trades_384`.
- `partial:volatility_breakout_branch_pf_1_327_trades_348`.
- `partial:yahoo_es_range_reversion_pf_1_197_trades_557`.
- `fail_closed:not_auto_quant_backtest`.
- `fail_closed:not_all_required_providers_used_in_factor_screen`.
- `fail_closed:tradingviewremix_and_kraken_not_in_screen_inputs`.
- `fail_closed:no_cost_slippage_walk_forward_or_chronological_survival`.
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_admission`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Convert the best branch-level candidate into an Auto-Quant or hot-pluggable consumer strategy surface, then rerun with chronological/walk-forward splits and provider coverage before any ordered Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree admission attempt.
