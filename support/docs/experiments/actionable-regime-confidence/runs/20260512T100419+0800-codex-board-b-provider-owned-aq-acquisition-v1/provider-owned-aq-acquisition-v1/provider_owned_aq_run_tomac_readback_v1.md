# Provider-Owned AQ RunTOMAC Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1`

Mode: `incubation_only`

## Scope

This readback follows the provider-owned AQ prepare step. It consumes the already prepared isolated Auto-Quant workspace and records the actual `run_tomac.py` result. It does not edit Current Cursor, does not run selected-data promotion, does not advance Pre-Bayes/BBN/CatBoost/execution-tree promotion, and does not call `update_goal`.

## Commands

- `10_auto_quant_prepare_provider_yf`: exit `0`
- `11_auto_quant_status_after_prepare`: exit `0`
- `14_auto_quant_run_tomac_provider_yf_workspace`: exit `1`

## Prepared State

`auto-quant-status` after prepare:

- status: `dependency_ready_data_ready`
- healthy: `true`
- dependency healthy: `true`
- data ready: `true`

Prepared data files exist:

- `B2R_NQ_PROVIDER_100419_USD-1h.feather`
- `B2R_NQ_PROVIDER_100419_USD-4h.feather`
- `B2R_NQ_PROVIDER_100419_USD-1d.feather`

Strategy file exists:

- `user_data/strategies_external/TomacNQ_KillzoneBreakout.py`

## RunTOMAC Result

The provider-preseeded Auto-Quant run exited `1`:

- strategy: `TomacNQ_KillzoneBreakout`
- commit: `34ba6b6`
- status: `ERROR`
- error type: `OperationalException`
- error message: `No pair in whitelist.`
- successful backtests: `0`
- failed backtests: `1`

The run did not produce trade rows, branch-conditioned return rows, or a strategy library handoff.

## Root Cause

The data files were present, so this is not the previous provider-data absence blocker.

The active TOMAC config whitelist is:

`B2R_NQ_PROVIDER_100419/USD`

The prepared data files use the matching Freqtrade filename stem:

`B2R_NQ_PROVIDER_100419_USD-{1h,4h,1d}.feather`

The failure is the same class as earlier synthetic pair issues: the run-local Freqtrade pairlist rejects the underscore-bearing synthetic pair string before backtest measurement.

## Gate

- `pass:provider_owned_yahoo_nq_preseeded_into_autoquant`
- `pass:auto_quant_status_dependency_ready_data_ready`
- `fail_closed:run_tomac_no_pair_in_whitelist`
- `fail_closed:underscore_synthetic_pair_rejected_before_measurement`
- `fail_closed:no_successful_provider_preseeded_backtest`
- `fail_closed:no_nonzero_mature_rooted_branch_observations`
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_promotion_rerun`
- `promotion_allowed=false`
- `update_goal=false`

## Next

Do not rerun the same provider-preseeded TOMAC command unchanged. The next useful action is a run-local pair-alias/sanitizer repair that maps this provider-owned NQ data into a Freqtrade-compatible pair, for example by using an alias like `NQ/USD` with matching `NQ_USD-{1h,4h,1d}.feather` files. Only after that repaired run emits nonzero mature rooted branch observations should the workflow advance through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
