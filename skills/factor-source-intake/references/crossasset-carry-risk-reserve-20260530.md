# Cross-Asset Carry And Risk Reserve - 2026-05-30

This is waiting-window source intake only. It was created while a fresh Board B
claim owned the shared factor-training surface, so no provider, IBKR,
Auto-Quant, Freqtrade, paper, or lifecycle command was launched. These notes do
not prove `promotion_allowed=true` or `trade_usable=true`.

## Triggering Runtime State

2026-05-30T00:22+0800 compact claim audit reported one fresh active claim:
`codex-m2k-opening-range-failure-fade-local-screen`, age 14 minutes,
`live_factor_processes=0`, `promotion_allowed_true=0`, `trade_usable_true=0`,
and `next_action=wait for fresh active claims to progress`. This reserve is the
non-colliding work done during that waiting window.

## Sources Checked

Crossref metadata was checked in this turn:

- Asness, Moskowitz, Pedersen, `Value and Momentum Everywhere`, Journal of
  Finance, 2013, DOI `10.1111/jofi.12021`.
- Koijen, Moskowitz, Pedersen, Vrugt, `Carry`, Journal of Financial Economics,
  2018, DOI `10.1016/j.jfineco.2017.11.002`.
- Gorton and Rouwenhorst, `Facts and Fantasies about Commodity Futures`,
  Financial Analysts Journal, 2006, DOI `10.2469/faj.v62.n2.4083`.
- Bollerslev, Tauchen, Zhou, `Expected Stock Returns and Variance Risk Premia`,
  Review of Financial Studies, 2009, DOI `10.1093/rfs/hhp008`.

## Duplicate / Negative-Evidence Notes

- Existing repo scripts include `run_vix_vrp_contango_pullback_yf_qqq_aq_v1.py`;
  do not rerun that exact VIX/VRP QQQ shape unchanged.
- Historical `SourceRootStopCarryLongHorizonV1` and
  `RootLiquidityVolCarryLongHistoryV1` artifacts exist as prior carry-style
  evidence. New candidates below must keep branch novelty explicit and cannot
  reuse old daily carry rows as practical proof.
- Commodity ETF ORB/RVOL expansion and oil/credit/duration scripts already
  exist. The commodity candidate below is a carry/term-structure filter idea,
  not another opening-range breakout.

## Candidate Packets

### crossasset-value-momentum-agreement-v1

```text
candidate_id: crossasset-value-momentum-agreement-v1
source: Asness/Moskowitz/Pedersen value and momentum across asset classes
source_type: paper
source_risk: info_only
why_now: The current NQ work shows a cost wall for short-horizon churn; cross-asset agreement can act as a low-turnover regime filter for futures or ETF trend roots.
regime_root: TrendExpansion
branch_path: TrendExpansion -> CrossAssetValueMomentumAgreement -> MultiAssetTrendConfirmation -> crossasset_value_momentum_agreement_v1
instrument/timeframe: NQ or QQQ 1m entry origin with 1h/4h/1d trend context; cross-asset labels from ES/YM/TLT/UUP/GLD or available provider equivalents.
entry: Only take an existing trend or carryover parent entry when the traded asset's 1d momentum agrees with a slow cross-asset value/momentum basket direction.
confirmation: 1h/4h slope agrees, VIX or realized-volatility state is not crisis, and cross-asset agreement is known before the 1m entry bar.
exit/risk: Inherit parent fixed-RRR or multi-session hold; this packet is a filter, not a standalone exit engine.
expected_holding_period: Multi-hour to multi-session.
expected_cadence: Should reduce parent cadence, not create overtrading; target remains 0.05 to 0.5 trades/session on the filtered parent.
data_required: Retained or provider 1m origin plus synchronized daily cross-asset context; no lookahead in daily feature availability.
cost_model_required: Same as parent product plus any ETF/futures product-specific cost if the symbol changes.
duplicate_check: Do not reuse old SourceRootStopCarryLongHorizon rows as proof; use this only as a pre-entry agreement filter on a newly owned parent lane.
known_failure_modes: Slow cross-asset features lag reversals, filter erases the few winners, daily value proxy unavailable for futures, and high correlation can overstate independent evidence.
first_gate1_shape: Offline rescore parent trade schedules or run a pure Python prescreen after claim clears; compare filtered and unfiltered parent at 5bps stress with train/OOS split.
next_command_when_clear: If no fresh claim exists, open a factor-local workdoc for an owned parent such as NQ compound or TSMOM carryover and test as a child filter.
status: idea_only
promotion_allowed: false
trade_usable: false
```

### commodity-term-structure-carry-filter-v1

