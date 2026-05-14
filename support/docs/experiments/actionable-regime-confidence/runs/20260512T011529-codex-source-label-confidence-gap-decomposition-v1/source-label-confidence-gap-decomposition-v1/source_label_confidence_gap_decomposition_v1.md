# Source-Label Confidence Gap Decomposition v1

- Run id: `20260512T011529-codex-source-label-confidence-gap-decomposition-v1`.
- Gate result: `source_label_confidence_gap_decomposition_v1=all_roots_confidence_quality_blocked_no_acceptance`.
- Board cursor observed: `20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1`.
- Source reconstruction run: `docs/experiments/actionable-regime-confidence/runs/20260512T010053-codex-source-label-equivalence-reconstruction-v1`.
- Source rows checked: `248440`.
- Accepted source-confidence labels before this decomposition: `[]`.
- New confidence gate: false. Accepted rows added: `0`.
- Thresholds relaxed: false. Runtime code changed: false. Shared intake mutated: false. Raw data committed: false.
- Downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: false.

## Label Summary

| label | accepted_source_confidence_95 | total_support_across_required_splits | total_rows_at_or_above_0_95 | worst_split | worst_wilson95_lcb | best_wilson95_lcb | blocking_splits | largest_per_split_new_perfect_rows_needed | diagnosis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bear | false | 54939 | 52 | heldout_time | 0.0 | 0.0011242749 | calibration;heldout_market;heldout_time;test | 632515 | confidence_quality_blocked_not_support_blocked |
| Bull | false | 104979 | 10193 | heldout_market | 0.0581218497 | 0.119416014 | calibration;heldout_market;heldout_time;test | 1043824 | confidence_quality_blocked_not_support_blocked |
| Crisis | false | 30623 | 276 | heldout_market | 0.0 | 0.0173592424 | calibration;heldout_market;heldout_time;test | 411962 | confidence_quality_blocked_not_support_blocked |
| Sideways | false | 57899 | 8686 | test | 0.1075825871 | 0.2056385432 | calibration;heldout_market;heldout_time;test | 559036 | confidence_quality_blocked_not_support_blocked |

## Diagnosis

All `16` label/split cells have enough support (`>=50`) but fail the Wilson95 lower-bound gate for rows whose source confidence is at least `0.95`. This is a source-confidence-quality blocker, not a support-count blocker. The current source-label equivalence root is schema-ready, but it cannot be promoted to the user's 95% cross-market/cross-period requirement without stronger source-owned confidence flags or additional high-confidence source rows.

R6 owner controls, R3 native sub-hour rows, and R5 post-`2026-01-30` recency-extension rows remain separate blockers. This packet does not unlock downstream promotion.
