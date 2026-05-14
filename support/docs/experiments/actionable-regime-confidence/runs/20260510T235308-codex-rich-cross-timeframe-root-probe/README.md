# Rich Cross-Timeframe MainRegimeV2 Root Probe

This run reruns the corrected MainRegimeV2 root gate on the richer 62k-row 15m/1h cross-timeframe feature table. It keeps child/signature packets as context only, blocks `future_*` and `target_*` predictors, and leaves `Manipulation` fail-closed because direct inputs are absent.

- input feature table: `docs/experiments/actionable-regime-confidence/runs/20260510T224014-codex-cross-timeframe-regime-validation/cross_timeframe_regime_features.csv`
- calibration report: `docs/experiments/actionable-regime-confidence/runs/20260510T235308-codex-rich-cross-timeframe-root-probe/rich-root/main_regime_v2_rich_cross_timeframe_root_report.json`
- summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260510T235308-codex-rich-cross-timeframe-root-probe/rich-root/main_regime_v2_rich_cross_timeframe_root_summary.csv`
- assertions: `docs/experiments/actionable-regime-confidence/runs/20260510T235308-codex-rich-cross-timeframe-root-probe/checks/rich_cross_timeframe_root_probe_assertions.out`
