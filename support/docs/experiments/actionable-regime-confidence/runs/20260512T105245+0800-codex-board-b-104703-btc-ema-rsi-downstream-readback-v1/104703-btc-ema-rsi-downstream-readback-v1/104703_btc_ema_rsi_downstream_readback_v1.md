# 104703 BTC EMA/RSI Downstream Readback v1

Run id: `20260512T105245+0800-codex-board-b-104703-btc-ema-rsi-downstream-readback-v1`

Gate result: `104703_btc_ema_rsi_downstream_readback_v1=positive_provider_owned_branch_fail_closed`

## Scope

This packet registers and downstream-tests the source run `20260512T104703+0800-codex-board-b-provider-btc-ema-rsi-noncanary-v1`. It does not edit the Board B Current Cursor, does not approve selected history, does not approve source/control evidence, does not mutate canonical state, does not make a trade-usable claim, does not promote a candidate, and does not call `update_goal`.

## Source AQ Evidence

- Source workspace: `docs/experiments/actionable-regime-confidence/runs/20260512T104703+0800-codex-board-b-provider-btc-ema-rsi-noncanary-v1/workspace/auto-quant-provider-btc-ema-rsi-noncanary`
- Strategy: `ProviderBtcEmaRsiHold12`
- Provider/source lineage: copied from the provider BTC canary workspace, but the strategy logic is non-canary EMA/RSI continuation with a fixed 12-hour risk horizon.
- Explicit rooted branch path: `Bull -> ProviderTrend -> EmaRsiContinuation -> ProviderBtcEmaRsiHold12`
- Timerange: `20260401-20260512`
- Pair: `BTC/USDT`
- Metrics: `42` trades, `69.0476%` win rate, `+22.60%` total profit, `2.9309` profit factor, `9.2978` Sharpe, `-2.9274%` max drawdown.

## Downstream Readback

Isolated state dir: `/tmp/ict-engine-20260512T105245+0800-codex-board-b-104703-btc-ema-rsi-downstream-readback-v1-state`

All readback commands exited `0`:

- `auto-quant-results-import`: `1/1` strategy imported, `n_meta_invalid=0`.
- `auto-quant-prior-init --force`: applied in isolated state, `dry_run=false`, `evidence_value_gate_passed=true`, `trade_count=42`, `n_win=29`, `n_loss=13`.
- `pre-bayes-status --refresh`: no latest policy, bridge, soft evidence, filtered assignments, canonical structural regime, or gate status.
- `export-structural-path-ranking-target`: produced a target, but only bootstrap/no-workflow rows.
- `policy-training-status` after export: `raw_scored_mature=0/30`, `production_validation=0/30`, `observation_validation=0/30`, trainer artifact `missing`, runtime selection `disabled`.
- `workflow-status --phase structural-recommended-path-bundle`: path fell back to `bootstrap_readiness`.
- `workflow-status --phase execution-candidate`: `ready=false`, `actionable=false`, `review_status=observe`.
- Full `workflow-status`: `closed_loop_branch_admission.status=fail_closed` with reason `exact_structural_branch_visible_but_not_ready_or_actionable`.

## Decision

This is the strongest recent non-canary AQ branch signal inspected in this slice, but it still fails the promotion chain. The branch is profitable at TOMAC/AQ level and BBN prior application succeeds in isolated state; however, the imported branch has no pre-Bayes policy, no mature CatBoost/path-ranker rows, no trainer artifact, no runtime selection, and no workflow snapshot preserving the branch beyond bootstrap readiness.

Promotion allowed: `false`

`update_goal=false`

## Artifacts

- Strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T105245+0800-codex-board-b-104703-btc-ema-rsi-downstream-readback-v1/104703-btc-ema-rsi-downstream-readback-v1/strategy_library_104703_btc_ema_rsi_noncanary_v1.json`
- Import stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T105245+0800-codex-board-b-104703-btc-ema-rsi-downstream-readback-v1/command-output/01_auto_quant_results_import.out`
- BBN prior stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T105245+0800-codex-board-b-104703-btc-ema-rsi-downstream-readback-v1/command-output/02_auto_quant_prior_init_apply.out`
- Policy/CatBoost readback: `docs/experiments/actionable-regime-confidence/runs/20260512T105245+0800-codex-board-b-104703-btc-ema-rsi-downstream-readback-v1/command-output/06_policy_training_status_after_export.out`
- Execution candidate readback: `docs/experiments/actionable-regime-confidence/runs/20260512T105245+0800-codex-board-b-104703-btc-ema-rsi-downstream-readback-v1/command-output/08_workflow_execution_candidate.out`
- Full workflow readback: `docs/experiments/actionable-regime-confidence/runs/20260512T105245+0800-codex-board-b-104703-btc-ema-rsi-downstream-readback-v1/command-output/09_workflow_full.out`

## Next

The useful follow-up is not another provider-status or canary rerun. Continue from this candidate only if it is converted into structural feedback/training rows that preserve `Bull -> ProviderTrend -> EmaRsiContinuation -> ProviderBtcEmaRsiHold12` through Pre-Bayes, CatBoost/path-ranker, and execution tree, or extend it across additional provider/time/market contexts before retrying promotion.
