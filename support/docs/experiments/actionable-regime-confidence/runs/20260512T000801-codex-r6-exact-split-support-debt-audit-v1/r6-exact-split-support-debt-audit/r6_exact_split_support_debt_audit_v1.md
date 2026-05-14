# R6 Exact Split Support Debt Audit v1

Run id: `20260512T000801-codex-r6-exact-split-support-debt-audit-v1`

## Result

- Live intake rows: positives `73`, matched controls `73`.
- All-correct Wilson95 support floor: `73` rows per class.
- Chronological gate: `false`; exact-symbol gate: `false`; exact-venue gate: `false`.
- Current chronological quantile gate needs at least `219` more positive/control rows before symbol/venue gates are considered.
- Exact-symbol existing-bucket debt: `2559` pairwise rows; exact-venue existing-bucket debt: `732` pairwise rows.
- Remaining not-materialized candidate positives: `19`; rows missing matched controls: `22`.
- Gate result: `r6_exact_split_support_debt_audit_v1=pooled95_passed_exact_split_row_debt_structural_blocker_quantified`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Boundary

This is a read-only support-debt audit. It does not relax the gate or claim acceptance. It shows that the current exact-symbol/exact-venue verifier is now the binding blocker, not pooled Wilson95 support.
