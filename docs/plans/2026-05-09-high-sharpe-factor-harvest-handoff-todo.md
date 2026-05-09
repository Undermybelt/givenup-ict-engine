# High-Sharpe Factor Harvest Handoff TODO

Live board for paper/repo factor harvest and infinite iteration.

Goal: turn high-Sharpe factor references into zero-config, hot-plug sidecar candidates for `ict-engine`, with user-specific optional fields preserved but not required.

---

## Done

- [x] Routed through `ict-engine-runtime`.
- [x] Loaded heuristic learning harvest reference.
- [x] Checked current dirty worktree; unrelated dirty files preserved.
- [x] Reviewed existing heuristic learning docs:
  - `docs/plans/2026-05-09-heuristic-learning-module-harvest-report.md`
  - `docs/plans/2026-05-09-heuristic-learning-self-iteration-plan.md`
  - `docs/plans/2026-05-09-regime-classifier-r20-handoff-todo.md`
- [x] Searched papers and repos via arXiv/Semantic Scholar/GitHub API plus delegated research.
- [x] Created source registry and iteration contract:
  - `docs/plans/2026-05-09-high-sharpe-factor-harvest-and-infinite-iteration.md`

---

## Key harvest

Papers/families captured:

- Time-Series Momentum / managed futures trend following
- Value and Momentum Everywhere
- Carry / roll yield
- Betting Against Beta
- Quality Minus Junk
- Momentum Crash filter
- FX carry / FX momentum
- Variance Risk Premium / delta-hedged options
- Volatility spread / option momentum
- Crypto momentum/size/liquidity
- Order flow imbalance / book pressure
- Residual statistical arbitrage / OU reversion

Repos captured:

- `microsoft/qlib`
- `STHSF/alpha101`
- `quantopian/empyrical`
- `ranaroussi/quantstats`
- `pmorissette/bt`
- `hudson-and-thames/mlfinlab`
- `hudson-and-thames/arbitragelab`
- `robcarver17/pysystemtrade`
- `robcarver17/systematictradingexamples`
- `mansoor-mamnoon/limit-order-book`
- `kernc/backtesting.py`
- `quantrocket-llc/zipline`

---

## Consumer contract

- Zero-config default remains unchanged.
- Runtime must not import large research frameworks.
- Candidate factors are sidecar artifacts first.
- User-specific fields are optional and hot-plug:
  - `qqq_hv_level`
  - `qqq_hv_pct_rank_252`
  - `nq_vs_200d_pct`
  - `vix3m_level`
  - `vvix_over_vix`
  - `vrp`
  - `iv_rank`
  - `hv_rank`
- Missing optional fields must emit `missing_optional`, not fail.
- Promotion requires OOS/DSR/PBO/tail/regime/BBN/path-ranker/execution-tree closure.

---

## First implementation queue

### R22: factor formula seed library

- [x] Add `scripts/research/factor_formula_seed_library.py`.
- [x] Add tests: `scripts/research/tests/test_factor_formula_seed_library.py`.
- [x] Emit JSON candidate specs for first 16 candidates in the harvest doc.
- [x] Include `source_refs`, `family`, `required_fields`, `optional_fields`, `missing_optional_policy`.
- [x] Keep no third-party heavy dependency.
- [x] Validate JSON output.
- [x] Preserve user-specific fields as optional hot-plug fields, never required.

Observed artifact:

```text
/tmp/ict-hl/factor_seed_candidates.json
schema=factor-formula-seed-library/v1
candidate_count=16
first=tsmom_mtf_convexity_v1
vrp_optional_ok=True
```

### R23: payoff gate expansion

- [x] Ensure payoff report exposes:
  - Sharpe / Sortino / Calmar
  - max drawdown
  - CVaR / tail ratio
  - profit factor
  - hit rate
  - avg R/R
  - OOS Sharpe LCB
  - DSR / PBO
  - effective sample size
