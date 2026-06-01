# IBKR cross-asset vol/gamma/IV/OI/Greeks proxy AQ run

Use when the user asks to try Auto-Quant on IBKR across index futures, gold futures, and US stocks with volatility, gamma-wall, IV, open-interest, and Greeks-style profitability factors.

## Durable pattern

1. Keep scope broad but truth-label each evidence class:
   - Futures TRADES: real IBKR historical bars.
   - Stocks TRADES: real IBKR historical bars.
   - Stock HV/IV: real IBKR `HISTORICAL_VOLATILITY` and `OPTION_IMPLIED_VOLATILITY` daily series.
   - Futures IV/OI/Greeks: not available through current `fetch_external.py ibkr-historical`; use only realized-vol, round-level gamma-wall proxy, volume/count OI proxy, and Black-Scholes delta/gamma proxy unless a separate chain/market-data surface is wired.
2. Use `/tmp/...` run roots and a `/tmp/ict-engine-agent-claims/board-b-factor-refinement/...` claim before long Board B work.
3. For multi-asset Tomac/FreqTrade, prepare one synthetic pair per asset (`ES/USD`, `NQ/USD`, `GC/USD`, `SPY/USD`, etc.) and set `max_open_trades` high enough for concurrent assets.
4. If `analyze` needs one symbol, build a synthetic basket JSON from fetched bars for `--data-htf/--data-mtf/--data-ltf`; this lets the imported AQ evidence pass into BBN/ranker/execution while preserving separate per-pair AQ metrics in `strategy_library.json`.
5. Run CatBoost trainer even when target labels are immature; register the JSON `trainer_artifact.json` if registering the binary `.cbm` path fails due UTF-8 parsing. Keep `score_model_artifact_uri` pointing to the `.cbm` via the scores file.
6. Final decision remains fail-closed unless execution tree and validation both mature: `transition_guardrail/observe` or `raw_scored_mature=0/30` means incubate, not promote.

## Example evidence shape from the 2026-05-17 run

Run root:
`/tmp/ict-engine-ibkr-crossasset-vol-gamma-iv-oi-greeks-20260517`

Provider rows:
- ES/NQ/GC futures 5m: 2760 rows each.
- SPY/AAPL/NVDA stocks 5m: 1920 rows each.
- SPY/AAPL/NVDA stock HV/IV daily: about 250 rows each.

Tomac aggregate:
- trades=188
- total_profit_pct=3.22
- sharpe=32.9413
- profit_factor=1.4259
- max_drawdown_pct=-1.4477

Per pair:
- GC/USD: trades=27, profit=0.84%, PF=2.16
- ES/USD: trades=46, profit=0.69%, PF=2.34
- SPY/USD: trades=18, profit=0.49%, PF=2.22
- NVDA/USD: trades=33, profit=0.81%, PF=1.21
- AAPL/USD: trades=20, profit=0.28%, PF=1.25
- NQ/USD: trades=44, profit=0.12%, PF=1.11

Downstream:
- `auto-quant-results-import`: `n_ok=7`
- BBN: `evidence_value_gate_passed=true`, entropy/log-loss improved.
- CatBoost: model trained/applied; runtime enabled as `enabled_candidate_set_ready`.
- Execution: still `observe/transition_guardrail/guarded`.
- Ranker validation: `raw_scored_mature=0/30`, `production_validation=0/30`, `observation_validation=0/30`.

Decision:
`incubate_fail_closed`. Useful next cut is single-asset refinement on `GC` and `ES`; do not promote the aggregate.