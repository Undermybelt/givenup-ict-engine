# Selected Auto-Quant Completion Addendum v1

Run id: `20260512T012714+0800-codex-board-b-selected-auto-quant-completion-addendum-v1`

Scope: append-only readback for the selected offline Auto-Quant run that was still pending while the `010454` exact-branch repair rows were being assembled.

## Result

The selected offline Auto-Quant run completed successfully:

- Command: `13_auto_quant_run_recorded_branch_offline_2021_2025_selected`
- Exit: `0`
- Run log: `docs/experiments/actionable-regime-confidence/runs/20260512T004738-codex-board-b-220646-explicit-historical-rerun-v1/explicit-historical-rerun-v1/logs/13_auto_quant_run_recorded_branch_offline_2021_2025_selected.out`
- Strategy result count: `3` succeeded, `0` failed

Measured strategies:

| Strategy | Trades | Sharpe | Profit % | Win Rate % | Profit Factor | Max Drawdown % |
|---|---:|---:|---:|---:|---:|---:|
| `RegimeRootPulseBranch` | 4705 | 1.1480 | 59.59 | 35.7705 | 1.0872 | -25.1489 |
| `RegimeTrendCarry` | 556 | 0.4874 | 70.45 | 34.7122 | 1.2951 | -18.5655 |
| `RegimeVolBreakout` | 515 | 0.2928 | 37.35 | 36.5049 | 1.1837 | -17.9457 |

## Interpretation

This retires the pending-runtime question from the handoff: the selected offline run did not need to be killed or recorded as a runtime blocker.

It does not change the active Board B promotion state. These Auto-Quant measurements are supplemental backtest evidence. They do not prove exact `220646` Sideways structural-branch execution-candidate admission, and they do not repair the remaining consumed-validation / closed-loop confidence gap recorded in the active `010454` repair rows.

## Current Blocker

The active blocker remains downstream identity and closed-loop admission:

- Structural bundle selects the exact Sideways path: `Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`.
- Path-ranker/CatBoost is runtime-ready after the `010454` command-shape repairs.
- The execution candidate is still `execution-candidate:SRC_ROOT_CARRY_LONG_220646:analyze-live:v1` with `trade_direction=Bull`.
- Workflow still records `pass_neutralized`, `different_data_fingerprint`, and `no_consumed_validation`.

No promotion is allowed from this addendum.

