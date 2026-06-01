# Heuristic Learning Module Harvest for ICT-Engine

Use when the user asks to turn heuristic-learning / self-iteration plans into concrete papers, repos, formulas, or modules to splice into `ict-engine`.

## Core pattern

Do not recommend one large framework. Split into sidecar modules that emit explicit artifacts into `/tmp/...` state dirs, then let Rust runtime consume only stable summaries.

Preferred chain:

```text
label outcomes -> score payoff shape -> calibrate regime -> value BBN evidence -> rank execution paths -> write chain verdict -> compress lessons
```

## P0 module shortlist

1. Triple Barrier + Meta-labeling
- Sources: mlfinlab, López de Prado AFML.
- Output: `barrier_hit`, `realized_R`, `mfe`, `mae`, `time_to_hit`, `meta_label`.
- Target: `scripts/research/labeling_triple_barrier.py`, path-ranker `target.csv`.
- Pitfall: must use purged CV/embargo for overlapping labels.

2. Purged CV + DSR/PBO
- Sources: mlfinlab, vectorbt, Deflated Sharpe Ratio, Probability of Backtest Overfitting.
- Output: `psr`, `dsr`, `pbo`, `effective_trials`, `effective_sample_size`.
- Gate: do not promote raw high Sharpe without OOS LCB + DSR/PBO.

3. Qlib Alpha158 + WorldQuant Alpha101
- Sources: Qlib `qlib/contrib/data/loader.py`, Alpha101 repos.
- Use as formula seeds for `factor_expression.json`, not as a runtime dependency.
- Key operators: rolling rank, ts_rank, correlation, covariance, delta, delay, decay_linear.

4. Regime stack
- Sources: `ruptures`, `hmmlearn`, `statsmodels` Markov switching, BOCD repos, `river` drift.
- Use `ruptures` as ex-post truth/benchmark only; realtime decisions must use forward filters.
- Output: posterior, transition probability, persistence, flip-rate, regime age.

5. 95% confidence calibration
- Sources: MAPIE conformal prediction, block bootstrap, scikit-learn calibration.
- Definition: calibrated singleton conformal set + acceptable rolling coverage/ECE + no active transition/drift + persistence/flip guard.
- Never equate raw HMM posterior > 0.95 with calibrated 95% regime confidence.

6. BBN evidence valuation
- Sources: pgmpy / pyAgrum.
- Add evidence only if entropy reduction, OOS log-loss improvement, or contradiction lift is proven.
- Keep node vocabulary small: market_regime, liquidity_context, factor_alignment, factor_uncertainty, multi_timeframe_resonance, crowding_pressure, dealer_pressure, session_quality, entry_quality, trade_outcome.

7. Path ranking
- Sources: CatBoost / LightGBM ranking.
- Target should be risk-adjusted path utility, not raw PnL:
  `realized_R - lambda1*MAE - lambda2*slippage - lambda3*time_in_trade + lambda4*regime_persistence`.
- Require mature rows and execution tree trace contribution before claiming closure.

8. Payoff-shape / diversity reports
- Sources: empyrical, pyfolio, Riskfolio-Lib, backtrader analyzers.
- Output: Sharpe, Sortino, Calmar, max drawdown, tail ratio, VaR/CVaR, hit rate, win/loss ratio, exposure, turnover, factor return correlation, incremental portfolio Sharpe/CVaR.

## Existing repo modules to wire first

- `paper2code/rammstein`: OU theta, overextension, wait-vs-fill/reversion feasibility.
- `paper2code/crowded_trades`: herding/crowding, `block_crowded`, crowding_pressure BBN evidence.
- `paper2code/kyle_stochastic_liquidity`: Kyle lambda, market depth, slippage/fill realism.
- `paper2code/red_queens_trap`: friction barrier, survivor bias, mode collapse, capital decay.

## Recommended first implementation slice

Start with:

```text
scripts/research/labeling_triple_barrier.py
scripts/research/factor_payoff_shape_report.py
```

Reason: this pins down whether a candidate has real trade value before spending effort on regime, BBN, or path ranking.

## License posture

Prefer reimplementing formulas from papers/math and using repos as references. Avoid copying GPL/AGPL code into runtime. Keep heavy/uncertain dependencies in `scripts/research/` sidecars.