# Factor Source Intake: Trend Reserve While Runtime Blocked

created_at: 2026-05-29T23:56:16+0800
owner: codex
status: source_intake_only
trigger: fresh active claim `20260529T234824+0800-codex-nq-compound-cross-engine-repair.claim` blocked new launch work
promotion_allowed: false
trade_usable: false
update_goal: false

## Boundary

This packet is waiting-window knowledge reserve only. No Auto-Quant, Freqtrade,
TOMAC, IBKR, provider-status, `fetch_external.py`, clone, installer, or external
repo code was executed. Sources below are idea inputs, not trading evidence.

## Sources Read

- arXiv `2201.06635`: `Optimal trend following portfolios`.
- arXiv `1404.3274`: `Two centuries of trend following`.
- arXiv `1410.8409`: `Optimal Allocation of Trend Following Strategies`.
- Crossref DOI `10.1002/fut.22053`: `Time-series momentum in China's commodity futures market`.
- GitHub search result `bideeen/Building-A-Trading-Strategy-With-Python`: tutorial-style momentum, moving-average crossover, and Turtle trading description.

## Candidate Reserve

### candidate_id: cross_asset_trend_risk_parity_virtual_assets_v1

source: arXiv `2201.06635`, arXiv `1410.8409`
source_risk: info_only
regime_root: `TrendExpansion -> CrossAssetTrendAllocation -> CorrelationAwareRiskParity`
branch_path: `FUTURES -> index/metals/rates/fx basket -> 1h/4h/1d -> TrendExpansion -> CrossAssetTrendAllocation -> CorrelationAwareRiskParity -> cross_asset_trend_risk_parity_virtual_assets_v1`
instrument/timeframe: ES/NQ/YM plus lower-cost or less-correlated futures where retained clean 1h/4h/1d exists; 1m only for execution timing, not alpha origin.
entry: long/short sign from medium/long lookback return or EMA slope; position scaled by inverse realized volatility and correlation cluster.
exit/risk: rebalance at 1d or 4h boundary; ATR/volatility stop; no overlapping correlated over-betting.
data_required: clean multi-instrument futures ladder with enough 1h/4h/1d history; verified roll-adjustment and return sanity.
cost_model_required: product-specific per-contract futures commission/exchange/regulatory plus slippage; 5bps/side may be a stress screen only.
duplicate_check: adjacent to prior NQ TSMOM and YM Donchian/TSMOM lanes, but distinct because allocation/correlation is the factor root, not single-symbol cadence lift.
expected_gate1: python_prescreen_ready after multi-instrument retained data audit; likely better for cost wall because turnover is daily/4h not 1m.
status: python_prescreen_ready
next_command_when_clear: create new `/tmp` workdoc/claim, audit retained multi-instrument 1h/4h/1d coverage, then run local pandas prescreen only.
promotion_allowed: false
trade_usable: false

### candidate_id: short_trend_wither_filter_long_trend_only_v1

source: arXiv `1404.3274` summary notes long trend stability and shorter trend degradation.
source_risk: info_only
regime_root: `TrendExpansion -> LongHorizonTrendPersistence -> ShortTrendWitherFilter`
branch_path: `FUTURES -> NQ/YM/ES -> 1m execution + 4h/1d alpha -> TrendExpansion -> LongHorizonTrendPersistence -> ShortTrendWitherFilter -> short_trend_wither_filter_long_trend_only_v1`
instrument/timeframe: NQ/YM/ES retained futures; 4h/1d signal, 1m execution timing.
entry: only trade when 4h and 1d trend agree and short-window trend is not the only support; reject isolated 1m/5m breakouts.
exit/risk: multi-day fixed RRR bracket or volatility trail; single-slot per instrument.
data_required: 4h/1d clean history plus 1m execution rows; no-lookahead merge_asof shifted context.
cost_model_required: futures product-specific cost; explicit slippage model.
duplicate_check: avoids unchanged Donchian, Dual Thrust, opening-drive, and short intraday momentum; related to TSMOM but adds a hard `short_trend_wither` exclusion.
expected_gate1: candidate for NQ cost wall repair; should first screen sparse but high-payoff trades, then add instruments for cadence.
status: python_prescreen_ready
next_command_when_clear: local pandas prescreen on NQ/YM/ES 4h/1d alpha with 1m execution, enforcing non-overlap.
promotion_allowed: false
trade_usable: false

### candidate_id: commodity_like_monthly_tsmom_micro_contract_probe_v1

source: Crossref DOI `10.1002/fut.22053` summary: commodity futures TSMOM, best 1-month lookback and 1-month holding in the cited market.
source_risk: info_only
regime_root: `TrendExpansion -> CommodityLikeMonthlyTsmom -> MicroContractProbe`
branch_path: `FUTURES -> MGC/MCL/MES/MNQ -> 1d alpha -> TrendExpansion -> CommodityLikeMonthlyTsmom -> MicroContractProbe -> commodity_like_monthly_tsmom_micro_contract_probe_v1`
instrument/timeframe: micro futures with verified IBKR or retained daily bars; 1d origin, optional 1h/4h execution context.
entry: sign of prior 21 trading day return, held up to 21 trading days; optional volatility targeting.
exit/risk: monthly rebalance, hard stop only if volatility shock exceeds historical threshold.
data_required: product-specific continuous/roll-adjusted daily data and contract metadata; retained 1d may be insufficient for ES/MNQ/M2K if decimated.
cost_model_required: official per-contract micro futures cost and slippage by product.
duplicate_check: distinct from 1m Donchian/Turtle and NQ multi-day TSMOM because it is monthly commodity-like horizon and product-cost probe.
expected_gate1: idea_only until daily data and cost model are verified; likely low turnover.
status: paper_only
next_command_when_clear: verify daily data provenance and official cost model first, then decide whether to code.
promotion_allowed: false
trade_usable: false

### candidate_id: turtle_breakout_with_short_trend_decay_guard_v1

source: GitHub `bideeen/Building-A-Trading-Strategy-With-Python` description of Turtle trading plus arXiv long/short trend decay distinction.
source_risk: info_only
regime_root: `TrendExpansion -> TurtleBreakout -> ShortTrendDecayGuard`
branch_path: `FUTURES -> NQ/YM/ES -> 1m execution + 1h/4h context -> TrendExpansion -> TurtleBreakout -> ShortTrendDecayGuard -> turtle_breakout_with_short_trend_decay_guard_v1`
instrument/timeframe: NQ/YM/ES if retained 1m plus context is dense; avoid ES/MNQ/M2K decimated 1m if coverage audit fails.
entry: 20-day high/low breakout only when 4h/1d long trend agrees and recent 1m/5m overextension has cooled.
exit/risk: 10-day channel exit or fixed RRR bracket; single active position per instrument.
data_required: clean daily channel plus dense 1m execution; shifted context only.
cost_model_required: product-specific futures cost; do not assume universal 5bps as real cost.
duplicate_check: many Donchian/Turtle lanes exist; this is only acceptable if exact duplicate check proves no same market/product/timeframe/root with the decay guard.
expected_gate1: blocked_by_duplicate_check until exact claim/run-root search is narrowed.
status: blocked_by_runtime
next_command_when_clear: run exact duplicate matrix first; skip if unchanged Donchian/Turtle evidence already covers it.
promotion_allowed: false
trade_usable: false

## Immediate Use

If the current active NQ compound cross-engine repair remains fresh, continue
source intake instead of launching. If it clears, the strongest non-duplicate
candidate above is `cross_asset_trend_risk_parity_virtual_assets_v1` because it
directly addresses the observed NQ cost wall and cadence/breadth problem without
shortening holds.
