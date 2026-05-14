# Post-093937 Board A Continuation Audit v1

Run id: `20260512T100356+0800-codex-post-093937-board-a-continuation-audit-v1`

Mode: `append_only_readonly_non_promoting`

## Scope

This audit counts late Board B discovery root `093435` against Board A without promotion. It rechecks `093820`, `093854`, and `093937` only as duplicate-guard context because concurrent EOF registrations already count those roots. It also refreshes provider status, checks a known local Auto-Quant data-ready state, and reruns the direct Manipulation intake verifier. It does not select `HTF`, `MTF`, or `LTF`, does not approve source/control evidence, does not mutate canonical intake, and does not call `update_goal`.

## Readback

- `093435`: Auto-Quant TOMAC smoke ran and produced `5` trades, win rate `60.0000`, total profit `-1.3100`, Sharpe `-0.0192`, profit factor `0.6185`. Non-promoting.
- `093820`: pair repair exits `1` with `No data found`. Non-promoting.
- `093854`: HTF factor handoff exits `0`, but prepare exits `1` with DNS / Binance market-load failure. Non-promoting.
- `093937`: execution-candidate branch path is preserved, but readiness remains `0.4504361163104953` and observe-only. Non-promoting.
- Direct Manipulation sidecar verifier exits `0` with status `schema_ready_unscored`, positives `73`, controls `73`, matched groups `70`.
- Owner-export `direct_manipulation_*` triplet under `/tmp/ict-engine-board-a-r6-owner-export-v1` is present: `False`.
- Local Auto-Quant status is `dependency_ready_data_ready`, healthy `True`, data_ready `True`.

Provider status refresh:
- `yfinance` / `live_runtime`: ready=True, status=`ready`, reason=`native_yfinance_runtime_available`.
- `ibkr_bridge` / `local_runtime`: ready=False, status=`configured_runtime_unhealthy`, reason=`ibkr_bridge_runtime_dependencies_missing_with_gateway_reachable`.
- `kraken_cli` / `local_runtime`: ready=True, status=`ready`, reason=`kraken_cli_config_detected`.
- `ibkr` / `market_data`: ready=False, status=`configured_runtime_unhealthy`, reason=`ibkr_runtime_dependencies_missing_with_gateway_reachable`.
- `kraken_public` / `market_data`: ready=False, status=`configured_runtime_unhealthy`, reason=`python3_provider_dependencies_missing`.
- `tradingview_mcp` / `market_data`: ready=False, status=`configured_runtime_unhealthy`, reason=`tradingview_mcp_connectivity_probe_failed`.
- `yfinance` / `market_data`: ready=True, status=`ready`, reason=`public_yahoo_http_endpoints`.

## Decision

Gate: `post_093937_board_a_continuation_audit_v1=093435_counted_later_roots_duplicate_guard_non_promoting_goal_not_complete`.

Accepted rows added `0`; source/control evidence acquired false; explicit user-selected history false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.

## Next

Ask for exactly one explicit selected-history lane: `HTF`, `MTF`, or `LTF`; keep R6/R5/R3 source-control gates fail-closed and do not infer the selection from agent artifacts.
