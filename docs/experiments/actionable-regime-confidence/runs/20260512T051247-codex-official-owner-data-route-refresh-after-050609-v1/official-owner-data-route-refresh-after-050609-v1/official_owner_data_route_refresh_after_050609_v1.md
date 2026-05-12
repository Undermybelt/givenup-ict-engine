# Official Owner Data Route Refresh After 050609 v1

Run id: `20260512T051247-codex-official-owner-data-route-refresh-after-050609-v1`

Gate result: `official_owner_data_route_refresh_after_050609_v1=routes_confirmed_external_license_export_required_no_local_unlock`

## Purpose

Refresh the official CME/Cboe owner-data route after the terminal non-promoting `050609` ExtraTrees-light threshold screen. This is source-route evidence only. It does not create source/control rows, approve same-exhibit `FLIP` controls, mutate the canonical intake, run canonical merge, rerun downstream promotion, or authorize `update_goal`.

## Source Routes

| Owner | Route | Board relevance |
|---|---|---|
| CME Group | `https://www.cmegroup.com/market-data/datamine-historical-data/index.html` | CME DataMine is the historical data purchase/extract route and lists futures/options datasets including Market by Order. This matches the R6 need for licensed verifier-native order-lifecycle/depth exports. |
| CME Group | `https://cmegroupclientsite.atlassian.net/wiki/display/EPICSANDBOX/Market%2BDepth` | CME Market Depth documentation describes tick-level book/trade reconstruction data via DataMine/support. It is an owner/export route, not a local repo artifact. |
| Cboe DataShop | `https://datashop.cboe.com/cfe-vix-volatility-index-futures-trades-quotes` | CFE VIX Futures Trades and Quotes supplies historical CFE/VIX trades/quotes fields for the older product window. It still requires DataShop acquisition before Board A can use it as verifier-native evidence. |
| Cboe | `https://www.cboe.com/markets/us/futures/market-statistics/historical-data/settlement-archive` | Public CFE historical archive data is summary price-volume context. It is not row-level order-lifecycle data or owner-approved normal controls. |

## Local Root Check

| Root | Status |
|---|---|
| `/tmp/ict-engine-board-a-r6-owner-export-v1` | absent |
| `/tmp/ict-engine-native-subhour-source-label-intake` | absent |
| `/tmp/ict-engine-source-panel-recency-extension` | absent |

## Decision

- Official CME/Cboe owner routes are still the right route for the current cursor.
- Public summary/context pages are not enough for canonical merge.
- No verifier-native normal controls, source-owned R5 recency rows, or native sub-hour rows arrived locally.
- Promotion status remains unchanged: source/control evidence acquired `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Send or otherwise satisfy the CME and Cboe/CFE owner-export requests, preserving ticket/export/license identifiers in provenance. Only after verifier-native files are available under the approved `/tmp` root should the direct verifier, split calibration, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree chain rerun.
