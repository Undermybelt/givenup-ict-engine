# SI5M LinReg cost survivor downstream fail-closed, 2026-05-20

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use this when a retained-real futures linear-regression-channel branch survives Auto-Quant Gate 1 costs but downstream does not materialize exact execution readiness.

Packet:
- Source Gate 1: `support/docs/experiments/actionable-regime-confidence/runs/20260520T092555+0800-codex-ibkr-si5m-linreg-channel-breakout-1m-gate1-v1`
- Downstream: `support/docs/experiments/actionable-regime-confidence/runs/20260520T092555+0800-codex-ibkr-si5m-linreg-channel-breakout-1m-gate1-v1/downstream-exact-si-5m-linreg-channel-breakout-20260520T093800+0800`
- Branch: `FUTURES -> precious_metals -> SI -> 5m -> TrendChannelExpansion -> LinearRegressionChannelBreakout -> ibkr_si5m_linreg_channel_breakout_1m_gate1_v1`

Gate 1 was real and worth preserving as observation evidence:
- Retained same-session IBKR `SI 202607` `5m` data.
- Exact survivor: `SI/linreg_retest/5m`, `9` trades, raw `+1.28%`, `2bps=+0.92%`, `5bps=+0.38%`.

Downstream still failed closed:
- Auto-Quant import/prior, workflow/Pre-Bayes readbacks, structural target export, CatBoost train/apply/register, score application, runtime enable, final policy/export readbacks exited `0`.
- Both `analyze` calls timed out: `03_analyze_seed=124`, `12_analyze_after_ranker=124`.
- Runtime registered as CatBoost and was ready with one match, but validation was absent: `mature_rows=0`, `history_mature_rows=0`, `raw_scored_mature=0/30`, `production_validation=0/30`, `observation_validation=0/30`.
- Execution predicates failed: `execution_readiness=0.0`, `transition_hazard=1.0`, `pda_hybrid_alignment=false`, `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`.

Rule:
- Treat a real `5bps/side` LinReg channel survivor as a useful public-family cost observation, not as practical alpha, unless downstream also materializes the exact execution candidate and passes maturity plus the transition/PDA/readiness gates.
- Do not clone the same SI `5m` channel shape or stack light overlays merely because Gate 1 survived. The next same-root attempt must directly repair analyze/execution-candidate materialization, add acceptable mature feedback, or reduce the transition/PDA blocker trio.
- If terminal metrics contain stale copied decision labels, trust the run root, branch path, command exits, and hard predicate fields over the label string.
