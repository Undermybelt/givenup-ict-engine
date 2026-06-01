# Source-backed candidate triage after provider blocker

Session lesson from continuing ict-engine factor discovery after the matured IBKR high-window reclaim branch became execution-tree `observe` and fresh IBKR 30m fetches timed out.

## Context

Primary matured branch remained:

`TrendExpansion -> BreakoutPersistence -> high_window_reclaim_30m -> ibkr_cross_symbol_high_window_reclaim_30m_v1`

Execution-tree readback stayed exact-branch but fail-closed:

- `branch=transition_guardrail`
- `gate_status=observe`
- `execution_bias=guarded`
- `ranker_validation_ready=true`
- `closed_loop_actionable=false`

Fresh IBKR forward probes timed out for 30m 30D all-symbol and 30m 7D QQQ retry. TradingViewMCP worked as fallback for 5m/15m/30m/1h, but all fallback results were marked `provider_parity=fallback_only_not_ibkr_live_ready`.

## Candidate board

### 1. High-window reclaim 30m

Status: best matured branch.

Evidence already existed from IBKR + Auto-Quant + cost stress + BBN/CatBoost/tree handoff. Current forward watchlist showed no live entry on latest regular TradingViewMCP 5m/15m/30m/1h bars. Keep observing; do not demote just because fallback watchlist has no current trigger.

### 2. VWAP reclaim 30m

Branch:

`TrendExpansion -> VWAPReclaim -> rolling_vwap_reclaim_30m -> tv_cross_symbol_vwap_reclaim_30m_probe_v1`

Auto-Quant Gate1 on TradingViewMCP fallback 30m:

- 5/6 symbols positive;
- basket raw +2.33%;
- 14 trades;
- approximate stress stayed positive through 5 bps/side, failed at 10 bps/side;
- NVDA was negative and several cells were sparse.

Verdict: incubate only. It is a source-backed candidate worth native IBKR retry or broader native window, but not downstream BBN/CatBoost/tree promotion while it is TradingViewMCP fallback-only and sparse.

### 3. Gap-and-go 30m

Branch:

`TrendExpansion -> GapContinuation -> gap_go_30m -> tv_cross_symbol_gap_go_30m_probe_v1`

Auto-Quant Gate1 on TradingViewMCP fallback 30m returned zero trades on all six symbols.

Verdict: Gate1 factor failure, not provider failure. Drop or materially rework; do not hand off downstream.

### 4. Pair z-score relative value 30m

Branch:

`RangeCompression -> RelativeValueDislocation -> pair_zscore_30m -> tv_cross_pair_zscore_reversion_30m_probe_v1`

Pairs tested: NVDA/SMH, XLK/QQQ, QQQ/SPY, IWM/SPY. Auto-Quant Gate1 returned zero trades across all pairs.

Verdict: Gate1 factor failure for this parameterization/window. Drop or rework thresholds/window; do not hand off downstream.

### 5. Same-time-of-day slot alpha 30m

Branch:

`RangeCompression -> IntradaySeasonality -> same_time_slot_alpha_30m -> tv_cross_symbol_slot_alpha_walkforward_30m_probe_v1`

Walk-forward diagnostic on TradingViewMCP fallback 30m:

- slots learned from prior days only;
- trigger if prior cross-symbol slot mean > 8 bps and sample count >= 12;
- 312 diagnostic trades.

Cost stress:

- 0 bps/side: +13.1329%, PF 1.2209;
- 1 bps/side: +6.8929%, PF 1.1110;
- 2 bps/side: +0.6529%, PF 1.0100;
- 5 bps/side: -18.0671%, PF 0.7590.

Verdict: diagnostic positive but cost-fragile. Do not promote. If pursued, convert to an Auto-Quant native lane only after reducing turnover with top-slots-only, regime/trend filter, or larger timeframe gate.

## Durable workflow rule

When fresh IBKR is blocked but a fallback provider works:

1. Use fallback only for watchlist telemetry and candidate discovery.
2. Preserve `provider_parity=fallback_only_not_ibkr_live_ready` in summaries/material metadata.
3. Run source-backed candidates through small AQ Gate1 slices, but stop before BBN/CatBoost/tree unless native-provider or provider-parity evidence exists.
4. Terminalize zero-trade AQ rows as factor-gate failures when fetch and dispatch succeeded.
5. For dense intraday diagnostics, run cost stress before writing an AQ material; if 5 bps/side flips negative, classify as cost-fragile and require a turnover-reduction filter first.

## Promotion gate

A fallback-only candidate needs all of the following before downstream handoff:

- native IBKR or explicit provider-portability validation;
- at least two stable positive symbols/pairs with non-sparse trades;
- per-side cost stress positive at 0/1/2/5 bps;
- regime-root branch metadata preserved in material and rank rows;
- no worse sibling-provider or core-symbol failure hidden in the basket.
