# IBKR MNQ 1m compression breakout + session-liquidity overlay fail-closed (2026-05-20)

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

## Branch
`FUTURES -> equity_index -> MNQ -> 1m -> TrendExpansion -> CompressionBreakout -> ibkr_mnq1m_compression_breakout_7d_gate1_v1 -> ibkr_mnq1m_compression_breakout_session_liquidity_overlay_7d_gate1_v1`

## What worked
- Real IBKR 7D `MNQ` 1m-rooted Gate 1 packet preserved the exact regime/profit-factor path.
- Session-liquidity overlay kept enough cost-stressed rows for downstream admission.
- Best Gate 1 rows:
  - `session_liquidity_mid_compression_n45`: trades=8, raw=+1.00%, 2bps/side=+0.68%, 5bps/side=+0.20%.
  - `session_liquidity_mid_breakout_n120`: trades=7, raw=+0.77%, 2bps/side=+0.49%, 5bps/side=+0.07%.
  - `session_liquidity_late_trim_n45`: trades=11, raw=+0.84%, 2bps/side=+0.40%.
  - `session_liquidity_slope_align_n45`: trades=13, raw=+0.57%, 2bps/side=+0.05%.
- Downstream replay commands mostly completed and exact branch survived.
- `pre_bayes_allowed=true`, `bbn_allowed=true`, `catboost_allowed=true` after ranker/runtime plumbing.

## Decisive blocker
- `execution_readiness=0.0`
- `transition_hazard=1.0`
- `pda_hybrid_alignment=false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
- `closed_loop_branch_admission.status=fail_closed`
- Path-ranker target stayed immature: `mature_rows=0`, `raw_scored_mature=0/30`, `production_validation=0/30`, `observation_validation=0/30`.

## Durable lesson
A session-liquidity overlay can preserve Gate 1 density/cost on a 1m compression-breakout futures branch without moving the actual execution predicates. If the downstream blocker trio remains `transition_hazard >= 0.60`, `pda_hybrid_alignment=false`, or `execution_readiness < 0.65`, do not stack another near-equivalent liquidity/crowding overlay.

Next same-root candidate should directly target execution-predicate movement, e.g. `VWAP reclaim + reclaim persistence + transition guard`, while still preserving cost-stressed density. If it cannot improve the blocker trio, keep the branch as observation only and pivot to a materially different exact-root family.
