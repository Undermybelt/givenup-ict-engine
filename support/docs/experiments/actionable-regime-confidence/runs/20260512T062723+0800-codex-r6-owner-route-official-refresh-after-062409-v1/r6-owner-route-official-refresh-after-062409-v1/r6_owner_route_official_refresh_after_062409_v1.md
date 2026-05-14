# R6 Owner Route Official Refresh After 062409 v1

Run id: `20260512T062723+0800-codex-r6-owner-route-official-refresh-after-062409-v1`

Gate result: `r6_owner_route_official_refresh_after_062409_v1=official_routes_confirmed_no_dispatch_no_rows_no_approval`

Board sha256 before artifact: `e892bc5d5cb9a17c7cf7cbe42d51bb12b63a5c7dd9d225704eb0962362f08f36`

## Scope

This packet refreshes official owner/export routes after `062409` closed the TSIE/R3/R5 public-candidate branch. It does not send mail, use a vendor portal, acquire licensed exports, approve same-exhibit `FLIP` controls, mutate `/tmp/ict-engine-board-a-r6-owner-export-v1`, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Official Route Readback

| Owner | Official route evidence | Board relevance | Dispatch status |
|---|---|---|---|
| CME Group | CME DataMine advertises historical futures/options datasets including `Market by Order` and `PCAP`; the platform flow is select data, create/login account, request a data license, then receive/access data. CME lists Data Sales ordering contact `CMEDataSales@cmegroup.com`. Source: `https://www.cmegroup.com/market-data/datamine-historical-data.html` | Confirms the active CME Market Depth / Market by Order owner-export route remains the right path for licensed order-lifecycle normal controls. | `not_sent_no_ticket_no_export` |
| Cboe/CFE | Cboe Futures Exchange official contacts include CFE Market Data Services; Cboe DataShop futures products include `CFE VIX Futures Trades and Quotes` described as all VIX futures trades and quotes on CFE. Sources: `https://www.cboe.com/en/markets/us/futures/`, `https://datashop.cboe.com/futures` | Confirms the active Cboe/CFE VIX trades/quotes owner route remains the right path for licensed VIX/CFE validation/control evidence. | `not_sent_no_ticket_no_export` |

## Required Roots

- `/tmp/ict-engine-board-a-r6-owner-export-v1`: `false`
- `/tmp/ict-engine-native-subhour-source-label-intake`: `false`
- `/tmp/ict-engine-source-panel-recency-extension`: `false`

## Decision

The official route evidence is current enough to preserve the active Current Cursor next action, but it does not unlock promotion. No vendor ticket, license, export order, support identifier, source-owned normal controls, or explicit `FLIP`-as-control approval exists in this slice.

Promotion remains blocked: external requests sent `false`, approval present `false`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Use the existing v5 `.eml` drafts through an approved operator mail/vendor-portal path and preserve returned ticket/export/license/order/support identifiers in `provenance_manifest.json`, or supply explicit source/control approval or verifier-native owner-export rows. Only after `/tmp/ict-engine-board-a-r6-owner-export-v1` is populated under the current contract should direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback rerun.
