# R6 Owner Route Current Web Recheck v1

- Run id: `20260512T014314-codex-r6-owner-route-current-web-recheck-v1`.
- Gate result: `r6_owner_route_current_web_recheck_v1=current_official_routes_rechecked_controls_not_acquired_no_merge`.
- Current Cursor preserved: `true`.
- Board hash before artifact: `48aae7026e70b109ba517bb4fff2c529701017a179ad2b0a260b1a6245319e0d`.
- Artifact root restored after a reference-integrity verification found the local run root absent; this restoration keeps the same fail-closed result and does not add acceptance evidence.

## Result

- CME DataMine remains the current official public route for licensed historical CME futures/options exports. For the 2011-2013 R6 cells, the request should continue to emphasize Market Depth/FIX-FAST or licensed equivalent early-window rows; Market by Order is acceptable only if CME confirms product/date coverage for the requested cells.
- Cboe DataShop remains the current route for CFE/VIX futures trades and quotes that fit the 2014 VIX/CFE date window. It still does not prove historical full-depth or order-lifecycle availability.
- Cboe/CFE market-data services remain the current support/custom-export route for futures Top-of-Book/Depth-of-Book style data. Historical 2014 depth/order-lifecycle rows are still not acquired.
- R6 owner-export root is still absent. R3 native-subhour and R5 recency-extension roots are still absent. Source-label equivalence root is present but confidence-blocked.
- Accepted rows added: `0`; new confidence gate: `false`; canonical merge allowed: `false`; downstream promotion rerun allowed: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; R3/R5/R6 roots mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Current Official Route Sources

| Owner | Route | URL | Request implication |
|---|---|---|---|
| CME Group | CME DataMine historical data | `https://www.cmegroup.com/market-data/datamine-historical-data/index.html` | Route through CME DataMine/Data Sales and require verifier-native normal-control rows plus provenance. |
| CME Group | CME Market Depth Files FAQ | `https://www.cmegroup.com/market-data/files/cme-group-market-depth-faq.pdf` | Ask for Market Depth/FIX-FAST, Market by Order, or licensed equivalent rows with product/date coverage confirmation. |
| Cboe/CFE | Cboe DataShop CFE VIX futures trades and quotes | `https://datashop.cboe.com/cfe-vix-volatility-index-futures-trades-quotes` | Use for VIX trades/quotes and ask support for depth/order-lifecycle if the verifier requires deeper controls. |
| Cboe/CFE | Cboe U.S. Futures Market Data Services | `https://ww2.cboe.com/market_data_services/us/futures/` | Use as the support/custom-export path for Top-of-Book/Depth-of-Book style futures data. |

## Boundary

This recheck only refreshes current owner-route evidence for the already-sendable R6 requests. It does not acquire controls, approve `FLIP` rows, mutate intake roots, or authorize downstream promotion.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T014314-codex-r6-owner-route-current-web-recheck-v1/r6-owner-route-current-web-recheck-v1/r6_owner_route_current_web_recheck_v1.json`
- Source CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T014314-codex-r6-owner-route-current-web-recheck-v1/r6-owner-route-current-web-recheck-v1/r6_owner_route_current_web_sources_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T014314-codex-r6-owner-route-current-web-recheck-v1/checks/r6_owner_route_current_web_recheck_v1_assertions.out`
- Reproduction script: `docs/experiments/actionable-regime-confidence/runs/20260512T014314-codex-r6-owner-route-current-web-recheck-v1/scripts/r6_owner_route_current_web_recheck_v1.py`
