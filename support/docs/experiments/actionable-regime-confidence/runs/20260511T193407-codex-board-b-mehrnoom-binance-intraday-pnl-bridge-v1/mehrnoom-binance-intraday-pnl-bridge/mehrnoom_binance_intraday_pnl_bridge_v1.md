# Mehrnoom Binance Intraday PnL Bridge v1

Run ID: `20260511T193407+0800-codex-board-b-mehrnoom-binance-intraday-pnl-bridge-v1`

## Decision

- Gate result: `diagnostic_only:intraday_rows_reconstructed_but_no_positive_edge_vs_controls`
- Positive direct-event rows: `3211`
- Same-coin control rows: `3211`
- Monthly folds: `13`
- Source-buy mean return: `0.047165`
- Provider-open positive mean return: `0.000756`
- Provider-open control mean return: `0.020499`
- Edge vs controls: `-0.019742`
- Promotion allowed: `False`

## Interpretation

- This repairs the previous all-zero direct scoped `Manipulation` PnL-input blocker only as an additive bridge: source Telegram buy levels are used for entry alignment, and Binance public 1h candles provide intraday exits.
- It does not promote downstream because this run is not a full RC-SPA candidate across all required roots, and it has not passed Pre-Bayes, BBN, CatBoost/path-ranker, or execution-tree consumption.
- Rows with source buy levels that do not align to the provider entry open are rejected instead of coerced.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T193407-codex-board-b-mehrnoom-binance-intraday-pnl-bridge-v1/mehrnoom-binance-intraday-pnl-bridge/mehrnoom_binance_intraday_pnl_bridge_v1.json`
- Rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T193407-codex-board-b-mehrnoom-binance-intraday-pnl-bridge-v1/mehrnoom-binance-intraday-pnl-bridge/mehrnoom_binance_intraday_pnl_rows_v1.csv`
- Symbol coverage CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T193407-codex-board-b-mehrnoom-binance-intraday-pnl-bridge-v1/mehrnoom-binance-intraday-pnl-bridge/mehrnoom_binance_symbol_coverage_v1.csv`
- Provider probe JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T193407-codex-board-b-mehrnoom-binance-intraday-pnl-bridge-v1/mehrnoom-binance-intraday-pnl-bridge/mehrnoom_binance_provider_probe_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T193407-codex-board-b-mehrnoom-binance-intraday-pnl-bridge-v1/checks/mehrnoom_binance_intraday_pnl_bridge_v1_assertions.out`

## Next

- Use these intraday provider-reconstructed direct rows only as scoped Manipulation bridge input; run full branch RC-SPA and downstream checks only if combined root branches pass without relaxed gates.
