# Execution Candidate Branch Preservation v1

Run id: `20260512T093937+0800-codex-board-b-execution-candidate-branch-preservation-v1`

Mode: `incubation_only`

## Scope

Fresh readback against the `092330` precision-fixed recorded MTF nursery signal. This verifies whether the exact rooted branch path survives from ict-engine structural bundle into execution-candidate. It does not select `HTF`, `MTF`, or `LTF`, does not approve source/control evidence, does not promote a candidate, and does not call `update_goal`.

State dir:
- `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/state_agent_selected_historical_factor_research_downstream_v1`

## Commands

```text
./target/debug/ict-engine workflow-status --symbol SRC_ROOT_CARRY_LONG_220646 --state-dir docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/state_agent_selected_historical_factor_research_downstream_v1 --refresh --phase structural-recommended-path-bundle --agent

./target/debug/ict-engine workflow-status --symbol SRC_ROOT_CARRY_LONG_220646 --state-dir docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/state_agent_selected_historical_factor_research_downstream_v1 --refresh --phase execution-candidate --agent
```

Both commands exited `0`.

Provider refresh command:

```text
./target/debug/ict-engine provider-status --agent
```

The provider refresh exited `0`.

## Readback

- Structural bundle path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.
- Execution-candidate path: `structural-recommended-path-bundle:Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.
- `path_ranker_runtime_source=history_path`.
- `path_ranker_raw_score=0.65`.
- `pre_bayes_gate_status=pass_neutralized`.
- `execution_readiness=0.4504361163104953`.
- `candidate_status=execution_observe_only`.
- `review_status=observe`.
- `ready=false`.

Provider readback:
- `yfinance` ready in live-runtime and market-data lanes.
- `tradingview_mcp` ready with MCP URL/API key available.
- `kraken_cli` ready.
- `ibkr` / `ibkr_bridge` not ready because required runtime dependencies are missing, although a local IBKR API is reachable on port `4002`.
- Market-data readiness remains partial: `2/7`.

## Decision

Gate: `incubation_only:execution_candidate_branch_path_preserved_observe_only`.

The exact regime-profit branch path now survives to execution-candidate in this live readback. The remaining blocker is not branch-collapse in this slice; it is execution readiness / pre-Bayes promotion readiness plus the still-missing explicit selected-history and source/control unlock gates.

Promotion: `false`.

`update_goal=false`.
