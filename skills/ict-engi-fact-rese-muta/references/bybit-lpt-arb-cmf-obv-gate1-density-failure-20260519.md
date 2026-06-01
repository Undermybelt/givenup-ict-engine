# Bybit LPT/ARB CMF/OBV breakout Gate 1 density failure — 2026-05-19

## Context
Continuation of regime-rooted profitability-factor training under the class-level rule:

`market -> product -> symbol -> base_timeframe -> main_regime -> sub_regime -> ... -> first_profit_factor -> optional_profit_factor_overlays...`

Tested branch:

`crypto -> bybit_linear_perp -> LPT_ARBUSDT -> 1m -> TrendExpansion -> BybitMidcapAccumulationBreakout -> cmf_obv_accumulation_breakout_1m_mtf -> bybit_lpt_arb_cmf_obv_breakout_1m_mtf_v1`

Run root:

`<ict-engine-repo>/support/docs/experiments/actionable-regime-confidence/runs/20260519T135842+0800-hermes-bybit-lpt-arb-cmf-obv-breakout-1m-mtf-v1`

Primary artifacts:

- `checks/terminal_metrics.json`
- `checks/cost_stress.json`
- `summaries/terminal_decision_summary.md`
- external claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/hermes-bybit-lpt-arb-cmf-obv-breakout-1m-mtf-v1.claim`

## Result

Auto-Quant and provider flow completed far enough for a real Gate 1 verdict:

- `provider_count=13`
- `rank_rows=13`
- `rank_total_trade_count=10`
- `branch_fields_preserved=true`
- `origin_1m_cost_survivors_2bps_side=[]`
- `any_cost_survivors_2bps_side=[]`
- `decision=drop_gate1_cost_or_density_failed`
- `downstream_allowed=false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

Observed sparse positives:

- LPT 30m: 4 trades, gross +1.27%, 2bps/side net +1.11% — below >=6-trade minimum.
- LPT 1h: 1 trade — too sparse.
- ARB 5m: 2 trades — too sparse.
- LPT/ARB 1m: 0 trades — no origin survivor.

Minor provider/validation issues:

- ARB 1h fetch exit=1.
- LPT/ARB 1d validate exit=1.

These were not the decisive blocker; the decisive blocker was cost/density failure at the 1m origin and all surviving HTF samples being too sparse.

## Durable lesson

For crypto Bybit CMF/OBV accumulation-breakout factors, higher-timeframe sparse positives are not enough to justify downstream. Even when branch metadata is preserved and provider/AQ run cleanly, stop at Gate 1 if:

- 1m origin has zero trades or no 2bps/side survivor;
- HTF positive rows have fewer than the minimum trade-count floor (normally >=6 for subclass evidence; higher for origin promotion);
- total ranked trades are too thin to support Pre-Bayes/BBN/CatBoost/execution-tree.

Do not treat 30m/1h single-digit wins as rescue evidence for a failed 1m origin root. Choose a materially denser 1m entry family instead.

## Suggested next factor shape

Pivot away from strict CMF/OBV breakout on LPT/ARB. Prefer a denser 1m crypto family:

- VWAP reclaim + RSI/OBV snapback with relaxed trend filter;
- micro-liquidity reclaim after compression with volume floor but no hard 42-bar range breakout;
- session/time-of-day density gate where the provider has continuous 1m candles;
- cost-stress first, then only downstream if 1m survives.
