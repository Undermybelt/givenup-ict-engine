# NQ Root-Aware Tomac Branch RC-SPA v1

Run id: `20260511T184218+0800-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1`.

## Decision

- Gate result: `fail:all_branch_paths_failed_rc_spa_hard_gates`
- Stable profit score: `61.0545`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Required root failures: `Bull, Bear, Sideways, Crisis`
- Root trade counts: `{'Bull': 4080, 'Bear': 803, 'Sideways': 1109, 'Crisis': 182}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: TomacNQRootAwareBranchMatrixV1 uses the accepted ^IXIC-to-NQ daily root attachment and real local Auto-Quant/Freqtrade NQ 1h data, but downstream promotion is allowed only if every required root branch clears RC-SPA hard gates.

## Inputs

- Auto-Quant root: `/Users/thrill3r/Auto-Quant`
- Auto-Quant config: `/Users/thrill3r/Auto-Quant/config.tomac.json`
- Pair: `NQ/USD`
- Timerange: `20110101-20251231`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Board A NQ attachment: `docs/experiments/actionable-regime-confidence/runs/20260511T170714-codex-qqq-nq-daily-crossmarket-attachment-v1/crossmarket-attachment/qqq_nq_daily_crossmarket_attachment_v1.md`
- Source anchor: `^IXIC`; target: `NQ=F`; local data: `NQ_USD-1h.feather`

## Variant Backtests

| Variant | Trades | Win Rate | Profit % | Sharpe | Drawdown % | Log |
|---|---:|---:|---:|---:|---:|---|
| `baseline_4h` | 6174 | 0.5081 | 233.9863 | 0.7794 | -11.8232 | `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1/logs/freqtrade_backtest_baseline_4h.out` |
| `dense_2h` | 9240 | 0.5103 | 459.6357 | 1.2435 | -17.5315 | `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1/logs/freqtrade_backtest_dense_2h.out` |
| `swing_8h` | 4195 | 0.5290 | 779.6487 | 0.8678 | -7.1673 | `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1/logs/freqtrade_backtest_swing_8h.out` |
| `wide_16h` | 3691 | 0.5194 | 1228.8646 | 0.7066 | -15.8488 | `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1/logs/freqtrade_backtest_wide_16h.out` |

## Branch Summary

| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | 4080 | 15 | 40 | 0.8667 | 0.000120 | 0.00 | 3.7168 | 61.0545 | `fail:reject_cost_fragile|reject_no_regime_specificity` |
| Bear | 803 | 13 | 12 | 0.7692 | -0.000221 | 0.06 | 0.9535 | 57.7500 | `fail:reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60` |
| Sideways | 1109 | 15 | 29 | 0.7333 | 0.000025 | 0.05 | 1.7712 | 59.4853 | `fail:reject_fold_inconsistency|reject_cost_fragile|reject_rc_spa_below_60` |
| Crisis | 182 | 5 | 16 | 0.6000 | -0.000786 | 0.40 | 0.3658 | 35.7390 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Manipulation(scoped) | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.00 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1/branch-rc-spa/nq_rootaware_tomac_branch_rc_spa_report_v1.json`
- Generated strategy: `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1/strategy/TomacNQRootAwareBranchMatrixV1.py`
- Root schedule: `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1/strategy/nq_ixic_root_schedule_v1.json`
- Trade rows: `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1/branch-rc-spa/nq_rootaware_tomac_branch_path_trades_v1.csv`
- Variant branch rows: `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1/branch-rc-spa/nq_rootaware_tomac_variant_branch_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1/branch-rc-spa/nq_rootaware_tomac_branch_rc_spa_summary_v1.csv`
- Backtest summary: `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1/branch-rc-spa/nq_rootaware_tomac_backtest_summaries_v1.csv`
- Provider snapshots: `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1/checks/provider-status-yfinance.agent.json`, `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1/checks/provider-status-tradingview_mcp.agent.json`, `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1/checks/provider-status-kraken_public.agent.json`, `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1/checks/provider-status-ibkr.agent.json`

## Next

- B2R-repeat: keep NQ/Tomac evidence only if branch gates improve; otherwise broaden root/source labels or synthesize another root-aware recipe before downstream promotion.
