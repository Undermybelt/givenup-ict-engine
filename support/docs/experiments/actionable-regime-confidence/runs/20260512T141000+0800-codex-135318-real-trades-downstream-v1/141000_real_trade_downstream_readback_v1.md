# 141000 Real-Trade Downstream Readback v1

Root: `docs/experiments/actionable-regime-confidence/runs/20260512T141000+0800-codex-135318-real-trades-downstream-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T135318+0800-codex-long-history-es-nq-aq-staging-v1`

## Command Evidence

- `01_export_tomac_real_trades.exit=0`
- `02_build_symbol_manifests.exit=0`
- `03_nq_results_import.exit=0`
- `04_nq_prior_init.exit=0`
- `05_nq_ingest_real_trades.exit=0`
- `06_nq_analyze_15m_1h_1d.exit=130`
- `06_nq_analyze_15m_1h_1d.interrupted=interrupted_at=2026-05-12T14:33:36+0800 reason=nq_analyze_15m_1h_1d_exceeded_20m_no_output_no_new_state`
- `07_nq_pre_bayes_status.exit=0`
- `08_nq_policy_training_status.exit=0`
- `09_nq_export_structural_path_target.exit=0`
- `10_nq_workflow_structural_bundle.exit=0`
- `11_nq_workflow_execution_candidate.exit=0`
- `12_nq_workflow_full.exit=0`
- `13_es_results_import.exit=0`
- `14_es_prior_init.exit=0`
- `15_es_ingest_real_trades.exit=0`
- `16_es_analyze_15m_1h_1d.exit=130`
- `16_es_analyze_15m_1h_1d.interrupted=interrupted_at=2026-05-12T14:36:32+0800 reason=es_analyze_15m_1h_1d_aborted_after_nq_same_path_exceeded_20m`
- `17_es_pre_bayes_status.exit=0`
- `18_es_policy_training_status.exit=0`
- `19_es_export_structural_path_target.exit=0`
- `20_es_workflow_structural_bundle.exit=0`
- `21_es_workflow_execution_candidate.exit=0`
- `22_es_workflow_full.exit=0`

## Readback

- Exported real trades from the 135318 TOMAC family: `192` total rows split into `77` NQ and `115` ES rows.
- NQ ingest applied `77/77` rows with `0` invalid rows. ES ingest applied `115/115` rows with `0` invalid rows.
- Both full analyze attempts were interrupted fail-closed before producing fresh analyze output or Pre-Bayes soft evidence. NQ exceeded `20m` with no output/new state; ES was aborted after the same full-path profile was classified as too heavy.
- Pre-Bayes status for both NQ and ES was null after the interrupted analyze attempts: no latest bridge, no canonical active regime, no policy, no soft evidence, and no gate status.
- Policy training stayed immature for both symbols: `analyze_runs=0`, both entry models had `matched_rows=0`, structural path-ranking runtime was disabled, and validation readiness was false.
- Structural path target export preserved the branch path, but only as a tiny censored target: NQ had `2` rows and `1` mature row; ES had `2` rows and `1` mature row. Both had `0` rows with raw path score, calibrated path probability, path lower bound, or execution gate status.
- Workflow/execution preserved the path `TrendExpansion -> LongHistoryTomacBreakout -> KillzoneContinuation -> TomacNQ_KillzoneBreakout`, but stayed observe-only: `ready=false`, `actionable=false`, `review_status=observe`, `execution_gate_status=execution_candidate_observed`, and no CatBoost/path-ranker score/probability/lower bound.

## Decision

This root is settled fail-closed support evidence. It proves import, real-trade ingest, branch-path preservation, and workflow visibility on the 135318 TOMAC family, but it does not produce Board A-compatible regime labels, non-null Pre-Bayes/BBN admission, CatBoost/path-ranker calibration, execution readiness, provider-backed portability, cross-market survival, or sufficient trade density.

Promotion remains disallowed. This root should be counted once as a chain-contract/infrastructure negative sample, not as market-factor failure and not as profitability promotion evidence.
