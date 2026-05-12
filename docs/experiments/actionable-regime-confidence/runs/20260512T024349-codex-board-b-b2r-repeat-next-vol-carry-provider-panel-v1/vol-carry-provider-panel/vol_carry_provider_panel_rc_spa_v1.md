# B2R Repeat Next Vol/Carry Provider Panel v1

Run id: `20260512T024349+0800-codex-board-b-b2r-repeat-next-vol-carry-provider-panel-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `62.7967`
- Selected trade rows: `56810`
- Variant trade rows: `279211`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Root trade counts: `{'Bull': 32387, 'Bear': 19962, 'Sideways': 4283, 'Crisis': 178, 'Manipulation(scoped)': 3211}`
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
| Bull | 32387 | 6 | 647 | 0.5000 | 0.000515 | 0.00 | 4.7143 | 999.000 | 62.7967 | `fail:reject_fold_inconsistency|reject_cost_fragile` |
| Bear | 19962 | 5 | 801 | 0.4000 | -0.000756 | 1.00 | -1.0471 | -0.729 | 21.0000 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Sideways | 4283 | 6 | 72 | 0.1667 | -0.002838 | 0.00 | -4.9295 | -6.272 | 27.5000 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | 178 | 2 | 68 | 0.5000 | -0.021628 | 1.00 | -4.0631 | -76.041 | 22.5000 | `fail:reject_insufficient_test_folds|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Manipulation(scoped) | 3211 | 13 | 1 | 0.5385 | -0.001004 | 1.00 | 0.6958 | -0.020 | 30.0000 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T024349-codex-board-b-b2r-repeat-next-vol-carry-provider-panel-v1/vol-carry-provider-panel/vol_carry_provider_panel_rc_spa_v1.json`
- Provider panel inputs: `docs/experiments/actionable-regime-confidence/runs/20260512T024349-codex-board-b-b2r-repeat-next-vol-carry-provider-panel-v1/vol-carry-provider-panel/vol_carry_provider_panel_inputs_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260512T024349-codex-board-b-b2r-repeat-next-vol-carry-provider-panel-v1/vol-carry-provider-panel/vol_carry_provider_panel_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260512T024349-codex-board-b-b2r-repeat-next-vol-carry-provider-panel-v1/vol-carry-provider-panel/vol_carry_provider_panel_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260512T024349-codex-board-b-b2r-repeat-next-vol-carry-provider-panel-v1/vol-carry-provider-panel/vol_carry_provider_panel_branch_summary_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T024349-codex-board-b-b2r-repeat-next-vol-carry-provider-panel-v1/checks/vol_carry_provider_panel_v1_assertions.out`

## Next

- Do not promote downstream from this vol/carry panel. Use the failure tags to seed a new B2R nursery branch with stronger Sideways/Crisis edge or source-owned Manipulation PnL; only run Pre-Bayes/BBN/CatBoost/execution-tree after all required root branches pass RC-SPA.
