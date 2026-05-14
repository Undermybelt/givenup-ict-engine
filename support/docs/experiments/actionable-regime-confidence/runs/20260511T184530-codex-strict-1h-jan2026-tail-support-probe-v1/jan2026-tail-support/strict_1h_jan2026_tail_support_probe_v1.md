# Strict 1h Jan-2026 Tail Support Probe v1

Run ID: `20260511T184530+0800-codex-strict-1h-jan2026-tail-support-probe-v1`

## Decision

- Current strict exact `1h` accepted rows remain `41/156`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Candidate rows checked: `13`.
- Provider-ready for Jan-2026 tail: `13/13`.
- Existing Jan-2026 source tail covers the missing-extra count for `4` candidates.
- Standalone Jan-2026 tail gates passing `support>=73` and Wilson95>=0.95: `0`.
- Gate result: `strict_1h_jan2026_tail_support_probe_v1=tail_support_found_future_gate_only_no_current_acceptance`.
- Full objective achieved: false. `update_goal=false`.

## Tail-Covered Candidates

| Instrument | Root | Missing extra | Jan-2026 tail sessions | Tail LCB |
|---|---|---:|---:|---:|
| ABBV | Sideways | 6 | 19 | 0.8318207759 |
| TMO | Bull | 6 | 18 | 0.8241207764 |
| HD | Bull | 4 | 15 | 0.7961166990 |
| AMD | Bull | 11 | 12 | 0.7575059933 |

## Guardrail

Jan-2026 source labels are source-owned tail evidence, but they are not a retroactive repair for the fixed 2024/2025 strict gate. They can only seed a predeclared future chronological gate.

## Next

For strict 1h, use the rows with tail_covers_missing_extra=true as the first future-gate targets if a predeclared 2026-tail validation protocol is opened; otherwise keep strict support at 41/156.