- [x] Add failure tags for `high_pbo`, `low_dsr`, `tail_risk_hidden`.
- [x] Add regression test: `test_report_exposes_r23_payoff_gate_fields_and_failure_tags`.
- [x] Validate CLI JSON output.

Observed artifact:

```text
/tmp/ict-hl/r23_payoff_report.json
sharpe=-2.5303377710824577
sortino=-2.5561399172110284
calmar=-0.48333333333333334
cvar_95=-3.0
tail_ratio=0.09999999999999999
profit_factor=0.532258064516129
avg_rr=0.152073732718894
oos_sharpe_lcb=-3.183671104415791
dsr=0.0
pbo=1.0
effective_sample_size=9
failure_tags=['thin_density', 'negative_edge', 'low_dsr', 'high_pbo', 'tail_risk_hidden']
promotion_gate=reject
```

### R24: QQQ/NQ VRP sidecar

- [x] Add optional auxiliary schema for VIX/VIX3M/VVIX/HV/IV.
- [x] Emit `vrp_pressure_qqq_v1`.
- [x] Keep zero-config fallback when fields missing.
- [x] Add sidecar script: `scripts/research/qqq_nq_vrp_sidecar.py`.
- [x] Add tests: `scripts/research/tests/test_qqq_nq_vrp_sidecar.py`.
- [x] Validate CLI JSON output.

Observed artifact:

```text
/tmp/ict-hl/r24_vrp_sidecar.json
schema=qqq-nq-vrp-sidecar/v1
candidate=vrp_pressure_qqq_v1
rows=3
missing_policy=emit_missing_optional_and_continue
zero_config_fallback=True
last_vrp=7.0
last_pressure=7.899047619047619
last_confidence=1.0
bbn_targets=dealer_pressure,factor_uncertainty,crash_risk
```

### R25: OFI/session sidecar

- [ ] Add optional L2/trade-flow schema.
- [ ] Emit `ofi_book_pressure_v1`.
- [ ] Add OHLCV proxy mode with low confidence if L2 missing.

Status: paused after user correction. Do not continue sidecar-only work before proving the current candidates through Auto-Quant -> filter/analyze -> BBN -> ranker -> execution tree.

### R26: BBN evidence value gate

- [x] Run managed Auto-Quant workspace, not just synthetic sidecar JSON.
- [x] Import a real Auto-Quant run manifest through `auto-quant-results-import`.
- [x] Apply strategy evidence through `auto-quant-prior-init` and verify `strategies_applied` is non-empty.
- [x] Admit factor evidence only if entropy/log-loss/contradiction lift improves.
- [x] Persist `bbn_entropy_reduction` and `bbn_log_loss_delta`.

Observed real closure slice:

```text
run_root=/tmp/ict-high-sharpe-real-20260509-234554
provider_status=market_data ready 5/7; yfinance+kraken_public ready; ibkr/tradingview_mcp pending
analyze_before=market_state TrendExpansion/BullTrendAcceleration; execution observe/transition_guardrail/guarded
Auto-Quant bootstrap=healthy pinned_ref=34ba6b6ee6aa69813a50a72158d4c089d97afb96
Auto-Quant prepare=data_ready true
Auto-Quant run log=/tmp/ict-high-sharpe-real-20260509-234554/logs/11_auto_quant_run.log
strategy_library=/tmp/ict-high-sharpe-real-20260509-234554/strategy_library_after_real_auto_quant_run_v3.json
import_artifact=auto_quant_strategy_library_NQ_20260509T155207.539452000Z
import_n_ok=2
prior_artifact=auto_quant_prior_init_NQ_20260509T155207.769438000Z
prior_initial=[0.999956,0.000022,0.000022]
prior_final=[0.6734197006771924,0.000000013279761567917304,0.326580286043046]
strategies_applied=MomentumMTFConfluence,RegimeAdaptiveBNB
MomentumMTFConfluence=854 trades, sharpe 0.3993, win_rate 34.7775, profit 53.24%, max_dd -23.1801%, pf 1.1682
RegimeAdaptiveBNB=115 trades, sharpe 0.1380, win_rate 69.5652, profit 16.41%, max_dd -4.6742%, pf 1.4262
```

