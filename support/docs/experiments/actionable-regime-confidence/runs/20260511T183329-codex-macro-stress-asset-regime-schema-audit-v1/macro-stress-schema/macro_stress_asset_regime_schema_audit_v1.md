# Macro Stress Asset Regime Schema Audit v1

Run ID: `20260511T183329+0800-codex-macro-stress-asset-regime-schema-audit-v1`

## Decision

- Decision: `blocked_feature_context_only_no_source_regime_labels`.
- Gate result: `macro_stress_asset_regime_schema_audit_v1=feature_context_only_no_source_label_equivalence`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Full objective achieved: `false`; `update_goal=false`.

## Candidate

- Dataset: `kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes`.
- URL: https://www.kaggle.com/datasets/kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes.
- File: `Global_Market_Stress_and_Liquidity_Regimes.csv`.
- Rows: `4150`; fields: `18`.
- Date range: `2014-10-17` to `2026-02-25`.
- Rows after source-panel tail `2026-01-30`: `26`.
- Cross-asset columns: `Equities_US, Equities_Tech, Equities_Emerging, Bonds_LongTerm, Gold, Oil, Volatility_Index, Crypto_Bitcoin, Yield_Curve_Spread, High_Yield_Spread, Financial_Stress_Index`.
- Label-like fields: `none`.

## Guardrail

This dataset is feature/context evidence only. It has no explicit `Bull`/`Bear`/`Sideways`/`Crisis` source labels, no direct `Manipulation` labels, and no matched negative/control groups. Do not promote its post-tail feature rows into source-panel recency labels.
