# A9 TradingView-Style Formula Recipes

Loop id: `20260510T205000+0800-hermes-a9-tv-formula-recipes`

Objective: normalize TradingView/Pine-style regime formulas into auditable,
non-leaky feature recipes without trusting script profitability.

Inputs:
- Research note:
  `docs/market-regime-profitable-strategy-research-2026-05-10.md`
- Base cross-market feature table:
  `docs/experiments/actionable-regime-confidence/runs/20260510T202359-hermes-cross-market-regime-validation/cross-market/cross_market_regime_features_and_labels.csv`
- Provider status source:
  `docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/provider/provider-status-agent.json`

Method:
- No live TradingView data was trusted; TradingView MCP remains fail-closed.
- No TradingView script PnL, strategy equity curve, or backtest claim was used.
- Formula ingredients were normalized into ADX/DMI, ATR percentile, MA
  slope/spread, RSI, volatility percentile, and Bollinger bandwidth features.
- Missing regimes searched: `TrendExpansion`, `ExtremeStress`,
  `ReversalBrewing`.

Result:
- Accepted 95 candidates for missing regimes: 0.
- Accepted 99 candidates for missing regimes: 0.
- Existing accepted coverage remains 3/6:
  `SessionLiquidityCoreViable`, `RangeConsolidation`,
  `ThinLiquidityOffHoursPersistent`.

Artifacts:
- `recipes/tradingview_formula_recipe_manifest.json`
- `recipes/a9_tv_formula_features.csv`
- `recipes/a9_tv_formula_candidate_report.json`
- `recipes/a9_tv_formula_candidate_rules.csv`
- `evidence_packet_a9_tv_formula_recipes.json`
- `checks/a9_tv_formula_recipe_assertions.out`
- `recipes/a9_tv_formula_recipe_search.py`
