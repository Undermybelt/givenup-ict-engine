# Board A Sticky-Hazard Contract Audit

Loop ID: `20260510T211206+0800-codex-sticky-hazard-contract-audit`

## Question

Can the newer sticky-hazard run close Board A as `accepted_95` under the current prompt-to-artifact contract?

## Audited Artifacts

- `docs/experiments/actionable-regime-confidence/runs/20260510T205856-codex-sticky-hazard-per-regime/evidence_packet_sticky_hazard_per_regime.json`
- `docs/experiments/actionable-regime-confidence/runs/20260510T205856-codex-sticky-hazard-per-regime/evidence_packet_sticky_hazard_cross_context.json`
- `docs/experiments/actionable-regime-confidence/runs/20260510T205717-hermes-a10-order-flow-input-audit/evidence_packet_a10_order_flow_input_audit.json`

## Result

Do not promote Board A to `accepted_95` yet.

The cross-context sticky-hazard packet is useful: it adds field-complete `accepted_95` packets for `TrendExpansion`, `ExtremeStress`, and `ReversalBrewing` without relaxing thresholds. Each has an explicit `qualifying_condition`, chronological train/calibration/test evidence, at least two instruments, and at least two market contexts.

The run still cannot close Board A because it carries three legacy accepted packets that do not expose the current required fields:

| Required Regime | Numeric Status | Field Contract | Missing Fields |
|---|---|---|---|
| `SessionLiquidityCoreViable` | accepted_95 legacy | fail | `qualifying_condition`, `validation_instruments`, `validation_periods`, `validation_market_contexts` |
| `RangeConsolidation` | accepted_95 legacy | fail | `qualifying_condition`, `validation_instruments`, `validation_periods`, `validation_market_contexts` |
| `ThinLiquidity` | accepted_95 legacy via `ThinLiquidityOffHoursPersistent` | fail | `qualifying_condition`, `validation_instruments`, `validation_periods`, `validation_market_contexts` |

## Field-Complete New Packets

| Regime | Rule | Wilson95 | Cal/Test | Contexts |
|---|---|---:|---|---|
| `TrendExpansion` | `trend_persistence_16 >= 1 AND stretch64 >= 0.05054785682` | 0.953644 | 273 / 581 | NQ, QQQ, SPY, BTC-USD; CME local + yfinance ETF/crypto |
| `ExtremeStress` | `stress_persistence_16 >= 1 AND jump_intensity_32 >= 0.125` | 0.974129 | 445 / 215 | NQ, QQQ, SPY; CME local + yfinance ETF |
| `ReversalBrewing` | `ma64_slope16 <= 0.00115583574 AND stretch64 <= 0.005836516932` | 0.991943 | 843 / 901 | NQ, QQQ, SPY, BTC-USD; CME local + yfinance ETF/crypto |

## Decision

Board state remains `active`.

Accepted gate is `incomplete_under_current_contract`: 3 of 6 required regimes are field-complete under the current contract, and 3 legacy accepted regimes must be reissued or enriched before Board A can hand off a complete 6/6 packet set to Board B.

## Next Action

Reissue or enrich `SessionLiquidityCoreViable`, `RangeConsolidation`, and `ThinLiquidity` accepted packets with explicit qualifying conditions plus `validation_instruments`, `validation_periods`, and `validation_market_contexts`. If any cannot be defended from real chronological evidence, mark that regime contract-incomplete instead of promoting Board A.

The A10 order-flow entropy lane remains fail-closed with `missing_required_inputs`; do not use OHLCV proxies for that lane.
