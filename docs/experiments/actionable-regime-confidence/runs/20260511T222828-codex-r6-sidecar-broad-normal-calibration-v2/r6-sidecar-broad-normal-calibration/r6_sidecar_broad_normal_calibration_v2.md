# R6 Sidecar Broad Normal Calibration v2

Run ID: `20260511T222828+0800-codex-r6-sidecar-broad-normal-calibration-v2`

## Result

- Direct positives: `57`; Wilson95 LCB `0.936861165147`; pass `false`.
- Same-event control seeds remain `57` and are not broad-normal controls.
- Independent Nasdaq ITCH sidecar controls: `80`; Wilson95 LCB `0.954181870464`; pass `true`.
- Min Wilson95 across direct-positive and sidecar axes: `0.936861`.
- Additional all-correct owner-approved positive rows needed for pooled Wilson95 `>=0.95`: `16`.
- Gate result: `r6_sidecar_broad_normal_calibration_v2=independent_control_axis_pass_positive_confidence_still_blocked`.
- Shared intake mutated: `false`; accepted rows added: `0`; strict full objective achieved: `false`; `update_goal=false`.

## Boundary

This artifact wires the sidecar controls as an independent broad-normal control axis. It does not append negative-only sidecar rows into the shared matched-negative intake, and it does not relax the direct positive/support/species gates.
