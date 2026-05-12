# MainRegimeV2 Accepted Packet Demotion

Run id: `20260511T070654+0800-codex-mainregimev2-accepted-packet-demotion`

## Decision

Board A is now pointed at `MainRegimeV2` with four main price-regime roots:

- `Bull`
- `Bear`
- `Sideways`
- `Crisis`

`Manipulation` is outside that price-root axis. It is a separate direct-event class or overlay gate used for suppress/abstain/cooldown routing, not a price-regime root.

## Demoted Packets

The following previously accepted packets are downgraded to `sub_regime_evidence_only`:

| Packet | New Accounting Class | Allowed Use | Root Completion Allowed |
|---|---|---|---|
| `TrendExpansion` | `sub_regime_evidence_only` | child/provenance evidence under a separately accepted parent trend context | false |
| `RangeConsolidation` | `sub_regime_evidence_only` | child/provenance evidence under separately accepted `Sideways` | false |
| `ExtremeStress` | `sub_regime_evidence_only` | child/provenance evidence under separately accepted `Crisis` | false |
| `ReversalBrewing` | `sub_regime_evidence_only` | transition/guardrail evidence only | false |
| `SessionLiquidityCoreViable` | `sub_regime_evidence_only` | liquidity-context evidence only | false |
| `ThinLiquidity` | `sub_regime_evidence_only` | liquidity-risk evidence only | false |

These packets may explain, route, or guard a parent regime after the parent is separately proven. They cannot be counted as `Bull`, `Bear`, `Sideways`, `Crisis`, or `Manipulation` acceptance.

## Manipulation Boundary

`Manipulation` cannot be accepted from OHLCV/session/liquidity/sweep proxies. The accepted source must be direct event/order-flow/order-lifecycle/microstructure/on-chain/social-event evidence. Proxy-only lanes remain fail-closed or explicitly lower-confidence diagnostics.

## Current Accounting

| Class | Labels | Status |
|---|---|---|
| Main price roots | `Bull`, `Bear`, `Sideways`, `Crisis` | baseline parent-root evidence preserved; expanded full-universe/full-cycle goal still blocked |
| Separate direct-event class / overlay | `Manipulation` | direct-event overlay only; not counted as a price root |
| Sub-regime evidence | six demoted packets above | not counted as roots |
| Residual | `UnknownOrMixed` | abstain bucket only |

Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

