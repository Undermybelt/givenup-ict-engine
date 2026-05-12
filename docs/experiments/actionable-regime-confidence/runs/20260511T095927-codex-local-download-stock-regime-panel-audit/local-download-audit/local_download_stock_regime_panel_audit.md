# Local Download Stock Regime Panel Audit

Run ID: `20260511T095927+0800-codex-local-download-stock-regime-panel-audit`

Board: `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`

Candidate source path: `/Users/thrill3r/Downloads/stock-market-regimes-20002026`

## Source Readback

- Files seen: `dataset_summary.txt`, `regime_analysis_by_ticker.csv`, `regime_by_year.csv`, `stock_market_regimes_2000_2026.csv`, `stock_market_regimes_2000_2026.parquet`.
- Main table rows: `245021`.
- Tickers: `39`.
- Date range: `2000-01-03` to `2026-01-30`.
- Native timeframe: daily / `1d`.
- Labels: `Bull=103766`, `Sideways=56668`, `Bear=54939`, `Crisis=29632`, `High-volatility=16`.

## Attachability

The labels are aligned with active `MainRegimeV2` parent-root wording, but the panel does not fill the current missing-slot denominator.

- Current missing-slot request consumed: `docs/experiments/actionable-regime-confidence/runs/20260511T094002-codex-external-label-request-package-v3/acquisition-request/missing_parent_root_label_slots_request_v3.csv`.
- Missing slots inspected: `564`.
- Missing by root: `Bull=141`, `Bear=141`, `Sideways=141`, `Crisis=141`.
- Exact missing-instrument overlap: `^DJI`, `^GSPC`.
- Overlap missing slots: `56`.
- Overlap missing timeframes: `1m=8`, `5m=8`, `15m=8`, `30m=8`, `1h=8`, `4h=8`, `1mo=8`.
- Matching current missing `1d` / `1w` slots: `0`.

## Decision

- Accepted parent-root slots added: `0`.
- Accepted direct `Manipulation` rows/windows added: `0`.
- Gate result: `blocked_local_download_stock_regime_panel_daily_only_no_current_missing_slots`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

## Next Action

Continue source acquisition for exact-underlying intraday/monthly `MainRegimeV2` labels and direct `Manipulation` rows. Do not re-audit this local daily stock panel as a new source unless the missing-slot denominator changes.
