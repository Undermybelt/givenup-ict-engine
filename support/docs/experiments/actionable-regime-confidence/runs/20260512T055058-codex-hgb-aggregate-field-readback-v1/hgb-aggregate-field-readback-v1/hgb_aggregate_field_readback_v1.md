# HGB Aggregate Field Readback v1

Run id: `20260512T055058-codex-hgb-aggregate-field-readback-v1`

Gate result: `hgb_aggregate_field_readback_v1=all_hgb_labels_aggregate_fields_present_source_control_absent`

## Scope

This readback maps the accepted `051844` HGB diagnostic confidence gates to explicit per-regime aggregate validation fields from the source-label equivalence intake.

Caveat: validation axes here are aggregate actual source-label rows for each regime, not exact HGB high-confidence selected rows. Exact high-confidence split support and Wilson95 values come from the `051844` HGB gate table.

## Summary

| Label | Qualifying condition | HGB 95 accepted | Min support | Min Wilson95 | Source rows | Instruments | Periods | Contexts | Aggregate fields present |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `Bear` | `hgb_numeric_probability(Bear) >= 0.98` | `true` | `177` | `0.9787578642` | `54939` | `39` | `4` | `2` | `true` |
| `Bull` | `hgb_numeric_probability(Bull) >= 0.97` | `true` | `618` | `0.9908918883` | `104979` | `40` | `4` | `3` | `true` |
| `Crisis` | `hgb_numeric_probability(Crisis) >= 0.985` | `true` | `547` | `0.9930261988` | `30623` | `40` | `4` | `3` | `true` |
| `Sideways` | `hgb_numeric_probability(Sideways) >= 0.97` | `true` | `534` | `0.990666799` | `57899` | `40` | `4` | `3` | `true` |

## Decision

- Diagnostic aggregate field-complete labels: `['Bear', 'Bull', 'Crisis', 'Sideways']`.
- Source/control evidence acquired `false`; canonical merge `false`; downstream promotion rerun `false`; trade usable `false`; `update_goal=false`.
- This readback can help audit per-regime fields after source/control unlock, but it cannot unlock Board A promotion by itself.
