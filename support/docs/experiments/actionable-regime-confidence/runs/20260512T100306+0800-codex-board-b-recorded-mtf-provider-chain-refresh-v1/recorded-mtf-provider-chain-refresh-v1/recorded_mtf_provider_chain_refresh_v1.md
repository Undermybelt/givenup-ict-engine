# Recorded MTF Provider Chain Refresh v1

Run id: `20260512T100306+0800-codex-board-b-recorded-mtf-provider-chain-refresh-v1`

Mode: `incubation_only`

Source nursery packet: `20260512T092330+0800-codex-board-b-aq-first-nursery-feedback-v1`

State copy used for readback: `/tmp/ict-engine-20260512T100306-state`

## Scope

Fresh non-promoting readback for the strongest current Board B nursery signal: the precision-fixed recorded MTF branch.

This run does not select `HTF`, `MTF`, or `LTF` for the user, does not approve source/control evidence, does not mutate the prior run state, does not promote a candidate, and does not call `update_goal`.

## Branch Path

`Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`

## Commands

All recorded command exits were `0`.

- `provider-status --agent`
- `provider-status --jsonl`
- `workflow-status --refresh --agent`
- `pre-bayes-status --refresh --human`
- `pre-bayes-status --refresh`
- `workflow-status --phase pre-bayes-policy --agent`
- `workflow-status --phase pre-bayes-soft-evidence --agent`
- `workflow-status --phase structural-path-ranking-target --agent`
- `workflow-status --phase structural-recommended-path-bundle --agent`
- `workflow-status --phase execution-candidate --agent`
- `workflow-status --phase execution-candidate-history --agent`
- `policy-training-status --human`
- `export-structural-path-ranking-target`
- `pandas_path_ranker_trainer.py` CatBoost train via `uv run --with catboost`
- `pandas_path_ranker_trainer.py --apply` to current target
- `register-structural-path-ranking-trainer-artifact`
- `apply-structural-path-ranking-external-scores`
- `enable-structural-path-ranking-runtime --reuse-mode candidate_set_only`
- post-CatBoost `policy-training-status`
- post-CatBoost `workflow-status --phase structural-recommended-path-bundle`
- post-CatBoost `workflow-status --phase execution-candidate`

## Provider Readback

- `yfinance`: live runtime ready and market-data ready.
- `TradingViewRemix / tradingview_mcp`: not ready; `tradingview_mcp_connectivity_probe_failed`.
- `IBKR`: not ready for market-data; `ibkr_runtime_dependencies_missing_with_gateway_reachable`.
- `Kraken`: `kraken_cli` ready; `kraken_public` not ready because Python provider dependencies are missing.

## Pre-Bayes / BBN

- Pre-Bayes gate: `pass_neutralized`.
- BBN soft evidence was applied into the filter surface.
- Market-regime soft evidence: `range=0.65`, `bear=0.175`, `bull=0.175`.
- Read-only regime BBN label set preserved the branch path and marked `read_only_regime_bbn_trade_usable=true`.

## CatBoost / Path-Ranker

- Exported target: `6` current rows, `295` history rows, `288` mature history rows.
- CatBoost trainer output: `catboost_model.cbm`.
- Training rows: `288`.
- Usable feature set: `structural_baseline_score` only.
- Current-score rows: `6`.
- Crisis branch CatBoost raw score: `0.9336295132673809`.
- ict-engine consumed the scores as `runtime_source=registered_artifact`, `score_model_family=catboost`, `score_source=external_artifact`, `runtime_matches=3`.

## Execution Tree

- The exact rooted path survived into `execution-candidate`.
- Post-CatBoost execution candidate:
  - `ready=false`
  - `review_status=observe`
  - `candidate_status=execution_observe_only`
  - `execution_readiness=0.4504361163104953`
  - `pre_bayes_gate_status=pass_neutralized`
  - `selected_path_probability=0.41526935554751543`
- The structural bundle still emits `recommended_next_step.action_type=ask_user_choose_historical_data` with `blocked_reason=user_selected_historical_data_missing`.

## Decision

Gate: `incubation_only:recorded_mtf_catboost_registered_artifact_observe_only`.

This slice proves the ordered runtime surfaces are callable and branch-preserving on the recorded MTF nursery path:

`provider -> Pre-Bayes/filter -> BBN soft evidence -> CatBoost/path-ranker -> execution-candidate`.

It does not open production promotion. Promotion remains blocked by:

- explicit selected-history approval missing,
- source/control unlock missing,
- Pre-Bayes still `pass_neutralized`,
- execution tree still `observe` / `ready=false`.

Promotion allowed: `false`.

`update_goal=false`.

## Artifacts

- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T100306+0800-codex-board-b-recorded-mtf-provider-chain-refresh-v1/checks/recorded_mtf_provider_chain_refresh_v1_assertions.out`
- CatBoost model: `docs/experiments/actionable-regime-confidence/runs/20260512T100306+0800-codex-board-b-recorded-mtf-provider-chain-refresh-v1/catboost-path-ranker/catboost_model.cbm`
- CatBoost current scores: `docs/experiments/actionable-regime-confidence/runs/20260512T100306+0800-codex-board-b-recorded-mtf-provider-chain-refresh-v1/catboost-path-ranker/current_scores.csv`
- Raw command output directory: `docs/experiments/actionable-regime-confidence/runs/20260512T100306+0800-codex-board-b-recorded-mtf-provider-chain-refresh-v1/raw/`
