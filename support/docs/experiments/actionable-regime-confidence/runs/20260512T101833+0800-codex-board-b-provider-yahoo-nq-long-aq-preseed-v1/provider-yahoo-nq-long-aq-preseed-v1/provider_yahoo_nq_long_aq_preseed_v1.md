# Provider Yahoo NQ Long Auto-Quant Preseed v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T101833+0800-codex-board-b-provider-yahoo-nq-long-aq-preseed-v1`

## Scope

This packet registers the completed `101833` provider-owned Yahoo NQ long-window Auto-Quant preseed readback. It is Board A / Board B nursery evidence only. It does not accept a regime packet, approve source/control evidence, select history, mutate canonical intake, promote Auto-Quant, promote BBN/CatBoost/path-ranking/execution-tree output, make a trade claim, or authorize `update_goal`.

## Inputs

- Source CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1/provider-csv/yahoo_nq_f_1h_20240601_20260512.csv`
- Pair: `NQ/USD`
- Config timerange: `20240601-20260512`
- Strategy: `TomacNQ_KillzoneBreakout`
- Auto-Quant runner: `uv --directory /Users/thrill3r/Auto-Quant run python`

## Command Results

| Step | Exit | Evidence |
| --- | ---: | --- |
| prepare Yahoo NQ CSV to Auto-Quant feathers | 0 | `command-output/00_prepare_provider_csv_long.out` |
| run TOMAC strategy on prepared data | 0 | `command-output/01_run_tomac_provider_yahoo_nq_long.out` |

The prepare step loaded `11,086` raw rows from `2024-06-02 22:00:00+00:00` to `2026-05-11 23:00:00+00:00`, skipped cleaning by request, and wrote:

- `NQ_USD-1h.feather`: `11,086` bars
- `NQ_USD-4h.feather`: `3,006` bars
- `NQ_USD-1d.feather`: `596` bars

The backtest ran from `2024-06-13 08:00:00` to `2026-05-11 23:00:00` after startup-candle adjustment and completed with `1` succeeded strategy and `0` failed strategies.

## Decision

The longer provider-owned Yahoo NQ input repaired the short-window limitation from prior one-month preseed attempts, but it still produced no usable strategy observations:

- Trades: `0`
- Sharpe: `0.0000`
- Total profit: `0.0000%`
- Win rate: `0.0000%`
- Profit factor: `0.0000`
- Mature rooted branch observations added: `0`
- Accepted regime packets added: `0`

Gate result: `provider_yahoo_nq_long_aq_preseed_v1=prepared_and_backtested_zero_trades_no_promotion`.

## Next

Do not repeat this same Yahoo NQ long-window TOMAC preseed. The next changed surface should be one of:

- a different provider-owned strategy expected to produce nonzero mature rooted observations,
- explicit selected-history approval for exactly one branch lane,
- real R6/R5/R3 source/control unlock,
- a coordinated structural-feedback owner fix after the shared dirty worktree is checked.
