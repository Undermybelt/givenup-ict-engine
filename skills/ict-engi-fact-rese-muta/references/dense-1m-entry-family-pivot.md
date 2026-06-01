# Dense 1m Entry Family Pivot

Use when a regime-rooted intraday branch is valid in shape but too sparse for live-practical promotion.

Observed pattern:
- Full rooted path preserved across AQ / pre-bayes / BBN / CatBoost / execution-tree plumbing.
- 1m origin survives as an observation sample but yields only 0-2 trades or otherwise fails the real-cost density gate.
- Wider overlays make the branch sparser, not better.

Action:
1. Keep the full branch identity: `market -> product -> symbol -> base_timeframe -> main_regime -> sub_regime -> ... -> first_profit_factor -> optional_overlays`.
2. Stop tightening overlays on the same sparse root.
3. Pivot to a denser 1m entry family inside the same root, usually session-liquidity / reclaim / continuation rather than opening-impulse pullback.
4. Re-run the same cost stress before any downstream handoff.
5. Keep 4h missing as a real provider gap; do not synthesize it.

Promotion rule:
- If `trade_count < 6` or 2bps/side is not positive, keep the branch as observation/incubate only.
- Dense 30m/1h siblings do not rescue a sparse 1m root.
