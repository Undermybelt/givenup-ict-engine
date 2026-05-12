# Board B Recipe Selection v1

Run id: `20260511T151712+0800-codex-board-b-recipe-selection-v1`.

## Decision

- Selected recipe: `CrashRebound`.
- Accepted regime input: `BoardA_market_regime_context_MainRegimeV2_price_roots4`.
- Recipe source artifact: `docs/experiments/actionable-regime-confidence/runs/20260510T191144-board-b-factor-research-mtf1h/ict-engine/auto_quant_strategy_library.measured.json`.
- Auto-Quant timeframe: `1h`.
- Pairs: `SOL/USDT`, `AVAX/USDT`, `BNB/USDT`.
- Aggregate existing metrics: `trades=207`, `win_rate_pct=68.599`, `total_profit_pct=55.69`, `profit_factor=1.4161`, `max_drawdown_pct=-11.3086`, `sharpe=0.2903`.
- Selection rationale: among the inspected local Auto-Quant candidates, this is the highest-win-rate positive-return recipe with at least `100` trades.

## Inspected Candidates

| Recipe | Timeframe | Pairs | Trades | Win Rate % | Profit % | Profit Factor | Selection |
|---|---|---|---:|---:|---:|---:|---|
| `CrashRebound` | `1h` | `SOL/USDT,AVAX/USDT,BNB/USDT` | 207 | 68.599 | 55.69 | 1.4161 | selected |
| `PerPairMR` | `1h` | `BTC/USDT,ETH/USDT,BNB/USDT,SOL/USDT,AVAX/USDT` | 519 | 58.1888 | 35.78 | 1.1981 | runner_up |
| `VolBreakoutSized` | `1h` | `BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,AVAX/USDT` | 1221 | 32.8419 | 25.02 | 1.4751 | lower_win_rate |
| `TomacNQ_ScratchNoRSINoConflict15m` | `15m` | `NQ/USD` | 1081 | 31.4524 | -10.8816 | 0.9016 | rejected_negative_edge |
| `TomacNQ_KillzoneBreakout` | `1h` | `QQQ/USD` | 74 | 52.7027 | 6.98 | 1.2501 | rejected_thin_trades |

## Guardrails

- `CrashRebound` is a recipe selection, not a profitability pass.
- Its `expected_regime=reversal_or_rebound_after_drawdown` is child/provenance language and must not be promoted to a parent root.
- The next gate must condition the recipe by Board A main price roots: `Bull`, `Bear`, `Sideways`, and `Crisis`.
- RC-SPA is still uncomputed because fold metadata, net cost/slippage stress, PBO, DSR, tail-loss, and root-specificity matrix are not present in the measured library summary.

## Next

- Consume or rerun the `CrashRebound` backtest with trade/fold-level outputs.
- Compute root-conditioned win rate and edge by `Bull`, `Bear`, `Sideways`, and `Crisis`.
- Compute RC-SPA hard gates before any downstream promotion.
