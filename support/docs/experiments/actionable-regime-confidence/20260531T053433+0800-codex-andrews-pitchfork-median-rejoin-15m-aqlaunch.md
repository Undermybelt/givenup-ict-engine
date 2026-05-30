# Andrews Pitchfork Median Rejoin 15m AQ Launch

- created_at: `2026-05-31T05:34:33+0800`
- owner: `codex`
- agent_name: `codex-andrews-pitchfork-median-rejoin-15m-aqlaunch-20260531T053433+0800`
- repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- branch: `main`
- route_alias: `sd/ict-engi-fact-rese-muta`
- run_root: `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aq-20260531T053433+0800`
- workdoc: `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aq-20260531T053433+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T053433+0800-codex-andrews-pitchfork-median-rejoin-15m-aqlaunch.claim`
- source_prep_doc: `support/docs/experiments/actionable-regime-confidence/20260531T050703+0800-codex-andrews-pitchfork-median-rejoin-aqprep.md`
- factor_family: `andrews_pitchfork_median_rejoin`
- candidate_class: `TomacAndrewsPitchforkMedianRejoin15mPrepV1`
- native_timeframe: `15m`
- symbols: `NQ/YM/XAU`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- status: `terminalized_aq_screen_negative`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Guard

Same-turn compact audit at `2026-05-31T05:31:39+0800` reported
`status=pass`, `active_claims=0`, `live_factor_processes=0`,
`promotion_allowed_true=0`, `trade_usable_true=0`, and
`same_tree_practical_closure=null`.

This launch uses an isolated AQ workspace under the run root. It does not modify
`/Users/thrill3r/Auto-Quant`.

## Launch Command

```bash
cd /tmp/ict-engine-andrews-pitchfork-median-rejoin-aq-20260531T053433+0800/aq_workspace
/Users/thrill3r/Auto-Quant/.venv/bin/python \
  /Users/thrill3r/projects-ict-engine/ict-engine/support/scripts/auto_quant_external/run_tomac_one.py \
  TomacAndrewsPitchforkMedianRejoin15mPrepV1 15m \
  /tmp/ict-engine-andrews-pitchfork-median-rejoin-aq-20260531T053433+0800/checks/aq_trades_andrews_pitchfork_15m.json \
  NQ/USD,YM/USD,XAU/USD 20210103-20251231
```

## Current Caveat

The strategy class is still named `PrepV1` and uses a closed-bar median-line
proxy for the pitchfork channel. Treat this run as exact-AQ engine screening of
the prepared implementation, not practical proof of a fully validated Andrews
three-pivot implementation. Practical flags must remain false unless later
evidence replaces or validates the pivot extraction and passes the full
same-tree lifecycle contract.

## Terminal Readback

- terminal_metrics: `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aq-20260531T053433+0800/checks/terminal_metrics.json`
- terminal_summary: `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aq-20260531T053433+0800/summaries/terminal_summary.md`
- AQ export: `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aq-20260531T053433+0800/checks/aq_trades_andrews_pitchfork_15m.json`
- Freqtrade backtest zip: `/tmp/ict-engine-andrews-pitchfork-median-rejoin-aq-20260531T053433+0800/aq_workspace/user_data/backtest_results/backtest-result-2026-05-31_05-37-03.zip`
- decision: `terminalized_aq_screen_negative_no_gate_survivor`
- backtest window: `2021-01-07 02:00:00` to `2025-12-31 00:00:00`
- trade_count: `234`
- trades_per_day: `0.128713`
- total_profit_pct: `-0.91`
- profit_factor: `0.981542`
- sharpe: `-0.016311`
- per-pair: `NQ/USD +3.13%`, `XAU/USD +0.39%`, `YM/USD -4.43%`
- density_target_1_to_3_per_day: `false`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

The wrapper failed to write an exit file because zsh treats `status` as
read-only. The AQ export and metrics exist, but this is fail-closed terminal
screen evidence and not a downstream/practical candidate.
