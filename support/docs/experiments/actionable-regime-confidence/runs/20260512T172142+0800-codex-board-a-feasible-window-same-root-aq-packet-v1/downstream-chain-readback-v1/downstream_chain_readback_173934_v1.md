# Downstream Chain Readback 173934 v1

Source packet: `172142_feasible_window_same_root_aq_packet`.
State dir: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1/state_downstream_v1`.
Strategy library: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1/provider_btc_172142_strategy_library_v1.json`.
Candles: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1/data/cleaned/btc_usd_1h_yfinance_candles.json`.

## Command Exits
- `00_build_downstream_inputs` exit `0`.
- `01_auto_quant_results_import` exit `0`.
- `02_auto_quant_prior_init` exit `0`.
- `03_analyze` exit `0`.
- `04_pre_bayes_status` exit `0`.
- `05_policy_training_status` exit `0`.
- `06_workflow_status` exit `0`.
- `07_workflow_execution_candidate` exit `0`.
- `08_export_structural_path_ranking_target` exit `0`.
- `09_catboost_path_ranker_train` exit `0`.
- `10_catboost_path_ranker_apply` exit `0`.
- `11_register_structural_path_ranking_trainer_artifact` exit `0`.
- `12_apply_structural_path_ranking_external_scores` exit `0`.
- `13_enable_structural_path_ranking_runtime` exit `0`.
- `14_policy_training_status_after_catboost` exit `0`.
- `15_workflow_status_after_catboost` exit `0`.
- `16_workflow_execution_candidate_after_catboost` exit `0`.

## Path-Ranker Readback
- Target CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1/state_downstream_v1/BTCUSD/policy_training/structural_path_ranking_target_history.csv`.
- Target rows: `3`.
- Scores CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1/path-ranker/downstream-v1-catboost-scores.csv`.
- Scores rows: `3`.
- Score families: `catboost`.
- Trainer model family: `catboost`.
- Trainer rows: `3`.
- Calibration rows: `3`.
- Mature min30 ready: `False`.

## Gate
- Gate result: `downstream_chain_ran_catboost_registered_fail_closed_maturity_below_30`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Supplemental Terminal Verification 183919 v1

This supplemental verification closes the later `downstream-173934` command chain that carried the already-terminal `172142` provider/AQ packet into a BTC run-local downstream state. It does not rerun provider fetches, does not rerun Auto-Quant/TOMAC, does not count duplicate sibling packets, does not edit runtime code or production state, and does not claim Board A acceptance.

Command-output root: `docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1/command-output/downstream-173934/`.
Check root: `docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1/checks/downstream-173934/`.
State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1/state_downstream_v1`.

Prompt-to-artifact checklist:

| Requirement | Evidence | Status |
|---|---|---|
| Use one controlling provider/AQ packet | Source packet remains `172142_feasible_window_same_root_aq_packet`; sibling `172214` and `172448` were duplicate-suppressed in the board. | pass |
| Six provider provenance | `172142` terminal readback records YF, Kraken, Binance, Bybit, TVR local-stdio, and IBKR rows in one root. | pass |
| Auto-Quant/TOMAC evidence | `172142` terminal readback records `6/6` AQ compile exits, `6/6` TOMAC exits, `12` metric sets, and `1953` AQ metric trades. | pass |
| Build downstream inputs | `00_build_downstream_inputs.exit=0`; candles and strategy library regenerated under the run root. | pass |
| Auto-Quant import | `02_auto_quant_results_import.exit=0`. | pass |
| BBN prior/init and network | `03_auto_quant_prior_init.exit=0`; `state_downstream_v1/BTC/bbn_network.json` exists and is non-empty (`45586` bytes). | pass |
| Real trade feedback ingest | `04_auto_quant_ingest_real_trades.exit=0`; `trades_total=1953`, `trades_applied=1953`, `trades_invalid=0`, `feedback_records_inserted=1953`. | pass |
| Analyze/filter/Pre-Bayes | `05_analyze_same_1h_triplet.exit=0`, `06_pre_bayes_status_refresh.exit=0`; latest gate is `pass_neutralized`. | partial |
| CatBoost/path-ranker | `12_path_ranker_catboost_integration.exit=0`, `13_apply_structural_path_scores.exit=0`; `catboost_model.cbm` exists and is non-empty (`14424` bytes); scores CSV has `3` rows. | partial |
| Execution tree/workflow readback | `16_workflow_execution_candidate_after_catboost.exit=0`, `17_workflow_structural_bundle_after_catboost.exit=0`; execution candidate remains blocked. | fail-closed |
| 95%-99% calibrated regime confidence | Pre-Bayes canonical structural confidence is `0.523311097658614`; structural bundle posterior is `0.24532535527299926`; selected path probability is `0.2959422708992021`; no `>=0.95` acceptance exists. | fail-closed |
| Cross-market/timeframe acceptance | This downstream chain used the `172142` provider/AQ packet and same 1h BTC downstream data; it did not validate every root regime across other markets/timeframes. | fail-closed |

