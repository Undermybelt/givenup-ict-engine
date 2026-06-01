# 2026-05-20 regime-rooted 1m cost-density lesson

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use under `ict-engi-fact-rese-muta` for future ict-engine profitability-factor training runs.

## User preference reinforced
- Start from a regime-rooted branch: `market -> product -> symbol -> timeframe -> main_regime -> sub_regime... -> first_profit_factor -> overlay_profit_factor...`.
- A main/sub-regime may branch to another sub-regime or first profit factor; a profit factor may only branch to later profit factors.
- Filtering, Pre-Bayes/BBN, CatBoost, execution tree, and feedback must preserve the same regime-rooted path.
- Default start is 1m when feasible, with widest practical provider windows and 5m/15m/30m/1h/4h/1d context where available.
- Do not lower gates to force pass. Only retain factors with real-cost density, AQ-to-downstream directional agreement, `transition_hazard < 0.60`, `pda_hybrid_alignment=true`, and stable `execution_readiness >= 0.65`.

## Session evidence
Two fresh IBKR 1m Gate-1 candidate classes were run after a YF QQQ cache-replay candidate failed:

1. `ibkr_mnq1m_vwap_bollinger_snapback_7d_gate1_v1`
   - Branch: `FUTURES -> equity_index -> MNQ -> 1m -> RangeReversion -> VwapBollingerSnapback -> ibkr_mnq1m_vwap_bollinger_snapback_7d_gate1_v1`
   - Data: 9269 MNQ 1m rows; `local_cache_replay=false_fresh_ibkr_fetch_from_same_session`.
   - Result: 3 variants, 24 trades total. Each variant had 8 trades, raw +0.11%, but failed after 1bps/2bps/5bps per side.
   - Decision: drop/block before downstream.

2. `ibkr_futures_liquidity_sweep_vwap_reclaim_1m_gate1_v1`
   - Branches:
     - `FUTURES -> equity_index -> MES -> 1m -> RangeReversion -> LiquiditySweepReclaim -> ibkr_futures_liquidity_sweep_vwap_reclaim_1m_gate1_v1`
     - `FUTURES -> equity_index -> MNQ -> 1m -> RangeReversion -> LiquiditySweepReclaim -> ibkr_futures_liquidity_sweep_vwap_reclaim_1m_gate1_v1`
     - `FUTURES -> precious_metals -> MGC -> 1m -> RangeReversion -> LiquiditySweepReclaim -> ibkr_futures_liquidity_sweep_vwap_reclaim_1m_gate1_v1`
   - Data: fresh IBKR rows MES=8978, MNQ=8978, MGC=8979; `local_cache_replay=false`.
   - Result: 9 variants, 432 trades total. Dense/high-frequency reclaim produced enough trades but not enough per-trade edge; all variants failed 2bps and 5bps cost stress.
   - Decision: drop/block before downstream.

## Durable lesson
High-frequency 1m reclaim/snapback candidates can show attractive raw Sharpe and density while being purely cost-fragile. Treat raw-positive, high-trade-count, sub-1bps-edge 1m candidates as observation only until cost stress survives.

## Next search bias
After repeated thin-edge 1m failures, prefer candidates with fewer but thicker moves:
- short-side exhaustion/fade,
- failed breakout/fakeout with wider excursion,
- volatility expansion reversal,
- range-bound snapback with explicit minimum excursion/ATR target,
- cross-instrument relative-value dislocation with wider expected move.

Avoid spending more iterations on dense VWAP reclaim or Bollinger snapback variants unless the entry includes a minimum expected move large enough to survive realistic cost.

## Reporting requirement
Final report should state:
- exact branch path,
- provider rows and cache/fresh marker,
- covered/missing timeframes,
- raw vs 1/2/5bps cost stress,
- downstream gate booleans,
- whether the candidate is promotion/trade usable,
- if blocked, the next executable candidate shape.
