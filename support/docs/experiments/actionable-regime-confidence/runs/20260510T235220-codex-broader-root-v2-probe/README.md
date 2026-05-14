# Broader MainRegimeV2 Root Probe

This run reruns the corrected MainRegimeV2 root gate on the broader cross-timeframe feature table. It derives 8h forward targets per context and blocks all `future_*` and `target_*` fields from predictor use. Existing subtype packets remain evidence only.

- input feature table: `docs/experiments/actionable-regime-confidence/runs/20260510T224014-codex-cross-timeframe-regime-validation/cross_timeframe_regime_features.csv`
- schema: `docs/experiments/actionable-regime-confidence/runs/20260510T235220-codex-broader-root-v2-probe/root-v2-broader/main_regime_v2_broader_target_schema.json`
- crosswalk: `docs/experiments/actionable-regime-confidence/runs/20260510T235220-codex-broader-root-v2-probe/root-v2-broader/main_regime_v2_broader_crosswalk.json`
- calibration report: `docs/experiments/actionable-regime-confidence/runs/20260510T235220-codex-broader-root-v2-probe/root-v2-broader/main_regime_v2_broader_root_calibration_report.json`
- summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260510T235220-codex-broader-root-v2-probe/root-v2-broader/main_regime_v2_broader_root_probe_summary.csv`
