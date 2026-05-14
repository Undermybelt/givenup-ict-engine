# R6 Owner Export Access Route Preflight v1

- Run id: `20260512T010212-codex-r6-owner-export-access-route-preflight-v1`.
- Regenerated after the `20260512T010744` board-reference integrity readback recorded this run root as missing.
- Gate result: `r6_owner_export_access_route_preflight_v1=official_dispatch_routes_pinned_controls_not_acquired`.
- Current Cursor is not changed by this repair; `20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1` remains authoritative.

## Result

- Official source/access surfaces pinned: `7`.
- Owner branches: `2` (`cme_group`, `cboe_cfe`).
- Required Oystacher normal-control cells: `17`; required support per cell: `73`.
- R6 owner-export required files present: false.
- Source-label equivalence root is now present, but remains `schema_ready_unscored_no_confidence_acceptance` per the `010053` / `011013` verifier readbacks.
- R3 native-subhour and R5 recency-extension source roots still lack required files.
- Valid source-owned normal controls acquired: `0`.
- Same-exhibit `FLIP` approval acquired: false.
- Canonical merge allowed: false; downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: false.
- Accepted rows added: `0`; source-label accepted confidence labels remain `0/4`; new confidence gate: false; strict full objective achieved: false. `update_goal=false`.
- Runtime code changed: false. Shared intake mutated: false. Owner-export root mutated: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Evidence

- Official/access route CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T010212-codex-r6-owner-export-access-route-preflight-v1/r6-owner-export-access-route-preflight-v1/official_source_access_routes_v1.csv`
- Required-file status CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T010212-codex-r6-owner-export-access-route-preflight-v1/r6-owner-export-access-route-preflight-v1/owner_export_required_file_status_v1.csv`
- Summary JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T010212-codex-r6-owner-export-access-route-preflight-v1/r6-owner-export-access-route-preflight-v1/r6_owner_export_access_route_preflight_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T010212-codex-r6-owner-export-access-route-preflight-v1/checks/r6_owner_export_access_route_preflight_v1_assertions.out`

## Next

- Preserve the Current Cursor next action: use the verified `005913` request drafts and `010506` contact routes to satisfy the R6 CME/Cboe owner-export requests or obtain explicit same-exhibit `FLIP`-control approval. Only after verifier-native controls plus provenance exist should `/tmp/ict-engine-board-a-r6-owner-export-v1` be populated under the shared lock and the direct verifier plus full chain be rerun.
