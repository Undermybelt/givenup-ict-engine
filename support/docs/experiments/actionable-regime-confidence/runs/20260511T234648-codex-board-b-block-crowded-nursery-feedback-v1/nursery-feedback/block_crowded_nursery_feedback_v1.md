# Block Crowded Nursery Feedback v1

- Run id: `20260511T234648+0800-codex-board-b-block-crowded-nursery-feedback-v1`
- Nursery branch id: `B2R_NURSERY_220646_CRISIS_BLOCK_CROWDED_V1`
- Nursery status: `incubation_only`
- Branch path: `Crisis -> RangeConsolidation/WideRange -> BlockCrowdedExecutionAdmissibility -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Auto-Quant evidence: `trades=532`, `folds=10`, `RC-SPA=83.0`.
- Pre-Bayes: `pass_neutralized` quality `0.562`.
- BBN evidence label: `primary::ExtremeStress`.
- CatBoost/path-ranker: score `0.5373`, validation ready `True`, production rows `274`.
- Prior execution tree: `block_crowded` / `blocked` with readiness `0.4433` below floor `0.45`.
- Fresh execution tree: `fill_viable` / `observe` with readiness `0.4504` versus floor `0.45`.
- Provider readback: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- Interpretation: context-sensitive negative execution-admissibility feature, not a profitability rejection and not a branch-routing failure.
- Promotion allowed: `False`.
- Next action: Use this as incubation-only negative execution-admissibility feedback. The fresh refresh did not repeat block_crowded, so treat the feature as context-sensitive and repeat across compatible live/readback contexts before sending a Board A split; do not promote until workflow blocking truth and closed-loop confidence are explicit.

Artifacts:
- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234648-codex-board-b-block-crowded-nursery-feedback-v1/nursery-feedback/block_crowded_nursery_feedback_v1.json`
- CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234648-codex-board-b-block-crowded-nursery-feedback-v1/nursery-feedback/block_crowded_nursery_feedback_v1.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234648-codex-board-b-block-crowded-nursery-feedback-v1/checks/block_crowded_nursery_feedback_v1_assertions.out`
