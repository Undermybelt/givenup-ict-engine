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

### R26: BBN evidence value gate

- [ ] Admit factor evidence only if entropy/log-loss/contradiction lift improves.
- [ ] Persist `bbn_entropy_reduction` and `bbn_log_loss_delta`.

### R27: path-ranker / execution-tree closure

- [ ] Export target rows for promoted/probe candidates.
- [ ] Require path-ranker score contribution visible.
- [ ] Require `workflow-status --human` to explain practical recommendation delta.

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