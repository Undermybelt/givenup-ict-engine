# CFTC / FINRA Direct Public Positive Probe v1

Run ID: `20260511T205239+0800-codex-cftc-finra-direct-public-positive-probe-v1`

- Gate result: `cftc_finra_direct_public_positive_probe_v1=public_positives_extracted_controls_absent_blocked`.
- Public CFTC positive examples extracted: `2`.
- FINRA public layering/spoofing schema fields captured: `38`.
- Matched same-schema normal controls acquired: `false`.
- Verifier status: `blocked`.
- Verifier reason: `missing_required_files`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Public Sources Probed

- CFTC order: `https://www.cftc.gov/sites/default/files/2019-02/enfkrishnamohanorder022519.pdf`.
- FINRA public report-center schema: `https://www.finra.org/compliance-tools/report-center/cross-market-equities-supervision/potential-manipulation-report`.

## Intake Files

- Positive rows written to `/tmp`: `/tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv`.
- Provenance manifest written to `/tmp`: `/tmp/ict-engine-direct-manipulation-row-intake/provenance_manifest.json`.
- Matched negative normal activity rows: `/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv` missing.

## Boundary

The CFTC order supplies source-owned positive spoofing examples only. The FINRA page documents exception-report schema, but public access does not include firm-level monthly exception rows or matched normal controls. This run therefore keeps the direct Manipulation gate blocked and does not run chronological Wilson95 calibration.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T205239-codex-cftc-finra-direct-public-positive-probe-v1/cftc-finra-direct-public-positive-probe/cftc_finra_direct_public_positive_probe_v1.json`
- FINRA fields CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T205239-codex-cftc-finra-direct-public-positive-probe-v1/cftc-finra-direct-public-positive-probe/finra_layering_spoofing_public_schema_fields_v1.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T205239-codex-cftc-finra-direct-public-positive-probe-v1/checks/cftc_finra_direct_public_positive_probe_v1_assertions.out`
