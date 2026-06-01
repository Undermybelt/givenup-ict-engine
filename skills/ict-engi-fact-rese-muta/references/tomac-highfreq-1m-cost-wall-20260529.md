# TOMAC 1m High-Frequency Cost Wall, 2026-05-29

## Context

The user asked to explore a higher-cadence profitability factor, roughly 20 to
800 trades per day, while still preferring TOMAC data plus IBKR historical or
paper-trade evidence and without lowering gates.

Current Board B state had a fresh active TOMAC clean-AQ claim plus a later live
TOMAC process, so the safe work slice was a non-colliding local screen over
retained TOMAC parquet data only.

## Branch Tested

- Factor id: `tomac_idxfut_highfreq_microburst_liquidity_1m_v1`
- Branch path: `MicrostructureRegime -> OneMinuteBurstLiquidity -> MtfVolatilityAdmission -> MicroburstContinuationOrRejection -> HighFrequencyCadence20to800d -> tomac_idxfut_highfreq_microburst_liquidity_1m_v1`
- Data: retained TOMAC `NQ/YM/XAU` `1m` parquet, with real `5m/15m/30m/1h/4h/1d` context where available.
- Screen families: `MicroburstContinuation`, `MicroburstRejection`, `CompressionBreakExpansion`.
- Historical cost stress used by the original screen: fixed `5bps/side`,
  `10bps` round trip. This is retained as stress evidence only; it is not the
  correct primary commission model for futures. Future futures reruns must use a
  product-specific per-contract cost model with source URL/date.
- Evidence root: `/tmp/ict-engine-tomac-highfreq-microburst-liquidity-20260529T160425+0800`
- Durable packet: `support/docs/experiments/actionable-regime-confidence/runs/20260529T160425+0800-codex-tomac-highfreq-microburst-liquidity-v1`

## Result

Local screen command exited `0`; clean rerun exited `0` with `stderr_bytes=0`.

- `candidate_rows=1860`
- `highfreq_rows_20_to_800_per_day=563`
- `positive_highfreq_5bps_rows=0`
- `local_screen_survivors=0`
- Decision: `drop_local_highfreq_no_5bps_survivor_in_20_to_800_per_day_band`
- Practical flags: `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`

Representative high-cadence rows:

- XAU `MicroburstContinuation`, MTF `ladder_5m15m1h`, hold 1: `25,866` trades, `20.08/session`, gross `+20.02%`, net5bps `-2566.58%`, avg gross `+0.077bps/trade`, avg net `-9.923bps/trade`.
- YM `MicroburstContinuation`, MTF `ladder_5m15m1h`, hold 1: `26,105` trades, `20.22/session`, gross `+7.25%`, net5bps `-2603.25%`, avg gross `+0.028bps/trade`, avg net `-9.972bps/trade`.
- NQ `CompressionBreakExpansion`, MTF `fast_5m15m`, hold 5: `26,304` trades, `20.36/session`, gross `+8.52%`, net5bps `-2621.88%`, avg gross `+0.032bps/trade`, avg net `-9.968bps/trade`.

Rehearing note after the futures cost-model repair: the NQ representative row is
not a bps false negative. At a representative `15000` NQ price, verified
commission-only is about `$4.50` round turn, roughly `0.15bps`; the wrapper's
explicit all-in assumption is about `$19.50`, roughly `0.65bps`. The row's
gross edge is only about `0.032bps/trade`, so commission-only still loses about
`-31%` and all-in loses about `-163%` over `26,304` trades. Low futures
commissions do not rescue this zero-edge churn. The real bps-stress false
negative bucket is rows with gross edge above verified all-in cost but below the
old fixed `5bps/side` stress.

## Lesson

For retained TOMAC `1m` OHLCV, simple 20-800 trades/day bar-level high-frequency
strategies did not fail because of density in this historical stress run; they
failed because the per-trade gross edge was near zero. Because the stress used a
notional `10bps` round-trip model, do not reuse its terminal decision as a
futures commission verdict without recomputing product-specific per-contract
fees.

Do not keep parameter-grinding this exact shape. More thresholds on one-minute
bursts, failed excursions, compression breakouts, and simple MTF slope filters
are likely to rediscover the same cost wall.

The next materially different high-frequency attempt should change the evidence
surface, not lower the gate:

- Use IBKR historical ticks, bid/ask, or paper fills to measure spread,
  slippage, queue/latency, and sub-minute execution truth.
- Or use an explicitly lower-cost instrument/execution venue with real fee and
  fill evidence.
- Or keep TOMAC 1m only as a coarse prefilter and require a downstream tick/fill
  simulator before any AQ, paper, Pre-Bayes, BBN, path-ranker, execution-tree,
  promotion, or trade-use handoff.

Until such evidence exists, classify this branch family as Python-only
fail-closed evidence. No Auto-Quant, IBKR paper/sim, downstream, promotion,
trade usability, or goal completion follows from it.
