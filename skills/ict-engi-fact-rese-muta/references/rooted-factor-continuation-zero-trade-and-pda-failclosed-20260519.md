# 2026-05-19 rooted factor continuation: zero-trade overlay and downstream fail-closed

Session lesson for `ict-engi-fact-rese-muta`.

## Context
User asked to continue live-profit factor training with strict regime-rooted branch grammar:
`market -> product -> symbol -> base_timeframe -> main_regime -> sub_regime... -> first_profit_factor -> overlays...`.

Loaded route: `sd/ict-engi-fact-rese-muta`.

## What was attempted

### 1. Same-root PDA/stability overlay on TVR XLB
Script:
`support/docs/experiments/actionable-regime-confidence/scripts/run_tvr_xlb_pda_stability_directional_separation_v1.py`

Run root:
`support/docs/experiments/actionable-regime-confidence/runs/20260519T133519+0800-codex-tvr-xlb-pda-stability-directional-separation-v1`

Evidence:
- Provider/status and all timeframe fetches exited 0 for `1m/5m/15m/30m/1h/4h/1d`.
- Auto-Quant batch/dispatch/rank exited 0.
- Rank rows:
  - `1m`: completed, `trade_count=0`, `sharpe=0.0`
  - `5m`: completed, `trade_count=0`, `sharpe=0.0`
  - `15m`: completed, `trade_count=0`, `sharpe=0.0`
  - `30m`: completed, `trade_count=0`, `sharpe=0.0`
  - `1h`: completed, `trade_count=0`, `sharpe=0.0`
  - `4h/1d`: failed
- Terminal decision: `drop_or_block_gate1_practical`.

Durable lesson:
A same-root PDA/stability overlay that compiles, fetches, and ranks cleanly but yields zero trades across all practical low/medium frames is a factor-gate failure, not a downstream candidate. Do not proceed to Pre-Bayes/BBN/CatBoost/execution tree. Pivot to a less restrictive density-producing entry family under the same regime root, or restart a separate exact timeframe root if a higher timeframe earns independent evidence.

### 2. Public Elder Impulse MACD downstream replay
Script:
`support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_public_elder_impulse_downstream_v1.py`

Existing run root:
`support/docs/experiments/actionable-regime-confidence/runs/20260517T212946+0800-codex-ibkr-public-elder-impulse-macd-ladder-v1`

Evidence:
- Gate 1 had nonzero trade rows: `rank_nonzero_trade_rows=5`, `rank_total_trade_count=566`.
- Branch path survived structurally:
  `TrendExpansion -> MomentumPersistence -> public_elder_impulse_macd_histogram -> ibkr_public_elder_impulse_macd_histogram_v1`
- Pre-Bayes showed `gate_status=pass_neutralized`.
- CatBoost/path ranker reported `runtime_selection_ready=true`.
- Execution tree still failed closed:
  - `closed_loop_branch_admission_status=fail_closed`
  - `execution_gate_status=execution_blocked`
  - `review_status=observe`
  - `analyze_execution_triage_branch=transition_guardrail`
  - `analyze_decision_hint=execution_guarded_due_to_pda_hybrid_disagreement`
- Objective remained `trade_usable=false`, `promotion_allowed=false`, `update_goal=false`.

Durable lesson:
A branch can have solid Gate 1 density, pass neutralized Pre-Bayes, and have CatBoost/path-ranker visibility, yet still be non-tradable if the live execution-tree readback fails transition/readiness/materialization predicates. Treat this as exact-branch observation evidence. Next iteration should target the current active blockers from source/readback, not lower gates or claim live readiness.

## Practical rule
When all or most downstream boolean gates are false, reverse the booleans into the first failed rooted-path prerequisite:
1. zero/sparse real-cost trade density -> stop before downstream;
2. exact branch absent or sibling path selected -> same-root parity failure;
3. PDA/hybrid disagreement or transition guardrail -> observation only, design overlay for alignment;
4. `execution_readiness < 0.65` -> diagnose readiness components before more AQ sweeps;
5. cache/fallback provider used -> mark not live-ready even if AQ/downstream runs.

## Closure note
This is a class-level continuation lesson, not a new skill. Keep it under `ict-engi-fact-rese-muta` references.
