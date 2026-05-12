# Long-History Evidence Ladder Correction v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T134339+0800-codex-long-history-1m-contract-inventory-v1`

## Correction

The user clarified that `15 years of 1m data` is not a hard pass/fail requirement for every run. It is the benchmark for seriousness and the direction the boards must enforce: use the largest feasible history and highest useful frequency before making claims, instead of treating a few daily bars or a few days of hourly bars as meaningful validation.

This correction supersedes any wording in `long_history_1m_contract_inventory_v1.md` or the Board A/B writebacks that reads like a rigid `15y/1m or nothing` gate.

## Evidence Ladder

Preferred evidence order:

1. Longest feasible 1m or intraday history, with chronological and walk-forward splits.
2. If full 1m is too expensive or unavailable, use the longest feasible lower-frequency intraday data, and explicitly record what was skipped and why.
3. If only daily or short-window provider overlap is available, use it only as provider/plumbing diagnostics, not as a regime-confidence or profitability conclusion.
4. For every downgrade, record the lost coverage: years, markets, timeframes, providers, and chain layers.

## Board Semantics

Board A should require seriousness of validation, not a brittle impossible gate. Each regime claim must show that the agent tried to maximize span and sample size, then report calibrated confidence and lower bounds under the best feasible evidence actually run.

Board B should apply the same idea to profitability. A strategy candidate cannot be promoted from a tiny backtest or low trade count, but if a full 15-year 1m run is not feasible in one slice, the agent should run the largest practical slice and mark the remaining span/provider/timeframe gaps as open work.

## Current Status

This packet does not accept any regime, profitability candidate, or execution path. It only corrects the contract language:

- `15y_1m_role=target_benchmark_not_hard_gate`
- `short_window_role=diagnostic_only`
- `downgrade_allowed=true_with_explicit_gap_accounting`
- `promotion_allowed=false_without_sufficient_span_sample_and_chain_evidence`
- `update_goal=false`
