# R6 CFTC Schema-Ready Calibration Gate v1

- Decision: `r6_cftc_schema_ready_calibration_gate_v1=schema_ready_but_calibration_blocked`.
- Positive rows: `9`; matched negative rows: `9`.
- Unique dates: `6`; symbols: `4`; venues: `2`.
- Wilson95 LCB positive/negative/min: `0.700855` / `0.700855` / `0.700855`.
- Chronological split ok: `true`; heldout symbol/venue ok: `true`.
- Broad normal sample: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Gates

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `positive_support` | `9` | `50` | `false` |
| `negative_support` | `9` | `50` | `false` |
| `chronological_split` | `6` | `2` | `true` |
| `heldout_symbol_or_venue` | `symbols=4;venues=2` | `symbol>=2 or venue>=2` | `true` |
| `wilson95_lcb` | `0.700855` | `>=0.95` | `false` |
| `broad_normal_sample` | `Derived only from public CFTC facts describing genuine iceberg order legs in the same examples; schema-ready/unscored seed, not a broad normal-activity calibration sample.` | `source-owned broad normal activity sample` | `false` |

## Interpretation

The current CFTC/FINRA intake is schema-ready only. It has 6 dates, 4 symbols, 2 venues, 9 positives, and 9 same-report control seeds. This cannot satisfy the unchanged Wilson95/support/broad-normal gates.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T210030-codex-r6-cftc-schema-ready-calibration-gate-v1/r6-cftc-schema-ready-calibration-gate/r6_cftc_schema_ready_calibration_gate_v1.json`
- Gate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T210030-codex-r6-cftc-schema-ready-calibration-gate-v1/r6-cftc-schema-ready-calibration-gate/r6_cftc_schema_ready_calibration_gate_v1_gates.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T210030-codex-r6-cftc-schema-ready-calibration-gate-v1/checks/r6_cftc_schema_ready_calibration_gate_v1_assertions.out`
