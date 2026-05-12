# 115700 Selected-History BTC Alias Auto-Quant Readback v1

Generated: 2026-05-12T12:41:29+0800

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1`

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T123227+0800-codex-115700-selected-history-btc-alias-aq-v1`

Board hash before registration: `563e8d8418751c88ddfbcbd596f2d0328660a9a6216e6a0d1ed3e1e9928237c2`

## Scope

This is a support-only readback for the already-created `123227` BTC alias probe. It records command outcomes and the isolated generated-workspace timerange repair. It does not edit the Board B cursor, does not approve source-control evidence, does not promote a candidate, does not make a live-trade claim, and does not call `update_goal`.

## Inputs

- Selected recorded dataset path used by the attempt: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/provider-data-json/BTC_USD-1h.json`
- Auto-Quant symbol: `BTC`
- Prepared pair alias: `BTC/USD`
- Objective: `expansion_manipulation`
- Auto-Quant pinned commit: `b640cc8ea0fd3ac5e6b2eaca75ba8abbd0aca91f`

## Readback

- Initial `factor-research --symbol BTC` exited `0` and reported `dependency_ready_data_missing`.
- `auto-quant-prepare` exited `0` and moved readiness to `dependency_ready_data_ready`.
- Prepared data files existed under the isolated Auto-Quant workspace: `BTC_USD-1h.feather`, `BTC_USD-4h.feather`, and `BTC_USD-1d.feather`.
- Post-prepare `factor-research --symbol BTC` exited `0` and pointed to `run_tomac.py`.
- The first Auto-Quant venv TOMAC run exited `1`; Freqtrade loaded, but `TomacAggressiveBE`, `TomacKillzoneBreakout`, and `TomacRRWinRate` all failed with `OperationalException: No data found. Terminating.` because the generated config was still outside the selected data window.
- The generated `config.tomac.json` in this isolated workspace was patched to `timerange=20260401-20260512` with `pair_whitelist=["BTC/USD"]`; no repo runtime code was changed.
- The patched TOMAC run exited `0`: `3` strategies succeeded, `0` failed.
- All three successful backtests produced `0` trades, `0.0000` total profit, `0.0000` Sharpe, `0.0000` win rate, and `0.0000` profit factor.
- Strategy windows after startup were `2026-04-09 08:00:00 -> 2026-05-11 23:00:00`, `2026-04-11 10:00:00 -> 2026-05-11 23:00:00`, and `2026-04-13 12:00:00 -> 2026-05-11 23:00:00`.
- Result: selected-history gate advanced through data readiness and Freqtrade execution, but produced no nonzero provider-rooted Auto-Quant observations.
- No measured profitability packet, RC-SPA surface, mature rooted observation set, or downstream Pre-Bayes/BBN/CatBoost/execution-tree promotion artifact was produced.

## Checklist

| Check | Result |
|---|---|
| Selected recorded BTC 1h path used | pass |
| Isolated Auto-Quant workspace used | pass |
| Data prepared for 1h/4h/1d | pass |
| Freqtrade runtime dependency solved via Auto-Quant venv | pass |
| BTC/USD pair alias and timerange repaired in generated workspace only | pass |
| TOMAC process exited cleanly after repair | pass |
| Nonzero trades observed | fail-closed |
| Measured profitability packet available | fail-closed |
| Downstream Pre-Bayes/BBN/CatBoost/execution-tree promotion artifact available | fail-closed |

## Gate

- `support_once:123227_115700_selected_history_btc_alias_aq_v1`.
- `supporting_only:selected_history_btc_alias_timerange_repair_readback`.
- `pass:factor_research_initial_exit0`.
- `pass:auto_quant_prepare_exit0_data_ready_true`.
- `pass:factor_research_after_prepare_exit0`.
- `pass:prepared_btc_usd_1h_4h_1d_feathers`.
- `pass:auto_quant_venv_freqtrade_loaded`.
- `pass:isolated_config_pair_btc_usd_timerange_20260401_20260512`.
- `pass:patched_tomac_exit0`.
- `pass:strategies_succeeded_3_failed_0`.
- `fail_closed:initial_tomac_no_data_found_before_timerange_patch`.
- `fail_closed:total_trades_0`.
- `fail_closed:total_profit_pct_0`.
- `fail_closed:sharpe_0`.
- `fail_closed:no_measured_profitability_packet`.
- `fail_closed:no_rc_spa_no_downstream_promotion`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Do not promote from `123227`. The next valid transition needs a provider-rooted selected-history strategy/factor that emits nonzero trades and can then survive the ordered Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree chain with chronological and cross-context validation.
