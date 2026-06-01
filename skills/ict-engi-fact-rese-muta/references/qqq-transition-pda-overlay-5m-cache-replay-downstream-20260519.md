# QQQ transition/PDA overlay 5m cache-replay downstream readback (2026-05-19)

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

## Class lesson

When a 1m-origin branch fails but a higher-timeframe sibling has real-cost Gate 1 evidence, restart that sibling as its own exact timeframe root before downstream. Preserve the full branch path and do not let the sibling rescue the failed 1m root.

## Exact branch used

`US -> equity_etf -> QQQ -> 5m -> Trend -> SessionLiquidity -> intraday_micro_trend_reclaim_density -> ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1 -> transition_stability_pda_alignment_overlay_v1 -> stable_balanced_5m_exact`

## Evidence pattern

- Source Gate 1 row: retained IBKR/cache replay, `local_cache_replay=true`, `fresh_ibkr_live_ready=false`.
- `QQQ/5m stable_balanced`: 18 trades, raw `+1.25%`, win rate `61.1111%`, `+0.53%` after `2bps/side`, `-0.55%` after `5bps/side`.
- Full downstream mechanics ran: AQ import/prior, analyze, workflow, Pre-Bayes, structural target export, CatBoost train/apply, score import, trainer registration, runtime enablement, post-ranker analyze/workflow/Pre-Bayes/policy.
- Exact branch survived, path-ranker visible, but not used because validation was not ready.
- Execution failed closed: gate `observe`, branch `transition_guardrail`, `execution_readiness=0.09017100890267189`, `transition_hazard=0.9753777392009695`, `pda_hybrid_alignment=false`.

## Durable rule

A positive cache-replay sibling can justify downstream mechanical readback, but not live readiness or promotion. If the downstream blocker is PDA/hybrid disagreement plus extreme transition hazard, stop further near-identical transition overlays. The next candidate should target PDA sequence consistency and regime/factor direction agreement before repeating downstream.

## Classification

`exact_qqq_5m_cache_replay_downstream_fail_closed`

Promotion fields remain false:

- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
