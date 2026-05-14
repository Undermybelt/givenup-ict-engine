# Source Label High-Confidence Subset Triage v1

- Decision: `source_label_high_confidence_subset_triage_v1=triage_only_no_acceptance`.
- Calibration baseline: `source_label_equivalence_confidence_calibration_v1=source_confidence_scored_no_acceptance`.
- Confidence threshold: `0.95`; min support per split: `50`.
- Candidate labels with high-confidence support across all splits plus >=2 market families: `['Bull', 'Sideways']`.
- Support-only candidates across all splits: `['Bull', 'Sideways']`.
- Missing confidence rows: `0`.
- Accepted rows added: `0`; new confidence gate: `false`; canonical merge allowed: `false`; downstream chain rerun allowed: `false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Label Summary

| Label | Total Rows | High-Conf Rows | Split Support Pass | Market Families | Candidate | Blockers |
|---|---:|---:|---|---:|---|---|
| `Bear` | `54939` | `52` | `false` | `2` | `false` | `calibration_high_conf_support_below_50;heldout_market_high_conf_support_below_50;heldout_time_high_conf_support_below_50;test_high_conf_support_below_50` |
| `Bull` | `104979` | `10193` | `true` | `3` | `true` | `` |
| `Crisis` | `30623` | `276` | `false` | `1` | `false` | `heldout_market_high_conf_support_below_50;cross_market_family_high_conf_coverage_below_2` |
| `Sideways` | `57899` | `8686` | `true` | `3` | `true` | `` |

## Boundary

This packet is triage only. It identifies whether a future qualifying-condition packet could use `source_confidence >= 0.95` as a candidate filter. It does not replace the existing source-confidence calibration gate, does not accept labels, and does not authorize downstream promotion.
