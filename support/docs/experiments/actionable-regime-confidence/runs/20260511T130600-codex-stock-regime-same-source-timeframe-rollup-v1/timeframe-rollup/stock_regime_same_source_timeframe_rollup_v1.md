# Stock Regime Same-Source Timeframe Rollup v1

Run ID: `20260511T130600+0800-codex-stock-regime-same-source-timeframe-rollup-v1`

## Result

- Materialized same-source labels: `44396`.
- By root: `{'Bear': 10021, 'Bull': 21314, 'Crisis': 5119, 'Sideways': 7942}`.
- By timeframe: `{'1mo': 5200, '1w': 39196}`.
- Timeframes: `1w`, `1mo`.
- Full objective gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.

## Policy

This is not another S&P source-window projection. It rolls the confirmed daily stock-market-regimes parent-label panel into weekly/monthly labels for the same tickers only.

## Guardrails

- No confidence gate claimed in this run.
- Low-consensus periods are abstained.
- No runtime code changed; no thresholds relaxed; no raw data committed.

## Artifacts

- `stock_regime_same_source_timeframe_rollup_v1.json`
- `stock_regime_same_source_timeframe_rollup_v1.csv`
- `../checks/stock_regime_same_source_timeframe_rollup_v1_assertions.out`
