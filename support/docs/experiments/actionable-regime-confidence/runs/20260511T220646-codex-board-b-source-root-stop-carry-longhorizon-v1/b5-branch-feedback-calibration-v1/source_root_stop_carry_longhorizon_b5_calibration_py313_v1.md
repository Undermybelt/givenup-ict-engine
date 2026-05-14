# SourceRootStopCarryLongHorizon B5 Calibration py313 v1

- Decision: `b5_catboost_runtime_ready_but_execution_tree_branch_path_not_consumed`
- Selected feedback: `48` rows; root counts `{'Bull': 12, 'Bear': 12, 'Sideways': 12, 'Crisis': 12}`
- CatBoost trained: `True`
- Trainer/runtime: `runtime_eligible`, runtime ready `True`
- Production validation: `True` with `274` rows
- Observation validation: `True` with `48` rows
- Pre-Bayes gate: `None`
- Current workflow path is required Board B branch path: `False`
- Execution candidate ready: `False`
- Closed-loop confidence ready: `False`
- Promotion allowed: `False`

## Runtime Readback

CatBoost is now a real local model artifact, trained with `python3.13` on branch-path history and registered through `ict-engine register-structural-path-ranking-trainer-artifact`; `policy-training-status` reports runtime eligible and validation ready. The exact Board B branch paths are present in path-ranking history, but `workflow-status --phase structural-recommended-path-bundle` still emits `path:scenario:SRC_ROOT_CARRY_LONG_220646:update:actionable:execute_recommended_path:primary` rather than one of the four `regime_profit_branch_path` values, and `workflow-status --phase execution-candidate` returns `null`. Promotion therefore remains fail-closed.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/b5-branch-feedback-calibration-v1/source_root_stop_carry_longhorizon_b5_calibration_py313_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/b5-branch-feedback-calibration-v1/source_root_stop_carry_longhorizon_b5_calibration_py313_v1_assertions.out`
- Commands: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/b5-branch-feedback-calibration-v1/command-output`
- CatBoost model: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/b5-branch-feedback-calibration-v1/catboost/path_ranker_model_py313/catboost_model.cbm`
