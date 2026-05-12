# Board A Provider Reachability After 034813 v1

Run id: `20260511T195320-codex-board-a-provider-reachability-after-034813-v1`

Gate result: `board_a_provider_reachability_after_034813_v1=ibkr_yfinance_kraken_reachable_tradingview_failed_source_controls_absent_no_promotion`

## Scope

This packet registers provider reachability command evidence after the `034813`/`035049` blocked audits. It does not mutate source roots, copy local triplets into the owner-export root, accept labels, approve `FLIP` rows, run canonical merge, rerun downstream promotion, or call `update_goal`.

## Readback

- Overall `provider-status --agent` exited `0` with `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- yfinance provider status exited `0`; yfinance QQQ 1d harness exited `0`.
- IBKR provider status exited `0` but reported dependency/runtime unhealthy; the ad-hoc low-pollution external fetch path exited `0` and wrote `21` QQQ daily rows from `2026-04-13` through `2026-05-11`.
- TradingView MCP provider status exited `0`, but the live QQQ harness exited `1` with `get_ohlcv` failure and recredential/MCP endpoint guidance.
- Kraken CLI provider status exited `0`; Kraken CLI OHLC exited `0`.
- The first Kraken external helper invocation used the wrong argument shape and exited `2`; a second corrected `uv` invocation was blocked by a PyPI TLS fetch failure; a third `python3` invocation used the right pair argument but wrong interval token and exited `1`; the final corrected `python3` invocation exited `0` and wrote `721` XBTUSD 1h rows from `2026-04-11 19:00:00+00:00` through `2026-05-11 19:00:00+00:00`.

## Decision

- Provider reachability improved for IBKR ad-hoc fetch and Kraken external helper readback, but this is not Board A acceptance evidence.
- Required source/control roots remain absent in the fresh readback: `/tmp/ict-engine-board-a-r6-owner-export-v1`, `/tmp/ict-engine-native-subhour-source-label-intake`, and `/tmp/ict-engine-source-panel-recency-extension`.
- The approval package remains non-approving: approval false, `FLIP` controls false, canonical merge false, downstream rerun false, strict full objective false, trade usable false, and `update_goal=false`.
- Accepted rows added: `0`; new confidence gate: `false`; canonical merge allowed: `false`; downstream promotion rerun allowed: `false`.

## Artifacts

- Command outputs: `docs/experiments/actionable-regime-confidence/runs/20260511T195320-codex-board-a-provider-reachability-after-034813-v1/command-output/`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T195320-codex-board-a-provider-reachability-after-034813-v1/provider-reachability-after-034813-v1/provider_reachability_after_034813_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T195320-codex-board-a-provider-reachability-after-034813-v1/checks/provider_reachability_after_034813_v1_assertions.out`

## Next

Preserve the Current Cursor next action. Continue only from explicit approval, verifier-native owner/export rows/source-owned normal controls, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before target-root materialization, verifier rerun, canonical merge, and downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion.
