# 125715 ETH Downstream CatBoost Runtime Readback v1

Run id: `20260512T131500+0800-codex-125715-eth-downstream-ingest-readback-v1`

## Scope

- Delta readback over the already-registered `131500` downstream ingest root for source packet `20260512T125715+0800-codex-six-provider-eth-same-root-aq-v1`.
- This artifact records the later CatBoost/path-ranker runtime closure in the same run root after the earlier Board A registration saw raw-scored mature rows as absent.
- It is isolated run evidence only. It does not mutate production BBN priors/CPDs, does not promote CatBoost/path-ranker or execution-tree state, and does not make a live-trade claim.

## Evidence

- Derived six-provider momentum rows: `162` total across yfinance `21`, Kraken `20`, Binance `34`, Bybit `34`, TVR `21`, and IBKR/AGGTRADES `32`.
- Isolated ingest applied `162/162` trades with `0` invalid and `162` feedback records inserted.
- All recorded command exits are `0` across `24` checks, including CatBoost train/apply/register/runtime readbacks.
- CatBoost/path-ranker runtime: status `enabled_candidate_set_ready`, ready `True`, active matches `2`, score model `catboost/external_model`.
- Validation: raw-scored mature `163/30`, production validation `162/30`, observation validation `162/30`.
- Calibration is `evaluated` with Brier `0.22618857455512223` and expected error `0.0018819632640756367`.

## Decision

- Gate: `same_root_eth_catboost_runtime_ready_but_execution_prebayes_fail_closed_no_promotion`.
- The downstream chain advanced materially beyond the earlier `131500` readback: CatBoost exists, runtime is candidate-set ready, and mature scored production validation is above the 30-row floor.
- Board A still remains fail-closed because Pre-Bayes has no policy/gate, the execution candidate is `ready=false` and `actionable=false`, review status is `observe`, and the posterior/readiness is nowhere near a calibrated `>=95%` regime packet.
- The selected branch remains `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1` with current posterior `0.345679012345679`, selected path probability `0.6632710958496916`, and raw CatBoost path score `0.2934390186466203`.
- Net Board A effect: accepted `>=95%` contexts added `0`; production likelihood mutation false; strict full objective false; trade usable false; promotion allowed false; and `update_goal=false`.

## Next

- Do not count this as new provider authority or as Board A acceptance. Count it only as a delta closure over `131500` showing CatBoost/path-ranker runtime can be made ready for the same-root ETH six-provider packet.
- The next repair target is Pre-Bayes/filter and execution-tree admission: produce a real policy/gate and non-observe execution readiness while preserving the same-root provider provenance, then require calibrated `>=95%` confidence before any promotion.
