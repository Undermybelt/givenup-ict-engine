# TrendExpansion-Only Regime Transition Local Screen

- owner: codex
- created_at: 2026-05-31T23:59:26+0800
- last_updated_at: 2026-06-01T00:25:06+0800
- run_root: `/tmp/ict-engine-trend-expansion-only-regime-transition-20260531T235926+0800`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T235926+0800-codex-trend-expansion-only-regime-transition-local-screen.claim`
- compact_root: `support/docs/experiments/actionable-regime-confidence/runs/20260531T235926+0800-codex-trend-expansion-only-regime-transition-local-screen-v1`
- script: `support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_trend_expansion_only_regime_transition_local_screen_v1.py`
- test: `support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_trend_expansion_only_regime_transition_local_screen_v1.py`

## Contract

Only a closed-bar prediction that the market is becoming `TrendExpansion` may
open a trade. Every other regime is reference/veto evidence only:
`RangeCompression`, `Chop`, `StressVolatility`, `MeanReversion`, and unknown
states do not enter.

This slice is local screen evidence only. It does not run provider fetch,
IBKR historical, AutoQuant/Freqtrade exact-AQ, paper/live execution,
Pre-Bayes, BBN, path-ranker, execution-tree, or feedback lifecycle. Keep
`promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.

## No-Lookahead Shape

- Features are computed from closed bars.
- `3m` is derived causally from complete retained `1m` bars only:
  `causal_resample_1m_to_3m_closed_left_label_left`.
- MTF context is shifted before `merge_asof`.
- Entries are simulated at the next bar open after the signal bar.
- No realized future regime label is used as an entry condition.

## Data Scope

- source: retained TOMAC local cache under `/Users/thrill3r/Downloads/Tomac/factor_training/cache`
- symbols: `NQ,YM`
- target_timeframes: `1m,3m,5m,15m,30m,1h,4h`
- context_timeframes: `1m,3m,5m,15m,30m,1h,4h,1d`
- date_window: `2021-01-01` through `2025-12-31`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- retained_session_coverage: pass for NQ and YM, including non-RTH rows

## Source Intake

These sources were used as factor-tailoring material, not copied as code and
not treated as promotion evidence.

| source | kind | used as |
|---|---|---|
| Hamilton, `A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle`, `https://api.crossref.org/works/10.2307/1912559` | paper | Regime-transition framing. |
| `A Hidden Hierarchical Markov Model for Predicting S&P 500 Trend Reversals`, `https://arxiv.org/abs/2605.27848` | paper | One-bar execution-lag and state-transition guard inspiration. |
| `Trend Following Trading under a Regime Switching Model`, `https://epubs.siam.org/doi/10.1137/090770552` | paper | Regime-switching trend-following framing. |
| `Bayesian Online Changepoint Detection`, `https://arxiv.org/abs/0710.3742` | paper | Future online transition detector candidate; not fit in this local screen. |
| `Time Series Momentum`, `https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum` | paper | Futures trend-persistence source; local screen uses intraday proxies. |
| `Trends' Signal Strength and the Performance of CTAs`, `https://rpc.cfainstitute.org/research/financial-analysts-journal/2018/ip-v4-n1-3-trends-signal-strength` | paper summary | Adaptive trend-strength weighting idea across horizons. |
| `Intraday Opening Range Breakout Strategy`, `https://github.com/sam-bateman/trading-orb` | strategy code | ORB/relative-volume breakout tailoring source. |
| StockSharp `TTM Squeeze` Python strategy, `https://stocksharp.com/store/stocksharp.strategies.0452_ttm_squeeze.py/` | strategy code | Volatility compression/release source family. |
| StockSharp `Bollinger Squeeze` Python strategy, `https://stocksharp.com/store/stocksharp.strategies.0021_bollinger_squeeze.py/` | strategy code | Secondary squeeze-breakout source family. |
| QuantConnect `Average Directional Index`, `https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/supported-indicators/average-directional-index` | indicator | Trend-strength confirmation with +DI/-DI. |
| Interactive Brokers `Vertical Horizontal Filter`, `https://www.interactivebrokers.com/campus/glossary-terms/vertical-horizontal-filter/` | indicator | Trendiness filter to separate expansion/trend from range congestion. |
| QuantConnect `Choppiness Index`, `https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/supported-indicators/choppiness-index` | indicator | Non-trend veto/reference state filter. |

