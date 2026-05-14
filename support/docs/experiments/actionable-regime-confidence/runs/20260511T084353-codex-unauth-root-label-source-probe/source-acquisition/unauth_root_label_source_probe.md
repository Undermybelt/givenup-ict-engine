# Unauthenticated Root Label Source Probe

Run id: `20260511T084353+0800-codex-unauth-root-label-source-probe`

## Result

- Missing/rejected MainRegimeV2 root-label slots inspected: `564`.
- Catalog/API endpoints queried: `36`.
- Metadata candidates classified: `60`.
- New accepted MainRegimeV2 root-label slots: `0`.
- New accepted direct `Manipulation` label sources: `0`.
- Gate result: `blocked_no_accepted_unauthenticated_non_kaggle_source_labels`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Missing Slot Shape

| Dimension | Counts |
|---|---|
| Reason | `{'missing_intraday_or_monthly_source_label': 392, 'missing_instrument_source_label': 40, 'rejected_near_underlying_proxy_not_accepted': 24, 'missing_non_yfinance_source_label': 108}` |
| Provider | `{'yfinance': 456, 'kraken_public_lowpollution_http': 108}` |
| Timeframe | `{'1m': 68, '5m': 68, '15m': 68, '30m': 68, '1h': 68, '1d': 44, '1w': 44, '1mo': 68, '4h': 68}` |
| Root | `{'Bull': 141, 'Bear': 141, 'Sideways': 141, 'Crisis': 141}` |

## Catalog Coverage

- Catalog result counts: `{'github': 27, 'huggingface': 5, 'zenodo': 25, 'openml_page': 3}`.
- Decision counts: `{'rejected_proxy_or_model_generated': 29, 'rejected_missing_full_mainregimev2_roots': 17, 'sidecar_only_needs_exported_rows_and_controls': 14}`.
- Public metadata was allowed; raw market datasets/large OHLCV files were not downloaded.

## Sidecar / Follow-up Candidates

| Source | Catalog | Decision | Reason |
|---|---|---|---|
| [`github:Jananigaekwad/Group-3-Wash-Trading-Case-Study-for-ERC20-Token`](https://github.com/Jananigaekwad/Group-3-Wash-Trading-Case-Study-for-ERC20-Token) | `github` | `sidecar_only_needs_exported_rows_and_controls` | Metadata mentions direct manipulation/wash/spoofing concepts, but no replayable positive/negative windows were exported in this probe. |
| [`github:divyamg13/BITS-F464-Machine-Learning`](https://github.com/divyamg13/BITS-F464-Machine-Learning) | `github` | `sidecar_only_needs_exported_rows_and_controls` | Metadata mentions direct manipulation/wash/spoofing concepts, but no replayable positive/negative windows were exported in this probe. |
| [`github:SystemsLab-Sapienza/pump-and-dump-dataset`](https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset) | `github` | `sidecar_only_needs_exported_rows_and_controls` | Metadata mentions direct manipulation/wash/spoofing concepts, but no replayable positive/negative windows were exported in this probe. |
| [`github:karnikkanojia/TadGAN-Research`](https://github.com/karnikkanojia/TadGAN-Research) | `github` | `sidecar_only_needs_exported_rows_and_controls` | Metadata mentions direct manipulation/wash/spoofing concepts, but no replayable positive/negative windows were exported in this probe. |
| [`github:akasshvinod/Market-Manipulation-Detection`](https://github.com/akasshvinod/Market-Manipulation-Detection) | `github` | `sidecar_only_needs_exported_rows_and_controls` | Metadata mentions direct manipulation/wash/spoofing concepts, but no replayable positive/negative windows were exported in this probe. |
| [`github:Gopal-Dahale/qkrishi-assignment`](https://github.com/Gopal-Dahale/qkrishi-assignment) | `github` | `sidecar_only_needs_exported_rows_and_controls` | Metadata mentions direct manipulation/wash/spoofing concepts, but no replayable positive/negative windows were exported in this probe. |
| [`zenodo:4540223`](https://zenodo.org/records/4540223) | `zenodo` | `sidecar_only_needs_exported_rows_and_controls` | Metadata mentions direct manipulation/wash/spoofing concepts, but no replayable positive/negative windows were exported in this probe. |
| [`zenodo:17830944`](https://zenodo.org/records/17830944) | `zenodo` | `sidecar_only_needs_exported_rows_and_controls` | Metadata mentions direct manipulation/wash/spoofing concepts, but no replayable positive/negative windows were exported in this probe. |
| [`zenodo:5026154`](https://zenodo.org/records/5026154) | `zenodo` | `sidecar_only_needs_exported_rows_and_controls` | Metadata mentions direct manipulation/wash/spoofing concepts, but no replayable positive/negative windows were exported in this probe. |
| [`zenodo:4580200`](https://zenodo.org/records/4580200) | `zenodo` | `sidecar_only_needs_exported_rows_and_controls` | Metadata mentions direct manipulation/wash/spoofing concepts, but no replayable positive/negative windows were exported in this probe. |
| [`zenodo:16955639`](https://zenodo.org/records/16955639) | `zenodo` | `sidecar_only_needs_exported_rows_and_controls` | Metadata mentions direct manipulation/wash/spoofing concepts, but no replayable positive/negative windows were exported in this probe. |
| [`zenodo:17860328`](https://zenodo.org/records/17860328) | `zenodo` | `sidecar_only_needs_exported_rows_and_controls` | Metadata mentions direct manipulation/wash/spoofing concepts, but no replayable positive/negative windows were exported in this probe. |
| [`zenodo:19653452`](https://zenodo.org/records/19653452) | `zenodo` | `sidecar_only_needs_exported_rows_and_controls` | Metadata mentions direct manipulation/wash/spoofing concepts, but no replayable positive/negative windows were exported in this probe. |
| [`openml_search_page:market_manipulation`](https://www.openml.org/search?type=data&status=active&search=market+manipulation) | `openml_page` | `sidecar_only_needs_exported_rows_and_controls` | Metadata mentions direct manipulation/wash/spoofing concepts, but no replayable positive/negative windows were exported in this probe. |

## Fail-Closed Decision

No unauthenticated public metadata candidate proved an independent, exact-underlying, instrument/timeframe-attached `Bull` / `Bear` / `Sideways` / `Crisis` label panel for the 564 missing slots.
No direct `Manipulation` candidate produced exported positive/negative chronological windows; Dune or another labeled source still needs authenticated/exported rows before acceptance.

## Next Action

Obtain a non-Kaggle exact-underlying label panel with schema/rows for the missing intraday/monthly/Kraken/instrument slots, or provide authenticated/exported direct `Manipulation` positive and negative windows; keep HMM/GMM/future-return/OHLCV/proxy labels fail-closed.
