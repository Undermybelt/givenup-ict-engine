# 104610 BTC Pullback Downstream Readback v1

Run id: `20260512T105014+0800-codex-104610-btc-pullback-downstream-readback-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T104610+0800-codex-board-b-yahoo-crypto-precision-fix-aq-v1`

Gate result: `104610_btc_pullback_downstream_readback_v1=btc_positive_noncanary_branch_ingested_bbn_written_but_branch_path_not_promotable_downstream`

## Scope

This readback filters the `104610` provider-owned Yahoo crypto precision-fix run to the only positive non-canary sub-slice:

- Strategy: `ProviderCryptoPullbackRevertV1`.
- Pair slice: `BTC/USDT` only.
- Source branch path: `Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1`.
- Source metric: `146` BTC/USDT trades, `+2.65%` total profit, Sharpe `0.1930`, win rate `45.2055%`, profit factor `1.1218`, max drawdown `-3.8986%`.

The source strategy is not a canary, and the source trades carry `main_regime`, `sub_regime`, `sub_sub_regime_or_profit_factor`, `profit_factor`, and `regime_profit_branch_path` fields. The parent multi-asset strategy remains negative overall, so this packet tests only whether the positive BTC branch can survive the ordered downstream chain.

## Command Evidence

All run-local commands exited `0`:

- `00_filter_btc_trades`: filtered `146` BTC/USDT rows from `ProviderCryptoPullbackRevertV1.real_trades.jsonl`.
- `01_ingest_real_trades_dry_run`.
- `02_ingest_real_trades_force`.
- `03_pre_bayes_status`.
- `04_policy_training_status`.
- `05_export_structural_path_ranking_target`.
- `06_workflow_structural_bundle`.
- `07_workflow_execution_candidate`.
- `08_workflow_full`.
- `09_policy_training_status_after_export`.

Raw command outputs are under `command-output/`; exit markers are under `checks/`.

## Readback

- `auto-quant-ingest-real-trades --force` applied `146/146` rows with `0` invalid rows.
- The ingest wrote BBN state at `state_ingest/auto-quant/B2R_YAHOO_CRYPTO_BTC_PULLBACK_104610/bbn_network.json`.
- `pre-bayes-status --refresh` exited `0`, but latest policy, bridge, soft evidence, filtered assignments, canonical structural regime, and gate status were all absent.
- `export-structural-path-ranking-target` exited `0` and produced `rows=1`, `history_rows=1`, `candidate_set_size=1`, `mature_rows=0`, and `history_mature_rows=0`.
- The exported structural target row did not preserve the source branch path. Its `regime_profit_branch_path`, `main_regime`, `sub_regime`, `sub_sub_regime_or_profit_factor`, and `profit_factor` columns are empty, and the row path is `bootstrap_readiness`.
- CatBoost/path-ranker was not ready: `raw_scored_mature=0/30`, `production_validation=0/30`, `observation_validation=0/30`, calibration `not_fitted`, trainer artifact `missing`, and runtime selection `disabled`.
- `workflow-status --phase structural-recommended-path-bundle` selected only `path:scenario:B2R_YAHOO_CRYPTO_BTC_PULLBACK_104610:bootstrap:no_workflow_state:bootstrap_collect_inputs:primary`.
- `workflow-status --phase execution-candidate` stayed `actionable=false`, `ready=false`, `review_status=observe`, with empty `pre_bayes_gate_status`.
- Full workflow readback returned `closed_loop_branch_admission.status=fail_closed`, `ready=false`, `actionable=false`, and blocking truth `insufficient_state`.

## Decision

- This is materially stronger than the previous canary-only downstream readback because the source is a non-canary provider-owned factor slice with positive BTC/USDT performance and explicit source-side regime branch fields.
- It still cannot be promoted. The branch path does not survive into structural target/workflow, Pre-Bayes/filter state is absent, CatBoost/path-ranker has no mature/scored validation rows, and the execution tree stays bootstrap/observe.
- Accepted production rows added: `0`.
- Promotion allowed: `false`.
- `update_goal=false`.

## Artifacts

- Filtered BTC trades: `derived/provider_crypto_pullback_btc_only_104610_trades.jsonl`.
- Source metrics: `docs/experiments/actionable-regime-confidence/runs/20260512T104610+0800-codex-board-b-yahoo-crypto-precision-fix-aq-v1/workspace/auto-quant-yahoo-crypto-precision-fix/derived/ProviderCryptoPullbackRevertV1.metrics.json`.
- Source real trades: `docs/experiments/actionable-regime-confidence/runs/20260512T104610+0800-codex-board-b-yahoo-crypto-precision-fix-aq-v1/workspace/auto-quant-yahoo-crypto-precision-fix/derived/ProviderCryptoPullbackRevertV1.real_trades.jsonl`.
- Ingest readback: `command-output/02_ingest_real_trades_force.out`.
- Pre-Bayes readback: `command-output/03_pre_bayes_status.out`.
- Structural target export: `command-output/05_export_structural_path_ranking_target.out`.
- Policy/CatBoost readback after export: `command-output/09_policy_training_status_after_export.out`.
- Structural bundle readback: `command-output/06_workflow_structural_bundle.out`.
- Execution candidate readback: `command-output/07_workflow_execution_candidate.out`.
- Full workflow readback: `command-output/08_workflow_full.out`.
