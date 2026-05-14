# Auto-Quant Synthetic Market Map Probe v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T023920-codex-autoquant-synthetic-market-map-backtest-probe-v1`

Purpose: read back the previously running Auto-Quant probe and classify whether it can advance Board B `B2R-repeat-next`.

## Command Evidence

- `00_auto_quant_status_before.exit=0`
- `01_auto_quant_run_synthetic_market_map.exit=0`
- `02_auto_quant_status_after.exit=0`
- Auto-Quant status before and after: `dependency_ready_data_ready`
- Auto-Quant pinned commit: `34ba6b6ee6aa69813a50a72158d4c089d97afb96`
- Auto-Quant backtests: `12` succeeded, `0` failed

The run used `scripts/sitecustomize.py` to inject synthetic spot market metadata for `BTC/USDT`, `ETH/USDT`, `SOL/USDT`, `BNB/USDT`, and `AVAX/USDT`. That shim is diagnostic only and does not make this a provider-complete or promotion-ready Board B candidate.

## Strategy Readback

| Strategy | Full-window trades | Full-window profit | Full-window win rate | Robust Sharpe | Worst timerange profit | Profit floor |
|---|---:|---:|---:|---:|---:|---|
| `CrashRebound` | 176 | 40.58% | 65.34% | 0.1516 | 8.63% | FAIL |
| `PerPairMR` | 287 | 23.97% | 64.11% | -0.2159 | -2.48% | FAIL |
| `RegimeAdaptiveBNB` | 30 | 15.96% | 60.00% | -0.0390 | -0.76% | FAIL |

All three strategies failed the per-timerange profit floor. `RegimeAdaptiveBNB` also had low trade support and a negative winter timerange.

## Board B Classification

Classification: `diagnostic_only:auto_quant_screen_not_b2r_repeat_candidate`.

Reasons:
- No rooted Board B branch path was emitted: `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`.
- No RC-SPA, Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution-tree chain was run for this probe.
- The synthetic market metadata shim is useful for local Auto-Quant/Freqtrade interoperability readback, not provider-complete promotion evidence.
- This probe does not supersede the live Board B cursor. At readback, the cursor had advanced to `20260512T024509+0800-codex-board-b-b2r-correlation-shock-panel-v1` for `CorrelationShockAbsorptionV1`; this diagnostic remains additive only.

Next: complete or consume the active `024509` root-aware correlation-shock panel if it is still running. If that panel fails, select or synthesize another materially different root-aware Bull/Bear/Sideways/Crisis family/provider panel and run the full provider -> Auto-Quant -> Pre-Bayes/BBN -> CatBoost/path-ranker -> execution-tree chain before any promotion claim.
