# IBKR HMDS Farm Status Readback v1

Run id: `20260512T102828+0800-codex-ibkr-hmds-farm-status-readback-v1`

Mode: `provider_health_readback_only`

## Scope

This readback answers the IBKR historical-data farm question for both Board A and Board B. It does not approve source/control evidence, does not select historical data, does not promote Auto-Quant, BBN, CatBoost/path-ranking, or execution-tree output, does not make a trade claim, and does not call `update_goal`.

## Evidence

- `provider-status --agent` exited `0`: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- `provider-status --provider ibkr --agent` exited `0` but reported `market_data:0/1 ready`.
- `provider-status --provider ibkr_bridge --agent` exited `0` but reported `local_runtime:0/1 ready`.
- Both `ibkr` and `ibkr_bridge` are still `configured_runtime_unhealthy` in the default ict-engine provider catalog because the runtime executing provider-status is missing the expected IBKR dependencies, even though the local IBKR API is reachable on port `4002`.
- A low-pollution direct probe with `uv run --with ib_async --with pandas` connected read-only to `127.0.0.1:4002` as `clientId=383`, qualified `QQQ`, and requested `5 D` daily historical data.

## Historical Farm Readback

Direct probe result:

- Connected: `true`
- Managed account visible: `DUN189136`
- Qualified `QQQ` contract: `conId=320227571`, `exchange=SMART`, `primaryExchange=NASDAQ`
- Historical rows returned: `5`
- First bar: `2026-05-05`
- Last bar: `2026-05-11`

IBKR farm messages captured during the probe:

- `2104`: market data farm connection OK: `hfarm`
- `2107`: historical market data farm connection inactive but available on demand: `apachmds`
- `2107`: historical market data farm connection inactive but available on demand: `ushmds`
- `2158`: security-definition data farm connection OK: `secdefhk`
- `2106`: historical market data farm connection OK: `ushmds`

Interpretation:

- The `Inactive: apachmds, ushmds` surface is not by itself proof that IBKR historical data is unavailable. IBKR reported the historical farms as inactive/on-demand before the request, then activated `ushmds` when the US `QQQ` historical request was made.
- `apachmds` remained inactive because this probe did not request an APAC instrument. It should stay a visible provider-context caveat, not a promotion blocker for a US-only QQQ probe.
- The important Board A/B gate is stricter: default ict-engine provider readiness still says `ibkr` and `ibkr_bridge` are not ready, so any chain requiring default provider readiness remains fail-closed until that catalog path is repaired or the run explicitly records an accepted low-pollution `uv --with ib_async` fetch artifact.

## Decision

Gate: `ibkr_hmds_farm_status_readback_v1=ad_hoc_historical_probe_pass_default_provider_gate_fail_closed`.

This resolves the narrow farm-status question: `ushmds` can activate on demand and return historical rows. It does not make IBKR fully ready in the default ict-engine provider catalog and does not unlock Board A or Board B promotion.

Promotion allowed: `false`

`update_goal=false`

## Next

For future A/B chains, record IBKR in two separate fields:

- `ibkr_ad_hoc_historical_probe`: pass only when a run-local `uv --with ib_async` request returns rows for the exact instrument/window.
- `ibkr_default_provider_gate`: fail-closed until `provider-status --provider ibkr` and `provider-status --provider ibkr_bridge` report ready in the same runtime or the board explicitly accepts the low-pollution override for that slice.
