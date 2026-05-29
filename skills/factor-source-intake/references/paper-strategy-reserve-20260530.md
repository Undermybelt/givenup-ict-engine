# Paper Strategy Reserve - 2026-05-30

This is source intake only. These notes create future Gate 1 candidates while
Board B claims or runtime owners block launches. They do not prove
`promotion_allowed=true` or `trade_usable=true`.

## Sources Checked

- Moskowitz, Ooi, Pedersen, `Time series momentum`, Journal of Financial
  Economics, 2012, DOI `10.1016/j.jfineco.2011.11.003`.
- Gao, Han, Li, Zhou, `Market intraday momentum`, Journal of Financial
  Economics, 2018, DOI `10.1016/j.jfineco.2018.05.009`.
- Heston, Korajczyk, Sadka, `Intraday Patterns in the Cross-section of Stock
  Returns`, Journal of Finance, 2010, DOI `10.1111/j.1540-6261.2010.01573.x`.
- Li, Shen, Wang, Zhang, `Does intraday time-series momentum exist in Chinese
  stock index futures market?`, Finance Research Letters, 2020, DOI
  `10.1016/j.frl.2019.09.007`.
- Chan, Chan, Karolyi, `Intraday Volatility in the Stock Index and Stock Index
  Futures Markets`, Review of Financial Studies, 1991, DOI
  `10.1093/rfs/4.4.657`.
- Hasbrouck, `Order Flow and the Probability of Informed Trading`, Empirical
  Market Microstructure, 2007, DOI `10.1093/oso/9780195301649.003.0006`.
- Ke and Lin, `An Improved Version of the Volume-Synchronized Probability of
  Informed Trading`, Critical Finance Review, 2017, DOI
  `10.1561/104.00000046`.
- arXiv `2605.04004`, `Structural Limits of OHLCV-Based Intraday Signals in MNQ
  Futures`, 2026. Use as a falsification warning, not as alpha evidence.
- arXiv `2605.17724`, `Sequential Structure in Intraday Futures Data: LSTM vs
  Gradient Boosting on MNQ`, 2026. Metadata was not verified in the 2026-05-30
  waiting window because arXiv returned HTTP 429; keep it as
  `unverified_info_only` and use only as a warning against single-instrument 5m
  OHLCV ML overfitting until refreshed.
- Gatev, Goetzmann, Rouwenhorst, `Pairs Trading: Performance of a
  Relative-Value Arbitrage Rule`, Review of Financial Studies, 2006, DOI
  `10.1093/rfs/hhj020`.
- Moreira and Muir, `Volatility-Managed Portfolios`, Journal of Finance, 2017,
  DOI `10.1111/jofi.12513`.
- Kim and Suh, `Overnight stock returns, intraday returns, and firm-specific
  investor sentiment`, North American Journal of Economics and Finance, 2021,
  DOI `10.1016/j.najef.2020.101287`.
- Barndorff-Nielsen and Shephard, `Power and Bipower Variation with Stochastic
  Volatility and Jumps`, Journal of Financial Econometrics, 2004, DOI
  `10.1093/jjfinec/nbh001`.
- Corsi, Pirino, Reno, `Threshold bipower variation and the impact of jumps on
  volatility forecasting`, Journal of Econometrics, 2010, DOI
  `10.1016/j.jeconom.2010.07.008`.
- Brock, Lakonishok, LeBaron, `Simple Technical Trading Rules and the
  Stochastic Properties of Stock Returns`, Journal of Finance, 1992, DOI
  `10.1111/j.1540-6261.1992.tb04681.x`.

## Metadata Verification

2026-05-30T00:17:34+0800 waiting-window check:

- Crossref confirmed every DOI listed above with matching title/year.
- arXiv confirmed `2605.04004` with title `Structural Limits of OHLCV-Based
  Intraday Signals in MNQ Futures: A Systematic Falsification Study`.
- arXiv lookup for `2605.17724` returned HTTP 429, so that entry remains
  `unverified_info_only` and must not drive candidate selection until refreshed.

## Candidate Packets

### nq-session-halfday-mim-v1

