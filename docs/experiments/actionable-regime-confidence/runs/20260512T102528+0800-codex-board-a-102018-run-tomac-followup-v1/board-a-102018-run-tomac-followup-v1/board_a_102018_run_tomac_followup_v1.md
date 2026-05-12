# Board A 102018 RunTOMAC Follow-up v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T102528+0800-codex-board-a-102018-run-tomac-followup-v1`

Source run root: `docs/experiments/actionable-regime-confidence/runs/20260512T102018+0800-codex-board-a-aq-provider-authority-readback-v1`

Mode: `board_a_tomac_followup_fail_closed_terminal_zero_trade`

## Scope

This packet records the existing follow-up that invoked `run_tomac.py` from the prepared Board A AQ workspace created by `102018`. It does not edit Current Cursor, does not approve R6 source/control policy, does not mutate canonical intake, does not promote a regime packet, does not promote Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree output, and does not call `update_goal`.

## Commands

- Recommended command outside managed directory: `uv run --with ta-lib .../run_tomac.py`; result: `ModuleNotFoundError: No module named 'freqtrade'`.
- Managed workspace retry: `uv --directory .../.deps/auto-quant run --with ta-lib python run_tomac.py`; exit `1`, because the workspace data starts in 2026 while the inherited config ended at `20251231`.
- Shadow timerange repair: `uv --directory .../.deps/auto-quant run --with ta-lib python <shadow>/run_tomac.py`; exit `0`. The shadow workspace symlinked the original `102018` provider-owned `user_data` and used a derived `config.tomac.json` with `timerange=20260401-20260512`, leaving the original `102018` root untouched.

## Readback

- `aq_provider_invoked=true_run_tomac_from_102018_prepared_aq_workspace`.
- Provider provenance is inherited from `102018`: yfinance `NQ=F` provider data prepared into `NQ_USD-1h.feather`, `NQ_USD-4h.feather`, and `NQ_USD-1d.feather`; the six-provider matrix remains `IBKR,TradingViewRemix/TVR,yfinance/YF,Kraken,Binance,Bybit` with TVR fail-closed and IBKR available through the low-pollution uv fetch sidecar.
- `local_cache_replay=false` for the primary Board A input; local files are only provider-provenance sidecars.
- The direct managed retry reached Freqtrade but failed with `OperationalException: No data found. Terminating.`
- Stderr shows `NQ/USD, spot, 1h, data starts at 2026-04-01 00:00:00`; this exposed the inherited timerange mismatch.
- The shadow timerange repair loaded the 2026 provider-owned NQ feathers, backtested `2026-04-11 10:00:00` to `2026-05-11 23:00:00`, and completed with `1` succeeded strategy and `0` failed strategies.
- Strategy `TomacNQ_KillzoneBreakout` produced `0` trades, Sharpe `0.0000`, total profit `0.0000%`, win rate `0.0000%`, and profit factor `0.0000`.
- Successful backtests `1`; failed backtests `0`; mature rooted branch observations `0`.

## Gate

- `pass:board_a_auto_quant_run_tomac_invoked_from_prepared_workspace`
- `fail_closed:recommended_command_missing_freqtrade_outside_managed_dir`
- `fail_closed:managed_dir_run_tomac_no_data_found`
- `pass:shadow_timerange_repair_backtest_exit_0`
- `fail_closed:shadow_timerange_repair_zero_trades`
- `fail_closed:no_mature_rooted_branch_observations`
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_promotion_rerun`
- `promotion_allowed=false`
- `update_goal=false`

## Next

Do not repeat the same one-month Yahoo NQ Board A TOMAC path. The next useful AQ/provider move needs longer provider-provenanced NQ history, a different provider-owned market family, or a branch-specific strategy/input set that can create nonzero mature observations after the R6 source/control gates are unlocked.
