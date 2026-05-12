# R6 Candidate Bundle Split Calibration Sweep After 035442 v1

Gate result: `r6_candidate_bundle_split_calibration_sweep_after_035442_v1=pooled_candidates_pass_but_split_broad_controls_policy_blocked_no_promotion`

## Result

- Candidate bundles calibrated: `4`.
- Strongest pooled candidate: `jpm_cbot_staging` with Wilson95 LCB `0.952479911333`.
- Any pooled gate: `true`.
- All chronological/symbol/venue gates: `false`.
- Broad independent normal controls: `false`; accepted rows added: `0`; `update_goal=false`.

## Summary

| Candidate | Pooled LCB | Pooled | Chronological | Heldout Symbol | Heldout Venue | Failing Cells |
|---|---:|---|---|---|---|---:|
| `jpm_cbot_staging` | `0.952479911333` | `true` | `false` | `false` | `false` | `54` |
| `direct_manipulation_intake` | `0.950006246616` | `true` | `false` | `false` | `false` | `50` |
| `v55_reconstruction_intake` | `0.950006246616` | `true` | `false` | `false` | `false` | `50` |
| `v56_clean_readback_intake` | `0.950006246616` | `true` | `false` | `false` | `false` | `50` |

## Boundary

This is a read-only calibration sweep. It does not copy candidate bundles into the required owner-export root and does not run downstream promotion.
