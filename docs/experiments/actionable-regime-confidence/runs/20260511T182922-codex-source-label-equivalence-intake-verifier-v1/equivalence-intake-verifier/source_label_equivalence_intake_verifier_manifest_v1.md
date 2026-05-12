# Source Label Equivalence Intake Verifier v1

Run ID: `20260511T182922+0800-codex-source-label-equivalence-intake-verifier-v1`

This makes `source_label_equivalence_request_v1` executable. It does not accept rows or claim confidence.

## Result

- Target packages covered: `5`.
- Required CSV fields: `17`.
- Verifier missing-intake status: `blocked` / `missing_required_files`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Gate result: `source_label_equivalence_intake_verifier_v1=ready_rows_not_acquired`.
- Full objective achieved: `false`; `update_goal=false`.

## Required Intake Files

| File | Destination | Purpose |
|---|---|---|
| `source_label_equivalence_rows.csv` | `/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv` | source-owned or owner-approved price-root/direct-Manipulation label rows using the request schema |
| `source_label_equivalence_provenance.json` | `/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_provenance.json` | source owner, pull/approval date, export identity, hashes, and non-proxy attestation |

## Verifier

```bash
python3 docs/experiments/actionable-regime-confidence/runs/20260511T182922-codex-source-label-equivalence-intake-verifier-v1/equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py --intake-root /tmp/ict-engine-source-label-equivalence-intake
```

Schema readiness is not confidence acceptance; after a pass, rerun the unchanged gates.
