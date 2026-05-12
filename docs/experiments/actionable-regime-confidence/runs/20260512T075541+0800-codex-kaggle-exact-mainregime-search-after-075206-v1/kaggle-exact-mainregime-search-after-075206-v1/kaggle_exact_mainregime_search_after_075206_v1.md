# Kaggle Exact MainRegime Search After 075206 v1

Run id: `20260512T075541+0800-codex-kaggle-exact-mainregime-search-after-075206-v1`

Gate result: `kaggle_exact_mainregime_search_after_075206_v1=existing_stock_regime_only_no_new_source_control_unlock`

## Scope

Bounded current Kaggle CLI search for exact Board A source terms after the `075206` current-objective audit. This packet does not mutate R3/R5/R6 target roots, approve public metadata as source/control evidence, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Queries

| Query | Rows | Notable result |
|---|---:|---|
| `Bull Bear Sideways Crisis` | `1` | `mafaqbhatti/stock-market-regimes-20002026` |
| `MainRegimeV2` | `0` | `none` |
| `stock_market_regimes_2000_2026` | `1` | `mafaqbhatti/stock-market-regimes-20002026` |
| `Crisis market regime label` | `5` | `kanchana1990/world-bank-commodity-price-intelligence-19602026; kanchana1990/bis-global-debt-securities-intelligence-19622025; sergionefedov/big-energy-dataset-gas-solarwind-generation; ahaanverma00/nifty-500-market-and-behavior-regime-dataset; svenneawolf/geopolitics-nationfiles-stability-index-nfsi` |

## Decision

- `MainRegimeV2` returned no Kaggle dataset rows.
- Exact `Bull Bear Sideways Crisis` and `stock_market_regimes_2000_2026` searches returned the already-known `mafaqbhatti/stock-market-regimes-20002026` dataset.
- Known R5 redownload profile: rows `245021`, date range `2000-01-03` to `2026-01-30`, rows after `2026-01-30` `0`.
- Broad `Crisis market regime label` results include unrelated macro/commodity/geopolitical datasets and the already-screened NIFTY behavior-regime dataset, not a required Board A source/control root.
- Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Next

Continue source/control acquisition only before any direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.