## Terminal Local-Screen Result

- command:
  `python3 support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_trend_expansion_only_regime_transition_local_screen_v1.py --root /tmp/ict-engine-trend-expansion-only-regime-transition-20260531T235926+0800 --compact-root support/docs/experiments/actionable-regime-confidence/runs/20260531T235926+0800-codex-trend-expansion-only-regime-transition-local-screen-v1 --symbols NQ,YM --target-timeframes 1m,3m,5m,15m,30m,1h,4h --start 2021-01-01 --end 2025-12-31 --compact`
- decision: `local_instrument_cost_candidate_needs_exact_aq_downstream`
- candidate_count: `112`
- instrument_cost_candidate_count: `11`
- gate1_survivor_count: `0`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

Top local instrument-cost candidates:

| symbol | timeframe | side/variant | trades | trades/session | instrument-cost net % | PF | note |
|---|---|---|---:|---:|---:|---:|---|
| NQ | 15m | long balanced | 1832 | 1.178135 | 32.851746 | 1.238785 | best local screen row; needs exact-AQ/downstream. |
| NQ | 15m | long clean | 1319 | 0.848232 | 30.002309 | 1.267284 | cleaner cadence, positive 5/5 years. |
| NQ | 30m | long clean | 818 | 0.526045 | 29.585669 | 1.307323 | lower density, positive 5/5 years. |
| NQ | 3m | long strict | 705 | 0.456606 | 14.609061 | 1.331949 | strict 3m causal-resample candidate. |
| YM | 3m | short balanced | 1634 | 1.211268 | 19.745733 | 1.183158 | YM expansion-state short candidate. |

Rejected-but-informative rows:

- NQ 1m long balanced: positive net but `10.271383` trades/session, rejected as too dense.
- NQ 3m long balanced: near upper density band but rejected on instrument-cost economics.
- NQ 1h short loose: positive net but `0.186495` trades/session, rejected as too sparse.

## Evidence Artifacts

- terminal metrics: `/tmp/ict-engine-trend-expansion-only-regime-transition-20260531T235926+0800/checks/terminal_metrics.json`
- terminal summary: `/tmp/ict-engine-trend-expansion-only-regime-transition-20260531T235926+0800/summaries/terminal_summary.json`
- terminal markdown: `/tmp/ict-engine-trend-expansion-only-regime-transition-20260531T235926+0800/summaries/terminal_decision_summary.md`
- screen rows: `/tmp/ict-engine-trend-expansion-only-regime-transition-20260531T235926+0800/summaries/screen_rows.csv`
- source map: `/tmp/ict-engine-trend-expansion-only-regime-transition-20260531T235926+0800/materials/source_evidence_map.json`

## No-Fill Exact-AQ Follow-Up

