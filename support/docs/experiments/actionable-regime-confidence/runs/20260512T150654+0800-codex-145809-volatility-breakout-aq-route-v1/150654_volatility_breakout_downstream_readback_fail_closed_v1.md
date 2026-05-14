# 150654 Volatility Breakout Downstream Readback Fail-Closed v1

Run root:
`docs/experiments/actionable-regime-confidence/runs/20260512T150654+0800-codex-145809-volatility-breakout-aq-route-v1`

Source:
- Upstream source root: `20260512T145809+0800-codex-provider-backed-high-density-factor-screen-v1`.
- Candidate branch: `trend_expansion->high_volatility->up_momentum->volatility_breakout_follow`.
- Candidate strategy: `volatility_breakout_follow_v1`.
- Symbol used for downstream state: `B2R_VOL_BREAKOUT_150654`.

Command exits:
- `01_build_volatility_breakout_packet.exit=0`
- `02_auto_quant_results_import.exit=1`
- `03_auto_quant_prior_init.exit=1`
- `04_auto_quant_ingest_real_trades.exit=0`
- `05_pre_bayes_status.exit=0`
- `06_policy_training_status_before_export.exit=0`
- `07_export_structural_path_target.exit=0`
- `08_policy_training_status_after_export.exit=0`
- `09_train_catboost_history.exit=0`
- `10_apply_catboost_current_target.exit=0`
- `11_apply_external_scores.exit=0`
- `12_register_catboost_trainer_artifact.exit=0`
- `13_enable_path_ranker_runtime.exit=0`
- `14_policy_training_status_after_runtime.exit=0`
- `15_workflow_structural_bundle.exit=0`
- `16_workflow_execution_candidate.exit=0`
- `17_workflow_full.exit=0`

Readback:
- Packet summary preserved `348` real-trade rows with aggregate win rate `0.5229885057471264`, profit factor `1.3270317756098415`, average return `0.0024524889854152443`, and total return units `0.853466166924505`.
- Walk-forward passed only `2/10` folds: `2020` and `2024`. All other yearly folds were fail-closed.
- Provider provenance had six provider rows, but only `IBKR`, `yfinance/YF`, and `Binance` were requested/acquired for this branch seed. `TradingViewRemix/TVR`, `Kraken`, and `Bybit` were absent for the branch.
- `auto_quant_results_import` and `auto_quant_prior_init` both failed because `strategy_library_volatility_breakout_v1.json` did not parse: invalid type `"not_auto_quant_native_backtest"` where a structured validation error was expected.
- `pre-bayes-status` exited `0`, but canonical structural regime, canonical confidence, probabilities, gate status, and filtered assignments were absent/null.
- Policy training after runtime had `analyze_runs=0`; entry models had `matched_rows=0` and `ready=false`.
- Structural path-ranker target had `history_rows=350`, `history_mature_rows=349`, and `observation_validation=348/30`, but current target validation remained insufficient: `raw_scored_mature=1/30`, `production_validation=0/30`, `calibration=not_fitted`.
- CatBoost trainer artifact was present and runtime selection was enabled in candidate-set mode, with `score_model_family=catboost`, `score_source=external_model`, and `runtime_matches=2`, but `path_ranker_calibrated_path_prob` and `path_ranker_path_prob_lower_bound` remained null.
- Execution candidate was `ready=false`, `actionable=false`, `review_status=observe`, `selected_path_probability=0.6644427013798627`, `path_ranker_raw_score=0.6918494098764735`, and `execution_gate_status=execution_candidate_observed`.
- Full workflow readback returned `blocking_truth.status=insufficient_state` and no latest analyze/execution candidate snapshot.

Acceptance decision:
- This root demonstrates partial downstream plumbing for a volatility-breakout branch, including real-trade observation history and CatBoost candidate-set score exposure.
- It does not satisfy Board A because the AQ result import/prior initialization failed, same-root six-provider branch acquisition failed, Pre-Bayes canonical state was absent, path-ranker calibration/lower bound was absent, and execution-tree admission stayed non-actionable.
- Board A remains fail-closed: accepted `>=95%` contexts `0`, `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.
