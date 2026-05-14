# 115700 Enriched Downstream Readback v1

- Decision: `115700_enriched_rows_schema_valid_downstream_readback_fail_closed`
- Source AQ root: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`
- State dir: `/tmp/ict-engine-board-b-115700-enriched-downstream-121324-r2`
- Enriched rows: `237`; schema-accepted rows: `237`.
- Ingest status: `applied`; trades applied: `237`; invalid: `0`.
- Structural path target rows: `5`; history rows: `240`; external score rows: `2`.
- Promotion: `false`; trade usable: `false`; `update_goal=false`.

## Provider Rows

| Provider | Rows |
|---|---:|
| `binance_public` | `52` |
| `bybit_public` | `51` |
| `ibkr_paxos_long_midpoint` | `44` |
| `kraken_public` | `32` |
| `tvr_default_binance` | `37` |
| `yfinance` | `21` |

## Commands

| Command | Exit | Output | Error |
|---|---:|---|---|
| `analyze_btc_usdt_ibkr_midpoint` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/analyze_btc_usdt_ibkr_midpoint.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/analyze_btc_usdt_ibkr_midpoint.err` |
| `pre_bayes_status_before_ingest` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/pre_bayes_status_before_ingest.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/pre_bayes_status_before_ingest.err` |
| `auto_quant_ingest_real_trades_enriched` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/auto_quant_ingest_real_trades_enriched.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/auto_quant_ingest_real_trades_enriched.err` |
| `pre_bayes_status_after_ingest` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/pre_bayes_status_after_ingest.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/pre_bayes_status_after_ingest.err` |
| `policy_training_status_after_ingest` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/policy_training_status_after_ingest.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/policy_training_status_after_ingest.err` |
| `export_structural_path_ranking_target` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/export_structural_path_ranking_target.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/export_structural_path_ranking_target.err` |
| `apply_structural_path_ranking_external_scores` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/apply_structural_path_ranking_external_scores.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/apply_structural_path_ranking_external_scores.err` |
| `register_structural_path_ranking_trainer_artifact` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/register_structural_path_ranking_trainer_artifact.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/register_structural_path_ranking_trainer_artifact.err` |
| `enable_structural_path_ranking_runtime` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/enable_structural_path_ranking_runtime.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/enable_structural_path_ranking_runtime.err` |
| `workflow_status_structural_ranker_runtime` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/workflow_status_structural_ranker_runtime.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/workflow_status_structural_ranker_runtime.err` |
| `workflow_status_execution_candidate` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/workflow_status_execution_candidate.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/command-output/workflow_status_execution_candidate.err` |

## Gate

- `pass:115700_enriched_schema_rows_present`
- `pass:ingested_feedback_records_237`
- `pass:structural_path_export_rows_5`
- `pass:external_path_score_rows_2`
- `fail_closed:selected_history_source_control_locked`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Result

This repairs the row-level chain contract for the current `115700` packet and proves the isolated downstream surfaces can consume it. It still does not promote the packet: the scores are run-local branch outcome-rate scores, not a live CatBoost training package, and selected-history/source-control gates remain locked.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/115700-enriched-downstream-readback-v1/115700_enriched_downstream_readback_v1.json`
- Enriched JSONL: `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/115700-enriched-downstream-readback-v1/115700_enriched_real_trades.jsonl`
- Row schema gate: `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/115700-enriched-downstream-readback-v1/115700_enriched_row_schema_gate.json`
- External scores: `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/115700-enriched-downstream-readback-v1/115700_external_path_scores.jsonl`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T121324+0800-codex-115700-enriched-downstream-readback-v1/checks/115700_enriched_downstream_readback_v1_assertions.out`