```text
candidate_id: nq-session-halfday-mim-v1
source: Gao/Han/Li/Zhou market intraday momentum plus Li/Shen/Wang/Zhang futures intraday TSMOM
source_type: paper
source_risk: info_only
why_now: Current NQ compound evidence shows longer-hold 1m roots can clear 5bps; MIM offers low-turnover session segmentation rather than churn.
regime_root: TrendExpansion
branch_path: TrendExpansion -> MarketIntradayMomentum -> RthFirstHalfContinuation -> HtfTrendAgreement -> nq_session_halfday_mim_v1
instrument/timeframe: NQ 1m origin; 5m/15m/30m/1h/4h/1d context
entry: After RTH first-half return exceeds threshold and HTF slope agrees, enter once in the afternoon continuation window.
confirmation: Prior-session volatility not extreme, current realized range above floor, no opposing 1h/4h trend.
exit/risk: Fixed RRR bracket or RTH/overnight timeout; at most one trade per session.
expected_holding_period: 90 minutes to multi-session if fixed-RRR exit persists.
expected_cadence: 0.2 to 1.0 trades/session.
data_required: retained NQ 1m plus MTF context; provider or paper parity later.
cost_model_required: NQ futures product-specific costs before practical admission; 5bps/side only as stress screen.
duplicate_check: Do not rerun existing opening-drive or dual-thrust roots unchanged; this is session-half segmentation with HTF agreement.
known_failure_modes: Sparse positives, afternoon reversal, first-half signal already exhausted, limit/market fill mismatch.
first_gate1_shape: Python prescreen on retained NQ 1m with shifted HTF features, train 2021-2023, OOS 2024-2025, positive all-years preferred.
next_command_when_clear: create factor-local claim/workdoc, then run local Python Gate 1 only if compact audit has no fresh owners.
status: python_prescreen_ready
promotion_allowed: false
trade_usable: false
```

### index-futures-tsmom-carryover-v1

```text
candidate_id: index-futures-tsmom-carryover-v1
source: Moskowitz/Ooi/Pedersen time series momentum plus futures intraday TSMOM evidence
source_type: paper
source_risk: info_only
why_now: Many failed TOMAC rows die from 1m turnover cost; multi-session carryover amortizes costs and can use 1m only for entry precision.
regime_root: TrendExpansion
branch_path: TrendExpansion -> TimeSeriesMomentum -> MultiSessionCarryover -> VolatilityScaledRrr -> index_futures_tsmom_carryover_v1
instrument/timeframe: NQ, ES, YM, XAU 1m origin; 1h/4h/1d trend context
entry: Daily/4h momentum agrees with 1h pullback reclaim; execute on 1m reclaim after volatility compression.
confirmation: Cross-index breadth or safe-haven divergence must not contradict the selected root.
exit/risk: Volatility-scaled stop, fixed RRR, and max hold 2-5 sessions.
expected_holding_period: Multi-session.
expected_cadence: 0.05 to 0.5 trades/session.
data_required: retained futures feathers across 1m/5m/15m/30m/1h/4h/1d; roll-adjusted provenance required.
cost_model_required: product-specific futures costs; stress screen at 5bps/side remains conservative but not final.
duplicate_check: Existing cross-asset risk-rotation negative packet means do not reuse that exact reentry logic.
known_failure_modes: Trend crowding, overnight gap risk, same-root duplicate of NQ compound, insufficient paper fill semantics.
first_gate1_shape: Start with NQ-only or ES/NQ pair-relative prescreen; compare to NQ compound so it adds novelty rather than rebrands the same branch.
next_command_when_clear: stage as new claim only after active compound provider/paper gates clear.
status: idea_only
promotion_allowed: false
trade_usable: false
```

### vpin-toxicity-filter-v1

```text
candidate_id: vpin-toxicity-filter-v1
source: Hasbrouck order-flow informed trading; VPIN improved formulation
source_type: paper
source_risk: info_only
why_now: Current OHLCV 1m work repeatedly hits cost and fill-quality limits; toxicity is better used as a filter for paper/live semantics than as standalone alpha.
regime_root: TransitionRisk
branch_path: TransitionRisk -> OrderFlowToxicity -> VpinVolumeBucketFilter -> ExecutionQualityGate -> vpin_toxicity_filter_v1
instrument/timeframe: NQ/MNQ futures; not OHLCV-only practical evidence
entry: No standalone entry. Gate existing NQ compound or MIM candidates away from high-toxicity buckets.
confirmation: Volume-bucket imbalance, spread/slippage proxy, and paper-fill rejects.
exit/risk: Reduce size, skip entries, or require wider RRR during toxic windows.
expected_holding_period: Filter only.
expected_cadence: Should reduce trades, not create new ones.
data_required: tick/order-flow/paper-fill or a validated proxy; 1m OHLCV alone is insufficient.
cost_model_required: broker/paper slippage and reject semantics, not just bps stress.
duplicate_check: No direct TOMAC duplicate; avoid pretending RVOL is VPIN.
known_failure_modes: Pseudo-VPIN from bars overfits; missing bid/ask makes toxicity unverified.
first_gate1_shape: Do not run Gate 1 until tick/paper source exists; add as provider/paper feature in lifecycle tests instead.
next_command_when_clear: search provider/paper artifacts for fill/slippage fields; otherwise keep blocked.
status: blocked_by_runtime
promotion_allowed: false
trade_usable: false
```

