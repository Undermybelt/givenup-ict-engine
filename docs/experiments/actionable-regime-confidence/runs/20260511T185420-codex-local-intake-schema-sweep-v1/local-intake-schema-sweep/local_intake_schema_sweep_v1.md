# Local Intake Schema Sweep v1

Run ID: `20260511T185420-codex-local-intake-schema-sweep-v1`

Header/schema-only sweep over local candidate files from the Board A local acquisition ledger. Raw rows were not promoted and Current Cursor was not edited.

## Decision

`local_intake_schema_sweep_v1=no_exact_required_schema_match`

- Candidate files checked: `515`.
- Files with readable headers/keys/schema: `176`.
- Exact required schema matches: `0`.
- Strong partial schema matches: `0`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Schemas Checked

- `external_price_rows`: `17` required fields.
- `external_recency_rows`: `15` required fields.
- `direct_positive_rows`: `15` required fields.
- `direct_controls`: `11` required fields.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T185420-codex-local-intake-schema-sweep-v1/local-intake-schema-sweep/local_intake_schema_sweep_v1.json`
- Rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T185420-codex-local-intake-schema-sweep-v1/local-intake-schema-sweep/local_intake_schema_sweep_v1_rows.csv`
- Partial matches CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T185420-codex-local-intake-schema-sweep-v1/local-intake-schema-sweep/local_intake_schema_sweep_v1_partial_matches.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T185420-codex-local-intake-schema-sweep-v1/checks/local_intake_schema_sweep_v1_assertions.out`
