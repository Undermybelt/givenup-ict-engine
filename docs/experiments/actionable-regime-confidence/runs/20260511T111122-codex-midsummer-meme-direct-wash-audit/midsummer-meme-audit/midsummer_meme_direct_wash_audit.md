# Midsummer Meme Direct Wash Audit

Run ID: `20260511T111122+0800-codex-midsummer-meme-direct-wash-audit`

Board cursor readback: `20260511T110628+0800-codex-aimmgt-public-direct-source-audit`

## Source

- Zenodo record: `17830944`
- DOI: `10.5281/zenodo.17830944`
- URL: `https://zenodo.org/records/17830944`
- Related repository: `https://github.com/Alb4tro/Code-and-Dataset-for-A-Midsummer-Meme-s-Dream-`
- Raw ZIP location: `/tmp/ict-regime-midsummer-meme/meme_coin-main.zip`
- ZIP SHA-256: `4ef60d79cc70bc14287002d0a97a127ca46757690bae075801858356489571c9`

## Board Contract

Active taxonomy remains `MainRegimeV2`: `Bull`, `Bear`, `Sideways`, and `Crisis` are price roots. `Manipulation` is a separate direct class or overlay and still needs timestamped direct rows plus negative controls.

## Inspected Files

| File | Rows Including Header | Decision |
|---|---:|---|
| `data/wash_trading_detected.csv` | 1044 | positive token-day provenance only |
| `data/lpi_operations_detected.csv` | 73 | positive-only; no explicit negative controls accepted in this audit |
| `data/pump_and_dumps_on_performing_tokens_after_mid_january.csv` | 92 | OHLCV-derived profit-extraction event; not direct wash/order-lifecycle acceptance |
| `data/rug_pulls_detected_on_performing_tokens_after_mid_january.csv` | 3 | sparse OHLCV-derived event; not accepted |
| `data/dune_data_on_potential_wash_trading_makers_HP_coins.csv` | 64622 | usable direct on-chain maker-token-day source labels for a bounded BSC slice |

## Accepted Scoped Slice

Accepted only the stricter same-token-day BSC wash-maker slice from `dune_data_on_potential_wash_trading_makers_HP_coins.csv`.

Unit: `maker-token-day`.

Source label: `is_both_buyer_seller`.

Rules:
- Positive: `platform == "bsc"` and same token-day has both positive and negative controls and `is_both_buyer_seller == True`.
- Negative: `platform == "bsc"` and same token-day paired controls and `is_both_buyer_seller == False`.

Chronological split:
- Date range: `2021-09-18` to `2025-02-05`.
- Cut date: `2024-06-27`.
- Paired token-days: `298`.
- Rows: `4864`.
- Positive rows: `1870`.
- Negative controls: `2994`.

| Split | Positive Rows | Negative Rows | Positive Wilson95 LCB | Negative Wilson95 LCB |
|---|---:|---:|---:|---:|
| calibration | 897 | 1673 | 0.995736 | 0.997709 |
| test | 973 | 1321 | 0.996067 | 0.997100 |

Minimum split/class Wilson95 LCB: `0.995736`.

Gate result: `accepted_95_bounded_bsc_meme_wash_maker_direct_slice_not_full_manipulation_coverage`.

## Rejections

All-chain scope remains rejected because the minimum per-chain split/class Wilson95 LCB is `0.722467`; Base and Solana calibration classes are too sparse under the unchanged per-chain support check.

Pump/dump and rug-pull files are not accepted as direct `Manipulation` evidence here because they are OHLCV-derived profit-extraction detections. LPI is not accepted in this bounded audit because the inspected release gives positive rows but no explicit negative controls.

## Decision

- Accepted parent-root slots added: `0`.
- Accepted direct `Manipulation` rows added: `1870`.
- Accepted gate: `accepted_95_bounded_bsc_meme_wash_maker_direct_slice`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.
- Full objective achieved: false.

Next action: keep exact `MainRegimeV2` parent-root label-window acquisition as the global blocker, while treating this as one additional scoped direct `Manipulation` wash-trading slice.
