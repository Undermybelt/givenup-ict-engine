# IBKR options/profit-factor timeframe ladder to tree handoff

Session lesson from an ict-engine options-profit-factor iteration using Auto-Quant and structural tree handoff.

## Durable pattern

When the user asks to widen the time window and run one-minute-up timeframes:

1. Prefer IBKR data first, using the largest feasible window per timeframe.
2. Treat each timeframe as its own Gate 1 lane; do not mix vectorized diagnostics with Auto-Quant results.
3. If a longer IBKR request times out for a timeframe/symbol, downgrade the window for that lane and keep running other feasible lanes.
4. Promote only the strongest Auto-Quant-passing candidate into the structural path tree.
5. For practical options/profit-factor work, test slippage/cost early; 5m alpha can disappear at 2bps/side.
6. If a higher-timeframe candidate survives cost and repeats across sibling symbols, it can be more useful than denser 1m/5m rows.

## Concrete candidate pattern observed

A 30m MACD breakout branch over IBKR-fed US equity/ETF OHLCV survived where lower-timeframe micro edges were fragile.

Observed branch shape:

- timeframe: 30m
- signal: MACD line crosses above signal line, histogram expanding, price breaking recent high, realized-volatility gate not too stretched
- target: +2.5%
- stop: -2.5%
- max hold: 24 bars
- cost stress used: 2bps/side
- symbols in passing packet: NVDA, QQQ, IWM, XLK

Observed aggregate packet:

- 17 trades
- 17 wins / 0 losses
- PF capped/reported as 999
- Sharpe about 6.6
- combined profit about +25%

Do not over-promote this exact branch from the chat numbers alone: it reached structural visibility but not full production maturity because validation rows were below the 30-row gate.

## Structural handoff recipe

After Auto-Quant Gate 1 passes:

1. Export the strategy library as an Auto-Quant agent material.
2. Run `auto-quant-agent-material-batch` against the local Auto-Quant checkout when available.
3. Rank the resulting material and preserve the authoritative `ranking[]` artifact.
4. Export real trades JSONL from the passing ranked strategy.
5. Apply the trades through the ict-engine Auto-Quant real-trade ledger.
6. Export the structural path ranking target after analyze.
7. Train/apply scores to the current post-analyze target; prefer history mode if direct target rows are too few.
8. Enable/register runtime scoring and rerun analyze/workflow/policy readback.
9. Check all maturity gates before claiming live-readiness.

## Gate language

Use this wording:

- `tree handoff complete` when the candidate is ingested and visible to the structural path ranking runtime.
- `candidate only` when raw scored rows are below production/observation validation thresholds.
- `not live-ready` until `raw_scored_mature`, `production_validation`, and `observation_validation` meet the gate, typically 30/30 or better.

Example from this session:

- raw_scored_mature = 17/30
- production_validation = 17/30
- observation_validation = 17/30
- runtime_selection = enabled_history_ready
- runtime_mode = prefer_history

Correct conclusion: tree handoff succeeded, but sample maturity remained short by 13 rows.

## Pitfalls

- Do not call IBKR timeout a factor failure. It is a provider-window downgrade.
- Do not let a lower-timeframe scan dominate if cost stress kills it.
- Do not claim CatBoost/tree promotion from visibility alone; row maturity and exact branch admission still matter.
- Avoid pandas dot-access for columns named like methods/attributes (`df.hist`); use bracket access (`df["hist"]`).
