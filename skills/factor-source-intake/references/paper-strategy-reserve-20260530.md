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
- arXiv `2605.20142`, Jia and Lee, `Mining Financial Data using Mixtures of
  Mirrored Weibull Distributions`, 2026. Use as a prior-return left-tail VaR
  gate or skip sidecar for already-defined entries, not standalone alpha.
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
- Brunnermeier and Pedersen, `Market Liquidity and Funding Liquidity`, Review
  of Financial Studies, 2009, DOI `10.1093/rfs/hhn098`.
- Chordia, Roll, Subrahmanyam, `Commonality in liquidity`, Journal of
  Financial Economics, 2000, DOI `10.1016/S0304-405X(99)00057-4`.
- Schreiber, `Measuring Information Transfer`, Physical Review Letters, 2000,
  DOI `10.1103/PhysRevLett.85.461`.
- Marschinski and Kantz, `Analysing the information flow between financial time
  series`, European Physical Journal B, 2002, DOI
  `10.1140/epjb/e2002-00379-2`.
- Dimpfl and Peter, `Using transfer entropy to measure information flows between
  financial markets`, Studies in Nonlinear Dynamics and Econometrics, 2013,
  DOI `10.1515/snde-2012-0044`.
- Engle and Granger, `Co-Integration and Error Correction: Representation,
  Estimation, and Testing`, Econometrica, 1987, DOI `10.2307/1913236`.
- Johansen, `Statistical analysis of cointegration vectors`, Journal of
  Economic Dynamics and Control, 1988, DOI `10.1016/0165-1889(88)90041-3`.
- Hansen and Johansen, `Some tests for parameter constancy in cointegrated
  VAR-models`, The Econometrics Journal, 1999, DOI `10.1111/1368-423x.00035`.
- Kim, Koh, Boyd, and Gorinevsky, `l1 Trend Filtering`, SIAM Review, 2009,
  DOI `10.1137/070690274`.
- Tibshirani, `Adaptive piecewise polynomial estimation via trend filtering`,
  Annals of Statistics, 2014, DOI `10.1214/13-aos1189`.
- Lacasa, Luque, Ballesteros, Luque, `From time series to complex networks:
  The visibility graph`, PNAS, 2008, DOI `10.1073/pnas.0709247105`.
- Luque, Lacasa, Ballesteros, Luque, `Horizontal visibility graphs: Exact
  results for random time series`, Physical Review E, 2009, DOI
  `10.1103/PhysRevE.80.046103`.
- Stephen, Gu, Yang, `Visibility Graph Based Time Series Analysis`, PLOS ONE,
  2015, DOI `10.1371/journal.pone.0143015`.
- Li and Zhao, `Multiscale horizontal-visibility-graph correlation analysis of
  stock time series`, EPL, 2018, DOI `10.1209/0295-5075/122/40007`.

## Metadata Verification

2026-05-30T00:17:34+0800 waiting-window check:

- Crossref confirmed every DOI listed above with matching title/year.
- arXiv confirmed `2605.04004` with title `Structural Limits of OHLCV-Based
  Intraday Signals in MNQ Futures: A Systematic Falsification Study`.
- arXiv lookup for `2605.17724` returned HTTP 429, so that entry remains
  `unverified_info_only` and must not drive candidate selection until refreshed.
- 2026-05-30T11:50:22+0800: Crossref confirmed Brunnermeier/Pedersen
  `Market Liquidity and Funding Liquidity` and Chordia/Roll/Subrahmanyam
  `Commonality in liquidity` with matching title/year. Use them as source
  support for a filter-only liquidity-stress reserve, not standalone alpha.
- 2026-05-30T12:13:46+0800: Crossref confirmed Schreiber transfer entropy,
  Marschinski/Kantz financial time-series information flow, and Dimpfl/Peter
  financial-market transfer entropy with matching title/year. Use them as
  source support for a cross-market confirmation/veto filter only, not
  standalone alpha.
- 2026-05-30T12:32:35+0800: Crossref confirmed Engle/Granger cointegration,
  Johansen cointegration vectors, and Hansen/Johansen parameter-constancy
  sources with matching title/year. Use them as source support for a
  cointegration-residual stability and half-life admission filter only, not a
  standalone pair-trading alpha.
- 2026-05-30T12:44:16+0800: Crossref confirmed Kim/Koh/Boyd/Gorinevsky L1
  trend filtering and Tibshirani adaptive trend filtering sources with matching
  title/year. Use them as source support for a sparse trend-denoising slope
  stability admission filter only, not standalone alpha.
- 2026-05-30T13:19:44+0800: Crossref confirmed Lacasa visibility graph, Luque
  horizontal visibility graph, Stephen/Gu/Yang visibility-graph analysis, and
  Li/Zhao multiscale HVG stock-time-series sources with matching title/year.
  Use them as source support for a parent trend-persistence admission filter
  only, not standalone alpha.
- 2026-05-31T21:06:24+0800: user-provided arXiv `2605.20142` PDF was downloaded
  and text-extracted locally. The paper proposes mixtures of mirrored Weibull
  distributions for non-normal return modelling and VaR estimation; it uses
  rolling prior-return windows for one-day VaR forecasts. In ict-engine, use it
  only as a lagged tail-risk gate for a parent entry. It must not generate entry
  signals by itself.
- 2026-06-01T04:10:29+0800: TOMAC futures source directories were repaired from
  ZIP-pristine archives. Previous ES/NQ `ict-cleaned-mtf` evidence is invalidated
  because extracted source dirs contained old `20100606-20260403` CSV material,
  an ES symlink to that old CSV, and an NQ shifted fallback CSV; XAU also had
  generated HTF CSVs mixed into the raw source directory. New cleaned MTF root:
  `/Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf`, manifest schema
  `zip-pristine-cleaned-mtf-manifest/v2`, all five archive validations passed,
  all quality checks passed, and practical flags remain false. Prior ES3m/ES15m
  exact-AQ negatives are retained only as polluted-provenance observation/debt,
  while ES30m positive observation must be rerun before it can be used as
  cleaned evidence.

