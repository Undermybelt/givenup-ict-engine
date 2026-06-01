# Regime-rooted IBKR QQQ overlay Gate 1 negative sample - 2026-05-19

Context:
- Branch: `US -> equity_etf -> QQQ -> 1m -> Trend -> SessionLiquidity -> intraday_micro_trend_reclaim_density -> ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1 -> transition_stability_pda_alignment_overlay_v1`
- Provider: fresh IBKR, no cache replay.
- Ladder covered: `1m/5m/15m/30m/1h/4h/1d`.
- Auto-Quant rank rows: 21.
- Branch fields preserved through AQ: `true`.

Decision:
- `drop_gate1_no_1m_cost_density`.
- Do not proceed to Pre-Bayes, BBN, CatBoost, or execution tree.

Key result:
- Best 1m origin row: `stable_balanced/QQQ/1m`, 9 trades, raw `+0.18%`, 1bps/side `0.00%`, 2bps/side `-0.18%`.
- 1m 2bps/side survivors: none.
- Positive sibling/context rows existed:
  - `stable_balanced/QQQ/1h`: 6 trades, raw `+0.91%`, 2bps/side `+0.67%`, 5bps/side `+0.31%`.
  - `stable_dense/QQQ/1h`: 9 trades, raw `+0.83%`, 2bps/side `+0.47%`, 5bps/side `-0.07%`.
  - `pda_quality/QQQ/5m`: 11 trades, raw `+0.91%`, 2bps/side `+0.47%`, 5bps/side `-0.19%`.
  - `stable_balanced/QQQ/5m`: 18 trades, raw `+1.25%`, 2bps/side `+0.53%`, 5bps/side `-0.55%`.
- 4h/1d produced zero trades.

Lesson:
- When the requested root is explicitly `1m`, positive 5m/1h siblings are context only. They may justify a new independent sibling-root experiment, but they must not rescue or promote the failed 1m root.
- A branch can have perfect branch-field parity and full timeframe coverage while still failing Gate 1 because the root timeframe has no cost-stressed survivor.
- Stop downstream immediately when the exact root timeframe fails cost-density; set `pre_bayes_allowed=false`, `bbn_allowed=false`, `catboost_allowed=false`, `execution_tree_allowed=false`, `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.

Reusable next move:
- If 5m/1h context survives cost stress, open a new sibling root such as `US -> equity_etf -> QQQ -> 5m -> Trend -> SessionLiquidity -> stable_balanced_transition_pda_reclaim_5m_v1` instead of stacking more overlays onto the failed 1m branch.
- If continuing the 1m root, change to a materially denser 1m entry family; do not tighten the existing overlay.
