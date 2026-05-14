# Branch Path Closure Readback v1

Run id: `20260512T003655+0800-codex-board-b-220646-branch-path-closure-readback-v1`

Source cursor: `20260512T002020+0800-codex-board-b-220646-branch-path-closure-readback-v1`

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1`

State: `fail_closed:downstream_readback_executed_no_promotion`

## Scope

This readback closes the exact `220646` branch-path consumption loop for `SourceRootStopCarryLongHorizonV1`. It does not rescore RC-SPA, change the recipe, change runtime code, or promote the strategy. The only question checked here is whether the existing strict-pass branch paths can survive the ordered local chain:

`Auto-Quant/feedback -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree/workflow`.

## Source Branch Paths

The selected real-trade wire has `80` rows and preserves the four required rooted branch paths, `20` rows each:

- `Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12`
- `Bear -> BearReliefCarry -> StopManagedRecoveryCarry -> SourceRootStopCarryLongHorizonV1:bear_carry_h20_sl048_tp12`
- `Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`
- `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`

Evidence:

- `b5-branch-feedback-calibration-v2/selected_feedback_manifest.json`
- `b5-branch-feedback-calibration-v2/selected_real_trades_wire.jsonl`

## Provider / Runtime Readback

Provider status exited `0`. The usable current paths are yfinance and local Kraken CLI. IBKR is reachable but blocked by missing runtime dependencies, TradingViewRemix MCP is unhealthy, and `kraken_public` is blocked by Python provider dependencies. This is not a total data block.

Evidence:

- `branch-path-closure-readback-v1/logs/00_provider_status_agent.out`
- `branch-path-closure-readback-v1/logs/00_provider_status_agent.exit`

## Ordered Chain Readback

All recorded commands in `branch-path-closure-readback-v1/logs/*.exit` returned `0`. The Auto-Quant selected-wire ingest and all branch-feedback update command outputs in `b5-branch-feedback-calibration-v2/command-output/*.exit` also returned `0`.

Pre-Bayes/filter:

- Latest gate status: `pass_neutralized`.
- Branch path count preserved: `4`.
- The rooted branch-path set is visible in `latest_filtered_assignments`.

BBN:

- Read-only regime BBN decision: `accepted`.
- Soft evidence strength: `moderate`, weight `0.650`.
- Application status in the filtered assignments remains `skipped`; workflow traces also report `regime_bundle_bbn_evidence_skipped=no_supported_label`.
- Result: BBN evidence is visible/readable but not a promotable closed-loop posterior.

CatBoost/path-ranker:

- Structural target rows: `5`.
- Exact branch-path runtime matches: `4`.
- Runtime selection: enabled and ready.
- Production validation: `306/30`.
- Observation validation: `48/30`.
- The four exact branch rows carry raw path score `0.857407`, calibrated path probability `0.500000`, lower bound `0.190069`, and execution gate `observe`.

Execution tree/workflow:

- Structural bundle selects an exact rooted path, currently the Crisis branch, but keeps execution gate `observe`.
- Execution candidate is `actionable=false`, `candidate_status=no_trade`, `review_status=observe`.
- Workflow status is blocked with `user_selected_historical_data_missing`.

## Gate Result

RC-SPA source status remains the prior strict pass: `85.7407`, price roots `4/4`, scoped Manipulation pass upstream.

Downstream closure is verified but not promotable:

- `pass:branch_paths_preserved_through_path_ranker`
- `pass:commands_callable_and_exit_zero`
- `fail_closed:pre_bayes_pass_neutralized`
- `fail_closed:bbn_not_promotable_posterior`
- `fail_closed:path_ranker_execution_gate_observe`
- `fail_closed:execution_candidate_no_trade`
- `fail_closed:workflow_user_selected_historical_data_missing`

Promotion allowed: `false`.

## Next

The next smallest safe action is to select or obtain an explicit historical dataset for `SRC_ROOT_CARRY_LONG_220646` and rerun the recommended factor-research/factor-backtest path from the recorded `analyze_live_20260511T162824_*` files. Do not run another broad recipe scan unless it is a materially different Bull/Bear/Sideways/Crisis family or provider panel.
