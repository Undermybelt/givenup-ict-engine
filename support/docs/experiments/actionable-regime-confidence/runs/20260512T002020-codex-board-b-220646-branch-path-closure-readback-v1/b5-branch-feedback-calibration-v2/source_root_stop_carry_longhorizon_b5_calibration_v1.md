# SourceRootStopCarryLongHorizon B5 Calibration v1

- Decision: `b5_branch_feedback_promotable_candidate`
- Selected feedback: `80` rows, `20` per root
- Required branch paths covered in history: `True`
- CatBoost trained: `True`
- Policy production validation ready: `True`
- Policy observation validation ready: `True`
- Current structural path is required Board B branch path: `True`
- Execution-tree candidate ready: `True`
- Closed-loop confidence ready: `True`
- Promotion allowed: `True`

## Branch Paths
- `Bear -> BearReliefCarry -> StopManagedRecoveryCarry -> SourceRootStopCarryLongHorizonV1:bear_carry_h20_sl048_tp12`
- `Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12`
- `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- `Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1/b5-branch-feedback-calibration-v2/source_root_stop_carry_longhorizon_b5_calibration_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1/b5-branch-feedback-calibration-v2/source_root_stop_carry_longhorizon_b5_calibration_v1_assertions.out`
- Command logs: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1/b5-branch-feedback-calibration-v2/command-output`
- State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1/b5-branch-feedback-calibration-v2/state_branch_feedback_v1`

## Readback
The exact Board B branch paths are present in the structural feedback history and CatBoost scoring path. The current ict-engine execution-tree surface still emits its own structural path rather than one of the four `regime_profit_branch_path` values, so production promotion remains fail-closed unless that runtime surface consumes a required Board B branch path directly.
