# 093854 Local Cache Seed v2 Auto-Quant Readback

Run root: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2`

## Commands

- Compile: `command-output/03_strategy_py_compile.cmd`, exit `0`.
- Official AQ oracle without resolver shim: `command-output/05_auto_quant_run.cmd`, exit `1`; blocker was aiohttp/aiodns DNS failure while loading Binance `exchangeInfo`.
- Same AQ oracle with threaded DNS shim: `command-output/06_auto_quant_run_threaded_dns.cmd`, exit `0`; `Done: 8 backtests succeeded, 0 failed.`

## Metrics

| Strategy | Full-window trades | Full win rate | Full profit | Full Sharpe | Robust Sharpe | Worst Profit | Profit Floor | Branch Rooted |
|---|---:|---:|---:|---:|---:|---:|---|---|
| BNBMeanRevertSharp | 125 | 70.4000% | 16.2500% | 0.1848 | 0.0870 | 2.8000% | FAIL | no |
| CrashReboundVolume | 208 | 69.2308% | 38.0100% | 0.2802 | -0.0018 | -0.0500% | FAIL | no |

## Gate

- `pass:local_cache_seed_moved_auto_quant_status_to_dependency_ready_data_ready`.
- `pass:threaded_dns_shim_retired_aiodns_binance_market_metadata_failure`.
- `pass:auto_quant_run_py_real_backtests_nonzero_trades`.
- `pass:ict_engine_auto_quant_results_import_n_ok_2`.
- `pass:bbn_prior_init_dry_run_evidence_value_gate_passed`.
- `fail_closed:profit_floor_failed_for_both_seed_strategies`.
- `fail_closed:crypto_local_cache_seed_not_board_b_branch_rooted`.
- `fail_closed:no_mature_rooted_board_b_branch_observations`.
- `fail_closed:bbn_prior_init_was_dry_run_only`.
- `fail_closed:no_catboost_path_ranking_or_execution_tree_promotion`.
- `promotion_allowed=false`.
- `update_goal=false`.

## ict-engine Registration

- `auto-quant-results-import` exited `0`: `n_ok=2`, `n_error=0`, library artifact `auto_quant_strategy_library_SRC_ROOT_CARRY_LONG_220646_20260512T022923.980165000Z`.
- `auto-quant-prior-init --dry-run` exited `0`: `evidence_value_gate_passed=true`, final dry-run probabilities `[0.6934000690615427, 0.00000004901141743247006, 0.3065998819270398]`.
- The dry-run applied the two full-window trade counts as BBN evidence (`125` BNB, `208` crash-rebound), but this is deliberately not persisted to the trading network because the evidence is crypto local-cache research and does not preserve the Board B rooted branch path.

## Next

Do not promote from this packet. Use it as an infrastructure retirement: local/provider-cache seeding plus a threaded DNS shim can make the isolated Auto-Quant workspace runnable. The next admissible Board B step still needs provider-provenanced or explicitly selected-history data that maps into `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor` before downstream promotion.
