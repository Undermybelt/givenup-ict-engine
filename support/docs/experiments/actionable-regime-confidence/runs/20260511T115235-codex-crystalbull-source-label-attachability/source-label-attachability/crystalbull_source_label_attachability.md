# CrystalBull Source-Label Attachability

Run ID: `20260511T115235+0800-codex-crystalbull-source-label-attachability`

## Decision

- Attached source-label slots added: `3`.
- Accepted calibrated root factors added: `0`.
- Accepted parent-root completion slots added: `0`.
- Full objective achieved: `false`.
- Gate result: `partial_crystalbull_qqq_daily_source_labels_attached_factor_gate_still_blocked`.

## Attached Slots

| Provider | Instrument | Timeframe | Root | Source Label | Rows |
|---|---|---|---|---|---:|
| `yfinance` | `QQQ` | `1d` | `Bull` | `Confirmed Uptrend` | `3046` |
| `yfinance` | `QQQ` | `1d` | `Bear` | `Market in Correction` | `1065` |
| `yfinance` | `QQQ` | `1d` | `Sideways` | `Uptrend Under Pressure` | `846` |

## Blockers

- CrystalBull/IBD does not expose a `Crisis` root label.
- The source is daily QQQ only; intraday, weekly, and monthly slots stay blocked without an approved timeframe crosswalk.
- The prior factor gate remains blocked: no Bull/Bear/Sideways rule survived held-out 95% Wilson LCB.
- This branch does not address direct `Manipulation` evidence.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T115235-codex-crystalbull-source-label-attachability/source-label-attachability/crystalbull_source_label_attachability.json`
- Slot CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T115235-codex-crystalbull-source-label-attachability/source-label-attachability/crystalbull_source_label_attachability_slots.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T115235-codex-crystalbull-source-label-attachability/checks/crystalbull_source_label_attachability_assertions.out`
