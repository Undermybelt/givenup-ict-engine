# Auto-Quant timeframe ladder fail-closed notes

Use this when an ict-engine factor request asks to rerun a profitability factor across a short fixed window and "send it to tree" only if gates pass.

## Session pattern captured

A three-month Auto-Quant timeframe ladder was run for the rooted branch:

```text
Transition -> LiquiditySweep -> sweep_reclaim_small_cycle -> liquidity_sweep_reclaim_15m_wide_v1
```

Window:

```text
20251001-20251231
```

Locally retained Auto-Quant NQ data only had:

```text
5m, 15m, 1h, 4h, 1d
```

No retained `1m` or `3m` data existed, so the valid ladder began at `5m` rather than fabricating missing lower timeframes.

## Durable workflow lesson

1. Enumerate retained provider/AQ timeframe files before promising the full ladder.
2. Run every available timeframe in isolated `/tmp` Auto-Quant-compatible workspace variants; do not mutate the user's Auto-Quant checkout.
3. Treat `0` trades on all timeframes as a factor-gate failure, not provider failure, if all backtests exit `0`.
4. It is still valid to push a fail-closed library through readback surfaces for parity:
   - `auto-quant-results-import`
   - `auto-quant-prior-init`
   - real-trade ingestion attempt
   - structural path target export
   - path-ranker / CatBoost runtime attempt
   - analyze / workflow / Pre-Bayes / policy readback
5. Do not claim promotion or tree readiness unless real trades produce matched policy rows and ranker scores are visible/used by execution tree.

## Fail-closed evidence shape

A proper terminal decision should name all of these:

```text
timeframes_run
missing_timeframes
trade_count_by_timeframe
pass_count
auto_quant_exit_status
real_trade_matched_rows
ranker_runtime_status
execution_gate_status
actionable
final_decision
```

For the captured session, all available timeframes (`5m`, `15m`, `1h`, `4h`, `1d`) produced `0` trades, `pass_count=0`, `auto_quant_real_trade_entry_v1 matched_rows=0`, ranker runtime was `enabled_no_matching_scores`, execution stayed `observe/transition_guardrail`, and final decision was `drop_three_month_timeframe_ladder`.

## Pitfall

Do not force a downstream CatBoost/execution-tree success narrative after a zero-trade ladder. A tree readback can prove branch attribution and fail-closed behavior, but cannot promote a factor with no realized trade rows.
