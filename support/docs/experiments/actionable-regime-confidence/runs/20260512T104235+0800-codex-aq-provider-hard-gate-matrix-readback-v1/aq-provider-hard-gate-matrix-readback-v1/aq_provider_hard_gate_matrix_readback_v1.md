# AQ Provider Hard Gate Matrix Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T104235+0800-codex-aq-provider-hard-gate-matrix-readback-v1`

Mode: `six_provider_hard_gate_matrix_readback_no_promotion`

## Scope

This packet materializes the Board A hard gate from `2026-05-12 Supplemental 103404 AQ Provider Hard Gate Restatement v1`: future Board A/B promotion claims must show real AQ/provider provenance and explicit rows for `IBKR`, `TradingViewRemix/TVR`, `yfinance/YF`, `Kraken`, `Binance`, and `Bybit`. It does not select `HTF`, `MTF`, or `LTF`, does not approve source/control evidence, does not run a selected-data AQ promotion chain, does not promote BBN/CatBoost/execution-tree output, and does not call `update_goal`.

## Commands

- `./target/debug/ict-engine provider-status --provider yfinance --agent`: exit `0`
- `./target/debug/ict-engine provider-status --provider tradingview_mcp --agent`: exit `0`
- `./target/debug/ict-engine provider-status --provider ibkr --agent`: exit `0`
- `./target/debug/ict-engine provider-status --provider ibkr_bridge --agent`: exit `0`
- `./target/debug/ict-engine provider-status --provider kraken_public --agent`: exit `0`
- `./target/debug/ict-engine provider-status --provider kraken_cli --agent`: exit `0`
- `./target/debug/ict-engine provider-status --provider binance_public --agent`: exit `0`
- `./target/debug/ict-engine provider-status --provider bybit_public --agent`: exit `0`
- `./target/debug/ict-engine auto-quant-status --state-dir docs/experiments/actionable-regime-confidence/runs/20260512T101221+0800-codex-board-b-093854-local-cache-seed-v2/state_local_cache_seed_v2 --output-format json`: exit `0`

## Provider Matrix

| Provider group | Readback |
|---|---|
| `yfinance/YF` | Ready for live runtime and market data. |
| `TradingViewRemix/TVR` | Fail-closed: `tradingview_mcp_connectivity_probe_failed`. |
| `IBKR` | Fail-closed in default ict-engine runtime: dependencies missing while gateway is reachable. `ibkr_bridge` also remains not ready. |
| `Kraken` | Mixed: `kraken_cli` local runtime ready; `kraken_public` market-data adapter fail-closed on missing system Python dependencies. |
| `Binance` | Fail-closed: `python3_provider_dependencies_missing`. |
| `Bybit` | Fail-closed: `python3_provider_dependencies_missing`. |

## AQ Readback

The referenced `101221` Auto-Quant workspace reports `dependency_ready_data_ready`, `healthy=true`, and `data_ready=true`. That evidence is useful for AQ readiness, but it is not a single AQ/provider run that satisfies the full six-provider matrix plus nonzero mature rooted observations.

## Gate

- `pass:six_provider_matrix_rows_recorded`
- `pass:auto_quant_status_reference_exit0_dependency_ready_data_ready`
- `partial:yfinance_ready`
- `partial:kraken_cli_ready_but_public_market_data_not_ready`
- `fail_closed:tradingview_mcp_connectivity_probe_failed`
- `fail_closed:ibkr_default_provider_gate_not_ready`
- `fail_closed:ibkr_bridge_provider_gate_not_ready`
- `fail_closed:kraken_public_binance_public_bybit_public_python3_dependencies_missing`
- `fail_closed:no_single_artifact_satisfies_aq_provider_invoked_plus_six_provider_matrix_plus_nonzero_mature_rooted_observations`
- `accepted_rows_added=0`
- `mature_rooted_branch_observations_added=0`
- `promotion_allowed=false`
- `update_goal=false`

## Next

Do not treat provider-status exit `0` as provider readiness. Future AQ/provider packets must record the same six-provider rows, distinguish ready/default/ad-hoc paths, and still produce nonzero mature rooted observations before the ordered `Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution tree` chain can be considered for promotion.
