# Auto-Quant synthetic autoresearch negative seed

Session note:
- A managed Auto-Quant autoresearch handoff was prepared from IBKR MNQ 202606 1h retained rows (499 candles).
- Control plane sequence: factor-autoresearch -> auto-quant-prepare -> factor-autoresearch -> run_tomac.py.
- Resulting managed seed was not promotable.

Decision facts:
- strategy: TomacNQ_KillzoneBreakout
- pair: MNQ202606/USD
- trades: 4
- total_profit_pct: -0.55
- win_rate_pct: 50.0
- profit_factor: 0.7746
- sharpe: -0.5223
- daily_avg_trades: 0.22

Gate interpretation:
- downstream_allowed=false
- pre_bayes_allowed=false
- bbn_allowed=false
- catboost_allowed=false
- execution_tree_allowed=false
- promotion_allowed=false
- trade_usable=false
- update_goal=false

Lesson:
- Do not promote synthetic managed autoresearch seeds just because the control-plane handoff completed.
- A negative or sparse managed seed remains observation-only; keep the older exact-root survivor as observation and switch to a new exact-root factor shape.
- For regime-rooted profitability work, exact rooted path, real-cost density, and downstream direction agreement still outrank managed synthetic iteration.
