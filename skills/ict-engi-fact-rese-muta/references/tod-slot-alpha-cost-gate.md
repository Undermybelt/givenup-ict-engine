# Same-time-of-day slot alpha cost gate

Use this note when testing intraday seasonality / same-time-of-day slot alpha factors through Auto-Quant and ict-engine downstream gates.

## Session pattern

Branch shape used:

- `TrendContinuation -> IntradaySeasonality -> same_time_of_day_slot_alpha -> ibkr_qqq_tod_slot_alpha_mtf_v1`
- provider: IBKR QQQ retained native bars
- ladder: `1m`, `5m`, `15m`, `30m`, `1h`
- rule class: walk-forward slot mean by clock-minute/hour, with trend/rvol/ATR gates

Auto-Quant Gate 1 can report strong-looking low-timeframe rows:

- 5m example: 32 trades, 81.25% win rate, +1.03% total profit, Sharpe 8.50, PF 2.68
- 1m/15m/1h may show small positive rows

But local cost replay showed the edge was micro and friction-sensitive:

- 5m: +0.98% at 0 bps/side, -0.70% at 1 bps/side, -2.38% at 2 bps/side
- 1m: +0.15% at 0 bps/side, -1.29% at 1 bps/side
- 30m vector proxy barely survived 2 bps/side, but the actual AQ 30m row was negative/sparse

Downstream also failed closed:

- BBN prior/import could be applied
- CatBoost training failed due constant/ignored features and one usable training sample
- execution tree stayed `observe / transition_guardrail / guarded`
- ranker was not used by execution tree
- maturity gates remained far short: `raw_scored_mature=1/30`, `production_validation=0/30`, `observation_validation=0/30`

## Durable rule

For same-time-of-day slot alpha and other intraday seasonal micro-edges:

1. Treat AQ-positive low-timeframe rows as discovery only.
2. Run cost stress before promotion, with at least 1/2/5 bps per side.
3. If the best AQ row flips negative at 1 bps/side, terminalize as `cost_fragile` even if AQ PF/Sharpe look high.
4. If a higher-timeframe vector replay survives cost but the matching AQ row is sparse or negative, do not promote the vector proxy.
5. Continue to BBN/CatBoost/execution-tree only as fail-closed parity evidence unless cost-stressed AQ rows remain positive and maturity gates are reachable.

## Preferred next move after failure

Do not keep tuning micro slot thresholds. Move to lower-turnover, larger-expectancy candidates:

- 52-week-high + intraday reclaim
- 30m MACD trend-compression baseline over wider IBKR windows and sibling symbols
- other sourced factors with fewer trades and larger average return per trade
