# Board A Completion Audit

Run id: `20260511T045938+0800-codex-board-a-completion-audit`

## Objective

/Users/thrill3r/projects-ict-engine/ict-engine/docs/plans/2026-05-10-actionable-regime-confidence-todo.md every active regime reaches >=95% confidence before reporting result

## Prompt-to-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Named TODO file owns the active Board A contract | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md Current Cursor and Active MainRegimeV2 Root Ledger` | `pass` |
| Every active completion root has calibrated 95% evidence | `docs/experiments/actionable-regime-confidence/runs/20260511T035045-codex-kaggle-bull-coverage-buffer-gate/kaggle-bull-gate/kaggle_bull_coverage_buffer_gate_report.json`<br>`docs/experiments/actionable-regime-confidence/runs/20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json`<br>`docs/experiments/actionable-regime-confidence/runs/20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json`<br>`docs/experiments/actionable-regime-confidence/runs/20260510T235220-codex-broader-root-v2-probe/root-v2-broader/main_regime_v2_broader_root_calibration_report.json`<br>`docs/experiments/actionable-regime-confidence/runs/20260511T045102-codex-mehrnoom-telegram-direct-manipulation-gate/direct-event-gate/mehrnoom_telegram_direct_manipulation_gate_report.json` | `pass` |
| Residual UnknownOrMixed is not promoted as a completion root | `Active ledger marks UnknownOrMixed residual_only` | `pass` |
| Candidate additional concepts are not silently counted as complete roots | `Active ledger marks BubbleEuphoria/LiquidityDrought/VolatilityDislocation/TransitionRecovery/CrossAssetRotation/MacroPolicyRegime preflight_only` | `pass` |
| Manipulation is accepted only from direct evidence, not OHLCV proxy | `docs/experiments/actionable-regime-confidence/runs/20260511T045102-codex-mehrnoom-telegram-direct-manipulation-gate/direct-event-gate/mehrnoom_telegram_direct_manipulation_gate_report.json` | `pass` |

## Root Audit

| Root | Rule | Cal Wilson95 | Test Wilson95 | Cal Support | Test Support | Status |
|---|---|---:|---:|---:|---:|---|
| `Bull` | `close_drawdown60 >= -0.0032047199531 AND volatility <= 0.152179344579` | 0.952516 | 0.961931 | 2202 | 3125 | `pass` |
| `Bear` | `bear_drawdown_ratio >= 1 AND bear_return_ratio >= 1` | 0.993968 | 0.992722 | 633 | 524 | `pass` |
| `Sideways` | `sideways_abs_return_ratio <= 0.505204858191 AND sideways_range_ratio <= 0.357222193236` | 0.988647 | 0.995568 | 495 | 863 | `pass` |
| `Crisis` | `range_ratio32_128 >= 1.43116959912` | 0.996248 | 0.995981 | 1020 | 952 | `pass` |
| `Manipulation` | `classified_telegram_coin_pump_event_present == 1` | 0.999735 | 0.999701 | 14516 | 12834 | `pass` |

Achieved: `true`
