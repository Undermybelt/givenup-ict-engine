# 041143 Sanitized Pair Tomac Readback v1

Append-only readback for the completed `06_sanitized_pair_prepare_and_run`
command under the `041143` agent-selected MTF sidecar.

This artifact does not edit the Current Cursor, does not satisfy
`user_selected_historical_data`, and does not promote the `032157` recipe.

## Scope

- Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T041143+0800-codex-board-b-032157-agent-selected-mtf-factor-research-v1`
- Command: `command-output/06_sanitized_pair_prepare_and_run.cmd`
- Output: `command-output/06_sanitized_pair_prepare_and_run.out`
- Error log: `command-output/06_sanitized_pair_prepare_and_run.err`
- Exit file: `command-output/06_sanitized_pair_prepare_and_run.exit`
- Pair: `B2RNQCOSTCRISISREPAIR032157/USD`
- Strategy: `TomacNQ_KillzoneBreakout`

## Readback

- `06_sanitized_pair_prepare_and_run.exit=0`.
- `prepare_external.py` loaded `260` rows from `profile_source.csv` with
  `bad_date=0`, `duplicate_ts=0`, and `nan_ohlc=0`.
- The source range was `2025-10-31 16:00:00+00:00` to
  `2025-12-31 20:00:00+00:00`.
- The run-local Auto-Quant workspace wrote `260` `1h` bars, `260` `4h`
  bars, and `53` `1d` bars for `B2RNQCOSTCRISISREPAIR032157/USD`.
- Freqtrade loaded the `1h` data from `2025-10-31 16:00:00` to
  `2025-12-31 00:00:00`, moved the backtest start by `250` startup candles,
  and backtested from `2025-11-11 02:00:00` to `2025-12-31 00:00:00`.
- `TomacNQ_KillzoneBreakout` produced `0` trades, `0.0000` total profit,
  `0.0000` Sharpe, `0.0000` win rate, and `0.0000` profit factor.

## Prompt-to-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Train/evaluate profitability factors from a regime-rooted context | The sidecar target is `B2R_NQ_COST_CRISIS_REPAIR_032157`; this command only replayed the agent-selected MTF profile through Tomac and produced no mature observations. | incomplete |
| Preserve branch path through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree | No downstream rerun was valid because the Auto-Quant replay produced `0` trades and no mature rooted branch observations. | not_started |
| Use real local Auto-Quant artifacts instead of speculation | `06_sanitized_pair_prepare_and_run.exit=0` and output files show real local feather preparation plus a Freqtrade backtest. | pass_diagnostic |
| Do not disturb concurrent Board B work | This artifact is append-only and does not edit the Current Cursor. | pass |
| Use explicit user-selected historical data | The run remains agent-selected MTF only; it does not satisfy `user_selected_historical_data`. | blocked |
| Use provider breadth claims carefully | This command did not add new IBKR, TradingViewRemix, yfinance, or Kraken provider evidence. | no_new_claim |

## Gate

- `fail_closed:agent_selected_mtf_tomac_zero_trades_no_mature_observations`
- `blocked:user_selected_historical_data_missing`
- `not_started:no_pre_bayes_bbn_catboost_execution_tree_promotion_rerun`
- `promotion_allowed=false`

## Decision

Do not promote from this sanitized-pair Tomac replay. It repairs the
agent-selected MTF pair/data shape enough to run Auto-Quant/Freqtrade, but it
does not produce trades, a branch-conditioned return series, mature rooted
observations, or downstream admission evidence.

The next qualifying path remains explicit user selection of exactly one of
`HTF`, `MTF`, or `LTF`, followed by a selected-data factor-research/Auto-Quant
run that emits nonzero mature rooted branch observations before
Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree can advance.
