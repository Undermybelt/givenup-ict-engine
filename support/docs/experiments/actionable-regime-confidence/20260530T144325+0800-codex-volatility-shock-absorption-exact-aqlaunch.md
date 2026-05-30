# Volatility Shock Absorption Exact-AQ Prep Workdoc

- created_at: `20260530T144325+0800`
- owner: `codex`
- agent_name: `codex-volatility-shock-absorption-exact-aqprep-20260530T144325+0800`
- run_root: `/tmp/ict-engine-volatility-shock-absorption-exact-aqlaunch-20260530T144325+0800`
- compact_root: `support/docs/experiments/actionable-regime-confidence/runs/20260530T144325+0800-codex-volatility-shock-absorption-exact-aqlaunch-v1`
- repo_doc: `support/docs/experiments/actionable-regime-confidence/20260530T144325+0800-codex-volatility-shock-absorption-exact-aqlaunch.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T144325+0800-codex-volatility-shock-absorption-exact-aqlaunch.claim`
- local_screen_root: `/tmp/ict-engine-volatility-shock-absorption-trend-continuation-local-screen-20260530T120034+0800`
- fee_rescue_queue_terminal_metrics: `/tmp/ict-engine-futures-fee-rescue-exact-replay-queue-20260530T132455+0800/checks/terminal_metrics.json`
- family_id: `volatility_shock_absorption_trend_continuation`
- primary_factor_id: `tomac_idxfut_volatility_shock_absorption_trend_continuation_30m_v1`
- branch_path: `TrendExpansion -> VolatilityShockAbsorption -> PostShockTrendHold -> VolTargetAtrExit -> tomac_idxfut_volatility_shock_absorption_trend_continuation_30m_v1`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- status: `exact_aq_completed_fail_closed`
- coordination_only: `false`
- provider_or_aq_launched: `true`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Runtime Boundary

- `--launch` passed same-turn collision guard with `ready=true` and ran six Freqtrade futures exact-AQ backtests.
- No provider fetch, IBKR historical fetch, paper, simulated, live, downstream lifecycle, or same_tree_practical_closure packet was produced here.
- This is exact-AQ evidence only; practical promotion remains fail-closed.

## Targets
- `tomac_idxfut_volatility_shock_absorption_trend_continuation_30m_v1` NQ 30m short `z2_abs0.45_h8_s1.4_t2.4_tr55` trades=462 instrument_cost_ret_pct=13.010348
- `tomac_idxfut_volatility_shock_absorption_trend_continuation_15m_v1` NQ 15m long `z2.4_abs0.5_h10_s1.6_t3_tr89` trades=443 instrument_cost_ret_pct=12.787945
- `tomac_idxfut_volatility_shock_absorption_trend_continuation_30m_v1` NQ 30m short `z1.8_abs0.38_h6_s1.2_t2_tr34` trades=525 instrument_cost_ret_pct=12.631436
- `tomac_idxfut_volatility_shock_absorption_trend_continuation_5m_v1` YM 5m long `z2.4_abs0.5_h10_s1.6_t3_tr89` trades=437 instrument_cost_ret_pct=8.351408
- `tomac_idxfut_volatility_shock_absorption_trend_continuation_5m_v1` NQ 5m long `z1.8_abs0.38_h6_s1.2_t2_tr34` trades=2303 instrument_cost_ret_pct=4.243476
- `tomac_idxfut_volatility_shock_absorption_trend_continuation_15m_v1` NQ 15m short `z2.4_abs0.5_h10_s1.6_t3_tr89` trades=518 instrument_cost_ret_pct=1.788416

## Launch Commands When Audit Clears

```bash
<AUTO_QUANT_VENV_PYTHON> <REPO_ROOT>/support/scripts/auto_quant_external/run_tomac_one.py TomacIdxfutVolatilityShockAbsorptionTrendContinuation30mShortZ2Abs045H8S14T24Tr55 30m /tmp/ict-engine-volatility-shock-absorption-exact-aqlaunch-20260530T144325+0800/checks/aq_trades_TomacIdxfutVolatilityShockAbsorptionTrendContinuation30mShortZ2Abs045H8S14T24Tr55.json NQ/USD 20210103-20251231
<AUTO_QUANT_VENV_PYTHON> <REPO_ROOT>/support/scripts/auto_quant_external/run_tomac_one.py TomacIdxfutVolatilityShockAbsorptionTrendContinuation15mLongZ24Abs05H10S16T3Tr89 15m /tmp/ict-engine-volatility-shock-absorption-exact-aqlaunch-20260530T144325+0800/checks/aq_trades_TomacIdxfutVolatilityShockAbsorptionTrendContinuation15mLongZ24Abs05H10S16T3Tr89.json NQ/USD 20210103-20251231
<AUTO_QUANT_VENV_PYTHON> <REPO_ROOT>/support/scripts/auto_quant_external/run_tomac_one.py TomacIdxfutVolatilityShockAbsorptionTrendContinuation30mShortZ18Abs038H6S12T2Tr34 30m /tmp/ict-engine-volatility-shock-absorption-exact-aqlaunch-20260530T144325+0800/checks/aq_trades_TomacIdxfutVolatilityShockAbsorptionTrendContinuation30mShortZ18Abs038H6S12T2Tr34.json NQ/USD 20210103-20251231
<AUTO_QUANT_VENV_PYTHON> <REPO_ROOT>/support/scripts/auto_quant_external/run_tomac_one.py TomacIdxfutVolatilityShockAbsorptionTrendContinuation5mLongZ24Abs05H10S16T3Tr89 5m /tmp/ict-engine-volatility-shock-absorption-exact-aqlaunch-20260530T144325+0800/checks/aq_trades_TomacIdxfutVolatilityShockAbsorptionTrendContinuation5mLongZ24Abs05H10S16T3Tr89.json YM/USD 20210103-20251231
<AUTO_QUANT_VENV_PYTHON> <REPO_ROOT>/support/scripts/auto_quant_external/run_tomac_one.py TomacIdxfutVolatilityShockAbsorptionTrendContinuation5mLongZ18Abs038H6S12T2Tr34 5m /tmp/ict-engine-volatility-shock-absorption-exact-aqlaunch-20260530T144325+0800/checks/aq_trades_TomacIdxfutVolatilityShockAbsorptionTrendContinuation5mLongZ18Abs038H6S12T2Tr34.json NQ/USD 20210103-20251231
<AUTO_QUANT_VENV_PYTHON> <REPO_ROOT>/support/scripts/auto_quant_external/run_tomac_one.py TomacIdxfutVolatilityShockAbsorptionTrendContinuation15mShortZ24Abs05H10S16T3Tr89 15m /tmp/ict-engine-volatility-shock-absorption-exact-aqlaunch-20260530T144325+0800/checks/aq_trades_TomacIdxfutVolatilityShockAbsorptionTrendContinuation15mShortZ24Abs05H10S16T3Tr89.json NQ/USD 20210103-20251231
```

