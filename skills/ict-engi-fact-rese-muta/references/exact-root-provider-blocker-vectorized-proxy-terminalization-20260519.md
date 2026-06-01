# Exact-root provider blocker + vectorized proxy terminalization

Use when a regime-rooted profitability-factor run has sibling/context provider rows and vectorized proxy results, but the exact root timeframe (usually `1m`) has no real provider rows.

Session pattern:
- Branch: `US -> equity_sector_etf -> XLU -> 1m -> Range -> DefensiveLiquidity -> vwap_reclaim_density -> yf_xlu_defensive_utilities_vwap_reclaim_autoresearch_1m_mtf_v1`
- Fresh provider: yfinance/YF, `local_cache_replay=false`
- Exact root: `1m` returned `0` rows / provider exit failure
- Missing context: `4h` unavailable through YF contract; not synthesized
- Sibling/context frames existed: `5m/15m/30m/1h/1d`
- Vectorized proxy showed one positive sibling (`15m`) but was not Auto-Quant Gate 1 proof for the `1m` root

Required handling:
1. Terminalize the exact-root run as `blocked_exact_1m_root_no_downstream` or equivalent.
2. Write/read back `checks/terminal_metrics.json` and `summaries/terminal_decision_summary.md` even if the original runner only produced provider/proxy summaries.
3. Close the active claim with `status=done` and the exact blocker/result.
4. Set all downstream booleans false:
   - `pre_bayes_allowed=false`
   - `bbn_allowed=false`
   - `catboost_allowed=false`
   - `execution_tree_allowed=false`
   - `promotion_allowed=false`
   - `trade_usable=false`
   - `update_goal=false`
5. Treat positive sibling/context frames as observation only. They may seed a new exact timeframe root, but they do not rescue the failed root.

Do not:
- Promote vectorized proxy output as Auto-Quant evidence.
- Use a positive `15m`/`30m` proxy to open BBN/CatBoost/execution-tree for a missing `1m` root.
- Fabricate unsupported `4h` rows or silently substitute another timeframe.

Next-step choices:
- Rerun with a provider/window that yields real `1m` rows for the same exact root.
- Or restart the positive sibling as its own exact branch, e.g. `... -> XLU -> 15m -> ...`, with fresh provider/AQ Gate 1 evidence.
