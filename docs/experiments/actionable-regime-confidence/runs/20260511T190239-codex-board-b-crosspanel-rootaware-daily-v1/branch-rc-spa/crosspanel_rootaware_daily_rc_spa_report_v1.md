# Cross-Panel Root-Aware Daily RC-SPA v1

Run id: `20260511T190239+0800-codex-board-b-crosspanel-rootaware-daily-v1`.

## Decision

- Gate result: `fail:all_branch_paths_failed_rc_spa_hard_gates`
- Stable profit score: `84.2333`
- Selected trade rows: `231`
- Variant trade rows: `775`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Root trade counts: `{'Bull': 128, 'Bear': 33, 'Sideways': 70, 'Crisis': 0, 'Manipulation(scoped)': 0}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Cross-panel daily Auto-Quant/Freqtrade readback changed the source/panel surface, but at least one required root branch still failed RC-SPA hard gates; scoped Manipulation remains zero direct rows.

## Inputs

- Auto-Quant root: `/Users/thrill3r/Auto-Quant`
- Auto-Quant config: `/Users/thrill3r/Auto-Quant/config.tomac.json`
- Pairs: `SPY/USD, QQQ/USD, NQ/USD, AAPL/USD, ES/USD`
- Pair source anchors: `{'SPY/USD': '^GSPC', 'QQQ/USD': '^IXIC', 'NQ/USD': '^IXIC', 'AAPL/USD': 'AAPL', 'ES/USD': '^GSPC'}`
- Timerange: `20110101-20251231`
- Provider/panel probe: `docs/experiments/actionable-regime-confidence/runs/20260511T184121-codex-board-b-crisis-panel-provider-probe-v1/crisis_panel_provider_probe_v1.md`

## Variant Backtests

| Variant | Trades | Win Rate % | Profit % | Sharpe | PF | Log |
|---|---:|---:|---:|---:|---:|---|
| `dense_5d` | 231 | 60.606 | 15.910 | 0.1346 | 1.566 | `docs/experiments/actionable-regime-confidence/runs/20260511T190239-codex-board-b-crosspanel-rootaware-daily-v1/logs/freqtrade_backtest_dense_5d.out` |
| `swing_10d` | 113 | 62.832 | 12.520 | 0.0703 | 1.573 | `docs/experiments/actionable-regime-confidence/runs/20260511T190239-codex-board-b-crosspanel-rootaware-daily-v1/logs/freqtrade_backtest_swing_10d.out` |
| `broad_rebound_7d` | 223 | 58.296 | 15.980 | 0.1104 | 1.447 | `docs/experiments/actionable-regime-confidence/runs/20260511T190239-codex-board-b-crosspanel-rootaware-daily-v1/logs/freqtrade_backtest_broad_rebound_7d.out` |
| `stress_only_15d` | 76 | 68.421 | 13.310 | 0.0649 | 1.824 | `docs/experiments/actionable-regime-confidence/runs/20260511T190239-codex-board-b-crosspanel-rootaware-daily-v1/logs/freqtrade_backtest_stress_only_15d.out` |
| `cost_filtered_3d` | 132 | 63.636 | 5.700 | 0.0461 | 1.353 | `docs/experiments/actionable-regime-confidence/runs/20260511T190239-codex-board-b-crosspanel-rootaware-daily-v1/logs/freqtrade_backtest_cost_filtered_3d.out` |

## Branch Summary

| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | Specificity | RC-SPA | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | 128 | 5 | 1 | 0.6000 | -0.000885 | 0.40 | 1.0834 | 0.283 | 42.5061 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Bear | 33 | 5 | 3 | 1.0000 | 0.007626 | 0.20 | 3.1390 | 13.157 | 84.2333 | `fail:reject_thin_trades` |
| Sideways | 70 | 4 | 9 | 0.5000 | -0.003971 | 0.40 | 0.2284 | 0.129 | 28.8917 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.00 | 0.0000 | 0.000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Manipulation(scoped) | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.00 | 0.0000 | 0.000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T190239-codex-board-b-crosspanel-rootaware-daily-v1/branch-rc-spa/crosspanel_rootaware_daily_rc_spa_report_v1.json`
- Generated strategy: `docs/experiments/actionable-regime-confidence/runs/20260511T190239-codex-board-b-crosspanel-rootaware-daily-v1/strategy/CrossPanelRootAwareDailyV1.py`
- Root schedule: `docs/experiments/actionable-regime-confidence/runs/20260511T190239-codex-board-b-crosspanel-rootaware-daily-v1/strategy/crosspanel_root_schedule_v1.json`
- Selected trade rows: `docs/experiments/actionable-regime-confidence/runs/20260511T190239-codex-board-b-crosspanel-rootaware-daily-v1/branch-rc-spa/crosspanel_rootaware_daily_selected_trades_v1.csv`
- Variant trade rows: `docs/experiments/actionable-regime-confidence/runs/20260511T190239-codex-board-b-crosspanel-rootaware-daily-v1/branch-rc-spa/crosspanel_rootaware_daily_variant_trades_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T190239-codex-board-b-crosspanel-rootaware-daily-v1/branch-rc-spa/crosspanel_rootaware_daily_branch_summary_v1.csv`
- Backtest summary: `docs/experiments/actionable-regime-confidence/runs/20260511T190239-codex-board-b-crosspanel-rootaware-daily-v1/branch-rc-spa/crosspanel_rootaware_daily_backtest_summary_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T190239-codex-board-b-crosspanel-rootaware-daily-v1/checks/crosspanel_rootaware_daily_v1_assertions.out`

## Next

- B2R-repeat: do not promote downstream; acquire real direct Manipulation rows or move to a different non-Tomac family with explicit provider/panel change.
