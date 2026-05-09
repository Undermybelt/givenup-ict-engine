# Heuristic Learning Execution TODO

> Master implementation board. Follow this before each new slice.

**Goal:** turn the module harvest plan into a zero-config, consumer-usable, hot-pluggable self-iteration chain for ICT Engine.

**Ground rules:**
- Use TDD for code slices.
- Sidecar first; touch Rust runtime only when sidecar output cannot satisfy consumers.
- Write only under explicit output dirs or docs/scripts/tests.
- Ignore unrelated formatting drift from other agents.
- Commit each coherent slice after tests pass.

---

## Completed

- [x] Slice 1: Triple Barrier + Meta-labeling
  - Commit: `89a0007 feat: add heuristic payoff labeling tools`
  - Files: `labeling_triple_barrier.py`, tests
- [x] Slice 2: Payoff-shape report
  - Commit: `89a0007 feat: add heuristic payoff labeling tools`
  - Files: `factor_payoff_shape_report.py`, tests
- [x] Slice 3: Zero-config payoff pipeline
  - Commit: `35f509c feat: add heuristic payoff pipeline`
  - Files: `heuristic_payoff_pipeline.py`, handoff, tests
- [x] Slice 4: PSR/DSR high-Sharpe guard
  - Commit: `5da0318 feat: add deflated sharpe payoff guard`
- [x] Slice 5: Payoff-gated path-ranker target + BBN gate
  - Commit: `781a97a feat: export payoff gated path ranker targets`
  - Rule: `probe/promote` enter path-ranker + BBN; `reject` enters failure memory only
- [x] Slice 6: Purged CV / Embargo / PBO guard
  - Commit: `ca6200b feat: add purged cv payoff guard`
  - Files: `purged_cv_backtest_guard.py`, handoff, tests

- [x] Slice 7: Regime confidence report
  - Commit: `5f2e79f feat: add regime confidence report`
  - Files: `regime_confidence_report.py`, handoff, tests
- [x] Slice 8: Transition evidence aggregator
  - Commit: pending this slice
  - Files: `transition_evidence_aggregator.py`, handoff, tests
  - Tests: `42 OK`

## Next Implementation Order

### Slice 9: BBN evidence value report

**Objective:** only add BBN evidence nodes/edges if they improve entropy/log-loss/contradiction lift.

**Create:**
- `scripts/research/bbn_evidence_value_report.py`
- tests + handoff

**Outputs:**
- `posterior_entropy_delta`
- `logloss_delta`
- `contradiction_lift`
- `accepted_edges`
- `rejected_edges`

### Slice 10: Risk-adjusted path utility

**Objective:** make path-ranker target model trade utility, not raw PnL.

**Modify:**
- `scripts/research/payoff_to_path_ranker_target.py`
- maybe `scripts/auto_quant_external/pandas_path_ranker_trainer.py`

**Add fields:**
- `risk_adjusted_path_utility`
- `mae_penalty`
- `time_penalty`
- `regime_confidence_bonus`
- `slippage_penalty`

### Slice 11: Formula seed library

**Objective:** give model a hot-pluggable factor seed pool.

**Create:**
- `scripts/research/factor_formula_library.py`
- tests + handoff

**Sources:**
- Qlib Alpha158 style formulas
- Alpha101 operator skeletons
- existing paper2code modules

### Slice 12: paper2code adapters

**Objective:** wire existing modules as sidecar reports before runtime changes.

**Targets:**
- rammstein OU reversion feasibility
- crowded_trades crowding pressure
- kyle stochastic liquidity / slippage realism
- red_queens_trap friction/mode collapse

---

## Current Slice Status

Active: Slice 7 `regime_confidence_report.py`.

- [ ] Write failing tests
- [ ] Implement minimal script
- [ ] Add handoff doc
- [ ] Run target tests
- [ ] Run full research tests
- [ ] Commit slice
