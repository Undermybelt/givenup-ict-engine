# Root vs Subtype Taxonomy Correction

Loop ID: `20260510T234852+0800-codex-root-vs-subtype-taxonomy-correction`

Decision: the recent names that look like `BullExpansion`, `BearExpansion`, `ConsolidationRange`, `CrisisStress`, `TransitionAccumulationDistribution`, `SessionLiquidityCoreViable`, `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, and `ThinLiquidity` are not accepted MainRegimeV2 root classes. They are child signatures or overlay/context packets unless a separate root-class target proves otherwise.

## MainRegimeV2 Root Contract

Accepted root labels are limited to:

- `Bull`
- `Bear`
- `Sideways`
- `Crisis`
- `UnknownOrMixed`

`Manipulation` is not accepted from OHLCV proxy evidence. It must be modeled either as:

- a fifth root class with direct tick/order-flow/L2/order-lifecycle or event/social evidence; or
- an overlay state attached to a root class.

Until those direct inputs exist, manipulation state is `missing_required_inputs` or `proxy_only_low_confidence`.

## Child Signature Mapping

| Child Signature / Probe Label | Parent Candidate | Current Use |
|---|---|---|
| `BullExpansion` | `Bull` child | directional expansion signature only |
| `BearExpansion` | `Bear` child | directional expansion signature only |
| `ConsolidationRange` | `Sideways` child | range/chop signature only |
| `CrisisStress` | `Crisis` child | stress signature only |
| `TransitionAccumulationDistribution` | `UnknownOrMixed` or transition overlay | transition signature only, not a release root |
| `SessionLiquidityCoreViable` | overlay/context | session/liquidity guardrail only |
| `TrendExpansion` | `Bull` or `Bear` child after sign split | unsigned trend signature only |
| `RangeConsolidation` | `Sideways` child | range signature only |
| `ExtremeStress` | `Crisis` child | stress signature only |
| `ReversalBrewing` | transition overlay | reversal setup only |
| `ThinLiquidity` | overlay/context | liquidity context only, not manipulation |

## Evidence Consequence

The corrected Board A status is `blocked` for MainRegimeV2 root coverage:

- accepted root classes: none
- accepted child/signature packets: retained as guardrail evidence only
- root acceptance gate: still requires each root class to pass the unchanged 95% calibrated gate on the root target itself
- no threshold relaxation
- no trade-usable promotion from child signatures

The `20260510T233637-root-regime-refinement` and `20260510T233911-main-regime-v2-advanced-root-features` artifacts remain useful feature-search provenance, but their `*Expansion`, `*Range`, `*Stress`, and transition labels are child-signature probes. They must not be counted as MainRegimeV2 root acceptance.
