# R6 Logista CFTC Row Repair v1

- Decision: `r6_logista_cftc_row_repair_v1=source_rows_repaired_support_still_blocked`.
- Source: `CFTC Complaint: CFTC v. Logista Advisors LLC, Southern Trust Metals, Inc., Loreley Overseas Corp., and Michael Serotta, No. 1:23-cv-07485, Document 1`.
- Source URL: https://www.cftc.gov/media/9206/enflogistaadvisorscomplaint090723/download.
- Positive rows: `53` -> `53`; added `0`; repaired `0`; removed deprecated `0`.
- Matched negative rows: `53` -> `53`; added `0`; repaired `0`; removed deprecated `0`.
- Verifier status: `schema_ready_unscored`.
- Wilson95 min LCB: `0.932418`.
- Support floor `50/50` met: `true`.
- Broad normal sample: `false`; direct species closed: `false`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.

## Boundary

This repairs transient Logista row values against the official CFTC complaint text. The repaired rows remain same-event CFTC spoof/genuine-order examples, not broad normal-market controls.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T220556-codex-r6-logista-cftc-row-repair-v1/r6-logista-cftc-row-repair/r6_logista_cftc_row_repair_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T220556-codex-r6-logista-cftc-row-repair-v1/r6-logista-cftc-row-repair/r6_logista_cftc_row_repair_v1.md`
- Corrected rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T220556-codex-r6-logista-cftc-row-repair-v1/r6-logista-cftc-row-repair/r6_logista_cftc_row_repair_rows_v1.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T220556-codex-r6-logista-cftc-row-repair-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T220556-codex-r6-logista-cftc-row-repair-v1/checks/r6_logista_cftc_row_repair_v1_assertions.out`
