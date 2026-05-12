# R6 Oystacher Owner-Control Source Route Screen v1

- Run id: `20260512T003924-codex-r6-oystacher-owner-control-source-route-screen-v1`.
- Gate result: `r6_oystacher_owner_control_source_route_screen_v1=official_source_routes_identified_controls_not_acquired`.
- Required cells: `17`.
- Cells with candidate official source route: `17`.
- Valid source-owned normal controls acquired: `0`.
- FLIP-as-control approved: `false`.
- Canonical merge allowed: `false`.
- Downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun: `false`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Official Source Routes

- CME route: CME DataMine Market Depth/FIX-FAST or cloud market-depth export for CME Globex, NYMEX, and COMEX cells. Use for crude oil, natural gas, high-grade copper, and E-mini S&P 500 normal controls; confirm product/date availability for 2011-2013 cells.
- Cboe route: Cboe/CFE DataShop or CFE Depth-of-Book market data export for VIX futures normal controls; confirm historical depth/order-book detail and licensing.

## Next

Use CME DataMine/market-depth exports for CME/NYMEX/COMEX/CME Globex cells and Cboe/CFE DataShop or depth-of-book exports for VIX/CFE cells; place source-owned normal controls under /tmp/ict-engine-board-a-r6-owner-export-v1 with provenance, or get explicit FLIP-control approval, then rerun the full chain.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T003924-codex-r6-oystacher-owner-control-source-route-screen-v1/r6-oystacher-owner-control-source-route-screen/r6_oystacher_owner_control_source_route_screen_v1.json`
- Source routes CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T003924-codex-r6-oystacher-owner-control-source-route-screen-v1/r6-oystacher-owner-control-source-route-screen/r6_oystacher_owner_control_source_routes_v1.csv`
- Cell route CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T003924-codex-r6-oystacher-owner-control-source-route-screen-v1/r6-oystacher-owner-control-source-route-screen/r6_oystacher_required_cell_source_routes_v1.csv`
- Export request: `docs/experiments/actionable-regime-confidence/runs/20260512T003924-codex-r6-oystacher-owner-control-source-route-screen-v1/r6-oystacher-owner-control-source-route-screen/owner_normal_control_export_request_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T003924-codex-r6-oystacher-owner-control-source-route-screen-v1/checks/r6_oystacher_owner_control_source_route_screen_v1_assertions.out`
