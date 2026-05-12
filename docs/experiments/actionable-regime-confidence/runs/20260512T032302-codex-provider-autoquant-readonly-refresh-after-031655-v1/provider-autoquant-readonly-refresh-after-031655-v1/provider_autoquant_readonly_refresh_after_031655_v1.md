# Provider/Auto-Quant Readonly Refresh After 031655 v1

Run id: `20260512T032302-codex-provider-autoquant-readonly-refresh-after-031655-v1`

Gate result: `provider_autoquant_readonly_refresh_after_031655_v1=readiness_refreshed_no_promotion_source_controls_blocked`.

## Result

- Provider summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- Auto-Quant status: `dependency_ready_data_ready`, healthy `true`, data_ready `true`, commit `34ba6b6ee6aa69813a50a72158d4c089d97afb96`.
- yfinance live/runtime and market-data lanes remain ready.
- Kraken CLI status in this restored shell readback: `ready` / `kraken_cli_config_detected`; Kraken public market-data remains blocked by Python provider dependencies.
- IBKR gateway is reachable but market-data/bridge lanes remain blocked by missing `redis`/`ib_async` runtime dependencies.
- TradingViewRemix/TradingView MCP remains blocked by connectivity probe failure.
- Approval remains non-approving; canonical merge and downstream promotion rerun remain false.
- This packet is read-only and does not run Auto-Quant strategies, filters, Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion.
- Restoration note: this run root was restored because the board `032417` status packet referenced `032302` as an input side packet.

## Next

Continue only from owner/operator R6 export delivery, explicit `FLIP` approval, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before canonical merge and downstream promotion.
