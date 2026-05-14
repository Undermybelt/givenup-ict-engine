# Explicit Historical Tomac Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T004649-codex-board-b-220646-explicit-history-selection-v1`

Board B context: `BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation`

Recipe under test: `TomacNQ_KillzoneBreakout` derived from `SourceRootStopCarryLongHorizonV1` explicit 220646 historical profile.

## Result

This run proves the explicit historical profile can be prepared and can produce a measured Auto-Quant/Freqtrade result after run-local pair, timerange, and precision normalization. It does not prove Board B promotion readiness.

Key evidence:
- Manual external prepare consumed `2,746` rows and wrote `689` 1h bars, `187` 4h bars, and `38` 1d bars.
- Normalized Auto-Quant run exited `0`.
- `TomacNQ_KillzoneBreakout` produced `9` trades, `6` wins, `3` losses, `66.6667%` win rate, `5.28%` total profit, Sharpe `4.1966`, and profit factor `7.3091`.
- Results import exited `0`; the manifest matched `1/1` strategy block in the log.
- Prior-init exited `0` and applied the strategy with `temper=0.25`, `n_win=6`, `n_loss=3`, and `evidence_value_gate_passed=true`.
- Pre-Bayes, policy/path-ranker, structural bundle, execution-candidate, workflow-status, and provider-status readbacks all exited `0`.

## Fail-Closed Decision

Status: `incubation_only_explicit_history_thin_support`.

Promotion remains blocked for these concrete reasons:
- Trade support is thin: `9` trades is below the Board B intraday promotion floor.
- Latest Pre-Bayes gate readback is `blocked` with `pre_bayes_branch_path_gate=blocked_missing_consumed_pre_bayes_filter` on the Sideways branch path.
- Policy/path-ranker validation is callable and ready, but the workflow remains an observe/update lane rather than exact structural-branch promotion.
- Execution-candidate is an `analyze-live` artifact with `review_status=promote_latest`, but the full workflow still records promotion hold and no consumed validation.
- The full workflow status includes `promotion_blocked` and `pre_bayes:blocked_missing_consumed_pre_bayes_filter`.

Provider readback:
- `yfinance` is ready.
- `kraken_cli` is ready.
- `IBKR` gateway is reachable, but provider runtime dependencies are missing.
- `TradingViewRemix` credentials are present but the MCP connectivity probe failed.

## Evidence Files

- `command-output/06_manual_prepare_external_profile.out`
- `command-output/09_auto_quant_run_tomac_profile_normalized.out`
- `measured-explicit-history/strategy_library_explicit_history_tomac_v1.json`
- `command-output/10_auto_quant_results_import_explicit_history.out`
- `command-output/11_auto_quant_prior_init_explicit_history.out`
- `command-output/12_pre_bayes_status_after_explicit_history.out`
- `command-output/13_policy_training_status_after_explicit_history.out`
- `command-output/15_workflow_structural_bundle_after_explicit_history.out`
- `command-output/16_workflow_execution_candidate_after_explicit_history.out`
- `command-output/17_workflow_status_after_explicit_history.out`
- `command-output/18_provider_status_after_explicit_history.out`

## Drift Check

This artifact is additive and does not supersede the active Board B cursor. The cursor had already moved to `20260512T004738+0800-codex-board-b-220646-explicit-historical-rerun-v1` when this readback artifact was written; a later pre-ledger re-read showed it had moved again to `20260512T010454+0800-codex-board-b-220646-real-catboost-explicit-closure-v1`. Keep the real chain order unchanged:

`Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree`

Next safe action for this run is append-only board-ledger writeback only. Do not rewrite the cursor from this `004649` result.
