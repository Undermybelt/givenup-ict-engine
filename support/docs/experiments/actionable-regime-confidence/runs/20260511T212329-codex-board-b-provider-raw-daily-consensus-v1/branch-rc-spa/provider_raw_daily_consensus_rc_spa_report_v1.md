# Provider Raw Daily Consensus RC-SPA v1

Run id: `20260511T212329+0800-codex-board-b-provider-raw-daily-consensus-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `77.0395`
- Price-root paths passed: `0/4`
- Scoped Manipulation component pass consumed: `True`
- Variant rows: `843`
- Selected rows: `197`
- Selected root counts: `{'Bull': 22, 'Bear': 20, 'Sideways': 154, 'Crisis': 1, 'Manipulation(scoped)': 13535}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk; Bear=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk; Sideways=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk|reject_dsr_nonpositive

## Panel / Variant Summary

| Market | TF | Variant | Trades | Mean | Win Rate | Net R |
|---|---:|---|---:|---:|---:|---:|
| SPY/USD | 1d | `provider_consensus_momentum` | 92 | 0.002238 | 0.5435 | 0.205856 |
| SPY/USD | 1d | `provider_pullback_reclaim` | 2 | 0.023778 | 1.0000 | 0.047556 |
| SPY/USD | 1d | `btc_crossvenue_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1d | `provider_breakdown_short` | 13 | -0.004125 | 0.4615 | -0.053627 |
| SPY/USD | 1d | `defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1d | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1d | `dispersion_reversion` | 20 | -0.002617 | 0.3500 | -0.052336 |
| SPY/USD | 1d | `provider_range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1d | `crisis_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1d | `crisis_defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1d | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPL/USD | 1d | `provider_consensus_momentum` | 73 | 0.002718 | 0.5342 | 0.198411 |
| AAPL/USD | 1d | `provider_pullback_reclaim` | 2 | -0.023126 | 0.0000 | -0.046252 |
| AAPL/USD | 1d | `btc_crossvenue_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPL/USD | 1d | `provider_breakdown_short` | 9 | 0.011525 | 0.6667 | 0.103726 |
| AAPL/USD | 1d | `defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPL/USD | 1d | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPL/USD | 1d | `dispersion_reversion` | 16 | 0.003489 | 0.4375 | 0.055829 |
| AAPL/USD | 1d | `provider_range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPL/USD | 1d | `crisis_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPL/USD | 1d | `crisis_defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPL/USD | 1d | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ES/USD | 1d | `provider_consensus_momentum` | 92 | 0.002545 | 0.5761 | 0.234130 |
| ES/USD | 1d | `provider_pullback_reclaim` | 1 | 0.041634 | 1.0000 | 0.041634 |
| ES/USD | 1d | `btc_crossvenue_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ES/USD | 1d | `provider_breakdown_short` | 13 | -0.009114 | 0.4615 | -0.118486 |
| ES/USD | 1d | `defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ES/USD | 1d | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ES/USD | 1d | `dispersion_reversion` | 18 | -0.001139 | 0.4444 | -0.020499 |
| ES/USD | 1d | `provider_range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ES/USD | 1d | `crisis_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ES/USD | 1d | `crisis_defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ES/USD | 1d | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USD | 1d | `provider_consensus_momentum` | 44 | 0.005025 | 0.4773 | 0.221110 |
| BTC/USD | 1d | `provider_pullback_reclaim` | 7 | 0.020325 | 0.7143 | 0.142277 |
| BTC/USD | 1d | `btc_crossvenue_carry` | 45 | 0.005007 | 0.5333 | 0.225325 |
| BTC/USD | 1d | `provider_breakdown_short` | 14 | -0.010018 | 0.3571 | -0.140248 |
| BTC/USD | 1d | `defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USD | 1d | `failed_reclaim_short` | 1 | 0.050747 | 1.0000 | 0.050747 |
| BTC/USD | 1d | `dispersion_reversion` | 15 | -0.007974 | 0.4667 | -0.119603 |
| BTC/USD | 1d | `provider_range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USD | 1d | `crisis_tail_short` | 1 | -0.020214 | 0.0000 | -0.020214 |
| BTC/USD | 1d | `crisis_defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USD | 1d | `crisis_panic_reversal` | 1 | 0.014200 | 1.0000 | 0.014200 |
| BTC/USDT | 1d | `provider_consensus_momentum` | 21 | -0.006554 | 0.3810 | -0.137638 |
| BTC/USDT | 1d | `provider_pullback_reclaim` | 2 | 0.041185 | 1.0000 | 0.082370 |
| BTC/USDT | 1d | `btc_crossvenue_carry` | 24 | -0.010502 | 0.4167 | -0.252046 |
| BTC/USDT | 1d | `provider_breakdown_short` | 7 | -0.007450 | 0.2857 | -0.052153 |
| BTC/USDT | 1d | `defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1d | `failed_reclaim_short` | 1 | 0.050199 | 1.0000 | 0.050199 |
| BTC/USDT | 1d | `dispersion_reversion` | 7 | -0.002753 | 0.4286 | -0.019273 |
| BTC/USDT | 1d | `provider_range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1d | `crisis_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1d | `crisis_defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1d | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1d | `provider_consensus_momentum` | 21 | -0.006634 | 0.3810 | -0.139309 |
| BTC/USDT | 1d | `provider_pullback_reclaim` | 2 | 0.041231 | 1.0000 | 0.082463 |
| BTC/USDT | 1d | `btc_crossvenue_carry` | 24 | -0.010563 | 0.4167 | -0.253502 |
| BTC/USDT | 1d | `provider_breakdown_short` | 7 | -0.007426 | 0.2857 | -0.051983 |
| BTC/USDT | 1d | `defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1d | `failed_reclaim_short` | 1 | 0.050156 | 1.0000 | 0.050156 |
| BTC/USDT | 1d | `dispersion_reversion` | 7 | -0.002642 | 0.4286 | -0.018495 |
| BTC/USDT | 1d | `provider_range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1d | `crisis_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1d | `crisis_defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1d | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| XBT/USD | 1d | `provider_consensus_momentum` | 42 | 0.005403 | 0.4762 | 0.226944 |
| XBT/USD | 1d | `provider_pullback_reclaim` | 3 | 0.023706 | 0.6667 | 0.071119 |
| XBT/USD | 1d | `btc_crossvenue_carry` | 46 | 0.005739 | 0.5652 | 0.264011 |
| XBT/USD | 1d | `provider_breakdown_short` | 9 | 0.009223 | 0.4444 | 0.083005 |
| XBT/USD | 1d | `defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| XBT/USD | 1d | `failed_reclaim_short` | 1 | 0.050831 | 1.0000 | 0.050831 |
| XBT/USD | 1d | `dispersion_reversion` | 11 | -0.006152 | 0.4545 | -0.067673 |
| XBT/USD | 1d | `provider_range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| XBT/USD | 1d | `crisis_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| XBT/USD | 1d | `crisis_defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| XBT/USD | 1d | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `provider_consensus_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `provider_pullback_reclaim` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `btc_crossvenue_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `provider_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `defensive_fx_long` | 10 | 0.006420 | 0.8000 | 0.064197 |
| EUR/USD | 1d | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `dispersion_reversion` | 24 | 0.000105 | 0.4583 | 0.002508 |
| EUR/USD | 1d | `provider_range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `crisis_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `crisis_defensive_fx_long` | 1 | -0.012901 | 0.0000 | -0.012901 |
| EUR/USD | 1d | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `provider_consensus_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `provider_pullback_reclaim` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `btc_crossvenue_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `provider_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `defensive_fx_long` | 10 | 0.007327 | 0.6000 | 0.073270 |
| EUR/USD | 1d | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `dispersion_reversion` | 23 | 0.000194 | 0.3478 | 0.004461 |
| EUR/USD | 1d | `provider_range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `crisis_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `crisis_defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPYx/USD | 1d | `provider_consensus_momentum` | 19 | 0.001513 | 0.6842 | 0.028744 |
| SPYx/USD | 1d | `provider_pullback_reclaim` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPYx/USD | 1d | `btc_crossvenue_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPYx/USD | 1d | `provider_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPYx/USD | 1d | `defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPYx/USD | 1d | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPYx/USD | 1d | `dispersion_reversion` | 5 | 0.002743 | 0.4000 | 0.013714 |
| SPYx/USD | 1d | `provider_range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPYx/USD | 1d | `crisis_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPYx/USD | 1d | `crisis_defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPYx/USD | 1d | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPX/USD | 1d | `provider_consensus_momentum` | 11 | -0.070701 | 0.2727 | -0.777709 |
| SPX/USD | 1d | `provider_pullback_reclaim` | 1 | 0.136581 | 1.0000 | 0.136581 |
| SPX/USD | 1d | `btc_crossvenue_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPX/USD | 1d | `provider_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPX/USD | 1d | `defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPX/USD | 1d | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPX/USD | 1d | `dispersion_reversion` | 4 | 0.028572 | 0.7500 | 0.114288 |
| SPX/USD | 1d | `provider_range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPX/USD | 1d | `crisis_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPX/USD | 1d | `crisis_defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPX/USD | 1d | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPLx/USD | 1d | `provider_consensus_momentum` | 14 | 0.012605 | 0.7143 | 0.176468 |
| AAPLx/USD | 1d | `provider_pullback_reclaim` | 2 | 0.009267 | 0.5000 | 0.018533 |
| AAPLx/USD | 1d | `btc_crossvenue_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPLx/USD | 1d | `provider_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPLx/USD | 1d | `defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPLx/USD | 1d | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPLx/USD | 1d | `dispersion_reversion` | 4 | -0.011199 | 0.2500 | -0.044796 |
| AAPLx/USD | 1d | `provider_range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPLx/USD | 1d | `crisis_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPLx/USD | 1d | `crisis_defensive_fx_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPLx/USD | 1d | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `provider_pullback_reclaim` | 22 | 3 | 2 | 1.0000 | 0.014111 | 1.000 | 3.0875 | 76.4499 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk` |
| Bear | `defensive_fx_long` | 20 | 3 | 2 | 1.0000 | 0.001777 | 1.000 | 1.9657 | 77.0395 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk` |
| Sideways | `dispersion_reversion` | 154 | 4 | 9 | 0.2500 | -0.005020 | 1.000 | -0.4019 | 18.7500 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | `crisis_panic_reversal` | 1 | 1 | 1 | 1.0000 | 0.014200 | 1.000 | 0.0000 | 60.1500 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk|reject_dsr_nonpositive` |
| Manipulation(scoped) | `short_tp120_sl060_h72` | 13535 | 12 | 1127 | 0.7500 | 0.005609 | 0.000 | 1.0000 | 100.0000 | `pass` |

## Inputs

- Raw provider OHLCV files: `/Users/thrill3r/Auto-Quant/user_data/data/raw`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^IXIC`
- Scoped Manipulation component: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2.md`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T212329-codex-board-b-provider-raw-daily-consensus-v1/branch-rc-spa/provider_raw_daily_consensus_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T212329-codex-board-b-provider-raw-daily-consensus-v1/branch-rc-spa/provider_raw_daily_consensus_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T212329-codex-board-b-provider-raw-daily-consensus-v1/branch-rc-spa/provider_raw_daily_consensus_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T212329-codex-board-b-provider-raw-daily-consensus-v1/branch-rc-spa/provider_raw_daily_consensus_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T212329-codex-board-b-provider-raw-daily-consensus-v1/branch-rc-spa/provider_raw_daily_consensus_panel_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T212329-codex-board-b-provider-raw-daily-consensus-v1/ict-engine-fail-closed/provider_raw_daily_consensus_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T212329-codex-board-b-provider-raw-daily-consensus-v1/checks/provider_raw_daily_consensus_v1_assertions.out`

## Next

- B2R-repeat: keep the 205047 scoped Manipulation component, but repair Bull/Bear/Sideways/Crisis with a different root family or provider panel; do not relax RC-SPA.