Important: earlier manifest parse attempts v1/v2 produced `n_ok=0` and `strategies_applied=[]`; those are rejected evidence. v3 is the accepted run.

Observed live closure slice after user correction:

```text
run_root=/tmp/ict-high-sharpe-live-20260510-000946

provider matrix:
  yfinance provider-status: live_runtime 1/1 ready, market_data 1/1 ready
  yfinance actual fetch: QQQ 1h, 190 rows, success after one HTTP 429 retry
  kraken_public provider-status: market_data 1/1 ready
  kraken_public actual fetch: XBTUSD 1h, 721 rows, success
  ibkr provider-status: configured_runtime_unhealthy in default runtime because redis/ib_async missing, gateway reachable on port 4002
  ibkr actual fetch: QQQ 1h 30d, 480 rows via uv run --with redis --with ib_async --with pandas and gateway port 4002
  tradingview_mcp provider-status: install_required, missing ICT_ENGINE_TVREMIX_MCP_API_KEY
  tradingview_mcp actual fetch: attempted NASDAQ:QQQ, blocked by missing key; no TradingView data was used

Auto-Quant bootstrap:
  source=/Users/thrill3r/Auto-Quant
  managed_copy=/tmp/ict-high-sharpe-live-20260510-000946/auto-quant/auto-quant/.deps/auto-quant
  pinned_ref=34ba6b6ee6aa69813a50a72158d4c089d97afb96
  prepare=data_ready true
  run_exit=0
  run_log=/tmp/ict-high-sharpe-live-20260510-000946/logs/12_auto_quant_run.log
  manifest=/tmp/ict-high-sharpe-live-20260510-000946/strategy_library_from_live_run.json

Auto-Quant results:
  MomentumMTFConfluence full: 854 trades, sharpe 0.3993, win_rate 34.7775, profit 53.2400, max_dd -23.1801, pf 1.1682
  RegimeAdaptiveBNB full_5y: 115 trades, sharpe 0.1380, win_rate 69.5652, profit 16.4100, max_dd -4.6742, pf 1.4262
  RegimeAdaptiveBNB bull_2021: 16 trades, sharpe 0.3226
  RegimeAdaptiveBNB winter_2022: 25 trades, sharpe 0.2359
  RegimeAdaptiveBNB recovery_23_25: 72 trades, sharpe 0.0967

ict-engine filter/analyze:
  analyze_live_yfinance=TrendExpansion/BullTrendExhaustion; execution observe/transition_guardrail/guarded; gate pass_neutralized; quality 0.561
  analyze_demo_filter=TrendExpansion/BullTrendAcceleration; execution observe/transition_guardrail/guarded; gate pass_neutralized; quality 0.582
  persisted_paths=analyze_live htf/mtf/ltf/m1/m5/h4/spot JSONs under run_root/repo-state/NQ

BBN prior init:
  import_artifact=auto_quant_strategy_library_NQ_20260509T161635.677766000Z
  import_n_ok=2
  prior_artifact=auto_quant_prior_init_NQ_20260509T161711.472076000Z
  prior_initial=[0.999956,0.000022,0.000022]
  prior_final=[0.6734197006771924,0.000000013279761567917304,0.326580286043046]
  strategies_applied=MomentumMTFConfluence,RegimeAdaptiveBNB
  effects=854 trades -> 297 win/557 loss; 115 trades -> 80 win/35 loss
```

Observed R26 value-gate implementation slice:

