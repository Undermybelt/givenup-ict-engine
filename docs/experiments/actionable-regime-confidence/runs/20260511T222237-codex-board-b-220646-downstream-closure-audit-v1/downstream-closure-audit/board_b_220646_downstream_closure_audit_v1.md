# Board B 220646 Downstream Closure Audit v1

- Decision: `board_b_220646_downstream_closure_audit_v1=partial_fail_closed_no_closed_loop_confidence`.
- Source recipe: `SourceRootStopCarryLongHorizonV1`; RC-SPA gate `pass`, stable score `85.74074074074075`.
- Wire records: `12329`; branch paths preserved in wire: `true`.
- Existing clean ingest evidence applied `12329` records; no force ingest was run in this audit.
- Pre-Bayes branch-path posterior: `false`; BBN branch-path posterior: `false`.
- CatBoost/path-ranker calibrated branch rows ready: `false`; execution-tree branch admissibility ready: `false`.
- Closed-loop confidence ready: `false`; promotion allowed: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; Auto-Quant training started: `false`; raw data committed: `false`.

## Stage Gates

| Gate | Observed | Required | Pass | Evidence |
|---|---|---|---:|---|
| `auto_quant_rc_spa` | `pass` | `pass with 4/4 price roots and Manipulation component` | `true` | `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.json` |
| `wire_branch_paths` | `records=12329;branches=4;roots={'Bull': 4948, 'Bear': 1349, 'Sideways': 5500, 'Crisis': 532}` | `12329 records, 4 rooted price paths, Bull/Bear/Sideways/Crisis` | `true` | `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/ict-engine-downstream/source_root_stop_carry_longhorizon_real_trades_wire_v1.jsonl` |
| `real_trade_ingest` | `12329` | `12329` | `true` | `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/ict-engine-downstream/source_root_stop_carry_longhorizon_downstream_probe_v1.json` |
| `pre_bayes_branch_path_posterior` | `{'Bear -> BearReliefCarry -> StopManagedRecoveryCarry -> SourceRootStopCarryLongHorizonV1:bear_carry_h20_sl048_tp12': False, 'Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12': False, 'Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12': False, 'Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12': False}` | `all branch paths re-emitted with filter_posterior_confidence` | `false` | `docs/experiments/actionable-regime-confidence/runs/20260511T222237-codex-board-b-220646-downstream-closure-audit-v1/command-output/legacy_pre_bayes_status.out` |
| `bbn_branch_path_posterior` | `{'Bear -> BearReliefCarry -> StopManagedRecoveryCarry -> SourceRootStopCarryLongHorizonV1:bear_carry_h20_sl048_tp12': False, 'Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12': False, 'Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12': False, 'Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12': False}` | `all branch paths re-emitted with bbn_posterior_confidence` | `false` | `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/ict-engine/05_auto_quant_prior_init_longhorizon_apply.json` |
| `catboost_path_ranker_calibration` | `fresh_calibrated=0;legacy_calibrated=0;legacy_mature=0` | `>=4 calibrated and mature branch rows` | `false` | `docs/experiments/actionable-regime-confidence/runs/20260511T222237-codex-board-b-220646-downstream-closure-audit-v1/command-output/legacy_export_structural_path_ranking_target.out` |
| `execution_tree_branch_admissibility` | `{'Bear -> BearReliefCarry -> StopManagedRecoveryCarry -> SourceRootStopCarryLongHorizonV1:bear_carry_h20_sl048_tp12': False, 'Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12': False, 'Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12': False, 'Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12': False}` | `all branch paths re-emitted with execution_tree_admissibility` | `false` | `docs/experiments/actionable-regime-confidence/runs/20260511T222237-codex-board-b-220646-downstream-closure-audit-v1/command-output/legacy_workflow_status_execution_candidate.out` |
| `closed_loop_confidence` | `False` | `True` | `false` | `derived from ordered stage gates` |

## Boundary

This audit consumes existing Auto-Quant/RC-SPA artifacts and runs readback commands against the existing ict-engine downstream states. It does not rerun heavy Auto-Quant training, does not force duplicate ingest, and does not promote the candidate from RC-SPA alone.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T222237-codex-board-b-220646-downstream-closure-audit-v1/downstream-closure-audit/board_b_220646_downstream_closure_audit_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T222237-codex-board-b-220646-downstream-closure-audit-v1/downstream-closure-audit/board_b_220646_downstream_closure_audit_v1.md`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T222237-codex-board-b-220646-downstream-closure-audit-v1/downstream-closure-audit/board_b_220646_downstream_closure_audit_gates_v1.csv`
- Command CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T222237-codex-board-b-220646-downstream-closure-audit-v1/downstream-closure-audit/board_b_220646_downstream_closure_audit_commands_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T222237-codex-board-b-220646-downstream-closure-audit-v1/checks/board_b_220646_downstream_closure_audit_v1_assertions.out`
