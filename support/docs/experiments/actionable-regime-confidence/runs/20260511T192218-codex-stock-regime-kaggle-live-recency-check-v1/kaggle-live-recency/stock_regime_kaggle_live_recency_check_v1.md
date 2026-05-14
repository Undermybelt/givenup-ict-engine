# Stock Regime Kaggle Live Recency Check v1

Run ID: `20260511T192218-codex-stock-regime-kaggle-live-recency-check-v1`

## Decision

- Gate result: `stock_regime_kaggle_live_recency_check_v1=upstream_current_file_no_xom_sideways_tail_repair`.
- Dataset: [`mafaqbhatti/stock-market-regimes-20002026`](https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026).
- Live CSV rows: `245021`; tickers: `39`.
- Live date range: `2000-01-03` to `2026-01-30`.
- `XOM/Sideways` rows after `2026-01-30`: `0`.
- `XOM/Sideways` rows in `2026-01-02..2026-01-30`: `0`.
- `XOM/Sideways` rows in calendar `2025`: `68`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Interpretation

- `191552` identified `XOM/Sideways` as the next strict `1h` heldout-side target needing `5` source-owned sessions.
- The current upstream Kaggle file cannot supply those sessions: it still ends on `2026-01-30`, and it has no `XOM/Sideways` rows in the Jan-2026 source tail.
- Raw Kaggle data stayed under `/tmp`; repo output is this compact recency check only.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T192218-codex-stock-regime-kaggle-live-recency-check-v1/kaggle-live-recency/stock_regime_kaggle_live_recency_check_v1.json`
- Counts CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T192218-codex-stock-regime-kaggle-live-recency-check-v1/kaggle-live-recency/stock_regime_kaggle_live_recency_check_v1_counts.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T192218-codex-stock-regime-kaggle-live-recency-check-v1/checks/stock_regime_kaggle_live_recency_check_v1_assertions.out`
