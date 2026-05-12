# Board B 041404 Tick Precision Closeout v1

Run id: `20260512T041714+0800-codex-board-b-041404-tick-precision-closeout-v1`

This is a non-promoting readback of the completed `041404` LTF zero-trade
root-cause sidecar. It does not edit the Current Cursor, does not select
historical data, does not promote the LTF sidecar, and does not call
`update_goal`.

## Scope

The observed sidecar reused the `035511` LTF synthetic Auto-Quant workspace and
tested whether the zero-trade outcome came from absent signals or from the
Freqtrade market/precision execution shape.

## Evidence

- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/command-output/00_always_enter_probe.out`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/command-output/01_always_enter_result_keys.out`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/command-output/02_always_enter_tick_precision_probe.out`
- `docs/experiments/actionable-regime-confidence/runs/20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1/command-output/02_always_enter_tick_precision_probe.exit`

## Readback

- The first always-enter probe saw `373` precheck rows, `23` entry signals,
  `25` exit signals, and `0` entry/exit collisions, but the Freqtrade backtest
  still emitted `0` trades.
- The tick-size precision probe completed with exit `0`.
- The tick-size precision probe reported:
  - `precision_mode tick_size_amount_0.000001_price_0.01`
  - `backtest_trade_count 22`
  - `backtest_profit_pct 0.7400`
  - `backtest_sharpe 2.4936`
  - `backtest_win_rate_pct 54.5455`
  - `rejected_signals 0`
  - `timedout_entry_orders 0`
  - `canceled_entry_orders 0`
  - `left_open_trades_len 1`
  - `trades_len 22`

## Gate

- `diagnostic_only:tick_precision_unblocks_ltf_trade_creation`
- `blocked:user_selected_historical_data_missing`
- `not_promotable:always_enter_probe_not_regime_rooted_profit_factor`

## Next

Use the tick-size precision shape when the user-selected historical-data rerun
starts, but do not treat the always-enter diagnostic as profitability evidence.
The next qualifying run still requires explicit user selection of `HTF`, `MTF`,
or `LTF`, then nonzero mature rooted branch observations before
Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree can advance.
