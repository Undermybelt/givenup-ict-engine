# Board A Cross-Market Regime Condition Validation

This run adds explicit qualifying conditions for every Board A regime and validates each condition across QQQ, NQ, and Kraken XBTUSD contexts.

- Evidence packet: `docs/experiments/actionable-regime-confidence/runs/20260510T202359-hermes-cross-market-regime-validation/evidence_packet_cross_market_regime_validation.json`
- Condition matrix: `docs/experiments/actionable-regime-confidence/runs/20260510T202359-hermes-cross-market-regime-validation/cross-market/cross_market_regime_condition_matrix.json`
- Feature/label table: `docs/experiments/actionable-regime-confidence/runs/20260510T202359-hermes-cross-market-regime-validation/cross-market/cross_market_regime_features_and_labels.csv`
- Non-leaky simple threshold search: `docs/experiments/actionable-regime-confidence/runs/20260510T202359-hermes-cross-market-regime-validation/cross-market/simple_threshold_candidate_search.json`
- Full-chain context: `docs/experiments/actionable-regime-confidence/runs/20260510T200154-hermes-loop-full-chain-reaudit/evidence_packet_full_chain_reaudit.json`

The existing `SessionLiquidityCoreViable` 95% packet remains the only accepted Board A gate. The non-leaky threshold search found 0 additional accepted 95 candidates. This run does not claim 99% confidence or trade/execute readiness.
