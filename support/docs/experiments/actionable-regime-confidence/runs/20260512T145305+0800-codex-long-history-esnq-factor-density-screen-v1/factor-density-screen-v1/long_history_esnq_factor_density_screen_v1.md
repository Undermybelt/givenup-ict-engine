# Long-History ES/NQ Factor-Density Screen v1

Run root: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T145305+0800-codex-long-history-esnq-factor-density-screen-v1`
Source root: `/Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf`

## Scope

- This is a local long-history candidate-surface screen, not a promotion packet.
- It uses cleaned 1h frames derived from the local long-history MTF substrate.
- It does not invoke Auto-Quant provider routing; provider rows are emitted as a fail-closed provenance sidecar.
- It deliberately seeks higher trade density and branch-keyed outcomes before any ordered-chain admission attempt.

## Top Primary ES/NQ Candidate

- Candidate: `TwentyHourBreakoutContinuationV1`
- Trades: `2454`
- Win rate: `0.470253`
- Wilson95 LCB: `0.450567`
- Mean net return: `-0.00016192`
- Return profit factor: `0.963129`
- Density gate: `True`
- Chronological gate: `True`

## Top Primary Branch Leaf

- Branch: `Sideways -> BreakoutContinuation -> TwentyHourRangeExpansion -> TwentyHourBreakoutContinuationV1`
- Symbol: `ES`
- Trades: `243`
- Win rate: `0.485597`
- Wilson95 LCB: `0.423470`
- Mean net return: `0.00089015`
- Return profit factor: `1.722661`
- Positive chronological buckets: `3`

## Gate

- `evidence_class:local_training_candidate_surface_screen`
- `total_candidate_trades:16233`
- `primary_esnq_candidate_trades:11589`
- `primary_positive_branch_leaf_candidates:5`
- `pass:branch_path_fields_emitted`
- `pass:chronological_bucket_summary_emitted`
- `fail_closed:aq_provider_authority_missing_for_this_screen`
- `fail_closed:local_cache_replay_primary_source`
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_chain`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Next

Convert the best density-screened candidate into a portable or provider-routed Auto-Quant recipe, run provider acquisition/provenance for all six required providers, then pass only a provider-provenanced branch packet through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
