# Board A SPY Session-Compression Feedback Ingress Packet - 2026-05-23

## Scope

- Board: A, regime/subclass evidence only.
- Source run: `support/docs/experiments/actionable-regime-confidence/runs/20260517T081303+0800-codex-board-a-refine-spy-session-compression-yf-tvr-smallcycle-v1/`.
- Source rank artifact: `state/auto-quant/SPY_SESSION_COMPRESSION_SMALL/auto_quant_agent_material_rank.20260517T001718.072Z.json`.
- Replay run: `support/docs/experiments/actionable-regime-confidence/runs/20260523T064047Z-codex-board-a-positive-negative-feedback-ingress-v1/`.
- Runner: `support/docs/experiments/actionable-regime-confidence/scripts/run_board_a_positive_negative_feedback_ingress_v1.py`.
- Symbol bucket: `BOARD_A_SPY_SESSION_COMPRESSION_SMALL_FEEDBACK_20260523`.
- Candidate set: `board-a-spy-session-compression-positive-negative-feedback-v1`.

This replay consumes existing Board A Auto-Quant rank rows and sends both wins
and losses through `structural-feedback-v1` plus `ict-engine update
--feedback-file`. It does not open a Board B profitability lane and does not
promote a trade.

## Rooted Branch

```text
TrendExpansion -> SessionLiquidity -> session_compression_breakout -> session_compression_breakout_spy_5m_v1
```

## Executed Chain

- `emit-probe` wrote one positive Bayesian-evidence feedback file and two
  negative-boundary feedback files; all exits were `0`.
- `ict-engine update --feedback-file` ingested all three feedback files; all
  exits were `0`.
- Readbacks all exited `0`: `workflow-status`, `pre-bayes-status`,
  `policy-training-status`, and `export-structural-path-ranking-target`.

## Evidence Counts

- Source AQ rank rows: `3`.
- Positive target rows: `1`.
- Negative boundary target rows: `2`.
- Selected feedback rows: `3`.
- Learning state feedback history: `3`.
- Unique structural path ids: `3`.
- Auto-Quant real-trade feedback entry model: `matched_rows=3`,
  `structural_feedback_rows=3`, `outcomes=loss=2,win=1`.
- Structural path ranking target: `rows=6`, `history_rows=12`,
  `mature_rows=6`, `history_mature_rows=9`, `rows_with_raw_path_score=3`,
  `rows_with_training_weight=6`.
- Validation readback: `raw_scored_mature=3/30`,
  `production_validation=0/30`, `observation_validation=3/30`.
- Calibration/runtime readback: `calibration=not_fitted`,
  `trainer_artifact=missing`, `runtime_selection=disabled`,
  `runtime_matches=0`.

## Decision

Keep as Board A rooted-regime/subclass feedback evidence. The positive row
strengthens the `TrendExpansion -> SessionLiquidity` branch evidence; the two
loss rows are negative-boundary samples for the same branch family.

This remains observation/incubate only. It is not root-regime registration, not
`95%` bull/bear/root confidence, not CatBoost/runtime admission, not an
execution-tree promotion, and not a tradeable/profitability factor.
