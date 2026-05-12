# R6 CFTC Schema-Ready Calibration Gate v1

- Decision: `r6_cftc_schema_ready_calibration_gate_v1=schema_ready_but_calibration_blocked`.
- Positive rows: `8`; matched negative rows: `8`.
- Unique dates: `5`; symbols: `4`; venues: `2`.
- Wilson95 LCB positive/negative/min: `0.675592` / `0.675592` / `0.675592`.
- Chronological split ok: `true`; heldout symbol/venue ok: `true`.
- Broad normal sample: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Gates

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `positive_support` | `8` | `50` | `false` |
| `negative_support` | `8` | `50` | `false` |
| `chronological_split` | `5` | `2` | `true` |
| `heldout_symbol_or_venue` | `symbols=4;venues=2` | `symbol>=2 or venue>=2` | `true` |
| `wilson95_lcb` | `0.675592` | `>=0.95` | `false` |
| `broad_normal_sample` | `Derived only from public CFTC facts describing genuine order legs in the same examples; schema-ready/unscored seed, not a broad normal-activity calibration sample.` | `source-owned broad normal activity sample` | `false` |

## Interpretation

The current CFTC/FINRA intake is schema-ready only. It has 5 dates, 4 symbols, 2 venues, 8 positives, and 8 same-report control seeds. This cannot satisfy the unchanged Wilson95/support/broad-normal gates.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T210744-codex-r6-mohan-additional-row-uplift-v1/r6-mohan-additional-row-uplift/r6_cftc_schema_ready_calibration_gate_v1.json`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210744-codex-r6-mohan-additional-row-uplift-v1/r6-mohan-additional-row-uplift/r6_cftc_schema_ready_calibration_gate_v1_gates.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T210744-codex-r6-mohan-additional-row-uplift-v1/checks/r6_cftc_schema_ready_calibration_gate_v1_assertions.out`
