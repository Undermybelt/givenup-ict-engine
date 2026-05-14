# Past-Regime Persistence Root Probe

This probe tests whether non-leaky past-window regime persistence can close the remaining MainRegimeV2 root classes.

- Input table: `docs/experiments/actionable-regime-confidence/runs/20260510T224014-codex-cross-timeframe-regime-validation/cross_timeframe_regime_features.csv`
- Added predictors: past 8h return, past 8h absolute return, past 8h range, past-root flags, past-root streaks, and rolling 16/64 row past-root frequencies.
- Blocked predictors: all `future_*` and `target_*` fields.
- Result: `Crisis` remains accepted, but `Bull`, `Bear`, `Sideways`, and `Manipulation` remain blocked.

This is not a completion artifact.
