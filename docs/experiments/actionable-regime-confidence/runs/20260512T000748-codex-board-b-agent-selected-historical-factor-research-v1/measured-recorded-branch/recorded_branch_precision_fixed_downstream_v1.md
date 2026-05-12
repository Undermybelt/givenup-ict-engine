# Recorded Branch Precision-Fixed Downstream Readback v1

Run id: `20260512T000748+0800-codex-board-b-agent-selected-historical-factor-research-v1`

## Decision

Fail-closed supplemental evidence. This readback corrects the older zero-trade interpretation for the `000748` recorded-branch probe and proves the measured packet can move through Auto-Quant import, BBN prior-init, real-trade ingest, Pre-Bayes, CatBoost/path-ranker, and workflow/execution-candidate surfaces. It does not supersede the active `20260512T002020` board cursor and does not promote `220646`.

## Input Packet

- Measured manifest: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/measured-recorded-branch/strategy_library_recorded_nq_precision_fixed_v1.json`
- Measured summary: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/measured-recorded-branch/recorded_branch_precision_fixed_v1.json`
- Real trades: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/measured-recorded-branch/regime_root_pulse_branch_real_trades_v1.jsonl`
- Downstream state: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/state_agent_selected_historical_factor_research_downstream_v1`

## Ordered Readback

1. Auto-Quant results import: exit `0`; manifest/log cross-check matched `5/5` strategies with no mismatch.
2. BBN prior-init: exit `0`; non-dry-run, temper `0.25`, applied `RegimeRootPulseBranch`, `RegimeTrendCarry`, and `RegimeVolBreakout`.
3. Real-trade ingest: exit `0`; non-dry-run, inserted `300/300` RegimeRootPulseBranch feedback rows, invalid `0`.
4. Pre-Bayes refresh: exit `0`; latest gate remained `pass_neutralized`.
5. Policy/CatBoost/path-ranker status: exit `0`; runtime ready, raw-scored mature rows `288/30`, production validation `286/30`, observation validation `48/30`.
6. Structural target export: exit `0`; rows `6`, candidate set size `3`, history rows `295`, history mature rows `288`.
7. Workflow structural bundle: exit `0`; selected rooted path `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`, path-ranker raw score `0.65`, source `history_path`.
8. Workflow execution-candidate/full status: exit `0`; execution candidate stayed observe-only and workflow remained blocked by `user_selected_historical_data_missing`.

## Promotion Status

`promotion_allowed=false`: the precision-fixed replay is single recorded NQ/USD timerange evidence, the dense `RecordedBranchDailyPulse` strategy is adapter/data-path measurement only, Pre-Bayes is neutralized, execution-candidate review status is `observe`, and the workflow still requires a user-selected historical dataset before another comparable historical run.

## Evidence

- `logs/24_precision_fixed_results_import.out`
- `logs/25_precision_fixed_prior_init.out`
- `logs/26_precision_fixed_real_trades_ingest.out`
- `logs/27_precision_fixed_pre_bayes_status.out`
- `logs/28_precision_fixed_policy_training_status.out`
- `logs/29_precision_fixed_export_structural_path_ranking_target.out`
- `logs/30_precision_fixed_workflow_structural_bundle.out`
- `logs/31_precision_fixed_workflow_execution_candidate.out`
- `logs/32_precision_fixed_workflow_status_agent.out`
- `measured-recorded-branch/recorded_branch_precision_fixed_downstream_v1_assertions.out`