## Candidate Packets

### mmw-trend-expansion-tail-gate-v1

```text
candidate_id: mmw-trend-expansion-tail-gate-v1
source: Jia/Lee arXiv 2605.20142 mirrored Weibull mixture VaR model
source_type: paper
source_risk: filter_only
why_now: The operator requested a single actionable case: enter only when the next state predicts TrendExpansion; MMW can reduce left-tail risk without creating non-expansion entries.
regime_root: TrendExpansion
branch_path: RegimeTransition -> TrendExpansionOnly -> MirroredWeibullTailGate -> mmw_trend_expansion_tail_gate_v1
instrument/timeframe: NQ/YM futures; 5m/15m/30m/1h/4h/1d independent target factors with prior 1d return tail state
entry: Parent TrendExpansion closed-bar signal only; then require prior-return MMW 1%/5% VaR and tail-span gates to pass before next-bar market entry.
confirmation: 30m/1h context for intraday candidates; all other regimes remain reference/veto only.
exit/risk: Parent ATR stop/target and max-hold; MMW is a permission gate, not an exit optimizer.
expected_holding_period: Intraday to multi-session depending on parent timeframe.
expected_cadence: 0.3 to 1.0 trades/session for the current NQ 15m local candidates.
data_required: retained TOMAC futures cache plus prior daily returns; exact-AQ/provider/paper parity still required.
cost_model_required: verified NQ/YM futures cost model; keep promotion flags false until exact-AQ and lifecycle evidence pass.
duplicate_check: Distinct from raw TrendExpansion-only screen because the MMW state is a lagged left-tail risk gate; do not rerun without the gate.
known_failure_modes: Tail gate can remove 2025 upside, local/Python state may not match AQ state, no provider/paper feedback yet.
first_gate1_shape: Completed local screen root /tmp/ict-engine-mmw-trend-expansion-tail-gate-20260531T210624+0800; strongest all-year-positive candidate was NQ 15m long clean mmw_soft.
status: local_screen_candidate_needs_exact_aq
promotion_allowed: false
trade_usable: false
```

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

### funding-liquidity-commonality-stress-filter-v1

```text
candidate_id: funding_liquidity_commonality_stress_filter_v1
source: Brunnermeier/Pedersen funding-liquidity feedback plus Chordia/Roll/Subrahmanyam common liquidity state
source_type: paper
source_risk: info_only_filter_not_alpha
why_now: Current 1m factor work repeatedly dies at cost, fill-quality, and practical lifecycle gates. A liquidity-stress filter can preserve parent candidates by skipping periods where broad liquidity commonality and funding stress make bar-only entries least executable.
regime_root: TransitionRisk
branch_path: TransitionRisk -> FundingLiquidityStress -> LiquidityCommonalityRegime -> ParentSignalAdmissionFilter -> funding_liquidity_commonality_stress_filter_v1
instrument/timeframe: Parent ES/NQ/YM/XAU or US equity candidates; 1m origin plus shifted 5m/15m/30m/1h/4h/1d context only after parent ownership clears.
entry: No standalone entry. Admit, skip, shorten, or downweight an already-owned parent signal based on pre-entry liquidity-stress state.
confirmation: Pre-entry notional-volume state, spread or spread-proxy state, realized price-impact proxy, cross-symbol liquidity commonality, 1h/4h stress trend, and no unverified after-entry fields.
exit/risk: If stress is rising, skip entry or tighten max hold; if stress is receding and parent signal is already valid, permit parent risk plan unchanged.
expected_holding_period: Same as parent branch; filter should not increase turnover.
expected_cadence: Should reduce trades and improve per-trade executable quality, not create new trades.
data_required: Parent trade rows, retained full-session bars, point-in-time volume/notional fields, spread or official quote/fill fields where available, and optional external stress sidecars such as NFCI/OFR FSI only after timestamp semantics are verified.
cost_model_required: Same exact instrument cost model as the parent plus slippage/fill-quality assumptions; this filter cannot make an unverified cost model practical.
duplicate_check: Local search found existing Amihud price-impact, Pastor-Stambaugh liquidity-risk, Corwin/Roll spread, futures-roll liquidity, auction imbalance, OFI/VPIN, and Epps sync packets. This reserve is distinct because it is a funding-liquidity/commonality admission filter for parent candidates, not a standalone price-impact alpha or spread estimator.
known_failure_modes: OHLCV-only liquidity proxies overfit, stress proxies published with lag, filter removes already-sparse winners, hidden lookahead from realized spread/fill fields, treating stress avoidance as promotion evidence, and ignoring product-specific costs.
first_gate1_shape: After compact audit clears and a parent factor is owned, rescore existing parent trades with shifted liquidity-state bins; require positive 5bps parent economics before sidecar; no provider/AQ run for the filter alone.
next_command_when_clear: Select one owned parent with real 5bps/cost-positive or near-practical evidence, create a factor-local sidecar workdoc, then run a read-only rescore before any AQ/provider retry.
status: idea_only_filter_source_reserve
promotion_allowed: false
trade_usable: false
```

### macro-sentiment-attention-risk-appetite-sidecar-v1

