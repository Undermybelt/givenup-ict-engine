# Regime-rooted live-ready factor gate

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use this when continuing ICT Engine profitability-factor training after a session where the operator requires regime-rooted branches and fail-closed promotion discipline.

## Branch contract

A profitability branch must preserve the full rooted path as first-class data through Auto-Quant, Pre-Bayes/filter, BBN, CatBoost/path-ranker, and execution tree:

```text
<market> -> <product> -> <instrument> -> <timeframe> -> <main_regime> -> <sub_regime> -> <profit_factor> -> <overlay_profit_factor>...
```

For older four-part materials, keep compatibility fields too:

- `branch_path`
- `regime_profit_branch_path`
- `main_regime`
- `sub_regime`
- `sub_sub_regime_or_profit_factor`
- `profit_factor`
- provider / symbol / timeframe provenance

## Operator narrowing: trend-only first

2026-05-25 operator correction:

- Prefer trend-following profitability factors only for fresh Board B lanes.
- Treat multi-timeframe resonance as part of the trend definition, not as an optional decoration.
- Keep the root as canonical regime first, usually `TrendExpansion -> <trend subtype> -> <trend profit factor> -> ...`.
- Use `1m` as the entry/origin frame when available, while `5m/15m/30m/1h/4h/1d` act as resonance, veto, or context frames.
- Countertrend, reclaim, washout, and mean-reversion shapes are not fresh default lanes; use them only as protective filters or as exact same-root repairs for already retained evidence.
- Auto-Quant is useful but not mandatory for every validation step. If IBKR simulated/paper evidence is available for the same rooted trend branch, it may be used as Gate 2 execution/latency/slippage feedback after Gate 1 learning viability is proven.
- IBKR simulation does not bypass downstream gates and never makes `promotion_allowed=true` or `trade_usable=true` by itself.

## Gate discipline

Do not run downstream just to create activity. First prove Gate 1:

- real provider rows, not cache replay unless explicitly labeled `cache_replay=true`
- 1m origin when available
- widest feasible window
- attempt `1m/5m/15m/30m/1h/4h/1d`
- sufficient trade density, roughly 1-3 trades/day target after filtering
- positive after realistic costs
- branch fields preserved in AQ rank rows

If Gate 1 or cost gate fails, stop and mark observation/drop. Do not lower thresholds.

## Live-ready promotion floor

Only keep as candidate for live-ready promotion when all are true:

- true cost-adjusted profitability remains positive
- AQ -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree direction agrees
- `transition_hazard < 0.60`
- `pda_hybrid_alignment=true`
- `execution_readiness >= 0.65`
- path-ranker visible and used by execution tree
- CatBoost/runtime validation ready
- mature/training rows are sufficient for the relevant promotion claim

If any fails, report it as observation/incubate, not trade-usable.

## Session pattern captured

Two fresh TradingViewMCP AQ Gate 1 runs were useful despite failing:

- SPY first30->last30 covered `1m/5m/15m/30m/1h` with real TVR rows, but AQ produced zero trades; stop before downstream.
- XRT ORB/RVOL/VWAP covered full ladder `1m/5m/15m/30m/1h/4h/1d`, but all AQ rows were negative after costs; stop before downstream.

A stronger existing CRWD 5m PDA/MTF soft-confirmation branch showed the desired downstream shape:

- cost survives 2bps and 5bps per side
- `execution_readiness=0.67`
- `transition_hazard=0.5950369253623637`
- `pda_hybrid_alignment=true`
- path-ranker visible/used and validation-ready
- still not promotable because `mature_rows=3 < 30`

Next training should prioritize increasing mature rows for the same strong root/overlay branch, not spawning unrelated novelty branches.
