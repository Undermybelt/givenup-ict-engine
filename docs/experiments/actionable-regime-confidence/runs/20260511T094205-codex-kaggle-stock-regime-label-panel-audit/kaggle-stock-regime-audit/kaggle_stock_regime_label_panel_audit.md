# Kaggle Stock Regime Label Panel Audit

Run ID: `20260511T094205+0800-codex-kaggle-stock-regime-label-panel-audit`

Source: `https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026`

## Result

- The dataset is directly downloadable through the Kaggle API endpoint and was inspected only under `/tmp`.
- Files observed: `dataset_summary.txt`, `regime_analysis_by_ticker.csv`, `regime_by_year.csv`, `stock_market_regimes_2000_2026.csv`, and `stock_market_regimes_2000_2026.parquet`.
- Rows: `245021`.
- Tickers: `39`.
- Date range: `2000-01-03` to `2026-01-30`.
- Labels: `Bull=103766`, `Sideways=56668`, `Bear=54939`, `Crisis=29632`, `High-volatility=16`.
- Exact missing-instrument overlap with the current Board A acquisition CSV: `^DJI` and `^GSPC`.
- Overlapping missing slots: `56`, but all are `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, or `1mo`.
- Dataset timeframe is daily (`1d`), and matching missing `1d`/`1w` slots for `^DJI`/`^GSPC` are `0`.
- Accepted parent-root slots added: `0`.
- Accepted direct `Manipulation` rows/windows added: `0`.

## Gate

`blocked_kaggle_stock_regime_panel_daily_only_not_current_missing_slots`

This is a real downloadable MainRegimeV2-shaped label panel, but it does not fill the current missing slot contract because the exact-overlap gaps are intraday/monthly, while the dataset is daily. It also does not contain direct `Manipulation` rows.

Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.
