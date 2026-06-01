# High-Sharpe Factor Harvest + Seed Library

Use when continuing ICT Engine heuristic-learning work that starts from papers/repos and turns factor ideas into hot-plug sidecar candidates.

## Pattern learned

Do not import large quant frameworks into runtime. Harvest papers/repos as source refs, then generate zero-config sidecar candidate specs that can later feed payoff, BBN, path-ranker, and execution-tree gates.

Preferred chain:

```text
paper/repo source
-> factor seed candidate JSON
-> optional personal fields kept optional
-> payoff report
-> purged OOS + DSR/PBO
-> regime slice
-> BBN evidence valuation
-> path-ranker target contribution
-> execution-tree recommendation delta
```

## Repo artifacts from this slice

Docs:
- `docs/plans/2026-05-09-high-sharpe-factor-harvest-and-infinite-iteration.md`
- `docs/plans/2026-05-09-high-sharpe-factor-harvest-handoff-todo.md`

Script:
- `scripts/research/factor_formula_seed_library.py`

Test:
- `scripts/research/tests/test_factor_formula_seed_library.py`

Generated smoke artifact:
- `/tmp/ict-hl/factor_seed_candidates.json`

## Candidate library contract

CLI:

```bash
python3 scripts/research/factor_formula_seed_library.py --output /tmp/ict-hl/factor_seed_candidates.json
python3 -m json.tool /tmp/ict-hl/factor_seed_candidates.json >/dev/null
```

Expected fields:

```text
schema_version=factor-formula-seed-library/v1
candidate_count=16
runtime_dependency_policy=sidecar_only_no_large_framework_import
missing_optional_policy=emit_missing_optional_and_continue
```

Each candidate includes:
- `candidate_id`
- `source_refs`
- `family`
- `markets`
- `timeframes`
- `required_fields`
- `optional_fields`
- `factor_expression`
- `chain_targets`
- `artifact_contract`

## Personal optional fields

These are intentionally optional, never required:

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

If absent, candidate generation and downstream sidecars must continue with `missing_optional` semantics.

## First 16 candidate IDs

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

## Verification

```bash
python3 -m unittest scripts.research.tests.test_factor_formula_seed_library
python3 scripts/research/factor_formula_seed_library.py --output /tmp/ict-hl/factor_seed_candidates.json
python3 -m json.tool /tmp/ict-hl/factor_seed_candidates.json >/dev/null
```

Expected: 3 tests pass; JSON parses; candidate_count is 16.

## Pitfalls

- Do not call a source "high Sharpe" based on paper or repo claim alone; promotion requires OOS LCB, DSR/PBO, tail risk, regime slice, BBN value, path-ranker contribution, and execution-tree delta.
- Do not copy GPL/AGPL/restrictive code into runtime. Use formulas/math/source refs and reimplement sidecars.
- Do not make QQQ/NQ/VRP user fields required. They are personal priority fields but must be hot-plug optional.
- Do not write generated `/tmp/ict-hl/...` artifacts into git; commit docs, scripts, tests, and stable specs only.
