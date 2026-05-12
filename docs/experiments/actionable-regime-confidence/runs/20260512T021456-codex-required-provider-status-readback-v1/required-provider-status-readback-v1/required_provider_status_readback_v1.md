# Required provider status readback v1

Run id: `20260512T021456-codex-required-provider-status-readback-v1`

Observed at: `2026-05-12T02:14:56+0800`

Board hash before artifact: `a76ee17f2375d3df5177349e2a1664b9b65e8b1a5eca564804ae1a2e2f0f7d9f`

Source runtime artifact: `docs/experiments/actionable-regime-confidence/runs/20260512T020037-codex-readonly-runtime-chain-refresh-after-015533-v1`

## Purpose

Map the user-named providers, `IBKR`, `TradingViewRemix`, `yfinance`, and `Kraken`, to the freshest read-only runtime evidence. This is provider-readiness evidence only. It does not accept labels, supply source/control rows, allow canonical merge, or rerun downstream promotion.

## Result

Gate result: `required_provider_status_readback_v1=provider_requirements_mapped_non_promoting`.

Provider readback:
- `yfinance`: ready. Evidence: `live_runtime:1/1 ready | market_data:1/1 ready`.
- `TradingViewRemix`: not ready. Evidence: `tradingview_mcp@market_data` is unhealthy with `tradingview_mcp_connectivity_probe_failed`.
- `IBKR`: not ready as market-data provider. Evidence: `ibkr` and `ibkr_bridge` report runtime dependency gaps while a local IBKR API is reachable on port `4002`.
- `Kraken`: partially ready. Evidence: `kraken_cli` is ready, but `kraken_public@market_data` is unhealthy because Python provider dependencies are missing.

Fresh runtime-chain readback:
- Gate result: `readonly_runtime_chain_refresh_after_015533_v1=runtime_surfaces_callable_non_promoting_source_control_blocked`.
- Auto-Quant status: `missing_dependency`, `healthy=false`, `bootstrap_needed=true`.
- Pre-Bayes structural confidence: `0.5822867835012198`, not a Board A 95% gate.
- Policy/CatBoost matched rows: `0`.
- Execution candidate: `actionable=false`, `execution_observe_only`.
- Structural path export: `3` rows, `0` mature rows, `0` rows with training weight.

Conclusion:
- The user-named providers were checked, but only yfinance and Kraken CLI are currently ready.
- Provider readiness does not supply the missing R6 owner/control rows or source-owned cross-timeframe MainRegimeV2 labels.
- Accepted rows added: `0`.
- New confidence gate: false.
- Canonical merge allowed: false.
- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun allowed: false.
- Strict full objective achieved: false.
- `update_goal=false`.

## Next

Preserve the Current Cursor next action for R6. Continue from owner/operator R6 export delivery, explicit `FLIP` approval, or genuinely new source-owned cross-timeframe MainRegimeV2 exports before any canonical merge or downstream promotion rerun.
