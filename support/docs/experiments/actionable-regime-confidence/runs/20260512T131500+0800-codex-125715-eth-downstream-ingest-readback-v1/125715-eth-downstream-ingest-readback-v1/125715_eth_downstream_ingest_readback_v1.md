# 125715 ETH Downstream Ingest Readback v1

Run id: `20260512T131500+0800-codex-125715-eth-downstream-ingest-readback-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T125715+0800-codex-six-provider-eth-same-root-aq-v1`

Gate result: `125715_eth_downstream_ingest_readback_v1=six_provider_eth_aq_branch_path_ingested_path_ranker_ready_execution_fail_closed`

## Scope

This readback carries the positive six-provider ETH AQ momentum branch from `125715` through the local downstream chain in an isolated state dir.

- Strategy: `ProviderCryptoMomentumStateV1`.
- Branch path: `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1`.
- Provider rows: yfinance, Kraken, Binance, Bybit, TradingViewRemix/TVR, and IBKR PAXOS AGGTRADES were all present in the source root.
- Source AQ/TOMAC runs: `6/6` compile and run exits were `0`.
- This run does not mutate repo runtime code, production BBN CPDs, production CatBoost artifacts, execution-tree gates, or the board cursor.

## Command Evidence

All recorded commands exited `0`:

- `00_build_momentum_trades`: built one provider-provenanced JSONL with `162` momentum trades.
- `01_ingest_real_trades_dry_run`.
- `02_ingest_real_trades_force`.
- `03_pre_bayes_status`.
- `04_policy_training_status`.
- `05_export_structural_path_ranking_target`.
- `06_workflow_structural_bundle`.
- `07_workflow_execution_candidate`.
- `08_workflow_full`.
- `09_policy_training_status_after_export`.
- `10_train_catboost`.
- `11_apply_catboost_history`.
- `12_apply_external_scores`.
- `13_register_trainer_artifact`.
- `14_enable_runtime`.
- `15_policy_training_status_after_runtime`.
- `16_workflow_structural_bundle_after_runtime`.
- `17_workflow_execution_candidate_after_runtime`.
- `18_workflow_full_after_runtime`.
- `19_pre_bayes_status_after_runtime`.

## Readback

- `auto-quant-ingest-real-trades --force` applied `162/162` rows with `0` invalid rows.
- The source branch path survived into the downstream structural branch: `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1`.
- Pre-Bayes stayed empty: latest policy, soft evidence, bridge, filtered assignments, canonical structural posterior, and gate status were all `null`.
- Before CatBoost, path-ranker validation was not production-ready: `raw_scored_mature=0/30`, `production_validation=0/30`, `observation_validation=162/30`.
- CatBoost/path-ranker training, score application, trainer registration, and runtime enablement all succeeded.
- After runtime enablement, path-ranker validation became ready: `raw_scored_mature=163/30`, `production_validation=162/30`, `observation_validation=162/30`, `runtime_selection=enabled_candidate_set_ready`, `runtime_matches=2`, `score_model_family=catboost`, `score_source=external_model`.
- Execution remained fail-closed: `closed_loop_branch_admission.status=fail_closed`, `ready=false`, `actionable=false`, `review_status=observe`, `execution_gate_status=execution_candidate_observed`, reason `exact_structural_branch_visible_but_not_ready_or_actionable`.

## Decision

- This is materially stronger than the earlier `125500` support root because all six ETH provider lanes are first-class AQ inputs and the positive momentum branch reaches CatBoost/path-ranker runtime readiness.
- It is still not production promotion evidence. Pre-Bayes/filter and BBN did not produce a non-empty posterior/gate, and execution tree stayed observe/not ready.
- Evidence class: `chain_contract_negative_sample`.
- Market/factor learning quality weight: `0`.
- Provider/readiness/contract learning quality: useful.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts

- Source six-provider report: `docs/experiments/actionable-regime-confidence/runs/20260512T125715+0800-codex-six-provider-eth-same-root-aq-v1/six-provider-eth-same-root-aq-v1/six_provider_eth_same_root_aq_v1.md`.
- Derived momentum trades: `derived/125715_eth_six_provider_momentum_trades.jsonl`.
- Ingest readback: `command-output/02_ingest_real_trades_force.out`.
- Pre-Bayes readback: `command-output/19_pre_bayes_status_after_runtime.out`.
- Path-ranker runtime readback: `command-output/15_policy_training_status_after_runtime.out`.
- Execution readback: `command-output/18_workflow_full_after_runtime.out`.
- Assertions: `checks/125715_eth_downstream_ingest_readback_v1_assertions.out`.
