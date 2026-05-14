# Manipulation Stop/Take-Profit ict-engine Fail-Closed Summary v1

Run ID: `20260511T205047+0800-codex-board-b-manipulation-stop-tp-grid-v2`

- Direct Manipulation branch gate: `pass:direct_manipulation_stop_tp_candidate`
- Downstream consumption: `not_started:full_board_b_branch_gate_not_satisfied`
- Pre-Bayes / BBN / CatBoost / execution tree were not started because the full Board B five-branch RC-SPA gate is not satisfied.
- This is fail-closed direct-branch evidence, not a promoted profitability packet.

Primary blocker: full Board B still requires Bull/Bear/Sideways/Crisis plus scoped Manipulation branch gates; this run only evaluates direct Manipulation stop/take-profit action paths
