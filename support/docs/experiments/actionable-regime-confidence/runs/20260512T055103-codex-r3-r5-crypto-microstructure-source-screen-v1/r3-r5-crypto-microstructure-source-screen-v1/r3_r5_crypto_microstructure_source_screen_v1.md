# R3/R5 Crypto Microstructure Source Screen v1

Run id: `20260512T055103-codex-r3-r5-crypto-microstructure-source-screen-v1`

Gate result: `r3_r5_crypto_microstructure_source_screen_v1=crypto_native_candidates_screened_no_required_root_unlock_no_promotion`

Board hash before artifact: `daae8edfa8c7da836b832814138231cc1c3af00537ed3df2a2a9602f48d5b0f9`

## Scope

Read-only source-acquisition screen for crypto/native microstructure regime-like datasets that were not covered by the broad R5 NIFTY screen. This run keeps raw downloads in `/tmp`, does not mutate required target roots, does not map external labels into `MainRegimeV2`, does not run canonical merge or downstream promotion, and does not call `update_goal`.

## Search Readback

- `crypto microstructure regime`: exit `0`, rows `5`
- `crypto regime features`: exit `0`, rows `6`
- `limit order book market regimes`: exit `0`, rows `1`
- `binance trades regime`: exit `0`, rows `2`

## Candidate Disposition

| Ref | Downloaded | Max date | Post-cutoff rows | Disposition |
|---|---:|---:|---:|---|
| `sergionefedov/crypto-microstructure` | `True` | `2024-12-31` | `0` | `not_r5_or_r3_compatible_exact_mainregimev2_absent` |
| `quantiota/ska-engine-applied-to-crypto-from-binance` | `False` | `` | `0` | `raw_binance_trade_files_file_listing_only_no_source_regime_labels` |
| `sergionefedov/synthetic-limit-order-book-market-microstructure` | `False` | `` | `0` | `synthetic_dataset_not_source_owned_market_label_evidence` |
| `marketsignal/marketsignal-ai-feature-feed-mag-7-stocks` | `True` | `2024-07-16` | `0` | `not_r5_or_r3_compatible_exact_mainregimev2_absent` |

## Decision

No screened crypto/native microstructure candidate satisfies the R3 native AAPL/IXIC 15m/30m source-label intake or the R5 source-owned MainRegimeV2 post-cutoff stock-panel extension contract.

Reasons:
- The only downloaded crypto dataset with `regime_features.csv` is crypto-context feature evidence, not a source-owned `MainRegimeV2` `Bull`/`Bear`/`Sideways`/`Crisis` stock-panel extension.
- Mag-7 feature samples are equity feature feeds, not native AAPL/IXIC 15m/30m source labels and not R5 root labels.
- The Binance/SKA and synthetic LOB candidates are raw/synthetic microstructure routes without source-owned target labels; mapping them would be a derived ontology transform.
- Required target roots remain absent.

Required root status:
- `/tmp/ict-engine-board-a-r6-owner-export-v1`: `False`
- `/tmp/ict-engine-native-subhour-source-label-intake`: `False`
- `/tmp/ict-engine-source-panel-recency-extension`: `False`

Promotion status remains unchanged: accepted rows added `0`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Keep Board A blocked until R6 owner/export rows plus normal controls, source-owned R3 native sub-hour labels, source-owned R5 MainRegimeV2 recency rows, or explicit source/control approval unlock a required root.
