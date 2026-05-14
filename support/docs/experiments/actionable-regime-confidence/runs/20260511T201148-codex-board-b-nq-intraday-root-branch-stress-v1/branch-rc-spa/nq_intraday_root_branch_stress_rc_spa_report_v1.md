# Root Transition Triad RC-SPA v1

Run id: `20260511T201148+0800-codex-board-b-nq-intraday-root-branch-stress-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `27.6672`
- Variant rows: `270361`
- Selected rows: `22842`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Selected root counts: `{'Bull': 16154, 'Bear': 1989, 'Sideways': 4517, 'Crisis': 182, 'Manipulation(scoped)': 0}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Bear=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Sideways=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60

## Panel / Variant Summary

| Market | TF | Variant | Trades | Mean | Win Rate | Net R |
|---|---:|---|---:|---:|---:|---:|
| NQ/USD | 15m | `bear_intraday_breakdown_short` | 20219 | -0.000641 | 0.3782 | -12.957726 |
| NQ/USD | 15m | `bear_intraday_relief_long` | 25221 | -0.000739 | 0.3300 | -18.646110 |
| NQ/USD | 15m | `bear_intraday_vol_compression_short` | 15339 | -0.000573 | 0.3979 | -8.783216 |
| NQ/USD | 15m | `sideways_intraday_band_reversion` | 27752 | -0.000709 | 0.3355 | -19.686824 |
| NQ/USD | 15m | `sideways_intraday_range_breakout` | 20270 | -0.000584 | 0.3632 | -11.844612 |
| NQ/USD | 15m | `sideways_intraday_microtrend_filter` | 22431 | -0.000623 | 0.3601 | -13.980683 |
| NQ/USD | 15m | `crisis_intraday_tail_short` | 20941 | -0.000632 | 0.3778 | -13.226653 |
| NQ/USD | 15m | `crisis_intraday_relief_long` | 26417 | -0.000681 | 0.3366 | -17.996028 |
| NQ/USD | 15m | `crisis_intraday_abstain_defensive` | 25989 | -0.000693 | 0.3388 | -18.008448 |
| NQ/USD | 1h | `bear_intraday_breakdown_short` | 7031 | -0.000450 | 0.4443 | -3.164826 |
| NQ/USD | 1h | `bear_intraday_relief_long` | 7761 | -0.000661 | 0.4222 | -5.130126 |
| NQ/USD | 1h | `bear_intraday_vol_compression_short` | 5716 | -0.000353 | 0.4573 | -2.017610 |
| NQ/USD | 1h | `sideways_intraday_band_reversion` | 8333 | -0.000511 | 0.4255 | -4.256126 |
| NQ/USD | 1h | `sideways_intraday_range_breakout` | 6135 | -0.000193 | 0.4606 | -1.181805 |
| NQ/USD | 1h | `sideways_intraday_microtrend_filter` | 7054 | -0.000285 | 0.4536 | -2.007638 |
| NQ/USD | 1h | `crisis_intraday_tail_short` | 7156 | -0.000440 | 0.4521 | -3.146228 |
| NQ/USD | 1h | `crisis_intraday_relief_long` | 8139 | -0.000466 | 0.4314 | -3.794280 |
| NQ/USD | 1h | `crisis_intraday_abstain_defensive` | 8457 | -0.000565 | 0.4215 | -4.782213 |

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `bear_intraday_breakdown_short` | 16154 | 15 | 194 | 0.0667 | -0.000501 | 0.000 | -15.1090 | 26.0000 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Bear | `bear_intraday_vol_compression_short` | 1989 | 13 | 35 | 0.3846 | -0.000378 | 0.231 | -0.3365 | 21.5385 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Sideways | `sideways_intraday_range_breakout` | 4517 | 15 | 89 | 0.1333 | -0.000745 | 0.200 | -7.5484 | 19.0000 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | `crisis_intraday_relief_long` | 182 | 5 | 7 | 0.4000 | -0.001311 | 0.200 | -0.9535 | 27.6672 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Manipulation(scoped) | `no_direct_event_rows` | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.000 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Inputs

- Local Auto-Quant feathers: `/Users/thrill3r/Auto-Quant/user_data/data`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^IXIC`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T201148-codex-board-b-nq-intraday-root-branch-stress-v1/branch-rc-spa/nq_intraday_root_branch_stress_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T201148-codex-board-b-nq-intraday-root-branch-stress-v1/branch-rc-spa/nq_intraday_root_branch_stress_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T201148-codex-board-b-nq-intraday-root-branch-stress-v1/branch-rc-spa/nq_intraday_root_branch_stress_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T201148-codex-board-b-nq-intraday-root-branch-stress-v1/branch-rc-spa/nq_intraday_root_branch_stress_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T201148-codex-board-b-nq-intraday-root-branch-stress-v1/branch-rc-spa/nq_intraday_root_branch_stress_panel_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T201148-codex-board-b-nq-intraday-root-branch-stress-v1/ict-engine-fail-closed/nq_intraday_root_branch_stress_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T201148-codex-board-b-nq-intraday-root-branch-stress-v1/checks/nq_intraday_root_branch_stress_v1_assertions.out`

## Next

- B2R-repeat: keep RootTransitionTriad as fail-closed evidence; direct Manipulation still needs trade/PnL rows, and failed roots need a different family or provider panel without relaxing RC-SPA.
