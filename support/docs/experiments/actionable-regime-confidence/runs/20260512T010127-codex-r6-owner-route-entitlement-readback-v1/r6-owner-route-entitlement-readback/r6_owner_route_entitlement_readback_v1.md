# R6 Owner Route Entitlement Readback v1

- Run id: `20260512T010127-codex-r6-owner-route-entitlement-readback-v1`.
- Observed cursor: `20260512T004410+0800-codex-r6-official-route-date-fit-check-v1`.
- Gate result: `r6_owner_route_entitlement_readback_v1=route_fit_improved_controls_not_acquired_no_merge`.
- Required Oystacher normal-control cells: `17`.
- Valid source-owned normal controls acquired: `0`.
- FLIP-as-control approved: `false`.
- Canonical merge allowed: `false`; downstream rerun allowed: `false`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; owner-export root mutated: `false`; raw data committed: `false`.

## Findings

- CME public client documentation improves the route fit: Market Depth starts at CME `2005`, NYMEX `2007`, COMEX `2007`, and FIX-formatted files are available from `2009`; this covers the broad 2011-2013 Oystacher CME/NYMEX/COMEX date window at exchange level.
- That does not acquire verifier-native controls. The board still needs a licensed CME Market Depth/Market by Order or equivalent export, product/contract scope confirmation, provenance, and source-owned normal-control policy acceptance before canonical merge.
- Cboe DataShop exposes a legacy CFE VIX futures trades-and-quotes product covering April 2004 through February 2018, which improves the VIX date-route fit. It still does not prove historical full-depth/order-lifecycle availability; use DataShop/support for a custom export if depth/order-lifecycle is required.
- Local entitlement remains absent: no `databento` CLI, no `dbn` CLI, no Python `databento`, no Python `pyarrow`, no Databento API key env, and no complete owner-export package under `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Local Tomac futures material remains bar data (`ohlcv-1m`) and cannot be promoted into source-owned normal-control labels.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T010127-codex-r6-owner-route-entitlement-readback-v1/r6-owner-route-entitlement-readback/r6_owner_route_entitlement_readback_v1.json`
- Official route CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T010127-codex-r6-owner-route-entitlement-readback-v1/r6-owner-route-entitlement-readback/r6_owner_route_entitlement_sources_v1.csv`
- Local entitlement CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T010127-codex-r6-owner-route-entitlement-readback-v1/r6-owner-route-entitlement-readback/r6_owner_route_local_entitlement_v1.csv`
- Local schema CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T010127-codex-r6-owner-route-entitlement-readback-v1/r6-owner-route-entitlement-readback/r6_owner_route_local_schema_readback_v1.csv`

## Next

Obtain licensed CME Market Depth/Market by Order or equivalent exports and Cboe/CFE VIX historical trades/quotes or depth/order-lifecycle export with provenance, or explicitly approve same-exhibit `FLIP`-as-control. Only after verifier-native controls and provenance arrive should the owner-export root be populated and the full chain rerun.