```text
candidate_id: macro_sentiment_attention_risk_appetite_sidecar_v1
source: Baker/Wurgler investor sentiment; Andrei/Hasler investor attention and volatility; FRED UMCSENT as public proxy only
source_type: paper + public_data_doc
source_risk: info_only_filter_not_alpha
why_now: Current 1m and clean-AQ lanes repeatedly hit cost, sparse-density, and lifecycle blockers. A slow risk-appetite sidecar can reduce runtime churn by deciding when a parent signal deserves stricter confirmation or lower exposure.
regime_root: RiskAppetiteRegime
branch_path: RiskAppetiteRegime -> InvestorSentimentAttentionState -> MacroRiskAppetiteAdmissionFilter -> ParentSignalThrottle -> macro_sentiment_attention_risk_appetite_sidecar_v1
instrument/timeframe: ES/YM/NQ parent factors with ETH/full-retained 1m origin plus shifted 5m/15m/30m/1h/4h/1d context; macro sidecar is monthly/weekly/daily only after release-time lagging.
entry: No standalone entry. Admit, skip, or require stronger confirmation on an already-owned parent signal when sentiment/attention state is known before the entry bar.
confirmation: Parent branch already has cost-positive or near-practical evidence; sidecar timestamp is release-lagged; 4h/1d parent state agrees; attention shock does not create hidden lookahead.
exit/risk: If macro sentiment is euphoric and attention/volatility shock is rising, reduce size or skip continuation entries; if pessimism is extreme but parent trend confirms, allow only lower-turnover parent setups.
expected_holding_period: Same as parent, generally multi-hour to multi-session; this sidecar should not increase trade count.
expected_cadence: Reduces trades; cannot create new trades.
data_required: Parent trade rows, exact ETH/full-retained session coverage, FRED/Baker-Wurgler/attention proxy release timestamps, and no-lookahead joining rules.
cost_model_required: Same exact instrument cost model as parent. Macro sentiment cannot verify costs or rescue missing cost economics.
duplicate_check: No exact macro sentiment/attention/risk-appetite sidecar packet found; related overnight/intraday sentiment packet is a different return-decomposition filter. Avoid COT, options-pressure, VIX/VRP, realized-vol term-structure, liquidity, VPIN/OFI, auction, turn-of-month, and NQ compound lanes.
known_failure_modes: Monthly data is too slow for intraday timing, release-date lookahead, proxy inversion over regimes, filtering out all sparse winners, treating source popularity as practical evidence, and using sentiment as standalone alpha.
first_gate1_shape: After compact audit clears and a parent lane is owned, run a read-only rescore of existing parent rows with release-lagged sidecar bins. Do not run provider/AQ for the sidecar alone.
next_command_when_clear: Select one owned parent with real cost/density evidence, create a factor-local sidecar workdoc, then rescore with timestamp-lagged macro state before any AQ/provider retry.
status: idea_only_filter_source_reserve
promotion_allowed: false
trade_usable: false
```

### transfer-entropy-cross-market-confirmation-gate-v1

```text
candidate_id: transfer_entropy_cross_market_confirmation_gate_v1
source: Schreiber transfer entropy; Marschinski/Kantz financial time-series transfer entropy; Dimpfl/Peter financial-market information flow
source_type: paper
source_risk: info_only_filter_not_alpha
why_now: Current cross-market and peer-confirmation lanes risk confusing correlation, synchronization artifacts, or generic lead-lag with directional information. Transfer entropy can become a stricter no-lookahead parent confirmation/veto before spending runtime on cross-market branches.
regime_root: CrossMarketStructure
branch_path: CrossMarketStructure -> InformationFlowDirection -> TransferEntropyConfirmationGate -> ParentSignalAdmissionFilter -> transfer_entropy_cross_market_confirmation_gate_v1
instrument/timeframe: Parent-defined ES/NQ/YM/XAU or ETF/index peer baskets; 1m origin plus shifted 5m/15m/30m/1h/4h/1d context only after parent ownership clears.
entry: No standalone entry. Admit or veto an already-owned parent signal only when pre-entry transfer-entropy direction from the driver market to the traded market is stable and agrees with the parent side.
confirmation: Directional information score above shuffled/surrogate baseline, stable driver-target direction over adjacent windows, no same-bar target leakage, Epps/sync gate not failing, and parent 1h/4h trend or reclaim logic still intact.
exit/risk: Inherit parent exit. Skip entries when information direction is unavailable, unstable, symmetric/noisy, or dominated by session boundary bars.
expected_holding_period: Same as parent; likely multi-hour to multi-session if useful.
expected_cadence: Filter only; should reduce parent trades, not create new trades.
data_required: Retained timestamped peer OHLCV with common timezone and ETH/full-retained proof for the parent; enough overlapping history for lagged discrete-state or rank-binned transfer entropy; surrogate/shuffle baseline; optional tick data later.
cost_model_required: Same exact product cost model as parent. This gate has no independent economics and cannot satisfy cost survival.
duplicate_check: Focused same-turn local search found no exact transfer-entropy/information-flow confirmation gate. Do not duplicate Epps sync, NQ/YM lead-lag VWAP residual, XAU safe-haven lead-lag, cash-futures basis, auction, OFI/VPIN, or volatility-spillover lanes.
known_failure_modes: Entropy estimator instability on sparse samples, discretization overfit, same-bar leakage, driver/target reversal after regime shifts, holiday/session mismatch, redundant correlation gate, filter removes sparse winners, and treating source-only information flow as trade evidence.
first_gate1_shape: After compact audit clears and a cross-market parent is owned, run a read-only parent-trade rescore with pre-entry transfer-entropy bins and shuffled baselines. Report parent row count before/after, TE direction stability, cross-scale agreement, 5bps parent economics, density retention, and fail closed if ETH coverage or cost proof is lost.
next_command_when_clear: Re-run compact claim audit; if clear, choose one owned cross-market parent with positive or near-practical evidence and create a factor-local sidecar workdoc. Do not launch this as a standalone family.
status: paper_only_filter_source_reserve
promotion_allowed: false
trade_usable: false
```

### cointegration-residual-half-life-stability-gate-v1

