# User-Selected Historical Path Probe v1

Run id: `20260512T000604+0800-codex-board-b-user-selected-historical-path-probe-v1`

## Decision

- Status: `blocked`
- Blocker: `user_selected_historical_data_missing`
- Promotion allowed: `false`
- Interpretation: the recorded historical data path can be exercised through Auto-Quant handoff, Pre-Bayes/BBN, CatBoost/path-ranker, and execution-tree surfaces, but this was still an agent-selected probe. It does not satisfy the workflow's explicit user-selected historical-data gate.

## Probe Scope

- Symbol: `SRC_ROOT_CARRY_LONG_220646`
- Data path used: `docs/experiments/actionable-regime-confidence/runs/20260511T235535-codex-board-b-crisis-crowded-suppression-full-replay-v1/state_suppression_full_replay_v1/SRC_ROOT_CARRY_LONG_220646/analyze_live_20260511T154641_ltf.json`
- Paired path used: `docs/experiments/actionable-regime-confidence/runs/20260511T235535-codex-board-b-crisis-crowded-suppression-full-replay-v1/state_suppression_full_replay_v1/SRC_ROOT_CARRY_LONG_220646/analyze_live_20260511T154641_spot.json`
- Workflow's deferred user-choice path still points to the earlier `20260511T233426` recorded paths and asks the user to choose the historical dataset before another factor-research run.

## Layer Readback

- Auto-Quant factor-research exit: `0`; handoff artifact written at `state_user_selected_historical_path_probe_v1/SRC_ROOT_CARRY_LONG_220646/auto_quant_handoff.factor_research.json`
- Auto-Quant handoff readiness: `dependency_ready_data_missing`; next handoff blocker `auto_quant_prepare_required`
- Auto-Quant status readback on the copied isolated state: `missing_dependency` / `auto_quant_bootstrap_required`
- Later Auto-Quant prepare attempt in the same run root: `auto_quant_prepare_uv_manual.exit=1`; this records the prepare blocker separately from the core downstream readback, whose commands exited `0`
- Pre-Bayes/filter: `pass_neutralized`
- BBN evidence: `applied`; label `primary::ExtremeStress`; branch path `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`; soft evidence weight `0.650`; trade usable `true`
- CatBoost/path-ranker: `catboost` trainer artifact, `12329` trained rows, `274/30` production validation rows, `48/30` observation validation rows, runtime `enabled_candidate_set_ready`
- Structural bundle: exact Crisis path rank `1`, raw path score `0.65`, current posterior `0.5822884327025901`, selected path probability `0.3896757804925325`, historical total records `14`, structural path history `7 wins / 5 losses / 12 records`
- Execution candidate: `ready`, review `observe`, reason `candidate_not_comparable_same_data_factor_required`, top factor `structure_ict` with action `tune`, trade direction `Bull`
- Workflow status: `blocked`; next action `ask_user_choose_historical_data`; final action `Observe`

## Provider Readback

- Provider summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`
- yfinance: ready
- Kraken CLI: ready
- IBKR: configured but unhealthy; gateway reachable with runtime dependency gap
- TradingViewRemix MCP: configured but unhealthy; connectivity probe failed

## Artifacts

- Command outputs: `docs/experiments/actionable-regime-confidence/runs/20260512T000604-codex-board-b-user-selected-historical-path-probe-v1/command-output/`
- Isolated state: `docs/experiments/actionable-regime-confidence/runs/20260512T000604-codex-board-b-user-selected-historical-path-probe-v1/state_user_selected_historical_path_probe_v1`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T000604-codex-board-b-user-selected-historical-path-probe-v1/checks/user_selected_historical_path_probe_v1_assertions.out`

## Next

Ask for or otherwise obtain an explicit user-selected historical dataset before treating this gate as cleared. Until then, keep `SourceRootStopCarryLongHorizonV1` plus the sibling suppression evidence in nursery/observe mode only.