## Status

- decision: `exact_aq_completed_fail_closed`
- exact_aq_completed: `true`
- exact_aq_exit0_count: `6`
- exact_aq_positive_count: `2`
- exact_aq_negative_count: `4`
- next_gate: `same_tree_downstream_lifecycle_for_positive_exact_aq_rows_only`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Exact-AQ Result Table

| idx | symbol | tf | side | variant | trades | total_profit_pct | profit_factor | sharpe | max_drawdown_pct | verdict |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---|
| 0 | NQ | 30m | short | `z2_abs0.45_h8_s1.4_t2.4_tr55` | 537 | -15.13 | 0.9167 | -0.1973 | -24.8536 | `rejected_by_exact_aq` |
| 1 | NQ | 15m | long | `z2.4_abs0.5_h10_s1.6_t3_tr89` | 599 | 24.75 | 1.1609 | 0.3328 | -9.9976 | `positive_followup_not_trade_usable` |
| 2 | NQ | 30m | short | `z1.8_abs0.38_h6_s1.2_t2_tr34` | 631 | -25.22 | 0.8625 | -0.3755 | -30.6123 | `rejected_by_exact_aq` |
| 3 | YM | 5m | long | `z2.4_abs0.5_h10_s1.6_t3_tr89` | 1098 | -12.57 | 0.9158 | -0.3418 | -21.7180 | `rejected_by_exact_aq` |
| 4 | NQ | 5m | long | `z1.8_abs0.38_h6_s1.2_t2_tr34` | 2697 | 22.56 | 1.0690 | 0.5961 | -18.8088 | `positive_followup_not_trade_usable` |
| 5 | NQ | 15m | short | `z2.4_abs0.5_h10_s1.6_t3_tr89` | 602 | -2.89 | 0.9846 | -0.0380 | -14.8598 | `rejected_by_exact_aq` |

Result artifact: `/tmp/ict-engine-volatility-shock-absorption-exact-aqlaunch-20260530T144325+0800/summaries/aq_result_table.json`.

Only idx `1` and idx `4` remain alive for downstream/lifecycle work. They are not practical factors yet because same-tree lifecycle closure, accepted paper/live/broker feedback, and promotion gates are still absent.

## AQ Result Readback

- terminal_metrics: `/tmp/ict-engine-volatility-shock-absorption-exact-aqlaunch-20260530T144325+0800/checks/terminal_metrics.json`
- provider_or_aq_launched: `true`
- child_exit_zero_count: `6`
- futures_mode_readback: `Detected --trading-mode: futures` in every child stderr.
- data_stage: NQ `5m/15m/30m` and YM `5m` were `already_present` under the local Auto-Quant futures data root.

AQ-positive candidates:

- `TomacIdxfutVolatilityShockAbsorptionTrendContinuation15mLongZ24Abs05H10S16T3Tr89` NQ 15m long: trades `599`, total_profit_pct `+24.75`, max_drawdown_pct `-9.9976`, profit_factor `1.1609`, sharpe `0.3328`.
- `TomacIdxfutVolatilityShockAbsorptionTrendContinuation5mLongZ18Abs038H6S12T2Tr34` NQ 5m long: trades `2697`, total_profit_pct `+22.56`, max_drawdown_pct `-18.8088`, profit_factor `1.0690`, sharpe `0.5961`.

AQ-negative candidates:

- NQ 30m short `z2_abs0.45_h8_s1.4_t2.4_tr55`: total_profit_pct `-15.13`, profit_factor `0.9167`.
- NQ 30m short `z1.8_abs0.38_h6_s1.2_t2_tr34`: total_profit_pct `-25.22`, profit_factor `0.8625`.
- YM 5m long `z2.4_abs0.5_h10_s1.6_t3_tr89`: total_profit_pct `-12.57`, profit_factor `0.9158`.
- NQ 15m short `z2.4_abs0.5_h10_s1.6_t3_tr89`: total_profit_pct `-2.89`, profit_factor `0.9846`.

This is a fee-rescue exact-AQ readback, not practical promotion. The packet
remains `promotion_allowed=false`, `trade_usable=false`, and
`same_tree_practical_closure=null` until downstream same-root lifecycle evidence
and accepted execution feedback pass.
