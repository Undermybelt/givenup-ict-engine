# 151057 Provider-Backed Agent-Material AQ Dispatch Fail-Closed v1

Generated: `2026-05-12 15:18:28 +0800`

This is a readback for root `20260512T151057+0800-codex-provider-backed-agent-material-aq-dispatch-v1`. It is useful provider-backed Auto-Quant agent-material evidence, but it is not Board A regime-confidence acceptance and not Board B promotion.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Use real repo artifacts, not chat-only claims | This report and command outputs under this run root | Pass |
| Auto-Quant involved | `03_agent_material_batch.exit=0`, `04_agent_material_dispatch_group0.exit=0`; dispatch output reports `external_auto_quant_run_completed` | Pass |
| Provider-backed data | Materials use `143900` provider files for IBKR SPY 1h and Yahoo ES 1h | Partial |
| Six required providers | This root has IBKR and Yahoo/YF materials only; dispatched group is IBKR only | Fail closed |
| Regime/branch profitability candidate | `ProviderTrendPullbackResume` on IBKR SPY 1h produced 316 trades, PF 1.3903, total profit 29.99% | Partial |
| Chronological/cross-provider survival | Only one dispatched provider group completed | Fail closed |
| Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree | Not run in this root | Fail closed |
| Promotion/trade usable | No promotion; no live-trade claim | Fail closed |

## Evidence

- Material JSON validation: `checks/01_material_json_valid.exit=0`
- Strategy Python compile: `checks/02_strategy_py_compile.exit=0`
- Agent-material batch: `checks/03_agent_material_batch.exit=0`
- Dispatch group 0: `checks/04_agent_material_dispatch_group0.exit=0`
- Materials: `materials/ibkr_spy_provider_trend_pullback_resume.json`, `materials/yahoo_es_provider_trend_pullback_resume.json`
- Strategy: `strategies/ProviderTrendPullbackResume.py`
- Dispatch output: `command-output/04_agent_material_dispatch_group0.out`
- AQ workspace log: `state/auto-quant/agent_material_units/IBKR_SPY_1h_Provider_Trend_Pullback_Resume/aq_workspace/run_tomac.stdout.log`

## Readback

- Both material JSON files validated and the strategy compiled.
- The batch created two jobs: `IBKR_SPY_1h_Provider_Trend_Pullback_Resume` and `Yahoo_ES_1h_Provider_Trend_Pullback_Resume`.
- Only dispatch group `0` was executed in this root. That group ran the IBKR SPY 1h material and completed.
- The IBKR Auto-Quant run reported `316` trades over `2023-01-01` to `2025-12-31`, total profit `29.99%`, Sharpe `0.6637`, Sortino `1.6126`, Calmar `7.5834`, max drawdown `-6.8992%`, win rate `41.4557%`, and profit factor `1.3903`.
- The Yahoo ES material was prepared but not dispatched in this root.
- The stderr log shows Freqtrade filled missing SPY/USD 1h data from `12033` to `26361` rows, so the result needs additional provider-alignment scrutiny before any downstream use.
- This root does not include same-root `TradingViewRemix/TVR`, `Kraken`, `Binance`, or `Bybit` AQ dispatch, and it does not run Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution-tree admission.

## Gate

- `support_once:151057_provider_backed_agent_material_aq_dispatch_v1`.
- `evidence_class:single_provider_ibkr_aq_dispatch_positive_seed_fail_closed`.
- `pass:material_json_valid_exit0`.
- `pass:strategy_py_compile_exit0`.
- `pass:agent_material_batch_exit0`.
- `pass:ibkr_dispatch_group0_exit0`.
- `pass:ibkr_spy_1h_trades_316`.
- `pass:ibkr_spy_1h_profit_factor_1_3903`.
- `partial:ibkr_spy_1h_total_profit_pct_29_99`.
- `partial:yahoo_es_material_created_not_dispatched`.
- `fail_closed:not_six_provider_aq_authority`.
- `fail_closed:missing_tvr_kraken_binance_bybit_same_root_dispatch`.
- `fail_closed:only_ibkr_group_dispatched`.
- `fail_closed:freqtrade_missing_data_fillup_119_07pct`.
- `fail_closed:no_pre_bayes_filter_bbn_catboost_execution_tree_admission`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Use this root only as a positive IBKR provider-backed AQ seed. A valid continuation must dispatch the remaining provider groups in a same-root six-provider packet, then run the ordered Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree chain before any Board A acceptance or Board B promotion claim.