```text
candidate_id: cointegration_residual_half_life_stability_gate_v1
source: Engle-Granger cointegration/error-correction; Johansen cointegration vectors; Hansen-Johansen parameter constancy
source_type: paper
source_risk: info_only_filter_not_alpha
why_now: Current relative-value and cross-market lanes need stricter checks before spending AQ/provider runtime. A residual stability and half-life gate can reject unstable spreads instead of adding another high-turnover z-score root.
regime_root: CrossMarketStructure
branch_path: CrossMarketStructure -> CointegrationResidualStability -> HalfLifePersistenceGate -> ParentSignalAdmissionFilter -> cointegration_residual_half_life_stability_gate_v1
instrument/timeframe: Parent-defined ES/NQ/YM or metals pairs; 1m origin plus shifted 5m/15m/30m/1h/4h/1d context only after parent ownership clears.
entry: No standalone entry. Admit an already-owned parent relative-value or spread-reversion signal only when lagged residual tests show stable cointegration, bounded half-life, and no recent parameter-instability warning.
confirmation: Pre-entry residual z-score, rolling ADF/ECM speed, residual half-life inside a bounded window, Johansen or Engle-Granger relation stable on train windows, parameter-constancy check not failing, parent HTF state not one-way trend, and no same-bar target leakage.
exit/risk: Inherit parent exit. If residual half-life expands or the cointegration relation fails, skip entry or force parent to observation-only.
expected_holding_period: Same as parent; likely intraday to multi-session.
expected_cadence: Filter only; should reduce parent trades and reject unstable spreads.
data_required: Synchronized retained full-session peer bars, identical timezone/session semantics, no-lookahead rolling fit windows, parent trade rows, and later provider/paper execution evidence for multi-leg fills.
cost_model_required: Exact product costs for both legs plus slippage/legging assumptions. This source reserve cannot satisfy cost survival.
duplicate_check: Distinct from pair z-score mean-reversion runners because it is a pre-entry residual stability gate; not a Kalman/state-space slope family, not transfer entropy, not Epps sync, not cash-futures basis, not liquidity spread, and not generic regime-drift/changepoint work.
known_failure_modes: Rolling cointegration overfits pair choice, relation breaks during macro regimes, half-life estimate is unstable on short windows, OHLCV bar alignment hides legging risk, two-leg costs erase spread edge, and source-only stationarity is mistaken for practical readiness.
first_gate1_shape: After compact audit clears and a parent lane is owned, run read-only parent-trade rescore with lagged rolling residual features. Report parent rows before/after, 5bps or instrument-cost economics on both legs, density retention, split/year stability, and fail closed if ETH/full-retained coverage or cost proof is missing.
next_command_when_clear: Re-run compact claim audit; if clear, choose one owned relative-value parent with positive or near-practical evidence, create a factor-local sidecar workdoc, then run local no-launch rescore before any provider/AQ retry.
status: paper_only_filter_source_reserve
promotion_allowed: false
trade_usable: false
update_goal: false
```

### l1-trend-filter-slope-stability-gate-v1

```text
candidate_id: l1_trend_filter_slope_stability_gate_v1
source: Kim/Koh/Boyd/Gorinevsky l1 trend filtering; Tibshirani adaptive trend filtering
source_type: paper
source_risk: info_only_filter_not_alpha
why_now: Current trend-like 1m/MTF lanes often fail from noisy slope flips, churn, and poor year stability. A sparse trend-filter slope gate can require a cleaner piecewise trend before spending AQ/provider runtime on a parent continuation factor.
regime_root: TrendExpansion
branch_path: TrendExpansion -> SparseTrendDenoising -> L1TrendFilterSlopeStability -> ParentSignalAdmissionFilter -> l1_trend_filter_slope_stability_gate_v1
instrument/timeframe: Parent ES/NQ/YM/XAU futures candidates; each native 5m/15m/30m/1h/4h/1d timeframe can be an independent parent-sidecar factor after ownership clears.
entry: No standalone entry. Admit an already-owned parent trend or pullback-continuation signal only when pre-entry l1-filtered slope is stable, same-signed across the required lookback, and not contradicted by higher-timeframe context.
confirmation: Shifted l1-filter slope, slope sign persistence, kink density below churn cap, parent trend setup still valid, optional MTF slope resonance, ETH/full-retained coverage proof, and no same-bar target leakage.
exit/risk: Inherit parent exit. If denoised slope flips or kink density spikes before entry, skip. Do not widen stops or lower cost gates to force survival.
expected_holding_period: Same as parent, preferably multi-hour to multi-session.
expected_cadence: Filter only; should reduce parent trades and improve per-trade quality, not create extra entries.
data_required: Retained full-session parent bars, shifted rolling windows for each native timeframe, parent trade rows or candidate signals, and later exact provider/AQ/paper lifecycle evidence if the parent survives.
cost_model_required: Same exact product cost model as parent. Source metadata and denoised slope cannot verify costs.
duplicate_check: No exact local L1 trend-filter packet found. Distinct from Ehlers cycle-phase, continuous-information momentum, multires energy, Kalman/state-space slope, Hurst/fractal, variance-ratio, and realized-vol term-structure lanes.
known_failure_modes: Over-smoothing misses early trend turns, lambda selection overfits OOS, kink-density filter removes sparse winners, lag makes entries late after costs, and source-only denoising is mistaken for practical readiness.
first_gate1_shape: After compact audit clears and a parent lane is owned, run a read-only parent-trade rescore by native timeframe. Report parent rows before/after, instrument-cost and 5bps stress economics, density retention, split/year stability, and fail closed if ETH/full-retained coverage or cost proof is missing.
next_command_when_clear: Re-run compact claim audit; if clear, choose one owned trend parent with positive or near-practical evidence, create a factor-local sidecar workdoc, then run local no-launch rescore before any provider/AQ retry.
status: paper_only_filter_source_reserve
promotion_allowed: false
trade_usable: false
update_goal: false
```

### copula-tail-dependence-stress-admission-filter-v1

