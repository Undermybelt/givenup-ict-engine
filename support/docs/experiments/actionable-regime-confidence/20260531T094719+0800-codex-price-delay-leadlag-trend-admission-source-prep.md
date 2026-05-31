# Price Delay Lead-Lag Trend Admission Source Prep

- agent_name: `codex-price-delay-leadlag-trend-admission-source-prep-20260531T094719+0800`
- run_root: `/tmp/ict-engine-price-delay-leadlag-trend-admission-source-prep-20260531T094719+0800`
- workdoc: `/tmp/ict-engine-price-delay-leadlag-trend-admission-source-prep-20260531T094719+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T094719+0800-codex-price-delay-leadlag-trend-admission-source-prep.claim`
- terminal_metrics: `/tmp/ict-engine-price-delay-leadlag-trend-admission-source-prep-20260531T094719+0800/checks/terminal_metrics.json`
- factor_id: `tomac_idxfut_price_delay_leadlag_trend_admission_source_prep_v1`
- branch_path: `CrossMarketInformationDelay -> PriceDelayLeadLag -> TrendContinuationAdmission -> tomac_idxfut_price_delay_leadlag_trend_admission_source_prep_v1`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- status: `terminalized_source_prep_no_launch`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Current-State Guard

This packet was created only because current Board B runtime was not free.
Latest same-turn compact audit reported `status=needs_attention`,
`valid_active_claims=3`, and `live_factor_processes=1`; the live root was
`/tmp/ict-engine-multires-energy-trend-gate-aq-nq-1h-20260531T094202+0800`.

No provider fetch, IBKR historical, AutoQuant, Freqtrade/TOMAC runtime, local
screen/backtest, paper/sim/live execution, downstream lifecycle, feedback,
policy training, or same-tree practical closure was launched from this packet.

## Duplicate Search

Focused local searches found no exact `price delay`, Hou-Moskowitz delay, or
information-delay trend-admission lane in active `/tmp` claims, actionable
regime scripts, or factor-source references. Near families already present and
excluded: Hasbrouck information share, wavelet coherence lead-lag, transfer
entropy, dynamic correlation, rough path signatures, directional-change
overshoot, Kalman innovation, and generic lead-lag screens.

## Source Basis

- Hou and Moskowitz, "Market Frictions, Price Delay, and the Cross-Section of Expected Returns", Review of Financial Studies, 2005.
- Bibliographic source: `https://cir.nii.ac.jp/crid/1363107368856069504`
- Oxford PDF source listed by CiNii: `http://academic.oup.com/rfs/article-pdf/18/3/981/5344214/hhi023.pdf`

The candidate adapts the price-delay idea into an intraday futures admission
filter: compare target returns explained by current peer/market returns versus
current plus lagged peer/market returns. A high delay ratio with same-direction
lagged peer beta and shifted higher-timeframe trend context becomes an entry
admission filter, not a standalone alpha proof.

## Later Screen Contract

Only after a fresh compact audit and focused process guard clear:

- use retained ETH/full-session NQ target rows and ES/YM peer rows where cache
  coverage exists;
- use completed-bar shifted joins only;
- calculate `delay_ratio = 1 - restricted_r2 / full_r2`;
- require lagged peer beta alignment plus shifted `15m/1h/4h` target slope
  agreement;
- keep full-session density, year split, no-lookahead, and verified NQ
  instrument-cost gates separate from the source signal;
- keep `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`
  unless exact AQ/provider/downstream/accepted execution feedback and canonical
  same-tree practical closure pass later.

## Terminal Readback

- terminal_decision: `terminalized_source_prep_no_launch`
- local_screen_started: `false`
- provider_fetch_started: `false`
- ibkr_historical_started: `false`
- auto_quant_started: `false`
- tomac_freqtrade_started: `false`
- paper_sim_live_started: `false`
- downstream_lifecycle_started: `false`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`
