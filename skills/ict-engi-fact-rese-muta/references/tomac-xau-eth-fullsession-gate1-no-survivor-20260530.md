# TOMAC XAU ETH Full-Session Gate 1 No-Survivor, 2026-05-30

## Context

The user corrected the lane scope to ETH/full retained session, not RTH. A new
Board B packet was created for XAU/GC futures using retained TOMAC Databento
GLBX data and explicitly excluded the script's opening-drive family because that
family contains RTH-like opening and regular-session windows.

## Branch Tested

- Session scope: `ETH/full_retained_session`
- Product: XAU/GC futures, highest-volume positive outright `GC*` row per
  timestamp; spread rows rejected.
- Origin timeframe: `1m`
- Context ladder: `5m/15m/30m/1h/4h/1d`, synthesized from exact staged `1m` and
  marked derived context, not independent provider proof.
- Window: `20210106-20260105`
- Staged rows: `1769524`
- Runner: `run_tomac_xau_local_regime_rooted_mtf_gate1_v1.py`
- Run root:
  `/tmp/ict-engine-tomac-xau-eth-fullsession-vwap-washout-prep-20260530T014900+0800`
- Durable packet:
  `support/docs/experiments/actionable-regime-confidence/20260530T014900+0800-codex-tomac-xau-eth-fullsession-vwap-washout-prep.md`

Families tested:

- `tomac_xau_vwap_washout_reclaim_1m_v1`
- `tomac_xau_compression_breakout_1m_v1`
- `tomac_xau_ema_pullback_reclaim_1m_v1`
- `tomac_xau_wide_range_breakout_retest_1m_v1`

Each family ran `dense`, `balanced`, and `quality` variants, 12 direct AQ
candidates total.

## Result

All 12 direct Auto-Quant commands exited `0`; no timeouts occurred.

- `rank_rows=12`
- `exact_mtf_survivors_2bps=[]`
- `exact_mtf_survivors_5bps=[]`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
- Decision: `observation_gate1_no_practical_5bps_density_survivor`

Representative rows:

- `tomac_xau_vwap_washout_reclaim_1m_v1_dense`: `72144` trades,
  `56.274571` trades/day, raw `+1250.48%`, 1bps `-192.4%`, 2bps `-1635.28%`,
  5bps `-5963.92%`.
- `tomac_xau_vwap_washout_reclaim_1m_v1_quality`: `68137` trades,
  `53.148986` trades/day, raw `+1124.92%`, 1bps `-237.82%`, 2bps `-1600.56%`,
  5bps `-5688.78%`.
- `tomac_xau_wide_range_breakout_retest_1m_v1_dense`: `1317` trades,
  `1.027301` trades/day, density target true, raw `-2.36%`, 5bps `-134.06%`.

## Lesson

Do not satisfy an ETH/full-session request with an RTH-only or opening-drive
result. If a runner contains mixed session families, filter family ids before
launch and write `session_scope` into materials, terminal metrics, workdoc, and
claim.

For XAU/GC retained full-session `1m` OHLCV:

- VWAP washout variants found large raw edge but were too high-turnover; even
  1bps/side stress made them negative.
- Compression, EMA pullback, and wide-range retest reduced turnover but had no
  positive 2bps or 5bps survivor.
- The only density-target hit was raw negative, so no downstream lifecycle gate
  should run from this exact packet.

Do not rerun this exact XAU ETH/full-session packet unchanged. A continuation
must either reduce turnover while preserving the VWAP washout raw edge or switch
to a materially different ETH/full-session branch with a new claim/workdoc.
