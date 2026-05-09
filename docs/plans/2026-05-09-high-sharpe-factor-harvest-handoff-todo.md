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
- [ ] Admit factor evidence only if entropy/log-loss/contradiction lift improves.
- [ ] Persist `bbn_entropy_reduction` and `bbn_log_loss_delta`.

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

### R27: path-ranker / execution-tree closure

- [x] Export target rows for promoted/probe candidates.
- [x] Apply external ranker scores and make contribution visible.
- [x] Enable registered ranker runtime artifact explicitly.
- [x] Require `workflow-status --human` to explain practical recommendation delta.
- [ ] Replace fallback ranker with actual CatBoost once dependency is installed and mature rows exist.
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

- `docs/plans/2026-05-09-high-sharpe-factor-harvest-and-infinite-iteration.md`
- `docs/plans/2026-05-09-high-sharpe-factor-harvest-handoff-todo.md`

Unrelated dirty files remain outside this slice.