Readback:
- All `downstream-173934` command exits are `0`: build inputs, real-trade combine, Auto-Quant results import, prior init, real-trades ingest, analyze, Pre-Bayes refresh, policy-training status before/after, structural target export, workflow refresh, execution-candidate readback, structural-bundle readback, CatBoost integration, external score apply, and post-CatBoost workflow readbacks.
- Combined real trades: `1953` JSONL rows in `provider_btc_172142_real_trades_v1.jsonl`.
- Real-trades ingest was not a dry run: `ledger_status=applied`, `trades_applied=1953`, `feedback_records_inserted=1953`, `content_hash=d56f172efc2f8c42`.
- Pre-Bayes/filter result is not acceptance: `latest_gate_status=pass_neutralized`, canonical structural active regime `range`, canonical structural confidence `0.523311097658614`, structural probabilities `range=0.7471918003808868`, `stress=0.1780890195810245`, `transition=0.07471918003808868`, `trend=0.0`.
- Structural path-ranker runtime is wired but immature: target rows `3`, mature rows `2`, production validation rows `2`, production validation ready `false`, observation validation rows `1953`, trainer artifact status `present_validation_insufficient`.
- Path-ranker scores were applied from CatBoost/external model for `3` candidate paths. The top path is `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1` with raw score `0.7216652561948258`, calibrated path probability `0.75`, and lower bound `0.4324153656109918`.
- Execution tree does not admit action: `actionable=false`, `candidate_status=execution_blocked`, `execution_gate_status=execution_blocked`, `selected_path_probability=0.2959422708992021`, current posterior `0.24532535527299926`.

Gate:
- `active_claim_closed:173934_172142_downstream_chain_readback_v1`.
- `step_done:172142_provider_aq_packet_downstream_chain_executed`.
- `pass:downstream_command_exits_18_of_18_zero`.
- `pass:real_trades_ingested_1953_of_1953_invalid_0`.
- `pass:bbn_network_present_non_empty`.
- `partial:pre_bayes_filter_pass_neutralized_only`.
- `partial:catboost_path_ranker_runtime_wired_candidate_set_only`.
- `partial:observation_validation_1953_of_30`.
- `fail_closed:production_validation_2_of_30`.
- `fail_closed:path_ranker_mature_rows_2_of_30`.
- `fail_closed:execution_tree_execution_blocked`.
- `fail_closed:no_calibrated_95_regime_acceptance`.
- `fail_closed:no_cross_market_timeframe_acceptance`.
- `accepted_95_contexts_added_0`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

Next:
- Do not rerun `172142`, `172214`, or `172448` as another provider/AQ proof packet. The next non-duplicate Board A movement should either obtain more mature structural/reward rows for the same root path or open a new, explicitly different cross-market/timeframe validation slice that still keeps the six-provider AQ provenance matrix and runs the full downstream chain before any 95% acceptance claim.
