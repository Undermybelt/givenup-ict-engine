# Regime-rooted Gate 1 cost-density negative sample

Use when a regime-rooted profitability factor has real provider rows and Auto-Quant rank rows, but the small-timeframe origin is sparse or cost-fragile.

## Session pattern

Branch tested:

```text
RangeReversion -> VwapDeviationFade -> zscore_vwap_reclaim -> yf_etf_vwap_deviation_mean_reversion_1m_mtf_v1
```

Provider/AQ evidence:

- provider: yfinance/YF
- symbols: SPY, QQQ, IWM, SMH
- timeframes: 1m, 5m, 15m, 30m, 1h
- local_cache_replay=false
- provider fetches, strategy compile, Auto-Quant material batch, dispatch, and rank exited 0
- branch fields preserved

Gate result:

- rank_rows=20
- rank_total_trade_count=5
- origin_trades_1m=5
- positive_origin_1m=[]
- positive_higher_timeframes=[]
- positive_origin_after_2bps=[]
- cost_gate_survives=false
- dense_positive_gate=false

Decision:

```text
drop_small_cycle
```

Do not continue to Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution tree when Gate 1 fails this way. Preserve it as a source-backed negative/suppression sample only.

## Durable rule

For strict profitability-factor training, a real provider + AQ success is not enough. If the 1m-origin lane has no positive cost-stressed rows after 1-2 bps/side, stop at Gate 1 and pivot to a denser factor family. Do not add overlays to rescue a sparse root; overlays must compound an already evidence-earning first profit factor, not manufacture density.
