# RootAwareMultiBranchV1 Branch RC-SPA v1

Run id: `20260511T182222+0800-codex-board-b-rootaware-multibranch-rc-spa-v1`.

## Inputs

- Board B: `docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.json`
- Board A market context: `docs/experiments/actionable-regime-confidence/runs/20260511T144838-codex-market-regime-context-packet-v1/market-regime-context/market_regime_context_packet_v1.json`
- Source regime CSV: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv`
- Strategy file: `docs/experiments/actionable-regime-confidence/runs/20260511T182222-codex-board-b-rootaware-multibranch-rc-spa-v1/strategies/RootAwareMultiBranchV1.py`

## Auto-Quant Backtest Readback

| Segment | Timerange | Trades | Win rate % | Profit % | Sharpe | Log |
|---|---|---:|---:|---:|---:|---|
| `bull_2021` | `20210101-20211231` | 275 | 37.818 | 10.560 | 2.5422 | `docs/experiments/actionable-regime-confidence/runs/20260511T182222-codex-board-b-rootaware-multibranch-rc-spa-v1/logs/freqtrade_backtest_bull_2021.out` |
| `winter_2022` | `20220101-20221231` | 74 | 41.892 | 0.950 | 0.4249 | `docs/experiments/actionable-regime-confidence/runs/20260511T182222-codex-board-b-rootaware-multibranch-rc-spa-v1/logs/freqtrade_backtest_winter_2022.out` |
| `recovery_23_25` | `20230101-20251231` | 716 | 31.704 | 14.400 | 1.3029 | `docs/experiments/actionable-regime-confidence/runs/20260511T182222-codex-board-b-rootaware-multibranch-rc-spa-v1/logs/freqtrade_backtest_recovery_23_25.out` |
| `full_5y` | `20210101-20251231` | 1064 | 34.023 | 26.310 | 1.3522 | `docs/experiments/actionable-regime-confidence/runs/20260511T182222-codex-board-b-rootaware-multibranch-rc-spa-v1/logs/freqtrade_backtest_full_5y.out` |

## Branch Summary

| Root | Trades | Win rate % | Net R | Mean R | Edge LCB 5% | 2x cost net R | Branch path |
|---|---:|---:|---:|---:|---:|---:|---|
| `Bull` | 1063 | 33.960 | 10.109290 | 0.009510 | 0.004895 | 7.983290 | `Bull -> TrendExpansion -> Donchian24Ema4hTrendVolumeVolTarget -> RootAwareMultiBranchV1` |
| `Bear` | 0 | 0.000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | `Bear -> SuppressBearRootNoTrade -> NoPositiveEdge -> no_trade` |
| `Sideways` | 1 | 100.000 | 0.023452 | 0.023452 | 0.023452 | 0.021452 | `Sideways -> SuppressSidewaysRootNoTrade -> Donchian24Ema4hTrendVolumeVolTarget -> RootAwareMultiBranchV1` |
| `Crisis` | 0 | 0.000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | `Crisis -> SuppressCrisisRootNoTrade -> TailRiskSuppression -> no_trade` |

## RC-SPA Decision

- RC-SPA: `80.000`
- Promotion level: `reject`
- Failure reasons: `pbo, branch_min_total_trades_for_claimed_roots`
- Total trades: `1064`
- Fold positive rate: `1.000`
- PBO: `0.750`
- DSR: `0.825`
- Tail loss abs p95: `0.048978` vs budget `0.1`

## Artifacts

- Trades CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T182222-codex-board-b-rootaware-multibranch-rc-spa-v1/branch-rc-spa/rootaware_multibranch_trades_v1.csv`
- Summary JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T182222-codex-board-b-rootaware-multibranch-rc-spa-v1/branch-rc-spa/rootaware_multibranch_summary_v1.json`
- RC-SPA JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T182222-codex-board-b-rootaware-multibranch-rc-spa-v1/branch-rc-spa/rootaware_multibranch_rc_spa_report_v1.json`
- Profitability packet: `docs/experiments/actionable-regime-confidence/runs/20260511T182222-codex-board-b-rootaware-multibranch-rc-spa-v1/branch-rc-spa/rootaware_multibranch_profitability_packet_v1.json`
- Import manifest: `docs/experiments/actionable-regime-confidence/runs/20260511T182222-codex-board-b-rootaware-multibranch-rc-spa-v1/branch-rc-spa/rootaware_multibranch_strategy_library_for_import_v1.json`
