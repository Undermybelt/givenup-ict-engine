# TOMAC Sequential Betting Trend Admission Rerun Readback

- agent_name: `codex-tomac-sequential-betting-trend-admission-rerun-20260531T102214+0800`
- factor_id: `tomac_sequential_betting_trend_admission_filter_v1`
- branch_path: `TrendExpansion -> SequentialBettingMartingale -> TrendAdmissionFilter -> tomac_sequential_betting_trend_admission_filter_v1`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- status: `terminalized_no_launch_blocked_by_foreign_claim_or_runtime`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Artifacts

- original source/prep doc: `support/docs/experiments/actionable-regime-confidence/20260531T092549+0800-codex-tomac-sequential-betting-trend-admission-local-screen.md`
- first run root: `/tmp/ict-engine-tomac-sequential-betting-trend-admission-local-screen-run-20260531T101431+0800`
- first claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T101431+0800-codex-tomac-sequential-betting-trend-admission-local-run.claim`
- rerun root: `/tmp/ict-engine-tomac-sequential-betting-trend-admission-local-screen-rerun-20260531T102214+0800`
- rerun claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T102214+0800-codex-tomac-sequential-betting-trend-admission-rerun.claim`
- rerun terminal metrics: `/tmp/ict-engine-tomac-sequential-betting-trend-admission-local-screen-rerun-20260531T102214+0800/checks/terminal_metrics.json`
- rerun terminal summary: `/tmp/ict-engine-tomac-sequential-betting-trend-admission-local-screen-rerun-20260531T102214+0800/summaries/terminal_decision_summary.md`

## Readback

The first local-screen attempt exited before the factor script executed. Root
cause was the dynamic import wrapper: Python 3.13 `dataclasses` requires the
loaded module to be present in `sys.modules` before `spec.loader.exec_module`.
No metrics, screen rows, trades, provider fetch, IBKR historical, AutoQuant,
paper/sim/live, or downstream lifecycle artifacts were produced by that attempt.

A second fresh rerun claim and run root were created with a corrected import
shim. The final prelaunch full audit for the rerun returned `needs_attention`
before launch:

- active_claims: `2`
- valid_active_claims: `2`
- live_factor_processes: `2`
- own claim: `20260531T102214+0800-codex-tomac-sequential-betting-trend-admission-rerun.claim`
- foreign active claim: `20260531T102223+0800-codex-ehlers-autocorr-periodogram-cycle-regime-30m-exact-aq.claim`
- foreign live root: `/tmp/ict-engine-trend-magic-cci-atr-slow-long-exact-aq-nq-15m-20260531T102057+0800`
- foreign live root: `/tmp/ict-engine-ehlers-autocorr-periodogram-cycle-regime-exact-aq-20260531T102223+0800`

Per the collision contract, the local screen was not launched. The rerun packet
terminalized as `terminalized_no_launch_blocked_by_foreign_claim_or_runtime`.

## Final Current-State Audit

After terminalizing both sequential-betting claims, compact audit no longer
showed this lane as active. It did show newer foreign fresh active claims:

- `20260531T102334+0800-codex-price-stiffness-density-trend-carry-aq-nq-1h.claim`
- `20260531T102413+0800-codex-nq-compound-accepted-feedback-runtime.claim`

Those claims block a new runtime launch window. No `promotion_allowed=true` or
`trade_usable=true` evidence was produced in this slice.

## Next Gate

When compact audit and focused process readback are both clean again, the
prepared sequential-betting local screen can be retried under a new run root
with the corrected `sys.modules[spec.name] = module` import shim before
`exec_module`.
