# Kaggle Candidate Schema Probe

Run ID: `20260511T104807+0800-codex-kaggle-candidate-schema-probe`

Board hash before probe: `c2fee1b08298fa1756981f2aade00552b21ca0a2fcde59256cbbfe0396ab168d`

## Result

- Active board cursor observed before probe: `20260511T103015+0800-codex-mainregimev2-lock-after-v7-drift`.
- Active taxonomy observed: `MainRegimeV2`.
- Raw candidate ZIPs stayed under `/tmp/ict_regime_kaggle_candidate_probe`; raw data committed: false.
- Accepted parent-root slots added: `0`.
- Accepted direct `Manipulation` rows/windows added: `0`.
- Gate result: `blocked_kaggle_candidate_schema_probe_no_attachable_exact_parent_root_labels`.
- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

## Candidate Decisions

- `kaggle:sergionefedov/crypto-microstructure`: has `regime` values and Kraken rows, but the dataset description states it is synthetic. Rejected for accepted source-label accounting.
- `kaggle:kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes`: daily macro/asset feature panel. Rejected because no active root-label columns or direct manipulation rows were observed.
- `kaggle:nudratabbas/tech-titans-volatility-and-trend-analysis-data`: has daily `trend_label` Bull/Bear for tech stocks. Rejected because it is off the current exact missing-instrument universe and lacks Sideways/Crisis/intraday/monthly coverage.

## Next Action

Continue exact-underlying `MainRegimeV2` parent-root label acquisition for `Bull` / `Bear` / `Sideways` / `Crisis`, and broaden real direct `Manipulation` varieties outside bounded DEX self-trades.
