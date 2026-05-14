# R2/R4 source-label equivalence and strict 1h target support Request

Target root: `/tmp/ict-engine-source-label-equivalence-intake`

Please provide source-owned or owner-approved rows for:

Owner-approved or source-owned cross-market/source-label equivalence rows for Bull, Bear, Sideways, and Crisis; rows must use accepted MainRegimeV2 root vocabulary and must not duplicate already-counted panel evidence.

Required delivery files:
- `source_label_equivalence_rows.csv`
- `source_label_equivalence_provenance.json`

Required row schema:
`package_id`, `source_owner`, `source_report_or_dataset`, `source_pull_date`, `market_family`, `symbol`, `source_symbol`, `equivalence_policy`, `event_species`, `timestamp_or_date`, `timeframe`, `main_regime_v2_label`, `direct_label`, `matched_negative_group_id`, `split_role`, `source_row_id`, `provenance_hash`

Provenance requirements:
- identify the source owner/licensor
- include source dataset, export, ticket, or written approval reference
- include source version/hash or raw export hash
- state license constraints and whether raw rows can be committed
- state why rows are source-native labels rather than generated/HMM/KMeans/future-return/OHLCV proxy labels

Route:
Kaggle stock-regime owner plus index/exchange/vendor source-label owners

After delivery:
Place files under `/tmp/ict-engine-source-label-equivalence-intake` and rerun `docs/experiments/actionable-regime-confidence/runs/20260511T182922-codex-source-label-equivalence-intake-verifier-v1/equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py`. Schema readiness is not a confidence gate by itself; after verifier readiness, rerun the unchanged chronological/heldout-market/timeframe calibration and completion audit.

Current blocker:
source-label confidence remains 0/4 without verifier-ready rows.
