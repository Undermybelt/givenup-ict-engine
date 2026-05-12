# VolBreakoutSized Branch RC-SPA v1

Run id: `20260511T181445+0800-codex-board-b-volbreakoutsized-branch-rc-spa-v1`.

## Inputs

- Board B: `docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.json`
- Board A market context: `docs/experiments/actionable-regime-confidence/runs/20260511T144838-codex-market-regime-context-packet-v1/market-regime-context/market_regime_context_packet_v1.json`
- Auto-Quant root: `/Users/thrill3r/Auto-Quant`
- Strategy file: `/Users/thrill3r/Auto-Quant/versions/0.4.0/strategies/VolBreakoutSized.py`
- Source regime CSV: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv`

## Auto-Quant Backtest Readback

| Segment | Timerange | Trades | Win rate % | Profit % | Sharpe | Log |
|---|---|---:|---:|---:|---:|---|
| `bull_2021` | `20210101-20211231` | 301 | 37.209 | 10.570 | 2.6249 | `docs/experiments/actionable-regime-confidence/runs/20260511T181445-codex-board-b-volbreakoutsized-branch-rc-spa-v1/logs/freqtrade_backtest_bull_2021.out` |
| `winter_2022` | `20220101-20221231` | 104 | 31.731 | -0.400 | -0.2031 | `docs/experiments/actionable-regime-confidence/runs/20260511T181445-codex-board-b-volbreakoutsized-branch-rc-spa-v1/logs/freqtrade_backtest_winter_2022.out` |
| `recovery_23_25` | `20230101-20251231` | 816 | 31.373 | 14.850 | 1.3752 | `docs/experiments/actionable-regime-confidence/runs/20260511T181445-codex-board-b-volbreakoutsized-branch-rc-spa-v1/logs/freqtrade_backtest_recovery_23_25.out` |
| `full_5y` | `20210101-20251231` | 1221 | 32.842 | 25.020 | 1.3390 | `docs/experiments/actionable-regime-confidence/runs/20260511T181445-codex-board-b-volbreakoutsized-branch-rc-spa-v1/logs/freqtrade_backtest_full_5y.out` |

## Branch Summary

| Root | Trades | Win rate % | Net R | Mean R | Edge LCB 5% | 2x cost net R | Branch path |
|---|---:|---:|---:|---:|---:|---:|---|
| `Bull` | 1050 | 34.190 | 10.289923 | 0.009800 | 0.005317 | 8.189923 | `Bull -> TrendExpansion -> Donchian24Ema4hTrendVolumeVolTarget -> VolBreakoutSized` |
| `Bear` | 117 | 23.077 | -0.265870 | -0.002272 | -0.008878 | -0.499870 | `Bear -> BearReliefBreakout -> Donchian24Ema4hTrendVolumeVolTarget -> VolBreakoutSized` |
| `Sideways` | 44 | 31.818 | -0.441671 | -0.010038 | -0.016613 | -0.529671 | `Sideways -> RangeBreakoutAttempt -> Donchian24Ema4hTrendVolumeVolTarget -> VolBreakoutSized` |
| `Crisis` | 10 | 10.000 | -0.195205 | -0.019520 | -0.027662 | -0.215205 | `Crisis -> CrisisBreakoutSuppression -> Donchian24Ema4hTrendVolumeVolTarget -> VolBreakoutSized` |

## RC-SPA Decision

- RC-SPA: `59.507`
- Promotion level: `reject`
- Failure reasons: `cost_stress_survival, pbo, branch_min_total_trades_for_claimed_roots`
- Total trades: `1221`
- Fold positive rate: `0.750`
- PBO: `0.750`
- DSR: `0.723`
- Tail loss abs p95: `0.048488` vs budget `0.1`

## Artifacts

- Trades CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T181445-codex-board-b-volbreakoutsized-branch-rc-spa-v1/branch-rc-spa/volbreakoutsized_branch_trades_v1.csv`
- Trades JSONL: `docs/experiments/actionable-regime-confidence/runs/20260511T181445-codex-board-b-volbreakoutsized-branch-rc-spa-v1/branch-rc-spa/volbreakoutsized_branch_trades_v1.jsonl`
- Labels JSONL: `docs/experiments/actionable-regime-confidence/runs/20260511T181445-codex-board-b-volbreakoutsized-branch-rc-spa-v1/branch-rc-spa/volbreakoutsized_purged_cv_labels_v1.jsonl`
- Summary JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T181445-codex-board-b-volbreakoutsized-branch-rc-spa-v1/branch-rc-spa/volbreakoutsized_branch_summary_v1.json`
- RC-SPA JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T181445-codex-board-b-volbreakoutsized-branch-rc-spa-v1/branch-rc-spa/volbreakoutsized_rc_spa_report_v1.json`
- Payoff JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T181445-codex-board-b-volbreakoutsized-branch-rc-spa-v1/branch-rc-spa/volbreakoutsized_payoff_shape_v1.json`
- Purged CV JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T181445-codex-board-b-volbreakoutsized-branch-rc-spa-v1/branch-rc-spa/volbreakoutsized_purged_cv_guard_v1.json`
- Profitability packet: `docs/experiments/actionable-regime-confidence/runs/20260511T181445-codex-board-b-volbreakoutsized-branch-rc-spa-v1/branch-rc-spa/volbreakoutsized_regime_profitability_packet_v1.json`
- Import manifest: `docs/experiments/actionable-regime-confidence/runs/20260511T181445-codex-board-b-volbreakoutsized-branch-rc-spa-v1/branch-rc-spa/volbreakoutsized_strategy_library_for_import_v1.json`
