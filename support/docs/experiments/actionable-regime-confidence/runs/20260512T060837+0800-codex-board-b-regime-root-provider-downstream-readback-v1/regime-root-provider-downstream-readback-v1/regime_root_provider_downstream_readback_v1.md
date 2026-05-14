# Board B Regime-Root Provider Downstream Readback v1

Run id: `20260512T060837+0800-codex-board-b-regime-root-provider-downstream-readback-v1`

Gate result: `regime_root_provider_downstream_readback_v1=real_provider_and_downstream_readback_exit0_user_selected_data_still_missing_no_promotion`

## Scope

Fresh read-only Board B snapshot after the user reiterated that profitability factor training and every downstream consumer must preserve regime-root branch identity. This run does not select historical data, does not run a new selected-data Auto-Quant training loop, does not mutate source/control roots, does not edit the Current Cursor, does not promote any candidate, and does not call `update_goal`.

## Command Readback

- All command slots `00` through `17` exited `0`.
- Provider status summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- yfinance: provider status ready; `QQQ` 1h fetch wrote `197` rows from `2026-04-01 13:30:00+00:00` to `2026-05-11 20:00:00+00:00`.
- TradingViewRemix / TradingView MCP: catalog status remains unhealthy for the remote probe, but the local stdio harness fetch exited `0` and returned daily `NASDAQ:QQQ` OHLCV rows.
- Kraken: `kraken_cli` is ready; `kraken_public` catalog status reports missing system Python modules, but the direct public fetch exited `0` and wrote `721` `XBTUSD` 1h rows from `2026-04-11 22:00:00+00:00` to `2026-05-11 22:00:00+00:00`.
- IBKR: catalog status remains unhealthy because the default runtime misses `redis` / `ib_async`, but a low-pollution `uv --offline --with redis --with ib_async` fetch through the reachable port `4002` exited `0` and wrote `158` `AAPL` 1h rows from `2026-04-28T08:00:00+00:00` to `2026-05-11T21:00:00+00:00`.
- AutoQuant status for the combined state remains `dependency_ready_data_missing`: dependency healthy, `data_ready=false`, and `auto_quant_prepare_required`.
- Pre-Bayes/filter status remains `observe_only`.
- Read-only BBN branch set is accepted and preserves `5` rooted branch paths for `Bull`, `Bear`, `Sideways`, `Crisis`, and `Manipulation(scoped)`.
- CatBoost/path-ranker target export has `rows=5`, `history_rows=10`, `mature_rows=0`, `history_mature_rows=0`, `calibrated_rows=0`, `execution_gate_rows=0`, and `training_weight_rows=0`.
- Structural bundle preserves the selected exact branch path `Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72`, but the next step remains `ask_user_choose_historical_data` with `user_selected_historical_data_missing`.
- Execution candidate remains `ready=false`, `actionable=false`, `candidate_status=execution_blocked`, `pre_bayes_gate_status=observe_only`, and `execution_gate_status=execution_blocked`.

## Decision

The user-specified branch contract is still mechanically visible through the downstream readback:

`main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`

However, this is not a promotion packet. Provider fetches prove current provider reachability; they do not satisfy the explicit selected historical-data gate. AutoQuant is dependency-ready but still data-missing in the combined state. Pre-Bayes remains observe-only, the BBN branch set is read-only, CatBoost/path-ranker has zero mature/calibrated rows, and execution-tree output is blocked.

Promotion remains blocked: selected historical data `false`, nonzero mature rooted branch observations `false`, downstream promotion rerun `false`, execution-tree admissibility `false`, trade usable `false`, and `update_goal=false`.

## Next

Preserve the Board B Current Cursor. The next qualifying Board B action still requires explicit user selection of exactly one authoritative candidate:

- `htf`: `1d`
- `mtf`: `1h`
- `ltf`: `15m`

After that selection, run selected-data factor-research / Auto-Quant in an isolated state, keep only nonzero mature rooted branch observations, and then rerun filter / Pre-Bayes -> BBN -> CatBoost / path-ranking -> execution tree while preserving the exact `regime_profit_branch_path`.
