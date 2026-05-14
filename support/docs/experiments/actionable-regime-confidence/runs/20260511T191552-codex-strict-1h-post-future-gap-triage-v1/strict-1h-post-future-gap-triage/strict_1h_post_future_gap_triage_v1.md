# Strict 1h Post-Future Gap Triage v1

Run ID: `20260511T191552+0800-codex-strict-1h-post-future-gap-triage-v1`

This triage reads the strict `1h` near-miss candidates after `strict_1h_future_tail_gate_rerun_v1`. It adds no rows and does not edit Current Cursor.

## Decision

`strict_1h_post_future_gap_triage_v1=9_near_miss_targets_remaining_no_existing_tail_ready`

- Strict `1h` fixed-gate rows: `41/156`.
- Strict `1h` future-protocol rows: `45/156`.
- Near-miss candidates before future-tail rerun: `13`.
- Future-protocol accepted rows: `4`.
- Remaining near-miss targets after future-tail rerun: `9`.
- Remaining targets ready with existing Jan-2026 tail: `0`.
- Minimum new source-owned sessions needed for the next target: `5`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Remaining Near-Miss Targets

| Instrument | Root | Missing From 184151 | Existing Tail | New Sessions Needed | Repair Split |
|---|---|---:|---:|---:|---|
| `XOM` | `Sideways` | `5` | `0` | `5` | `heldout_2025` |
| `UNH` | `Bear` | `7` | `0` | `7` | `calibration_2024` |
| `^DJI` | `Sideways` | `7` | `0` | `7` | `calibration_2024` |
| `AMD` | `Bear` | `10` | `0` | `10` | `calibration_2024` |
| `HD` | `Sideways` | `11` | `1` | `10` | `calibration_2024` |
| `JNJ` | `Sideways` | `12` | `2` | `10` | `heldout_2025` |
| `DIS` | `Bull` | `18` | `6` | `12` | `heldout_2025` |
| `TMO` | `Bear` | `14` | `0` | `14` | `calibration_2024` |
| `INTC` | `Bear` | `20` | `0` | `20` | `heldout_2025` |

## Next

Do not rerun the already accepted four future-tail rows. The next strict `1h` acquisition target is `XOM/Sideways`, which needs `5` new source-owned heldout sessions beyond the current Jan-2026 tail. The next calibration-side targets are `UNH/Bear` and `^DJI/Sideways`, each needing `7` source-owned calibration sessions.

