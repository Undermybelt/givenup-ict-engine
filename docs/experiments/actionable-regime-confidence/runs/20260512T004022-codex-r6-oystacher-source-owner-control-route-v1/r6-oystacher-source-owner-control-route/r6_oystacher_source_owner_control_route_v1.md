# R6 Oystacher Source-Owner Control Route v1

- Run id: `20260512T004022-codex-r6-oystacher-source-owner-control-route-v1`.
- Gate result: `r6_oystacher_source_owner_control_route_v1=routes_identified_controls_not_acquired_no_merge_or_chain_rerun`.
- Required cells mapped: `17`.
- Source-owner routes checked: `6`.
- Local paths checked: `6`; existing local paths: `6`.
- CME Group is the source-owner route for CME/COMEX/NYMEX Oystacher cells.
- Cboe/CFE is the source-owner route for VIX futures cells.
- CourtListener/RECAP Exhibit A remains positive-candidate evidence only.
- FINRA Report Center remains useful for a separate equities manipulation branch, not the current Oystacher futures control cells.
- Local CME/Databento/Nautilus paths are aggregate, modern sample, or OHLCV/proxy data and remain rejected for this contract.
- Valid source-owned normal controls found: `0`.
- Canonical merge allowed: `false`; downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun: `false`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; owner-export root mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T004022-codex-r6-oystacher-source-owner-control-route-v1/r6-oystacher-source-owner-control-route/r6_oystacher_source_owner_control_route_v1.json`
- Source-owner routes CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T004022-codex-r6-oystacher-source-owner-control-route-v1/r6-oystacher-source-owner-control-route/r6_oystacher_source_owner_control_routes_v1.csv`
- Control cell route map CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T004022-codex-r6-oystacher-source-owner-control-route-v1/r6-oystacher-source-owner-control-route/r6_oystacher_control_cell_route_map_v1.csv`
- Local path disposition CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T004022-codex-r6-oystacher-source-owner-control-route-v1/r6-oystacher-source-owner-control-route/r6_oystacher_local_control_path_disposition_v1.csv`
- Source-owned normal control request: `docs/experiments/actionable-regime-confidence/runs/20260512T004022-codex-r6-oystacher-source-owner-control-route-v1/r6-oystacher-source-owner-control-route/r6_oystacher_source_owner_control_request_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T004022-codex-r6-oystacher-source-owner-control-route-v1/checks/r6_oystacher_source_owner_control_route_v1_assertions.out`

Next:
- Acquire source-owned normal controls from the mapped CME/Cboe routes, or obtain explicit board/user approval for RECAP/PACER provenance plus FLIP-as-control, then merge under a shared lock and rerun the full chain.
