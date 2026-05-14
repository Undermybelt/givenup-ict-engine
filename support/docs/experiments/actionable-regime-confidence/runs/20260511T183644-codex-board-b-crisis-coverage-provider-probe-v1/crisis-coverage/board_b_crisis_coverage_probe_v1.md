# Board B Crisis Coverage Provider Probe v1

Run id: `20260511T183644+0800-codex-board-b-crisis-coverage-provider-probe-v1`.

## Decision

- Board state: `rejected`
- Gate result: `fail:no_new_auto_quant_recipe_scored`
- Downstream consumption: `not_started:blocked_by_missing_rc_spa_candidate`
- Stable profit score: `0`
- Primary blocker: current Auto-Quant/Freqtrade crypto evidence uses the `2021-2025` window, where the accepted Board A root schedule has only `8` dominant `Crisis` days. The local source label panel has `8` dominant `Crisis` days in the same period but `417` dominant `Crisis` days across `2000-2026`, so the bottleneck is the current tradeable panel/window, not the source-label corpus.

## Provider Readback

- `provider-status --agent`: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:2/7 ready`
- `yfinance`: ready for market data and live runtime.
- `tradingview_mcp`: ready.
- `ibkr`: gateway reachable but runtime dependencies missing.
- `kraken_public`: Python provider dependencies missing.
- `kraken_cli`: ready local runtime, but it does not resolve the current tradfi crisis-panel need.

## yfinance Fetch Readback

- `SPY` via `yfinance`: `208` rows, `2008-09-02T13:30:00Z` -> `2009-06-29T13:30:00Z`
- `QQQ` via `yfinance`: `208` rows, `2008-09-02T13:30:00Z` -> `2009-06-29T13:30:00Z`
- `^VIX` via `yfinance`: `208` rows, `2008-09-02T07:00:00Z` -> `2009-06-29T07:00:00Z`
- `GLD` via `yfinance`: `208` rows, `2008-09-02T13:30:00Z` -> `2009-06-29T13:30:00Z`
- `SPY` via `yfinance`: `1254` rows, `2021-01-04T14:30:00Z` -> `2025-12-30T14:30:00Z`
- `QQQ` via `yfinance`: `1254` rows, `2021-01-04T14:30:00Z` -> `2025-12-30T14:30:00Z`
- `^VIX` via `yfinance`: `1254` rows, `2021-01-04T08:00:00Z` -> `2025-12-30T08:00:00Z`
- `GLD` via `yfinance`: `1254` rows, `2021-01-04T14:30:00Z` -> `2025-12-30T14:30:00Z`

## Coverage Readback

- Source CSV rows: `245021`
- Source tickers: `39`
- Dominant Crisis days by useful older windows: `2000=72`, `2001=64`, `2002=80`, `2008=43`, `2009=90`, `2020=15`.
- Current Board A root schedule days by root: `{'Bear': 1364, 'Bull': 3887, 'Crisis': 385, 'Sideways': 923}`
- Current Board A root schedule days by root for `2021-2025`: `{'Bear': 298, 'Bull': 844, 'Crisis': 8, 'Sideways': 105}`

## Artifact Path Check

- Board current row referenced report exists: `True` at `docs/experiments/actionable-regime-confidence/runs/20260511T182222-codex-board-b-rootaware-multibranch-rc-spa-v1/branch-rc-spa/rootaware_multibranch_branch_rc_spa_report_v1.md`
- Actual dense readback report exists: `True` at `docs/experiments/actionable-regime-confidence/runs/20260511T183030-codex-board-b-rootaware-dense-readback-v1/branch-rc-spa/rootaware_multibranch_branch_rc_spa_report_v1.md`

## Next

B2R-repeat: convert the broader `2000-2020` tradfi crisis panel into an Auto-Quant-compatible backtest input, or select a recipe that can trade older crisis windows before any downstream branch promotion.
