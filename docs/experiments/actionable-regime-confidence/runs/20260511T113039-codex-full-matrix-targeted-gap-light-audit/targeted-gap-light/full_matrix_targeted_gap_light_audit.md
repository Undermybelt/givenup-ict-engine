# Full-Matrix Targeted Gap Light Audit

Run ID: `20260511T113039+0800-codex-full-matrix-targeted-gap-light-audit`

## Result

- Accepted parent-root gap slices added: `0`.
- Gate result: `blocked_light_gap_audit_no_95_source_label_slice`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

## Crisis Source-Label Probe

- Rows: `295865`.
- Accepted 95: `false`.
- Best blocked rule: `volatility >= 0.654152684787 AND close_drawdown60 <= -0.20621762849 AND fed_funds_rate >= 6.02`.
- Best blocked calibration/test Wilson95: `0.947042` / `0.955249`.
- Best blocked blockers: `calibration_support_below_250; calibration_wilson95_below_0_95; calibration_coverage_below_0_01; calibration_market_contexts_below_2; test_support_below_250; test_coverage_below_0_01; test_market_contexts_below_2`.

## Intraday Source-Label Readiness

- Rows: `62002`.
- Has independent source root label column: `false`.
- Target-like columns: `target_trend_structural_next, target_stress_next, target_reversal_next, target_thin_soft_next`.
- Decision: `blocked_intraday_table_has_future_target_columns_but_no_independent_source_root_labels`.

## Next Action

Acquire independent source root labels for the missing intraday/monthly provider matrix; do not count future-return target columns as source labels. Continue separate direct Manipulation variety acquisition.
