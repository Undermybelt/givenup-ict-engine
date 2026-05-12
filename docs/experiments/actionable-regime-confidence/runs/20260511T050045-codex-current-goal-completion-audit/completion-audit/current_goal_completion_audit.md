# Current Goal Completion Audit

Run id: `20260511T050045+0800-codex-current-goal-completion-audit`.

## Decision

- Goal achieved: `true`
- Accepted roots: `Bull, Bear, Sideways, Crisis, Manipulation`
- Missing roots: `none`
- UnknownOrMixed: residual only, not a completion root.
- Trade usable: `false`.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Named board exists and is the active contract | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` | pass |
| Active roots are MainRegimeV2 parent roots plus direct-input-gated Manipulation | `Board Active MainRegimeV2 Root Ledger` | pass |
| Expanded labels are not counted as completion roots | `Board research guidance and root ledger` | pass |
| Every active root has accepted 95 evidence under concrete artifacts | `Per-root artifact audit` | pass |
| No trade-usable strategy is claimed by Board A | `Per-root reports` | pass |
| No runtime code changes or threshold relaxation are needed for accepted evidence | `Per-root reports` | pass |

## Root Evidence

| Root | Status | Artifact | Rule | Cal Wilson95 | Test Wilson95 | Test Support | Test Coverage |
|---|---|---|---|---:|---:|---:|---:|
| Bull | pass | `docs/experiments/actionable-regime-confidence/runs/20260511T035045-codex-kaggle-bull-coverage-buffer-gate/kaggle-bull-gate/kaggle_bull_coverage_buffer_gate_report.json` | `close_drawdown60 >= -0.0032047199531 AND volatility <= 0.152179344579` | 0.952516 | 0.961931 | 3125 | 0.052777 |
| Bear | pass | `docs/experiments/actionable-regime-confidence/runs/20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json` | `bear_drawdown_ratio >= 1 AND bear_return_ratio >= 1` | 0.993968 | 0.992722 | 524 | 0.065582 |
| Sideways | pass | `docs/experiments/actionable-regime-confidence/runs/20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json` | `sideways_abs_return_ratio <= 0.505204858191 AND sideways_range_ratio <= 0.357222193236` | 0.988647 | 0.995568 | 863 | 0.108010 |
| Crisis | pass | `docs/experiments/actionable-regime-confidence/runs/20260510T235220-codex-broader-root-v2-probe/root-v2-broader/main_regime_v2_broader_root_calibration_report.json` | `range_ratio32_128 >= 1.43116959912` | 0.996248 | 0.995981 | 952 | 0.061758 |
| Manipulation | pass | `docs/experiments/actionable-regime-confidence/runs/20260511T045102-codex-mehrnoom-telegram-direct-manipulation-gate/direct-event-gate/mehrnoom_telegram_direct_manipulation_gate_report.json` | `classified_telegram_coin_pump_event_present == 1` | 0.999735 | 0.999701 | 12834 | 0.521877 |

## Residual Risk

- Manipulation acceptance is direct event-confirmation for suppression/abstain/cooldown, not pre-event prediction.
- Board B profitability and execution promotion remain outside Board A.
