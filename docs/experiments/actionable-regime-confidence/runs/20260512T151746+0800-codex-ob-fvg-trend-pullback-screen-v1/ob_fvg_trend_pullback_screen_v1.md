# Order Block / FVG Trend-Pullback Screen v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T151746+0800-codex-ob-fvg-trend-pullback-screen-v1/`

Board: `docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md`

## Scope

This is a low-pollution screening pass for the user-supplied Order Block and Fair Value Gap concepts. It does not edit repo runtime code, does not start heavy Auto-Quant training, does not promote a strategy, and does not call `update_goal`.

The screen uses OHLCV-only approximations:
- `order_block_retest_continuation_v1`: last opposing candle before displacement, followed by retest and same-direction continuation.
- `fvg_retrace_continuation_v1`: three-candle gap, followed by retest and same-direction continuation.
- `ob_fvg_confluence_continuation_v1`: OB and FVG retest signals within 24 bars.
- `fvg_ob_pullback_resume_v1`: FVG retest after a recent same-direction OB signal.

Evidence class: `screen_only_ohlcv_proxy`. Promotion is not allowed from this packet.

## Inputs

Provider-backed normalized CSVs from `143900`:
- Binance `BTCUSDT` 1h: `76,429` bars, roundtrip cost `0.0008`
- IBKR `SPY` 1h: `20,034` bars, roundtrip cost `0.0004`
- Yahoo `ES` 1h: `11,383` bars, roundtrip cost `0.0004`

## Outputs

- Manifest: `summaries/ob_fvg_screen_manifest.json`
- Signal rows: `summaries/ob_fvg_signal_rows.csv`
- Provider/branch summary: `summaries/ob_fvg_summary.csv`
- Cross-provider branch aggregate: `summaries/ob_fvg_aggregate_by_branch.csv`
- Walk-forward fold summary: `summaries/ob_fvg_fold_summary.csv`
- Top candidates: `summaries/ob_fvg_top_candidates.csv`
- Script: `scripts/ob_fvg_trend_pullback_screen.py`

## Results

The screen emitted `24,504` total signals:

| Provider | Symbol | Bars | OB Signals | FVG Signals | Confluence Signals |
|---|---:|---:|---:|---:|---:|
| binance | BTCUSDT | 76,429 | 2,792 | 7,574 | 5,550 |
| ibkr | SPY | 20,034 | 645 | 3,355 | 1,762 |
| yahoo | ES | 11,383 | 402 | 1,471 | 953 |

Best provider-specific rows with at least 50 trades:

| Candidate | Branch Path | Trades | Win Rate | Avg Net Return | Profit Factor | Fold Readback |
|---|---|---:|---:|---:|---:|---|
| `fvg_ob_pullback_resume_v1` / Binance BTCUSDT | `range_or_de_risk->high_volatility->down_or_flat_momentum->fvg_ob_pullback_resume` | 122 | 0.5328 | 0.002398 | 1.3735 | 4/4 positive folds |
| `fvg_ob_pullback_resume_v1` / Yahoo ES | `trend_expansion->normal_volatility->down_or_flat_momentum->fvg_ob_pullback_resume` | 85 | 0.5059 | 0.001282 | 1.3432 | 2/4 positive folds |
| `order_block_retest_continuation_v1` / Binance BTCUSDT | `range_or_de_risk->high_volatility->up_momentum->order_block_retest_continuation` | 113 | 0.5221 | 0.001285 | 1.2037 | 3/4 positive folds |
| `fvg_retrace_continuation_v1` / Binance BTCUSDT | `trend_expansion->high_volatility->up_momentum->fvg_retrace_continuation` | 725 | 0.5007 | 0.000836 | 1.1125 | 3/4 positive folds |

Cross-provider aggregate is weaker:
- Best broad-coverage FVG row: `trend_expansion->normal_volatility->up_momentum->fvg_retrace_continuation`, `3` providers, `3,416` trades, profit factor `1.0042`.
- Best broad-coverage OB row: `trend_expansion->normal_volatility->up_momentum->order_block_retest_continuation`, `3` providers, `975` trades, profit factor `1.0372`.
- Broad provider support exists, but the edge mostly dilutes when BTCUSDT, SPY, and ES are pooled.

## Interpretation

Order Block and FVG are useful branch leaves, but this packet is not promotion evidence.

The strongest signal is not generic trend following. It is a pullback/resume nursery leaf:

```text
range_or_de_risk -> high_volatility -> down_or_flat_momentum -> fvg_ob_pullback_resume
```

That row is interesting because it has non-thin trade count, positive fold consistency, and better PF than the broad aggregate, but it is currently Binance/BTCUSDT-dominant. The provider-broad aggregates are mostly flat after costs, so the correct next action is not promotion; it is Auto-Quant routing for a smaller survivor set.

## Gate

- `support_once:151746_ob_fvg_trend_pullback_screen_v1`
- `evidence_class:screen_only_ohlcv_proxy`
- `pass:signals_generated_24504`
- `pass:three_provider_files_consumed`
- `partial:fvg_ob_pullback_resume_binance_high_vol_down_momentum_pf_1_3735`
- `partial:order_block_retest_binance_high_vol_up_momentum_pf_1_2037`
- `fail_closed:not_six_provider_aq_authority`
- `fail_closed:ohlcv_proxy_not_true_order_flow`
- `fail_closed:cross_provider_aggregate_edge_weak`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Next

Route only two survivor leaves into the next AQ-owned/provider-routed packet when capacity is free:

1. `fvg_ob_pullback_resume_v1`
2. `order_block_retest_continuation_v1`

Combine them with the existing `trend_pullback_resume_v1` and `volatility_breakout_follow_v1` branches, but keep `ob_fvg_confluence_continuation_v1` as a confirmation feature rather than a primary leaf until it improves provider-broad PF and fold consistency.
