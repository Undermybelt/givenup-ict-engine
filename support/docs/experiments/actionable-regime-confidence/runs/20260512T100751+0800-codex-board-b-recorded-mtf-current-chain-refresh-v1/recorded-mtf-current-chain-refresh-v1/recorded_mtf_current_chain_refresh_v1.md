# Recorded-MTF Current Chain Refresh v1

Run id: `20260512T100751+0800-codex-board-b-recorded-mtf-current-chain-refresh-v1`

Mode: `incubation_only`

## Scope

This is a copied-state readback for the recorded-MTF `092330` nursery branch. It does not edit the Board B Current Cursor, does not select `HTF` / `MTF` / `LTF`, does not approve source/control evidence, does not mutate the source experiment state, and does not promote a candidate.

Copied state:

- Source: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/state_agent_selected_historical_factor_research_downstream_v1`
- Working copy: `/tmp/ict-engine-20260512T100751+0800-codex-board-b-recorded-mtf-current-chain-refresh-v1-state`

## Commands

All command logs are under `command-output/`; exit codes and SHA-256 evidence are under `checks/`.

Key commands:

- `auto-quant-results-import`: imported `strategy_library_recorded_nq_precision_fixed_v1.json`, `5/5` strategies ok.
- `auto-quant-prior-init --dry-run --force`: applied `RegimeRootPulseBranch`, `RegimeTrendCarry`, and `RegimeVolBreakout` as a BBN prior preview; evidence value gate passed.
- `auto-quant-ingest-real-trades --dry-run --force`: parsed `300/300` `RegimeRootPulseBranch` real-trade rows with `0` invalid rows.
- `pre-bayes-status --refresh`: returned `pass_neutralized` and preserved the read-only BBN label set containing the exact Crisis branch path.
- `policy-training-status`: showed structural path-ranking validation ready with `raw_scored_mature=288/30`, `production_validation=286/30`, and `observation_validation=48/30`.
- `workflow-status --phase structural-recommended-path-bundle` and `--phase execution-candidate`: preserved `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.

## CatBoost Readback

The stale score file from the older candidate set failed correctly:

- `09_apply_structural_path_scores` exited `1`: no refreshed target rows matched the supplied stale scores.
- `14_catboost_apply_refreshed_target` exited `1`: the older CatBoost model expected feature `year_fold`, which is absent from the refreshed target pool.

The corrected path was to train a fresh scratch CatBoost model on the copied state target history and apply it to the refreshed target:

- History target: `295` rows, `288` training samples.
- Feature set available to the trainer: `structural_baseline_score` only.
- New model: `catboost_refreshed_history_model_v1/catboost_model.cbm`.
- New scores: `command-output/20_refreshed_history_catboost_scores.csv`.
- `apply-structural-path-ranking-external-scores` consumed the refreshed scores successfully.
- Post-apply policy status: `score_model_family=catboost`, `score_source=external_model`, `runtime_matches=3`.

This is CatBoost plumbing/readback evidence, not rich feature-learning evidence.

## Provider Readback

Provider-specific status checks were run for the requested provider families:

- `yfinance`: ready in live-runtime and market-data lanes.
- `TradingViewRemix / tradingview_mcp`: not ready; connectivity probe failed.
- `IBKR`: not ready in the default market-data runtime; local gateway is reachable on port `4002`, but runtime dependencies are missing.
- `kraken_public`: not ready due missing Python provider dependencies.
- `kraken_cli`: ready as a local runtime.
- `market-data-harness` yfinance QQQ 1d fetch succeeded.

## Decision

Gate: `incubation_only:recorded_mtf_current_chain_catboost_refreshed_scores_observe_only`.

The exact regime-profit branch path survives Auto-Quant import / dry-run BBN prior / dry-run real-trade ingest / Pre-Bayes / CatBoost path-ranking / execution-candidate. The refreshed CatBoost score raised the path-ranker raw score to `0.9336295132673808`, but execution remains fail-closed:

- `ready=false`
- `review_status=observe`
- `candidate_status=execution_observe_only`
- `execution_readiness=0.4504361163104953`
- `pre_bayes_gate_status=pass_neutralized`
- `recommended_next_step.blocked_reason=user_selected_historical_data_missing`

Promotion allowed: `false`.

`update_goal=false`.

## Next

Do not promote from this readback. The next useful slice is either explicit selected-history/source-control unlock for the recorded branch, or a longer provider-provenanced Auto-Quant input that adds nonzero mature branch observations before repeating the promotion chain.
