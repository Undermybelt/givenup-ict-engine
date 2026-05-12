# Board B Provider Yahoo NQ AQ Preseed v1

Run id: `20260512T101256+0800-codex-board-b-provider-yahoo-nq-aq-preseed-v1`

Mode: `incubation_only`

## Scope

Provider-owned Auto-Quant preseed attempt from `20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1/provider-csv/yahoo_nq_f_1h.csv`.

This packet does not edit Current Cursor, does not approve selected history or source/control evidence, does not run selected-data promotion, does not advance Pre-Bayes/BBN/CatBoost/execution-tree promotion, does not promote a candidate, and does not call `update_goal`.

## Command Evidence

- `00_prepare_provider_csv`: exited `2`; failed because the relative provider CSV path was resolved under `/Users/thrill3r/Auto-Quant`.
- `01_run_tomac_provider_yahoo_nq`: exited `2`; failed because the relative workspace run script path was resolved under `/Users/thrill3r/Auto-Quant`.
- `02_prepare_provider_csv_abs`: exited `0`; absolute-path retry succeeded.
- `03_run_tomac_provider_yahoo_nq_abs`: exited `0`; absolute-path TOMAC run completed.

Raw command outputs:
- `docs/experiments/actionable-regime-confidence/runs/20260512T101256+0800-codex-board-b-provider-yahoo-nq-aq-preseed-v1/command-output/`

## Data Preseed Readback

Input:
- `docs/experiments/actionable-regime-confidence/runs/20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1/provider-csv/yahoo_nq_f_1h.csv`

Absolute-path prepare result:
- `raw_rows=642`
- `bad_date=0`
- `duplicate_ts=0`
- `nan_ohlc=0`
- date range `2026-04-01 00:00:00+00:00 -> 2026-05-11 23:00:00+00:00`
- wrote `NQ_USD-1h.feather` with `642` bars
- wrote `NQ_USD-4h.feather` with `173` bars
- wrote `NQ_USD-1d.feather` with `34` bars

Workspace:
- `docs/experiments/actionable-regime-confidence/runs/20260512T101256+0800-codex-board-b-provider-yahoo-nq-aq-preseed-v1/workspace/auto-quant-yahoo-nq`

## Auto-Quant Readback

The TOMAC run loaded `NQ/USD` provider-preseeded data and completed:

- Backtest window after startup candles: `2026-04-11 10:00:00 -> 2026-05-11 23:00:00`
- Strategy: `TomacNQ_KillzoneBreakout`
- Succeeded strategies: `1`
- Failed strategies: `0`
- Trade count: `0`
- Sharpe: `0.0000`
- Total profit: `0.0000%`
- Win rate: `0.0000%`
- Profit factor: `0.0000`

Freqtrade filled session/weekend gaps:
- `1h` rows before/after fill: `642 -> 984`
- `4h` rows before/after fill: `173 -> 246`

## Decision

Gate: `provider_yahoo_nq_aq_preseed_v1=prepared_and_backtested_zero_trades`.

This retires the immediate "pre-seed provider CSV into Auto-Quant" next action for the current Yahoo `NQ=F` one-month provider window and current TOMAC strategy shape. It produced a real Auto-Quant run, but no mature rooted branch observations and no profitability evidence.

Promotion allowed: `false`

`update_goal=false`

## Next

Do not rerun the same Yahoo one-month TOMAC preseed shape. The next useful provider-owned direction is either a longer provider-provenanced NQ history, a different branch-specific factor/strategy that can generate nonzero trades, or a direct recorded-history replay that already has mature observations. Keep selected-data promotion blocked until explicit selected-history and source/control unlock gates are both satisfied.