```text
state_dir=/tmp/ict-r26-bbn-value-gate-20260510
source_manifest=/tmp/ict-high-sharpe-live-20260510-000946/strategy_library_from_live_run.json
source_log=/tmp/ict-high-sharpe-live-20260510-000946/logs/12_auto_quant_run.log
import_summary=/tmp/ict-r26-bbn-value-gate-20260510/import.json
import_n_ok=2
import_log_cross_check=matched 2, mismatches [], manifest_only [], log_only []
prior_summary=/tmp/ict-r26-bbn-value-gate-20260510/prior_init.json
prior_artifact=auto_quant_prior_init_NQ_20260509T171431.268234000Z
prior_state=/tmp/ict-r26-bbn-value-gate-20260510/auto-quant/NQ/auto_quant_prior_init_NQ_20260509T171431.268234000Z.json
prior_history=/tmp/ict-r26-bbn-value-gate-20260510/auto-quant/NQ/auto_quant_prior_init_history.json
evidence_value_gate_passed=true
bbn_entropy_reduction=0.018056766371967514
bbn_log_loss_delta=6.588649375209126
bbn_contradiction_lift=1.931483401354385
strategies_applied=MomentumMTFConfluence,RegimeAdaptiveBNB
strategies_skipped=[]
MomentumMTFConfluence gate=true entropy_reduction=0.0 log_loss_delta=6.348640598279494 contradiction_lift=1.292299795823666
RegimeAdaptiveBNB gate=true entropy_reduction=0.018056766371967514 log_loss_delta=0.24000877692963196 contradiction_lift=0.639183605530719
```

Implementation evidence:

```text
code=src/application/auto_quant/results/prior_init.rs
persistence=src/application/auto_quant/results/persistence.rs
summary_surface=src/application/auto_quant/command_entry.rs
test=cargo test --lib prior_init -- --nocapture
test_result=14 passed
test=cargo test --lib persistence -- --nocapture
test_result=46 passed
real_import=cargo run --quiet -- auto-quant-results-import --symbol NQ --state-dir /tmp/ict-r26-bbn-value-gate-20260510 --library /tmp/ict-high-sharpe-live-20260510-000946/strategy_library_from_live_run.json --log /tmp/ict-high-sharpe-live-20260510-000946/logs/12_auto_quant_run.log
real_prior_init=cargo run --quiet -- auto-quant-prior-init --symbol NQ --state-dir /tmp/ict-r26-bbn-value-gate-20260510
```

Boundary: this closes the BBN evidence-value admission/persistence gap for the current Auto-Quant strategy-library prior-init path. It does not promote the strategies to production; R27 still needs registered CatBoost runtime artifact support and mature scored rows.

### R27: path-ranker / execution-tree closure

- [x] Export target rows for promoted/probe candidates.
- [x] Apply external ranker scores and make contribution visible.
- [x] Enable registered ranker runtime artifact explicitly.
- [x] Require `workflow-status --human` to explain practical recommendation delta.
- [x] Train and apply actual CatBoost package against exported structural path target rows.
- [x] Feed CatBoost-produced raw scores back into ict-engine candidate-set runtime and verify `workflow-status --human` readback.
- [ ] Add a supported registered CatBoost runtime artifact path; current registry rejects binary `.cbm` and rejects the JSON companion as `weighted_feature_sum_v1`.
- [ ] Collect enough mature scored rows for production validation (`raw_scored_mature >= 30`).

Observed real closure slice:

```text
export_target=/tmp/ict-high-sharpe-real-20260509-234554/repo-state-v3/NQ/policy_training/structural_path_ranking_target.csv
rows=3
mature_rows=0
raw_scored_mature_before=0/30
trainer=/tmp/ict-high-sharpe-real-20260509-234554/path_ranker/trainer_artifact.json
catboost=not_installed
actual_model_family=weighted_feature_sum_v1
scores=/tmp/ict-high-sharpe-real-20260509-234554/path_scores.csv
rows_with_raw_path_score_after=3
runtime_selection=enabled_registered_model_ready
runtime_source=registered_model_artifact
runtime_matches=3
analyze_after=ranker registered_model_artifact/weighted_feature_sum_v1/not_ready
workflow_structural=trend_follow_through posterior=0.452 selected_prob=0.369
workflow_final_ranker=status using_registered_model_artifact source registered_model_artifact applied=3 artifact=3 lb=0.489 gate=observe
execution=observe/transition_guardrail/guarded
```

