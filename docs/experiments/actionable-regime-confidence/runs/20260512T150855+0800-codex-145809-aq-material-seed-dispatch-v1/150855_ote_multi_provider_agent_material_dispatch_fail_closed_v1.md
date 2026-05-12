# 150855 OTE Multi-Provider Agent-Material Dispatch Fail-Closed v1

Generated: `2026-05-12 15:22:51 +0800`

This is a readback for root `20260512T150855+0800-codex-145809-aq-material-seed-dispatch-v1`. It is a useful multi-provider Auto-Quant agent-material dispatch, but it is not same-root six-provider authority and not downstream admission.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Real repo-local artifact | This report plus `command-output/`, `checks/`, and `state/auto-quant/B2R_OTE_BRANCH_150855/` | Pass |
| Auto-Quant executed | `02_auto_quant_agent_material_dispatch.exit=0`; dispatch output shows external AQ runs | Pass |
| Provider breadth | Materials for Binance, IBKR, Yahoo/YF, Kraken, and Bybit | Partial |
| Required six providers | TradingViewRemix/TVR absent; Kraken and Bybit jobs failed | Fail closed |
| Profitability evidence | IBKR SPY completed with 162 trades and PF 1.2609; Yahoo ES completed but negative; Binance completed with 0 trades | Mixed |
| Rank evidence | `03_auto_quant_agent_material_rank.exit=0` and ranking JSON/output present | Pass |
| Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree | Not run in this root | Fail closed |
| Promotion/trade usable | No promotion; no live-trade claim | Fail closed |

## Evidence

- Batch output: `command-output/01_auto_quant_agent_material_batch.out`
- Dispatch output: `command-output/02_auto_quant_agent_material_dispatch.out`
- Rank output: `command-output/03_auto_quant_agent_material_rank.out`
- State artifacts: `state/auto-quant/B2R_OTE_BRANCH_150855/auto_quant_agent_material_dispatch.20260512T071838.149Z.json`, `state/auto-quant/B2R_OTE_BRANCH_150855/auto_quant_agent_material_rank.20260512T071914.134Z.json`
- Data line counts: `data_line_counts.txt`

## Readback

- Checks `01_auto_quant_agent_material_batch`, `02_auto_quant_agent_material_dispatch`, and `03_auto_quant_agent_material_rank` all exited `0`.
- The material batch created five provider-backed jobs: Binance BTCUSDT 1h, IBKR SPY 1h, Yahoo ES 1h, Kraken XBTUSD 1h, and Bybit BTCUSDT 1h.
- Dispatch selected all five groups. Totals were `total_jobs=5`, `completed_jobs=3`, `failed_jobs=2`.
- IBKR SPY 1h completed with `162` trades, total profit `5.96%`, Sharpe `0.2471`, Sortino `0.6153`, Calmar `2.7994`, max drawdown `-3.7193%`, win rate `34.5679%`, and profit factor `1.2609`.
- Yahoo ES 1h completed with `103` trades but was negative: total profit `-0.84%`, Sharpe `-0.0873`, max drawdown `-4.4802%`, win rate `30.0971%`, and profit factor `0.9270`.
- Binance BTCUSDT 1h completed but generated `0` trades.
- Kraken XBTUSD and Bybit BTCUSDT failed with `OperationalException: No data found. Terminating.`
- TradingViewRemix/TVR is absent from this root.
- The rank output ordered IBKR first, Yahoo second, Binance third, then the failed Kraken and Bybit jobs.
- No Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution-tree admission was run from this root.

## Gate

- `support_once:150855_ote_multi_provider_agent_material_dispatch_v1`.
- `evidence_class:multi_provider_agent_material_dispatch_fail_closed`.
- `pass:agent_material_batch_exit0`.
- `pass:agent_material_dispatch_exit0`.
- `pass:agent_material_rank_exit0`.
- `pass:five_provider_jobs_created`.
- `pass:three_completed_two_failed`.
- `partial:ibkr_spy_1h_profit_factor_1_2609_trades_162`.
- `fail_closed:yahoo_es_profit_factor_0_927_negative_total_profit`.
- `fail_closed:binance_btcusdt_zero_trades`.
- `fail_closed:kraken_xbtusd_no_data_found`.
- `fail_closed:bybit_btcusdt_no_data_found`.
- `fail_closed:tvr_absent`.
- `fail_closed:not_six_provider_aq_authority`.
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_admission`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Use `150855` as a multi-provider AQ dispatch negative/seed packet. A valid continuation must either repair Kraken/Bybit data namespace and add TVR, or start a new same-root six-provider packet, then carry surviving observations through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree before any acceptance or promotion claim.
