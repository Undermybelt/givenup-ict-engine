# Regime Bundle BBN Branch-Path Unit v1

Timestamp: `20260512T052749+0800`

Scope:
- Targeted unit verification for branch-path assignment preservation from regime-consumer bundle diagnostics into the Pre-Bayes filter and BBN evidence packet adapter.
- No historical dataset was selected.
- No Auto-Quant training, canonical merge, CatBoost/path-ranker, workflow, or execution-tree promotion rerun was performed.

Evidence:
- `checks/regime_bundle_bbn_branch_path_unit_v1.out`
- `tests/regime_consumer_bundle_adapter.rs`
- `src/application/regime/consumer_bundle_adapter.rs`

Readback:
- The targeted test `single_branch_path_survives_pre_bayes_into_bbn_assignments` passed.
- The test asserts that `regime_profit_branch_path` survives into `PreBayesFilterState.evidence_assignments`.
- The test also asserts that `belief_evidence_packet_from_pre_bayes_filter` carries the same `regime_profit_branch_path` assignment into the BBN evidence packet path.

Gate:
- `diagnostic_only:regime_bundle_bbn_branch_path_unit`.
- `pass:single_branch_path_survives_pre_bayes_into_bbn_assignments`.
- `blocked:user_selected_historical_data_missing`.
- `promotion_allowed=false`.
- `update_goal=false`.
