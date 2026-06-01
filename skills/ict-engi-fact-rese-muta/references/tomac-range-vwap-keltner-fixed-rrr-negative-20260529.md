# TOMAC Range VWAP Keltner Fixed RRR Negative Screen, 2026-05-29

## Context

The user reiterated a preference for TOMAC data plus IBKR historical or paper
trade evidence. Same-turn claim audit still showed fresh active claims, so IBKR,
paper, provider, AutoQuant, and freqtrade launches were deferred. This slice was
a non-colliding local-only TOMAC screen.

## Branch Tested

- Factor id: `tomac_idxfut_range_vwap_keltner_fixed_rrr_1m_v1`
- Branch path: `RangeRegime -> LowEfficiencyChop -> SessionVwapKeltnerStretch -> FixedRrrMeanReversion -> tomac_idxfut_range_vwap_keltner_fixed_rrr_1m_v1`
- Data: retained TOMAC `NQ/YM/XAU` `1m` parquet with available `5m/15m/30m/1h/4h/1d` context.
- Gate: `5bps/side`, `10bps` round trip, cadence `0.333` to `3` trades/day, PF `>=1.10`, all available years positive, minimum `200` trades.
- Evidence root: `/tmp/ict-engine-tomac-range-vwap-keltner-rrr-20260529T162731+0800`
- Durable packet: `support/docs/experiments/actionable-regime-confidence/runs/20260529T162731+0800-codex-tomac-range-vwap-keltner-rrr-v1`

## Result

Local screen command exited `0` and copied evidence into the durable packet.

- `rows_tested=1152`
- `screen_gate_pass_count=0`
- `cadence_and_positive_5bps_count=0`
- `near_positive_count=0`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

The best row with actual trades was still strongly negative after honest cost:

- XAU long, `501` trades, `0.344804` trades/day, `net_5bps_side_total_return_pct=-61.900317`, `avg_net_bps_per_trade=-12.355353`, `profit_factor_5bps_side=0.002289`, `yearly_positive_count=0/5`.

## Lesson

On retained TOMAC `1m` OHLCV, range/chop VWAP-plus-Keltner fixed-RRR mean
reversion is not just sparse; when it reaches the requested cadence floor it is
decisively negative after `5bps/side` cost.

Do not rerun this exact branch unchanged or promote it as near-practical. A
future range/chop attempt must change a real source of edge, such as execution
surface, instrument, regime root, or fill model. If the next work claims high
frequency or mean reversion, prefer IBKR historical bid/ask, tick data, or paper
fills before AQ/downstream promotion, and keep practical flags false until the
full same-root live-usability chain passes.
