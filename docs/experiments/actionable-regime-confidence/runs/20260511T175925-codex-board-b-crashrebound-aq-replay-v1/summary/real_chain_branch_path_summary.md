# Real Chain Branch Path Summary

Run id: `20260511T175925-codex-board-b-crashrebound-aq-replay-v1`

## Decision

- Board B result: `reject`.
- RC-SPA: `0.0`.
- Diagnostic score before hard-fail zeroing: `66.7300`.
- Downstream status: `research_watch_branch_path_not_consumed`.
- Conservative branch-path addendum: `not_eligible_fail_closed`.
- Next action: rerun the recipe or next recipe with Board A trade-root labels emitted per trade, four independent folds, `Crisis` coverage, and an ict-engine path-ranker feature-schema bridge.

## Evidence

- Auto-Quant replay: `autoquant/crashrebound_replay.out`.
- Trade/fold extraction: `rc-spa/crashrebound_trades_with_branch_paths.csv`, `rc-spa/crashrebound_branch_fold_metrics.csv`.
- RC-SPA report: `rc-spa/crashrebound_branch_rc_spa_v1.md`, `rc-spa/crashrebound_rc_spa_summary.json`.
- BBN rows: `rc-spa/crashrebound_bbn_evidence_rows.csv`.
- CatBoost branch target and scores: `rc-spa/crashrebound_path_ranker_target.csv`, `catboost/crashrebound_path_scores.csv`.
- ict-engine dry run: `ict-engine/analyze_crashrebound_bundle_human.out`, `ict-engine/pre_bayes_status_human.out`, `ict-engine/policy_training_status_human.out`, `ict-engine/export_structural_target.json`.
- Conservative branch-path RC-SPA: `branch-path-rc-spa/rc_spa_report.json`, `branch-path-rc-spa/crashrebound_branch_trade_rows.csv`, `branch-path-rc-spa/crashrebound_branch_folds.csv`, `branch-path-rc-spa/payoff_report.json`.
- Fail-closed downstream handoff: `downstream-fail-closed/bbn_gate.json`, `downstream-fail-closed/path_ranker_handoff_summary.json`, `downstream-fail-closed/failure_memory.jsonl`.
- Isolated fail-closed ict-engine readback: `ict-engine-readback/pre-bayes-status.json`, `ict-engine-readback/policy-training-status.json`, `ict-engine-readback/workflow-status.json`.

## Conservative Branch-Path Addendum

- Generated at: `2026-05-11T10:12:17Z`.
- Branch-path decision: `reject`.
- RC-SPA: `0.0`.
- Trade rows: `207` full-replay trades plus `205` independent fold rows; the branch-path CSV contains `412` physical rows because it stores both the full-run diagnostic rows and the independent fold rows.
- Test folds: `3`; valid branch-path folds: `2`.
- Covered roots: `Bull`, `Bear`.
- Missing roots: `Sideways`, `Crisis`.
- Manipulation overlay covered: `false`.
- Hard gate failures: `reject_missing_branch_path`, `reject_no_positive_edge`, `reject_overfit_risk`.
- Conservative label rule: `recovery_23_25` is not a Board A accepted root and is marked `UnacceptedRecoveryContext`, so it is not counted as `Sideways` coverage.
- Downstream handoff: BBN consumes failure memory only; path-ranker target row count is `0`; execution tree is not eligible because there is no stable or pilot candidate.
- Isolated ict-engine readback: Pre-Bayes has no policy state, policy training has `0` matched rows, structural path-ranker runtime is disabled/missing target export, and workflow status is `insufficient_state`.

## Hard Failures

- `reject_missing_branch_path:branch_path_is_proxy_not_recipe_or_board_a_trade_root`
- `reject_missing_branch_path:missing_roots=Crisis`
- `manipulation_overlay_not_observed`
- `reject_overfit_risk:min_test_folds_lt_4`
- `reject_overfit_risk:pbo_gt_0_25`

## Downstream Readback

- Pre-Bayes loaded the bundle as read-only context.
- BBN mutation skipped with `regime_bundle_bbn_evidence_skipped=no_supported_label` because current BBN mapping does not consume `MainRegimeV2::*` branch labels.
- CatBoost trained and scored the generated branch target, but applying that branch model to the repo structural target failed with a feature-schema mismatch.
- Execution tree stayed `observe/transition_guardrail/guarded`; path-ranker score was not visible or used by execution tree.

## Provider Readback

Provider evidence for this Board B slice is in sibling run `docs/experiments/actionable-regime-confidence/runs/20260511T172521-codex-real-provider-branch-chain-v1/provider/`.

- `yfinance`: ready; fetched QQQ 1h, 190 rows from 2026-04-01 to 2026-05-08.
- `tradingview_mcp`: ready in provider-status/harness plan.
- `kraken`: public fetch succeeded for XBTUSD 1h, 721 rows from 2026-04-11 to 2026-05-11; `kraken_cli` also ready in provider-status.
- `ibkr`: attempted, but remained blocked by local runtime dependencies (`redis`/`ib_async` path); provider-status reported gateway reachable but runtime unhealthy.
