# Direct Manipulation Row Intake Manifest v1

Run ID: `20260511T151950+0800-codex-direct-manipulation-row-intake-manifest-v1`

This turns the remaining direct `Manipulation` blocker into an executable intake package. It does not accept proxy rows or claim new confidence.

## Result

- Target variety: `spoofing_layering`.
- Schema fields: `24`; required fields: `17`.
- Accepted direct rows added: `0`.
- Gate result: `direct_manipulation_row_intake_manifest_v1=ready_rows_not_acquired`.
- Full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Required Intake Files

| File | Destination | Purpose |
|---|---|---|
| `positive_spoofing_layering_rows.csv` | `/tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv` | direct positive spoofing/layering rows |
| `matched_negative_normal_activity_rows.csv` | `/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv` | same-schema normal controls matched by venue/symbol/date/session/liquidity bucket |
| `provenance_manifest.json` | `/tmp/ict-engine-direct-manipulation-row-intake/provenance_manifest.json` | source export identity, pull date, source owner, redaction notes |

## Verifier

```bash
python3 docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py --intake-root /tmp/ict-engine-direct-manipulation-row-intake
```

The verifier is fail-closed: missing files, missing fields, empty positives/negatives, or positives without matched negative groups block the gate.

## Guardrails

- Public docs without row exports remain schema evidence only.
- OHLCV/session/liquidity/sweep/HMM/model labels remain rejected proxies.
- Synthetic or teaching datasets are not accepted unless they prove real direct order-lifecycle provenance.
- Enforcement case metadata without matched negatives remains positive inventory only.
