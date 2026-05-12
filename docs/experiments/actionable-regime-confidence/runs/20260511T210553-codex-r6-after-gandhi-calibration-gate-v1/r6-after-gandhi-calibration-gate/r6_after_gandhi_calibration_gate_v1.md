# R6 After-Gandhi Calibration Gate v1

- Decision: `r6_after_gandhi_calibration_gate_v1=chronology_and_heldout_improved_support_wilson_broad_control_blocked`.
- Direct verifier status: `schema_ready_unscored`.
- Positive rows: `4`; matched negative rows: `4`.
- Unique dates: `3`; symbols: `3`; venues: `1`; matched groups: `3`.
- Wilson95 LCB positive/negative/min: `0.510109` / `0.510109` / `0.510109`.
- Chronological split ok: `true`; heldout symbol/venue ok: `true`.
- Support ok: `false`; broad normal sample: `false`.
- Accepted rows added: `0`; new confidence gate: `false`; R6 direct species closed: `false`.
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

The Gandhi uplift improves the R6 direct intake from one date/symbol group to two dates and two symbols, so the chronological and heldout-symbol gates now pass. The intake remains fail-closed because support is only four positives and four same-report control seeds, Wilson95 min LCB remains below `0.95`, and the matched controls are not a broad source-owned normal-market sample.

## Consumed Artifacts

- Gandhi uplift: `docs/experiments/actionable-regime-confidence/runs/20260511T210150-codex-cftc-gandhi-source-row-uplift-v1`
- Official CFTC expansion scout: `docs/experiments/actionable-regime-confidence/runs/20260511T210156-codex-r6-official-cftc-expansion-scout-v1`
- Additional CFTC public order screen: `docs/experiments/actionable-regime-confidence/runs/20260511T210228-codex-r6-additional-cftc-public-order-screen-v1`

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T210553-codex-r6-after-gandhi-calibration-gate-v1/r6-after-gandhi-calibration-gate/r6_after_gandhi_calibration_gate_v1.json`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210553-codex-r6-after-gandhi-calibration-gate-v1/r6-after-gandhi-calibration-gate/r6_after_gandhi_calibration_gate_v1_gates.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T210553-codex-r6-after-gandhi-calibration-gate-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T210553-codex-r6-after-gandhi-calibration-gate-v1/checks/r6_after_gandhi_calibration_gate_v1_assertions.out`
