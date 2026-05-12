# Board B AQ-First Nursery Feedback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T092330+0800-codex-board-b-aq-first-nursery-feedback-v1`

Mode: `incubation_only`

## Evidence
- Precision-fixed recorded branch measurement: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/measured-recorded-branch/recorded_branch_precision_fixed_v1.md`
- Precision-fixed downstream assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/measured-recorded-branch/recorded_branch_precision_fixed_downstream_v1_assertions.out`
- Recorded MTF replay correction: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/agent_selected_recorded_mtf_nonzero_replay_correction_v1.md`
- Agent-selected historical factor research: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/agent_selected_historical_factor_research_v1.md`
- LTF synthetic Auto-Quant initial readback: `docs/experiments/actionable-regime-confidence/runs/20260512T035511-codex-board-b-032157-ltf-synthetic-autoquant-v1/ltf_synthetic_autoquant_initial_readback_v1.md`
- Path score row: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/downstream-chain/agent_selected_recorded_mtf_path_scores_v1.csv`

## Readback
- The precision-fixed recorded NQ/USD branch is the useful AQ-first nursery signal in this slice.
- The root cause was run-local market precision: the synthetic market rounded NQ position size to `0.0`; the fixed adapter emitted nonzero trades.
- Dense measurement probe: `RecordedBranchDailyPulse` produced `478` trades, profit `14.7500%`, Sharpe `6.4413`, profit factor `1.3201`; it was excluded from downstream scoring as a measurement probe rather than a production recipe.
- Downstream dry-run candidate: `RegimeRootPulseBranch` produced `300` trades, profit `3.1600%`, Sharpe `1.5610`, win rate `35.0000%`, profit factor `1.1132`, and `300/300` real-trade rows parsed with `0` invalid rows.
- Downstream assertions show command failures `0`, Auto-Quant manifest import `5/5`, BBN prior init applied `3` strategies, Pre-Bayes `pass_neutralized`, path-ranker runtime ready, workflow structural path `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`, execution candidate `observe`, and workflow blocking reason `user_selected_historical_data_missing`.
- The LTF synthetic readback failed earlier with `No pair in whitelist`, so it is a dead-end for nursery promotion rather than a useful production signal.

## Nursery Signal
- Prefer precision-fixed recorded historical replay over synthetic pair construction for branch search.
- Keep `RegimeRootPulseBranch` as a nursery-only downstream candidate, not a promoted branch.
- Treat the LTF synthetic path as search noise until pair wiring or market construction is repaired.

## Board A Feedback
- Search priority should favor precision-fixed recorded historical replay with nonzero trade output and a visible Crisis-rooted branch path.
- Production promotion stays blocked.
- Source/control and explicit selected-history gates remain fail-closed for the current objective.

## Decision
- Gate: `incubation_only:aq_first_nursery_feedback_v1_recorded_branch_precision_fixed`
- Promotion allowed: `false`
- update_goal: `false`

## Next
- Consume this as Board A search-priority feedback only.
- Do not treat it as source/control unlock evidence or selected-history approval.