### tod-seasonality-recurrence-filter-v1

```text
candidate_id: tod-seasonality-recurrence-filter-v1
source: Heston/Korajczyk/Sadka intraday same-time recurrence; Chan/Chan/Karolyi intraday volatility seasonality
source_type: paper
source_risk: info_only
why_now: TOD families are already heavily mined; the useful reserve is a recurrence/stability filter for existing candidates, not another raw TOD alpha rerun.
regime_root: SessionRhythm
branch_path: SessionRhythm -> IntradayRecurrence -> VolatilitySeasonalityStability -> tod_seasonality_recurrence_filter_v1
instrument/timeframe: NQ/YM/XAU 1m origin with session slot features
entry: No standalone entry unless paired with a non-TOD signal. Filter entries to stable slot/volatility regimes.
confirmation: Slot performance must be stable across train/OOS and not concentrated in one year.
exit/risk: Slot-specific max hold and stop width, but no gate relaxation.
expected_holding_period: Same as parent branch.
expected_cadence: Should reduce churn and improve per-trade payoff.
data_required: retained 1m plus per-slot event history; no lookahead in slot statistics.
cost_model_required: same as parent branch.
duplicate_check: Balanced TOD and contrarian density repairs already exist; this must be a filter on a new parent or a same-root repair with explicit novelty.
known_failure_modes: Overfit slot mining, sparse slot hero years, stale same-time recurrence after regime shift.
first_gate1_shape: Apply only to a parent that already has positive 5bps economics but cadence/readiness blockers.
next_command_when_clear: do targeted duplicate search before any claim; likely best as child filter for NQ compound or MIM, not a new root.
status: idea_only
promotion_allowed: false
trade_usable: false
```

### index-relative-value-spread-reversion-v1

```text
candidate_id: index-relative-value-spread-reversion-v1
source: Gatev/Goetzmann/Rouwenhorst pairs trading relative-value rule
source_type: paper
source_risk: info_only
why_now: Pair-relative-value claims have appeared as active blockers; a clean reserve should separate mean-reversion spread logic from trend/breadth roots and avoid duplicate live lanes.
regime_root: RangeReversion
branch_path: RangeReversion -> CrossIndexRelativeValue -> ZscoreSpreadReversion -> VolatilityManagedExit -> index_relative_value_spread_reversion_v1
instrument/timeframe: ES/NQ/YM 1m origin with 15m/1h/4h/1d spread context
entry: Enter the lagging/leading leg only when ES-NQ or NQ-YM spread z-score reaches an extreme and higher-timeframe spread slope is mean-reverting.
confirmation: Volatility state is not stress-trending, broad index direction is not one-way momentum, and spread half-life is inside a bounded window.
exit/risk: Exit at spread mean, time stop, or volatility expansion stop; avoid pair execution until paper/fill semantics exist.
expected_holding_period: Intraday to multi-session.
expected_cadence: 0.05 to 0.5 trades/session.
data_required: synchronized retained futures feathers for ES/NQ/YM; paper/provider parity later for multi-leg execution.
cost_model_required: product-specific futures costs on both legs plus slippage; 5bps/side stress alone is not final.
duplicate_check: Recheck active pair-relative-value and cross-asset risk-rotation claims before opening; do not reuse terminalized risk-rotation logic.
known_failure_modes: Legging/slippage, one-way index trend, spread regime shift, double-cost drag.
first_gate1_shape: Python prescreen can test single-leg proxy first; multi-leg practical admission requires paper/provider execution semantics.
next_command_when_clear: only claim after current pair-relative or cross-asset claims terminalize.
status: idea_only
promotion_allowed: false
trade_usable: false
```

