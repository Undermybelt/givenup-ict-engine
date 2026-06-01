# IBKR XLI Vortex/VI Gate 1 no-survivor with partial higher-frame timeout

Use under `ict-engi-fact-rese-muta` when continuing IBKR stock `1m`-root
profitability-factor training that builds a full MTF ladder, but the exact
`1m` economics fail even though several higher frames fetch successfully.

## Branch

`TrendExpansion -> IndustrialsSectorTrendContinuation -> VortexViMomentumConfirmation -> ibkr_xli1m_vortex_vi_industrials_trend_gate1_v1`

## Durable lesson

- A partial context-frame timeout does not automatically block a lawful exact
  Gate 1 verdict if the exact `1m` root and enough surrounding context already
  exist to score the claimed branch.
- In this `XLI` run, `1m/5m/15m/1h/4h/1d` all landed, `30m 6M` timed out with
  `exit=124`, and the wrapper still terminalized correctly with
  `decision=drop_gate1_no_exact_1m_5bps_survivor`.
- Do not promote or relaunch just because some higher frames succeeded. Exact
  `1m` economics remain the root authority for this branch.
- Do not claim Auto-Quant, Bayes, BBN, CatBoost, or execution-tree readiness
  when `auto_quant_started=false` and `exact_1m_survivors_5bps=[]`.

## Evidence pattern

- exact `1m 30D`: `11,330` rows
- `5m 2M`: `3,281` rows
- `15m 3M`: `1,614` rows
- `30m 6M`: timeout after `240s`, no file
- `1h 1Y`: `1,882` rows
- `4h 2Y`: `1,204` rows
- `1d 3Y`: `751` rows

Exact `1m` cost stress:

- `vi_dense`: `441` trades, `5bps/side=-62.6384%`
- `vi_balanced`: `382` trades, `5bps/side=-44.2098%`
- `vi_quality`: `285` trades, `5bps/side=-38.7881%`
- `vi_reclaim`: `382` trades, `5bps/side=-57.2627%`

## Workflow rule

1. Record the timed-out context frame explicitly in terminal metrics.
2. Keep the branch fail-closed if every exact `1m` variant is negative at the
   required cost gate, even when higher frames look healthy.
3. Treat the timeout as a provider/runtime lesson and the negative exact-root
   economics as the factor verdict. Do not blur them together into a fake
   “provider blocked” outcome.
4. Future retries should only happen if the branch logic materially changes or
   the provider timeout path itself is the target of repair. A clean re-run
   without branch change is not evidence of progress.
