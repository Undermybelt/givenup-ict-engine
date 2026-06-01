# SI 5m true-1m context readback still fail-closed

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Date: 2026-05-20

Use this note when a retained-real lower-timeframe context repair looks like it
should promote an SI `5m` branch.

The IBKR `SI/5m` `RangeConsolidation -> TightRangeBandExpansionFade` branch
kept exact root identity and reran simulated-trade admission with true retained
`1m` context from real IBKR `SI 202607` rows:

- run root: `support/docs/experiments/actionable-regime-confidence/runs/20260520T070456+0800-codex-ibkr-si5m-tight-range-band-expansion-fade-1m-gate1-v1/simulated-trade-admission-si-5m-tight-range-band-expansion-fade-true-1m-context-20260520T135707+0800/`
- valid analyze subset: `1m=9453`, `5m=6047`, `15m=2016`, `30m=1008`, `1h=504`, `4h=136`; `1d=27/29` insufficient
- simulated feedback: `9` same-Auto-Quant-workspace trades, `7` wins and `2` losses
- CatBoost/path-ranker: trained, applied, registered, runtime enabled, exact branch visible

Verdict stays observation-only:

- `ranker_validation_ready=false`
- `raw_scored_mature=10/30`
- `production_validation=9/30`
- `observation_validation=9/30`
- `execution_candidate_status=no_trade`
- `execution_readiness=0.3719991181993223`
- `transition_hazard=0.9657999879763439`
- `pda_hybrid_alignment=false`
- `promotion_allowed=false`
- `trade_usable=false`

Rule: true lower-timeframe context can improve readback quality, but it does not
override validation readiness, PDA/range-family agreement, transition hazard, or
execution readiness gates. Do not repeat SI `5m` simulated-feedback replay or
stack light RVOL/VWAP/liquidity overlays under this same root unless the
hypothesis directly repairs mature validation, PDA alignment, transition hazard,
or execution candidate readiness.

## 2026-05-24 addendum

The later same-root simulated-admission replay with the true retained `1m`
context improved the readback but still failed closed:

- run root: `support/docs/experiments/actionable-regime-confidence/runs/20260520T070456+0800-codex-ibkr-si5m-tight-range-band-expansion-fade-1m-gate1-v1/simulated-trade-admission-si-5m-tight-range-band-expansion-fade-true-1m-context-20260524T153222+0800/`
- simulated feedback: `9` same-workspace trades, `7` wins, `2` losses, `0` breakevens
- analyze subset: `1m=9453`, `5m=6047`, `15m=2016`, `30m=1008`, `1h=504`, `4h=136`, `1d=27` insufficient
- readback: `exact_branch_survived=false`, `mature_rows=1`, `history_mature_rows=9`, `execution_candidate_status=no_trade`, `execution_readiness=0.4075716612293404`, `transition_hazard=0.6157999879763439`, `pda_hybrid_alignment=true`, `path_ranker_score_visible_to_execution_tree=true`, `path_ranker_score_used_by_execution_tree=false`

Lesson: true `1m` context can repair the readback shape, but it does not by
itself clear the admission trio. Keep this branch in observation/repair until
transition hazard drops, readiness rises, and mature validation fills.
