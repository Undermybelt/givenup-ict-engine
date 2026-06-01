# MNQ regime-rooted failed-expansion note

Date: 2026-05-19
Scope: IBKR MNQ 202606, 30m and 1h lanes, regime-rooted Gate 1 training.

What happened
- Ran two exact-root families under the same rooted grammar:
  - `FUTURES -> equity_index -> MNQ -> 30m -> TrendExpansion -> VolatilityCompressionExpansion -> ibkr_mnq_low_turnover_vol_expansion_gate1_v1`
  - `FUTURES -> equity_index -> MNQ -> 30m/1h -> TrendExpansion -> FailedBreakoutFade -> ibkr_mnq_short_failed_expansion_fade_gate1_v1`
- Both families passed provider fetch, strategy compile, AQ batch, dispatch, and rank, but none produced positive 2bps/side survivors.
- Cost-stressed outcome: `survivors_2bps=[]`, `survivors_5bps=[]`, `downstream_allowed=false`.
- Interpretation: 30m/1h expansion/fade shapes on this root are observation-only. Do not keep grinding the same family.

Reusable lesson
- When a rooted lane stays negative after fair AQ + cost stress, pivot to a denser root family instead of widening overlays.
- For this user's regime-rooted work, preserve the branch grammar but change the actual first profit factor family when density fails.
- Use 1m-origin families first when feasible; keep 5m/15m/30m/1h/4h/1d as explicit sibling/context lanes, not as excuses to promote a sparse root.
