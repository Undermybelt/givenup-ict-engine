# Board A Prompt-To-Artifact Completion Audit

Loop ID: `20260510T212828+0800-codex-legacy-regime-contract-reissue`

## Objective

`docs/plans/2026-05-10-actionable-regime-confidence-todo.md` must show that every required regime has:

- its own qualifying condition;
- chronological train/calibration/test validation periods;
- validation across different instruments/products;
- validation across different market contexts;
- unchanged Board A 95% confidence gates;
- no trade/execution promotion.

## Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Same Board A markdown updated | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` current cursor says `board_state=accepted_95`, `accepted_gate=complete_under_current_contract`, and next action is Board B handoff as context/guardrails only | pass |
| Six required regimes covered | `evidence_packet_legacy_regime_contract_reissue.json` contains six `accepted_regime_packets`: `SessionLiquidityCoreViable`, `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, `ThinLiquidity` | pass |
| Each regime has qualifying condition | `jq` assertion required every packet to have a non-empty `qualifying_condition` | pass |
| Different instruments/products | `jq` assertion required every packet to have at least two `validation_instruments`; actual counts are 3-4 | pass |
| Different chronological periods | `jq` assertion required every packet to contain `validation_periods.train`, `validation_periods.calibration`, and `validation_periods.test` | pass |
| Different market contexts | `jq` assertion required every packet to have at least two `validation_market_contexts`; actual counts are 2-3 | pass |
| 95% gates unchanged | `jq` assertion required every packet to satisfy `precision_wilson_lcb >= 0.95`, `calibration_support >= 120`, `test_support >= 60`, `ece <= 0.05`, and `coverage >= 0.03` | pass |
| No leakage predictors | A11 script uses current/past daily OHLCV-derived features for masks; `future_`/`target_` columns are listed as blocked predictors and used only as labels | pass |
| No provider readiness overclaim | A11 packet says no new provider readiness was claimed; it reused NQ local daily and persisted yfinance QQQ/SPY/BTC-USD features | pass |
| No trade promotion | A11 decision keeps `trade_usable=false`; Board A next action says Board B handoff is context/guardrails only | pass |

## Verification Commands

```bash
python3 -m py_compile docs/experiments/actionable-regime-confidence/runs/20260510T212828-codex-legacy-regime-contract-reissue/legacy-reissue/legacy_regime_contract_reissue.py
jq empty docs/experiments/actionable-regime-confidence/runs/20260510T212828-codex-legacy-regime-contract-reissue/evidence_packet_legacy_regime_contract_reissue.json docs/experiments/actionable-regime-confidence/runs/20260510T212828-codex-legacy-regime-contract-reissue/legacy-reissue/legacy_regime_contract_reissue_report.json docs/experiments/actionable-regime-confidence/runs/20260510T211206-codex-sticky-hazard-contract-audit/completion-audit/board_a_sticky_hazard_contract_audit.json docs/experiments/actionable-regime-confidence/runs/20260510T205856-codex-sticky-hazard-per-regime/evidence_packet_sticky_hazard_cross_context.json
jq -e '<contract assertion>' docs/experiments/actionable-regime-confidence/runs/20260510T212828-codex-legacy-regime-contract-reissue/evidence_packet_legacy_regime_contract_reissue.json
rg -n '^\\| board_state \\| accepted_95 \\||complete_under_current_contract|accepted_95 field-complete 6/6|A11 legacy packet reissue completed|Hand the 6/6 field-complete' docs/plans/2026-05-10-actionable-regime-confidence-todo.md
git diff --check -- docs/plans/2026-05-10-actionable-regime-confidence-todo.md docs/experiments/actionable-regime-confidence/runs/20260510T211206-codex-sticky-hazard-contract-audit docs/experiments/actionable-regime-confidence/runs/20260510T212828-codex-legacy-regime-contract-reissue
```

All listed checks exited 0. The `py_compile` cache was removed after verification.

## Evidence Summary

| Regime | Wilson95 | Cal/Test | Instruments | Market Contexts | Artifact |
|---|---:|---|---:|---:|---|
| `SessionLiquidityCoreViable` | 0.998989 | 3496 / 3797 | 4 | 3 | `evidence_packet_legacy_regime_contract_reissue.json` |
| `TrendExpansion` | 0.953644 | 273 / 581 | 4 | 3 | `evidence_packet_legacy_regime_contract_reissue.json` |
| `RangeConsolidation` | 0.956760 | 503 / 266 | 4 | 3 | `evidence_packet_legacy_regime_contract_reissue.json` |
| `ExtremeStress` | 0.974129 | 445 / 215 | 3 | 2 | `evidence_packet_legacy_regime_contract_reissue.json` |
| `ReversalBrewing` | 0.991943 | 843 / 901 | 4 | 3 | `evidence_packet_legacy_regime_contract_reissue.json` |
| `ThinLiquidity` | 0.985604 | 584 / 263 | 4 | 3 | `evidence_packet_legacy_regime_contract_reissue.json` |

## Residual Boundaries

- Board A is accepted only for regime-confidence coverage.
- `trade_usable=false`; execution promotion is still blocked until Board B proves non-observe release and path-specific edge gates.
- A10 order-flow entropy remains fail-closed with `missing_required_inputs` until aligned tick/trade tape plus bid/ask or L2 data is attached.
