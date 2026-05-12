# Board B LTF Signal-Positive Zero-Trade Readback v1

Run id: `20260512T041631+0800-codex-board-b-ltf-signal-positive-zero-trade-readback-v1`

Scope: append-only diagnostic readback of the completed `041404` LTF zero-trade probe.

This artifact does not edit the Board B Current Cursor, does not supersede
`034002/downstream-combined-v1`, does not satisfy `user_selected_historical_data`,
does not promote a candidate, and does not call `update_goal`.

## Evidence

- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/strategies/AlwaysEnterProbe.py`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/command-output/00_always_enter_probe.out`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/command-output/00_always_enter_probe.err`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/command-output/00_always_enter_probe.exit`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/command-output/01_always_enter_result_keys.out`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/command-output/01_always_enter_result_keys.exit`

## Readback

- `00_always_enter_probe.exit=0` and `01_always_enter_result_keys.exit=0`.
- The probe loaded pair `B2RNQCOSTCRISISREPAIR032157/USD`.
- The pre-backtest signal check saw `373` processed rows, `23` `enter_long` signals, `25` `exit_long` signals, and `0` entry/exit collisions.
- FreqTrade still reported `0` trades, `0.0000` total profit, `0.0000` Sharpe, and `0.0000` win rate.
- FreqTrade logged `Missing data fillup ... before: 239 - after: 373 - 56.07%`, then backtested `2025-12-15 13:00:00` to `2025-12-31 00:00:00`.

## Interpretation

This isolates the LTF zero-trade behavior downstream of signal generation for this
agent-selected synthetic profile. A baseline strategy can emit entry/exit signals
against the loaded frame, but the current FreqTrade/materialized-data profile still
does not turn them into executed trades.

This is diagnostic only. It is not profitability evidence, not a mature rooted
branch observation set, and not a replacement for explicit user selection of
`htf`, `mtf`, or `ltf`.

## Gate

- `fail_closed:ltf_signal_positive_but_trade_materialization_zero`
- `blocked:user_selected_historical_data_missing`
- `not_started:no_pre_bayes_bbn_catboost_execution_tree_rerun`

## Next

Keep `034002` as the current fail-closed cursor. User selection among `htf`,
`mtf`, or `ltf` is still required before the next qualifying factor-research run.
After selection, require a baseline trade-materialization check and carry forward
only nonzero mature rooted branch observations through Pre-Bayes/filter -> BBN ->
CatBoost/path-ranker -> execution tree.
