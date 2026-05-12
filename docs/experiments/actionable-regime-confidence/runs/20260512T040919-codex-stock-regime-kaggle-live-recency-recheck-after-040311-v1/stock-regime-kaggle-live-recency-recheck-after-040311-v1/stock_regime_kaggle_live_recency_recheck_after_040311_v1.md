# Stock Regime Kaggle Live Recency Recheck After 040311 v1

Run ID: `20260512T040919-codex-stock-regime-kaggle-live-recency-recheck-after-040311-v1`

## Decision

- Gate result: `stock_regime_kaggle_live_recency_recheck_after_040311_v1=upstream_unchanged_no_r5_recency_tail_repair_no_promotion`.
- Dataset: `mafaqbhatti/stock-market-regimes-20002026`.
- Live CSV rows: `245021`; tickers: `39`.
- Live date range: `2000-01-03` to `2026-01-30`.
- Target cells checked: `XOM/Sideways`, `UNH/Bear`, `^DJI/Sideways`, and `AMD/Bear`.
- Any target rows after `2026-01-30`: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- R5 recency-tail repair closed: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Raw Kaggle CSV stayed under `/tmp`; repo output contains only this compact evidence packet.

## Target Counts

| Ticker | Regime | Rows after 2026-01-30 | Rows 2026-01-01..2026-01-30 | Rows calendar 2025 | Rows all dates |
|---|---|---:|---:|---:|---:|
| `XOM` | `Sideways` | 0 | 0 | 68 | 2067 |
| `UNH` | `Bear` | 0 | 0 | 151 | 1225 |
| `^DJI` | `Sideways` | 0 | 0 | 87 | 2198 |
| `AMD` | `Bear` | 0 | 0 | 76 | 1667 |

## Interpretation

- The live Kaggle source remains usable for historical readback but does not provide the post-`2026-01-30` source-owned target rows required by the strict R5 recency-tail blocker.
- This does not create R3 native sub-hour labels, R6 owner/export controls, canonical merge input, downstream promotion evidence, or trade evidence.
