# R6 Current Intake Stability Calibration v1

- Decision: `r6_current_intake_stability_calibration_v1=stable_snapshot_support_wilson_broad_control_blocked`.
- Stable snapshot: `true`; stable hashes: `true`; verifier count match: `true`.
- Direct verifier status: `schema_ready_unscored`.
- Positive rows: `9`; matched negative rows: `9`.
- Unique dates: `6`; symbols: `4`; venues: `2`; matched groups: `8`.
- Wilson95 LCB positive/negative/min: `0.700855` / `0.700855` / `0.700855`.
- Chronological split ok: `true`; heldout symbol/venue ok: `true`.
- Support ok: `false`; broad normal sample: `false`.
- Accepted rows added: `0`; new confidence gate: `false`; R6 direct species closed: `false`.
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
| `broad_normal_sample` | `Derived only from public CFTC facts describing genuine iceberg order legs in the same examples; schema-ready/unscored seed, not a broad normal-activity calibration sample. Genuine-order legs are source-described same-event control seeds only; they are not independent broad normal-market calibration rows.` | `source-owned broad normal activity sample` | `false` |
| `stable_snapshot` | `True` | `True` | `true` |

## Interpretation

This readback reconciles the live direct intake after concurrent row materialization. Even when the snapshot is stable, the R6 lane remains fail-closed because support is below `50/50`, Wilson95 min LCB is below `0.95`, and controls are same-event CFTC genuine-order seeds rather than a broad source-owned normal-market calibration sample.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T211130-codex-r6-current-intake-stability-calibration-v1/r6-current-intake-stability-calibration/r6_current_intake_stability_calibration_v1.json`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T211130-codex-r6-current-intake-stability-calibration-v1/r6-current-intake-stability-calibration/r6_current_intake_stability_calibration_v1_gates.csv`
- Direct verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T211130-codex-r6-current-intake-stability-calibration-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T211130-codex-r6-current-intake-stability-calibration-v1/checks/r6_current_intake_stability_calibration_v1_assertions.out`
