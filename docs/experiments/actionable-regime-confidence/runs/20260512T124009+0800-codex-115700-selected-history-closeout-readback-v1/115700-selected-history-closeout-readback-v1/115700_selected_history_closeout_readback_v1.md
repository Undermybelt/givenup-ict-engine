# 115700 Selected-History Closeout Readback v1

Run id: `20260512T124009+0800-codex-115700-selected-history-closeout-readback-v1`

## Scope

Support-only closeout over settled selected-history attempts after `121347`.
This does not edit the source state, does not approve source-control selection,
does not promote a candidate, and does not call `update_goal`.

## Evidence

- Native selected-history preflight: `docs/experiments/actionable-regime-confidence/runs/20260512T123211+0800-codex-115700-selected-history-preflight-v1/115700-selected-history-preflight-v1/115700_selected_history_preflight_v1.md`
- BTC alias AQ handoff and TOMAC run: `docs/experiments/actionable-regime-confidence/runs/20260512T123227+0800-codex-115700-selected-history-btc-alias-aq-v1/command-output/05_run_tomac_timerange_patched.out`
- Duplicate venv TOMAC readback: `docs/experiments/actionable-regime-confidence/runs/20260512T123704+0800-codex-123227-selected-history-tomac-run-v1/command-output/02_run_tomac_venv.out`
- BTC/USDT pairmap failed run: `docs/experiments/actionable-regime-confidence/runs/20260512T123508+0800-codex-115700-selected-history-btcusdt-pairmap-v1/command-output/run_tomac_btcusdt_pairmap.out`
- Prior 122600 terminal readback is already registered on the board.

## Readback

- `123211` checked `BTC_USD-1h.json`, `BTC_USD-4h.json`, and `BTC_USD-1d.json` in copied state. All `factor-research` and `workflow-status` commands exited `0`, but all three remained `ready=false`, `actionable=false`, `review=observe`, `execution_gate=execution_blocked`, and `execution_readiness=0.3`.
- `123227` repaired the selected 1h path into a BTC alias AQ workspace: factor-research initial `0`, auto-quant-prepare `0`, factor-research after prepare `0`, and data readiness became `dependency_ready_data_ready`.
- `123227` / `123704` reached FreqTrade measurement through TOMAC, but all three strategies produced `0` trades, `0.0000` Sharpe, `0.0000` total profit, `0.0000` win rate, and `0.0000` profit factor.
- `123508` tried a BTC/USDT pairmap root but failed closed: first run exited `1` because `fiat_display_currency=USDT` is invalid for the FreqTrade config schema; retry still exited `1` with `0/3` strategies successful.
- No selected-history attempt produced mature rooted branch observations, a measured profitability packet, BBN update authority, CatBoost/path-ranker positive training labels, or an execution-tree non-observe candidate.

## Gate

- `support_once:124009_115700_selected_history_closeout_readback_v1`.
- `supporting_only:selected_history_closeout_after_123211_123227_123704_123508`.
- `pass:123211_native_preflight_3_paths_exit0`.
- `pass:123227_aq_prepare_data_ready_true`.
- `pass:123227_123704_tomac_reached_measurement`.
- `fail_closed:123211_execution_ready_false_actionable_false_observe`.
- `fail_closed:123227_123704_tomac_trades_0_of_3`.
- `fail_closed:123508_btcusdt_pairmap_config_and_retry_failed`.
- `fail_closed:no_mature_rooted_observations`.
- `fail_closed:no_selected_history_source_control_unlock`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Stop duplicating selected-history TOMAC repair roots for this exact `115700`
slice unless a materially new data window or strategy family is introduced.
The current evidence says the recorded paths can be replayed and AQ can be
prepared, but the selected-history/TOMAC path does not produce usable trades
or execution readiness. The next useful transition is either a materially new
provider-provenanced data window with enough history and nonzero rooted branch
observations, or a separate strategy family that can produce mature observations
before Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
