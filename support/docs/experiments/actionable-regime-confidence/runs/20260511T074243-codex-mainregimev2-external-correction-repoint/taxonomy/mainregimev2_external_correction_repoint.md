# MainRegimeV2 External Correction Repoint

Run id: `20260511T074243+0800-codex-mainregimev2-external-correction-repoint`

## Decision

External material corrects the active Board A taxonomy back to `MainRegimeV2`.

Active Board A accounting is:

- Main price roots: `Bull`, `Bear`, `Sideways`, `Crisis`
- Separate direct-event class / overlay: `Manipulation`
- Residual: `UnknownOrMixed`

The `20260511T073701+0800-codex-main-regime-v3-reopened-source-refresh` run is superseded as taxonomy drift. It remains source-refresh provenance only.

## Demotion

The following accepted packets are downgraded to `sub_regime_evidence_only`:

- `TrendExpansion`
- `RangeConsolidation`
- `ExtremeStress`
- `ReversalBrewing`
- `SessionLiquidityCoreViable`
- `ThinLiquidity`

These packets may explain, guard, or enrich a parent regime after the parent root is independently identified. They do not complete `Bull`, `Bear`, `Sideways`, `Crisis`, or the separate `Manipulation` overlay.

## Manipulation Boundary

`Manipulation` cannot be accepted from OHLCV proxy subfactors such as thin-liquidity, session-liquidity, sweep-like range, or volume-ratio signatures.

Accepted `Manipulation` evidence must come from direct event, order-flow, order-lifecycle, social/event-confirmed, on-chain wash-trading, spoofing/layering, or equivalent direct-source evidence. Proxy-only lanes remain fail-closed.

## Gate

Gate result: `board_a_repointed_to_mainregimev2_external_correction_subtype_packets_demoted`.

The expanded full-universe/full-cycle objective remains blocked until independent source-backed MainRegimeV2 root labels cover ready yfinance/Kraken/local cells, and direct `Manipulation` coverage expands beyond the currently accepted baseline direct-event slice.

Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

