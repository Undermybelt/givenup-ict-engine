# Provider BTC Precision Fix AQ v1

Run id: `20260512T103240+0800-codex-board-b-provider-btc-precision-fix-aq-v1`

Gate result: `provider_btc_precision_fix_aq_v1=nonzero_provider_owned_tomac_branch_fail_closed`

## Root Cause

The previous provider BTC TOMAC nursery had nonzero entry signals but zero trades because the run-local synthetic market metadata used decimal-style precision under a tick-size exchange runtime. `precision.amount = 8` rounded a BTC order amount near `0.147` down to `0.0`, so Freqtrade discarded the entries before opening trades.

This run copied the `101623` isolated Auto-Quant workspace and changed only the run-local synthetic market metadata to tick sizes: `amount=0.00000001`, `price=0.01`.

## Auto-Quant / TOMAC Readback

- Provider CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1/provider-csv/binance_btcusdt_1h.csv`.
- Provider rows: `985` BTC/USDT 1h rows from `2026-04-01 00:00:00+00:00` to `2026-05-12 00:00:00+00:00`.
- Corrected TOMAC run exited `0`.
- Branch-metadata TOMAC run exited `0` with `4` strategies succeeded and `0` failed.
- Best branch-preserving strategy: `SourceRootStopCarryProviderBtcCross`.
- Exact branch metadata: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:provider_btc_precision_fix_cross_v1`.
- Metrics: `9` trades, `55.5556%` win rate, `+2.14%` total profit, `1.7770` profit factor, `1.2260` Sharpe, `-1.6264%` max drawdown.

## Downstream Readback

The prior branch-preserving state from `100751` was copied to `/tmp/ict-engine-20260512T103240+0800-provider-btc-precision-fix-state` before import/readback.

- `auto-quant-results-import` exited `0`: `1/1` strategy imported, `n_meta_invalid=0`.
- `auto-quant-prior-init --dry-run --force` exited `0`: `SourceRootStopCarryProviderBtcCross` applied as BBN prior preview with `trade_count=9`, `n_win=5`, `n_loss=4`, and `evidence_value_gate_passed=true`.
- `pre-bayes-status --refresh` exited `0` and stayed `latest_gate_status=pass_neutralized`.
- `policy-training-status` exited `0`.
- `workflow-status --phase structural-recommended-path-bundle` exited `0`.
- `workflow-status --phase execution-candidate` exited `0` and preserved exact execution path `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.
- Execution stayed non-promoting: `candidate_status=execution_observe_only`, `ready=false`, `review_status=observe`, `execution_readiness=0.4504361163104953`.

## Decision

- The zero-trade provider BTC blocker is retired for this artifact workspace.
- This adds a real provider-owned, nonzero, profitable TOMAC branch observation.
- It is still too thin to promote: `9` trades is below the user’s family-level evidence threshold.
- The BBN readback was a dry-run prior preview, not an applied promotion.
- CatBoost/path-ranker was not retrained from provider BTC trades; execution tree continued to use the copied history path-ranker score.
- No selected-history approval, source/control unlock, canonical merge, selected-data promotion, or trade-usable evidence was produced.
- Promotion allowed: `false`.
- `update_goal=false`.

## Artifacts

- Strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T103240+0800-codex-board-b-provider-btc-precision-fix-aq-v1/provider-btc-precision-fix-aq-v1/strategy_library_provider_btc_precision_fix_v1.json`
- Corrected TOMAC stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T103240+0800-codex-board-b-provider-btc-precision-fix-aq-v1/command-output/02_run_provider_btc_branch_metadata_precision_fix.out`
- Import stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T103240+0800-codex-board-b-provider-btc-precision-fix-aq-v1/command-output/03_auto_quant_results_import.out`
- BBN prior dry-run stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T103240+0800-codex-board-b-provider-btc-precision-fix-aq-v1/command-output/04_auto_quant_prior_init_dry_run.out`
- Execution-candidate stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T103240+0800-codex-board-b-provider-btc-precision-fix-aq-v1/command-output/08_workflow_execution_candidate_agent.out`

## Next

Do not rerun this exact one-month BTC cross as promotion evidence. The next useful provider-owned direction is a longer provider-provenanced BTC/NQ slice or a denser branch-preserving strategy that reaches at least family-level trade count before CatBoost/path-ranker retraining and execution-tree promotion are attempted.