```text
candidate_id: copula_tail_dependence_stress_admission_filter_v1
source: Patton conditional/asymmetric copula dependence; Ang/Chen asymmetric correlations; Longin/Solnik extreme correlations; Jondeau/Rockinger Copula-GARCH conditional dependencies
source_type: paper
source_risk: info_only_filter_not_alpha
why_now: Current cross-market and trend-continuation candidates often look acceptable in normal correlation regimes but can fail when downside joint-tail dependence spikes. A shifted copula/tail-dependence stress gate can veto parent entries during fragile cross-market states without launching a duplicate standalone alpha.
regime_root: CrossMarketStructure
branch_path: CrossMarketStructure -> TailDependenceStress -> ConditionalCopulaRegime -> ParentSignalAdmissionFilter -> copula_tail_dependence_stress_admission_filter_v1
instrument/timeframe: Parent-defined ES/NQ/YM/XAU or ETF/index baskets; 1m origin plus shifted 5m/15m/30m/1h/4h/1d context only after parent ownership clears.
entry: No standalone entry. Admit or veto an already-owned parent trend, reclaim, relative-value, or cross-market signal only when pre-entry downside tail-dependence state is not in a stress cluster against the parent side.
confirmation: Shifted rolling rank transforms, empirical lower-tail co-exceedance, conditional copula or pseudo-copula state bucket, parent-side correlation asymmetry, 1h/4h stress trend, and no same-bar target leakage.
exit/risk: Inherit parent exit. If downside joint-tail dependence rises into stress, skip entry, shorten max hold, or force observation-only according to the parent risk plan.
expected_holding_period: Same as parent; intended to improve executable quality, not create extra turnover.
expected_cadence: Filter only; should reduce parent trade count and improve per-trade robustness.
data_required: Retained full-session parent and peer bars with common timezone, shifted rank/return windows, enough history for tail buckets, parent trade rows, and later provider/paper execution semantics if the parent survives.
cost_model_required: Same exact product cost model as the parent plus any multi-leg/slippage assumptions. Tail-dependence metadata cannot verify costs.
duplicate_check: Focused local search found no exact copula/tail-dependence stress admission packet in repo docs or active `/tmp` claims. Do not duplicate transfer entropy, cointegration residual stability, variance-ratio, realized skew/semivariance, realized-jump, Epps synchronization, index-dispersion, liquidity commonality, or generic correlation-break lanes.
known_failure_modes: Tail buckets are sparse, copula fit overfits short windows, dependence state is unstable around macro events, delayed confirmation creates lookahead, filter removes rare winners, and source-only stress detection is mistaken for practical readiness.
first_gate1_shape: After compact audit clears and a parent cross-market or trend lane is owned, run a read-only parent-trade rescore with pre-entry lower-tail dependence buckets. Report parent rows before/after, 5bps or instrument-cost economics, density retention, split/year stability, tail-state hit rate, and fail closed if ETH/full-retained coverage or cost proof is missing.
next_command_when_clear: Re-run compact claim audit; if clear, choose one owned parent with real 5bps/cost-positive or near-practical evidence, create a factor-local sidecar workdoc, then run local no-launch rescore before any provider/AQ retry.
status: paper_only_filter_source_reserve
promotion_allowed: false
trade_usable: false
update_goal: false
```

### matrix-profile-motif-discord-admission-filter-v1

```text
candidate_id: matrix_profile_motif_discord_admission_filter_v1
source: Yeh/Zhu/Ulanova/Begum/Ding/Dau/Silva/Mueen/Keogh matrix profile motifs/discords; Ermshaus/Wogulis/Dau/Bagnall/Keogh variable-length matrix-profile motif/discord discovery
source_type: paper
source_risk: info_only_filter_not_alpha
why_now: Many parent TOMAC and local-screen branches fail from one-off shape anomalies, sparse hero motifs, or regime breaks that only become visible after trade rows exist. Matrix-profile distances can later rescore whether a pre-entry shape resembles historically accepted parent setups and whether it is a discord/anomaly, without spending shared runtime during occupied windows.
regime_root: ValidationMaturity
branch_path: ValidationMaturity -> MatrixProfileMotifDiscord -> ParentSignalSimilarityAdmission -> matrix_profile_motif_discord_admission_filter_v1
instrument/timeframe: Future parent trend, pullback, breakout, or reclaim candidates on ES/YM/NQ/XAU. Each native 5m/15m/30m/1h/4h/1d parent timeframe is an independent future factor after ownership clears.
entry: No standalone entry. Admit a parent setup only when the shifted pre-entry subsequence is close to historically accepted motifs and not a discord/anomaly under the same parent context.
confirmation: Shifted matrix-profile distance, motif cluster stability across train/OOS, discord veto below threshold, parent signal still valid, MTF context not contradictory, ETH/full-retained coverage proof, and no same-bar target leakage.
exit/risk: Inherit parent exit. If the pre-entry sequence is discord-like, skip rather than widen risk or lower gates.
expected_holding_period: Same as parent, preferably multi-hour to multi-session.
expected_cadence: Filter only; should reduce parent trades and improve per-trade quality, not add entries.
data_required: Parent trade rows or signal rows, retained full-session bars, shifted rolling subsequences for each native timeframe, and later exact provider/AQ/paper lifecycle evidence if the parent survives.
cost_model_required: Same exact product cost model as parent. Shape similarity cannot verify costs.
duplicate_check: No exact local matrix-profile, discord, shapelet, STOMP, SCRIMP, or subsequence-similarity admission lane found. Distinct from volume-clock participation, rough-path signatures, permutation entropy, directional-change/overshoot, Ehlers/Hilbert cycle phase, SSA denoising, continuous-information momentum, and multires energy gates.
known_failure_modes: Motif mining overfits train shapes, discord veto removes rare winners, subsequence length becomes another hidden parameter sweep, overlapping windows inflate confidence, and shape similarity is mistaken for practical readiness.
first_gate1_shape: After compact audit clears and a parent lane is owned, run a no-provider parent-trade rescore by native timeframe. Report before/after rows, instrument-cost and 5bps stress economics, density retention, split/year stability, motif cluster coverage, discord veto rate, and fail closed if ETH/full-retained coverage or cost proof is missing.
next_command_when_clear: Re-run compact claim audit; if clear, choose one owned parent with existing trade rows and run a local no-launch matrix-profile rescore before any provider/AQ retry.
status: paper_only_filter_source_reserve
promotion_allowed: false
trade_usable: false
update_goal: false
```

