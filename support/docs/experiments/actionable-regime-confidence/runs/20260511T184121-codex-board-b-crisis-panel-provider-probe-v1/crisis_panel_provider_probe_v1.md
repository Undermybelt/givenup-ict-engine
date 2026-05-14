# Board B Crisis Panel Provider Probe v1

Run id: `20260511T184121+0800-codex-board-b-crisis-panel-provider-probe-v1`.

## Decision

- Gate result: `not_started:panel_probe_no_recipe_scored`
- Downstream: `not_started:no_rc_spa_passing_recipe`
- Next action: B2R-repeat: synthesize and score a second root-aware recipe on the broader source-panel/yfinance equity-index daily universe with per-instrument roots; treat IBKR/Kraken as recorded support/unhealthy paths, not as blockers, and do not run downstream promotion unless branch RC-SPA passes.
- Completion: `not_achieved`

## Provider Readback

| Provider | provider-status | harness fetch | Artifact |
|---|---|---|---|
| `yfinance` | `live_runtime:1/1 ready | market_data:1/1 ready` | `ok=1 error=0 stderr_bytes=0` | `docs/experiments/actionable-regime-confidence/runs/20260511T184121-codex-board-b-crisis-panel-provider-probe-v1/provider/harness-yfinance-qqq-1d.out` |
| `tradingview_mcp` | `market_data:1/1 ready` | `ok=1 error=0 stderr_bytes=0` | `docs/experiments/actionable-regime-confidence/runs/20260511T184121-codex-board-b-crisis-panel-provider-probe-v1/provider/harness-tradingview-qqq-1d.out` |
| `ibkr` | `market_data:0/1 ready` | `ok=0 error=1 stderr_bytes=904` | `docs/experiments/actionable-regime-confidence/runs/20260511T184121-codex-board-b-crisis-panel-provider-probe-v1/provider/harness-ibkr-qqq-1d.out` |
| `kraken_public` | `market_data:0/1 ready` | `ok=0 error=0 stderr_bytes=143` | `docs/experiments/actionable-regime-confidence/runs/20260511T184121-codex-board-b-crisis-panel-provider-probe-v1/provider/harness-kraken-xbtusd-1d.out` |

## Crisis Panel Coverage

- Source panel 2021-2025 by root: `{'Bear': {'rows': 12057, 'unique_dates': 1248, 'unique_tickers': 39}, 'Bull': {'rows': 21528, 'unique_dates': 1251, 'unique_tickers': 39}, 'Crisis': {'rows': 4646, 'unique_dates': 1162, 'unique_tickers': 39}, 'Sideways': {'rows': 10714, 'unique_dates': 1253, 'unique_tickers': 39}}`
- Dominant daily 2021-2025 by root: `{'Bear': 301, 'Bull': 846, 'Crisis': 8, 'Sideways': 100}`
- Local Auto-Quant data files: `40/40` readable; intervals `{'15m': 5, '1d': 12, '1h': 11, '4h': 11, '5m': 1}`
- yfinance full-history fetch ok symbols: `['^GSPC', '^IXIC', '^RUT', 'AAPL', 'AMD', 'AMZN', 'MSFT', 'NVDA', 'TSLA', 'XOM', 'JPM', 'BTC-USD']`
- yfinance full-history fetch failed symbols: `[]`

## Prompt-To-Artifact Checklist

| Requirement | Status | Evidence |
|---|---|---|
| Board B file remains the authoritative execution board. | `covered` | docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md |
| Profitability factors must emit root-first branch paths. | `covered_but_rejected` | Current board cursor and 183244 branch matrix preserve Bull/Bear/Sideways/Crisis branch rows. |
| Auto-Quant evidence must be real, not inferred. | `covered_for_prior_candidate` | Prior 183244 branch matrix has 5198 real Auto-Quant/Freqtrade rows; this probe does not create a recipe. |
| Downstream filter/BBN/CatBoost/execution-tree branch promotion must only happen after RC-SPA pass. | `blocked_correctly` | Current branch matrix failed RC-SPA; downstream remains fail-closed. |
| Use provider evidence from yfinance, TradingViewRemix, IBKR, and Kraken before declaring data blocked. | `covered` | {"harness": {"harness-ibkr-qqq-1d": {"error_count": 1, "ok_count": 0, "stderr_artifact": "docs/experiments/actionable-regime-confidence/runs/20260511T184121-codex-board-b-crisis-panel-provider-probe-v1/provider/harness-ibkr-qqq-1d.err", "stderr_bytes": 904, "stderr_excerpt": "ibkr-historical require |
| Broader crisis-capable panel must be available before another crisis-depth claim. | `available_for_next_recipe_but_not_yet_scored` | {"dominant_daily_2021_2025": {"Bear": 301, "Bull": 846, "Crisis": 8, "Sideways": 100}, "local_autoquant": {"by_interval": {"15m": 5, "1d": 12, "1h": 11, "4h": 11, "5m": 1}, "file_count": 40, "instruments": {"AAPL_USD": ["1d"], "AVAX_USDT": ["1d", "1h", "4h"], "BNB_USDT": ["1d", "1h", "4h"], "BTCY_US |
| Objective can be marked complete. | `not_achieved` | No branch has passed RC-SPA and no promoted branch path has completed downstream consumption. |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T184121-codex-board-b-crisis-panel-provider-probe-v1/crisis_panel_provider_probe_v1.json`
- Provider status directory: `docs/experiments/actionable-regime-confidence/runs/20260511T184121-codex-board-b-crisis-panel-provider-probe-v1/provider`
- Source panel counts: `docs/experiments/actionable-regime-confidence/runs/20260511T184121-codex-board-b-crisis-panel-provider-probe-v1/panel/source_regime_root_counts_v1.json`
- Local Auto-Quant feather summary: `docs/experiments/actionable-regime-confidence/runs/20260511T184121-codex-board-b-crisis-panel-provider-probe-v1/panel/local_autoquant_feather_summary.json`
- yfinance fetch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T184121-codex-board-b-crisis-panel-provider-probe-v1/panel/yfinance_panel_fetch_summary_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T184121-codex-board-b-crisis-panel-provider-probe-v1/checks/crisis_panel_provider_probe_v1_assertions.out`
