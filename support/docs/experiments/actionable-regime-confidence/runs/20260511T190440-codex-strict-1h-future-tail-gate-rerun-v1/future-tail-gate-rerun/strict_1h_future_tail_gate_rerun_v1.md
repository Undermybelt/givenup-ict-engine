# Strict 1h Future Tail Gate Rerun v1

Run ID: `20260511T190440+0800-codex-strict-1h-future-tail-gate-rerun-v1`

This rerun applies the predeclared protocol from `strict_1h_future_tail_gate_spec_v1`. It accepts rows only under the future-tail chronological protocol. It does not retroactively repair the fixed `2024` calibration / `2025` heldout strict gate.

## Decision

`strict_1h_future_tail_gate_rerun_v1=accepted4_future_protocol_rows_fixed_gate_unchanged`

- Accepted future-protocol rows added: `4`.
- Accepted rows added to fixed gate: `0`.
- Strict `1h` fixed-gate rows before: `41/156`.
- Strict `1h` future-protocol rows after: `45/156`.
- New confidence gate: `true`, scope `future_tail_chronological_protocol_only`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Accepted Future-Protocol Rows

| Instrument | Root | 2024 Cal Support | 2024 Cal LCB | 2025 Heldout Support | 2025 Heldout LCB | Jan-2026 Tail | Future Support | Future LCB | Future Acceptance |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `ABBV` | `Sideways` | `75` | `0.9512761575` | `67` | `0.9457738606` | `19` | `86` | `0.9572418027` | `accepted_95` |
| `TMO` | `Bull` | `118` | `0.9684716610` | `67` | `0.9457738606` | `18` | `85` | `0.9567605162` | `accepted_95` |
| `HD` | `Bull` | `162` | `0.9768365592` | `69` | `0.9472627418` | `15` | `84` | `0.9562682716` | `accepted_95` |
| `AMD` | `Bull` | `76` | `0.9518864149` | `62` | `0.9416559279` | `12` | `74` | `0.9506502206` | `accepted_95` |

## Guardrails

- This is a future-tail chronological protocol gate, not a current fixed-gate repair.
- No thresholds were relaxed: support minimum remains `73`; Wilson95 LCB minimum remains `0.95`.
- The source tail is bounded to source-owned `2026-01-02` to `2026-01-30` rows and exact `1h` provider coverage.
- This still leaves the strict full objective blocked: native sub-hour overlap, full other-market/source-label equivalence, broader source recency, and direct `Manipulation` full species coverage remain open.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T190440-codex-strict-1h-future-tail-gate-rerun-v1/future-tail-gate-rerun/strict_1h_future_tail_gate_rerun_v1.json`
- Rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T190440-codex-strict-1h-future-tail-gate-rerun-v1/future-tail-gate-rerun/strict_1h_future_tail_gate_rerun_v1_rows.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T190440-codex-strict-1h-future-tail-gate-rerun-v1/checks/strict_1h_future_tail_gate_rerun_v1_assertions.out`

