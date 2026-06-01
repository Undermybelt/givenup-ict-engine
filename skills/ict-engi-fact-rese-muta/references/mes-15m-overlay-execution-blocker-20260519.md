# MES 15m rooted overlay execution blocker (2026-05-19)

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

## Context
User goal: profitability factors must remain rooted by exact market/product/symbol/timeframe/regime path. First profit factor sits under the regime branch; later profit factors are overlays under that factor. AQ -> Pre-Bayes/BBN/CatBoost/execution tree must preserve the same branch path. Do not lower gates.

## Base branch
`FUTURES -> equity_index -> MES -> 15m -> TrendExpansion -> MicroTrendPullbackReclaim -> ibkr_mes_15m_micro_trend_pullback_reclaim_exact_v1`

Gate 1 source:
- run: `20260519T233231+0800-codex-ibkr-mes-15m-micro-trend-pullback-reclaim-exact-gate1-v1`
- survivor: `MES/balanced/15m`
- trades: `23`
- raw: `+1.40%`
- `2bps/side`: `+0.48%`
- `5bps/side`: `-0.90%`
- downstream allowed at Gate 1: true

Downstream:
- script: `run_ibkr_mes_15m_micro_trend_pullback_reclaim_exact_downstream_v1.py`
- commands exited 0 through AQ import, Pre-Bayes, CatBoost/path-ranker, execution tree readbacks
- decision: `exact_mes_15m_downstream_fail_closed`
- Pre-Bayes: `pass_neutralized`
- execution_readiness: `0.47884576457689876`
- transition_hazard: `0.9516058661705619`
- pda_hybrid_alignment: `false`
- execution tree: `observe`, `transition_guardrail`

## Overlay branch tested
`FUTURES -> equity_index -> MES -> 15m -> TrendExpansion -> MicroTrendPullbackReclaim -> ibkr_mes_15m_micro_trend_pullback_reclaim_exact_v1 -> ibkr_mes_15m_pda_transition_stability_overlay_v1`

Gate 1 overlay:
- script: `run_ibkr_mes_15m_micro_trend_pda_transition_overlay_gate1_v1.py`
- run: `20260519T235008+0800-hermes-ibkr-mes-15m-micro-trend-pda-transition-overlay-gate1-v1`
- provider rows: IBKR MES 202606 15m, `1997`, source-provider-root reused from base packet, no fabricated cache
- survivor: `MES/pda_soft/15m_pda_overlay`
- trades: `19`
- raw: `+0.86%`
- `1bps/side`: `+0.48%`
- `2bps/side`: `+0.10%`
- `5bps/side`: `-1.04%`
- branch fields preserved: true
- downstream_allowed: true

Overlay downstream:
- script: `run_ibkr_mes_15m_micro_trend_pda_transition_overlay_downstream_v1.py`
- run: `downstream-exact-mes-15m-pda-transition-overlay-20260519T235220+0800`
- commands exited 0 through AQ import, Pre-Bayes, ranker, execution tree readbacks
- decision: `exact_mes_15m_pda_overlay_downstream_fail_closed`
- exact_branch_survived: true
- Pre-Bayes/BBN/CatBoost/execution_tree allowed mechanically: true
- execution_readiness: `0.0`
- transition_hazard: `1.0`
- pda_hybrid_alignment: `false`
- promotion_allowed/trade_usable: false

## Durable lesson
If an exact rooted branch passes Gate 1 cost/density but execution tree fails due to transition/PDA predicates, one PDA/transition overlay is worth trying only if it preserves density. If the overlay survives Gate 1 but downstream still reports `transition_hazard >= 0.60`, `pda_hybrid_alignment=false`, or `execution_readiness < 0.65`, stop adding same-timeframe overlays. Treat it as observation and pivot to a denser `1m`/`5m` exact root or a different market cell.

Do not describe `workflow actionable_artifacts` or `promote_candidate=true` as live readiness when execution predicates fail. Execution predicates override mechanical downstream success.