### visibility-graph-trend-persistence-filter-v1

```text
candidate_id: visibility_graph_trend_persistence_filter_v1
source: Lacasa visibility graph; Luque horizontal visibility graph; Stephen/Gu/Yang visibility-graph time-series analysis; Li/Zhao multiscale HVG stock-time-series analysis
source_type: paper
source_risk: info_only_filter_not_alpha
why_now: Current retained 1m and MTF trend candidates frequently fail from noisy slope flips, choppy local sequences, and unstable year splits. Visibility-graph topology can describe pre-entry sequence persistence without adding another same-bar price threshold or claiming standalone alpha.
regime_root: TrendExpansion
branch_path: TrendExpansion -> SequenceTopology -> VisibilityGraphTrendPersistence -> ParentSignalAdmissionFilter -> visibility_graph_trend_persistence_filter_v1
instrument/timeframe: Parent ES/NQ/YM/XAU futures candidates first; 1m origin plus shifted 5m/15m/30m/1h/4h/1d context when available.
entry: No standalone entry. Admit an already-owned parent trend, breakout, pullback, or carryover signal only when pre-entry rolling visibility-graph features indicate directional persistence and not local sequence noise.
confirmation: Shifted rolling natural/HVG degree features, degree-asymmetry, local clustering or motif stability, parent signal still valid, higher-timeframe direction not contradictory, ETH/full-retained coverage proof, and no same-bar target leakage.
exit/risk: Inherit parent exit. If graph persistence deteriorates before entry, skip or observation-only; do not widen stops, lower costs, or add trades to force survival.
expected_holding_period: Same as parent, preferably multi-hour to multi-session where costs can be amortized.
expected_cadence: Filter only; should reduce parent trades and improve per-trade quality, not create extra entries.
data_required: Retained full-session bars, rolling pre-entry windows by native timeframe, parent signal or trade rows, and later exact provider/AQ/paper lifecycle evidence if the parent survives.
cost_model_required: Same exact product cost model as parent. Visibility-graph metadata cannot verify transaction costs.
duplicate_check: No exact local visibility-graph/HVG sequence-topology factor lane found. Keep distinct from matrix profile, rough path, permutation entropy, directional-change/overshoot, Hawkes intensity, Ehlers/Hilbert, SSA, continuous-information momentum, and multires energy filters.
known_failure_modes: Graph features overfit window length, short 1m windows become noisy random graphs, feature lag misses fast trend turns, filter removes rare winners, and topology metrics are mistaken for practical readiness.
first_gate1_shape: After compact audit clears and a parent lane is owned, run a no-provider parent-trade rescore by native timeframe. Report before/after rows, instrument-cost and 5bps stress economics, density retention, split/year stability, topology bucket coverage, and fail closed if ETH/full-retained coverage or cost proof is missing.
next_command_when_clear: Re-run compact claim audit; if clear, choose one owned trend parent with real trade rows, create a factor-local sidecar workdoc, then run local no-launch visibility-graph rescore before any provider/AQ retry.
status: paper_only_filter_source_reserve
promotion_allowed: false
trade_usable: false
update_goal: false
```

### structural-break-variance-shift-admission-filter-v1

```text
candidate_id: structural_break_variance_shift_admission_filter_v1
source: Bai/Perron multiple structural changes; Inclan/Tiao variance-shift cumulative sums of squares
source_type: paper
source_risk: info_only_filter_not_alpha
why_now: Many parent factors die after apparent local positives because the return/risk relation is unstable by year, session, or volatility state. A shifted structural-break and variance-shift veto can prevent runtime spend on parent signals whose recent estimation window is nonstationary.
regime_root: ValidationMaturity
branch_path: ValidationMaturity -> StructuralBreakStability -> VarianceShiftAndParameterBreak -> ParentSignalAdmissionFilter -> structural_break_variance_shift_admission_filter_v1
instrument/timeframe: Parent ES/NQ/YM/XAU futures candidates first; each owned 5m/15m/30m/1h/4h/1d parent timeframe remains an independent later factor.
entry: No standalone entry. Admit an already-owned parent signal only when pre-entry rolling coefficients and variance state have no fresh structural break against the parent side.
confirmation: Shifted Bai-Perron style break score on parent explanatory features, shifted ICSS-style variance-break score, stable parent-side slope sign, enough post-break sample, ETH/full-retained coverage proof, and no same-bar target leakage.
exit/risk: Inherit parent exit; skip or observation-only when a fresh break is active. Do not widen stops or lower cost gates.
expected_holding_period: Same as parent; intended to protect multi-hour to multi-session parents where transaction costs can be amortized.
expected_cadence: Filter only; should reduce parent trade count and improve stability, not add entries.
data_required: Retained full-session parent bars, parent trade/signal rows, shifted rolling feature windows, and later exact provider/AQ/paper lifecycle evidence if the parent survives.
cost_model_required: Same exact product cost model as parent. Break-test metadata cannot verify costs.
duplicate_check: No exact local structural-break plus variance-shift parent-admission packet found. Keep distinct from CUSUM deadzone, persistent homology, causal trend-cycle, variance-ratio, Kalman/state-space slope, and generic regime-shift packets.
known_failure_modes: Break tests overreact to outliers, minimum segment length creates lag, small samples make year splits sparse, the filter removes rare winners, and source-only stability is mistaken for practical readiness.
first_gate1_shape: After compact audit clears and a parent lane is owned, run a no-provider parent-trade rescore by native timeframe. Report before/after rows, 5bps and instrument-cost economics, density retention, split/year stability, break-state hit rate, and fail closed if ETH/full-retained coverage or cost proof is missing.
next_command_when_clear: Re-run compact claim audit; if clear, choose one owned parent with trade rows, create a factor-local sidecar workdoc, then run local no-launch rescore before any provider/AQ retry.
status: paper_only_filter_source_reserve
promotion_allowed: false
trade_usable: false
update_goal: false
```

