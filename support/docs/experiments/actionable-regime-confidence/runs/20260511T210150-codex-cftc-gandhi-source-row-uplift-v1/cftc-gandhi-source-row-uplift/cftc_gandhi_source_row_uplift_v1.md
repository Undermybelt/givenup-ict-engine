# CFTC Gandhi Source Row Uplift v1

- Gate result: `cftc_gandhi_source_row_uplift_v1=direct_intake_rows_uplifted_schema_ready_unscored`.
- Previous cursor checked: `20260511T205654+0800-codex-cftc-matched-control-seed-v1`.
- Source: `https://www.cftc.gov/sites/default/files/2018-10/enfkamaldeepdandhiorder101118.pdf`.
- Positive rows now: `4`; added this run: `0`.
- Matched negative/control rows now: `4`; added this run: `0`.
- Verifier status: `schema_ready_unscored`; matched groups: `3`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Boundary

This expands the R6 spoofing/layering intake with two additional CFTC public-order examples from Gandhi. It is still schema-ready/unscored only: support is small, controls are same-report genuine-order seeds, and there is no chronological Wilson95 or heldout-symbol/venue acceptance.

## Verifier

```json
{
  "status": "schema_ready_unscored",
  "positive_rows": 4,
  "matched_negative_rows": 4,
  "matched_group_count": 3,
  "provenance_keys": [
    "cftc_gandhi_order",
    "cftc_genuine_order_text_checks",
    "cftc_genuine_order_text_status",
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
    "positive_rows_count",
    "positive_rows_path",
    "source",
    "updated_at_utc",
    "updated_by"
  ],
  "next": "run chronological and heldout-symbol/venue Wilson95 calibration gate"
}
```

## Next Action

Acquire additional source-owned/owner-approved positive and same-schema normal-control rows across more symbols, venues, and periods; then run the chronological plus heldout-symbol/venue Wilson95 calibration gate before another completion audit.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T210150-codex-cftc-gandhi-source-row-uplift-v1/cftc-gandhi-source-row-uplift/cftc_gandhi_source_row_uplift_v1.json`
- Intake summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210150-codex-cftc-gandhi-source-row-uplift-v1/cftc-gandhi-source-row-uplift/cftc_gandhi_source_row_uplift_v1_intake_summary.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T210150-codex-cftc-gandhi-source-row-uplift-v1/checks/cftc_gandhi_source_row_uplift_v1_assertions.out`
