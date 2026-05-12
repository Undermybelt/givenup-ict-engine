# R6 Mohan Additional Row Uplift v1

- Gate result: `r6_mohan_additional_row_uplift_v1=direct_intake_rows_uplifted_schema_ready_calibration_still_blocked`.
- Positive rows now: `8`; added this run: `4`.
- Matched negative/control rows now: `8`; added this run: `4`.
- Verifier status: `schema_ready_unscored`; matched groups: `7`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Boundary

This expands the R6 spoofing/layering intake with additional row-level examples from the official CFTC Mohan complaint. It remains schema-ready/unscored only: support is still short and the matched controls are same-complaint genuine-order legs, not a broad normal-market sample.

## Verifier

```json
{
  "matched_group_count": 7,
  "matched_negative_rows": 8,
  "next": "run chronological and heldout-symbol/venue Wilson95 calibration gate",
  "positive_rows": 8,
  "provenance_keys": [
    "cftc_gandhi_order",
    "cftc_genuine_order_text_checks",
    "cftc_genuine_order_text_status",
    "cftc_mohan_additional_examples",
    "cftc_order",
    "cftc_text_checks",
    "cftc_text_extraction_status",
    "created_at_utc",
    "finra_public_schema",
    "gandhi_matched_negative_rows_added",
    "gandhi_positive_rows_added",
    "gandhi_rows_materialized_at_utc",
    "license_or_permission",
    "matched_control_limitations",
    "matched_control_policy",
    "matched_negative_control_policy",
    "matched_negative_materialized_at_utc",
    "matched_negative_rows_acquired",
    "matched_negative_rows_count",
    "matched_negative_rows_path",
    "matched_negative_rows_sha256",
    "mohan_additional_matched_negative_rows_added",
    "mohan_additional_positive_rows_added",
    "mohan_additional_rows_materialized_at_utc",
    "positive_rows_count",
    "positive_rows_path",
    "source",
    "updated_at_utc",
    "updated_by"
  ],
  "status": "schema_ready_unscored"
}
```

## Next Action

Acquire additional source-owned/owner-approved positive and broad same-schema normal-control rows across more symbols, venues, and periods; then run the chronological plus heldout-symbol/venue Wilson95 calibration gate before another completion audit.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T210744-codex-r6-mohan-additional-row-uplift-v1/r6-mohan-additional-row-uplift/r6_mohan_additional_row_uplift_v1.json`
- Intake summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210744-codex-r6-mohan-additional-row-uplift-v1/r6-mohan-additional-row-uplift/r6_mohan_additional_row_uplift_v1_intake_summary.csv`
- Calibration JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T210744-codex-r6-mohan-additional-row-uplift-v1/r6-mohan-additional-row-uplift/r6_cftc_schema_ready_calibration_gate_v1.json`
- Calibration report: `docs/experiments/actionable-regime-confidence/runs/20260511T210744-codex-r6-mohan-additional-row-uplift-v1/r6-mohan-additional-row-uplift/r6_cftc_schema_ready_calibration_gate_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T210744-codex-r6-mohan-additional-row-uplift-v1/checks/r6_mohan_additional_row_uplift_v1_assertions.out`
