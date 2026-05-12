# Strict 1h Future Tail Gate Spec v1

Run ID: `20260511T185905+0800-codex-strict-1h-future-tail-gate-spec-v1`

This artifact predeclares a future chronological gate for strict exact `1h` near-miss rows whose missing source sessions are covered by the existing Jan-2026 source-owned tail. It is not a gate rerun and it accepts no current rows.

## Protocol

- Calibration split: `calendar_2024_fixed_from_exact_1h_universe`.
- Future validation split: `calendar_2025_heldout_plus_source_owned_jan2026_tail`.
- Tail window: `2026-01-02` to `2026-01-30`.
- Minimum support: `73`; minimum Wilson95 LCB: `0.95`.
- Required provenance: source-owned labels, exact `1h` provider coverage, no generated/proxy labels, no threshold relaxation.

## Decision

`strict_1h_future_tail_gate_spec_v1=predeclared_4_candidates_no_current_acceptance`

- Future-rerun candidates: `4`.
- Eligible under this predeclared protocol if rerun later: `4`.
- Accepted rows added now: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Current Cursor edited: `false`.

## Candidate Rows

| Instrument | Root | 2024 Cal Support | 2025 Heldout Support | Jan-2026 Tail | Future Heldout Support | Future Heldout LCB | Eligible Later | Accepted Now |
|---|---|---:|---:|---:|---:|---:|---|---|
| `ABBV` | `Sideways` | `75` | `67` | `19` | `86` | `0.9572418027` | `true` | `false` |
| `TMO` | `Bull` | `118` | `67` | `18` | `85` | `0.9567605162` | `true` | `false` |
| `HD` | `Bull` | `162` | `69` | `15` | `84` | `0.9562682716` | `true` | `false` |
| `AMD` | `Bull` | `76` | `62` | `12` | `74` | `0.9506502206` | `true` | `false` |

## Guardrail

This spec can only seed a later rerun under the named future chronological protocol. It does not change the fixed 2024/2025 strict gate and accepts no current rows.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T185905-codex-strict-1h-future-tail-gate-spec-v1/future-tail-gate-spec/strict_1h_future_tail_gate_spec_v1.json`
- Rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T185905-codex-strict-1h-future-tail-gate-spec-v1/future-tail-gate-spec/strict_1h_future_tail_gate_spec_v1_rows.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T185905-codex-strict-1h-future-tail-gate-spec-v1/checks/strict_1h_future_tail_gate_spec_v1_assertions.out`
