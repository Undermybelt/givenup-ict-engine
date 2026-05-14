# Provider BTC Always-Entry Canary v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T103010+0800-codex-board-b-provider-btc-always-entry-canary-v1`

Purpose: diagnostic plumbing only. This run proves the copied Binance BTC/Freqtrade harness can execute, extract, ingest, and expose nonzero trade feedback after the market-order pricing repair. It is not a profitability factor candidate and not promotion evidence.

## Provider / AQ Readback

- `aq_provider_invoked`: true, via the run-local Auto-Quant/TOMAC/Freqtrade workspace.
- `provider_requested`: Binance BTC/USDT 1h only for this slice.
- `provider_data_acquired`: true, using the copied provider-prepared BTC/USDT feathers in the run-local workspace.
- `provider_unreachable`: none observed for the invoked Binance replay path.
- `providers_not_invoked_this_slice`: IBKR, TradingViewRemix/TVR, yfinance/YF, Kraken, Bybit.
- `local_cache_replay`: true; this is a copied provider-owned workspace replay, not a fresh six-provider matrix acquisition.
- `regime_profit_branch_path`: `Bull -> ProviderPlumbing -> SignalCadence -> ProviderBtcAlwaysEntryCanary`.

## Auto-Quant / Freqtrade Result

- Signal probe: `985` rows, `82` entry labels, `81` exit labels.
- First run failed with Freqtrade requiring `entry_pricing.price_side = "other"` for market entries.
- Second run failed with Freqtrade requiring `exit_pricing.price_side = "other"` for market exits.
- Third run exited `0` after both run-local pricing repairs.
- Backtest window: `2026-04-01 01:00:00 -> 2026-05-12 00:00:00`.
- Trades: `81`; wins/losses: `43/38`; win rate: `53.1%`.
- Total profit: `441.072 USDT` / `4.41%`.
- Sharpe: `2.56`; Sortino: `3.52`; profit factor: `1.20`; max underwater: `4.98%`.

## ict-engine Ingest / Downstream

- Extracted real-trade JSONL: `derived/provider_btc_always_entry_canary_trades_v1.jsonl`.
- Extracted rows: `81`; total PnL: `441.0723246099999`; wins/losses: `43/38`.
- Dry-run ingest exited `0`: `trades_applied=81`, `trades_invalid=0`, `feedback_records_inserted=0`.
- Force ingest exited `0`: `trades_applied=81`, `trades_invalid=0`, `feedback_records_inserted=81`.
- Pre-Bayes readback exited `0`, but latest policy/gate/soft evidence/bridge are all `null`.
- Policy/path-ranker readback exited `0`: policy matched rows `0`, ranker runtime disabled, raw scored mature rows `0`, production validation `0`, observation validation `0`.
- Structural target export exited `0`: `rows=1`, `history_rows=1`, `mature_rows=0`, `history_mature_rows=0`.
- Workflow structural bundle exited `0`: `bootstrap_readiness`, `direction=observe`, `trigger_summary=No workflow snapshot exists yet`.
- Workflow execution candidate exited `0`: `ready=false`, `actionable=false`, `review_status=observe`, `review_reason=structural_recommended_path_visible_but_execution_or_pre_bayes_gate_not_ready`.

## Decision

This is useful plumbing evidence: copied provider BTC data can produce nonzero Freqtrade fills, real-trade JSONL, BBN feedback insertion, structural target export, and execution-candidate visibility.

It remains fail-closed for Board B promotion:

- diagnostic always-entry canary, not a factor or strategy candidate;
- only `81` trades, below the Board B `100`-trade liquid intraday threshold;
- no six-provider matrix evidence;
- no selected-history approval;
- no source/control unlock;
- Pre-Bayes has no active policy or gate;
- CatBoost/path-ranker has no mature validation rows and runtime is disabled;
- execution tree remains observe / not ready / not actionable.

Next: count this once as a diagnostic ingest/downstream plumbing closeout. Continue from provider-owned factor candidates or NQ/BTC tick-size repaired reruns that produce mature rooted branch observations; do not promote from this canary.
