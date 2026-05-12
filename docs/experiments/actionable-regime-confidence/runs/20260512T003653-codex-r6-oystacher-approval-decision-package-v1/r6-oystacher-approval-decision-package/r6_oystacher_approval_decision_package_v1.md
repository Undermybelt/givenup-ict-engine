# R6 Oystacher Approval Decision Package v1

Run ID: `20260512T003653-codex-r6-oystacher-approval-decision-package-v1`

This package does not approve canonical promotion. It isolates the two explicit decisions needed before any copy into the owner-export root or canonical live intake.

## Current evidence

- `SPOOF` positive candidates: `5182`.
- Same-exhibit `FLIP` rows: `1553`.
- Isolated verifier status: `schema_ready_unscored`.
- Isolated split axes pass: `True`.
- PDF SHA-256: `3ceb2758093d3ec9ec1a861ee1ab52074175517b158ffb50aff014ddac017a66`.

## Required decision

Choose exactly one decision option from `r6_oystacher_approval_options_v1.csv`. Until then, canonical merge and downstream rerun remain blocked.

## Gate

`r6_oystacher_approval_decision_package_v1=decision_package_ready_no_approval_no_merge`.
