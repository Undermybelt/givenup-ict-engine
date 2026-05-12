# Board A AQ Provider Authority Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T102018+0800-codex-board-a-aq-provider-authority-readback-v1`

Mode: `board_a_readback_provider_authority_no_promotion`

## Scope

This packet responds to the AQ/provider authority correction for Board A. It proves Board A invoked the Auto-Quant path and prepared provider-provenanced market data in an isolated AQ workspace. It does not edit Current Cursor, does not approve R6 source/control policy, does not claim regime confidence acceptance, does not run Board B recipe profitability, does not run Pre-Bayes/BBN/CatBoost/execution-tree promotion, and does not call `update_goal`.

## Commands

- `provider-status --agent`: exit `0`
- `auto-quant-status` before handoff: exit `0`
- `factor-research --backend auto-quant --auto-quant-profile synthetic_ohlcv`: exit `0`
- `auto-quant-prepare` first attempt: exit `127`; shell invocation error only, retained as provenance.
- `auto-quant-prepare` retry: exit `0`
- `auto-quant-status` after prepare retry: exit `0`

## Provider / AQ Fields

- `aq_provider_invoked=true_factor_research_auto_quant_handoff_and_prepare`
- `provider_requested=IBKR,TradingViewRemix/TVR,yfinance/YF,Kraken,Binance,Bybit`
- `provider_data_acquired=yfinance:NQ=F_1h_642_rows;ibkr:QQQ_1d_21_rows_via_101138_uv_fetch;kraken:XBTUSD_1h_721_rows;binance:BTCUSDT_1h_985_rows;bybit:BTCUSDT_linear_1h_985_rows`
- `provider_unreachable=TradingViewRemix/TVR:get_ohlcv_failed;default_IBKR_harness:redis_missing_but_uv_fetch_succeeded_elsewhere`
- `local_cache_replay=false`
- `provider_sidecar_replay=true`, because the local JSON input was generated from the provider-owned Yahoo `NQ=F` CSV and remains tied to the provider acquisition artifact.

## Evidence

- Provider matrix: `docs/experiments/actionable-regime-confidence/runs/20260512T102018+0800-codex-board-a-aq-provider-authority-readback-v1/board-a-aq-provider-authority-readback-v1/provider_matrix_v1.csv`
- Provider input summary: `docs/experiments/actionable-regime-confidence/runs/20260512T102018+0800-codex-board-a-aq-provider-authority-readback-v1/provider-data/yahoo_nq_f_1h_candles_summary.json`
- Provider candle JSON consumed by ict-engine/AQ handoff: `docs/experiments/actionable-regime-confidence/runs/20260512T102018+0800-codex-board-a-aq-provider-authority-readback-v1/provider-data/yahoo_nq_f_1h_candles.json`
- AQ handoff artifact: `docs/experiments/actionable-regime-confidence/runs/20260512T102018+0800-codex-board-a-aq-provider-authority-readback-v1/state_board_a_aq_provider_readback_v1/NQ/auto_quant_handoff.factor_research.json`
- AQ status after prepare: `docs/experiments/actionable-regime-confidence/runs/20260512T102018+0800-codex-board-a-aq-provider-authority-readback-v1/command-output/08_auto_quant_status_after_prepare_retry.out`
- Raw command outputs: `docs/experiments/actionable-regime-confidence/runs/20260512T102018+0800-codex-board-a-aq-provider-authority-readback-v1/command-output`

## Readback

The AQ dependency is pinned to `34ba6b6ee6aa69813a50a72158d4c089d97afb96`. `factor-research --backend auto-quant` created the Board A handoff for symbol `NQ` and objective `board_a_regime_provider_authority`. The retry `auto-quant-prepare` moved the isolated workspace from `dependency_ready_data_missing` to `dependency_ready_data_ready`, with `data_ready=true`.

Prepared AQ data files:

- `NQ_USD-1d.feather`
- `NQ_USD-1h.feather`
- `NQ_USD-4h.feather`

## Gate

- `pass:board_a_auto_quant_handoff_created`
- `pass:provider_yfinance_nq_csv_replayed_as_provider_provenanced_sidecar`
- `pass:auto_quant_prepare_dependency_ready_data_ready`
- `partial:provider_matrix_yfinance_ibkr_kraken_binance_bybit_acquired_tvr_unreachable`
- `fail_closed:no_regime_promotion_from_readback`
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_promotion_rerun`
- `promotion_allowed=false`
- `update_goal=false`

## Next

Keep Board A blocked on the existing R6 source/control approval and owner-export gates. When those gates unlock, rerun the ordered chain with AQ/provider routing first, then regime packet calibration, then Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree readback. Do not treat repo-local/static data as a substitute for the AQ/provider path.
