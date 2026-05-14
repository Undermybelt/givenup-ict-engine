# Crisis Volatility Expansion Fade Branch Selection v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T145305+0800-codex-long-history-esnq-factor-density-screen-v1`

Source artifact set:
- `factor_candidate_trades.csv`
- `factor_candidate_summary_by_branch.csv`
- `factor_candidate_summary_by_period.csv`
- `factor_candidate_rankings.csv`
- `aq_provider_provenance_sidecar.csv`

## Selection

The global primary ranking is not a promotion candidate. `TwentyHourBreakoutContinuationV1` has `2454` primary ES/NQ trades but negative average return and return profit factor below one.

The only branch-level candidate worth carrying forward is:

`Crisis -> VolatilityShock -> SixHourExhaustionFade -> VolatilityExpansionFadeV1`

Primary ES/NQ combined readback:
- `trades=1082`
- `wins=566`
- `win_rate=0.5231053604436229`
- `mean_net_return=0.0014706924186166776`
- `sum_net_return=1.5912891969432452`
- `return_profit_factor=1.230380812816915`
- `symbols=ES:657,NQ:425`
- `periods=pre_2018:149,2018_2020:202,2021_2022:319,2023_2024:412`

Per-symbol primary readback:
- ES Crisis branch: `trades=657`, `win_rate=0.550989`, `wilson95_lcb=0.512768`, `mean_net_return=0.001248`, `sum_net_return=0.819613`, `return_profit_factor=1.463931`, `max_drawdown_compounded=-0.194334`.
- NQ Crisis branch: `trades=425`, `win_rate=0.48`, `wilson95_lcb=0.432893`, `mean_net_return=0.001816`, `sum_net_return=0.771676`, `return_profit_factor=1.150116`, `max_drawdown_compounded=-0.560168`.

Support-market readback is mixed:
- XAU Crisis branch: `trades=104`, `return_profit_factor=1.059704`.
- YM Crisis branch: `trades=44`, `return_profit_factor=1.844086`, too few trades.
- EUR Crisis branch: `trades=192`, `return_profit_factor=0.908705`.

## Gate

- `evidence_class:local_branch_candidate_selection_not_promotion`.
- `selected_branch_path:Crisis -> VolatilityShock -> SixHourExhaustionFade -> VolatilityExpansionFadeV1`.
- `pass:branch_path_fields_emitted`.
- `pass:primary_esnq_combined_trades_1082`.
- `pass:primary_esnq_return_profit_factor_1_2304`.
- `partial:es_branch_wilson95_lcb_above_0_50`.
- `partial:nq_branch_profitable_but_wilson95_lcb_below_0_50`.
- `partial:chronological_buckets_positive_in_primary_esnq`.
- `fail_closed:provider_authority_missing_for_this_screen`.
- `fail_closed:support_market_eur_negative`.
- `fail_closed:ym_support_trade_count_44_too_low`.
- `fail_closed:no_auto_quant_provider_routed_recipe_yet`.
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_chain`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Carry only this branch into a provider-backed or portable recipe attempt. The next valid packet must turn `VolatilityExpansionFadeV1` into an Auto-Quant/provider-routed material surface, acquire or attach provider provenance, and then pass the branch packet through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree. Do not promote from this local density screen alone.
