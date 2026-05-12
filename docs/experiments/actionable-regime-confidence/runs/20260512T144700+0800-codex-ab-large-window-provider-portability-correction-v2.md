# A/B Large-Window Provider-Portability Direction Correction v2

Date: 2026-05-12T14:47:00+0800

Scope:
- Board A actionable regime confidence.
- Board B regime-conditional Auto-Quant profitability.
- Hot-plug personal data / factor release handoff.

Correction:
- Fifteen years of one-minute candles is not a public hard requirement. It is the high-quality local reference class for what enough evidence can look like.
- The actual requirement is to maximize feasible history, candle count, and trade observations before training or promoting a factor.
- Daily bars over a few days or a few dozen candles are not acceptable factor-training evidence.
- Low trade counts such as 77 NQ trades, 115 ES trades, 153 aggregate trades, 192 aggregate trades, or 224 aggregate trades are smoke/support evidence only, not a stable Board A or Board B acceptance basis.
- Provider-backed acquisition is the consumer path. The agent should request the largest feasible windows from existing providers first, including yfinance, IBKR, TradingViewRemix/TVR, Kraken, Binance, and Bybit as applicable.
- If a provider cannot supply the requested window or interval, record the provider limitation and try the next provider/window. Do not silently fall back to tiny daily samples.
- Maintainer-local long-history data is allowed for training, hardening, and factor discovery, but it cannot become a required consumer input.
- A locally trained factor is only useful for release if it becomes portable: built into ICT Engine, emitted as hot-pluggable agent material, or paired with a provider-backed data recipe that consumers can run without maintainer-local files.
- A/B evidence must remain keyed by regime and branch, not only aggregate Sharpe, aggregate win rate, or aggregate TOMAC family metrics.
- The output must flow back into the stack: Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution tree.

Operational rule:
- Before the next A/B promotion attempt, choose a data window by this order:
  1. Largest feasible provider-backed historical window at the target interval.
  2. If the provider interval is capped, use the largest lower-resolution provider window that still yields enough candles and trade observations.
  3. Use maintainer-local long-history data for training/stress only when the resulting factor has a portable delivery path.
  4. Treat short-window daily candles and tiny trade samples as diagnostics, never as acceptance evidence.

Gate:
- `direction_correction:large_window_not_short_daily`.
- `direction_correction:provider_first_consumer_path`.
- `direction_correction:local_training_allowed_if_portable`.
- `direction_correction:low_trade_samples_smoke_only`.
- `direction_correction:regime_branch_keyed_required`.
- `direction_correction:bbn_catboost_execution_tree_feedback_required`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.