### mirrored-weibull-mixture-tail-risk-filter-v1

```text
candidate_id: mirrored_weibull_mixture_tail_risk_filter_v1
source: Jia and Lee, "Mining Financial Data using Mixtures of Mirrored Weibull Distributions", arXiv:2605.20142.
source_type: paper
source_risk: paper_only_plus_local_screen_plus_exact_aq_ladder_weak_5m
why_now: A paper-derived tail-shape model can act as a shifted, no-lookahead admission filter for trend parents that otherwise churn through adverse tail-expansion states. It addresses cost/stability by skipping bad tail states rather than adding more entries.
regime_root: TrendExpansion
branch_path: TrendExpansion -> TailShapeRiskState -> MirroredWeibullMixtureRiskCompression -> mirrored_weibull_mixture_tail_risk_filter_v1
instrument/timeframe: NQ retained local 5m/15m/30m/1h/4h/1d ladder. 15m/30m/1h exact-AQ reproductions failed; 5m exact-AQ is weak positive only.
entry: Parent trend-continuation signal only. The MMW state admits or vetoes long/short entries using completed-bar rolling adverse-tail VaR and tail-width compression.
confirmation: Rolling mirrored-Weibull-mixture fit on past returns only, BIC/fixed small component count, shifted VaR 1%/5%, trend slope/momentum, ETH/full-retained coverage proof, and no same-bar target leakage.
exit/risk: Fixed ATR TP/SL plus max-hold in local screen. Exact AQ must preserve runner-owned exit semantics and verified NQ instrument-cost conversion.
expected_holding_period: Multi-hour to multi-day; first local positive used 96 x 15m max hold.
expected_cadence: Local best row had 1630 trades over 1555 sessions, 1.048 trades/session.
data_required: Retained full-session OHLCV; later exact AQ/provider/paper/downstream evidence if promoted beyond source screen.
cost_model_required: Verified product-specific NQ futures cost model; local screen used shared futures instrument-cost helper, not fixed-bps promotion authority.
duplicate_check: Focused local search found no exact Weibull/MMW/mirrored-Weibull packet or active claim before the 2026-05-31 screen.
known_failure_modes: Paper proves VaR calibration, not alpha; MMW transform is unit-sensitive through c; coarse refit cadence can miss fast state changes; 2025 was negative in the first 15m local row; local pandas positives can fail exact AQ badly.
first_gate1_shape: Do not rerun the failed 15m/30m/1h exact-AQ shapes as-is. The 5m exact-AQ result may be used only as an observe/downstream feedback candidate; preserve false practical flags until downstream lifecycle, provider/paper feedback, and same-tree closure evidence exists.
local_screen_evidence: /tmp/ict-engine-mirrored-weibull-mixture-tail-risk-source-screen-20260531T181305+0800/checks/terminal_metrics.json
best_local_row: trades=1630, trades_per_session=1.0482315112540193, gross_total_profit_pct=20.87299635609968, fee_only_total_profit_pct=18.56320235349653, instrument_cost_total_profit_pct=10.863889011486037, instrument_cost_profit_factor=1.0458766386007643, years_positive=4, 2025=-6.722019856140216.
exact_aq_15m_evidence: /tmp/ict-engine-mmw-tail-risk-filter-exact-aqprep-20260531T184620+0800/checks/terminal_metrics.json, exit=0 but total_profit_pct=-30.01, profit_factor=0.84, trade_count=2885, status=exact_aq_completed_fail_closed.
mtf_ladder_evidence: /tmp/ict-engine-mmw-tail-risk-mtf-ladder-screen-20260531T193258+0800/summaries/mtf_ladder_summary.json. 5m candidates=8 best cost_pct=11.0224 PF=1.0608; 30m candidates=6 best cost_pct=25.7163 PF=1.1627; 1h candidates=6 best cost_pct=27.5482 PF=1.1493; 4h/1d rejected for density.
exact_aq_ladder_evidence: /tmp/ict-engine-mmw-tail-risk-mtf-ladder-screen-20260531T193258+0800/summaries/exact_aq_ladder_summary.json. 15m=-30.01% PF=0.8399; 30m=-15.95% PF=0.8948; 1h=-23.86% PF=0.8101; 5m=+1.08% PF=1.0036, 3584 trades, weak_positive_observe_only.
status: exact_aq_ladder_weak_5m_observe_only_no_practical_promotion
promotion_allowed: false
trade_usable: false
update_goal: false
```

### trend-expansion-only-regime-transition-v1

