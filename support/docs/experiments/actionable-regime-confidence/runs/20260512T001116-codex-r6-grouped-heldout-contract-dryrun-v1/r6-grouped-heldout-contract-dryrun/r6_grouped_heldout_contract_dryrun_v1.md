# R6 Grouped Heldout Contract Dry-Run v1

- Run id: `20260512T001116-codex-r6-grouped-heldout-contract-dryrun-v1`.
- Live verifier status: `schema_ready_unscored` with positives `73` and matched controls `73`.
- Exact split debt reference: `docs/experiments/actionable-regime-confidence/runs/20260512T000801-codex-r6-exact-split-support-debt-audit-v1/r6-exact-split-support-debt-audit/r6_exact_split_support_debt_audit_v1.json`.
- Grouped market-family pass: `false`.
- Grouped venue-family pass: `false`.
- Grouped contract pass: `false`.
- Owner-approved contract: `false`.
- Gate result: `r6_grouped_heldout_contract_dryrun_v1=grouped_contract_still_fails_owner_approval_required`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Summary

The grouped contract is not enough on the current row set. It reduces exact bucket debt conceptually, but current market-family and venue-family cells still fail support/Wilson gates, and no owner approval exists for replacing the exact split contract.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T001116-codex-r6-grouped-heldout-contract-dryrun-v1/r6-grouped-heldout-contract-dryrun/r6_grouped_heldout_contract_dryrun_v1.json`
- Metrics CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T001116-codex-r6-grouped-heldout-contract-dryrun-v1/r6-grouped-heldout-contract-dryrun/r6_grouped_heldout_contract_dryrun_v1_metrics.csv`
- Direct verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T001116-codex-r6-grouped-heldout-contract-dryrun-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`

## Next

Source a large owner-approved direct row export or obtain explicit approval for a different validation contract before another R6 split-acceptance attempt.
