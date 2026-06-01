# Options-proxy Auto-Quant practicalization

Session pattern captured from an ict-engine factor iteration on NQ option-profit proxies.

## When to use
- User asks to turn option/volatility ideas into practical trading factors.
- Historical option chain, OI, Greeks, true IV/HV, GEX, or 0DTE flow are unavailable.
- Existing Auto-Quant / tree workflow still needs real trade-like rows and structural path feedback.

## Research-to-signal translation
Do not fabricate unavailable options fields.

Durable proxy ladder:
1. VRP / IV-RV compression proxy
   - Use realized volatility compression from retained OHLCV when VIX/VXN sidecars are missing.
   - Name output explicitly as `*_proxy`, not real IV/HV.
2. Short-vol carry behavior proxy
   - Prefer calm or non-expanding volatility, not raw low volatility only.
   - Example gate: `rv_fast(12) < rv_slow(72) * k` plus ATR percentile ceiling.
3. MACD/reclaim trigger for density
   - Options-proxy gates alone often produce no trades.
   - Use a dense, simple entry trigger first, then apply option-vol proxy as a risk gate.
4. Practical execution overlay
   - Sweep target, stop, hold time, and session window after signal density is proven.
   - Treat all higher timeframes that fail PF/sample gates as discarded siblings, not partial wins.

## Practical candidate pattern
For NQ 5m retained data, a useful starting family was:
- `close > EMA34 > EMA89`
- MACD crosses above signal and histogram rises
- RSI bounded, e.g. 38..76
- `rv_fast(12) < rv_slow(72) * 1.6`
- ATR percentile/rank below a ceiling, e.g. < 0.95
- volume > 0

Then sweep execution overlays:
- target: 0.25% / 0.35% / 0.45% / 0.60%
- stop: -0.60% / -0.80% / -1.00% / -1.40%
- max hold: 6 / 12 / 24 bars
- sessions: all, US extended, RTH

Strong practical candidates should show:
- at least 30 trades in the window
- PF > 1.3
- positive months in most/all months
- drawdown materially below raw return
- slippage sensitivity still acceptable

## Auto-Quant parity pitfall
If Freqtrade/Auto-Quant reports zero trades but a local vectorized diagnostic shows many signals:
1. Run a minimal always-long smoke strategy on the same pair/timeframe/config.
2. If always-long also returns zero trades, suspect adapter/config/pair/data-contract parity, not the factor.
3. Preserve the AQ attempt as evidence, but label any pandas/vectorized runner as `proxy` or `candidate-discovery` until full AQ parity is restored.
4. Do not call the pandas run a clean Auto-Quant pass; it can still be ingested as real-trade-like feedback only if clearly labeled by provider/source.

## Tree handoff discipline
When proxy rows are ingested:
- Check `structural_path_ranking_runtime.ready`.
- Check `raw_scored_mature`, `production_validation`, and `observation_validation` against the minimum row count.
- If analyze gate is `pass_neutralized` or `promotion_allowed=false` because of market policy/liquidity penalty, report it exactly; do not overstate promotion.
- Keep `state` and `state2` clean if a prior interrupted run corrupted update ledgers.

## Completion language
Good final wording:
- "5m branch is candidate; higher timeframes discarded."
- "Tree runtime ready, but promotion blocked/neutralized by policy."
- "Next required check: walk-forward and slippage sensitivity."

Bad final wording:
- "Real options GEX/0DTE factor passed" when no chain/OI/Greeks existed.
- "Auto-Quant passed" when the actual Freqtrade path returned zero trades and pandas proxy was used.
