# R6 Owner Export Official Contact Route Check v1

- Run id: `20260512T010506-codex-r6-owner-export-official-contact-route-check-v1`.
- Input request drafts: `docs/experiments/actionable-regime-confidence/runs/20260512T005913-codex-r6-owner-export-sendable-requests-v3`.
- Gate result: `r6_owner_export_official_contact_route_check_v1=official_contact_routes_verified_requests_not_sent_controls_not_acquired`.
- Required Oystacher normal-control cells represented: `17`.
- Required support per cell: `73` valid source-owned normal/non-manipulation controls.
- External requests sent by this packet: false.
- Valid source-owned normal controls acquired now: `0`.
- Same-exhibit `FLIP` approval acquired now: false.
- Canonical merge allowed now: false.
- Downstream rerun allowed now: false.

## Verified Official Contact Routes

| Owner | Route | Official URL | Contact channel captured | Use |
|---|---|---|---|---|
| CME Group | DataMine historical data ordering and sales | `https://www.cmegroup.com/market-data/datamine-historical-data/index.html` | `CMEDataSales@cmegroup.com`; DataMine account/order/license workflow | Send CME/NYMEX/COMEX/CME Globex 2011-2013 owner-export request or request product/date availability confirmation. |
| CME Group | CME DataMine support/contact fallback | `https://www.cmegroup.com/market-data/datamine-historical-data/index.html` | `marketdata@cmegroup.com` | Use for DataMine or market-data service questions if sales route does not accept the export request. |
| Cboe/CFE | Cboe DataShop contact | `https://datashop.cboe.com/contactus-2` | DataShop sales/support contact page; phone `800-307-8979`; global phone `312-786-7400`; contact form categories `Sales` and `Support` | Send or route the 2014 VIX/CFE historical depth/order-lifecycle request to DataShop support/sales. |
| Cboe/CFE | CFE market-data services | `https://www.cboe.com/markets/us/futures/` | CFE Market Data Services contact observed on the official page: `marketdata@cboe.com`, phone `212-378-8821` | Confirm 2014 CFE/VIX futures depth/order-lifecycle availability and licensing. |

## Artifacts

- Contact route CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T010506-codex-r6-owner-export-official-contact-route-check-v1/r6-owner-export-official-contact-route-check-v1/r6_owner_export_official_contact_routes_v1.csv`
- Summary JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T010506-codex-r6-owner-export-official-contact-route-check-v1/r6-owner-export-official-contact-route-check-v1/r6_owner_export_official_contact_route_check_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T010506-codex-r6-owner-export-official-contact-route-check-v1/checks/r6_owner_export_official_contact_route_check_v1_assertions.out`

## Decision

The request branch is now contact-route-ready, but not evidence-ready. Do not populate `/tmp/ict-engine-board-a-r6-owner-export-v1`, merge canonical intake, or rerun provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree promotion until source-owned controls and provenance arrive, or explicit same-exhibit `FLIP` approval is recorded.

## Next

Use the verified CME and Cboe/CFE contact routes to send the v3 request drafts. Preserve ticket, export, license, order, or support identifiers in `provenance_manifest.json` when controls arrive.
