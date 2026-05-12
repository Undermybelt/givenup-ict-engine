# SourceRootStopCarryLongHorizon Downstream Probe v1

- Decision: `downstream_probe_partial_fail_closed`
- State dir: `/tmp/ict-engine-board-b-source-root-stop-carry-longhorizon-220646`
- Wire records: `12329`
- Unique branch paths: `4`
- Branch path preserved: `true`
- Ingest applied: `false`
- Pre-Bayes observed: `true`
- Path-ranker target observed: `true`
- Execution candidate observed: `true`
- Closed-loop confidence ready: `false`
- Promotion allowed: `false`

## Commands

| Step | Exit | Output |
|---|---:|---|
| `auto_quant_ingest_real_trades_dry_run` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/downstream-consumption/command-output/auto_quant_ingest_real_trades_dry_run.out` |
| `auto_quant_ingest_real_trades_apply` | `1` | `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/downstream-consumption/command-output/auto_quant_ingest_real_trades_apply.out` |
| `pre_bayes_status_refresh` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/downstream-consumption/command-output/pre_bayes_status_refresh.out` |
| `workflow_status_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/downstream-consumption/command-output/workflow_status_agent.out` |
| `workflow_status_execution_candidate` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/downstream-consumption/command-output/workflow_status_execution_candidate.out` |
| `policy_training_status` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/downstream-consumption/command-output/policy_training_status.out` |
| `export_structural_path_ranking_target` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/downstream-consumption/command-output/export_structural_path_ranking_target.out` |

## Branch Paths

- `Bear -> BearReliefCarry -> StopManagedRecoveryCarry -> SourceRootStopCarryLongHorizonV1:bear_carry_h20_sl048_tp12`
- `Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12`
- `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- `Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`
