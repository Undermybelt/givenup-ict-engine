# Per-Regime Candidate Search

Loop id: `20260510T203010+0800-hermes-per-regime-candidate-search`

Objective: generate stronger per-regime candidates for `TrendExpansion`,
`RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, and `ThinLiquidity`,
then rerun cross-market chronological calibration without relaxing thresholds.

Inputs:
- Feature table:
  `docs/experiments/actionable-regime-confidence/runs/20260510T202359-hermes-cross-market-regime-validation/cross-market/cross_market_regime_features_and_labels.csv`
- Provider status:
  `provider/provider-status-agent.json`
- Auto-Quant status:
  `autoquant/auto-quant-status-agent.json`

Method:
- Candidate thresholds are derived from the train split only.
- `future_*` and `target_*` columns are blocked as predictors.
- Candidate forms include base regime conditions, one or two non-leaky threshold
  predicates, and base-condition conjunctions with those predicates.
- Calibration/test evidence is chronological and reported across QQQ IBKR 1h,
  QQQ yfinance 1h, NQ 15m, and Kraken PF_XBTUSD 1h contexts.

Result:
- Accepted 95 candidates: 0.
- Accepted 99 candidates: 0.
- Per-regime acceptance complete: false.
- Existing `SessionLiquidityCoreViable` remains the only accepted 95 packet.

Artifacts:
- `calibration/per_regime_candidate_search.py`
- `calibration/per_regime_candidate_search_report.json`
- `calibration/per_regime_candidate_rules.csv`
- `evidence_packet_per_regime_candidate_search.json`
- `checks/per_regime_candidate_assertions.out`
