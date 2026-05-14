# 135532 Long-History ES/NQ 1m AQ Stage Retry v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T135532+0800-codex-long-history-es-nq-1m-aq-stage-retry-v1`

## Purpose

This is a retry of the failed `20260512T135257+0800-codex-long-history-es-nq-1m-aq-stage-v1` staging command. The failed root used a repo-relative script path while running from `/Users/thrill3r/Auto-Quant`, so Python looked for the script under the Auto-Quant checkout and exited before staging data.

This retry copies the staging script into its own run root and executes that copied script by absolute path. The output is an isolated Auto-Quant workspace under this run root.

## Command Status

- `01_stage_long_history_es_nq_aq.exit=0`
- Stderr is empty.
- Command log: `command-output/01_stage_long_history_es_nq_aq.cmd`

## Staged Data

The staged workspace is:

`workspace/auto-quant/`

The stage produced ES and NQ feather files for:

- `1m`
- `5m`
- `15m`
- `1h`
- `4h`
- `1d`

Key row counts:

| Market | 1m rows | 1m start | 1m end |
|---|---:|---|---|
| NQ | 301577 | 2012-07-06T12:46:00+00:00 | 2023-10-26T16:19:00+00:00 |
| ES | 299107 | 2012-04-23T13:38:00+00:00 | 2025-08-04T12:10:00+00:00 |

Full manifest:

- `long_history_es_nq_aq_stage_manifest.json`
- `long_history_es_nq_aq_stage_rows.csv`

## Gate

- `evidence_class=long_history_1m_aq_staging_repair`
- `stage_success=true`
- `auto_quant_workspace_isolated=true`
- `measured_auto_quant_candidate=false`
- `pre_bayes_bbn_consumed=false`
- `catboost_path_ranker_consumed=false`
- `execution_tree_admitted=false`
- `accepted_95_contexts=0`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Decision

The path blocker from `135257` is fixed for this retry: the ES/NQ long-history 1m data is now staged into an isolated Auto-Quant workspace with multi-timeframe sibling files.

This is not an acceptance packet. It does not contain a measured Auto-Quant strategy result, a Pre-Bayes/BBN posterior, CatBoost/path-ranker calibration, provider-context validation, or execution-tree readiness.

Several sibling long-history runs were active after this stage was produced. They should be treated as the next source of measured evidence; this packet only proves that the local ES/NQ cleaned 1m data can be staged correctly for Auto-Quant.

## Next

Use the staged workspace or the active sibling measured roots to produce a real Auto-Quant candidate packet, then feed that packet through filter/Pre-Bayes, BBN, CatBoost/path-ranker, and execution-tree admission. Keep provider-context coverage fail-closed until the IBKR, TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, and Bybit overlap matrix is recorded.
