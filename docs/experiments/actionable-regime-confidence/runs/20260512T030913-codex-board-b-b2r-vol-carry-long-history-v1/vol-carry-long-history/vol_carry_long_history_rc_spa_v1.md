# B2R Repeat Next Vol/Carry Provider Panel v1

Run id: `20260512T030913+0800-codex-board-b-b2r-vol-carry-long-history-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `58.8223`
- Selected trade rows: `63290`
- Variant trade rows: `305856`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Root trade counts: `{'Bull': 34575, 'Bear': 22632, 'Sideways': 5868, 'Crisis': 215, 'Manipulation(scoped)': 3211}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: B2R-repeat-next used a materially different local Auto-Quant provider panel and volatility/liquidity/carry family, but required root branches still fail RC-SPA hard gates; downstream promotion remains blocked.

## Inputs

- Auto-Quant data root: `/Users/thrill3r/Auto-Quant/user_data/data`
- Board A source roots: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv`
- Accepted regime artifact: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Existing scoped Manipulation component: `docs/experiments/actionable-regime-confidence/runs/20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/branch-rc-spa/root_plus_manip_bridge_branch_summary_v1.csv`

## Branch Summary

| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | Specificity | RC-SPA | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | 34575 | 16 | 232 | 0.3125 | 0.000457 | 0.00 | 4.4257 | 999.000 | 58.8223 | `fail:reject_fold_inconsistency|reject_cost_fragile|reject_rc_spa_below_60` |
| Bear | 22632 | 13 | 142 | 0.5385 | -0.000556 | 0.50 | -0.4969 | -0.485 | 23.0769 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Sideways | 5868 | 16 | 49 | 0.0625 | -0.002449 | 0.56 | -6.2128 | -5.999 | 15.9375 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | 215 | 4 | 12 | 0.2500 | -0.018897 | 0.75 | -4.1763 | -82.810 | 18.7500 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Manipulation(scoped) | 3211 | 13 | 1 | 0.5385 | -0.001004 | 1.00 | 0.6958 | -0.020 | 30.0000 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T030913-codex-board-b-b2r-vol-carry-long-history-v1/vol-carry-long-history/vol_carry_long_history_rc_spa_v1.json`
- Provider panel inputs: `docs/experiments/actionable-regime-confidence/runs/20260512T030913-codex-board-b-b2r-vol-carry-long-history-v1/vol-carry-long-history/vol_carry_long_history_inputs_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260512T030913-codex-board-b-b2r-vol-carry-long-history-v1/vol-carry-long-history/vol_carry_long_history_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260512T030913-codex-board-b-b2r-vol-carry-long-history-v1/vol-carry-long-history/vol_carry_long_history_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260512T030913-codex-board-b-b2r-vol-carry-long-history-v1/vol-carry-long-history/vol_carry_long_history_branch_summary_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T030913-codex-board-b-b2r-vol-carry-long-history-v1/checks/vol_carry_long_history_v1_assertions.out`

## Next

- Do not promote downstream from this vol/carry panel. Use the failure tags to seed a new B2R nursery branch with stronger Sideways/Crisis edge or source-owned Manipulation PnL; only run Pre-Bayes/BBN/CatBoost/execution-tree after all required root branches pass RC-SPA.
