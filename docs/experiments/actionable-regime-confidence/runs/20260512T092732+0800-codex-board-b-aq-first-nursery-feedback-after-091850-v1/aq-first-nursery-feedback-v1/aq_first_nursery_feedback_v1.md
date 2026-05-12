# Board B AQ-First Nursery Feedback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T092732+0800-codex-board-b-aq-first-nursery-feedback-after-091850-v1`

Mode: `incubation_only`

## Evidence
- Direct TOMAC backtest log: `docs/experiments/actionable-regime-confidence/runs/20260512T092732+0800-codex-board-b-aq-first-nursery-feedback-after-091850-v1/auto-quant-nursery-feedback-v1/logs/01_run_tomac.out`
- Direct TOMAC stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T092732+0800-codex-board-b-aq-first-nursery-feedback-after-091850-v1/auto-quant-nursery-feedback-v1/logs/01_run_tomac.err`

## Readback
- Strategy: `TomacNQ_KillzoneBreakout`
- Pair: `NQ/USD`
- Trades: `0`
- Total profit %: `0.0`
- Win rate %: `0.0`
- Profit factor: `0.0`
- Sharpe: `0.0`
- Max drawdown %: `0.0`

## Nursery Signal
- This is a clean zero-trade nursery rerun on the existing local TOMAC workspace.
- It is useful as negative evidence only.
- It does not improve selected-history approval, source/control unlock, or downstream promotion readiness.

## Decision
- Gate: `incubation_only_zero_trade_direct_run_tomac`
- Promotion allowed: `false`
- update_goal: `false`

## Next
- Prefer the stronger recorded-MTF AQ-first nursery packet already present in Board B for search-priority feedback.
- Keep this direct TOMAC rerun as local negative evidence only.
