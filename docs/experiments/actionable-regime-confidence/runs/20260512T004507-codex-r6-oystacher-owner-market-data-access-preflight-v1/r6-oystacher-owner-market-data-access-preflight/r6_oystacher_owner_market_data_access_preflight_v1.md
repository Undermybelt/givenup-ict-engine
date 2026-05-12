# R6 Oystacher Owner Market-Data Access Preflight v1

- Run id: `20260512T004507-codex-r6-oystacher-owner-market-data-access-preflight-v1`.
- Gate result: `r6_oystacher_owner_market_data_access_preflight_v1=owner_data_access_not_available_locally_no_controls_acquired`.
- Required Oystacher normal-control cells: `17`.
- Required support per cell: `73`.
- Total normal-control shortfall: `1241`.
- Source-owned normal controls acquired: `0`.
- Cells with valid controls: `0/17`.
- Canonical merge allowed: `false`.
- Downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: `false`.
- Runtime code changed: `false`; shared intake mutated: `false`; owner-export root mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Result

The mapped owner routes are real but not locally actionable in this environment:

- Local Databento support is absent: no `databento` Python module, no `databento` CLI, no visible `DATABENTO`/`CME`/`CFTC`/`CBOE`/`CFE` environment variable names.
- Databento historical metadata for `GLBX.MDP3` returned `401 Not authenticated`; no market-data rows were downloaded.
- CME DataMine public pages returned `403` from this environment; no CME market-depth export was acquired.
- Cboe/CFE pages were reachable and confirmed public VIX/CFE market-data routes, but the public historical page exposes daily volume/open-interest and points to DataShop for custom data; no order-lifecycle normal-control rows were acquired.
- Official CFTC and CourtListener materials remain positive/provenance sources. They do not provide independent row-level normal/non-manipulation controls under the current contract.

This preflight does not change the active policy decision: same-exhibit `FLIP` rows are still rejected as controls unless explicitly approved, and no full downstream rerun is allowed before canonical merge.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T004507-codex-r6-oystacher-owner-market-data-access-preflight-v1/r6-oystacher-owner-market-data-access-preflight/r6_oystacher_owner_market_data_access_preflight_v1.json`
- Environment probe CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T004507-codex-r6-oystacher-owner-market-data-access-preflight-v1/r6-oystacher-owner-market-data-access-preflight/r6_oystacher_owner_access_environment_probe_v1.csv`
- Source access probe CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T004507-codex-r6-oystacher-owner-market-data-access-preflight-v1/r6-oystacher-owner-market-data-access-preflight/r6_oystacher_owner_source_access_probe_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T004507-codex-r6-oystacher-owner-market-data-access-preflight-v1/checks/r6_oystacher_owner_market_data_access_preflight_v1_assertions.out`
- Reproduction script: `docs/experiments/actionable-regime-confidence/runs/20260512T004507-codex-r6-oystacher-owner-market-data-access-preflight-v1/scripts/r6_oystacher_owner_market_data_access_preflight_v1.py`

## Next

Supply source-owned normal controls through the mapped CME/Cboe/Databento owner routes, or explicitly approve the same-exhibit `FLIP`-as-control exception; only then copy verifier-native files under the shared lock and rerun direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback while keeping R5 and R3 blocked.
