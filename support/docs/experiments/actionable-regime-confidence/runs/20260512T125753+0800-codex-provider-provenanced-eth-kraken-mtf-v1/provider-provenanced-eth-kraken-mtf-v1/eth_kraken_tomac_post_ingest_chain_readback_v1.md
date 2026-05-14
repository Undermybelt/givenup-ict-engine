# ETH Kraken TOMAC Post-Ingest Chain Readback v1

Generated: 2026-05-12T13:45:00+0800

## Scope

This note extends the settled root `20260512T125753+0800-codex-provider-provenanced-eth-kraken-mtf-v1` after the one-trade TOMAC result was exported as real-trade JSONL and ingested into ict-engine.

This is a downstream chain-contract readback only. It does not satisfy the six-provider lock, does not promote a factor, does not mark the path trade-usable, and does not call `update_goal`.

## Ordered Chain Evidence

Provider and Auto-Quant:

- Kraken ETHUSD MTF fetch/convert/analyze/prepare commands exited `0` before this note.
- `auto_quant_run_tomac_pair_alias_timerange` exited `0` after the isolated pair-alias and timerange repair.
- The Auto-Quant result remained thin: exactly `1` trade, profit `0.77%`, win rate `100%`, Sharpe/Sortino/Calmar `-100`, profit factor `0`.

Real-trade export and ingest:

- Exported trade file: `derived/eth_kraken_tomac_real_trades_pair_alias_timerange.jsonl`.
- Branch path preserved on the trade row: `TrendExpansion -> BullTrendAcceleration -> MultiTimeframeIntradayResonance -> TomacNQ_KillzoneBreakout`.
- Ingest command: `auto-quant-ingest-real-trades --symbol ETH_KRAKEN --state-dir state_eth_kraken_mtf --source auto_quant_real_trades_eth_kraken_tomac_125753`.
- Ingest readback: `ledger_status=applied`, `trades_total=1`, `trades_applied=1`, `trades_invalid=0`, `feedback_records_inserted=1`, `content_hash=e35aebcd068f00c6`.

Pre-Bayes / BBN:

- `post_ingest_02_pre_bayes_status_refresh` exited `0`.
- `latest_gate_status=pass_neutralized`.
- Soft evidence was active: `latest_uses_soft_evidence=true`.
- Canonical structural posterior readback: active regime `trend`, confidence `0.5574970918447152`, probabilities `trend=0.4460727525727625`, `range=0.3107854494854475`, `stress=0.16745597773596904`, `transition=0.075685820205821`.
- Filtered market state retained the regime branch root: `market_state_primary_regime=TrendExpansion`, `market_state_secondary_regime=BullTrendAcceleration`, `multi_timeframe_resonance=aligned`.

Structural path-ranking target:

- `post_ingest_07_export_structural_path_ranking_target` exited `0`.
- Export summary: `rows=3`, `candidate_set_size=3`, `mature_rows=1`, `history_mature_rows=2`, `rows_with_raw_path_score=0`, `rows_with_calibrated_path_prob=0`, `rows_with_path_prob_lower_bound=0`, `rows_with_training_weight=1`.
- The ranked mature row preserved the required split:
  - `main_regime=TrendExpansion`
  - `sub_regime=BullTrendAcceleration`
  - `sub_sub_regime_or_profit_factor=MultiTimeframeIntradayResonance`
  - `profit_factor=TomacNQ_KillzoneBreakout`

CatBoost / path-ranker:

- `post_ingest_09_catboost_train_thin_target` exited `1`.
- Trainer read `3` rows but only `1` mature training sample.
- CatBoost failed with `All features are either constant or ignored.`
- No CatBoost model, trainer artifact, calibrated path probability, lower bound, or runtime score was produced from this thin target.

Execution tree / candidate:

- `post_ingest_06_workflow_execution_candidate` exited `0`.
- Exact structural branch was visible: `TrendExpansion -> BullTrendAcceleration -> MultiTimeframeIntradayResonance -> TomacNQ_KillzoneBreakout`.
- `selected_path_probability=0.45043788716383176`.
- `pre_bayes_gate_status=pass_neutralized`.
- `execution_readiness=0.43776422616823835`.
- `execution_gate_status=execution_blocked`.
- `candidate_status=execution_blocked`, `review_status=observe`, `ready=false`, `actionable=false`.
- `closed_loop_branch_admission.status=fail_closed` with reason `exact_structural_branch_visible_but_not_ready_or_actionable`.

## Decision

The `125753` root is now a valid provider-provenanced, regime-rooted, downstream-ingested negative/thin sample:

- It proves the isolated Kraken ETH MTF provider/AQ path can be repaired into FreqTrade, exported as a regime-rooted real trade, ingested into ict-engine, and surfaced through Pre-Bayes/BBN, structural path-ranking export, CatBoost attempt, and execution candidate readback.
- It does not prove a mature profitability factor, because the evidence is one trade and CatBoost cannot train on the exported target.
- The correct Board B classification is fail-closed: `provider_provenanced_kraken_eth_mtf_aq_ingested_but_catboost_thin_target_execution_blocked`.

## Evidence Files

- Ingest: `command-output/ingest_eth_kraken_tomac_real_trades.out`
- Pre-Bayes: `command-output/post_ingest_02_pre_bayes_status_refresh.out`
- Workflow full: `command-output/post_ingest_03_workflow_full_refresh.out`
- Structural bundle: `command-output/post_ingest_04_workflow_structural_bundle.out`
- Structural feedback: `command-output/post_ingest_05_workflow_structural_feedback.out`
- Execution candidate: `command-output/post_ingest_06_workflow_execution_candidate.out`
- Path target export: `command-output/post_ingest_07_export_structural_path_ranking_target.out`
- Policy training status: `command-output/post_ingest_08_policy_training_status.out`
- CatBoost failure: `command-output/post_ingest_09_catboost_train_thin_target.err`

## Next

Do not re-run this same one-trade TOMAC path as proof. Useful follow-up is either:

- extend this Kraken ETH MTF branch until it has enough rooted observations for CatBoost/path-ranker maturity, or
- continue the stronger same-root six-provider ETH line where provider authority is broader and CatBoost runtime closure already has more usable support.
