# R6 Logista/Franko Row Uplift v1

- Decision: `r6_logista_franko_row_uplift_v1=support_50_50_reached_confidence_still_blocked`.
- Positive rows: `62` -> `65`; added `3`.
- Matched negative rows: `62` -> `65`; added `3`.
- Verifier status: `schema_ready_unscored`; matched groups `64`.
- Wilson95 LCB positive/negative/min: `0.944198` / `0.944198` / `0.944198`.
- Support floor `50/50` met: `true`; Wilson95 `>=0.95`: `false`.
- Broad normal sample: `false`; direct species closed: `false`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.

## Boundary

The added rows are official CFTC complaint/order event examples. The matched negatives are same-source genuine-order legs, so this slice closes the raw `50/50` support floor but does not provide independent broad normal-market controls or a 95% Wilson gate.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T221034-codex-r6-logista-franko-row-uplift-v1/r6-logista-franko-row-uplift/r6_logista_franko_row_uplift_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T221034-codex-r6-logista-franko-row-uplift-v1/r6-logista-franko-row-uplift/r6_logista_franko_row_uplift_v1.md`
- Rows added CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T221034-codex-r6-logista-franko-row-uplift-v1/r6-logista-franko-row-uplift/r6_logista_franko_row_uplift_rows_added_v1.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T221034-codex-r6-logista-franko-row-uplift-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T221034-codex-r6-logista-franko-row-uplift-v1/checks/r6_logista_franko_row_uplift_v1_assertions.out`
