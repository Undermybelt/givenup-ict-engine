# VWAP reclaim provider-fallback Gate 1

Session lesson from testing a source-backed VWAP reclaim/deviation candidate after the high-window reclaim branch remained execution-tree observe-only.

## Branch shape

Preserve regime-rooted path:

`TrendExpansion -> VWAPReclaim -> rolling_vwap_reclaim_30m -> tv_cross_symbol_vwap_reclaim_30m_probe_v1`

Required metadata fields:

- `branch_path`
- `regime_profit_branch_path`
- `main_regime=TrendExpansion`
- `sub_regime=VWAPReclaim`
- `sub_sub_regime_or_profit_factor=rolling_vwap_reclaim_30m`
- `profit_factor=tv_cross_symbol_vwap_reclaim_30m_probe_v1`
- `provider_parity=fallback_only_not_ibkr_live_ready` when using TradingViewMCP/YF after IBKR timeout

## Candidate logic

OHLCV-only 30m rolling VWAP reclaim:

- provider source in this run: TradingViewMCP fallback 30m, not IBKR parity;
- symbols: NVDA, SMH, XLK, IWM, QQQ, SPY;
- rolling VWAP20 from typical price and volume;
- entry: close crosses above `rolling_vwap20 * 1.001` from prior bar below/near VWAP;
- trend context: `close > EMA50` and `EMA20 >= EMA50 * 0.995`;
- not chase: `close < prior_high_40 * 1.012`;
- quality: RSI 48-72, volume >= 0.80 * SMA20(volume), ATR/close < 0.030;
- long-only, ROI around 1.6%, stop around 1.4%, trailing offset around 1.4%.

## Observed Gate 1 result

Auto-Quant run root:

`/tmp/ict-engine-runs/20260518T104810+0800-hermes-tv-vwap-reclaim-30m-aq-v1`

Rank rows:

- SPY: 1 trade, +0.46%, win 100%, Sharpe placeholder -100 due one trade;
- SMH: 4 trades, +1.80%, win 75%, Sharpe 1.3687;
- XLK: 3 trades, +0.20%, win 66.67%, Sharpe 0.1592;
- QQQ: 3 trades, +0.18%, win 66.67%, Sharpe 0.1433;
- IWM: 2 trades, +0.35%, win 50%, Sharpe 1.6222;
- NVDA: 1 trade, -0.66%, win 0%, Sharpe placeholder -100.

Basket raw: 14 trades, +2.33%, 5/6 positive.

Approx cost stress from AQ rank total minus entry+exit bps:

- 0 bps/side: +2.33%;
- 1 bps/side: +2.05%;
- 2 bps/side: +1.77%;
- 5 bps/side: +0.93%;
- 10 bps/side: -0.47%.

## Verdict language

Correct classification:

- `incubate_sourced_candidate`
- `candidate_positive_but_provider_fallback_only`
- `do_not_handoff_to_BBN_CatBoost_tree_until_IBKR_or_native_provider_validation`

Do not call this promotion/live-ready because:

- provider was TradingViewMCP fallback after IBKR timeout;
- trade count was sparse;
- NVDA failed;
- 10 bps stress flipped negative;
- no same-branch downstream maturity exists.

## Next step

Retry the same VWAP reclaim package on real IBKR 30m or native feasible IBKR smaller window. If IBKR remains blocked, keep it as watchlist/incubate and move to the next source-backed candidate such as gap fade/go or pair z-score.
