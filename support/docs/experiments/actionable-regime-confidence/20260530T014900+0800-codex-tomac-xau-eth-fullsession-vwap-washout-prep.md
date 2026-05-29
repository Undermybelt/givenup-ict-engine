# TOMAC XAU ETH Full-Session VWAP Washout Prep

- created_at: `2026-05-30T01:49:00+08:00`
- agent_name: `codex-eth-fullsession-xau-vwap-washout-prep-20260530T014900`
- repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- run_root: `/tmp/ict-engine-tomac-xau-eth-fullsession-vwap-washout-prep-20260530T014900+0800`
- workdoc: `/tmp/ict-engine-tomac-xau-eth-fullsession-vwap-washout-prep-20260530T014900+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T014900+0800-codex-tomac-xau-eth-fullsession-vwap-washout-prep.claim`
- session_scope: `ETH/full_retained_session`
- status: `terminalized_exact_eth_fullsession_gate1_no_5bps_survivor`

## Target

Train a profitability factor for the retained extended-hours session, not an RTH-only window. The selected rooted family is XAU/GC futures from local TOMAC Databento GLBX data, using the existing direct Auto-Quant surface:

- script: `support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_xau_local_regime_rooted_mtf_gate1_v1.py`
- source data: `/Users/thrill3r/Downloads/Tomac/xau future 2021-2025/glbx-mdp3-20210106-20260105.ohlcv-1m.csv`
- origin timeframe: `1m`
- context ladder: `5m,15m,30m,1h,4h,1d`
- selected families:
  - `tomac_xau_vwap_washout_reclaim_1m_v1`
  - `tomac_xau_compression_breakout_1m_v1`
  - `tomac_xau_ema_pullback_reclaim_1m_v1`
  - `tomac_xau_wide_range_breakout_retest_1m_v1`
- variants: `dense,balanced,quality`

## Non-Goals

- Do not count or promote RTH-only results.
- Do not use the script's `tomac_xau_opening_drive_rvol_reclaim_1m_v1` family for this lane; that family has explicit RTH-like opening/regular-session windows.
- Do not treat Ethereum/ETHUSDT crypto lanes as satisfying this request; here `ETH` means extended trading hours/full retained session.
- Do not set `promotion_allowed=true`, `trade_usable=true`, or `update_goal=true` from this prep packet.

## Launch Command

Run only after `python3 support/scripts/factor_claim_terminalization_audit.py --compact` shows no foreign live factor/backend processes and this claim is the only relevant active owner for the run root:

```bash
python3 support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_xau_local_regime_rooted_mtf_gate1_v1.py \
  --timeframes 1m \
  --families tomac_xau_vwap_washout_reclaim_1m_v1,tomac_xau_compression_breakout_1m_v1,tomac_xau_ema_pullback_reclaim_1m_v1,tomac_xau_wide_range_breakout_retest_1m_v1 \
  --variants dense,balanced,quality \
  --top-n 12 \
  --run-label eth_full_retained_session_no_rth
```

## Current Blocker

At preparation time, compact audit reported foreign live factor/runtime roots:

- `support/docs/experiments/actionable-regime-confidence/runs/20260530T014643+0800-codex-yf-us-equity-52week-high-regime-reclaim-1m-mtf-v1`
- `support/docs/experiments/actionable-regime-confidence/runs/20260530T014751+0800-codex-ibkr-mgc1m-kalman-vwap-slope-reclaim-full-ladder-gate1-v1`

The lane was initially staged as prep-only. After those foreign roots cleared, the focused XAU/GC ETH/full-retained-session Gate 1 was launched under the run root above.

## Terminal Readback

- terminal_decision: `observation_gate1_no_practical_5bps_density_survivor`
- terminal_metrics: `/tmp/ict-engine-tomac-xau-eth-fullsession-vwap-washout-prep-20260530T014900+0800/checks/terminal_metrics.json`
- compact_terminal_metrics: `support/docs/experiments/actionable-regime-confidence/runs/20260530T014900+0800-codex-tomac-xau-eth-fullsession-vwap-washout-prep/checks/terminal_metrics.json`
- rank_rows_csv: `support/docs/experiments/actionable-regime-confidence/runs/20260530T014900+0800-codex-tomac-xau-eth-fullsession-vwap-washout-prep/summaries/rank_rows.csv`
- command_exits_all_zero: `true`
- command_timeouts_any: `false`
- rank_rows: `12`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- staged_1m_rows: `1769524`
- retained_rows_outside_ny_0820_1330_rth_comparison: `1368608`
- retained_rows_inside_ny_0820_1330_rth_comparison: `400916`
- outside_rth_retained_first_last: `2021-01-06T00:00:00+00:00` -> `2026-01-05T23:59:00+00:00`
- exact_mtf_survivors_2bps: `[]`
- exact_mtf_survivors_5bps: `[]`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

Top raw candidates were the VWAP washout variants, but all failed cost and density. The only density-target hit was `tomac_xau_wide_range_breakout_retest_1m_v1_dense` with `1.027301` trades/day, but it was raw negative and 5bps negative.

## Practical Flags

- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

Gate 1 plus downstream lifecycle evidence is still required before any practical flag can become true.

Do not rerun this exact packet unchanged.