- run_root: `/tmp/ict-engine-trend-expansion-only-regime-transition-nofill-exact-aq-20260601T002119+0800`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260601T002119+0800-codex-trend-expansion-only-nq15m-nofill-exact-aq.claim`
- strategy: `TomacNq15mTrendExpansionOnlyRegimeTransitionLongBalancedStateShiftExactAqV1`
- command shape: `run_tomac_one.py --no-fill-missing ... NQ/USD 20210103-20251231`
- exact_aq_exit: `0`
- gross_trade_count: `1686`
- gross_total_profit_pct: `37.503981`
- gross_profit_factor: `1.185803`
- gross_sharpe: `1.130082`
- gross_max_drawdown_pct: `10.121661`
- decision: `exact_aq_nofill_run_completed_but_fillup_warning_persists`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

The no-fill command reproduced the positive gross exact-AQ result, but it did
not clear the parity blocker. Freqtrade still reported informative timeframe
fillup:

- `NQ/USD 1h`: before `29498`, after `43730`, fillup `48.25%`
- `NQ/USD 30m`: before `58981`, after `87459`, fillup `48.28%`

Terminal readback:

- metrics: `/tmp/ict-engine-trend-expansion-only-regime-transition-nofill-exact-aq-20260601T002119+0800/checks/terminal_metrics.json`
- summary: `/tmp/ict-engine-trend-expansion-only-regime-transition-nofill-exact-aq-20260601T002119+0800/summaries/terminal_summary.md`
- stdout: `/tmp/ict-engine-trend-expansion-only-regime-transition-nofill-exact-aq-20260601T002119+0800/checks/exact_aq_nofill_stdout.txt`
- stderr: `/tmp/ict-engine-trend-expansion-only-regime-transition-nofill-exact-aq-20260601T002119+0800/checks/exact_aq_nofill_stderr.txt`

## Next Gates

1. Re-run `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
   plus focused `ps` before any downstream/provider/paper launch.
2. Prefer the NQ 15m long balanced or NQ 30m long clean row for downstream
   because they keep density inside the target band.
3. Keep all practical flags false until provider/pre-Bayes/BBN/path-ranker/
   execution-tree/feedback/policy/same-tree closure passes.

## No-Fill Informative Parity Fix

- run_root: `/tmp/ict-engine-trend-expansion-only-regime-transition-nofill-parity-fix-20260601T004708+0800`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260601T004708+0800-codex-trend-expansion-only-nq15m-nofill-parity-fix.claim`
- strategy: `TomacNq15mTrendExpansionOnlyRegimeTransitionLongBalancedStateShiftExactAqV1`
- code fix: `support/scripts/auto_quant_external/run_tomac_one.py`
- regression test: `support/scripts/auto_quant_external/tests/test_run_tomac_one.py`
- exact_aq_exit: `0`
- fill_missing_requested: `false`
- fillup_warning_status: `cleared`
- freqtrade_missing_data_fillup_warning_count: `0`
- gross_trade_count: `1614`
- gross_total_profit_pct: `38.75214795211`
- gross_profit_factor: `1.2061369607240258`
- gross_sharpe: `1.1707333828726036`
- gross_max_drawdown_pct: `10.477114607596572`
- decision: `exact_aq_nofill_informative_parity_repaired_candidate_evidence_only`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

The repair patches `--no-fill-missing` across Freqtrade's main history loader
and informative-timeframe `DataProvider` loader. The new stderr/stdout logs have
no `Missing data fillup` lines for `NQ/USD 1h` or `NQ/USD 30m`. The economics
changed from the prior filled-informative run because the informative context now
keeps source gaps instead of calendar-filled rows.

Terminal readback:

- metrics: `/tmp/ict-engine-trend-expansion-only-regime-transition-nofill-parity-fix-20260601T004708+0800/checks/terminal_metrics.json`
- summary: `/tmp/ict-engine-trend-expansion-only-regime-transition-nofill-parity-fix-20260601T004708+0800/summaries/terminal_summary.md`
- stdout: `/tmp/ict-engine-trend-expansion-only-regime-transition-nofill-parity-fix-20260601T004708+0800/checks/exact_aq_nofill_stdout.txt`
- stderr: `/tmp/ict-engine-trend-expansion-only-regime-transition-nofill-parity-fix-20260601T004708+0800/checks/exact_aq_nofill_stderr.txt`
- trade export: `/tmp/ict-engine-trend-expansion-only-regime-transition-nofill-parity-fix-20260601T004708+0800/checks/aq_trades_TomacNq15mTrendExpansionOnlyRegimeTransitionLongBalancedStateShiftExactAqV1_nofill.json`
