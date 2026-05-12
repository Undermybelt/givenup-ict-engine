# 131717 Pre-Bayes/BBN Bundle Repair v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T131717+0800-codex-131500-prebayes-bbn-bundle-repair-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T131500+0800-codex-125715-eth-downstream-ingest-readback-v1/state_ingest`

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Result |
|---|---|---|
| Preserve the same ETH branch lineage | Symbol `B2R_ETH_SIX_PROVIDER_MOMENTUM_125715`; branch path `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1` | pass |
| Keep inherited six-provider provenance | Composite source rows: YF `983`, Kraken `721`, Binance `985`, Bybit `985`, TVR `720`, IBKR/PAXOS aggtrades `784` | pass as inherited provider authority |
| Build composite MTF data and bundle | `checks/00_build_composite_mtf_and_bundle.exit=0` | pass |
| Run analyze with regime bundle | Initial quoted-command attempt `01` failed `127`; direct compact-window attempt `02` failed because `1d` rows were `21`; full-window retry `03` exited `0` | pass after full-window retry |
| Confirm Pre-Bayes/BBN output | `checks/04_pre_bayes_status_refresh.exit=0`; policy `318900600c5e8cf2`; gate `observe_only`; soft evidence present | pass, but non-admitting |
| Confirm CatBoost/path-ranker runtime | `checks/05_policy_training_status.exit=0`, `09_enable_runtime_prefer_history.exit=0`, `10_policy_training_status_after_prefer_history.exit=0`; runtime `enabled_candidate_set_ready`, CatBoost external model, matches `2` | pass |
| Confirm execution-tree branch admission | `checks/06`, `07`, and `08` exited `0`; exact branch visible in closed-loop admission | fail_closed |
| Confirm promotion criteria | Pre-Bayes confidence `0.367008438103555`, selected path probability `0.48062669012284853`, calibrated path probability `null`, lower bound `null`, execution `blocked` | fail_closed |

## Readback

- Full-window analyze succeeded after two preserved failed attempts. The compact composite had only `21` `1d` rows, while the full-window copy produced enough data for analyze.
- Pre-Bayes/BBN is present but non-admitting: policy version `318900600c5e8cf2`, gate `observe_only`, active canonical structural regime `trend`, and canonical confidence `0.367008438103555`.
- BBN soft evidence from the regime bundle favors bull under `market_regime={bear:0.175,bull:0.65,range:0.175}`, but canonical structural probabilities remain diffuse: `trend=0.4806303686597211`, `transition=0.2330329060168345`, `stress=0.1843848289410794`, and `range=0.10195189638236508`.
- CatBoost/path-ranker runtime remains available in the branch-preserving candidate set: `enabled_candidate_set_ready`, reuse mode `prefer_history`, score model family `catboost`, score source `external_model`, runtime matches `2`, raw scored mature `163/30`, production validation `162/30`, and observation validation `162/30`.
- The execution-candidate readback keeps the exact provider-momentum branch visible with `path_label=Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1`, candidate set `structural-candidates:B2R_ETH_SIX_PROVIDER_MOMENTUM_125715:1f1e181a89fe1242`, selected path probability `0.48062669012284853`, and path-ranker raw score `0.663271`.
- Execution still fails closed: `ready=false`, `actionable=false`, `review_status=observe`, `candidate_status=execution_blocked`, `execution_gate_status=execution_blocked`, calibrated path probability `null`, and path probability lower bound `null`.

## Evidence Classification

- `evidence_class=chain_contract_negative_sample`
- Upstream/current branch path: `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1`
- Four branch fields: `main_regime=Bull`, `sub_regime=ProviderCryptoMomentum`, `sub_sub_regime_or_profit_factor=RsiMidlineExpansion`, `profit_factor=ProviderCryptoMomentumStateV1`
- Provider provenance: inherited from the already-counted `125715` six-provider ETH AQ root: IBKR/PAXOS AGGTRADES, TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, and Bybit.
- Pre-Bayes/filter status: `observe_only`, policy `318900600c5e8cf2`
- BBN posterior: active `trend`, confidence `0.367008438103555`, soft bull evidence present
- CatBoost/path-ranker label/status: branch raw score present, but calibrated probability and lower bound absent
- Execution-tree decision: `execution_blocked`, observe, not actionable
- Final outcome: `fail_closed`
- Failure reason: `branch_preserved_but_pre_bayes_confidence_and_path_lower_bound_below_admission`
- Quality weight: `market_factor_learning=0`, `chain_contract_learning=1`, `execution_readiness_learning=1`

## Next

Do not treat the branch as a market/factor negative or a promotion candidate. The useful next repair is calibrated current-row probability/lower-bound plus non-observe Pre-Bayes/execution admission for the same branch; provider/AQ authority and raw CatBoost score do not need to be reproved for this ETH root.
