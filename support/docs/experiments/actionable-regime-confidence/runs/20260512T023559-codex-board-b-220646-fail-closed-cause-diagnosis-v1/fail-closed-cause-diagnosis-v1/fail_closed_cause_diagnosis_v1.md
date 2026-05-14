# Board B 220646 Fail-Closed Cause Diagnosis v1

Scope: copied-state diagnostic for the exact `220646` Sideways branch after execution-tree trace parity was repaired in `022335`.

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T023559-codex-board-b-220646-fail-closed-cause-diagnosis-v1`

## Command exits

- `00_provider_status`: `0`
- `01_auto_quant_status`: `0`
- `02_pre_bayes_status`: `0`
- `03_policy_training_status`: `0`
- `04_workflow_structural_bundle`: `0`
- `05_workflow_execution_candidate`: `0`
- `06_workflow_full`: `0`

## Findings

The exact branch identity is preserved:

`Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`

CatBoost/path-ranker is not the current blocker. Policy status reports `score_model_family=catboost`, `score_source_kind=external_model`, `runtime_active_match_count=4`, and validation ready with `production_validation=869/30` and `observation_validation=82/30`.

Pre-Bayes is the first hard fail-closed cause. It remains `pass_neutralized`, not `pass_hard`. The current evidence has `factor_alignment=mixed`, filtered `market_regime=trend`, market state `TrendExpansion / BullTrendAcceleration`, and a very small long/short probability gap `0.007747` against policy `min_directional_support_gap=0.08`.

Execution admissibility is the second hard fail-closed cause. The execution tree lineage reports `execution_readiness=0.4421`, below the `0.45` readiness threshold, and first classifies the branch as `block_crowded`. The persisted trace then remains top-level `observe / transition_guardrail / guarded` because `hybrid_transition_hazard=0.600`.

Workflow remains blocked for historical replay promotion by `user_selected_historical_data_missing`. The recommended factor-research command is an `ask-user` path-selection command, not an autonomous promotion path.

Provider readback is mixed: `yfinance` is ready, `kraken_cli` is ready, `ibkr` / `ibkr_bridge` are reachable but dependency-unhealthy, `tradingview_mcp` failed connectivity, and `kraken_public` lacks system Python provider dependencies. The copied diagnostic state reports Auto-Quant `missing_dependency`; that is a copied-state dependency status, not a new RC-SPA or profitability blocker for the already accepted `220646` source pass.

## Result

`220646` should remain fail-closed. This is no longer a branch-preservation, CatBoost/runtime, or execution-tree trace parity bug. The remaining decision is whether to reject the exact branch for this context or rerun only after explicit historical data selection and compatible regime/execution context evidence can move Pre-Bayes to `pass_hard` and execution readiness above threshold.

No RC-SPA rerun, no promotion claim, and no runtime code edit was made in this slice.
