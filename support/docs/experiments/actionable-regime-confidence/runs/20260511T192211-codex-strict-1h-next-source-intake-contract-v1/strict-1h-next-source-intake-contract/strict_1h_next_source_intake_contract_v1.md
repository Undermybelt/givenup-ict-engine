# Strict 1h Next Source Intake Contract v1

Run ID: `20260511T192211+0800-codex-strict-1h-next-source-intake-contract-v1`

This turns the post-future strict `1h` gap triage into an exact request contract for the next source-owned row drop. It is not evidence, does not provide rows, and does not create a confidence gate.

## Decision

`strict_1h_next_source_intake_contract_v1=request_contract_ready_no_rows_acquired`

- Target intake root: `/tmp/ict-engine-source-label-equivalence-intake`.
- Required files: `source_label_equivalence_rows.csv`, `source_label_equivalence_provenance.json`.
- Target rows specified: `4`.
- Minimum new source sessions for the first target: `5`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Required Verifier Shape

Use the existing source-label equivalence verifier:

```bash
python3 docs/experiments/actionable-regime-confidence/runs/20260511T182922-codex-source-label-equivalence-intake-verifier-v1/equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py --intake-root /tmp/ict-engine-source-label-equivalence-intake
```

For these strict `1h` source-extension rows, use verifier package id `native_subhour_overlap_after_recency`; do not invent a new `package_id` unless the verifier is updated first.

Disallowed equivalence-policy tokens:

- `ohlcv_proxy`
- `generated_label`
- `future_return`
- `unapproved_ixic`

## Next Requested Rows

| Priority | Symbol | Root | Split Role | Min New Source Sessions | Package ID |
|---:|---|---|---|---:|---|
| `1` | `XOM` | `Sideways` | `heldout_time` | `5` | `native_subhour_overlap_after_recency` |
| `2` | `UNH` | `Bear` | `calibration` | `7` | `native_subhour_overlap_after_recency` |
| `3` | `^DJI` | `Sideways` | `calibration` | `7` | `native_subhour_overlap_after_recency` |
| `4` | `AMD` | `Bear` | `calibration` | `10` | `native_subhour_overlap_after_recency` |

## Guardrails

- The rows must be source-owned or owner-approved labels.
- Provider OHLCV, HMM/generated labels, future-return labels, and unapproved taxonomy crosswalks do not count.
- This contract intentionally does not create `/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv`; a real source row drop must supply it.

