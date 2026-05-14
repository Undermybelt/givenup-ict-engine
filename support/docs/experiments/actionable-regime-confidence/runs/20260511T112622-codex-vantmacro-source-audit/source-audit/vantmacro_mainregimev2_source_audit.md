# VantMacro MainRegimeV2 Source Audit

Run ID: `20260511T112622+0800-codex-vantmacro-source-audit`

## Scope

- Active Board A taxonomy: `MainRegimeV2`.
- Required price roots: `Bull`, `Bear`, `Sideways`, `Crisis`.
- Separate direct lane: `Manipulation`.
- Candidate source: VantMacro public methodology and market-regime guide.

## Public Source Readback

- VantMacro documents a daily historical replay of its classifier from 2003-12-17 to 2026-01-20 with `8039` daily classifications on the methodology page.
- Its market-regime guide describes a 7-state classification system and a daily historical replay from 2003-12-17 to 2025-12-05 with `8025` daily classifications and `427` transitions.
- Public regimes are macro composite states: `ReflationaryExpansion`, `StagflationarySqueeze`, `PostShockRecovery`, `DisinflationarySlowdown`, `LateCycleInflationaryBoom`, `CrisisLiquidation`, and `Transitional`.
- Public inputs are macro/market factors from FRED and Yahoo Finance, including CFNAI, CPI, Fed balance sheet, VIX, high-yield OAS, and asset prices.
- The root page says the free tier exposes today's regime snapshot and methodology, while Pro unlocks the full historical regime history.

Sources:
- https://vantmacro.com/methodology
- https://vantmacro.com/learn/guides/market-regimes
- https://vantmacro.com/

## Decision

- Accepted MainRegimeV2 parent-root slots added: `0`.
- Accepted direct `Manipulation` rows/windows added: `0`.
- Public historical row export located: `false`.
- Exact active roots located: `false`.
- Native timeframe: `1d`.
- Gate result: `blocked_vantmacro_macro_model_output_not_exact_mainregimev2_label_panel`.

VantMacro is useful macro-context provenance, but it is not an attachable Board A label panel. Its states are not exact `Bull` / `Bear` / `Sideways` / `Crisis` labels for the current yfinance/Kraken provider-instrument-timeframe missing slots. `CrisisLiquidation` can only inform `Crisis` provenance. A local reimplementation from the public methodology would be a derived model/proxy, not an independent source-label export.

Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.
