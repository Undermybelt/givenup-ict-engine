# 105014 Ingest Bridge Fix v1

## Scope

This run replays the `105014` BTC-only pullback real-trade ingest after the
`auto-quant-ingest-real-trades` shell wrapper fix. It uses the same filtered
source trades from `20260512T105014+0800-codex-104610-btc-pullback-downstream-readback-v1`.

## Code Change Under Test

- `src/auto_quant_command.rs`: `auto_quant_ingest_real_trades_shell` now writes
  real-trade posterior feedback into the requested `--state-dir` instead of
  rewriting it to `<state-dir>/auto-quant`.
- Regression test:
  `cargo test auto_quant_ingest_real_trades_shell_feeds_requested_downstream_state_dir --bin ict-engine -- --nocapture`.

## Evidence

- Build: `cargo build --bin ict-engine` exited `0`.
- All replay commands `01` through `09` exited `0`; see `checks/`.
- Real-trade ingest applied `146/146` rows with `0` invalid rows.
- The requested downstream state now contains:
  - `state_ingest_bridge_fix_v1/B2R_YAHOO_CRYPTO_BTC_PULLBACK_104610/bbn_network.json`
  - `state_ingest_bridge_fix_v1/B2R_YAHOO_CRYPTO_BTC_PULLBACK_104610/learning_state.json`
- `learning_state.feedback_history=146`, and all `146` rows carry structural
  feedback for:
  `Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1`.

## Readback

- Structural target export now has `rows=2`, `mature_rows=1`, `history_rows=2`,
  and `history_mature_rows=1`.
- Rank 1 structural target row preserves:
  - `regime_profit_branch_path=Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1`
  - `main_regime=Range`
  - `sub_regime=ProviderCryptoPullback`
  - `sub_sub_regime_or_profit_factor=MeanRevertBounce`
  - `profit_factor=ProviderCryptoPullbackRevertV1`
- Structural bundle selects the exact branch with `historical_total_records=146`,
  `selected_path_probability=0.7508532423208192`, and
  `current_posterior=0.4520547945205479`.
- Execution candidate preserves the exact branch but remains
  `ready=false`, `actionable=false`, `candidate_status=execution_candidate_observed`.
- Full workflow keeps `closed_loop_branch_admission.status=fail_closed` with
  reason `exact_structural_branch_visible_but_not_ready_or_actionable`.

## Remaining Blockers

- `pre-bayes-status --refresh` still has no latest policy, bridge, soft evidence,
  canonical structural regime, or gate status.
- CatBoost/path-ranker is not promotion-ready:
  - `raw_scored_mature=0/30`
  - `production_validation=0/30`
  - `trainer_artifact=missing`
  - `runtime_selection=disabled`
- Observation validation is now visible and ready at `146/30`, but that is not a
  substitute for CatBoost/path-ranker production validation.
- This does not satisfy selected-history, source/control, or six-provider
  authority gates.

## Decision

The ingest bridge bug is fixed and branch identity now survives the normal
`--state-dir` downstream path. This run is not a promotion packet.
