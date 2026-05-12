# OB/FVG AQ Agent-Material Terminal Readback v1

Run root:
`docs/experiments/actionable-regime-confidence/runs/20260512T160511+0800-codex-ob-fvg-aq-agent-material-packet-v1`

## Objective

Convert the existing `151907` OB/FVG branch screen into a new unowned Board B Auto-Quant profitability-factor packet while preserving:

- `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`
- `TrendTransition -> LowVolatility -> up_momentum -> order_block_pullback_v1`
- six provider rows for `IBKR`, `TradingViewRemix/TVR`, `yfinance/YF`, `Kraken`, `Binance`, and `Bybit`

## Commands

- Initial batch attempt `01_auto_quant_agent_material_batch` exited `1`: zsh command-length handling failed before `ict-engine` execution.
- Symlink retry `01b_auto_quant_agent_material_batch_symlink_retry` exited `127`: zsh treated the command string as a single executable word.
- Array retry `01c_auto_quant_agent_material_batch` exited `0` and produced batch artifact `auto-quant-agent-material-batch:B2R_OB_FVG_AQ_160511:20260512T081513.808Z`.
- Dispatch `02_auto_quant_agent_material_dispatch` exited `0` and produced dispatch artifact `auto-quant-agent-material-dispatch:B2R_OB_FVG_AQ_160511:20260512T081839.654Z`.
- Rank `03_auto_quant_agent_material_rank` exited `0` and produced rank artifact `auto-quant-agent-material-rank:B2R_OB_FVG_AQ_160511:20260512T082002.936Z`.

## Provider / AQ Results

- `IBKR` / `SPY 1h`: completed, `350` trades, win rate `39.1429%`, total profit `9.65%`, Sharpe `0.2862`, profit factor `1.1346`.
- `yfinance/YF` / `ES 1h`: completed, `255` trades, win rate `34.1176%`, total profit `-2.02%`, Sharpe `-0.1338`, profit factor `0.9508`.
- `Binance` / `BTCUSDT 1h`: completed with `0` trades.
- `Kraken` / `XBTUSD 1h`: failed with `OperationalException: No data found. Terminating.`
- `Bybit` / `BTCUSDT linear 1h`: failed with `OperationalException: No data found. Terminating.`
- `TradingViewRemix/TVR`: not called in this root; recorded as `provider_unreachable_current_rate_limited` from `154536`.

## Gate

- `support_once:160511_ob_fvg_aq_agent_material_packet_v1`.
- `active_claim_closed:160511_ob_fvg_aq_agent_material_packet_v1`.
- `evidence_class:aq_agent_material_provider_packet_fail_closed`.
- `pass:board_work_claim_before_execution`.
- `pass:branch_path_preserved_trendtransition_lowvolatility_up_momentum_order_block_pullback_v1`.
- `pass:provider_rows_6`.
- `pass:tvr_recorded_unreachable_without_new_call`.
- `pass:auto_quant_batch_exit0_after_wrapper_retries`.
- `pass:auto_quant_dispatch_exit0`.
- `pass:auto_quant_rank_exit0`.
- `partial:ibkr_spy_positive_350_trades_pf_1_1346_profit_9_65_pct`.
- `fail_closed:yf_es_negative_profit_minus_2_02_pct_pf_0_9508`.
- `fail_closed:binance_zero_trades`.
- `fail_closed:kraken_no_data_found`.
- `fail_closed:bybit_no_data_found`.
- `fail_closed:tvr_unreachable_current_rate_limited`.
- `fail_closed:non_tvr_rows_local_cache_replay_from_150855`.
- `fail_closed:not_current_same_root_six_provider_authority`.
- `fail_closed:no_portable_cross_provider_profitability`.
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_handoff`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Do not promote from `160511`. Keep it as a real AQ agent-material negative/partial packet: useful for OB/FVG branch nursery evidence and provider/readiness classification, not for market/factor learning. The next valid step is a fresh same-root provider/AQ packet with current provider acquisition, including TVR health or explicit same-run TVR unreachable handling, before any downstream handoff probe.
