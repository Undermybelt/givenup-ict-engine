# High-Sharpe Factor Harvest + Payoff Gate Notes

Use when continuing `docs/plans/2026-05-09-high-sharpe-factor-harvest-handoff-todo.md` or any task that turns papers/repos into hot-plug ICT Engine factor candidates.

## Contract

Do not import large research frameworks into runtime. Use papers/repos as source references, then emit small sidecar artifacts under `/tmp/ict-hl/...`.

Default chain:

```text
paper/repo idea
-> factor seed candidate JSON
-> payoff-shape report
-> OOS/DSR/PBO/tail gate
-> regime slice check
-> BBN evidence value check
-> path-ranker contribution
-> execution-tree recommendation delta
-> promote/probe/reject
```

## R22 seed library slice

Files:

```text
scripts/research/factor_formula_seed_library.py
scripts/research/tests/test_factor_formula_seed_library.py
docs/plans/2026-05-09-high-sharpe-factor-harvest-handoff-todo.md
```

CLI:

```bash
python3 scripts/research/factor_formula_seed_library.py --output /tmp/ict-hl/factor_seed_candidates.json
python3 -m json.tool /tmp/ict-hl/factor_seed_candidates.json >/dev/null
python3 -m unittest scripts.research.tests.test_factor_formula_seed_library
```

Expected artifact:

```text
schema=factor-formula-seed-library/v1
candidate_count=16
missing_optional_policy=emit_missing_optional_and_continue
runtime_dependency_policy=sidecar_only_no_large_framework_import
```

Must preserve user-specific optional fields as optional hot-plug fields, never required:

```text
qqq_hv_level
qqq_hv_pct_rank_252
nq_vs_200d_pct
vix3m_level
vvix_over_vix
vrp
iv_rank
hv_rank
```

First 16 candidate IDs:

```text
tsmom_mtf_convexity_v1
trend_crash_guard_v1
carry_momentum_blend_v1
vrp_pressure_qqq_v1
iv_hv_spread_rank_v1
option_momentum_bucket_v1
ofi_book_pressure_v1
session_liquidity_quality_v1
alpha101_ts_rank_delta_v1
alpha101_corr_vol_price_v1
qlib_kline_shape_v1
qlib_slope_bundle_v1
residual_ou_reversion_v1
fx_hml_carry_v1
crypto_mom_liquidity_v1
low_beta_stability_v1
```

## R23 payoff gate expansion

Files:

```text
scripts/research/factor_payoff_shape_report.py
scripts/research/tests/test_factor_payoff_shape_report.py
docs/plans/2026-05-09-high-sharpe-factor-harvest-handoff-todo.md
```

Validation:

```bash
python3 -m unittest scripts.research.tests.test_factor_payoff_shape_report
python3 scripts/research/factor_payoff_shape_report.py \
  --candidate-id r23-tail-risk \
  --trades-jsonl /tmp/ict-hl/r23_trades.jsonl \
  --output-json /tmp/ict-hl/r23_payoff_report.json \
  --nb-trials 200
python3 -m json.tool /tmp/ict-hl/r23_payoff_report.json >/dev/null
```

Payoff report fields required by R23:

```text
sharpe
sortino
calmar
max_drawdown_R
cvar_95
tail_ratio
profit_factor
hit_rate
avg_rr
oos_sharpe_lcb
psr
dsr
pbo
effective_trials
effective_sample_size
failure_tags
promotion_gate
```

Failure tags added:

```text
low_dsr
high_pbo
tail_risk_hidden
```

Promotion gate should not promote unless:

```text
trade_count >= 80
oos_sharpe_lcb > 0
dsr >= 0.80
pbo <= 0.10
net_return_R > 0
no hard failure tags
```

## Source families harvested

- Time-series momentum / managed futures trend following
- Value and momentum everywhere
- Carry / roll yield
- Betting against beta / low beta
- Quality minus junk
- Momentum crash filter
- FX carry / FX momentum
- Variance risk premium / delta-hedged options
- Volatility spread / option momentum
- Crypto momentum / size / liquidity
- Order flow imbalance / book pressure
- Residual stat-arb / OU reversion

## Repo posture

- Qlib / Alpha101 / empyrical / quantstats: reference formulas and metrics; reimplement small pieces.
- mlfinlab: concept source only; visible license is restrictive, do not copy code.
- pysystemtrade / systematictradingexamples / backtesting.py: GPL/AGPL risk, do not import/copy.
- arbitragelab / limit-order-book: can inspire sidecars; keep attribution and avoid runtime coupling.

## Pitfalls

- High in-sample Sharpe is presumed leakage/selection bias/short-tail exposure until OOS + DSR/PBO + tail gates pass.
- Options/VRP factors must expose CVaR, tail loss, margin/gap risk, and stale quote/liquidity filters before promotion.
- Missing optional user fields must not fail zero-config flows; emit `missing_optional` or continue with low confidence.
- Keep commits scoped: only stage the files touched for the current slice; leave unrelated dirty files alone.