```yaml
intake_date: 2026-05-31
candidate_id: trend_expansion_only_regime_transition_v1
source:
  - Crossref DOI metadata for Hamilton 1989 regime switching: https://api.crossref.org/works/10.2307/1912559
  - Hidden hierarchical Markov trend reversal paper: https://arxiv.org/abs/2605.27848
  - StockSharp TTM Squeeze Python strategy: https://stocksharp.com/store/stocksharp.strategies.0452_ttm_squeeze.py/
  - QuantConnect Choppiness Index reference: https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/supported-indicators/choppiness-index
why_now: User explicitly narrowed the factor tailor task to exactly one entry condition: predict the next state as expansion/trend, enter only there, and use every other regime only as a no-entry warning.
regime_root: RegimeTransition
branch_path: RegimeTransition -> TrendExpansionOnly -> CompressionBreakoutStateShift -> tomac_nq_15m_trend_expansion_only_regime_transition_long_balanced_state_shift_exact_aq_v1
instrument/timeframe: NQ futures 15m exact-AQ child from retained TOMAC NQ 5m/15m/30m/1h local screen; ETH/full_retained_session.
entry: Closed-bar deterministic proxy for next-state TrendExpansion. Trigger is volatility-compression release or narrow-range Donchian expansion; confirmation uses ADX rising, VHF rising, CHOP below cap, trend slope, and higher-timeframe EMA-slope agreement. Entry is next bar only.
veto_policy: RangeCompression, Chop, StressVolatility, and MeanReversion are reference/veto states only and cannot produce entries.
no_lookahead_guard: Signal features use completed bars only; local simulation enters at next bar open; exact-AQ strategy shifts entry_raw by one candle.
local_screen_evidence: /tmp/ict-engine-trend-expansion-only-regime-transition-20260531T202324+0800/checks/terminal_metrics.json
best_local_row: NQ 15m long balanced_state_shift, trades=1832, trades_per_session=1.178135, instrument_cost_total_profit_pct=32.851746, instrument_cost_profit_factor=1.238785, years_positive=5/5.
exact_aq_evidence: /tmp/ict-engine-trend-expansion-only-regime-transition-20260531T202324+0800/checks/exact_aq_stdout.txt
exact_aq_gross: trades=1686, total_profit_pct=37.50, profit_factor=1.1858, sharpe=1.1301, max_drawdown_pct=10.1217.
exact_aq_instrument_cost_evidence: /tmp/ict-engine-trend-expansion-only-regime-transition-20260531T202324+0800/checks/exact_aq_instrument_cost_summary.json
exact_aq_instrument_cost_readback: trades=1686, instrument_cost_total_profit_pct=30.687344, instrument_cost_profit_factor=1.174468, train=5.840608, validation=9.555212, test=15.291523, years_positive=4/5.
known_failure_modes: 2022 exact-AQ year remains negative, Freqtrade informative timeframe fillup warnings need no-fill parity follow-up, exact-AQ gross fees are zero and require separate instrument-cost readback, and no provider/paper/downstream lifecycle evidence exists.
first_gate1_shape: Next step is exact-AQ parity/no-fill cleanup plus downstream lifecycle packet only if fresh claim audit remains clear. Do not promote from this source reserve alone.
status: exact_aq_instrument_cost_positive_needs_downstream_paper_lifecycle
promotion_allowed: false
trade_usable: false
update_goal: false
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
- Treat funding-liquidity/commonality stress as an admission filter on an
  already-owned parent, not a new alpha root. It can justify skipping or
  shortening trades during broad liquidity stress, but it cannot rescue an
  unverified cost model, missing parent economics, or absent paper/fill
  semantics.
- Treat macro sentiment / investor-attention sources as slow risk-appetite
  sidecars only. They need release-time lagging and parent-signal evidence, and
  they cannot create standalone entries or practical-readiness flags.
- Treat transfer entropy / directed information flow as a confirmation or veto
  sidecar for already-owned cross-market parents only. It needs pre-entry
  lagging, shuffled baselines, stable driver-target direction, and parent cost
  evidence; it is not standalone alpha and cannot create practical-readiness
  flags.
- Treat copula / tail-dependence stress state as a parent admission veto, not a
  fresh alpha root. It needs shifted rank windows, sparse-tail controls,
  parent-side cost evidence, and retained-session proof before any Gate 1 spend.
- Treat visibility-graph / HVG sequence topology as a parent persistence filter,
  not a new alpha root. It needs shifted pre-entry windows, parent trade rows,
  ETH/full-retained coverage, and exact product cost evidence before any Gate 1
  spend.
- Treat structural-break / variance-shift tests as parent admission vetoes, not
  entry alpha. They need shifted rolling windows, enough post-break sample,
  parent trade rows, ETH/full-retained coverage, and exact product cost evidence
  before any Gate 1 spend.
- Treat entropy-pooling / minimum-relative-entropy view confidence as a parent
  admission and uncertainty-stress filter, not standalone alpha or a sizing
  shortcut. It needs shifted parent trade rows, explicit view features, bounded
  tilt distance, retained-session proof, exact product costs, and split/year
  stability before any Gate 1 spend; practical flags stay false until the
  same-root lifecycle chain independently closes.
- Treat Form 4 insider cluster-buying as event-data-first source prep, not
  intraday alpha. Crossref metadata supports insider-trade informativeness, but
  this host returned SEC source blockers for Form 4/company-ticker endpoints on
  2026-05-30, so any future Gate 1 must first verify official point-in-time
  filing accepted timestamps, transaction code `P`, CIK/ticker mapping,
  amendment status, and corporate-action-adjusted ETH/full-retained intraday
  rows. Keep it as a parent admission filter with practical flags false until
  source data, costs, and same-root lifecycle evidence independently pass.
- Treat mirrored-Weibull-mixture tail state as a parent admission filter, not a
  standalone alpha root. The first local NQ 15m screen found long-side
  instrument-cost-positive candidates, but the evidence is local-screen only
  and the best row was negative in 2025. It needs exact AQ/provider/downstream
  reproduction before any practical-readiness claim.
- Treat TrendExpansion-only regime-transition entries as a promising but still
  non-practical source-backed branch: local and exact-AQ NQ 15m results were
  positive after verified IBKR NQ fee readback, but 2022 exact-AQ was negative
  and provider/paper/downstream lifecycle evidence is absent. Keep all other
  regimes as veto/reference states only, and keep practical flags false until
  same-tree lifecycle closure exists.
