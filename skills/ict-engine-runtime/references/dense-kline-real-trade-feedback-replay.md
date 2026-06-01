# Dense K-line real trade feedback replay

Use when a regime-rooted dense K-line branch has positive Auto-Quant/Freqtrade aggregate results and the next step is structural feedback replay.

## Durable lesson

Do not replay feedback from aggregate summaries. Export the real per-trade rows first, then replay only those rows.

A valid branch path keeps these fields through Auto-Quant -> rank -> BBN -> CatBoost -> execution tree:

- `main_regime`
- `sub_regime`
- `sub_sub_regime_or_profit_factor`
- `profit_factor`
- `regime_profit_branch_path`
- provider / symbol / timeframe provenance

Expected branch shape:

`主regime -> 子regime -> 子子regime或盈利因子 -> 盈利因子`

## Required sequence

1. Claim the lane in the authoritative board doc before work.
2. Locate the Freqtrade/Auto-Quant result artifact for each provider/timeframe.
3. Export `bt.results["strategy"][strategy]["trades"]` rows to CSV.
4. Verify row count and PnL semantics per export.
5. Check `sum(trades.profit_abs) == summary.profit_total_abs` within numeric tolerance.
6. Only after this, replay structural feedback observations.
7. Stamp each feedback row with branch path + provider + symbol + timeframe + source CSV.
8. Re-run BBN prior/evidence, CatBoost/path-ranker train/apply/register, then execution-tree trace.
9. After rerunning `analyze`, export the structural target again and re-apply scores to the new live `candidate_set_id`; analyze can mint a new candidate set, and stale scores can leave execution-tree ranker visibility false or `enabled_no_matching_scores`.
10. Verify execution tree after the final score apply/analyze cycle, not before it.
11. Promotion requires maturity gates and non-guarded execution; positive dense aggregates or ranker readiness alone mean handoff/incubate, not promote.

## Rejection rules

Reject or block when:

- feedback rows were generated from aggregate summary fields instead of trades
- branch fields are absent or collapsed before rank/BBN/CatBoost
- `profit_abs` row sums do not match Freqtrade summary PnL
- mixed packets hide timeframe split behavior, e.g. 1m/5m positive but 15m/30m negative
- TradingViewRemix/IBKR/YF/Kraken provenance is missing from feedback rows
- execution tree trace lacks nested `output.path_ranker_score_visible_to_execution_tree`, `output.path_ranker_score_used_by_execution_tree`, or model family evidence
- `workflow-status` says ranker ready but the live structural bundle reports `enabled_no_matching_scores`; export the current target, reapply scores for that current `candidate_set_id`, and rerun analyze
- reporting target-history rows as unique trade observations; `history_mature_rows` can inflate after repeated exports, while real evidence count is the number of distinct feedback/trade rows replayed

## Provider notes

Treat IBKR, TradingViewRemix, yfinance/YF, and Kraken as provider dimensions, not interchangeable data. If one provider fetch fails, record the failure and continue valid providers; do not infer missing provider evidence from another provider.

## Board hygiene

Multi-agent Board docs are the lock. Convert `Active` to `Handoff` or `Blocked` with evidence paths before ending. Never overwrite another agent's active/completed lane.
