# 133943 ETH Post-Export Workflow Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T133943+0800-codex-131714-post-export-workflow-readback-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T131714+0800-codex-131333-eth-prebayes-bbn-consumption-readback-v1`

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Result |
|---|---|---|
| Preserve inherited six-provider ETH authority | Source chain remains `125715 -> 131500 -> 131333 -> 131714`; no new local-only provider claim is made | pass as inherited provenance |
| Rerun post-export policy/workflow readbacks | `checks/01_policy_training_status_after_export.exit` through `05_pre_bayes_status_after_export.exit` are all `0` | pass |
| Confirm Pre-Bayes/BBN is no longer absent | `command-output/05_pre_bayes_status_after_export.out` has policy `318900600c5e8cf2`, gate `observe_only`, soft evidence present, and active canonical regime `range` | pass, but non-admitting |
| Confirm current BBN posterior quality | Canonical confidence is `0.367008438103555`; posterior probabilities are `range=0.34954935902525164`, `stress=0.18438482894107935`, `transition=0.2330329060168345`, `trend=0.2330329060168345` | fail_closed below 0.95 |
| Confirm CatBoost/path-ranker current-score alignment | `command-output/03_workflow_execution_candidate_after_export.out` reports runtime status `enabled_no_matching_scores`, raw score `null`, calibrated path probability `null`, and lower bound `null` | fail_closed chain-contract mismatch |
| Confirm execution-tree admission | Execution candidate is `ready=false`, `actionable=false`, `review_status=observe`, `candidate_status=execution_blocked`, and `execution_gate_status=execution_blocked` | fail_closed |
| Classify negative evidence | Upstream branch is provider-provenanced, but post-BBN candidate-set scoring is not aligned to the current execution candidate | `chain_contract_negative_sample` |

## Readback

- All post-export readback commands exited `0`: policy-training status, structural bundle workflow, execution-candidate workflow, full workflow refresh, and Pre-Bayes refresh.
- Pre-Bayes/BBN did produce a current policy and posterior. The latest policy version is `318900600c5e8cf2`, latest gate is `observe_only`, and soft evidence is present.
- BBN posterior is diffuse and non-admitting: active canonical regime `range`, canonical confidence `0.367008438103555`, and market-regime soft evidence `{range: 0.34954935902525164, stress: 0.18438482894107935, transition: 0.2330329060168345, trend: 0.2330329060168345}`.
- The current execution path after BBN is `range_mean_reversion` with candidate set `structural-candidates:B2R_ETH_SIX_PROVIDER_MOMENTUM_125715:b7d77aa214e58a0a`, candidate set size `3`, and selected path probability `0.33333333333333337`.
- CatBoost/path-ranker runtime is enabled but not matched to the current candidate set: runtime status `enabled_no_matching_scores`, `candidate_set_match_count=0`, `artifact_match_count=0`, and `history_match_count=0`.
- Current execution candidate has no usable score fields: `path_ranker_raw_score=null`, `path_ranker_calibrated_path_prob=null`, and `path_ranker_path_prob_lower_bound=null`.
- Execution remains blocked: `ready=false`, `actionable=false`, `review_status=observe`, `candidate_status=execution_blocked`, `execution_gate_status=execution_blocked`, and readiness `0.3046756738194877`.

## Evidence Classification

- `evidence_class=chain_contract_negative_sample`
- Upstream branch path: `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1`
- Four branch fields: `main_regime=Bull`, `sub_regime=ProviderCryptoMomentum`, `sub_sub_regime_or_profit_factor=RsiMidlineExpansion`, `profit_factor=ProviderCryptoMomentumStateV1`
- Provider provenance: inherited from the already-counted `125715` six-provider ETH AQ root: IBKR/AGGTRADES, TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, and Bybit.
- Pre-Bayes/filter status: `observe_only`, policy `318900600c5e8cf2`
- BBN posterior: `range` active, confidence `0.367008438103555`
- CatBoost/path-ranker label/status: current candidate score mismatch, `enabled_no_matching_scores`, score fields `null`
- Execution-tree decision: `execution_blocked`, observe, not actionable
- Final outcome: `fail_closed`
- Failure reason: `post_bbn_candidate_set_no_matching_catboost_scores`
- Quality weight: `market_factor_learning=0`, `chain_contract_learning=1`

## Next

Do not rerun the unfinished `131717` bundle just to repeat Pre-Bayes/BBN presence. The next useful transition is to align CatBoost/path-ranker scores with the post-BBN candidate set and then regenerate calibrated path probability, lower bound, and execution admission on the same inherited six-provider branch.
