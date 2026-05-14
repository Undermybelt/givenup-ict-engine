# AQ-First LTF Signal Diagnostic v1

Run id: `20260512T093150+0800-codex-board-b-aq-first-ltf-signal-diagnostic-v1`

Board B hash before this diagnostic artifact: `e94cb9264655beb01f747923e06b4052105706d6d148569fad0863e65d7a1d4c`.

## Scope

This is a non-promoting Board B nursery diagnostic over the existing `032157` / `035511` LTF synthetic Auto-Quant workspace. It does not select `HTF`, `MTF`, or `LTF` on behalf of the user, does not approve source/control evidence, does not run canonical merge, does not promote profitability, and does not call `update_goal`.

Source workspace:
- `docs/experiments/actionable-regime-confidence/runs/20260512T035511-codex-board-b-032157-ltf-synthetic-autoquant-v1/state_ltf_synthetic_autoquant_v1/.deps/auto-quant`

Source data:
- `user_data/data/B2RNQCOSTCRISISREPAIR032157_USD-1h.feather`

Prior AQ readback:
- `command-output/11_auto_quant_run_tomac_three_strategies.out`

## Command

Executed a read-only `uv run --with ta-lib python` diagnostic inside the source Auto-Quant workspace. The diagnostic loaded the 1h feather file, normalized millisecond timestamps, recomputed the `NQRootPulseMeanRevert` indicators, and counted post-startup entry/exit conditions.

## Readback

- Asset: `B2RNQCOSTCRISISREPAIR032157/USD`.
- Rows: `260`.
- Date span: `2025-12-15 12:00:00+00:00` to `2025-12-31 21:00:00+00:00`.
- Volume-positive rows: `260`; zero-volume rows: `0`.
- `NQRootPulseMeanRevert` mean-revert entry signals: `58` total, `55` after `startup_candle_count=30`.
- Post-startup exit signals under the same strategy logic: `142`.
- Prior Auto-Quant synthetic backtest completed `3` strategy runs with `0` command failures, but all three strategies reported `trade_count=0`.

First post-startup mean-revert entry examples:

```text
2025-12-17 16:00:00+00:00 close=27870.50 volume=100458 rsi7=15.064125
2025-12-17 17:00:00+00:00 close=27858.00 volume=65061 rsi7=14.606049
2025-12-17 18:00:00+00:00 close=27793.75 volume=46235 rsi7=12.353412
2025-12-17 19:00:00+00:00 close=27811.50 volume=37601 rsi7=16.503877
```

## Decision

Gate: `non_promoting_aq_feedback:signal_exists_trade_count_zero`.

The `035511` zero-trade result is not explained by missing local history, zero volume, or absent mean-revert entry signals. It is more likely an Auto-Quant/Freqtrade synthetic execution bridge issue or a strategy/backtest consumption issue. The next nursery slice should inspect why the synthetic backtester reports `0` trades despite post-startup signals, before adding more root families or treating the branch as economically dead.

Promotion: `false`.

`update_goal=false`.
