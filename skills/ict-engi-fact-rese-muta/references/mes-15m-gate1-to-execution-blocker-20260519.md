# MES 15m Gate 1 survivor -> execution blocker (2026-05-19)

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

## Context
- Class: ict-engine live-profit factor training.
- Exact rooted branch:
  `FUTURES -> equity_index -> MES -> 15m -> TrendExpansion -> MicroTrendPullbackReclaim -> ibkr_mes_15m_micro_trend_pullback_reclaim_exact_v1`
- Source Gate 1 run:
  `support/docs/experiments/actionable-regime-confidence/runs/20260519T233231+0800-codex-ibkr-mes-15m-micro-trend-pullback-reclaim-exact-gate1-v1`
- Downstream run:
  `.../downstream-exact-mes-15m-micro-trend-pullback-reclaim-20260519T233720+0800/checks/downstream_metrics.json`

## Gate 1 result
- Selected lane: `MES/balanced/15m`
- Trades: `23`
- Win rate: `52.1739%`
- Raw total: `+1.40%`
- Cost stress:
  - `1bps/side`: `+0.94%`
  - `2bps/side`: `+0.48%`
  - `5bps/side`: `-0.90%`
- Gate 1 decision: downstream allowed, but not promotion.

## Downstream readback
- All downstream commands exited `0` through Auto-Quant import, Pre-Bayes, workflow readback, CatBoost/path-ranker train/apply/register/enable, and execution-tree readback.
- Pre-Bayes gate: `pass_neutralized`
- Posterior: active regime `range`, confidence `0.775240580639643`
- Execution candidate: `actionable=false`, status `no_trade`
- `execution_readiness=0.47884576457689876`
- `transition_hazard=0.9516058661705619`
- `pda_hybrid_alignment=false`
- Execution tree: gate `observe`, branch `transition_guardrail`, hint `execution_guarded_due_to_pda_hybrid_disagreement`
- Policy rows were not mature: `mature_rows=0`, `history_mature_rows=0`, `training_weight_rows=0`

## Durable lesson
When a rooted branch passes Gate 1 and downstream mechanics all execute, but execution tree fails on high transition hazard / PDA disagreement / low readiness, do not call it live-ready and do not loosen thresholds. Preserve the branch as an observation sample and repair the same-root execution blocker directly.

Preferred next experiment shape:
`same market/product/symbol/timeframe/regime/profit-factor -> PDA/transition-hazard guard overlay`

The overlay must first re-run Gate 1 and preserve cost/density before another downstream pass. If the overlay kills density or flips 1-2bps cost survival, drop the overlay and pivot to a denser exact-root family (`MES 1m/5m`) rather than rescuing the branch with lower gates.
