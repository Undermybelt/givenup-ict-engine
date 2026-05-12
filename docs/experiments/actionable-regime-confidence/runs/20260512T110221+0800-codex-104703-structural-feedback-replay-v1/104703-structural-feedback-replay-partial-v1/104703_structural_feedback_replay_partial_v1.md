# 104703 Structural Feedback Replay Partial v1

Run id: `20260512T110221+0800-codex-104703-structural-feedback-replay-v1`

Gate result: `104703_structural_feedback_replay_partial_v1=partial_mature_observation_fail_closed`

## Scope

This packet registers a partial structural-feedback replay for source branch `20260512T104703+0800-codex-board-b-provider-btc-ema-rsi-noncanary-v1`.
It does not edit Board B Current Cursor, approve selected history, approve source/control evidence, satisfy the six-provider authority gate, train/register CatBoost, enable path-ranker runtime, promote execution-tree output, make a trade claim, or call `update_goal`.

## Source Context

- Source strategy: `ProviderBtcEmaRsiHold12`
- Source branch path: `Bull -> ProviderTrend -> EmaRsiContinuation -> ProviderBtcEmaRsiHold12`
- Source AQ result already registered via `105445`: `42` BTC/USDT trades, `+22.60%` total profit, Sharpe `9.2978`, win rate `69.0476%`, profit factor `2.9309`, max drawdown `-2.9274%`.

## Replay Readback

- Candle materialization first failed, then corrected materialization exited `0`.
- First replay command failed with `127`.
- Corrected replay command terminated with `143` after producing partial replay state.
- One structural feedback observation was emitted at `replay/feedback/structural_feedback_obs_01.json`.
- The observation had `followed_path=true`, `realized_outcome=win`, `realized_pnl=0.008412209719880881`, `exit_reason=forward_12_bar_close`, and `pre_bayes_gate_status=pass_neutralized`.
- Partial policy-training readback exited `0`.

## Path-Ranking Readback

- Structural target summary: `rows=3`, `history_rows=10`, `mature_rows=1`, `history_mature_rows=4`.
- Validation improved from the earlier zero-row state but stayed below gates: `raw_scored_mature=3/30`, `production_validation=2/30`, `observation_validation=1/30`.
- Calibration was evaluated, but CatBoost/path-ranker trainer artifact was `missing` and runtime selection stayed `disabled`.
- Exported current target rows still have empty `regime_profit_branch_path`, `main_regime`, `sub_regime`, `sub_sub_regime_or_profit_factor`, and `profit_factor` fields, so the source AQ branch path did not survive as the required Board B branch shape.

## Decision

This is a useful nursery datapoint because it creates one mature structural-feedback win observation for the `104703` symbol and moves the path-ranking surface away from pure bootstrap. It is not promotion evidence. The required source branch path is not preserved in the structural target row, validation remains far below `30` mature rows, and no CatBoost/path-ranker runtime or execution-tree promotion exists.

Promotion allowed: `false`

`update_goal=false`

## Artifacts

- Feedback observation: `docs/experiments/actionable-regime-confidence/runs/20260512T110221+0800-codex-104703-structural-feedback-replay-v1/replay/feedback/structural_feedback_obs_01.json`
- Partial policy readback: `docs/experiments/actionable-regime-confidence/runs/20260512T110221+0800-codex-104703-structural-feedback-replay-v1/command-output/04_policy_training_status_partial.out`
- Structural target export: `docs/experiments/actionable-regime-confidence/runs/20260512T110221+0800-codex-104703-structural-feedback-replay-v1/command-output/05_export_structural_path_ranking_target_partial.out`
- Target summary: `docs/experiments/actionable-regime-confidence/runs/20260512T110221+0800-codex-104703-structural-feedback-replay-v1/replay/state/B2R_PROVIDER_BTC_EMA_RSI_104703/policy_training/structural_path_ranking_target_summary.json`

## Next

Do not promote from this partial replay. The next useful work is to make the structural-feedback owner preserve `Bull -> ProviderTrend -> EmaRsiContinuation -> ProviderBtcEmaRsiHold12` into `regime_profit_branch_path` and the `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor` columns, then gather enough mature observations for CatBoost/path-ranker validation and execution-tree review.
