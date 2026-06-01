# TOD slot alpha practicalization pivot

## Trigger
Use when a regime-rooted TOD / intraday seasonality factor has a positive Auto-Quant Gate 1 row but downstream execution remains fail-closed or observe-only.

## Durable lesson
Do not force a sparse TOD branch through live promotion. First diagnose exact blockers, then either collect enough same-branch feedback rows or pivot to a more trade-dense candidate family under a new rooted branch.

## Required audit before promotion
- Check `closed_loop_branch_admission.status`, `execution_gate_status`, `execution_tree_branch`, and `decision_hint`.
- Compute `execution_readiness` shortfall against the ready threshold.
- Verify `ranker_validation_ready`, `raw_scored_mature`, `production_validation`, `observation_validation`, and policy `matched_rows`.
- Replay the exact signal logic into per-trade feedback rows; aggregate Auto-Quant rank rows are not enough.
- If exact replay has sparse signals or mixed outcomes, terminalize as incubate instead of lowering gates.

## Practical pivot pattern
1. Preserve the original branch as incubate with exact failure evidence.
2. Run `auto-quant-prepare` and a small seed strategy set only after reading the local Auto-Quant `program.md` contract.
3. Prefer trade-dense candidates that pass profit, drawdown, and robustness gates across regime slices.
4. Treat a strong slice as a candidate-family lead, not live-ready, until it passes the ict-engine chain: AQ Gate 1 -> feedback rows -> BBN -> CatBoost/path-ranker -> execution tree.
5. If a candidate is strong only in one slice (for example bull-only) or fails robust/profit-floor gates, create a new regime-rooted branch and keep the decision scoped.

## Example evidence shape
- Sparse TOD branch: exact replay produced only 12 signals, mixed win/loss/breakeven, and `raw_scored_mature=0/30`; verdict `incubate`.
- Practical probe: a trade-dense Auto-Quant seed such as `CrashRebound` may show attractive slice metrics, but remains only a candidate-family lead unless full robust and downstream gates pass.
