# 104703 Structural Feedback Replay Corrected Partial v1

Run id: `20260512T110221+0800-codex-104703-structural-feedback-replay-v1`

Gate result: `104703_structural_feedback_replay_corrected_partial_v1=one_structural_feedback_partial_replay_mature_floor_not_met_fail_closed`

## Scope

This packet corrects the earlier readback that saw only the failed `127` wrapper execution for this run root. It preserves the failed wrapper steps, the corrected materialization, the operator-terminated partial replay, and the post-partial readback. It does not promote the branch or call `update_goal`.

## Evidence

- Source branch: `Bull -> ProviderTrend -> EmaRsiContinuation -> ProviderBtcEmaRsiHold12`.
- Materialized candles: `985` BTC/USDT 1h rows from the 104703 provider-backed feather.
- Early failures: materialization wrapper exit `1`, command-string wrapper exit `127`.
- Corrected materialization exit: `0`.
- Corrected replay exit: `143`; stopped after partial replay because 35 observations were too slow for the shared board run.
- Partial feedback files: `1`.
- Analyze/update readback: analyze_runs `2`, update_runs `1`.
- Structural target: rows `3`, history_rows `10`, mature_rows `1`, history_mature_rows `4`.
- Ranker validation: `Ranker validation: calibration=true quality_ready=true raw_scored_mature=3/30 production_validation=2/30 observation_validation=1/30 ready=false`.
- Execution candidate: ready `False`, actionable `False`, review `observe`.
- Workflow: `fail_closed` / `exact_structural_branch_visible_but_not_ready_or_actionable`.

## Decision

The corrected run proves the structural-feedback path is not blocked by the earlier shell-wrapper failure: one structural feedback update reached the state and changed the path-ranker surface from pure zero to partial observations. It still does not meet promotion floors: `raw_scored_mature=3/30`, `production_validation=2/30`, and `observation_validation=1/30`; entry-model matched rows are still `0`, the trainer artifact is missing, runtime selection is disabled, and execution remains fail-closed.

Accepted rows added: `0`. Mature rooted branch observations promoted: `0`. Six-provider matrix satisfied: false. Downstream promotion: false. Strict full objective: false. Trade usable: false. Promotion allowed: false. `update_goal=false`.

## Next

Do not count the older `127` wrapper failure as the final state of this root. Future work can resume from a smaller bounded structural-feedback replay or a faster direct real-trade structural-feedback enrichment path, but this partial packet does not authorize promotion.
