# Heuristic Learning Payoff + Regime Chain

Use when continuing ICT Engine self-iteration / high-Sharpe / regime-confidence work.

## User/project operating rules

- Multi-agent dirty worktree is expected. Ignore unrelated formatting drift and dirty Rust files from other agents.
- Commit only files touched for the current slice.
- Prefer sidecar scripts under `scripts/research/` before Rust runtime edits.
- Keep outputs explicit under caller-selected output dirs; do not write repo-root state.
- Keep JSON/JSONL/CSV artifacts compact and consumer-friendly.
- Use TDD: write failing `scripts/research/tests/test_*.py`, run RED, implement, run target tests, run full research tests, commit.

## Completed sidecar chain

Commits:
- `89a0007 feat: add heuristic payoff labeling tools`
- `35f509c feat: add heuristic payoff pipeline`
- `5da0318 feat: add deflated sharpe payoff guard`
- `781a97a feat: export payoff gated path ranker targets`
- `ca6200b feat: add purged cv payoff guard`
- `5f2e79f feat: add regime confidence report`
- `e048f0a feat: add transition evidence aggregator`
- `029800c feat: add bbn evidence value report`
- `8e3fec9 docs: record bbn evidence value slice`
- `b41f850 feat: add risk adjusted path utility`
- `d0f66cf docs: record risk adjusted utility slice`

Files / responsibilities:
- `scripts/research/labeling_triple_barrier.py`: Triple Barrier labels and meta-labeling.
- `scripts/research/factor_payoff_shape_report.py`: payoff shape, PSR/DSR, deflated Sharpe fields.
- `scripts/research/heuristic_payoff_pipeline.py`: zero-config pipeline; writes labels, payoff, purged CV guard, path-ranker target/BBN gate.
- `scripts/research/payoff_to_path_ranker_target.py`: `probe/promote` -> path-ranker target + BBN gate; `reject` -> failure memory only; now emits risk-adjusted target utility fields for ranker training.
- `scripts/research/purged_cv_backtest_guard.py`: Purged CV / embargo / PBO proxy / leakage flags.
- `scripts/research/regime_confidence_report.py`: operational `confidence_95` report.
- `scripts/research/transition_evidence_aggregator.py`: combines regime confidence + drift/changepoint rows into `transition_alert_95`, `transition_hazard`, `drift_flags`, `execution_tree_block_hint`.
- `scripts/research/bbn_evidence_value_report.py`: accepts/rejects BBN evidence edges by entropy delta, logloss delta, and contradiction lift.

## Default user-specific auxiliary fields

Carry these through hot-plug profiles and target rows unless user disables them:
- `qqq_hv_level`
- `nq_vs_200d_pct`
- `vix3m_level`
- `qqq_hv_pct_rank_252`
- `vvix_over_vix`

## Artifact gates

Payoff gate:
- `probe/promote`: allowed into path-ranker target and BBN/regime consumers.
- `reject`: write only `failure_memory.jsonl`; do not feed downstream.

Risk-adjusted path utility:
- target rows include `risk_adjusted_path_utility`, `mae_penalty`, `time_penalty`, `regime_confidence_bonus`, `slippage_penalty`.
- default formula: `realized_R - mae_penalty - time_penalty + regime_confidence_bonus - slippage_penalty`.
- current penalties: `mae_penalty=abs(min(0, mae))`, `time_penalty=max(0,time_to_hit)*0.01`, `regime_confidence_bonus=clamp(regime_confidence,0,1)*0.10`, `slippage_penalty=abs(slippage_R)`.
- keep raw `realized_R` for audit/fallback; train ranker on utility when present.

BBN evidence value:
- use `scripts/research/bbn_evidence_value_report.py` before adding new BBN edges/nodes.
- input JSONL fields: `edge_id`, `prior_prob`, `posterior_prob`, `outcome`, optional `contradiction`.
- negative `posterior_entropy_delta` and `logloss_delta` are improvements.
- accepted edges must pass entropy improvement, logloss improvement, and contradiction-lift thresholds; rejected edges should not be promoted into BBN.

Purged CV guard:
- emits `pbo`, `oos_sharpe_lcb`, `embargo_bars`, `leakage_flags`, `purged_cv_gate`.
- supports `purged_cv_enabled`, `embargo_bars`, `fold_count` in profile.

Regime confidence:
- zero-config defaults: `alpha=0.05`, `min_rolling_coverage=0.93`, `max_calibration_ece=0.05`, `max_transition_prob=0.2`, `max_flip_rate=0.2`.
- output fields: `confidence_95`, `conformal_set_size`, `rolling_coverage`, `calibration_ece`, `bootstrap_ci_width`, `transition_prob`, `flip_rate`, `regime_confidence_gate`.
- flip rate counts unstable A->B->A reversals, not one legitimate regime transition.

## Verification command

```bash
python3 -m unittest discover -s scripts/research/tests -p 'test_*.py'
```

Latest known result after Slice 10: `46 tests OK`.

## Master TODO

`docs/plans/2026-05-09-heuristic-learning-execution-todo.md`

Next planned slice:
- `scripts/research/factor_formula_library.py`
- sources: Qlib Alpha158 style formulas, Alpha101 operator skeletons, existing paper2code modules.

## Slice handoff docs

- Slice 8: `docs/plans/2026-05-09-transition-evidence-handoff-todo.md`
- Slice 9: `docs/plans/2026-05-09-bbn-evidence-value-handoff-todo.md`
- Slice 10: `docs/plans/2026-05-09-risk-adjusted-path-utility-handoff-todo.md`
