# Live Public Acquisition Recheck v36

- Decision: `live_public_acquisition_recheck_v36=no_new_public_rows_intakes_still_absent_blocked`
- Kaggle dataset: `mafaqbhatti/stock-market-regimes-20002026`
- Kaggle pull root: `/tmp/ict-engine-kaggle-stock-regimes-live-refresh-v36`
- Kaggle date max: `2026-01-30`
- Kaggle post-cutoff target rows after `2026-01-30`: `0`
- Recency intake materialized: `false`
- Ready intake roots: `0/4`.
- External authenticated/request messages sent: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Intake Roots

| Root | Ready | Missing Files |
|---|---:|---|
| `source_label_equivalence` | `false` | `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json` |
| `native_subhour_source_label` | `false` | `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json` |
| `source_panel_recency_extension` | `false` | `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json` |
| `direct_manipulation_row_intake` | `false` | `positive_spoofing_layering_rows.csv;matched_negative_normal_activity_rows.csv;provenance_manifest.json` |

## Target Cells

| Symbol | Label | Split Role | Required New Sessions | Post-Cutoff Rows | Total Rows |
|---|---|---|---:|---:|---:|
| `XOM` | `Sideways` | `heldout_time` | 5 | 0 | 2067 |
| `UNH` | `Bear` | `calibration` | 7 | 0 | 1225 |
| `^DJI` | `Sideways` | `calibration` | 7 | 0 | 2198 |
| `AMD` | `Bear` | `calibration` | 10 | 0 | 1667 |

## Result

The public Kaggle refresh did not produce post-cutoff target rows, and no required source-owned or owner-approved files are present in the four intake roots. The outbox remains the controlling closure path, but it cannot be sent without explicit user approval.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T204803-codex-live-public-acquisition-recheck-v36/live-public-acquisition-recheck/live_public_acquisition_recheck_v36.json`
- Intake-root CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T204803-codex-live-public-acquisition-recheck-v36/live-public-acquisition-recheck/live_public_acquisition_recheck_v36_intake_roots.csv`
- Kaggle target CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T204803-codex-live-public-acquisition-recheck-v36/live-public-acquisition-recheck/live_public_acquisition_recheck_v36_kaggle_targets.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T204803-codex-live-public-acquisition-recheck-v36/checks/live_public_acquisition_recheck_v36_assertions.out`
