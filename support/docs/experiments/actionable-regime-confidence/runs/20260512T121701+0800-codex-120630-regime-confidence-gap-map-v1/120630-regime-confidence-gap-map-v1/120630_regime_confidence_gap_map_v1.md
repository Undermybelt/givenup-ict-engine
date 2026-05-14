# 120630 Regime Confidence Gap Map v1

Run id: `20260512T121701+0800-codex-120630-regime-confidence-gap-map-v1`
Source downstream root: `20260512T120630+0800-codex-115700-six-provider-1h-downstream-chain-v1`

## Readback
- Active regime: `range` confidence `0.5250864595751618`; range probability `0.7476877176681956` leaves a `0.20231228233180432` gap to `0.95`.
- Pre-Bayes gate: `pass_neutralized`; filtered assignments `{'__policy_version': '318900600c5e8cf2', 'factor_alignment': 'mixed', 'factor_uncertainty': 'low', 'liquidity_context': 'neutral', 'market_regime': 'range', 'market_state_primary_regime': 'RangeConsolidation', 'market_state_secondary_regime': 'WideRange', 'multi_timeframe_resonance': 'aligned'}`.
- Directional gap: `0.003713368141665896` vs policy minimum `0.08`; shortfall `0.0762866318583341`.
- Soft evidence blockers: factor_alignment `{'bearish': 0.0, 'bullish': 0.0, 'mixed': 1.0}`, liquidity_context `{'favorable': 0.0, 'hostile': 0.0, 'neutral': 1.0}`, factor_uncertainty `{'high': 0.4187283851062096, 'low': 0.5812716148937904}`, multi_timeframe_resonance `{'aligned': 0.5812716148937904, 'dislocated': 0.0, 'mixed': 0.4187283851062096}`.
- CatBoost/runtime is available after feature support: raw scored mature `237/30`, production validation `237/30`, runtime `enabled_candidate_set_ready`.
- Execution remains `execution_blocked` / review `observe`, ready `False`, actionable `False`, readiness `0.32853919817900823`.

## Outcome Surface
- `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1`: trades `164`, wins `63`, losses `101`, win_rate `0.3841`.
- `Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1`: trades `73`, wins `18`, losses `55`, win_rate `0.2466`.

- `yfinance`: trades `21`, wins `10`, losses `11`, win_rate `0.4762`.
- `kraken_public`: trades `32`, wins `10`, losses `22`, win_rate `0.3125`.
- `binance_public`: trades `52`, wins `18`, losses `34`, win_rate `0.3462`.
- `bybit_public`: trades `51`, wins `18`, losses `33`, win_rate `0.3529`.
- `tvr_default_binance`: trades `37`, wins `10`, losses `27`, win_rate `0.2703`.
- `ibkr_paxos_long_midpoint`: trades `44`, wins `15`, losses `29`, win_rate `0.3409`.

## Decision
- Gate result: `120630_regime_confidence_gap_map_v1=bbn_regime_confidence_gap_identified_no_promotion`.
- The bottleneck is no longer provider/AQ or CatBoost runtime for this packet; it is calibrated regime confidence and execution admissibility.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next Evidence Needs
- hard or soft BBN node that separates trend/range/stress/transition beyond current OHLCV-derived range prior.
- provider/context features that turn factor_alignment away from mixed=1.0.
- directional evidence gap above 0.08 without relaxing policy thresholds.
- cross-provider and cross-period validation for any candidate regime lift.
- execution-tree candidate must become ready/actionable from evidence, not from assertion.
