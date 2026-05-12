# 150654 Manifest Schema Repair Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T150654+0800-codex-145809-volatility-breakout-aq-route-v1`

This is an additive correction to the earlier `150654` terminal readback. It does not promote the factor, does not make a live-trade claim, and does not call `update_goal`.

## Repair

- The first Auto-Quant import/prior steps failed because `validation_errors` in `strategy_library_volatility_breakout_v1.json` were emitted as strings.
- The run-local generator was repaired to emit structured `{file,error}` validation-error objects.
- The packet was rebuilt without changing the selected branch, source rows, provider matrix, walk-forward folds, real-trade JSONL, or repo runtime code.

## Command Evidence

- `checks/18_rebuild_packet_after_manifest_schema_fix.exit=0`
- `checks/19_auto_quant_results_import_after_manifest_schema_fix.exit=0`
- `checks/20_auto_quant_prior_init_after_manifest_schema_fix.exit=0`
- `checks/21_pre_bayes_status_after_manifest_schema_fix.exit=0`
- `checks/22_policy_training_status_after_manifest_schema_fix.exit=0`
- `checks/23_workflow_execution_candidate_after_manifest_schema_fix.exit=0`
- `checks/24_workflow_full_after_manifest_schema_fix.exit=0`

## Readback

- `auto-quant-results-import` now parsed manifest version `1.0` and imported `1/1` strategy; `n_meta_invalid=3` remains as structured validation metadata for non-native-AQ and missing-provider caveats.
- `auto-quant-prior-init` now applied the volatility-breakout strategy with `348` trades, `182` wins, `166` losses, and final prior probabilities `[0.5337068764044944, 0.0000004943820224719101, 0.4662926292134832]`.
- Branch packet metrics stayed unchanged: `348` rows, win rate `0.5229885057471264`, profit factor `1.3270317756098415`, total return units `0.853466166924505`.
- Walk-forward remains fail-closed: only `2/10` yearly folds passed.
- Same-root provider authority remains fail-closed: Binance, IBKR, and Yahoo/YF rows exist; TVR, Kraken, and Bybit rows are emitted but not acquired.
- Policy training after repair still rejects production readiness: `raw_scored_mature=1/30`, `production_validation=0/30`, `observation_validation=348/30`, `calibration=not_fitted`.
- CatBoost candidate-set runtime is visible (`runtime_matches=2`, model family `catboost`), but calibrated path probability and lower bound remain absent.
- Execution candidate preserves the exact branch path `trend_expansion->high_volatility->up_momentum->volatility_breakout_follow`, but remains `ready=false`, `actionable=false`, `review_status=observe`.

## Gate

- `correction:150654_manifest_schema_repair`
- `pass:auto_quant_results_import_after_schema_fix_exit0`
- `pass:auto_quant_prior_init_after_schema_fix_exit0`
- `pass:exact_branch_path_preserved`
- `pass:observation_validation_348_of_30`
- `partial:catboost_candidate_set_runtime_visible`
- `fail_closed:not_auto_quant_native_backtest`
- `fail_closed:tvr_kraken_bybit_not_acquired`
- `fail_closed:walk_forward_only_2_of_10_pass`
- `fail_closed:raw_scored_mature_1_of_30`
- `fail_closed:production_validation_0_of_30`
- `fail_closed:calibrated_path_prob_absent`
- `fail_closed:path_prob_lower_bound_absent`
- `fail_closed:execution_ready_false`
- `fail_closed:execution_actionable_false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Next

Keep `150654` counted once as a repaired but fail-closed volatility-breakout branch-seed packet. Do not promote it. The next valid profitability-factor continuation needs same-root six-provider AQ/provider acquisition, robust walk-forward survival, enough production-validatable path-ranker rows, calibrated path probability/lower bound, and non-observe execution admission.
