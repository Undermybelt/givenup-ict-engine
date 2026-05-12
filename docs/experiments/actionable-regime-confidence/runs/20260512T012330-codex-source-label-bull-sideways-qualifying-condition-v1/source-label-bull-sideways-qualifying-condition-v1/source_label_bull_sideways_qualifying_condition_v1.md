# Source Label Bull/Sideways Qualifying Condition v1

- Decision: `source_label_bull_sideways_qualifying_condition_v1=conditions_drafted_cross_market_period_ok_timeframe_r6_baseline_blocked_no_acceptance`.
- Calibration baseline: `source_label_equivalence_confidence_calibration_v1=source_confidence_scored_no_acceptance`.
- Prior triage: `source_label_high_confidence_subset_triage_v1=triage_only_no_acceptance`.
- Confidence threshold: `0.95`; min support per split/period: `50`/`50`.
- Accepted labels: `0`; accepted rows added: `0`; canonical merge allowed: `false`; downstream chain rerun allowed: `false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Condition Summary

| Label | High-Conf Rows | Splits | Periods | Markets | Timeframes | Acceptance | Blockers |
|---|---:|---|---|---|---|---|---|
| `Bull` | `10193` | `true` | `true` | `true` | `false` | `blocked_no_acceptance` | `multi_timeframe_support_absent_only_1d;baseline_source_label_calibration_still_no_acceptance;r6_owner_control_blocker_still_active;canonical_merge_not_allowed` |
| `Sideways` | `8686` | `true` | `true` | `true` | `false` | `blocked_no_acceptance` | `multi_timeframe_support_absent_only_1d;baseline_source_label_calibration_still_no_acceptance;r6_owner_control_blocker_still_active;canonical_merge_not_allowed` |

## Boundary

This packet drafts explicit Bull and Sideways source-label qualifying conditions from the existing schema-ready source-label root. Both labels retain support across required splits, market families, and chronological periods, but the packet remains fail-closed because the evidence is daily-only, the baseline source-label calibration is still no-acceptance, and the active R6 owner-control blocker still prevents canonical merge and downstream promotion.
