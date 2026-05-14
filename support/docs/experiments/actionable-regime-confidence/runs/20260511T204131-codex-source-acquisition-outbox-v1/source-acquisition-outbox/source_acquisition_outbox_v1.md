# Source Acquisition Outbox v1

- Decision: `source_acquisition_outbox_v1=outbox_ready_rows_not_acquired`
- Prior v34 decision: `current_goal_completion_audit_v34=request_matrices_ready_rows_not_acquired_blocked`
- Outbox rows: `5`
- Required intake roots: `4`
- Request sent: `false`; rows acquired: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Outbox

| ID | Requirements | Required Files | Gate After Request |
|---|---|---|---|
| `R2-source-label-equivalence-crossmarket` | `R2` | `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json` | rerun source_label_equivalence_intake_verifier_v1.py |
| `R3-native-subhour-source-labels` | `R3` | `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json` | rerun native-subhour intake package check and source-label verifier if crosswalk rows are also supplied |
| `R4-R5-stock-regime-owner-recency-and-1h` | `R4;R5` | `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json` | rerun source_panel_recency_extension_verifier_v1.py and strict 1h source gates |
| `R6-do-putnins-spoofing-layering` | `R6` | `positive_spoofing_layering_rows.csv;matched_negative_normal_activity_rows.csv;provenance_manifest.json` | rerun direct_manipulation_row_intake_verifier_v1.py then chronological/heldout calibration |
| `R6-direct-manipulation-remaining-species` | `R6` | `positive_spoofing_layering_rows.csv;matched_negative_normal_activity_rows.csv;provenance_manifest.json` | extend direct verifier package and rerun strict R6 calibration |

## Boundary

This artifact is a send-ready queue only. It does not contact owners, use authenticated accounts, download private rows, create intake files, or promote proxy labels. The next real closure step is external acquisition of the required source-owned or owner-approved files, followed by the existing fail-closed verifiers.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T204131-codex-source-acquisition-outbox-v1/source-acquisition-outbox/source_acquisition_outbox_v1.json`
- Outbox CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T204131-codex-source-acquisition-outbox-v1/source-acquisition-outbox/source_acquisition_outbox_v1.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T204131-codex-source-acquisition-outbox-v1/checks/source_acquisition_outbox_v1_assertions.out`
