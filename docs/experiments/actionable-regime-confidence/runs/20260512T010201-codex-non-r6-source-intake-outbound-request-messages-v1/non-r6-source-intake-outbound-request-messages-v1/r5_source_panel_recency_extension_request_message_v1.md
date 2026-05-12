# R5 source-panel recency after 2026-01-30 Request

Target root: `/tmp/ict-engine-source-panel-recency-extension`

Please provide source-owned or owner-approved rows for:

Post-2026-01-30 source-owned extension rows for required cells: XOM/Sideways, UNH/Bear, ^DJI/Sideways, and AMD/Bear.

Required delivery files:
- `stock_market_regimes_2026_extension.csv`
- `source_panel_recency_provenance.json`

Required row schema:
`date`, `ticker`, `close`, `returns`, `volatility`, `regime_label`, `regime_confidence`, `macro_context`, `unemployment_rate`, `fed_funds_rate`, `cpi`, `10y_treasury`, `2y_treasury`, `vix`

Provenance requirements:
- identify the source owner/licensor
- include source dataset, export, ticket, or written approval reference
- include source version/hash or raw export hash
- state license constraints and whether raw rows can be committed
- state why rows are source-native labels rather than generated/HMM/KMeans/future-return/OHLCV proxy labels

Route:
Kaggle stock-regime dataset owner/profile/discussion or equivalent source owner

After delivery:
Place files under `/tmp/ict-engine-source-panel-recency-extension` and rerun `docs/experiments/actionable-regime-confidence/runs/20260511T165405-codex-source-panel-recency-extension-manifest-v1/source-panel-recency/source_panel_recency_extension_verifier_v1.py`. Schema readiness is not a confidence gate by itself; after verifier readiness, rerun the unchanged chronological/heldout-market/timeframe calibration and completion audit.

Current blocker:
R5 public Kaggle refresh still stops at 2026-01-30; proxy yfinance labels are rejected.
