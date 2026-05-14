# Closure Reuse Cleanwire Bundle CatBoost Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-chain/closure_reuse_cleanwire_bundle_catboost_20260512T034711+0800`

This is an additive Board B readback for `NQRootAdaptiveCostCrisisRepairV3`. It reuses the cleanwire plus aggregate-regime-bundle state after the `034002` combined closure and does not update the Board B Current Cursor.

## Command Status

Commands `00-18` exited `0`.

- State copy/readback, aggregate bundle validation, analyze, Pre-Bayes status, structural target export, CatBoost train/apply/register/runtime enable, policy status, workflow structural bundle, workflow execution-candidate, workflow full, post-workflow Pre-Bayes, and pollution checks all completed.
- The run produced a real CatBoost model at `catboost/path_ranker_model/catboost_model.cbm`.
- The temporary `catboost_info` pollution directory was detected in `17_pollution_check.out` and absent after cleanup in `18_pollution_check_after_cleanup.out`.

## Branch Path Preservation

- The aggregate bundle kept `5` rooted paths visible:
  - `Bull -> TrendExpansion -> NQSourceRootCarry -> NQRootAdaptiveCostCrisisRepairV3:bull_source_root_carry_h72`
  - `Bear -> BearMarketDrawdown -> NQHighVixOversoldRebound -> NQRootAdaptiveCostCrisisRepairV3:bear_oversold_high_vix_rebound_h72`
  - `Sideways -> RangeConsolidation -> NQCalmVixZReversion -> NQRootAdaptiveCostCrisisRepairV3:sideways_calm_vix_z_revert_h72`
  - `Crisis -> ExtremeStress -> NQFlushRebound -> NQRootAdaptiveCostCrisisRepairV3:crisis_flush_rebound_h72`
  - `Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72`
- Structural target export emitted `5` current candidate rows and `13` history rows.
- CatBoost current scores covered all `5` exact current branch paths.
- Runtime selection was enabled with `runtime_source=candidate_set` and `runtime_matches=5`.

## Gate Result

Promotion remains fail-closed.

- Pre-Bayes latest gate: `observe_only`.
- Canonical structural confidence: `0.4038250313856651`.
- BBN bundle application status: `skipped`, while read-only bundle decision state was `accepted` and trade usable was `true`.
- Path-ranker validation: `0/30` production, `0/30` observation, `0` mature rows, calibration not fitted.
- Execution-candidate: `ready=false`, `actionable=false`, `execution_gate_status=execution_blocked`.
- Closed-loop branch admission: `status=fail_closed`, `reason=exact_structural_branch_visible_but_not_ready_or_actionable`.
- Blocking truth: `user_selected_historical_data_missing`.

## Next

Do not promote from CatBoost candidate-set raw scores. The next valid step is explicit historical-data path selection for the recorded `1d`, `1h`, or `15m` input files, then a structural-feedback / factor-research pass that can create mature branch observations before another promotion check.
