# Board B Main-Root Context Pivot v1

Run id: `20260511T151028+0800-codex-board-b-main-root-context-pivot-v1`.

## Decision

- Accepted Board A input for Board B: `BoardA_market_regime_context_MainRegimeV2_price_roots4`.
- Board A artifact: `docs/experiments/actionable-regime-confidence/runs/20260511T144838-codex-market-regime-context-packet-v1/market-regime-context/market_regime_context_packet_v1.json`.
- Main price roots: `Bull`, `Bear`, `Sideways`, `Crisis`.
- Child/provenance labels such as `BullExpansion`, `BearExpansion`, `ConsolidationBalance`, `CrisisDislocation`, `TrendExpansion`, or `RangeConsolidation` are not accepted Board B parent-regime inputs.
- Board B may now select one Auto-Quant recipe and score regime-conditioned win rate / RC-SPA against the Board A `market_regime_context`.
- No Auto-Quant recipe is selected in this pivot.
- Full execution promotion remains blocked until a recipe passes RC-SPA and downstream pre-Bayes, BBN, CatBoost/path-ranker, and execution-tree checks.

## Source Panel Readback

Source panel: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv`.

- Rows: `245021`.
- Date range: `2000-01-03` to `2026-01-30`.
- Tickers: `39`.
- Root label counts: `Bull=103766`, `Sideways=56668`, `Bear=54939`, `Crisis=29632`.
- Residual label: `High-volatility=16`; residual only, not a main root.

## Next

- Select exactly one Auto-Quant recipe.
- Evaluate it under `BoardA_market_regime_context_MainRegimeV2_price_roots4`.
- Report net-return win rate, fold consistency, trade depth, costs/slippage stress, PBO/DSR, tail loss, regime specificity, RC-SPA, and downstream consumption state.
- Do not return to child/sub-regime proof as a substitute for main price roots.
