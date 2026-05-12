# 121701 Context Split Validator v1

Run id: `20260512T122546+0800-codex-121701-context-split-validator-v1`
Source gap map: `20260512T121701+0800-codex-120630-regime-confidence-gap-map-v1`
Source layered rows: `20260512T121542+0800-codex-120630-115700-layered-postchain-validator-v1`
Source feedback packet: `20260512T121607+0800-codex-120630-bbn-negative-feedback-packet-v1`

## Readback
- Rows: `237` from `6` providers, `1` symbol namespace, `1` AQ/source timeframe.
- Chronological splits: `4`; minimum split rows `59`.
- Active regime: `range` active confidence `0.5250864595751618`; range probability `0.7476877176681956`.
- Row-level legacy BBN posterior mean: `{'bear': 0.263604, 'bull': 0.229046, 'range': 0.50735}`.
- Execution readback: ready `False`, actionable `False`, review `observe`.

## Context Coverage
- Cross-provider available: `True` with classes `['broker_crypto_midpoint', 'crypto_exchange_public', 'public_aggregator', 'tradingview_relay']`.
- Cross-provider chronological min-row coverage: `False`; low-row cells `24`.
- Cross-branch chronological min-row coverage: `False`; low-row cells `4`.
- Cross-instrument available: `False`; symbols `['B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700']`.
- Cross-timeframe available: `False`; timeframes `['1h']`.
- Contexts with Wilson 95% lower bound above 0.5: `0`.

## Per-Regime Confidence
- `trend` probability `0.0`, gap_to_95 `0.95`, meets_95 `False`.
- `range` probability `0.747688`, gap_to_95 `0.202312`, meets_95 `False`.
- `stress` probability `0.177544`, gap_to_95 `0.772456`, meets_95 `False`.
- `transition` probability `0.074769`, gap_to_95 `0.875231`, meets_95 `False`.

## Decision
- Gate: `121701_context_split_validator_v1=context_split_validation_failed_no_promotion`.
- Blockers: `['no_regime_probability_meets_95', 'cross_instrument_validation_missing_single_symbol_namespace', 'cross_timeframe_validation_missing_single_aq_timeframe', 'provider_chronological_cells_below_min_context_rows', 'branch_chronological_cells_below_min_context_rows', 'no_context_has_positive_wilson_lower_bound_above_0_5', 'execution_not_ready', 'execution_not_actionable', 'execution_review_observe']`.
- This packet adds chronological/provider/context validation over the existing negative/neutral rows; it does not mutate BBN likelihoods or production priors.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next
- Need additional instrument and timeframe evidence before any cross-context regime claim.
- Need a real BBN evidence node that moves at least one regime probability to `>=0.95` without relaxing thresholds.
- Need execution to leave `observe` through evidence, not through assertion.
