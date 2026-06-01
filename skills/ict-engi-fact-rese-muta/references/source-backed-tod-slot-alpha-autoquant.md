# Source-backed TOD slot alpha to Auto-Quant

Use when the user asks to stop local parameter grinding and source higher-quality intraday factors from papers/repos/blogs/social material before Auto-Quant.

## Source class

- Academic source: Heston / Korajczyk / Sadka, same-time-of-day intraday return seasonality, DOI `10.1111/j.1540-6261.2010.01559.x`.
- Community/blog source: RobotWealth intraday seasonality. Treat blog material as hypothesis only.
- Candidate branch shape:
  `Range -> IntradaySeasonality -> same_time_slot_alpha -> <profit_factor>`

## Auto-Quant implementation pattern

1. Fetch real provider bars for a small ETF basket first, e.g. `SPY/QQQ/IWM`.
2. Use `1m` as base/origin when available, and also test `5m/15m/30m/1h` lanes separately.
3. For each bar, compute slot by session minute.
4. Compute `slot_alpha` from shifted prior same-slot returns only; never include the current bar.
5. Pair the slot signal with practical filters:
   - VWAP/EMA direction confirmation;
   - slot-relative volume sanity (`rvol_slot`), not raw volume alone;
   - range/ATR sanity to avoid noisy bars;
   - RSI/momentum bounds to avoid already-stretched bars.
6. Preserve source metadata, DOI/blog URL, provider provenance, and full regime-profit branch path in every material file.
7. Rank in Auto-Quant before downstream. Do not treat the paper/blog as proof.

## Observed session result

Run shape:
- Provider: yfinance/YF.
- Symbols: `SPY/QQQ/IWM`.
- Lanes: `1m/5m/15m/30m/1h`.
- Branch: `Range -> IntradaySeasonality -> same_time_slot_alpha -> yf_etf_tod_slot_alpha_1m_mtf_v1`.

Gate 1 result:
- `15` ranked rows.
- `452` total trades.
- `10` positive rows with at least `8` trades.
- Strong examples: `IWM/30m`, `IWM/15m`, `QQQ/5m`, `SPY/15m`, `QQQ/15m`.
- Cost stress at `2bps/side` survived on multiple higher-timeframe rows.

Important blocker:
- `1m` origin rows had zero trades. Classify as medium-timeframe seasonal edge, not 1m execution proof.
- Downstream ran through AQ import, BBN prior init, analyze, workflow, Pre-Bayes, structural target export, and policy readback, but CatBoost stopped with `Target contains only one unique value`.
- Execution candidate stayed `actionable=false`, `candidate_status=no_trade`.

## Decision rule

If TOD slot alpha has dense positive `5m/15m/30m/1h` evidence but zero `1m` trades:

- keep as `source_backed_scoped_candidate` or `gate1_positive_cost_survives_downstream_catboost_single_class_blocker`;
- do not promote or claim live readiness;
- next slice should be either:
  - a denser 1m-origin formulation, or
  - walk-forward bucket validation on the same medium-timeframe seasonal edge.

## Pitfalls

- Slot alpha is highly overfit-prone; require shifted prior same-slot returns and walk-forward validation.
- Do not let high Sharpe on a few medium-timeframe rows bypass cost stress.
- Do not send a single-label downstream target into CatBoost as promotion evidence; record it as a real blocker and keep Gate 1 evidence separate.
- Blog/social explanations are hypothesis sources only; proof starts at provider rows and Auto-Quant ranks.
