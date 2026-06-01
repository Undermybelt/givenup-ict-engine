# YF aerospace-components ORB/RVOL Gate 1 density failure - 2026-05-19

Session lesson for ict-engine profitability-factor training.

## Branch

`US_EQ -> single_stock -> {HEI|TDG|HWM} -> {1m|5m|15m|30m|1h|1d} -> TrendExpansion -> AerospaceComponentsOpeningRangeExpansion -> orb_rvol_expansion -> yf_aerospace_components_orb_rvol_expansion_1m_mtf_1d_v1`

## Provider/AQ outcome

- Provider: `yfinance/YF` real fetch, `local_cache_replay=false`.
- Requested symbols: `HEI`, `TDG`, `HWM`.
- Requested ladder: `1m/5m/15m/30m/1h/1d`; Yahoo path had no real `4h` and it was not fabricated.
- Practical window used: `1m=7d`, `5m/15m/30m/1h=55d`, `1d=365d`.
- `HEI 1m` failed fetch; `TDG/HWM 1m` fetched but produced no positive 1m rows.
- Rank summary: sparse HTF positives only (`HWM/15m` one trade, `TDG/15m` one trade); `one_minute_trades=0`, `positive_1m=[]`, `dense_positive_gate=false`.

## Decision

Terminalize as `keep_subclass_evidence_or_drop_gate1_no_downstream`.

Do not open Pre-Bayes, BBN, CatBoost, execution-tree, promotion, or trade-usable gates when the exact 1m-origin branch has no positive cost-surviving density. Higher-timeframe one-trade positives are subclass evidence or seeds for new exact timeframe roots, not rescue evidence for the failed 1m root.

## Durable pitfall

When cloning wrapper scripts, overriding only top-level `BRANCH_PATH` is insufficient. Also override material-level helpers and namespaces:

- `branch_path_for_spec`
- `branch_identity_for_spec`
- package/material id namespace
- factor id and profit-factor identity

Otherwise material rows can appear rooted while downstream parity is lost or stale namespace evidence leaks across runs.

## Next candidate shape

Pivot inside the same market/product/symbol family to a denser 1m entry family. Do not tighten overlays on the sparse ORB/RVOL branch and do not lower density/cost gates to avoid all downstream booleans being false.