Boundary: this is a real command-level closure through Auto-Quant, filter/analyze, BBN, ranker registration, and execution tree. It is not a production high-confidence claim: CatBoost was unavailable, ranker used weighted fallback, and mature rows remain 0/30.

Observed live CatBoost / execution-tree slice after dependency install:

```text
run_root=/tmp/ict-high-sharpe-live-20260510-000946
export_target=/tmp/ict-high-sharpe-live-20260510-000946/repo-state/NQ/policy_training/structural_path_ranking_target.csv
target_rows=3
mature_rows=0
catboost_train=success
catboost_model=/tmp/ict-high-sharpe-live-20260510-000946/path_ranker_catboost/catboost_model.cbm
catboost_scores=/tmp/ict-high-sharpe-live-20260510-000946/path_scores_catboost.csv
features_used=structural_baseline_score fallback only
labels=pseudo-labels from structural_baseline_score because mature labels are unavailable
apply_scores=rows_with_raw_path_score 3
register_directory=failed Is a directory
register_cbm=failed stream did not contain valid UTF-8
register_json_companion_as_catboost=failed family mismatch source=weighted_feature_sum_v1
runtime_selection=enabled_candidate_set_ready
runtime_mode=candidate_set_only
runtime_source=candidate_set
runtime_matches=3
policy_status=raw_scored_mature 0/30; production_validation 0/30; observation_validation 0/30; calibration not_fitted
analyze_after=execution observe/transition_guardrail/guarded
workflow_ranker=status using_candidate_set_scores source candidate_set applied=3 artifact=0 candidate=3 raw=0.751 gate=n/a
```

Boundary correction: the 2026-05-10 slice did use the CatBoost dependency for training and scoring, but it did not produce a registered CatBoost runtime artifact. Runtime currently consumes candidate-set scores derived from CatBoost output.

### R28: Auto-Quant log cross-check parser hardening

- [x] Reproduce false drift from the live run where `SUMMARY` blocks reused strategy names and overwrote metric-bearing blocks.
- [x] Add RED regression for `SUMMARY` duplicate strategy names.
- [x] Add RED regression for same-strategy multi-timerange blocks where the manifest points at the full-window block.
- [x] Fix cross-check matching to choose the block that best matches the manifest status, timerange, and metrics.
- [x] Re-run parser tests.
- [x] Re-run live `auto-quant-results-import` against the same manifest and log in an isolated parser-check state dir.

Observed parser closure:

```text
original_import_log=/tmp/ict-high-sharpe-live-20260510-000946/logs/15_auto_quant_results_import.log
original_cross_check=matched 0, mismatches 4, false zero metrics from SUMMARY blocks
first_regression=SUMMARY duplicate selected log metrics 0 instead of full metrics
second_regression=RegimeAdaptiveBNB bull_2021 selected instead of manifest full_5y
test=cargo test --lib log_parser -- --nocapture
test_result=10 passed
live_recheck_state=/tmp/ict-high-sharpe-live-20260510-000946/repo-state-parser-check-2
live_recheck=matched 2, mismatches [], manifest_only [], log_only []
```

---

## Verification floor

```bash
git status --short
python3 scripts/research/factor_formula_seed_library.py --output /tmp/ict-hl/factor_seed_candidates.json
python3 -m json.tool /tmp/ict-hl/factor_seed_candidates.json >/dev/null
cargo check
./target/debug/ict-engine analyze --demo --symbol NQ --state-dir /tmp/ict-hl-smoke --human
./target/debug/ict-engine workflow-status --symbol NQ --state-dir /tmp/ict-hl-smoke --human
```

---

## Files in this slice

Stage only:

- `src/application/auto_quant/results/log_parser.rs`
- `docs/plans/2026-05-09-high-sharpe-factor-harvest-and-infinite-iteration.md`
- `docs/plans/2026-05-09-high-sharpe-factor-harvest-handoff-todo.md`

Unrelated dirty files remain outside this slice.
