# A8 Transition Sidecar Search

Loop id: `20260510T204325+0800-hermes-a8-transition-sidecar`

Objective: build non-leaky jump-model, persistence-penalty, and
transition-hazard sidecar features for the still-missing regimes:
`TrendExpansion`, `ExtremeStress`, and `ReversalBrewing`.

Inputs:
- Base feature table:
  `docs/experiments/actionable-regime-confidence/runs/20260510T202359-hermes-cross-market-regime-validation/cross-market/cross_market_regime_features_and_labels.csv`
- Prior accepted packet context:
  `docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/evidence_packet_regime_persistence_expansion.json`
- Provider and Auto-Quant status from:
  `docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/`

Method:
- Adds 20 current/past rolling sidecar features only.
- Blocks `future_*` and `target_*` columns as predictors.
- Selects candidate thresholds from train split only.
- Evaluates chronological calibration/test evidence across QQQ IBKR 1h,
  QQQ yfinance 1h, NQ 15m, and Kraken PF_XBTUSD 1h contexts.

Result:
- Accepted 95 candidates for missing regimes: 0.
- Accepted 99 candidates for missing regimes: 0.
- Existing accepted coverage remains 3/6:
  `SessionLiquidityCoreViable`, `RangeConsolidation`,
  `ThinLiquidityOffHoursPersistent`.

Artifacts:
- `sidecar/a8_transition_sidecar_search.py`
- `sidecar/a8_transition_sidecar_features.csv`
- `sidecar/a8_transition_sidecar_candidate_report.json`
- `sidecar/a8_transition_sidecar_candidate_rules.csv`
- `evidence_packet_a8_transition_sidecar.json`
- `checks/a8_transition_sidecar_assertions.out`
