# R6 CFTC Schema-Ready Calibration Gate v1

- Decision: `r6_cftc_gandhi_calibration_gate_v2=schema_ready_but_calibration_blocked`.
- Positive rows: `4`; matched negative rows: `4`.
- Unique dates: `3`; symbols: `3`; venues: `1`.
- Wilson95 LCB positive/negative/min: `0.510109` / `0.510109` / `0.510109`.
- Chronological split ok: `true`; heldout symbol/venue ok: `true`.
- Broad normal sample: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Gates

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `positive_support` | `4` | `50` | `false` |
| `negative_support` | `4` | `50` | `false` |
| `chronological_split` | `3` | `2` | `true` |
| `heldout_symbol_or_venue` | `symbols=3;venues=1` | `symbol>=2 or venue>=2` | `true` |
| `wilson95_lcb` | `0.510109` | `>=0.95` | `false` |
| `broad_normal_sample` | `Derived only from public CFTC facts describing genuine iceberg order legs in the same examples; schema-ready/unscored seed, not a broad normal-activity calibration sample.` | `source-owned broad normal activity sample` | `false` |

## Interpretation

The current CFTC/FINRA intake is schema-ready only. It has 3 dates, 3 symbols, 1 venues, 4 positives, and 4 same-report control seeds. This cannot satisfy the unchanged Wilson95/support/broad-normal gates.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T210230-codex-r6-cftc-gandhi-calibration-gate-v2/r6-cftc-gandhi-calibration-gate/r6_cftc_schema_ready_calibration_gate_v1.json`
- Gate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T210230-codex-r6-cftc-gandhi-calibration-gate-v2/r6-cftc-gandhi-calibration-gate/r6_cftc_schema_ready_calibration_gate_v1_gates.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T210230-codex-r6-cftc-gandhi-calibration-gate-v2/checks/r6_cftc_schema_ready_calibration_gate_v1_assertions.out`
