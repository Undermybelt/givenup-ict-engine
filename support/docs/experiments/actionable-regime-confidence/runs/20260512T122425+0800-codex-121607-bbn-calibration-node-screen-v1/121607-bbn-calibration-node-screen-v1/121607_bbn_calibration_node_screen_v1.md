# 121607 BBN Calibration Node Screen v1

Run id: `20260512T122425+0800-codex-121607-bbn-calibration-node-screen-v1`

## Inputs
- Enriched rows: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/derived/same_root_six_provider_1h_aq_real_trades.enriched_layer_contract.jsonl`
- Feedback packet: `docs/experiments/actionable-regime-confidence/runs/20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1/120630-bbn-negative-feedback-packet-v1/120630_bbn_negative_feedback_packet_v1.json`
- Gap map: `docs/experiments/actionable-regime-confidence/runs/20260512T121701+0800-codex-120630-regime-confidence-gap-map-v1/120630-regime-confidence-gap-map-v1/120630_regime_confidence_gap_map_v1.json`

## Result
- Rows screened: `237` across `6` providers and `2` branch paths.
- Active regime remained `range` confidence `0.5250864595751618`; gap to `0.95` was `0.20231228233180432`.
- Existing feedback context: `entry_quality=medium,factor_alignment=mixed,factor_uncertainty=low` with empirical outcome `{'probs': [0.341772, 0.0, 0.658228], 'rows': 237, 'states': ['win', 'breakeven', 'loss']}`.
- Accepted candidate BBN nodes: `0`.
- Gate: `121607_bbn_calibration_node_screen_v1=no_admissible_bbn_node_no_promotion`.

## Screened Nodes
- `source_provider`: best state `yfinance` rows `21` win_rate `0.47619`; accepted `False`; reject `best_provider_win_rate_below_0_95; single_symbol_single_timeframe_only; provider_outcomes_do_not_lift_regime_confidence`.
- `branch_path`: best state `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1` rows `164` win_rate `0.384146`; accepted `False`; reject `best_branch_win_rate_below_0_95; active_bbn_regime_constant_range; branch_label_is_not_independent_regime_state_evidence`.
- `source_provider_x_branch_path`: best state `yfinance | Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1` rows `13` win_rate `0.538462`; accepted `False`; reject `best_group_rows_below_30; best_group_not_cross_provider_stable; best_group_win_rate_below_0_95`.
- `chronological_quartile`: best state `Q1` rows `60` win_rate `0.5`; accepted `False`; reject `chronological_outcomes_unstable; worst_quartile_collapse; does_not_supply_cross_period_regime_lift`.
- `factor_weighted_score_sign`: best state `positive_score` rows `81` win_rate `1.0`; accepted `False`; reject `post_trade_pnl_label_leakage; weighted_score_equals_realized_pnl_for_all_rows; not_admissible_as_pre_trade_bbn_node`.
- `pre_bayes_canonical_regime`: best state `range` rows `237` win_rate `0.341772`; accepted `False`; reject `constant_state_range; pre_bayes_gate_pass_neutralized; no_cross_regime_separator_in_current_packet`.
- `execution_status_tuple`: best state `('execution_blocked', 'observe', False, False)` rows `237` win_rate `0.341772`; accepted `False`; reject `constant_fail_closed_execution_status; ready_false_actionable_false_review_observe; cannot_promote_without_execution_admissibility`.

## Leakage Guard
- `factor_weighted_score_sign` looked perfect, but `weighted_score == realized pnl` for `237/237` rows.
- This is rejected as post-trade label leakage and must not be used as a pre-trade BBN evidence node.

## Decision
- No screened node is admissible for production BBN likelihood mutation from this packet.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next Evidence Needs
- pre_trade provider/context features independent of realized pnl
- cross-provider and cross-period validation before CPD mutation
- non-constant pre-bayes regime evidence across trend/range/stress/transition
- execution admissibility evidence resolving ready=false/actionable=false/observe
