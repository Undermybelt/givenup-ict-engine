# 131333 ETH Six-Provider Pre-Bayes/BBN Consumption v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T131333+0800-codex-131500-eth-prebayes-bbn-consumption-v1`

Source roots:
- Provider/AQ authority root: `docs/experiments/actionable-regime-confidence/runs/20260512T125715+0800-codex-six-provider-eth-same-root-aq-v1`
- Downstream ingest/rooted state: `docs/experiments/actionable-regime-confidence/runs/20260512T131500+0800-codex-125715-eth-downstream-ingest-readback-v1`

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Result |
|---|---|---|
| Use AQ/provider authority, not local-only data | `data/eth_six_provider_composite_candles.provenance.json` points to the `125715` provider CSV dir and records six provider source files | pass as inherited six-provider provenance, not a new provider fetch |
| Include all required provider rows | Provider source rows: IBKR/AGGTRADES `784`, TVR/Binance `720`, yfinance `983`, Kraken `721`, Binance `985`, Bybit `985` | pass |
| Carry the same branch into ict-engine | Symbol `B2R_ETH_SIX_PROVIDER_MOMENTUM_125715`; branch path `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1` | pass |
| Run ict-engine analyze | `checks/01_analyze_six_provider_composite.exit=0` | pass |
| Run Pre-Bayes/filter readback | `checks/02_pre_bayes_status_refresh.exit=0`, `checks/03_pre_bayes_diff_refresh.exit=0` | pass, but gate remains non-admitting |
| Produce BBN/soft-evidence readback | `command-output/02_pre_bayes_status_refresh.out`, `state_prebayes_bbn_v1/.../bbn_network.json` | pass |
| Run CatBoost/path-ranker status | `checks/05_policy_training_status.exit=0` | pass; runtime remains CatBoost-backed candidate-set mode |
| Run execution-tree/workflow readback | `checks/06_workflow_structural_runtime.exit=0`, `07_workflow_structural_bundle.exit=0`, `08_workflow_execution_candidate.exit=0`, `09_workflow_full_refresh.exit=0` | pass, but execution remains blocked |
| Export structural path-ranking target | Original `10_export_structural_path_ranking_target.exit=2` due stale `--output-dir`; fixed `11_export_structural_path_ranking_target_fixed.exit=0` | pass after retry; original failure preserved |
| Reach calibrated 95% actionable confidence | Pre-Bayes canonical confidence `0.367008438103555`, selected path probability `0.3779949132087901`, no calibrated path prob/lower bound in current candidate rows | fail_closed |

## Readback

- Composite provider rows came from the already-counted `125715` six-provider AQ root: `ETH_1h_aggtrades.csv=784`, `tvr_binance_ethusdt_1h.csv=720`, `yfinance_eth_usd_1h.csv=983`, `kraken_ethusd_1h.csv=721`, `binance_ethusdt_1h.csv=985`, and `bybit_ethusdt_linear_1h.csv=985`.
- Composite candles produced `1017` `1h` rows, `249` `4h` rows, and `43` `1d` rows from `2026-03-31T20:01:00Z` to `2026-05-12T05:00:00Z`.
- Pre-Bayes/BBN consumed the branch and produced soft evidence, policy version `318900600c5e8cf2`, active canonical structural regime `range`, canonical confidence `0.367008438103555`, and gate `observe_only`.
- Soft evidence remained diffuse: `range=0.34954935902525164`, `stress=0.18438482894107935`, `transition=0.2330329060168345`, and `trend=0.2330329060168345`; multi-timeframe direction was `bullish` with alignment `0.999` and entry alignment `0.9026`.
- Entry-model policy training stayed not ready: `cisd_rb_long_v1` and `breaker_rb_long_v1` both had `matched_rows=0`.
- Structural path-ranker runtime stayed available and CatBoost-backed: `enabled_candidate_set_ready`, `score_model_family=catboost`, `score_source_kind=external_model`, `runtime_matches=2`, `raw_scored_mature=163/30`, `production_validation=162/30`, and `observation_validation=162/30`.
- The fixed structural target export produced rows `4`, candidate set size `3`, mature rows `1`, history rows `329`, history mature rows `325`, calibrated current rows `0`, lower-bound current rows `0`, and execution-gate current rows `0`.
- Execution candidate stayed non-admitting: `actionable=false`, `ready=false`, `review_status=observe`, `candidate_status=execution_blocked`, `execution_gate_status=execution_blocked`, `execution_readiness=0.3046756738194877`, selected path `range_mean_reversion`, and selected path probability `0.3779949132087901`.

## Gate

- `count_once:125715_six_provider_eth_aq_authority_packet`.
- `count_once:131500_125715_eth_downstream_ingest_readback_root`.
- `support_once:131333_125715_eth_six_provider_prebayes_bbn_consumption_v1`.
- `provider_authority:inherited_from_125715_six_provider_aq_root`.
- `local_composite_role:replay_provenance_sidecar_only`.
- `pass:all_six_provider_rows_present`.
- `pass:analyze_exit0`.
- `pass:pre_bayes_status_exit0`.
- `pass:bbn_soft_evidence_present`.
- `pass:catboost_path_ranker_runtime_present`.
- `pass:workflow_execution_candidate_exit0`.
- `pass:structural_path_export_fixed_exit0`.
- `fail_closed:pre_bayes_gate_observe_only`.
- `fail_closed:canonical_confidence_0.367008438103555_below_0.95`.
- `fail_closed:selected_path_probability_0.3779949132087901_below_0.95`.
- `fail_closed:current_candidate_calibrated_path_prob_absent`.
- `fail_closed:current_candidate_path_prob_lower_bound_absent`.
- `fail_closed:entry_model_matched_rows_0`.
- `fail_closed:execution_gate_status_execution_blocked`.
- `fail_closed:execution_ready_false`.
- `fail_closed:actionable_false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Do not rerun provider/AQ authority or the same CatBoost numeric-floor repair for this ETH root. The next useful transition is to make the current candidate rows acquire calibrated path probability/lower-bound evidence and non-observe Pre-Bayes/execution admission, without relaxing the six-provider AQ provenance lock or replacing AQ/provider provenance with local-only data.
