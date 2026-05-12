# R6 Current Live Intake Calibration Readback v1

- Decision: `r6_current_live_intake_calibration_readback_v1=schema_ready_but_calibration_blocked`.
- Verifier status: `schema_ready_unscored`; verifier positive rows `13`; verifier matched negatives `13`.
- CSV rows: positives `13`; matched negatives `13`; matched groups `12`.
- Breadth: dates `10`; symbols `6`; venues `3`; sessions `4`.
- Wilson95 LCB positive/negative/min: `0.771905` / `0.771905` / `0.771905`.
- Chronological split ok: `true`; heldout symbol/venue ok: `true`.
- Support ok: `false`; broad normal sample: `false`; species coverage ok: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Gates

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `positive_support` | `13` | `50` | `false` |
| `negative_support` | `13` | `50` | `false` |
| `chronological_split` | `10` | `2` | `true` |
| `heldout_symbol_or_venue` | `symbols=6;venues=3` | `symbol>=2 or venue>=2` | `true` |
| `wilson95_lcb` | `0.771905` | `>=0.95` | `false` |
| `broad_normal_sample` | `same-event CFTC genuine-order control seeds; not broad normal-market calibration` | `source-owned broad normal activity sample` | `false` |
| `direct_species_coverage` | `spoofing_layering` | `spoofing_layering;quote_spoofing;quote_stuffing;pinging;bear_raid;painting_tape` | `false` |

## Interpretation

The live R6 intake is schema-ready and stronger than the last cursored 4/4 artifact, but it still fails the unchanged Board A objective. Support remains below 50/50, Wilson95 min LCB remains below 0.95, controls are same-event CFTC genuine-order seeds rather than a broad normal sample, and direct Manipulation species coverage is still incomplete.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211050-codex-r6-current-live-intake-calibration-readback-v1/r6-current-live-intake-calibration-readback/r6_current_live_intake_calibration_readback_v1.json`
- Gate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211050-codex-r6-current-live-intake-calibration-readback-v1/r6-current-live-intake-calibration-readback/r6_current_live_intake_calibration_readback_v1_gates.csv`
- Verifier stdout: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211050-codex-r6-current-live-intake-calibration-readback-v1/r6-current-live-intake-calibration-readback/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211050-codex-r6-current-live-intake-calibration-readback-v1/checks/r6_current_live_intake_calibration_readback_v1_assertions.out`
