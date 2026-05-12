# HGB Validation Axis Audit After 051844 v1

Run id: `20260512T053856-codex-hgb-validation-axis-audit-after-051844-v1`

Gate result: `hgb_validation_axis_audit_after_051844_v1=price_roots_95_daily_cross_market_cross_period_only_timeframe_source_control_downstream_blocked`

Board hash before artifact: `e87a03c13c35a9ced1ac131464ac7f5bcf8f6568bd54a791dcaf8f6ab4b1d8d7`

## Objective Restatement

The objective is complete only if every active `MainRegimeV2` root has `>=95%` calibrated confidence, validates on other markets and other cycles/timeframes, and then the real ict-engine chain is operated in order after a valid source/control unlock: provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution tree.

## Evidence Readback

The `051844` HGB packet is a real diagnostic improvement. It scored `248440` rows and accepted all four active price roots:

| Label | Min support | Min Wilson95 LCB |
|---|---:|---:|
| `Bear` | `177` | `0.9787578642` |
| `Bull` | `618` | `0.9908918883` |
| `Crisis` | `547` | `0.9930261988` |
| `Sideways` | `534` | `0.990666799` |

The split structure is real but daily-only:

| Axis | Evidence | Status |
|---|---|---|
| Cross-market | `heldout_market=26236`; market families `us_single_stock`, `us_index`, `india_equity_index`. | `satisfied_daily_diagnostic_not_promotion` |
| Cross-period | `heldout_time=45384`, `test=27844`; source rows span `2000-01-03` to `2026-03-20`. | `satisfied_daily_diagnostic_not_promotion` |
| Cross-timeframe / cycle | `timeframe=1d` for all `248440` rows. | `blocked` |
| Source/control validity | `051844` has `source_control_evidence_acquired=false`; R6/R3/R5 target roots remain absent. | `blocked` |
| Downstream chain | `051844` has `canonical_merge=false` and `downstream_promotion_rerun=false`. | `blocked` |

## Decision

The HGB packet satisfies the current price-root confidence screen diagnostically across heldout market and heldout time splits, but it does not satisfy the user's full "other cycles/timeframes" requirement. It is daily source-label equivalence evidence only.

Board A is not complete. The required target roots remain absent, source/control evidence is not acquired, canonical merge has not run, downstream promotion has not rerun, trade usable remains false, and `update_goal=false`.

## Next

Do not promote from the daily HGB screen alone. Acquire or approve a required source/control target root, especially native sub-hour or genuinely source-owned cross-timeframe `MainRegimeV2` rows, then rerun direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.
