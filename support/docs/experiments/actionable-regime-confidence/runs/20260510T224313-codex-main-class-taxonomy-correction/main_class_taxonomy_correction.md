# Board A Main-Class Taxonomy Correction

Loop ID: `20260510T224313+0800-codex-main-class-taxonomy-correction`

## Finding

The six current `accepted_95` packets are calibrated execution-native subtype/signature packets, not proof that six parent market-regime classes have been covered.

Root cause: Board A used the term `regime` for two layers at once:

- parent/main class: broad market state such as trend, range, stress, transition/reversal, liquidity, unknown;
- subtype/signature: a narrow qualifying condition with calibrated support, horizon, and allowed-action semantics.

The current packets are valid subtype evidence, but reporting them as main-class coverage overclaims the ontology.

## Current Subtype Evidence

| Accepted subtype/signature | Likely parent class | Wilson95 | Correction |
|---|---|---:|---|
| `SessionLiquidityCoreViable` | `LiquidityState` | 0.998989 | subtype guardrail, not a full liquidity parent class |
| `TrendExpansion` | `DirectionalTrendState` | 0.953644 | subtype of trend persistence/expansion |
| `RangeConsolidation` | `BalanceRangeState` | 0.956760 | subtype of low-stress range persistence |
| `ExtremeStress` | `StressVolatilityState` | 0.974129 | subtype of sticky/high-stress persistence |
| `ReversalBrewing` | `TransitionReversalState` | 0.991943 | subtype of trend-failure transition hazard |
| `ThinLiquidity` | `LiquidityState` | 0.985604 | subtype of thin-liquidity persistence |

## Corrected Gate

Board A main-class acceptance is not closed by the six subtype packets.

Main-class closure requires one of:

- a parent class label itself passes the 95% calibrated gate with explicit train/calibration/test validation; or
- every child subtype needed to cover that parent class is enumerated, calibrated, and assigned an explicit abstain/unknown residual.

Until then:

- `subtype_coverage_state = accepted_95_subtypes_6_of_6`;
- `main_class_coverage_state = active_taxonomy_gap`;
- `trade_usable = false`;
- Board B can consume the current packets only as context/guardrails.

## Board B Implication

The previous 6/6 Board B handoff remains usable only as subtype/signature guardrail context. It must not be cited as parent/main-regime acceptance.

Board B may run subtype-conditioned recipe research if it names the exact subtype/signature context. Parent/main-regime profitability claims remain blocked until Board A defines and calibrates the parent taxonomy or enumerates calibrated child coverage plus an explicit unknown/residual bucket.

## Next

Define a parent taxonomy first, then rerun Board A evidence against parent-class coverage instead of treating accepted subtype signatures as parent regimes.
