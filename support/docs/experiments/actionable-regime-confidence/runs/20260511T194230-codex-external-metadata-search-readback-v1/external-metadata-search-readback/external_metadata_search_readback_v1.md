# External Metadata Search Readback v1

Run ID: `20260511T194230+0800-codex-external-metadata-search-readback-v1`

This is a readback-only registration of two legacy metadata searches that were already running when this slice resumed. It does not clone repositories, download dataset rows, execute external code, edit Current Cursor, relax thresholds, or promote generated labels.

## Decision

`external_metadata_search_readback_v1=no_promotable_source_owned_labels`

- Metadata searches polled: `2` sessions.
- Query readbacks recorded: `4`.
- Candidate records dispositioned: `6`.
- Ready source-owned or owner-approved active-regime label sources found: `0`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Full other-market/source-label equivalence: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Search Readback

| Source | Query | Result | Decision |
|---|---|---|---|
| GitHub metadata | `market regime Bull Bear Sideways Python` | `3` repositories | all generated/tool/framework surfaces |
| GitHub metadata | `regime_label Bull Bear Sideways ticker` | `0` repositories | no source label package found |
| GitHub metadata | `stock market regime labels dataset` | `0` repositories | no source label package found |
| Kaggle metadata | `regime_label Bull Bear Sideways ticker` | no datasets | no source label package found |

## Candidate Disposition

| Candidate | Decision | Reason |
|---|---|---|
| [`AndrewFSee/regime-rl-trading`](https://github.com/AndrewFSee/regime-rl-trading) | `blocked_feature_or_hmm_detector_outputs_not_source_labels` | Regime-detection/RL framework; no source-owned row-level label panel or approved `MainRegimeV2` crosswalk. |
| [`Hasan8123/Market-Regime-Detection-System`](https://github.com/Hasan8123/Market-Regime-Detection-System) | `blocked_tool_generated_from_historical_ohlcv` | Automated detection from historical market data, not source-owned labels. |
| [`BuildWithSaravanan/Market-Regime-Detection-System`](https://github.com/BuildWithSaravanan/Market-Regime-Detection-System) | `blocked_tool_generated_from_historical_ohlcv` | Automated regime detection from stock data, not source-owned labels with provenance. |
| GitHub exact label query | `no_results` | No repository hit for `regime_label Bull Bear Sideways ticker`. |
| GitHub dataset query | `no_results` | No repository hit for `stock market regime labels dataset`. |
| Kaggle exact label query | `no_datasets_found` | Kaggle returned no datasets for `regime_label Bull Bear Sideways ticker`. |

## Why It Still Blocks

These metadata hits do not satisfy the active Board A acceptance contract. Generated HMM/KMeans/feature-threshold labels, OHLCV-derived tool outputs, and empty search results cannot stand in for source-owned labels, owner-approved `MainRegimeV2` equivalence rows, strict `1h` intake rows, native sub-hour labels, or direct `Manipulation` positive/control rows.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T194230-codex-external-metadata-search-readback-v1/external-metadata-search-readback/external_metadata_search_readback_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T194230-codex-external-metadata-search-readback-v1/external-metadata-search-readback/external_metadata_search_readback_v1_candidates.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T194230-codex-external-metadata-search-readback-v1/checks/external_metadata_search_readback_v1_assertions.out`
