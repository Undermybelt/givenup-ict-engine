# R6 Owner Route Refresh After 031655 v1

Run id: `20260512T032258-codex-r6-owner-route-refresh-after-031655-v1`

Gate result: `r6_owner_route_refresh_after_031655_v1=official_routes_current_controls_not_acquired_no_merge`

Board sha256 before refresh: `436d3c55cc2093a46721fb92b814aa9be023aff4835439b7ec950f9e1526543e`

## Scope

This packet refreshes the official-source route evidence after the latest durable Board A current-objective audit, `031655`. It does not send external requests, acquire licensed rows, mutate `/tmp/ict-engine-board-a-r6-owner-export-v1`, approve same-exhibit `FLIP` controls, run canonical merge, rerun provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree, or call `update_goal`.

## Inputs

- Latest durable current-objective audit: `20260512T031655-codex-current-objective-completion-audit-after-031435-v1`, gate `not_complete_latest_r6_packets_nonpromoting_source_controls_downstream_blocked`.
- Dispatch readiness packet: `20260512T031353-codex-r6-owner-export-dispatch-readiness-after-030957-v1`, gate `requests_ready_dispatch_or_approval_required_rows_not_acquired`.
- Owner route entitlement packet: `20260512T010127-codex-r6-owner-route-entitlement-readback-v1`, gate `route_fit_improved_controls_not_acquired_no_merge`.
- Live roots rechecked before this packet: R6 owner-export root absent, R3 native-subhour root absent, R5 recency-extension root absent.

## Official Route Refresh

- CME Market Depth remains the strongest Oystacher-date route for CME/NYMEX/COMEX controls: the official page describes historical Market Depth availability covering CME from `2005`, NYMEX and COMEX from `2007`, with FIX-formatted files from `2009`, and order book/trade data at tick granularity. This improves exchange-level date fit but still requires a licensed verifier-native export, product/contract scope, provenance, and normal-control policy acceptance.
- Cboe DataShop legacy CFE VIX futures trades/quotes covers the Oystacher-era VIX window (`April 2004` through `February 2018`) and supplies quote/trade-style fields, but it does not by itself provide the order IDs or side-added-liquidity style order-lifecycle fields needed to replace independent normal controls.
- Cboe DataShop current CFE Futures Trades product has stronger trade/order identifiers, including buy/sell side, trade condition, order IDs, and side-added-liquidity fields, but its availability starts in `March 2018`, after the Oystacher VIX 2013/2014 window.
- Cboe US Futures Depth of Book remains a current-service route; historical 2013/2014 depth or order-lifecycle availability still needs DataShop or market-data support confirmation and licensed export.

## Decision

- Source-owned normal controls acquired: `0`.
- Explicit `FLIP` approval present: `false`.
- R6 owner-export root complete: `false`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Next

Preserve the `031655` current-objective blocker. Continue only from a licensed CME Market Depth/Market by Order or equivalent verifier-native export, a Cboe/CFE historical depth/order-lifecycle export or support-confirmed legacy package with provenance, explicit `FLIP`-as-control approval, or genuinely source-owned cross-timeframe `MainRegimeV2` exports. Only after source/control gates unlock should the full provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree chain rerun.
