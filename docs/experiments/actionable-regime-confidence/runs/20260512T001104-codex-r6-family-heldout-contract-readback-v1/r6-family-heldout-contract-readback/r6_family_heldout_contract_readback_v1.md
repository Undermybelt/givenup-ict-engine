# R6 Family Heldout Contract Readback v1

- Run id: `20260512T001104-codex-r6-family-heldout-contract-readback-v1`
- Live verifier: `schema_ready_unscored` rows `73/73`.
- Candidate contract replaces exact gate: `false`.
- Family axis pass: `false`.
- Family pairwise debt if all current family buckets must pass: `438`.
- Prior exact pairwise debt: `3291`.
- Best market family: `metals_futures` needs `34` paired rows.
- Best venue family: `metals_venues_comex_lme` needs `34` paired rows.
- Gate result: `r6_family_heldout_contract_readback_v1=family_contract_draft_reduces_exact_debt_but_gates_still_blocked`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Boundary
- This is a candidate contract/readback only. It preserves raw symbol and venue strings and does not waive chronology or species gates.
- No Board A confidence acceptance is claimed from this family grouping.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T001104-codex-r6-family-heldout-contract-readback-v1/r6-family-heldout-contract-readback/r6_family_heldout_contract_readback_v1.json`
- Contract CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T001104-codex-r6-family-heldout-contract-readback-v1/r6-family-heldout-contract-readback/r6_family_heldout_contract_v1.csv`
- Family metrics CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T001104-codex-r6-family-heldout-contract-readback-v1/r6-family-heldout-contract-readback/r6_family_heldout_contract_metrics_v1.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T001104-codex-r6-family-heldout-contract-readback-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T001104-codex-r6-family-heldout-contract-readback-v1/checks/r6_family_heldout_contract_readback_v1_assertions.out`

## Next
If the board/user accepts family-level heldout axes, source rows into metals_futures/metals_venues_comex_lme first; otherwise pursue a large owner-approved export for exact buckets. Either path still needs chronology and non-spoofing species closure.
