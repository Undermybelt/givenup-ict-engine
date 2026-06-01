# TOMAC NQ Two-Leg Clean Downstream Fail-Closed - 2026-05-21

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Context: Board B regime-rooted profitability-factor training for the TOMAC `NQ`
two-leg bidirectional opening-drive exact AQ survivor.

Branch path:
`TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> tomac_nq_bidir_opening_drive_twoleg_t15_x1080_exact_v1`.

Gate 1 evidence remained strong:

- `1720` trades
- raw `+665.58%`
- `5bps/side=+493.58%`
- `1.3354037267080745` trades/session

Clean downstream replay:

- runtime root:
  `/tmp/ict-engine-tomac-nq-bidir-opening-drive-twoleg-clean-downstream-20260521T2112+0800`
- durable readback:
  `support/docs/experiments/actionable-regime-confidence/runs/20260521T2112+0800-codex-tomac-nq-twoleg-clean-downstream-rerun-readback-v1`
- clean CSV conversion cleared the prior NUL/timestamp blocker:
  `1m=1768519`, `15m=117914`, `1h=29519`
- AQ import/prior, workflow, Pre-Bayes, target export, ranker train/apply,
  weighted trainer registration, runtime readback, policy readback, and final
  target export produced artifacts

Final blocker:

- seed analyze timed out: `03_analyze_seed.exit=124`
- initial trainer registration failed because CLI declared `catboost` while the
  emitted artifact was `weighted_feature_sum_v1`: `10_register_trainer.exit=1`
- re-registering the actual weighted fallback artifact succeeded and made
  runtime selection `enabled_registered_model_ready`
- final state still had `execution_gate_status=observe`
- `execution_readiness`, `transition_hazard`, and `pda_hybrid_alignment` did not
  materialize
- validation was far below gate: `raw_scored_mature=1/30`,
  `production_validation=0/30`, `observation_validation=0/30`

Decision:
`clean_downstream_rerun_fail_closed`.
`promotion_allowed=false`, `trade_usable=false`, `update_goal=false`.

Reusable lesson:
Do not rerun Gate 1 or lower gates for this branch. CSV repair and weighted
fallback registration can clear mechanics, but they are not execution admission.
The next valid work must repair full-window analyze materialization and produce
same-root execution-candidate/tree evidence plus enough mature validation rows
before the hard predicates can even be tested:
`transition_hazard < 0.60`, `pda_hybrid_alignment=true`, and
`execution_readiness >= 0.65`.
