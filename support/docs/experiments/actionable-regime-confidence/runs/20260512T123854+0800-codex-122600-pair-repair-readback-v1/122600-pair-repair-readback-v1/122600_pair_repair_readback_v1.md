# 122600 Pair Repair Readback v1

Run id: `20260512T123854+0800-codex-122600-pair-repair-readback-v1`

This is a support-only correction/readback for already-existing command outputs under `20260512T122600+0800-codex-115700-selected-history-factor-research-v1`. It does not launch a new provider, Auto-Quant, Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution-tree probe, does not edit the Board B cursor, does not promote a candidate, and does not call `update_goal`.

## Source State

- Selected-history source root: `20260512T122600+0800-codex-115700-selected-history-factor-research-v1`
- Provider/AQ root: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`
- Enriched downstream authority: `20260512T121347+0800-codex-115700-enriched-downstream-chain-v1`
- Current Board B hash before this readback: `04ad8a14b13f3c7bbd2c622a103f4232fe1697289bbb5693701e4cbead6ed2ef`

## Readback

The registered `123352` section correctly reported the initial selected-history attempt as fail-closed, but the same `122600` run root already contained later pair-repair command outputs. Those later outputs change the immediate blocker from `No pair in whitelist` to `no trades`.

Pair alias:

```text
original_pair=B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700/USD
sanitized_pair=B2RSAMEROOTSIXPROVIDER1HAQ115700/USD
reason=freqtrade_expand_pairlist_drops_underscore_pairs
```

Command evidence:

- `run_tomac_selected_history_sanitized_pair.exit`: `1`, failed with `No data found. Terminating.`
- `run_tomac_selected_history_sanitized_pair_selected_window.exit`: `0`
- selected-window command: `CONFIG=config.tomac.sanitized-pair-selected-window.json pair=B2RSAMEROOTSIXPROVIDER1HAQ115700/USD timerange=20260401-20260512 run_tomac.main()`

Backtest readback from the selected-window run:

| Strategy | Result | Trades | Total profit % | Win rate % | Profit factor |
|---|---|---:|---:|---:|---:|
| `TomacAggressiveBE` | succeeded | 0 | 0.0000 | 0.0000 | 0.0000 |
| `TomacKillzoneBreakout` | succeeded | 0 | 0.0000 | 0.0000 | 0.0000 |
| `TomacRRWinRate` | succeeded | 0 | 0.0000 | 0.0000 | 0.0000 |

Data coverage notes:

- 1h data loaded from `2026-04-01T00:00:00Z` to `2026-05-11T23:00:00Z`; fillup `971 -> 984` (`1.34%`).
- 4h informative data loaded from `2026-04-01T00:00:00Z` to `2026-05-11T20:00:00Z`; fillup `243 -> 246` (`1.23%`).
- Backtests effectively ran from `2026-04-11T10:00:00Z` or `2026-04-13T12:00:00Z` to `2026-05-11T23:00:00Z` after startup-candle movement.

## Gate

- `support_once:123854_122600_pair_repair_readback_v1`
- `supporting_only:corrects_123352_pair_blocker_to_pair_repaired_no_trades`
- `pass:sanitized_pair_selected_window_exit0`
- `pass:tomac_backtests_3_succeeded_0_failed`
- `fail_closed:all_three_tomac_strategies_trade_count_0`
- `fail_closed:no_measured_profitability_packet`
- `fail_closed:no_rc_spa_surface`
- `fail_closed:no_downstream_pre_bayes_bbn_catboost_execution_tree_promotion`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Next

Use this as support that the pair/whitelist construction blocker is repaired in the selected-history workspace. The remaining blocker is no-trade / no measured profitability. Do not feed this as accepted market-factor evidence. The next valid work needs a nonzero-trade selected-history recipe or a wider provider-provenanced history before RC-SPA and downstream closure.