### volatility-managed-trend-size-gate-v1

```text
candidate_id: volatility-managed-trend-size-gate-v1
source: Moreira/Muir volatility-managed portfolios
source_type: paper
source_risk: info_only
why_now: NQ compound has positive economics but still needs practical lifecycle proof; volatility management may be a risk-control overlay rather than a new alpha root.
regime_root: TrendExpansion
branch_path: TrendExpansion -> VolatilityManagedExposure -> RealizedVolatilityThrottle -> volatility_managed_trend_size_gate_v1
instrument/timeframe: NQ/ES 1m origin with 1h/4h/1d realized volatility context
entry: No standalone entry. Scale, skip, or widen risk only when parent trend signal survives and realized volatility state is acceptable.
confirmation: Realized volatility below stress cap, drawdown cluster not active, and parent signal remains actionable.
exit/risk: Size throttle, risk-off skip, or reduced max hold under volatility expansion.
expected_holding_period: Same as parent branch.
expected_cadence: Should not increase trade count.
data_required: parent trades plus realized volatility context; lifecycle state to test risk controls.
cost_model_required: same as parent, plus slippage sensitivity during volatility spikes.
duplicate_check: Use as overlay on NQ compound or MIM only after parent ownership clears.
known_failure_modes: Improves drawdown while reducing already-sparse winners; accidental gate relaxation through post-hoc sizing.
first_gate1_shape: Re-score existing NQ compound trades with pre-entry realized-vol bins; do not mark practical without same-tree lifecycle.
next_command_when_clear: add as analysis packet under an owned parent lane, not a standalone AQ launch.
status: idea_only
promotion_allowed: false
trade_usable: false
```

### overnight-intraday-disagreement-filter-v1

```text
candidate_id: overnight-intraday-disagreement-filter-v1
source: Kim/Suh overnight versus intraday return decomposition and investor sentiment literature
source_type: paper
source_risk: info_only
why_now: Existing opening-drive and gap branches often fail cost or density; overnight/intraday disagreement can be a filter for when to accept or reject session continuation.
regime_root: TransitionRisk
branch_path: TransitionRisk -> OvernightIntradayDisagreement -> GapSentimentFilter -> overnight_intraday_disagreement_filter_v1
instrument/timeframe: NQ/MNQ 1m origin with prior close, overnight range, RTH open, and HTF context
entry: No standalone entry at first. Gate opening-drive, MIM, or NQ compound entries when overnight move and early RTH flow disagree.
confirmation: Prior overnight return, first 30-60 minute RTH return, realized range, and 1h/4h trend alignment.
exit/risk: Skip or shorten holds when overnight and intraday evidence conflict.
expected_holding_period: Same as parent branch.
expected_cadence: Filter should reduce trades and improve per-trade payoff.
data_required: continuous futures sessions with accurate ETH/RTH split; no lookahead in session labels.
cost_model_required: same as parent; beware gap slippage and session boundary fills.
duplicate_check: Avoid unchanged opening-drive reruns; use only as a parent filter with explicit novelty.
known_failure_modes: Session-boundary errors, overfit gap buckets, sparse OOS positives.
first_gate1_shape: Apply to parent trade CSVs first; if useful, open a same-root child repair claim.
next_command_when_clear: evaluate on NQ compound trade schedule or future MIM screen after active NQ compound lifecycle claims clear.
status: idea_only
promotion_allowed: false
trade_usable: false
```

### realized-jump-volatility-state-filter-v1

