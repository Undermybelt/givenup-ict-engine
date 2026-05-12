# SidewaysConsolidation Legacy Reissue

Run id: `20260511T041213+0800-codex-sideways-consolidation-legacy-reissue`

## Decision

- Gate result: `accepted_sideways_consolidation_95`
- Active root accepted: `SidewaysConsolidation`
- Source packet: `docs/experiments/actionable-regime-confidence/runs/20260510T214429-codex-legacy-regime-contract-reissue/legacy-contract/legacy_regime_contract_reissue_report.json`
- Source regime id: `RangeConsolidation`
- Crosswalk: `RangeConsolidation` is reissued as the active MainRegimeV3SourceBacked root `SidewaysConsolidation` after the latest user correction that consolidation is a main regime class.
- Runtime code changed: `false`
- Thresholds relaxed: `false`
- Fresh calibration rerun: `false`
- Trade usable: `false`

## Evidence

Qualifying condition:

`catboost_isotonic_probability(RangeConsolidation_persists_next_15m) >= 0.9896907216494846`

| Split | Support | Success | Precision | Wilson95 LCB | Coverage | ECE |
|---|---:|---:|---:|---:|---:|---:|
| calibration | 467 | 463 | 0.991435 | 0.978186 | 0.094611 | 0.000000 |
| test | 313 | 309 | 0.987220 | 0.967607 | 0.063412 | 0.004488 |

Validation contexts:
- `NQ:AutoQuant_NQ_15m_cache:15m`
- `QQQ:yfinance_QQQ_1h:1h`
- `QQQ:IBKR_QQQ_1h:1h`

## Accounting

Accepted 95 roots after this reissue:
- `BullExpansion`
- `SidewaysConsolidation`
- `CrisisCrash`

Missing roots after this reissue:
- `BearExpansion`
- `Manipulation`

This packet does not claim strategy profitability or trade usability. It only closes the active regime-confidence root gate for `SidewaysConsolidation`.
