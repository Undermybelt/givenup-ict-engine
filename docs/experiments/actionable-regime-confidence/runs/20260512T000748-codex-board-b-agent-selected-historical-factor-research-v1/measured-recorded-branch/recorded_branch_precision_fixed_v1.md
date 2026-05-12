# Recorded Branch Precision-Fixed Measurement v1

Run id: `20260512T000748+0800-codex-board-b-agent-selected-historical-factor-research-v1`

## Decision

Fail-closed nursery evidence. The local recorded NQ/USD Auto-Quant bridge is now proven capable of nonzero measured trades after fixing the run-local synthetic market precision, but this is not a promotion pass.

## Root Cause Fixed

The adapter used Binance's tick-size precision mode but declared synthetic `amount` precision as `8`. Freqtrade rounded NQ position sizes around `3.8` contracts to `0.0`, so every entry signal became a no-op. The run-local adapter now uses `amount=0.000001` and `price=0.01` tick sizes.

## Measured Results

| Strategy | Trades | Win % | Profit % | Sharpe | Profit Factor |
|---|---:|---:|---:|---:|---:|
| `RecordedBranchDailyPulse` | 478 | 39.3305 | 14.7500 | 6.4413 | 1.3201 |
| `RegimeRootPulseBranch` | 300 | 35.0000 | 3.1600 | 1.5610 | 1.1132 |
| `RegimeRsiRelief` | 2 | 100.0000 | 0.3700 | 1.8253 | 0.0000 |
| `RegimeTrendCarry` | 30 | 36.6667 | 6.9100 | 0.7811 | 1.7378 |
| `RegimeVolBreakout` | 33 | 33.3333 | 3.2800 | 0.4492 | 1.2903 |

## Downstream Use

Selected for downstream dry-run only: `RegimeRootPulseBranch`, `RegimeTrendCarry`, `RegimeVolBreakout`.

Excluded from downstream scoring: `RecordedBranchDailyPulse`, because it is a dense measurement probe used to verify the adapter/data path rather than a production recipe.

## Artifacts

- Manifest: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/measured-recorded-branch/strategy_library_recorded_nq_precision_fixed_v1.json`
- Strategy summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/measured-recorded-branch/recorded_branch_precision_fixed_strategy_summary_v1.csv`
- Real-trade JSONL: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/measured-recorded-branch/regime_root_pulse_branch_real_trades_v1.jsonl`
- Trade export rerun log: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/measured-recorded-branch/regime_root_pulse_branch_trade_export_rerun.log`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/measured-recorded-branch/recorded_branch_precision_fixed_v1_assertions.out`

## Promotion Status

`promotion_allowed=false`: single recorded NQ/USD timerange, no branch RC-SPA/PBO/fold matrix, nursery-only strategy metadata, and no execution-tree promotion gate pass.

## Downstream Readback

- `auto-quant-results-import` exited `0`; the measured manifest imported with `5/5` strategies status `ok`.
- `auto-quant-prior-init --dry-run` exited `0`; `RegimeRootPulseBranch`, `RegimeTrendCarry`, and `RegimeVolBreakout` were applied in the dry-run and `evidence_value_gate_passed=true`.
- `auto-quant-ingest-real-trades --dry-run` exited `0`; `300/300` `RegimeRootPulseBranch` JSONL rows parsed with `trades_invalid=0`.
- `pre-bayes-status --refresh` exited `0`, but no active gate/policy/soft-evidence state exists for this run-local candidate.
- `policy-training-status` exited `0`; structural path-ranker runtime is visible, but validation remains `0/30` production rows and `0/30` observation rows.
- `workflow-status --phase execution-candidate` exited `0`; execution remains `observe`, `ready=false`, with `review_reason=structural_recommended_path_visible_but_execution_or_pre_bayes_gate_not_ready`.
- `workflow-status` exited `0`; blocking truth remains `insufficient_state` / `no workflow phase snapshots available`.

Downstream summary: `recorded_branch_precision_fixed_downstream_v1.json`; assertions: `recorded_branch_precision_fixed_downstream_v1_assertions.out`.
