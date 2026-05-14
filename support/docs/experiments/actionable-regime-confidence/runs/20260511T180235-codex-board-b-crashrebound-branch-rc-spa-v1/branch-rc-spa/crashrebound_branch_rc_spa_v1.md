# CrashRebound Branch RC-SPA v1

Run id: `20260511T180235+0800-codex-board-b-crashrebound-branch-rc-spa-v1`.

## Inputs

- Board B: `docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.json`
- Board A market context: `docs/experiments/actionable-regime-confidence/runs/20260511T144838-codex-market-regime-context-packet-v1/market-regime-context/market_regime_context_packet_v1.json`
- Auto-Quant root: `/Users/thrill3r/Auto-Quant`
- Strategy file: `/Users/thrill3r/Auto-Quant/versions/0.4.1/strategies/CrashRebound.py`
- Source regime CSV: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv`

## Auto-Quant Backtest Readback

| Segment | Timerange | Trades | Win rate % | Profit % | Sharpe | Log |
|---|---|---:|---:|---:|---:|---|
| `bull_2021` | `20210101-20211231` | 50 | 70.000 | 24.870 | 0.8496 | `docs/experiments/actionable-regime-confidence/runs/20260511T180235-codex-board-b-crashrebound-branch-rc-spa-v1/logs/freqtrade_backtest_bull_2021.out` |
| `winter_2022` | `20220101-20221231` | 32 | 68.750 | 2.990 | 0.0847 | `docs/experiments/actionable-regime-confidence/runs/20260511T180235-codex-board-b-crashrebound-branch-rc-spa-v1/logs/freqtrade_backtest_winter_2022.out` |
| `recovery_23_25` | `20230101-20251231` | 123 | 66.667 | 17.290 | 0.1920 | `docs/experiments/actionable-regime-confidence/runs/20260511T180235-codex-board-b-crashrebound-branch-rc-spa-v1/logs/freqtrade_backtest_recovery_23_25.out` |
| `full_5y` | `20210101-20251231` | 207 | 68.599 | 55.690 | 0.2903 | `docs/experiments/actionable-regime-confidence/runs/20260511T180235-codex-board-b-crashrebound-branch-rc-spa-v1/logs/freqtrade_backtest_full_5y.out` |

## Branch Summary

| Root | Trades | Win rate % | Net R | Mean R | Edge LCB 5% | 2x cost net R | Branch path |
|---|---:|---:|---:|---:|---:|---:|---|
| `Bull` | 140 | 70.714 | 1.708641 | 0.012205 | 0.004928 | 1.428641 | `Bull -> PullbackInUptrend -> DrawdownLt20RsiLt35VolumeConfirmDailyEmaSlopeUp -> CrashRebound` |
| `Bear` | 41 | 78.049 | 0.435294 | 0.010617 | -0.007760 | 0.353294 | `Bear -> BearMarketCapitulationRebound -> DrawdownLt20RsiLt35VolumeConfirmDailyEmaSlopeUp -> CrashRebound` |
| `Sideways` | 26 | 42.308 | -0.433273 | -0.016664 | -0.034989 | -0.485273 | `Sideways -> RangeShockMeanReversion -> DrawdownLt20RsiLt35VolumeConfirmDailyEmaSlopeUp -> CrashRebound` |
| `Crisis` | 0 | 0.000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | `` |

## RC-SPA Decision

- RC-SPA: `40.946`
- Promotion level: `reject`
- Failure reasons: `cost_stress_survival, pbo, tail_loss_p95, branch_min_total_trades_for_claimed_roots`
- Total trades: `207`
- Fold positive rate: `1.000`
- PBO: `0.750`
- DSR: `0.002`
- Tail loss abs p95: `0.113374` vs budget `0.1`

## Artifacts

- Trades CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T180235-codex-board-b-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_trades_v1.csv`
- Trades JSONL: `docs/experiments/actionable-regime-confidence/runs/20260511T180235-codex-board-b-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_trades_v1.jsonl`
- Labels JSONL: `docs/experiments/actionable-regime-confidence/runs/20260511T180235-codex-board-b-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_purged_cv_labels_v1.jsonl`
- Summary JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T180235-codex-board-b-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_summary_v1.json`
- RC-SPA JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T180235-codex-board-b-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_rc_spa_report_v1.json`
- Payoff JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T180235-codex-board-b-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_payoff_shape_v1.json`
- Purged CV JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T180235-codex-board-b-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_purged_cv_guard_v1.json`
- Profitability packet: `docs/experiments/actionable-regime-confidence/runs/20260511T180235-codex-board-b-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_regime_profitability_packet_v1.json`
- Import manifest: `docs/experiments/actionable-regime-confidence/runs/20260511T180235-codex-board-b-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_strategy_library_for_import_v1.json`
