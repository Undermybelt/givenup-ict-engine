# 134155 CatBoost Plus BBN Analyze Chain v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T134155+0800-codex-130814-plus-bbn-analyze-chain-v1`

Source roots:
- CatBoost/runtime source: `docs/experiments/actionable-regime-confidence/runs/20260512T130814+0800-codex-131500-eth-catboost-pathranker-closure-v1`
- Composite data source: `docs/experiments/actionable-regime-confidence/runs/20260512T131333+0800-codex-131500-eth-prebayes-bbn-consumption-v1/data`

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Result |
|---|---|---|
| Reuse the same ETH six-provider branch lineage | State was copied from `130814`; data was copied from `131333`; branch lineage remains `125715 -> 131500 -> 130814/131333` | pass as inherited provenance |
| Run analyze with BBN soft evidence over CatBoost-capable state | `checks/01_analyze_catboost_state_apply_bbn.exit=0` | pass |
| Read Pre-Bayes/BBN posterior | `checks/02_pre_bayes_status.exit=0`; policy `318900600c5e8cf2`; gate `observe_only`; soft evidence present | pass, but non-admitting |
| Re-read CatBoost/path-ranker after BBN/export | `checks/03_policy_training_status.exit=0`, `08_export_structural_path_ranking_target.exit=0`, `09_policy_training_status_after_export.exit=0` | pass, but runtime not matched |
| Re-read execution tree before and after export | `checks/04` through `07` and `10` through `12` all exited `0` | pass, fail-closed |
| Confirm validation floor vs runtime match | Validation floor remains satisfied: raw scored mature `163/30`, production validation `162/30`, observation validation `162/30`; runtime selection is `enabled_no_matching_scores` with `runtime_active_match_count=0` | fail_closed chain-contract mismatch |
| Confirm current execution admission | Current execution candidate is `ready=false`, `actionable=false`, `review_status=observe`, `execution_gate_status=execution_blocked`, readiness `0.3046756738194877` | fail_closed |

## Readback

- All twelve commands exited `0`.
- Pre-Bayes/BBN is present, but non-admitting: policy `318900600c5e8cf2`, gate `observe_only`, active canonical regime `range`, canonical confidence `0.367008438103555`, and soft evidence `{range: 0.34954935902525164, stress: 0.18438482894107935, transition: 0.2330329060168345, trend: 0.2330329060168345}`.
- CatBoost/path-ranker validation remains numerically repaired in history: calibration evaluated, trainer artifact `runtime_eligible`, raw scored mature `163/30`, production validation `162/30`, observation validation `162/30`, and outcome distribution `loss=106`, `win=56`.
- The current post-BBN candidate set is not matched by the runtime scores: runtime status `enabled_no_matching_scores`, runtime source `none`, score model family `unknown`, runtime matches `0`, current rows with raw path score `0`, calibrated path probability `0`, and path probability lower bound `0`.
- The current selected path is no longer the upstream provider-momentum branch; it is `range_mean_reversion` under `path:scenario:B2R_ETH_SIX_PROVIDER_MOMENTUM_125715:belief_regime_node:range:range_mean_reversion:primary`.
- Execution remains blocked: `ready=false`, `actionable=false`, `review_status=observe`, `candidate_status=execution_blocked`, `execution_gate_status=execution_blocked`, and readiness `0.3046756738194877`.

## Evidence Classification

- `evidence_class=chain_contract_negative_sample`
- Upstream branch path: `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1`
- Four branch fields: `main_regime=Bull`, `sub_regime=ProviderCryptoMomentum`, `sub_sub_regime_or_profit_factor=RsiMidlineExpansion`, `profit_factor=ProviderCryptoMomentumStateV1`
- Provider provenance: inherited from the already-counted `125715` six-provider ETH AQ root: IBKR/AGGTRADES, TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, and Bybit.
- Pre-Bayes/filter status: `observe_only`, policy `318900600c5e8cf2`
- BBN posterior: active `range`, confidence `0.367008438103555`
- CatBoost/path-ranker label/status: trainer artifact ready but current candidate set unmatched, `enabled_no_matching_scores`
- Execution-tree decision: `execution_blocked`, observe, not actionable
- Final outcome: `fail_closed`
- Failure reason: `post_bbn_candidate_set_no_matching_catboost_scores`
- Quality weight: `market_factor_learning=0`, `chain_contract_learning=1`

## Next

Do not treat the `106` loss / `56` win history distribution as a market/factor label for this current branch until the post-BBN candidate set receives matching CatBoost/path-ranker scores and calibrated lower-bound fields. The next repair target is candidate-set identity and score alignment after BBN, not another provider/AQ ingest.
