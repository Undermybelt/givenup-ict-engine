# R6 Sidecar Broad Normal Calibration v1

- Decision: `r6_sidecar_broad_normal_calibration_v1=broad_normal_sidecar_available_positive_split_species_still_blocked`.
- Live R6 positives: `57`; same-event controls: `57`; sidecar broad-normal controls: `80`.
- Broad-normal sidecar gate: `true`; broad-normal Wilson95 LCB: `0.954180`.
- Positive Wilson95 LCB: `0.936859`; pooled sidecar min LCB: `0.936859`; pooled sidecar gate: `false`.
- Positive chronological split gate: `false`; direct species closed: `false`.
- Additional source-owned positive rows needed for pooled Wilson95 only: `16`; split/heldout gates require materially more.
- Shared intake mutated: `false`; strict full objective achieved: `false`; new confidence gate: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Positive Chronological Split Metrics

| Split | Pos | Wilson95 LCB | Support OK | Wilson OK |
|---|---:|---:|---:|---:|
| `chronological_train` | `29` | `0.883026` | `false` | `false` |
| `chronological_calibration` | `14` | `0.784683` | `false` | `false` |
| `chronological_test` | `14` | `0.784683` | `false` | `false` |

## Boundary

This is a read-only calibration over the live R6 positive rows and the V52 sidecar Nasdaq ITCH broad-normal controls. It does not append sidecar rows into the shared intake and does not convert OHLCV/provider surfaces into direct evidence.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T222600-codex-r6-sidecar-broad-normal-calibration-v1/r6-sidecar-broad-normal-calibration/r6_sidecar_broad_normal_calibration_v1.json`
- Split metrics CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T222600-codex-r6-sidecar-broad-normal-calibration-v1/r6-sidecar-broad-normal-calibration/r6_sidecar_broad_normal_positive_split_metrics_v1.csv`
- Reproduction script: `docs/experiments/actionable-regime-confidence/runs/20260511T222600-codex-r6-sidecar-broad-normal-calibration-v1/scripts/r6_sidecar_broad_normal_calibration_v1.py`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T222600-codex-r6-sidecar-broad-normal-calibration-v1/checks/r6_sidecar_broad_normal_calibration_v1_assertions.out`
