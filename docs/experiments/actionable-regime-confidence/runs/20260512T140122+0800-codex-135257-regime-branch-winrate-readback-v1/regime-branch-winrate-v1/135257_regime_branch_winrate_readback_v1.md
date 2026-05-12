# 135257 Regime/Branch Win-Rate Readback v1

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T135257+0800-codex-long-history-es-nq-1m-aq-stage-v1`

## Result

- Trade rows exported: `224`
- Pair count: `2`
- Branch count: `4`
- Promotion allowed: `false`

## Key Readback

- The run reuses the already-registered `135257` isolated Auto-Quant workspace.
- Trade-level rows are now keyed by `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor` using entry-time long-history 1h context derived from the staged 1m substrate.
- This is a screening readback, not a Board B promotion packet: the branch labels are heuristic entry-context labels and have not yet passed Board A Pre-Bayes/BBN/CatBoost/execution-tree admission.

## Gates

- `support_once:135257_regime_branch_winrate_readback_v1`
- `evidence_class:market_factor_screening_sample_not_promotion`
- `pass:trade_rows_exported_224`
- `pass:branch_paths_populated_224`
- `pass:branch_summary_rows_7`
- `pass:chronological_bucket_summary_written`
- `fail_closed:heuristic_entry_regime_not_board_a_accepted_regime`
- `fail_closed:not_yet_pre_bayes_bbn_catboost_execution_tree`
- `fail_closed:not_yet_provider_context_matrix_validated`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
