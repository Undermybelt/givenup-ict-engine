# Non-Promoting Multicadence Rerun Readback v1

Run id: `20260512T092558+0800-codex-board-b-032157-non-promoting-multicadence-feedback-v1`

Lane labels: `incubation_only`, `non_promoting_aq_feedback`.

This is a supplemental readback for the clean rerun after Auto-Quant prepare normalized the synthetic pair to `NQ/USD`. It does not edit the current cursor, does not select user history, does not promote selected-data AutoQuant, does not run the production promotion chain, and does not call `update_goal`.

## Result

- `auto_quant_prepare_exit=0`
- `run_tomac_initial_exit=1`
- `run_tomac_rerun_exit=1`
- strategies discovered `5`; succeeded `3`; failed `2`
- successful-strategy trades total `0`
- best successful-strategy Sharpe `0.0000`
- best successful-strategy profit pct `0.0000`

| Strategy | Outcome | Trades | Sharpe | Profit % | Error |
|---|---:|---:|---:|---:|---|
| `NQMeanRevertFeedback` | succeeded | 0 | 0.0 | 0.0 |  |
| `NQTrendCarryFeedback` | succeeded | 0 | 0.0 | 0.0 |  |
| `TomacNQ_CompressionMeanRevert` | failed | 0 | N/A | N/A | No data left after adjusting for startup candles. |
| `TomacNQ_KillzoneBreakout` | succeeded | 0 | 0.0 | 0.0 |  |
| `TomacNQ_MulticadenceTrendPullback` | failed | 0 | N/A | N/A | No data left after adjusting for startup candles. |

## Interpretation

Synthetic multicadence staging is now runnable after `NQ/USD` normalization, but this local `032157/034002` slice is too short for useful Auto-Quant discovery: successful strategies emitted zero trades, and the two higher-startup strategies failed after startup-candle adjustment.

Gate: `fail_closed:incubation_only_zero_trade_short_window`.

Promotion allowed: `false`.

`update_goal=false`.

## Next

Use this as negative search feedback only. Prefer recorded historical replay or a longer explicit historical path before another Auto-Quant feedback loop; do not run production promotion from this packet.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T092558+0800-codex-board-b-032157-non-promoting-multicadence-feedback-v1/non-promoting-multicadence-rerun-readback-v1/non_promoting_multicadence_rerun_readback_v1.json`
- CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T092558+0800-codex-board-b-032157-non-promoting-multicadence-feedback-v1/non-promoting-multicadence-rerun-readback-v1/non_promoting_multicadence_rerun_readback_v1.csv`
- Raw rerun stdout/stderr: `raw/run_tomac_rerun.stdout.txt`, `raw/run_tomac_rerun.stderr.txt`

