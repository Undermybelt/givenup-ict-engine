# Branch CatBoost Runtime Gap Probe v1

- Branch rows: `12329`; chronological train rows: `9551`; holdout rows: `2778`.
- CatBoost model: `docs/experiments/actionable-regime-confidence/runs/20260511T222129-codex-board-b-220646-branch-catboost-runtime-gap-v1/catboost/branch_catboost_model_v1.cbm`.
- Branch score rows: `4`.
- Runtime target rows: `3`.
- Exact branch paths matching runtime `path_id`: `0`.
- Promotion status: `not_promoted:runtime_target_path_ids_do_not_match_regime_profit_branch_paths`.

## Branch Paths
- `Bear -> BearReliefCarry -> StopManagedRecoveryCarry -> SourceRootStopCarryLongHorizonV1:bear_carry_h20_sl048_tp12`
- `Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12`
- `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- `Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`

## Runtime Path IDs
- `path:scenario:NQ:belief_regime_node:trend:range_mean_reversion:primary`
- `path:scenario:NQ:belief_regime_node:trend:stress_de_risk:primary`
- `path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary`