```text
candidate_id: realized-jump-volatility-state-filter-v1
source: Barndorff-Nielsen/Shephard bipower variation; Corsi/Pirino/Reno threshold bipower variation
source_type: paper
source_risk: info_only
why_now: 1m entries often fail in jumpy volatility states; this is a state filter for parent factors, not standalone alpha.
regime_root: TransitionRisk
branch_path: TransitionRisk -> RealizedJumpVolatility -> BipowerJumpStateFilter -> realized_jump_volatility_state_filter_v1
instrument/timeframe: NQ/ES 1m origin with 5m/15m/1h realized-vol context
entry: No standalone entry. Gate parent NQ compound, MIM, or carryover entries away from jump-dominated windows unless a post-jump reclaim is explicit.
confirmation: Realized variance versus bipower variation gap, threshold jump flag, volume/range confirmation, and unchanged 1h/4h parent trend.
exit/risk: Skip entries, shorten holds, or reduce size during jump-risk states; no gate relaxation.
expected_holding_period: Same as parent branch.
expected_cadence: Should reduce trades and improve per-trade payoff.
data_required: Clean intraday OHLCV with stable session boundaries; shifted features only. Tick data can improve it but is not required for an initial filter.
cost_model_required: Same as parent plus slippage stress during jump windows.
duplicate_check: Not a rerun of WPR/Hurst, Keltner, NR7, Donchian, OpeningRange, or opening-drive roots; use only as a parent filter.
known_failure_modes: Microstructure noise, session-boundary jumps, overfit jump thresholds, and volatility filters that erase all winners.
first_gate1_shape: Re-score parent trade schedules or run a local Python prescreen with pre-entry jump-state labels; no AQ/provider launch from this packet alone.
next_command_when_clear: Apply first to NQ compound or session-halfday MIM after active parent claims clear.
status: idea_only
promotion_allowed: false
trade_usable: false
```

### bootstrap-trading-range-falsification-filter-v1

```text
candidate_id: bootstrap-trading-range-falsification-filter-v1
source: Brock/Lakonishok/LeBaron technical trading rule bootstrap tests
source_type: paper
source_risk: info_only
why_now: Many breakout/range roots have already terminalized; use bootstrap falsification to decide whether a new breakout-like parent deserves runtime, not as another raw breakout rerun.
regime_root: ValidationMaturity
branch_path: ValidationMaturity -> BootstrapRuleFalsification -> TradingRangeBreakoutFilter -> bootstrap_trading_range_falsification_filter_v1
instrument/timeframe: Parent breakout or trend-continuation candidates on NQ/ES/YM 1m origin with MTF context
entry: No standalone entry. Require the parent rule's signed returns to survive block/bootstrap or shuffled-signal falsification before spending AQ/provider runtime.
confirmation: Split stability, positive 5bps economics before bootstrap, no concentration in one year/session slot, and exact-root novelty.
exit/risk: No direct exit; inherits parent risk and only blocks weak parents.
expected_holding_period: Same as parent branch.
expected_cadence: Should not increase trade count.
data_required: Parent signal rows or trade CSVs with no-lookahead returns; retained-real data only.
cost_model_required: Same as parent; bootstrap cannot override real transaction costs.
duplicate_check: Explicitly not a Donchian, NR7, opening-range, Keltner, or daily-breakout rerun; use as a pre-runtime statistical filter.
known_failure_modes: Data-snooping, overlapping-trade bootstrap errors, p-value theater, and treating statistical novelty as practical readiness.
first_gate1_shape: Offline check on existing candidate outputs; keep `promotion_allowed=false` and `trade_usable=false` even if the falsification check passes.
next_command_when_clear: Add as a lightweight same-root analysis step before claiming any new breakout-like runtime lane.
status: idea_only
promotion_allowed: false
trade_usable: false
```

## Practical Bias From The Sources

- Prefer lower-turnover, longer-hold structures over high-frequency 1m churn.
- Treat TOD and intraday volatility seasonality as filters unless the root is
  materially different from terminalized TOD branches.
- Treat order-flow toxicity as a paper/provider feature until tick or paper-fill
  data exists.
- Treat single-instrument OHLCV ML papers as warnings: they support stricter
  falsification and validation maturity, not a shortcut to promotion.
- Volatility-managed portfolio literature can inspire a child risk throttle for
  TSMOM or NQ compound-like trend roots, but not a fresh trade-usable claim.
  Futures OOS evidence is mixed, so any volatility throttle must pass train/OOS
  split checks without cadence inflation and keep practical flags false until
  downstream lifecycle closure exists.
- VPIN/order-flow toxicity literature is most useful for paper-fill quality,
  skip logic, and slippage/reject semantics. Do not synthesize VPIN from 1m
  OHLCV/RVOL and do not treat toxicity as standalone alpha without tick,
  quote, volume-bucket, or broker paper-fill fields.
- Treat relative value and volatility management as execution/risk-control
  hypotheses until multi-leg or parent-lane paper semantics exist.
- Treat realized-jump and bootstrap trading-rule papers as filters and
  falsification tools. They can improve candidate triage, but cannot replace
  Gate 1, cost, provider/paper, lifecycle, or same-tree closure evidence.
