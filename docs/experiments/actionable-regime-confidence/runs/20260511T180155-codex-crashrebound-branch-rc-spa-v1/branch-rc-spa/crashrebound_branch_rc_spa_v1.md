# CrashRebound Branch RC-SPA v1

Run ID: `20260511T180155+0800-codex-crashrebound-branch-rc-spa-v1`

## Decision

- Gate result: `fail:reject_missing_accepted_per_trade_root_labels;reject_missing_required_roots_sideways_crisis;reject_min_test_folds_lt4;research_watch_branch_path_not_consumed`; promotion level `reject`.
- Extracted real FreqTrade trade rows from local Auto-Quant in-process Backtesting without editing Auto-Quant source files.
- Branch paths are present, but they are timerange-proxy labels, not Board A accepted per-trade root-label joins.
- `Sideways`, `Crisis`, and scoped direct `Manipulation` branch rows are absent for this recipe artifact.
- Pre-Bayes, BBN, CatBoost/path-ranker, and execution-tree branch consumption remain unverified.

## Fold Rows

| Fold | Root | Trades | Win % | Profit % | PF | Branch Path | Status |
|---|---|---:|---:|---:|---:|---|---|
| bull_2021 | Bull | 50 | 70.000 | 24.873 | 2.139 | `Bull -> DrawdownPullback -> OversoldRebound -> CrashRebound` | root_conditioned_timerange_proxy |
| winter_2022 | Bear | 32 | 68.750 | 2.990 | 1.143 | `Bear -> DrawdownCapitulation -> OversoldRebound -> CrashRebound` | root_conditioned_timerange_proxy |
| recovery_23_25 | unresolved_mixed_recovery | 123 | 66.667 | 17.295 | 1.268 | `unresolved_mixed_recovery -> PostBearRecovery -> OversoldRebound -> CrashRebound` | mixed_recovery_timerange_proxy_not_canonical_root |
| full_5y | mixed_overlap_not_a_root | 207 | 68.599 | 55.691 | 1.416 | `mixed_overlap_not_a_root -> AggregateBacktest -> OversoldRebound -> CrashRebound` | overlap_aggregate_not_used_for_rc_spa |

## Hard Gates

| Gate | Pass | Evidence |
|---|---:|---|
| `accepted_regime_id_present` | true | docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv |
| `branch_path_present` | true | all canonical fold rows emit regime_profit_branch_path |
| `accepted_per_trade_root_label_join` | false | root_label_source=timerange_proxy_not_board_a_per_trade_join |
| `required_main_roots_covered` | false | missing=Crisis,Sideways |
| `scoped_manipulation_overlay_joined` | false | manipulation_overlay_state=not_joined_abstain |
| `min_total_trades_gte_100` | false | canonical_trade_rows=82 |
| `min_test_folds_gte_4` | false | canonical_nonoverlapping_folds=2 |
| `min_trades_per_test_fold_gte_10` | true | bull_2021=50,winter_2022=32 |
| `fold_positive_rate_gte_0_75` | true | fold_positive_rate=1.000000 |
| `bootstrap_edge_lcb_5pct_gt_0` | false | bootstrap_edge_lcb_5pct=-0.00106078 |
| `cost_stress_survival_true` | false | 2x fee proxy subtracts extra 20 bps round trip; stressed_lcb=-0.00306078 |
| `pbo_lte_0_25` | false | not_computable_without_4plus_nonoverlapping_folds_or_model_selection_matrix |
| `dsr_gt_0` | false | not_computable_from_current artifact; no deflated-sharpe trials matrix |
| `tail_loss_p95_lte_budget` | false | tail_loss_p95=0.17779169; configured_risk_budget=missing |
| `regime_specificity_ratio_gte_1_20` | false | not_computable_without out-of-branch baseline roots |
| `downstream_branch_consumption_verified` | false | pre_bayes/bbn/catboost/execution_tree not run because hard gates failed |

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T180155-codex-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_rc_spa_v1.json`
- Fold CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T180155-codex-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_rc_spa_v1_folds.csv`
- Trade CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T180155-codex-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_rc_spa_v1_trades.csv`
- Hard gates CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T180155-codex-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_rc_spa_v1_hard_gates.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T180155-codex-crashrebound-branch-rc-spa-v1/checks/crashrebound_branch_rc_spa_v1_assertions.out`
