# Provider-Linked Momentum Downstream Corrected v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T110913+0800-codex-105637-provider-linked-momentum-downstream-corrected-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T105637+0800-codex-provider-linked-aq-provenance-probe-v1`

## Scope

This is the corrected downstream readback for the nonzero public-provider momentum trades emitted by `105637`.

The earlier `110627` downstream attempt failed because the derived real-trades JSONL was missing while the `105637` workspace was still settling. This corrected run builds the combined JSONL first, then runs the ordered ict-engine downstream surfaces in an isolated state directory.

## Source Trades

- Symbol: `B2R_PROVIDER_LINKED_MOMENTUM_105637`
- Providers included: `yfinance`, `kraken_public_ccxt`, `binance_public_ccxt`, `bybit_public_ccxt`
- Records: `7`
- Wins: `3`
- Losses: `4`
- Total PnL: `-200.6922557`
- Branch path: `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1`

## Command Readback

All corrected downstream commands exited `0`:

- `auto-quant-ingest-real-trades --dry-run`
- `auto-quant-ingest-real-trades --force`
- `pre-bayes-status --refresh`
- `policy-training-status`
- `export-structural-path-ranking-target`
- `workflow-status --phase structural-recommended-path-bundle`
- `workflow-status --phase execution-candidate`
- `workflow-status --refresh`

Forced ingest applied `7/7` rows with `0` invalid rows and inserted `7` feedback records.

## Downstream Result

- Pre-Bayes remained empty: no latest policy, bridge, soft evidence, filtered assignments, canonical structural regime, or gate status.
- Entry models remained not ready with `matched_rows=0`.
- Structural target export produced `rows=1`, `history_rows=1`, `mature_rows=0`, and `history_mature_rows=0`.
- The structural target stayed `bootstrap_readiness`; the source branch path did not mature into a structural/CatBoost candidate.
- Execution candidate stayed `actionable=false`, `ready=false`, `review_status=observe`, and `execution_gate_status=execution_candidate_observed`.
- Full workflow returned `closed_loop_branch_admission.status=fail_closed` with blocking truth `insufficient_state`.

## Gate

- `count_once:110913_105637_provider_linked_momentum_downstream_corrected`.
- `context_source:105637_provider_linked_aq_provenance_probe`.
- `supersedes_failed_attempt:110627_105637_provider_linked_downstream_failure_for_ingest_only`.
- `pass:combined_provider_linked_real_trades_rows_7`.
- `pass:dry_run_ingest_exit0`.
- `pass:force_ingest_exit0`.
- `pass:auto_quant_ingest_real_trades_applied_7_7`.
- `pass:pre_bayes_policy_catboost_workflow_commands_exit0`.
- `fail_closed:source_provider_aq_total_pnl_negative`.
- `fail_closed:tradingviewremix_still_failed_in_source_provider_packet`.
- `fail_closed:ibkr_not_btc_aq_feed_in_source_provider_packet`.
- `fail_closed:pre_bayes_policy_absent`.
- `fail_closed:entry_model_matched_rows_0`.
- `fail_closed:structural_target_mature_rows_0`.
- `fail_closed:structural_target_branch_path_not_preserved`.
- `fail_closed:execution_tree_bootstrap_observe`.
- `fail_closed:closed_loop_branch_admission_fail_closed`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Decision

This run corrects the `110627` ingest failure and proves the provider-linked momentum rows can enter the ordered downstream chain, but it is still a fail-closed diagnostic. It does not satisfy the six-provider authority gate, does not produce mature structural/CatBoost rows, and does not promote a trade.
