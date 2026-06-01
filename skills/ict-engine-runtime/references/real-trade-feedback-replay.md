# Real-trade feedback replay guardrails

Use when replaying real Freqtrade/Auto-Quant trades into `ict-engine update --feedback-file` for a Board B profitability branch.

## Proven pattern

1. Export actual `bt.results["strategy"][strategy]["trades"]` rows first.
2. Verify each provider slice with `sum(profit_abs) == profit_total_abs` before any replay.
3. Stamp feedback rows with branch path + provider + timeframe provenance.
4. Feed `ict-engine update` one real trade row per feedback file.
5. Use `--pnl=<negative-or-positive-value>` form, not `--pnl <value>`, when the PnL can be negative. This avoids shell/CLI parsing the leading `-` as a new flag.
6. If rerunning against an already-populated symbol state, read `state/<SYMBOL>/learning_state.json` first and skip the already-consumed prefix of feedback history instead of replaying from row 0 again.
7. Expect observation history and ranker validation to grow even when the live candidate-set ranker still reports `enabled_no_matching_scores`; replay success and live-score match are separate gates.

## Replay hygiene

- Do not replay aggregate summary rows.
- Do not collapse different providers or timeframes into one feedback stream.
- Keep `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor` intact in every replay payload.
- Record the exact replay log and the readback summary under the run root.
- If a run already has many feedback rows, prefer a deterministic skip index over ad hoc row selection so the replay remains idempotent.

## Useful evidence paths from the session

- `docs/experiments/actionable-regime-confidence/runs/20260513T193423+0800-hermes-low-hazard-reclaim-new-factor-v1/real_trade_feedback/low_hazard_reclaim_real_trade_export_summary.json`
- `docs/experiments/actionable-regime-confidence/runs/20260513T193423+0800-hermes-low-hazard-reclaim-new-factor-v1/real_trade_feedback/replay_low_hazard_real_trades.log`
- `docs/experiments/actionable-regime-confidence/runs/20260513T193423+0800-hermes-low-hazard-reclaim-new-factor-v1/summaries/low_hazard_reclaim_real_trade_feedback_replay_readback.md`
