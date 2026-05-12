# Kaggle Bear/Sideways Train-Only Log-Odds Probe

Run id: `20260511T040241+0800-codex-kaggle-bear-sideways-logodds-probe`.

## Decision

- Gate result: `blocked_kaggle_bear_sideways_logodds_below_95`
- Accepted new roots: none
- Missing roots after preserved accounting: Bear, Sideways, Manipulation
- Thresholds relaxed: `false`
- Runtime code changed: `false`

## Root Results

| Root | State | Rule | Cal LCB | Test LCB | Test Precision | Test Coverage | Blockers |
|---|---|---|---:|---:|---:|---:|---|
| Bear | blocked | `train_only_quantile_log_odds_score_Bear >= 9.49274139571` | 0.824304 | 0.775807 | 0.802313 | 0.016061 | calibration_wilson95_below_0_95, test_wilson95_below_0_95, calibration_coverage_below_0_03, test_coverage_below_0_03, ece_above_0_05 |
| Sideways | blocked | `train_only_quantile_log_odds_score_Sideways >= 5.10770657745` | 0.820398 | 0.770940 | 0.789664 | 0.032680 | calibration_wilson95_below_0_95, test_wilson95_below_0_95 |

## Policy

- Source `regime_label` is target-only.
- Source `regime_confidence`, labels, identifiers, and `future_*` / `target_*` / `next_*` fields are not predictors.
- Score bins and thresholds are selected on the train split only.
- `Manipulation` is not evaluated here because Kaggle OHLCV/macro labels are not direct manipulation evidence.
