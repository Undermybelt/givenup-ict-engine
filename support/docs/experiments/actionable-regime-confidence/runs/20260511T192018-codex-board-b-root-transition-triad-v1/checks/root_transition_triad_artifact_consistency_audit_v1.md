# RootTransitionTriad Artifact Consistency Audit v1

Run id: `20260511T192018+0800-codex-board-b-root-transition-triad-v1`.

## Decision

Treat this run root as fail-closed due to concurrent artifact writes. Two metric packs exist and both reject promotion:

1. `uv_run` / `board_b_root_transition_triad_v1.py` pack:

- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T192018-codex-board-b-root-transition-triad-v1/branch-rc-spa/root_transition_triad_rc_spa_report_v1.json`
- Markdown report: `docs/experiments/actionable-regime-confidence/runs/20260511T192018-codex-board-b-root-transition-triad-v1/branch-rc-spa/root_transition_triad_rc_spa_report_v1.md`

This report is self-contained and says:

- `variant_trade_rows=61896`
- `selected_trade_rows=11633`
- `branch_paths_evaluated=5`
- `branch_paths_passed=0`
- `stable_profit_score=76.25`
- `gate_result=fail:required_root_branch_hard_gates_failed`

2. Concurrent `root_transition_triad_v1.py` pack:

- `branch-rc-spa/root_transition_triad_report_v1.json`
- `branch-rc-spa/root_transition_triad_report_v1.md`
- `branch-rc-spa/root_transition_triad_all_variant_rows_v1.csv`
- `ict-engine-fail-closed/root_transition_triad_real_trades_wire_v1.jsonl`

This report says:

- `variant_matrix_trade_rows=16418`
- `selected_trade_rows=3358`
- `branch_paths_evaluated=5`
- `branch_paths_passed=2`
- `stable_profit_score=90.78068231417511`
- `gate_result=fail:required_root_branch_hard_gates_failed`

## Shared File Collision

The two processes wrote overlapping shared file names. At the final observed state, `selected_rows`, `variant_rows`, `branch_summary`, `panel_summary`, `assertions`, and `root_transition_triad_rc_spa_report_v1.json` matched the final `uv_run` pack. The separate `root_transition_triad_report_v1.*` and `root_transition_triad_all_variant_rows_v1.csv` paths still preserve the concurrent earlier pack. Therefore the Board B cursor uses `root_transition_triad_rc_spa_report_v1.*` as the authoritative metric pack, and the earlier pack is supplemental fail-closed evidence only.

The ict-engine dry-run remains supplemental fail-closed evidence only. Its ledger records both the first preview and the latest refreshed preview:

- first preview parsed `2819/3358` rows and rejected `539`
- latest/current preview parsed `3358/3358` rows with `0` invalid (`force=true`, `dry_run=true`, `feedback_records_inserted=0`)
- Pre-Bayes status stayed unavailable
- structural path-ranking target export stayed missing
- workflow status stayed `no_workflow_state`

## Board B Effect

No downstream promotion is allowed. Even under the more favorable concurrent pack, every required root branch did not pass. Scoped `Manipulation` still has `0` trade/PnL rows. A clean rerun should use a fresh run root or non-overlapping file names before treating a numeric RC-SPA score as the active cursor metric.
