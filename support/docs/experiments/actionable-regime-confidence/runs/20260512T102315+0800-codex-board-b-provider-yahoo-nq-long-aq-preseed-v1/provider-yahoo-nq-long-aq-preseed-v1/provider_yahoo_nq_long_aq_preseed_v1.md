# Provider Yahoo NQ Long AQ Preseed v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T102315+0800-codex-board-b-provider-yahoo-nq-long-aq-preseed-v1`

Purpose: test a longer provider-provenanced Yahoo `NQ=F` 1h history before any repeated Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree promotion attempt.

## Commands

- `00_fetch_yahoo_nq_f_1h_2y`: `uv run --with pandas --with requests python scripts/auto_quant_external/fetch_external.py yahoo --symbol 'NQ=F' --interval 1h --start 2024-05-13 --end 2026-05-12 --output .../provider-csv/yahoo_nq_f_1h_2y.csv`
- `01_prepare_provider_csv_long_abs`: `uv --directory /Users/thrill3r/Auto-Quant run python scripts/auto_quant_external/prepare_external.py --csv .../provider-csv/yahoo_nq_f_1h_2y.csv --pair NQ/USD --timeframes 1h,4h,1d --datadir .../workspace/auto-quant-yahoo-nq-long/user_data/data --column-map date:date,open:open,high:high,low:low,close:close,volume:volume --no-clean`
- `02_run_tomac_provider_yahoo_nq_long_abs`: `uv --directory /Users/thrill3r/Auto-Quant run python .../workspace/auto-quant-yahoo-nq-long/run_tomac.py`

## Provider And Prepare Readback

- Fetch exit: `0`.
- Provider CSV: `provider-csv/yahoo_nq_f_1h_2y.csv`.
- Yahoo `NQ=F` 1h rows: `11,381`.
- Provider range: `2024-05-13 00:00:00+00:00 -> 2026-05-11 23:00:00+00:00`.
- Prepare exit: `0`.
- Prepare audit: `raw_rows=11,381`, `bad_date=0`, `duplicate_ts=0`, `nan_ohlc=0`, `after_load=11,381`.
- Gap audit: `median_gap=3600s`, `max_gap=4,800.0min`, `big_gaps_gt_60x_median=4`.
- Prepared feathers:
  - `NQ_USD-1h.feather`: `11,381` bars.
  - `NQ_USD-4h.feather`: `3,085` bars.
  - `NQ_USD-1d.feather`: `612` bars.

## Auto-Quant / TOMAC Readback

- TOMAC exit: `0`.
- Strategy: `TomacNQ_KillzoneBreakout`.
- Pair: `NQ/USD`.
- Backtest window: `2024-05-23 10:00:00 -> 2026-05-11 23:00:00`.
- Trade count: `0`.
- Total profit: `0.0000%`.
- Sharpe: `0.0000`.
- Sortino: `0.0000`.
- Calmar: `0.0000`.
- Win rate: `0.0000%`.
- Profit factor: `0.0000`.
- Auto-Quant reported: `Done: 1 succeeded, 0 failed`.

## Gate Decision

- `provider_yahoo_nq_long_aq_preseed_v1=prepared_and_backtested_zero_trades_no_promotion`.
- `pass:provider_fetch_exit0`.
- `pass:provider_prepare_exit0`.
- `pass:auto_quant_tomac_exit0`.
- `fail_closed:zero_trades_no_mature_rooted_branch_observations`.
- `fail_closed:no_profitability_signal`.
- `fail_closed:no_selected_data_autoquant_training`.
- `fail_closed:source_control_evidence_acquired_false`.
- `fail_closed:downstream_promotion_rerun_false`.
- `promotion_allowed=false`.
- `update_goal=false`.

## Next

Do not rerun this same Yahoo NQ long-history TOMAC preseed shape. It adds technical provider/prepare/runtime evidence but no mature rooted branch observations. The next useful path is a materially different provider-owned strategy that produces nonzero executed trades, a fix for the Freqtrade entry-to-trade translation gap observed in later provider-owned NQ strategy work, a different provider-provenanced market family, or explicit selected-history/source-control unlock before any selected-data promotion chain.
