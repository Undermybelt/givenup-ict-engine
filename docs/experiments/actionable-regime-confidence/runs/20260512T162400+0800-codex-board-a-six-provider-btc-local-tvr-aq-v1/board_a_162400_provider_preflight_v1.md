# Board A 162400 Provider Preflight v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1`

Provider rows:
- IBKR: acquired=False exit=1 rows=0 first= last= source_or_blocker=`ibkr_paxos_btc_1h_fetch_failed`
- TradingViewRemix/TVR: acquired=True exit=0 rows=720 first=2026-04-12 09:00:00 last=2026-05-12 08:40:53 source_or_blocker=`docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/data/normalized/tvr_btc_usd_1h.normalized.csv`
- yfinance/YF: acquired=True exit=0 rows=2135 first=2026-02-12 00:00:00 last=2026-05-11 23:00:00 source_or_blocker=`docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/data/normalized/yfinance_btc_usd_1h.normalized.csv`
- Kraken: acquired=True exit=0 rows=2000 first=2026-02-12 00:00:00 last=2026-05-06 07:00:00 source_or_blocker=`docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/data/normalized/kraken_futures_pfxbtusd_1h.normalized.csv`
- Binance: acquired=True exit=0 rows=2137 first=2026-02-12 00:00:00 last=2026-05-12 00:00:00 source_or_blocker=`docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/data/normalized/binance_btcusdt_1h.normalized.csv`
- Bybit: acquired=True exit=0 rows=1000 first=2026-03-31 09:00:00 last=2026-05-12 00:00:00 source_or_blocker=`docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/data/normalized/bybit_linear_btcusdt_1h.normalized.csv`

Decision:
- same_root_six_provider_authority=false
- auto_quant_ran=false
- pre_bayes_bbn_catboost_execution_tree_ran=false
- promotion_allowed=false
- trade_usable=false
- update_goal=false
