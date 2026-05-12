# 103010 BTC Ingest Downstream Readback v1

Run id: `20260512T103851+0800-codex-103010-btc-ingest-downstream-readback-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T103010+0800-codex-board-b-provider-btc-always-entry-canary-v1`

Gate result: `btc_103010_ingest_downstream_readback_v1=real_trades_ingested_bbn_written_structural_chain_fail_closed_no_promotion`

## Readback

- Source Auto-Quant/Freqtrade canary produced `81` BTC/USDT trades from `2026-04-01 01:00:00` to `2026-05-12 00:00:00`, total profit `4.41%`, Sharpe `2.56`, win rate `53.1%`, profit factor `1.20`, and max drawdown `4.98%`.
- `auto-quant-ingest-real-trades --force` applied `81/81` rows with `0` invalid rows and wrote `feedback_records_inserted=81`.
- `state_ingest/auto-quant/B2R_PROVIDER_BTC_CANARY_103010/bbn_network.json` exists and its `trade_outcome` CPT includes an updated probability row for the canary feedback path.
- `pre-bayes-status --refresh` exited `0` but returned no latest policy, bridge, soft evidence, or filtered assignments.
- `policy-training-status` after structural target export exited `0` with `structural_path_ranking_target rows=1 history_rows=1 mature_rows=0 history_mature_rows=0`.
- CatBoost/path-ranker validation remains not ready: `raw_scored_mature=0/30`, `production_validation=0/30`, `observation_validation=0/30`, calibration `not_fitted`, trainer artifact `missing`, and runtime selection `disabled`.
- `workflow-status` structural bundle and execution candidate exited `0`, but the selected path is bootstrap-only: `path:scenario:B2R_PROVIDER_BTC_CANARY_103010:bootstrap:no_workflow_state:bootstrap_collect_inputs:primary`.
- Full workflow readback has `closed_loop_branch_admission.status=fail_closed`, `ready=false`, `actionable=false`, `candidate_status=execution_candidate_observed`, and blocking truth `insufficient_state`.

## Decision

- This is real provider-owned BTC trade feedback that reaches ict-engine ingestion and BBN state, so it is materially stronger than the earlier zero-trade provider loops.
- It still does not satisfy Board A promotion or completion requirements because Pre-Bayes/filter state is absent, CatBoost/path-ranking has no mature/scored validation rows, execution tree is bootstrap/no-workflow-state, and no cross-instrument or cross-period validation was performed.
- Accepted production rows added: `0`.
- Promotion allowed: `false`.
- `update_goal=false`.

## Artifacts

- Source trades: `docs/experiments/actionable-regime-confidence/runs/20260512T103010+0800-codex-board-b-provider-btc-always-entry-canary-v1/derived/provider_btc_always_entry_canary_trades_v1.jsonl`
- Source ingest output: `docs/experiments/actionable-regime-confidence/runs/20260512T103010+0800-codex-board-b-provider-btc-always-entry-canary-v1/command-output/06_ingest_real_trades_force.out`
- Pre-Bayes readback: `command-output/00_pre_bayes_status.out`
- Policy/CatBoost readback after export: `command-output/06_policy_training_status_after_export.out`
- Structural target export: `command-output/02_export_structural_path_ranking_target.out`
- Structural bundle readback: `command-output/03_workflow_structural_bundle.out`
- Execution candidate readback: `command-output/04_workflow_execution_candidate.out`
- Full workflow readback: `command-output/05_workflow_full.out`
