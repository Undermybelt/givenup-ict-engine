# CrashRebound Branch RC-SPA v1

Run ID: `20260511T180121+0800-codex-crashrebound-branch-rc-spa-v1`

## Decision

- Promotion level: `reject`.
- Gate result: `fail:reject_missing_branch_path;reject_missing_required_roots;reject_overfit_risk;reject_cost_fragile;reject_tail_risk`.
- RC-SPA: `59.7901`.
- Trades: `207` from the real local Auto-Quant/Freqtrade runtime.
- Branch paths were emitted, but their source is an Auto-Quant calendar-regime proxy, not Board A source-owned per-trade labels.
- `Crisis` and scoped direct `Manipulation` have no trade-level evidence in this recipe run; no proxy overlay was promoted.
- PBO and formal DSR are not available from a single selected recipe without a candidate panel, so promotion fails closed.

## Branches

| Branch path | Root | Trades | Win rate | Net profit ratio sum | Source |
|---|---|---:|---:|---:|---|
| Bear -> BearMarketCapitulation -> ReboundAttempt -> CrashRebound | Bear | 32 | 0.6875 | 0.105629 | auto_quant_v0.4.1_calendar_regime_proxy_not_board_a_source_label |
| Bull -> BullPullback -> CapitulationMeanReversionSetup -> CrashRebound | Bull | 159 | 0.6730 | 1.226626 | auto_quant_v0.4.1_calendar_regime_proxy_not_board_a_source_label |
| Sideways -> RangeConsolidation -> MeanReversionSetup -> CrashRebound | Sideways | 16 | 0.8125 | 0.378407 | auto_quant_v0.4.1_calendar_regime_proxy_not_board_a_source_label |

## Hard Gates

| Gate | Result |
|---|---|
| `accepted_regime_id_present` | `True` |
| `accepted_regime_artifact` | `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv` |
| `branch_path_present` | `True` |
| `branch_path_source_accepted_board_a_labels` | `False` |
| `all_required_roots_present` | `False` |
| `missing_roots` | `['Crisis']` |
| `total_trades_gate` | `True` |
| `min_test_folds_gate` | `True` |
| `min_trades_per_test_fold_gate` | `True` |
| `fold_positive_rate` | `0.8` |
| `fold_positive_rate_gate` | `True` |
| `bootstrap_edge_lcb_5pct` | `0.0015987614903785533` |
| `bootstrap_edge_lcb_gate` | `True` |
| `cost_stress_survival` | `False` |
| `pbo` | `None` |
| `pbo_gate` | `False` |
| `pbo_note` | `not computable from one selected recipe without a candidate panel` |
| `dsr` | `None` |
| `dsr_proxy` | `2.091119386051054` |
| `dsr_gate` | `True` |
| `dsr_note` | `proxy only; formal DSR not available in Auto-Quant artifact` |
| `tail_loss_p95` | `0.10322619762881445` |
| `tail_loss_budget` | `0.05` |
| `tail_loss_gate` | `False` |
| `regime_specificity_ratio` | `4.294021250648969` |
| `regime_specificity_gate` | `True` |

## Artifacts

- Trades CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T180121-codex-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_trades_v1.csv`
- Fold CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T180121-codex-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_folds_v1.csv`
- Summary JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T180121-codex-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_rc_spa_v1.json`
- Import library JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T180121-codex-crashrebound-branch-rc-spa-v1/branch-rc-spa/auto_quant_strategy_library.crashrebound_branch_v1.json`

## Next

Rerun or transform the recipe on Board A source-labeled branch rows before any pre-Bayes/BBN/CatBoost/execution-tree promotion attempt.
