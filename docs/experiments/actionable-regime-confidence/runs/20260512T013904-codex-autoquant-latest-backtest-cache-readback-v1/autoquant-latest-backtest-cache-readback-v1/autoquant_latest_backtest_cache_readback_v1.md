# Auto-Quant Latest Backtest Cache Readback v1

Run id: `20260512T013904-codex-autoquant-latest-backtest-cache-readback-v1`
Gate result: `autoquant_latest_backtest_cache_readback_v1=latest_cache_parsed_low_trade_negative_non_promoting`

Latest cache:
- Meta: `/Users/thrill3r/Auto-Quant/user_data/backtest_results/backtest-result-2026-05-12_00-27-36.meta.json`
- Zip: `/Users/thrill3r/Auto-Quant/user_data/backtest_results/backtest-result-2026-05-12_00-27-36.zip`
- Strategy: `TomacNQ_KillzoneBreakout`

Strategy metrics:
- timeframe `1h`, timerange `20210101-20251231`.
- trades `9`, wins `4`, losses `5`, winrate `0.4444444444444444`.
- profit_total `-0.058056`, profit_total_abs `-5805.6`, sharpe `-0.056157979678321875`, profit_factor `0.2537789203084833`.
- first/last trade `2022-07-07 14:00:00+00:00` -> `2023-01-12 14:00:00+00:00`.

Inventory:
- `active_default_strategy_py`: count `0`; files `none`.
- `external_strategy_py`: count `1`; files `user_data/strategies_external/TomacNQ_KillzoneBreakout.py`.
- `latest_backtest_zip_members`: count `4`; files `backtest-result-2026-05-12_00-27-36.json;backtest-result-2026-05-12_00-27-36_config.json;backtest-result-2026-05-12_00-27-36_TomacNQ_KillzoneBreakout.py;backtest-result-2026-05-12_00-27-36_market_change.feather`.

Tmp root readback:
- `r6_owner_export` present `false`.
- `r3_native_subhour` present `false`.
- `r5_recency_extension` present `false`.
- `source_label_equivalence` present `true`.

Result:
- The latest local Auto-Quant cache is real and parseable, but it is not Board A promotion evidence.
- Active default strategy source files remain `0`; the latest cached strategy has only `9` trades and negative edge.
- The cache does not contain accepted MainRegimeV2 source labels, R6 controls, R3 native sub-hour labels, or R5 recency rows.
- No canonical merge, downstream promotion rerun, trade usage, or `update_goal` is authorized.

