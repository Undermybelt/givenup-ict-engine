# R6 Mohan Complaint Expansion Gate v1

- Decision: `r6_mohan_complaint_expansion_gate_v1=schema_ready_but_calibration_blocked`.
- Verifier status: `schema_ready_unscored`.
- Positive rows: `9`; matched negative rows: `9`.
- Unique dates: `6`; symbols: `4`; venues: `2`; matched groups: `8`.
- Wilson95 LCB positive/negative/min: `0.700855` / `0.700855` / `0.700855`.
- Chronological split ok: `true`; heldout symbol/venue ok: `true`.
- Broad normal sample: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Gates

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `schema_verifier` | `schema_ready_unscored` | `schema_ready_unscored` | `true` |
| `positive_support` | `9` | `50` | `false` |
| `negative_support` | `9` | `50` | `false` |
| `chronological_split` | `6` | `2` | `true` |
| `heldout_symbol_or_venue` | `symbols=4;venues=2` | `symbol>=2 or venue>=2` | `true` |
| `wilson95_lcb` | `0.700855` | `>=0.95` | `false` |
| `broad_normal_sample` | `Derived only from public CFTC facts describing genuine iceberg order legs in the same examples; schema-ready/unscored seed, not a broad normal-activity calibration sample.` | `source-owned broad normal activity sample` | `false` |

## Interpretation

The Mohan complaint expansion improves date, symbol, and venue breadth, and the unchanged intake verifier parses the files. The slice remains calibration-blocked because support is below 50/50, Wilson95 min LCB is below 0.95, and same-event genuine-order rows are not broad independent normal controls.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211032-codex-r6-mohan-complaint-expansion-gate-v1/r6-mohan-complaint-expansion-gate/r6_mohan_complaint_expansion_gate_v1.json`
- Gate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211032-codex-r6-mohan-complaint-expansion-gate-v1/r6-mohan-complaint-expansion-gate/r6_mohan_complaint_expansion_gate_v1_gates.csv`
- Verifier output: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211032-codex-r6-mohan-complaint-expansion-gate-v1/checks/direct_manipulation_row_intake_verifier_v1.out`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211032-codex-r6-mohan-complaint-expansion-gate-v1/checks/r6_mohan_complaint_expansion_gate_v1_assertions.out`
