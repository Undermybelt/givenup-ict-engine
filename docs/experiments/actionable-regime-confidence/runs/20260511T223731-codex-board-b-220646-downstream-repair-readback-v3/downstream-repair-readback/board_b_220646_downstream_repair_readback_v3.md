# Board B 220646 Downstream Repair Readback v3

- Decision: `not_promoted:execution_tree_closed_loop_confidence_still_missing`
- Bear BBN current binary: applied `True`, skipped-no-supported-label `False`
- Exact feedback export copy: current rows `6`, exact Board B rows `4`, score rows `4`, apply exit `0`
- NQ runtime target: rows `3`, exact Board B rows `0`, branch paths `4`, status `fail_closed:no_exact_bijection_in_nq_runtime_target`
- Promotion: blocked until the actual B5 downstream state emits exact branch paths through Pre-Bayes, BBN, CatBoost/path-ranker, and execution tree.

## Runtime Path IDs

- `path:scenario:NQ:belief_regime_node:range:range_mean_reversion:primary`
- `path:scenario:NQ:belief_regime_node:range:stress_de_risk:primary`
- `path:scenario:NQ:belief_regime_node:range:transition_confirmation:primary`

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T223731-codex-board-b-220646-downstream-repair-readback-v3/downstream-repair-readback/board_b_220646_downstream_repair_readback_v3.json`
- Exact score file: `docs/experiments/actionable-regime-confidence/runs/20260511T223731-codex-board-b-220646-downstream-repair-readback-v3/downstream-repair-readback/exact_branch_runtime_scores_v3.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T223731-codex-board-b-220646-downstream-repair-readback-v3/checks/board_b_220646_downstream_repair_readback_v3_assertions.out`
- Command outputs: `docs/experiments/actionable-regime-confidence/runs/20260511T223731-codex-board-b-220646-downstream-repair-readback-v3/command-output`
