# Board B LTF Tick-Precision Probe Readback v1

Run id: `20260512T041404+0800-codex-board-b-ltf-zero-trade-root-cause-v1`

Scope: non-promotional root-cause and downstream readback for the completed `035511`, `035427`, and `040232` LTF/Tomac sidecars after all visible exit files were complete.

## Finding

The LTF Auto-Quant zero-trade symptom was not purely factor-empty. It was partly a synthetic market precision issue:

- Existing `035511` `run_tomac.py` synthetic market used `precision.amount=8` and `precision.price=8`; all actual strategies reported zero trades.
- A direct strategy-data probe found live entry signals inside the FreqTrade-loaded dataframe.
- An isolated `AlwaysEnterProbe` produced 23 entry signals / 25 exit signals / 0 collisions, but still executed 0 trades under the default `8/8` precision.
- The same `AlwaysEnterProbe` executed 22 trades when the synthetic market precision was overridden in memory to `amount=0.000001`, `price=0.01`.

## Measured LTF Result

With the tick-size precision override applied in memory to the actual `035511` strategies:

| Strategy | Rooted branch | Trades | Win rate | Total profit | Sharpe | Status |
|---|---:|---:|---:|---:|---:|---|
| `NQRootPulseMeanRevert` | `Sideways -> RangeConsolidation -> NQCalmVixZReversion -> NQRootAdaptiveCostCrisisRepairV3:sideways_calm_vix_z_revert_h72` | 11 | 81.8182% | 0.46% | 4.6585 | measured_thin |
| `NQRootTrendPulse` | `Bull -> TrendExpansion -> NQSourceRootCarry -> NQRootAdaptiveCostCrisisRepairV3:bull_source_root_carry_h72` | 4 | 75.0000% | 0.25% | 3.3511 | measured_too_thin |
| `TomacNQ_KillzoneBreakout` | Tomac NQ killzone | 0 | 0.0000% | 0.00% | 0.0000 | no_trades |

Materialized packet:

- `tick_precision_strategy_library_v1.json`
- `tick_precision_real_trades_v1.jsonl` (`15` rows)
- `tick_precision_packet_summary_v1.json`

## Downstream Readback

The packet was pushed through an isolated copy of `034002/downstream-combined-v1/state_combined_v1` at `state_tick_precision_v1`.

Command results:

- `06_auto_quant_results_import`: exit `0`; imported `2` ok strategies.
- `07_auto_quant_prior_init`: exit `1`; refused to stack a second Auto-Quant prior over the copied state's existing prior init. This was not forced.
- `08_auto_quant_ingest_real_trades`: exit `0`; applied `4/15`, invalid `11`.
- `09_pre_bayes_status`: exit `0`; gate stayed `observe_only`.
- `10_policy_training_status`: exit `0`; path-ranker validation stayed `0/30` production and `0/30` observation.
- `11_export_structural_path_ranking_target`: exit `0`; exported `5` current rows, `10` history rows, `0` mature rows.
- `12_workflow_structural_bundle`: exit `0`; remained a candidate-set score readback.
- `13_workflow_execution_candidate`: exit `0`; `ready=false`, `actionable=false`, `execution_blocked`.
- `14_workflow_full`: exit `0`; `blocking_truth.reason=user_selected_historical_data_missing`, `closed_loop_branch_admission.status=fail_closed`.

## Decision

No promotion. Do not edit the Current Cursor from `034002/downstream-combined-v1`.

This run proves the LTF sidecar has a mechanical precision bug and can emit real but thin measured trades after repair. It still cannot satisfy Board B because it is agent-selected rather than explicit user-selected historical data, trade counts are too low, prior-init was not cleanly reset, real-trade ingest applied only `4/15`, path-ranker validation remained `0/30`, and the execution tree remained fail-closed.

Next safe step: fix the synthetic market precision at the sidecar/Auto-Quant adapter boundary, then rerun only after an explicit selected historical data path is chosen and enough mature rooted branch observations exist.
