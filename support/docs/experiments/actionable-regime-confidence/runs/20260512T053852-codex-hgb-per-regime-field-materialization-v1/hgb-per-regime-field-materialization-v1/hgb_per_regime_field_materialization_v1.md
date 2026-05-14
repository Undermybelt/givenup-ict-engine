# HGB Per-Regime Field Materialization v1

Run id: `20260512T053852-codex-hgb-per-regime-field-materialization-v1`

Gate result: `hgb_per_regime_field_materialization_v1=all_hgb_labels_field_complete_diagnostic_source_control_absent`

## Scope

This packet turns the accepted `051844` HGB diagnostic screen into explicit per-regime field evidence: qualifying condition, split validation, instruments, periods, and market contexts.

It is diagnostic only. It does not create source/control evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.

## Summary

| Label | Qualifying condition | 95 accepted | Min support | Min Wilson95 | Instruments | Periods | Contexts | Diagnostic field complete |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `Bear` | `hgb_numeric_probability(Bear) >= 0.98` | `true` | `177` | `0.9787578642` | `39` | `4` | `2` | `true` |
| `Bull` | `hgb_numeric_probability(Bull) >= 0.97` | `true` | `618` | `0.9908918883` | `39` | `4` | `2` | `true` |
| `Crisis` | `hgb_numeric_probability(Crisis) >= 0.985` | `true` | `547` | `0.9930261988` | `40` | `4` | `3` | `true` |
| `Sideways` | `hgb_numeric_probability(Sideways) >= 0.97` | `true` | `534` | `0.990666799` | `39` | `4` | `3` | `true` |

## Decision

- Diagnostic field-complete labels: `['Bear', 'Bull', 'Crisis', 'Sideways']`.
- Source/control evidence acquired `false`; canonical merge `false`; downstream promotion rerun `false`; trade usable `false`; `update_goal=false`.
- This packet can be used as per-regime diagnostic field evidence after source/control unlock, but it cannot unlock Board A promotion by itself.
