# NQ Dual Thrust MTF Breakout Screen

created_at: 2026-05-29T23:00:33+0800
owner: codex
agent_name: codex-nq-dual-thrust-mtf-breakout-screen
status: terminalized_python_gate1_smoke_negative
run_root: /tmp/ict-engine-nq-dual-thrust-mtf-breakout-screen-20260529T230033+0800
workdoc: /tmp/ict-engine-nq-dual-thrust-mtf-breakout-screen-20260529T230033+0800/workdoc.md
claim: /tmp/ict-engine-agent-claims/board-b-factor-refinement/20260529T230033+0800-codex-nq-dual-thrust-mtf-breakout-screen.claim
promotion_allowed: false
trade_usable: false
update_goal: false

## Branch

```text
US index futures / NQ / 1m
-> TrendExpansion
-> PriorRangeVolatilityBreakout
-> DualThrustMtfConfirmation
-> SwingHoldRrrExit
-> nq_dual_thrust_mtf_breakout_v1
```

## Source Intake

- GitHub repository search returned `je-suis-tm/quant-trading`, described as a Python quantitative trading strategy collection including `Dual Thrust`.
- GitHub repository search returned `soham-srivastava/Dual_Thrust_Strategy`, described as previous N-bar breakout lines filtered by long-horizon EMA bias and ATR exits.
- External repositories are information-only sources; no clone/install/execution was performed.
- Exact local duplicate search for `Dual Thrust` / `dual_thrust` across repo experiment scripts and `/tmp` claims returned no matches before opening this lane.

## Current Plan

Run a local Python Gate1 screen from retained NQ full-ladder feathers. The screen must stay non-colliding while fresh active claims exist: no IBKR, no provider-status, no Auto-Quant, no Freqtrade, and no TOMAC runtime.

## Gate Standard

- Origin `1m`; context `5m/15m/30m/1h/4h/1d`.
- No look-ahead: prior session range and shifted HTF as-of features only.
- Positive `5bps/side` net, PF > 1, cadence between one trade per three sessions and three trades per session, and split/year stability before any downstream/AQ attempt.
- Python-only evidence cannot set `trade_usable=true`.

## Progress

- 2026-05-29T23:00:42+0800: compact audit still showed two fresh active claims and no live runtime roots, so this lane is intentionally local-screen only.
- 2026-05-29T23:06:00+0800: local runner created at `/tmp/ict-engine-nq-dual-thrust-mtf-breakout-screen-20260529T230033+0800/scripts/run_nq_dual_thrust_mtf_breakout_gate1.py`; `py_compile` and `--help` passed.
- 2026-05-29T23:08:00+0800: initial full-grid launch was stopped before metrics because it was inefficient; no economic verdict was emitted.
- 2026-05-29T23:12:29+0800: runner optimized and `py_compile` passed. Compact audit then showed foreign live runtime roots, so the prepared screen is waiting for runtime clear before execution.
- 2026-05-29T23:19:00+0800: first execution exposed a timezone-index bug; fixed lane-local runner to compare UTC epoch nanoseconds and revalidated with `py_compile`.
- 2026-05-29T23:25:00+0800: bounded source-formula smoke completed: 117 trades, trades/session 0.090768, raw +8.431172%, net 5bps/side -3.268828%, PF 0.974391, win 32.48%, positive years 2/5. OOS 2024-2025 was positive (+18.967633%, PF 1.444392), but train 2021-2023 was negative (-22.236461%) and cadence failed.
- 2026-05-29T23:26:00+0800: terminalized no-promotion. The smoke runner permits overlapping multi-day positions, so this is not a final optimized family verdict; successor work should enforce single-slot/non-overlap before any serious AQ handoff.

## Terminal Evidence

- Metrics: `/tmp/ict-engine-nq-dual-thrust-mtf-breakout-screen-20260529T230033+0800/checks/terminal_metrics.json`
- Summary: `/tmp/ict-engine-nq-dual-thrust-mtf-breakout-screen-20260529T230033+0800/summaries/terminal_packet.md`
- Trades: `/tmp/ict-engine-nq-dual-thrust-mtf-breakout-screen-20260529T230033+0800/checks/best_variant_trades.csv`

Final flags: `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`.
