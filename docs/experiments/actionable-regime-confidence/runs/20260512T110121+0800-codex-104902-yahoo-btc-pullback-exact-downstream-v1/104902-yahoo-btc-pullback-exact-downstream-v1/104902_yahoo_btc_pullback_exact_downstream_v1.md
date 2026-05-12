# 104902 Yahoo BTC Pullback Exact Downstream v1

Run id: `20260512T110121+0800-codex-104902-yahoo-btc-pullback-exact-downstream-v1`

Gate result: `104902_yahoo_btc_pullback_exact_downstream_v1=exact_root_downstream_fail_closed`

## Scope

This packet downstream-tests the exact positive branch from source run `20260512T104902+0800-codex-board-b-yahoo-btc-pullback-precision-aq-v1`. It does not count a new AQ backtest recipe, does not satisfy the six-provider authority gate, does not approve selected history, does not approve source/control evidence, does not promote a candidate, and does not call `update_goal`.

## Source Evidence

- Source run: `docs/experiments/actionable-regime-confidence/runs/20260512T104902+0800-codex-board-b-yahoo-btc-pullback-precision-aq-v1`
- Source strategy: `ProviderCryptoPullbackRevertV1`
- Source branch path: `Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1`
- Source metrics: `146` BTC/USDT trades, `+2.83%` total profit, `45.2055%` win rate, `1.1186` profit factor, `0.1875` Sharpe, `-4.2915%` max drawdown
- Exact trade input: `derived/provider_crypto_pullback_revert_104902_exact_trades.jsonl`

## Ordered Readback

All commands exited `0`.

- `auto-quant-ingest-real-trades --dry-run`: previewed `146/146` trades, `0` invalid.
- `auto-quant-ingest-real-trades --force`: applied `146/146` trades, inserted `146` feedback records, and wrote BBN state under `state_ingest/auto-quant/B2R_YAHOO_BTC_PULLBACK_PRECISION_104902/`.
- `pre-bayes-status --refresh`: no latest policy, bridge, soft evidence, filtered assignments, canonical structural regime, or gate status.
- `export-structural-path-ranking-target`: exported `rows=1`, `history_rows=1`, `candidate_set_size=1`, `mature_rows=0`, and `history_mature_rows=0`.
- `policy-training-status` after export: entry models matched `0` rows; structural path ranker stayed disabled/not ready with `raw_scored_mature=0/30`, `production_validation=0/30`, `observation_validation=0/30`, calibration `not_fitted`, trainer artifact `missing`, and runtime selection `disabled`.
- `workflow-status --phase structural-recommended-path-bundle`: selected only `bootstrap_readiness` with `no_workflow_state`.
- `workflow-status --phase execution-candidate`: `ready=false`, `actionable=false`, `review_status=observe`, and empty Pre-Bayes gate status.
- Full `workflow-status --refresh`: `closed_loop_branch_admission.status=fail_closed`, reason `exact_structural_branch_visible_but_not_ready_or_actionable`.

## Decision

The exact source branch survives in the real-trade input and BBN ingest, but it does not survive into a usable structural/workflow branch. The downstream target and workflow collapse to bootstrap/no-workflow state, with no mature CatBoost/path-ranker rows and no execution-tree readiness.

Promotion allowed: `false`

`update_goal=false`

## Artifacts

- Command outputs: `command-output/`
- Exit files: `checks/`
- Exact source trades: `derived/provider_crypto_pullback_revert_104902_exact_trades.jsonl`
- Structural path target: `state_ingest/B2R_YAHOO_BTC_PULLBACK_PRECISION_104902/policy_training/structural_path_ranking_target.jsonl`
- Full workflow readback: `command-output/09_workflow_full.out`

## Next

Do not promote `104902` from exact-root downstream ingest alone. The next valid continuation is a provider-matrix-backed AQ packet, a source/control unlock, explicit selected-history approval, or a bridge repair that turns source-side `Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1` feedback into mature structural rows before CatBoost/path-ranker and execution-tree review.
