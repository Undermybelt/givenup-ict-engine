# M2K Subset Materialization Timeout Fail-Closed (2026-05-21)

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use when continuing same-root M2K RVOL/PDA repair work after a real cost
survivor exists but execution materialization/readiness is still blocked.

## Evidence

- Run root:
  `<ict-engine-repo>/support/docs/experiments/actionable-regime-confidence/runs/20260521T191327+0800-codex-m2k-analyze-materialization-subset-diagnostic-v1`
- Source run:
  `support/docs/experiments/actionable-regime-confidence/runs/20260521T184916+0800-codex-m2k-rvol-pda-fresh14d-ladder-readback-v1`
- Branch:
  `RangeReversion -> LiquiditySweepRejectShort -> ibkr_m2k1m_liquidity_sweep_reject_short_7d_gate1_v1 -> ibkr_m2k1m_liquidity_sweep_reject_short_rvol_pda_guard_pda_consistency_floor_v1`

## Verdict

`auto_quant_results_import` and `auto_quant_prior_init` exited `0`, but
`analyze_subset` timed out after `360s` with exit `124`. Manual readbacks exited
`0` but remained fail-closed:

- workflow admission: `fail_closed`
- reason: `exact_structural_branch_visible_but_not_ready_or_actionable`
- structural candidate: `actionable=false`, `ready=false`, `persisted=false`
- Pre-Bayes: null/empty posterior
- structural target: `rows=2`, `mature_rows=0`, `history_mature_rows=0`
- validation: `raw_scored_mature=0/30`, `production_validation=0/30`,
  `observation_validation=0/30`
- ranker runtime: disabled, trainer artifact missing

Keep all practical gates false:

```text
downstream_allowed=false
pre_bayes_allowed=false
bbn_allowed=false
catboost_allowed=false
execution_tree_allowed=false
promotion_allowed=false
trade_usable=false
update_goal=false
```

## Reusable lesson

Do not repeat light overlays or simulated feedback on this root. The current
blocker is not Gate 1 economics; it is analyze/workflow execution
materialization plus missing real/current mature validation rows. Next useful
work should either make `analyze` complete on a smaller same-root materialization
fixture or add real/current same-root mature observations, then re-test
`transition_hazard < 0.60`, `pda_hybrid_alignment=true`, and
`execution_readiness >= 0.65`.
