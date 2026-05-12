# R6 Matched Control Readback v1

- Gate result: `r6_matched_control_readback_v1=direct_intake_schema_ready_unscored_confidence_gate_false`.
- Previous cursor checked: `20260511T205654+0800-codex-cftc-matched-control-seed-v1`.
- Positive source-owned CFTC spoofing/layering rows present: `2`.
- Provenance manifest present: `True`.
- Required same-schema matched normal-control rows present: `2`.
- Verifier return code: `0`.
- Verifier status: `schema_ready_unscored`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Source Boundary

- CFTC public material supports positive spoofing/layering examples and provenance.
- Same-report CFTC genuine-order legs now provide a same-schema control seed.
- FINRA public material supports schema/report-center routing for potential-manipulation exceptions, not broad public normal-market exports.
- This is schema readiness only: the two-positive/two-control same-report seed is too small for chronological Wilson95 calibration or heldout-symbol/venue validation.
- I did not derive controls from OHLCV or claim full direct `Manipulation` species coverage.

## Verifier

```json
{
  "status": "schema_ready_unscored",
  "positive_rows": 2,
  "matched_negative_rows": 2,
  "matched_group_count": 1,
  "provenance_keys": [
    "cftc_genuine_order_text_checks",
    "cftc_genuine_order_text_status",
    "cftc_order",
    "cftc_text_checks",
    "cftc_text_extraction_status",
    "created_at_utc",
    "finra_public_schema",
    "license_or_permission",
    "matched_control_limitations",
    "matched_control_policy",
    "matched_negative_control_policy",
    "matched_negative_materialized_at_utc",
    "matched_negative_rows_acquired",
    "matched_negative_rows_count",
    "matched_negative_rows_path",
    "matched_negative_rows_sha256",
    "positive_rows_path",
    "source",
    "updated_at_utc",
    "updated_by"
  ],
  "next": "run chronological and heldout-symbol/venue Wilson95 calibration gate"
}
```

## Next Action

Acquire additional source-owned/owner-approved positive and same-schema normal-control rows across more symbols, venues, and periods; then run the chronological plus heldout-symbol/venue Wilson95 calibration gate before any completion audit.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T205810-codex-r6-matched-control-failclosed-readback-v1/r6-matched-control-failclosed-readback/r6_matched_control_failclosed_readback_v1.json`
- Intake CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T205810-codex-r6-matched-control-failclosed-readback-v1/r6-matched-control-failclosed-readback/r6_matched_control_failclosed_readback_v1_intake_files.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T205810-codex-r6-matched-control-failclosed-readback-v1/checks/r6_matched_control_failclosed_readback_v1_assertions.out`
