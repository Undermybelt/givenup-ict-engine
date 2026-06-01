# High-window reclaim tree handoff

Session lesson from running a 30m IBKR cross-symbol high-window/quarter-high reclaim factor through Auto-Quant, cost stress, BBN, CatBoost, and execution-tree readback.

## Branch shape

Use regime-rooted metadata end-to-end:

`TrendExpansion -> BreakoutPersistence -> high_window_reclaim_30m -> ibkr_cross_symbol_high_window_reclaim_30m_v1`

Fields to preserve in agent material and downstream library metadata:

- `branch_path`
- `regime_profit_branch_path`
- `main_regime=TrendExpansion`
- `sub_regime=BreakoutPersistence`
- `sub_sub_regime_or_profit_factor=high_window_reclaim_30m`
- `profit_factor=ibkr_cross_symbol_high_window_reclaim_30m_v1`

## Candidate logic

OHLCV-only 30m proxy for 52-week/high-window continuation:

- retained real IBKR 30m candles, cross-symbol: NVDA, SMH, XLK, IWM, QQQ, SPY;
- `close > EMA50`, `EMA20 > EMA50`, `EMA50 >= EMA120 * 0.985`;
- reclaim near rolling high: `close > prior_high_40 * 0.998` and `close / prior_high_120 >= 0.985`;
- `RSI(14)` between 52 and 76;
- volume at least `0.65 * SMA20(volume)`;
- `ATR(14) / close < 0.035`;
- long-only, 30m, ROI/stop around 1.8%, trailing offset around 1.8%.

Name this as high-window/quarter-high proxy unless true 52-week daily context is available.

## Observed result

Auto-Quant Gate 1 on retained IBKR 30m cross-symbol data:

- SMH: 16 trades, win 81.25%, profit +10.10%, Sharpe 1.0623
- NVDA: 17 trades, win 64.71%, profit +9.31%, Sharpe 1.5006
- SPY: 28 trades, win 78.57%, profit +5.13%, Sharpe 1.4533
- QQQ: 27 trades, win 66.67%, profit +4.07%, Sharpe 0.8098
- XLK: 18 trades, win 66.67%, profit +2.17%, Sharpe 0.3626
- IWM: 21 trades, profit -2.34%

Vector cost stress stayed positive at the basket level through 10 bps/side:

- 0 bps/side: +37.65%, 53 trades, avg +71.03 bps/trade
- 2 bps/side: +35.53%, avg +67.03 bps/trade
- 5 bps/side: +32.35%, avg +61.03 bps/trade
- 10 bps/side: +27.05%, avg +51.03 bps/trade

## Downstream recipe

After AQ rank has at least two positive cross-symbol rows and cost stress survives:

1. Build a downstream `strategy_library_*.json` from positive AQ rank rows only.
2. Run `auto-quant-results-import` and `auto-quant-prior-init` into a fresh downstream state dir.
3. Run `analyze`, `pre-bayes-status --refresh`, `workflow-status --refresh`, and `export-structural-path-ranking-target`.
4. Train CatBoost on `structural_path_ranking_target_history.csv` when present; otherwise use current target.
5. Apply scores to current target.
6. Run `apply-structural-path-ranking-external-scores`, register trainer artifact, enable runtime.
7. Rerun `analyze`, `workflow-status --refresh`, and `policy-training-status`.
8. Read execution-tree fields, not just command exits.

## Gate language

Correct conclusion for this pattern when ranker is visible but validation is immature:

- `tree handoff complete`
- `best_current_candidate` if cross-symbol/cost evidence is strongest so far
- `candidate_only/not_live_ready` until validation rows mature

Do not call it live-ready if any of these remain short:

- `raw_scored_mature < 30`
- `production_validation < 30`
- `observation_validation < 30`
- `ranker_validation_ready=false`

Observed downstream state for this session:

- CatBoost trained/applied/registered/enabled successfully.
- Execution tree saw and used the CatBoost candidate-set score.
- `raw_path_score=0.820109`.
- Runtime: `enabled_candidate_set_ready`, `runtime_source=candidate_set`, `runtime_matches=3`.
- Execution tree remained `gate_status=observe`, `branch=transition_guardrail`, `execution_bias=guarded`.
- Validation was not ready: `raw_scored_mature=0/30`, `production_validation=0/30`, `observation_validation=0/30`.

## Guarded transition-risk overlay

A later refinement added a transition-hazard proxy guard to the same branch path:

`TrendExpansion -> BreakoutPersistence -> transition_guarded_high_window_reclaim_30m -> ibkr_cross_symbol_high_window_reclaim_guarded_30m_v1`

Observed guarded AQ result was 6/6 positive and fixed the IWM loss, but with lower expectancy than the unguarded primary:

- guarded 2 bps basket: +23.72%, 45 trades, avg +52.71 bps/trade
- unguarded 2 bps basket: +35.53%, 53 trades, avg +67.03 bps/trade

Use this pattern as a risk-filter / sizing overlay, not as automatic replacement. Policy shape:

- primary aggressive branch: unguarded `high_window_reclaim_30m` when transition hazard clears;
- guarded/smaller-size branch: `transition_guarded_high_window_reclaim_30m` when transition hazard is elevated but ranker/gates still allow observation.

Before superseding a matured primary factor with a guard, compare not just positivity count but basket expectancy, trade count, per-trade bps, and cost-stressed edge. A guard that repairs the weakest sibling can still reduce the portfolio edge.

## Pitfalls

- High-window proxy is not true 52-week-high proof unless daily 52-week context is fetched and joined.
- A single negative sibling such as IWM does not kill the factor if the branch is explicitly trend/breakout and broad tech/index siblings survive, but record the negative cell.
- Candidate-set CatBoost visibility is not promotion. It is execution-tree parity evidence only until mature validation rows exist.
- Do not rerun narrow NVDA-only parameter grinding if cross-symbol transfer is the real gate; move to cross-symbol and cost stress early.
- Do not promote a guarded variant merely because it makes every symbol positive; if it underperforms the matured unguarded branch after cost stress, keep it as overlay/sizing logic.
