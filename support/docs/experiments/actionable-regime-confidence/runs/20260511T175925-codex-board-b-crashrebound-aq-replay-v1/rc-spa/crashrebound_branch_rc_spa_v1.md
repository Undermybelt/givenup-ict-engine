# CrashRebound Branch RC-SPA v1

Run id: `20260511T175925-codex-board-b-crashrebound-aq-replay-v1`

## Decision

- RC-SPA: `0.0000`.
- Diagnostic score before hard-fail zeroing: `66.7300`.
- Promotion level: `reject`.
- Downstream status: `research_watch_branch_path_not_consumed`.

## Gates

- Non-overlapping trades: `205`.
- Test folds: `3`.
- Fold positive rate: `1.0000`.
- Bootstrap edge LCB 5pct: `0.007685`.
- 2x cost stress survival: `True`.
- PBO: `1.0000`.
- DSR proxy: `0.0577`.
- Tail loss p95: `0.1035`.
- Regime specificity ratio: `2.1624`.

## Hard Failures

- `reject_missing_branch_path:branch_path_is_proxy_not_recipe_or_board_a_trade_root`
- `reject_missing_branch_path:missing_roots=Crisis`
- `manipulation_overlay_not_observed`
- `reject_overfit_risk:min_test_folds_lt_4`
- `reject_overfit_risk:pbo_gt_0_25`

## Artifacts

- `trades_csv`: `docs/experiments/actionable-regime-confidence/runs/20260511T175925-codex-board-b-crashrebound-aq-replay-v1/rc-spa/crashrebound_trades_with_branch_paths.csv`
- `folds_csv`: `docs/experiments/actionable-regime-confidence/runs/20260511T175925-codex-board-b-crashrebound-aq-replay-v1/rc-spa/crashrebound_branch_fold_metrics.csv`
- `path_ranker_target_csv`: `docs/experiments/actionable-regime-confidence/runs/20260511T175925-codex-board-b-crashrebound-aq-replay-v1/rc-spa/crashrebound_path_ranker_target.csv`
- `bbn_rows_csv`: `docs/experiments/actionable-regime-confidence/runs/20260511T175925-codex-board-b-crashrebound-aq-replay-v1/rc-spa/crashrebound_bbn_evidence_rows.csv`
- `summary_json`: `docs/experiments/actionable-regime-confidence/runs/20260511T175925-codex-board-b-crashrebound-aq-replay-v1/rc-spa/crashrebound_rc_spa_summary.json`
- `bundle_json`: `docs/experiments/actionable-regime-confidence/runs/20260511T175925-codex-board-b-crashrebound-aq-replay-v1/rc-spa/crashrebound_regime_consumer_bundle.json`
- `report_md`: `docs/experiments/actionable-regime-confidence/runs/20260511T175925-codex-board-b-crashrebound-aq-replay-v1/rc-spa/crashrebound_branch_rc_spa_v1.md`
