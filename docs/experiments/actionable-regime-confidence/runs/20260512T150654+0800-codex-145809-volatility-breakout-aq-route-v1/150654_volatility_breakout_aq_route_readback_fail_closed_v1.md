# 150654 Volatility Breakout AQ Route Readback Fail-Closed v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T150654+0800-codex-145809-volatility-breakout-aq-route-v1`

This is a terminal readback for the Board B `150654` volatility-breakout branch-seed route. It is profitability-factor support evidence only. It does not promote a candidate, does not make a live-trade claim, and does not call `update_goal`.

## Evidence

- Packet assertions: `checks/volatility_breakout_packet_assertions.out`
- Recipe packet: `summaries/volatility_breakout_recipe_packet_v1.json`
- Walk-forward summary: `summaries/volatility_breakout_walkforward_summary.csv`
- Provider provenance matrix: `derived/aq_provider_provenance_volatility_breakout.csv`
- Real-trade rows: `derived/volatility_breakout_real_trades.jsonl`
- Policy training summary: `state_volatility_breakout_v1/B2R_VOL_BREAKOUT_150654/policy_training/structural_path_ranking_target_summary.json`
- Workflow readbacks: `command-output/16_workflow_execution_candidate.out`, `command-output/17_workflow_full.out`

## Readback

- Checks `01_build_volatility_breakout_packet`, `04_auto_quant_ingest_real_trades`, and `05` through `17` exited `0`.
- Checks `02_auto_quant_results_import` and `03_auto_quant_prior_init` exited `1` because `strategy_library_volatility_breakout_v1.json` did not parse as an Auto-Quant strategy-library manifest: `invalid type: string "not_auto_quant_native_backtest", expected struct StrategyLibraryValidationError`.
- The packet preserved branch path `trend_expansion->high_volatility->up_momentum->volatility_breakout_follow`.
- The branch packet had `348` trades, `182` wins, `166` losses, win rate `0.5229885057471264`, profit factor `1.3270317756098415`, and total return units `0.853466166924505`.
- Provider counts were Binance `269`, IBKR `47`, and Yahoo/YF `32`.
- The provider matrix emitted six required provider rows, but TVR, Kraken, and Bybit were not acquired for this branch seed.
- Walk-forward was weak: only `2/10` folds passed.
- Path-ranker runtime was enabled in `candidate_set_only` mode with CatBoost model family visible, but calibration remained not fitted.
- Target-row validation stayed below gate: `raw_scored_mature=1/30`, `production_validation=0/30`; observation validation was `348/30`.
- Workflow stayed observe/not actionable: `review_status=observe`, `ready=false`, `actionable=false`, selected path probability `0.6644427013798627`, and no calibrated path probability or lower bound.

## Gate

- `support_once:150654_volatility_breakout_aq_route_v1`
- `evidence_class:volatility_breakout_branch_seed_downstream_fail_closed`
- `pass:branch_path_preserved`
- `pass:trade_count_348`
- `pass:profit_factor_1_327`
- `pass:observation_validation_348_of_30`
- `partial:path_ranker_runtime_candidate_set_scores_visible`
- `fail_closed:auto_quant_results_import_exit1`
- `fail_closed:auto_quant_prior_init_exit1`
- `fail_closed:not_auto_quant_native_backtest`
- `fail_closed:six_provider_rows_emitted_but_not_acquired`
- `fail_closed:tvr_kraken_bybit_absent`
- `fail_closed:walk_forward_only_2_of_10_pass`
- `fail_closed:raw_scored_mature_1_of_30`
- `fail_closed:production_validation_0_of_30`
- `fail_closed:calibrated_path_prob_absent`
- `fail_closed:path_prob_lower_bound_absent`
- `fail_closed:ready_false`
- `fail_closed:actionable_false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Next

Count this root exactly once as volatility-breakout branch-seed downstream evidence. Do not promote it. A valid continuation must use an AQ-native or AQ-routed packet with actual same-root acquisition for all required provider rows, all walk-forward folds passing or a documented stricter survivor rule, mature raw-scored/production path-ranker validation, calibrated path probability/lower bound, and non-observe execution-tree admission.
