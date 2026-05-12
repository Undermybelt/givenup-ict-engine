# Source Label Qualifying Condition Fail-Closed v1

- Decision: `source_label_qualifying_condition_failclosed_v1=conditions_present_but_no_acceptance`.
- Current cursor observed: `20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1`.
- Baseline calibration: `source_label_equivalence_confidence_calibration_v1=source_confidence_scored_no_acceptance`.
- Triage baseline: `source_label_high_confidence_subset_triage_v1=triage_only_no_acceptance` with candidate labels `['Bull', 'Sideways']`.
- Field-complete condition labels: `['Bull', 'Sideways']`.
- Accepted labels: `[]`; accepted rows added: `0`; new confidence gate: `false`.
- Canonical merge allowed: `false`; downstream chain rerun allowed: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Conditions

| Label | High-Conf Rows | Support Gate | Cross-Axis Fields | Date Range | Accepted | Blockers |
|---|---:|---|---|---|---|---|
| `Bull` | `10193` | `true` | `true` | `2000-01-21..2026-01-30` | `false` | `source_label_equivalence_confidence_calibration_v1_no_accepted_labels;r6_owner_controls_or_flip_approval_missing;canonical_merge_not_allowed;calibration_source_confidence_wilson95_below_0.95;heldout_market_source_confidence_wilson95_below_0.95;heldout_time_source_confidence_wilson95_below_0.95;test_source_confidence_wilson95_below_0.95` |
| `Sideways` | `8686` | `true` | `true` | `2000-01-21..2026-01-30` | `false` | `source_label_equivalence_confidence_calibration_v1_no_accepted_labels;r6_owner_controls_or_flip_approval_missing;canonical_merge_not_allowed;calibration_source_confidence_wilson95_below_0.95;heldout_market_source_confidence_wilson95_below_0.95;heldout_time_source_confidence_wilson95_below_0.95;test_source_confidence_wilson95_below_0.95` |

## Boundary

This repaired artifact restores the run root already referenced by the board. It preserves the fail-closed outcome: Bull and Sideways have explicit condition fields, but no labels are accepted because the baseline full-row source-confidence calibration, R6 owner-control gate, canonical merge gate, and downstream promotion gate remain blocked.
