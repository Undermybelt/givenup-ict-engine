# Post-093435 Auto-Quant Ingest Chain Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T100231+0800-codex-post-093435-autoquant-ingest-chain-readback-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T093435+0800-codex-board-b-aq-first-tomac-smoke-downstream-v1`

## Objective Mapping

| Requirement | Evidence | Status |
|---|---|---|
| Use real Auto-Quant output | Reused the 093435 `TomacNQ_KillzoneBreakout` `NQ/USD` Freqtrade backtest from `/Users/thrill3r/Auto-Quant/user_data/backtest_results/backtest-result-2026-05-12_09-40-02.zip`. | done_non_promoting |
| Feed ict-engine from Auto-Quant output | Converted the 5 trades to `derived/tomac_nq_real_trades_post_093435_v2.jsonl`; dry-run parsed 5/5 and force ingest inserted 5 feedback records in isolated `state_ingest`. | done_non_promoting |
| Preserve filter / Pre-Bayes readback | `pre-bayes-status --refresh` exited 0 but all latest policy/bridge/soft-evidence fields were null. | fail_closed |
| Preserve BBN / feedback path readback | `auto-quant-ingest-real-trades --force` exited 0 and reported `feedback_records_inserted=5`; this is isolated-state feedback only. | done_non_promoting |
| Preserve CatBoost / policy-training readback | `policy-training-status` exited 0; both entry models have `matched_rows=0` and are not ready for BBN or CatBoost. | fail_closed |
| Preserve execution-tree / structural path readback | `workflow-status` and `export-structural-path-ranking-target` exited 0; exported 1 target row, `mature_rows=0`, `production_validation=0/30`, `observation_validation=0/30`, execution candidate remains `observe`. | fail_closed |
| Use provider readback | `provider-status --agent` exited 0; yfinance live/market-data and Kraken CLI are ready, IBKR gateway is reachable but dependencies are missing, TradingView MCP is unhealthy. | partial |
| Do not claim 95% regime completion | No accepted rows, no source/control unlock, no selected-data promotion, no CatBoost readiness, no execution promotion, no trade claim. | pass_fail_closed |

## Backtest Readback

`TomacNQ_KillzoneBreakout` on `NQ/USD` for `20230101-20251231` produced:

- trades: `5`
- total profit: `-1.31%` / `-1307.20 USD`
- win rate: `60.0%`
- profit factor: `0.6185`
- Sharpe: `-0.0192`

This is real Auto-Quant/Freqtrade execution evidence, but it is too thin and negative for promotion.

## Wire-Format Debugging

The first JSONL conversion used `long` as `factors_used[].direction`, so ict-engine parsed `0/5` and counted `5` invalid rows. The canonical wire owner is `src/application/auto_quant/real_trades/wire.rs`, where factor directions must be `Bull|Bear|Neutral`.

The v2 JSONL uses `Bull` for the long factor direction. Dry-run parsed `5/5`, then the real ingest was blocked by the same-content guard because the dry-run had written a `dry_run_preview` ledger entry. Since the state was isolated and the dry-run did not mutate the BBN, the force ingest was used and inserted 5 feedback records.

## Gate Result

`post_093435_autoquant_ingest_chain_readback_v1=autoquant_trades_ingested_isolated_downstream_fail_closed_no_promotion`

Board A remains incomplete:

- `accepted_rows_added=0`
- `valid_required_root_unlock=false`
- `source_control_evidence_acquired=false`
- `selected_data_autoquant_promotion=false`
- `downstream_promotion_rerun=false`
- `catboost_ready=false`
- `execution_candidate_ready=false`
- `strict_full_objective=false`
- `trade_usable=false`
- `promotion_allowed=false`
- `update_goal=false`

## Next

Keep this as non-promoting chain evidence. Production Board A still needs real R6/R5/R3 source/control unlock evidence or explicit selected-history approval before any selected-data Auto-Quant promotion, Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion can count toward the 95% regime objective.
