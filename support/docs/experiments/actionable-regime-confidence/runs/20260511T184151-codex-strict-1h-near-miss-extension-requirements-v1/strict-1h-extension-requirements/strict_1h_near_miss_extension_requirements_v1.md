# Strict 1h Near-Miss Extension Requirements v1

Run ID: `20260511T184151+0800-codex-strict-1h-near-miss-extension-requirements-v1`

## Decision

- Current strict exact `1h` accepted rows remain `41/156`.
- Current accepted rows added: `0`; new confidence gate: `false`.
- No blocked row is promoted under the fixed 2024/2025 gate.
- Blocked rows with one split already passing: `26`.
- Post-2025 extension candidates with <=20 missing source sessions: `13`.
- Gate result: `strict_1h_near_miss_extension_requirements_v1=ready_source_extension_targets_no_current_acceptance`.
- Full objective achieved: false. `update_goal=false`.

## Top Extension Candidates

| Instrument | Root | 2024 extra | 2025 extra | Total extra | Current blocker |
|---|---|---:|---:|---:|---|
| HD | Bull | 0 | 4 | 4 | `heldout_time_support_below_73|heldout_time_wilson95_below_0_95` |
| XOM | Sideways | 0 | 5 | 5 | `heldout_time_support_below_73|heldout_time_wilson95_below_0_95` |
| TMO | Bull | 0 | 6 | 6 | `heldout_time_support_below_73|heldout_time_wilson95_below_0_95` |
| ABBV | Sideways | 0 | 6 | 6 | `heldout_time_support_below_73|heldout_time_wilson95_below_0_95` |
| UNH | Bear | 7 | 0 | 7 | `calibration_support_below_73|calibration_wilson95_below_0_95` |
| ^DJI | Sideways | 7 | 0 | 7 | `calibration_support_below_73|calibration_wilson95_below_0_95` |
| AMD | Bear | 10 | 0 | 10 | `calibration_support_below_73|calibration_wilson95_below_0_95` |
| HD | Sideways | 11 | 0 | 11 | `calibration_support_below_73|calibration_wilson95_below_0_95` |
| AMD | Bull | 0 | 11 | 11 | `heldout_time_support_below_73|heldout_time_wilson95_below_0_95` |
| JNJ | Sideways | 0 | 12 | 12 | `heldout_time_support_below_73|heldout_time_wilson95_below_0_95` |
| TMO | Bear | 14 | 0 | 14 | `calibration_support_below_73|calibration_wilson95_below_0_95` |
| DIS | Bull | 0 | 18 | 18 | `heldout_time_support_below_73|heldout_time_wilson95_below_0_95` |
| INTC | Bear | 0 | 20 | 20 | `heldout_time_support_below_73|heldout_time_wilson95_below_0_95` |

## Guardrail

No blocked row is accepted under the current fixed 2024/2025 gate. Post-2025 source rows may only justify a future chronological gate, not retroactive acceptance.

## Next

If source-owned post-2025 labels are acquired, start with the candidate CSV rows where one fixed split already passes and <=20 additional source sessions would make both fixed splits pass; otherwise keep strict 1h support at 41/156.
