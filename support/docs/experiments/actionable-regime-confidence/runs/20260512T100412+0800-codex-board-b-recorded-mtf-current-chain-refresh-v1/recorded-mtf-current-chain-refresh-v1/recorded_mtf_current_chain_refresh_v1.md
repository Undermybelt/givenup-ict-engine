# Recorded MTF Current Chain Refresh v1

Run id: `20260512T100412+0800-codex-board-b-recorded-mtf-current-chain-refresh-v1`

Mode: `incubation_only`

## Scope

Fresh current-runtime readback for the `092330` precision-fixed recorded-MTF nursery signal. The state was copied to `/tmp/ict-engine-20260512T100412+0800-codex-board-b-recorded-mtf-current-chain-refresh-v1-state` before `--refresh` commands so existing evidence state was not mutated.

Source state:
- `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/state_agent_selected_historical_factor_research_downstream_v1`

## Commands

All commands exited `0`:
- `provider-status --agent`
- `auto-quant-status --state-dir <tmp_state> --output-format json`
- `pre-bayes-status --symbol SRC_ROOT_CARRY_LONG_220646 --state-dir <tmp_state> --refresh --output-format json`
- `policy-training-status --symbol SRC_ROOT_CARRY_LONG_220646 --state-dir <tmp_state> --output-format agent`
- `export-structural-path-ranking-target --symbol SRC_ROOT_CARRY_LONG_220646 --state-dir <tmp_state>`
- `workflow-status --phase structural-recommended-path-bundle --agent --refresh`
- `workflow-status --phase structural-feedback --agent --refresh`
- `workflow-status --phase execution-candidate --agent --refresh`
- `workflow-status --agent --refresh`

Raw outputs are under `command-output/`.

## Readback

- Provider status: `entry_model:2/2 ready`, `live_runtime:1/3 ready`, `local_runtime:1/2 ready`, `market_data:2/7 ready`.
- Provider ready set includes `yfinance`, `tradingview_mcp`, and `kraken_cli`; `ibkr` / `ibkr_bridge` are still not ready because runtime dependencies are missing, although a local gateway is reachable.
- Auto-Quant status on the copied recorded-MTF state is `dependency_ready_data_missing`; dependency is healthy but this state is not a data-ready AQ workspace.
- Pre-Bayes gate remains `pass_neutralized`; latest canonical structural active regime is `range` with confidence `0.5619249343265972`.
- Structural path ranker is runtime-ready: target rows `6`, history rows `295`, history mature rows `288`, production validation `286/30`, observation validation `48/30`, trainer artifact `runtime_eligible`, runtime selection `enabled_candidate_set_ready`.
- Structural bundle preserves exact path `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.
- Structural feedback does not preserve that exact Board B path in this slice; it emits generic BBN-derived path `path:scenario:SRC_ROOT_CARRY_LONG_220646:belief_regime_node:range:range_mean_reversion:primary`.
- Execution-candidate preserves the same exact path with `path_ranker_runtime_source=history_path`, `path_ranker_raw_score=0.65`, `pre_bayes_gate_status=pass_neutralized`, and `execution_readiness=0.4504361163104953`.
- Execution gate is still `execution_observe_only`; `review_status=observe`; `ready=false`.

## Decision

Gate: `incubation_only:recorded_mtf_exact_branch_preserved_execution_observe_only`.

This refresh confirms the current runtime preserves the rooted Board B branch path through CatBoost/path-ranker readiness and execution-candidate. It also exposes one remaining downstream mismatch: the structural-feedback/BBN feedback surface still falls back to a generic range node instead of the exact Board B branch path. It does not promote the candidate because execution readiness remains below promotion and the selected-history/source-control unlocks are still absent.

Promotion allowed: `false`.

`update_goal=false`.

## Next

Do not rerun closed LTF/TOMAC sidecars in the same shape. Continue only on recorded-history branches that can add mature observations or materially raise execution readiness, or wait for explicit selected-history/source-control unlock before treating the chain as promotion evidence.