```text
candidate_id: commodity-term-structure-carry-filter-v1
source: Gorton/Rouwenhorst commodity futures evidence plus Koijen/Moskowitz/Pedersen/Vrugt carry framework
source_type: paper
source_risk: info_only
why_now: Commodity and futures roots have many ORB/RVOL-style attempts; a term-structure or carry-state filter is structurally different and lower turnover.
regime_root: TrendExpansion
branch_path: TrendExpansion -> CommodityCarryState -> TermStructureContinuationFilter -> commodity_term_structure_carry_filter_v1
instrument/timeframe: CL/GC/SI/XAU or commodity ETFs, 1m entry origin when provider data exists, 1h/4h/1d trend context, daily term-structure/carry labels when available.
entry: No standalone entry at first. Allow parent trend continuation or pullback entries only when the commodity carry/term-structure state agrees with the 4h/1d trend.
confirmation: Realized volatility not in shock expansion, 1h trend not against the carry state, and session liquidity sufficient for the product.
exit/risk: Inherit parent fixed-RRR or multi-session hold; skip entries when carry state flips or becomes unavailable.
expected_holding_period: Multi-session preferred to amortize futures or ETF costs.
expected_cadence: 0.03 to 0.4 trades/session depending on product and parent root.
data_required: Continuous futures or ETF prices plus verified term-structure/carry source; if only front-month OHLCV exists, mark carry state unknown.
cost_model_required: Product-specific futures costs, multiplier, tick value, exchange/regulatory fees, or ETF broker/venue cost model.
duplicate_check: Not an agriculture/metals/oil ORB/RVOL rerun and not proof from prior SourceRootStopCarryLongHorizon artifacts.
known_failure_modes: Roll/term-structure data unavailable, stale carry labels around roll dates, ETF proxy drift, and sparse trade count after filtering.
first_gate1_shape: Start as source-only until carry data provenance is verified; then apply as a filter to a parent commodity trend branch rather than as standalone AQ launch.
next_command_when_clear: Search existing provider/material roots for verified roll or term-structure fields before any runtime claim.
status: blocked_by_runtime
promotion_allowed: false
trade_usable: false
```

### variance-risk-premium-stress-gate-v1

```text
candidate_id: variance-risk-premium-stress-gate-v1
source: Bollerslev/Tauchen/Zhou variance risk premia and existing VIX/VRP caution from local scripts
source_type: paper
source_risk: info_only
why_now: Existing VIX/VRP QQQ surfaces mean variance risk should be treated as a stress gate for parent trend/carry roots, not as a duplicate standalone alpha.
regime_root: TransitionRisk
branch_path: TransitionRisk -> VarianceRiskPremiumStress -> VixTermStructureGate -> variance_risk_premium_stress_gate_v1
instrument/timeframe: QQQ/SPY/NQ 1m parent entries with 1h/4h/1d volatility context and VIX/VIX3M or equivalent term-structure fields.
entry: No standalone entry. Permit long trend/carry parent entries only when VRP/term-structure is not in backwardated stress and realized volatility is not expanding against the position.
confirmation: Parent branch remains cost-positive before the gate, VIX term structure is known before entry, and cross-asset risk-off proxies do not contradict the trade.
exit/risk: Skip, de-risk, or reduce max hold during VRP stress; no gate relaxation.
expected_holding_period: Same as parent branch.
expected_cadence: Should reduce parent cadence and improve drawdown or return sanity, not raise trade count.
data_required: Parent trades plus VIX/term-structure or verified variance proxy aligned without lookahead.
cost_model_required: Same as parent; stress gate cannot compensate for unknown transaction costs.
duplicate_check: Do not rerun `run_vix_vrp_contango_pullback_yf_qqq_aq_v1.py` unchanged; use this as a child risk gate only.
known_failure_modes: VIX data unavailable for futures-only lanes, stress gate removes rebound winners, term-structure proxy delay, and false confidence from already-mined QQQ VRP rows.
first_gate1_shape: Rescore existing parent trade schedules by pre-entry VRP state, then open an owned child filter only if train/OOS improves after honest cost stress.
next_command_when_clear: Use as a child analysis packet for NQ compound or crossasset TSMOM, not a standalone fresh launch.
status: idea_only
promotion_allowed: false
trade_usable: false
```

## Practical Bias From This Addendum

- Prefer slow cross-asset state as a filter on an already cost-positive parent,
  not as a new high-turnover 1m signal.
- Do not treat prior carry artifacts as reusable proof. They only inform
  duplicate checks and failure modes.
- Any carry, term-structure, or VRP field must have source provenance and
  timestamp alignment before it can enter a Gate 1 screen.
- These candidates are future work only until the active claim clears and a
  proper factor-local workdoc plus claim exists.
