# Strict Cross-Timeframe Regime Audit

Loop ID: `20260510T224929+0800-codex-strict-cross-timeframe-audit`

This run audits the stricter user requirement that every accepted regime must pass 95%+ and also validate across other markets and at least two timeframes/cycles.

Result: `blocked`, not complete.

Artifacts:
- `audit/strict_cross_timeframe_audit.json`
- `audit/strict_cross_timeframe_candidate_summary.csv`
- `checks/strict_cross_timeframe_audit_assertions.out`
- `checks/legacy_intraday_missing_regime_exploration.out`

Strict pass regimes: SessionLiquidityCoreViable, RangeConsolidation

Missing cross-timeframe regimes: TrendExpansion, ExtremeStress, ReversalBrewing, ThinLiquidity

Additional legacy-contract intraday exploration also accepted 0 candidates for the four missing regimes.

Next: build or ingest broader aligned multi-timeframe evidence for the missing regimes and rerun unchanged 95% gates.
