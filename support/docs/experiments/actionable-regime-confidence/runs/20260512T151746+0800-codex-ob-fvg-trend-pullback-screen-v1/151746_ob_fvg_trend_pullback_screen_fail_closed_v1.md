# 151746 OB/FVG Trend Pullback Screen Fail-Closed v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T151746+0800-codex-ob-fvg-trend-pullback-screen-v1/`

## Evidence

- Manifest: `summaries/ob_fvg_screen_manifest.json`
- Summary: `summaries/ob_fvg_summary.csv`
- Top candidates: `summaries/ob_fvg_top_candidates.csv`
- Signal rows: `summaries/ob_fvg_signal_rows.csv`
- Command output: `command-output/01_ob_fvg_screen.out`

## Readback

- Evidence class is `screen_only_ohlcv_proxy`.
- Sources are Binance `BTCUSDT` 1h (`76,429` bars), IBKR `SPY` 1h (`20,034` bars), and Yahoo `ES` 1h (`11,383` bars), all sourced from the settled `143900` normalized provider data.
- The screen emitted `24,504` total OB/FVG/confluence signals, `108` summary rows, `415` fold rows, and `12` top-candidate rows.
- Best top-candidate row was `fvg_ob_pullback_resume_v1` on Binance `BTCUSDT`, branch `range_or_de_risk->high_volatility->down_or_flat_momentum->fvg_ob_pullback_resume`, with `122` trades, win rate `0.5327868852459017`, average net return `0.002397639435891284`, and profit factor `1.3735438736127317`.
- Larger-trade top rows remained weak or mixed: `fvg_retrace_continuation_v1` on Binance `BTCUSDT`, branch `trend_expansion->normal_volatility->up_momentum->fvg_retrace_continuation`, had `1,835` trades, win rate `0.49264305177111717`, and profit factor `1.034785252020533`.

## Fail-Closed Reasons

- This is a screen only, not an Auto-Quant backtest or AQ-owned/provider-routed execution packet.
- Same-root six-provider AQ authority is absent: TradingViewRemix/TVR, Kraken, and Bybit are not included.
- No filter/Pre-Bayes, BBN, CatBoost/path-ranker, calibrated path probability/lower-bound validation, or execution-tree admission was run.
- No Board A regime-confidence `>=0.95` claim is supported.

## Gate

- `support_once:151746_ob_fvg_trend_pullback_screen_v1`.
- `evidence_class:screen_only_ohlcv_proxy_not_acceptance`.
- `pass:signals_24504`.
- `pass:summary_rows_108`.
- `pass:fold_rows_415`.
- `partial:best_top_candidate_pf_1_3735_trades_122`.
- `partial:large_trade_candidate_pf_1_0348_trades_1835`.
- `fail_closed:not_auto_quant_backtest`.
- `fail_closed:not_aq_owned_or_aq_routed_execution_packet`.
- `fail_closed:same_root_six_provider_aq_authority_missing`.
- `fail_closed:missing_tvr_kraken_bybit`.
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_admission`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.
