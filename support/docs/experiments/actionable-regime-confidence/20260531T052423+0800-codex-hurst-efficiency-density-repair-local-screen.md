# Hurst Efficiency Density Repair Local Screen

- created_at: `2026-05-31T05:24:23+0800`
- owner: `codex`
- agent_name: `codex-hurst-efficiency-density-repair-local-screen-20260531T052423+0800`
- run_root: `/tmp/ict-engine-hurst-efficiency-density-repair-local-screen-20260531T052423+0800`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T052423+0800-codex-hurst-efficiency-density-repair-local-screen.claim`
- workdoc: `/tmp/ict-engine-hurst-efficiency-density-repair-local-screen-20260531T052423+0800/workdoc.md`
- parent_root: `/tmp/ict-engine-hurst-efficiency-trend-reacceleration-filter-local-screen-20260530T204009+0800`
- repo_packet: `support/docs/experiments/actionable-regime-confidence/runs/20260531T052423+0800-codex-hurst-efficiency-density-repair-local-screen-v1`
- factor_id: `tomac_idxfut_clean_hurst_efficiency_density_repair_v1`
- branch_path: `TrendExpansion -> HurstEfficiencyPersistence -> CompressionPause -> ReaccelerationBreakout -> DensityRepair -> tomac_idxfut_clean_hurst_efficiency_density_repair_v1`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`

## Purpose

The parent Hurst-efficiency trend screen produced verified-cost positive but
sparse NQ rows. This slice tests a non-colliding local-only density repair using
retained TOMAC NQ data. It does not launch provider, IBKR, Auto-Quant,
Freqtrade/TOMAC, paper/live, or downstream lifecycle commands because the same
turn compact audit reported a foreign low-vol AQ live root.

## Parent Evidence

- parent_terminal_metrics: `/tmp/ict-engine-hurst-efficiency-trend-reacceleration-filter-local-screen-20260530T204009+0800/checks/terminal_metrics.json`
- parent_best_sparse_rows: NQ `30m` loose state, NQ `15m` loose state, NQ `5m`
  loose state, and NQ `1h` balanced all survived verified instrument cost but
  failed density.
- parent_verdict: `terminalized_sparse_positive_local_screen_no_aq_launch`
- parent_promotion_allowed: `false`
- parent_trade_usable: `false`

## Gate Policy

- local screen evidence can only create an exact-AQ candidate, never a practical
  factor.
- later AQ/provider launch requires same-turn compact audit and focused process
  table to show no foreign runtime owner.
- `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false` until
  exact AQ, provider/downstream, validation, execution materialization, and the
  practical lifecycle packet all pass.

## Local Command

```bash
python3 /tmp/ict-engine-hurst-efficiency-density-repair-local-screen-20260531T052423+0800/scripts/hurst_efficiency_density_repair_local_screen.py \
  --root /tmp/ict-engine-hurst-efficiency-density-repair-local-screen-20260531T052423+0800
```

## Evidence

- terminal_metrics: `/tmp/ict-engine-hurst-efficiency-density-repair-local-screen-20260531T052423+0800/checks/terminal_metrics.json`
- local_screen_summary: `/tmp/ict-engine-hurst-efficiency-density-repair-local-screen-20260531T052423+0800/checks/local_screen_summary.json`
- leaderboard: `/tmp/ict-engine-hurst-efficiency-density-repair-local-screen-20260531T052423+0800/materials/leaderboard.csv`
- local_gate1_candidates: `/tmp/ict-engine-hurst-efficiency-density-repair-local-screen-20260531T052423+0800/summaries/local_gate1_candidates.csv`
- terminal_decision_summary: `/tmp/ict-engine-hurst-efficiency-density-repair-local-screen-20260531T052423+0800/summaries/terminal_decision_summary.md`
- repo_terminal_metrics: `support/docs/experiments/actionable-regime-confidence/runs/20260531T052423+0800-codex-hurst-efficiency-density-repair-local-screen-v1/checks/terminal_metrics.json`
- repo_terminal_decision_summary: `support/docs/experiments/actionable-regime-confidence/runs/20260531T052423+0800-codex-hurst-efficiency-density-repair-local-screen-v1/summaries/terminal_decision_summary.md`

## Status

- status: `terminalized_local_screen_complete_no_backend_launch`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Terminal Readback

- terminalized_at: `2026-05-31T05:27:00+0800`
- terminal_metrics: `/tmp/ict-engine-hurst-efficiency-density-repair-local-screen-20260531T052423+0800/checks/terminal_metrics.json`
- terminal_decision_summary: `/tmp/ict-engine-hurst-efficiency-density-repair-local-screen-20260531T052423+0800/summaries/terminal_decision_summary.md`
- local_gate1_candidate_count: `2`
- survives_instrument_cost_count: `5`
- provider_fetch_started: `false`
- ibkr_historical_started: `false`
- autoquant_launched: `false`
- downstream_lifecycle_started: `false`
- decision: `local_gate1_candidate_needs_collision_free_exact_aq`

Local candidate rows:

| symbol | timeframe | context | variant | trades | trades/day | PF | raw_total_profit_pct | instrument_cost_total_profit_pct | years_positive |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| `NQ` | `5m` | `15m` | `nq5m_microbreak_fast` | 589 | 0.378778 | 1.275140 | 14.413753 | 13.552642 | 5/5 |
| `NQ` | `5m` | `15m` | `nq5m_reclaim_fast` | 333 | 0.214148 | 1.439160 | 12.476664 | 11.989821 | 5/5 |

Next gate: after the low-vol AQ owner exits and a fresh compact audit/process
guard is clear, convert this exact branch into an exact AQ wrapper or prep
packet. Until exact AQ, provider/downstream replay, validation, execution
materialization, and practical lifecycle evidence pass, this remains candidate
evidence only.
