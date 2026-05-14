# Board B 041143 MTF Sanitized Run Zero-Trade Readback v1

Run id: `20260512T041903+0800-codex-board-b-041143-mtf-sanitized-run-zero-trade-v1`

Scope: append-only readback of the completed `041143` agent-selected MTF
sanitized pair prepare/run repair.

This artifact does not edit the Board B Current Cursor, does not supersede
`034002/downstream-combined-v1`, does not satisfy `user_selected_historical_data`,
does not promote a candidate, and does not call `update_goal`.

## Evidence

- `docs/experiments/actionable-regime-confidence/runs/20260512T041143+0800-codex-board-b-032157-agent-selected-mtf-factor-research-v1/command-output/04_auto_quant_status_after_direct_prepare.json`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041143+0800-codex-board-b-032157-agent-selected-mtf-factor-research-v1/command-output/05_auto_quant_run_tomac_mtf.out`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041143+0800-codex-board-b-032157-agent-selected-mtf-factor-research-v1/command-output/05_auto_quant_run_tomac_mtf.err`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041143+0800-codex-board-b-032157-agent-selected-mtf-factor-research-v1/command-output/05_auto_quant_run_tomac_mtf.exit`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041143+0800-codex-board-b-032157-agent-selected-mtf-factor-research-v1/command-output/06_sanitized_pair_prepare_and_run.out`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041143+0800-codex-board-b-032157-agent-selected-mtf-factor-research-v1/command-output/06_sanitized_pair_prepare_and_run.err`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041143+0800-codex-board-b-032157-agent-selected-mtf-factor-research-v1/command-output/06_sanitized_pair_prepare_and_run.exit`

## Readback

- `04_auto_quant_status_after_direct_prepare.exit=0`.
- `05_auto_quant_run_tomac_mtf.exit=1` with `OperationalException: No pair in whitelist`.
- `06_sanitized_pair_prepare_and_run.exit=0` after rewriting the profile as
  `B2RNQCOSTCRISISREPAIR032157/USD` and matching the pair whitelist.
- The sanitized prepare loaded `260` source rows from `2025-10-31 16:00:00+00:00`
  to `2025-12-31 20:00:00+00:00`, then wrote `260` `1h` bars, `260` `4h`
  bars, and `53` `1d` bars.
- The sanitized Tomac run succeeded but produced `0` trades, `0.0000` total
  profit, `0.0000` Sharpe, `0.0000` win rate, and `0.0000` profit factor.
- FreqTrade reported a `468.24%` missing-data fillup on the `1h` frame and
  moved the backtest start by `250` startup candles, leaving the measured run
  from `2025-11-11 02:00:00` to `2025-12-31 00:00:00`.

## Gate

- `fail_closed:agent_selected_mtf_tomac_zero_trades`
- `blocked:user_selected_historical_data_missing`
- `not_started:no_mature_rows_for_pre_bayes_bbn_catboost_execution_tree`
- `promotion_allowed=false`

## Next

Keep `034002` as the current fail-closed cursor. This MTF sidecar repairs the
pair whitelist/runtime shape but produces no mature branch observations. User
selection among `HTF`, `MTF`, or `LTF` is still required before a qualifying
factor-research/Auto-Quant run; downstream Pre-Bayes/filter -> BBN ->
CatBoost/path-ranker -> execution tree can advance only after nonzero mature
rooted branch observations exist.
