# Sapienza Binance ict-engine Fail-Closed Summary v1

Run id: `20260511T200931+0800-codex-board-b-sapienza-binance-pnl-bridge-v1`.

- Branch/PnL gate: `fail:insufficient_positive_rows`.
- Best horizon: `6h`; positive rows `24`, control rows `72`, monthly folds `17`.
- Best-horizon edge vs controls: `-0.012033`; bootstrap 5% LCB `-0.033142`; fold positive rate vs controls `0.058824`.
- Downstream consumption: `not_started:diagnostic_only_full_board_b_still_requires_all_root_rc_spa`.
- Real-trade wire: `ict-engine-fail-closed/sapienza_binance_real_trades_wire_v1.jsonl`, `96` records from the best horizon only.
- Real-trade ingest dry-run: parsed `96/96` with `trades_invalid=0`, `force=true`, `dry_run=true`, and `feedback_records_inserted=0`.
- Pre-Bayes status: `latest_gate_status=null`, `latest_policy=null`, `latest_soft_evidence=null`.
- BBN/CatBoost policy-training status: entry models are not ready, `matched_rows=0`, structural path-ranking runtime is `disabled`, and target rows are `0`.
- Workflow/execution-tree status: no phase snapshots, `blocking_truth.status=insufficient_state`, and latest promotable artifact is `null`.
- Pre-Bayes / BBN / CatBoost / execution-tree promotion was not started because the Sapienza/Binance PnL gate failed and the full Bull/Bear/Sideways/Crisis plus scoped Manipulation Board B gate is still unmet.
- This is a fail-closed readback, not a promoted profitability packet.

Primary blocker: only `24` Sapienza positive events were attachable to currently listed Binance symbols, all tested horizons had negative lower-bound edge versus same-pump-index controls, and existing root branches still fail the five-root RC-SPA hard gate.
