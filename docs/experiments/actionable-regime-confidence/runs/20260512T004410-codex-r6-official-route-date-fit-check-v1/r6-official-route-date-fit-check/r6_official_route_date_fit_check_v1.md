# R6 Official Route Date Fit Check v1

- Run id: `20260512T004410-codex-r6-official-route-date-fit-check-v1`.
- Gate result: `r6_official_route_date_fit_check_v1=official_owner_routes_confirmed_controls_not_acquired_cfe_depth_date_gap`.
- Required Oystacher normal-control cells reviewed: `17`.
- Candidate official owner routes still cover all cells: `17/17`.
- Valid source-owned normal controls acquired: `0`.
- FLIP-as-control approved: `false`.
- Canonical merge allowed: `false`.
- Downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun: `false`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`, limited to official route/date-fit lookup; trade usable: `false`.

## Findings

- CME DataMine remains the best official route for CME Globex, NYMEX, and COMEX cells because CME lists futures/options historical datasets including `Market by Order` and `PCAP`, and CME Market Depth files are designed to recreate Globex order books with order/trade timestamps. Product-specific start dates still need owner/export confirmation for the 2011-2013 CL, NG, HG, and ES cells.
- CME cloud market-depth is not enough for older cells by itself because the advertised cloud route starts later than the 2011-2013 Oystacher requirements; use DataMine/FIX-FAST/Market by Order or licensed equivalent instead.
- Cboe/CFE public historical pages confirm VIX futures history, daily volume/open interest, and price/volume detail, and Cboe lists real-time Top-of-Book/Depth-of-Book futures feeds. Those pages do not expose row-level historical depth/order-lifecycle normal controls for the 2014 VIX/CFE cell. Treat CFE as `custom DataShop/support export required`, not acquired.
- No owner approval, no licensed export files, and no verifier-native normal-control CSV/provenance exist under `/tmp/ict-engine-board-a-r6-owner-export-v1`.

## Official Sources Checked

- CME DataMine: `https://www.cmegroup.com/market-data/datamine-historical-data/index.html`
- CME futures/options data catalog: `https://www.cmegroup.com/market-data/browse-data/catalog/futures-and-options-data.html`
- CME Market Depth FAQ: `https://www.cmegroup.com/market-data/files/cme-group-market-depth-faq.pdf`
- CME historical/real-time data route: `https://www.cmegroup.com/market-data/real-time-and-historical-data.html`
- Cboe CFE futures historical data: `https://www.cboe.com/markets/us/futures/market-statistics/historical-data/futures/`
- Cboe CFE archive: `https://www.cboe.com/markets/us/futures/market-statistics/historical-data/settlement-archive`
- Cboe futures market data services: `https://www.cboe.com/market_data_services/us/futures/`
- Cboe VIX futures overview: `https://www.cboe.com/en/tradable-products/vix/vix-futures/`

## Next

Use CME DataMine/FIX-FAST/Market by Order or licensed equivalent for CME/NYMEX/COMEX/CME Globex cells, and request a Cboe/CFE DataShop or market-data-support export that explicitly covers historical depth/order-lifecycle rows for the 2014 VIX futures cell. Place source-owned normal controls and provenance under `/tmp/ict-engine-board-a-r6-owner-export-v1`, or explicitly approve the same-exhibit `FLIP`-as-control exception before any canonical merge or full-chain rerun.
