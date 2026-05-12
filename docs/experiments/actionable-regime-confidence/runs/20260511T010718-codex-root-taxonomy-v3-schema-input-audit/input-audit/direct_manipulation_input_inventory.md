# RootTaxonomyV3 Schema And Direct-Input Audit

Run id: `20260511T010718-codex-root-taxonomy-v3-schema-input-audit`

## Result

- RootTaxonomyV3 schema materialized: yes.
- Crosswalk materialized: yes.
- Fresh 95% calibration rerun: no, blocked by input audit.
- `Manipulation` input state: `missing_required_inputs`.
- Accepted root state remains partial: prior source-backed gate accepted only `CrisisStress`.

## Direct Input Audit Summary

| Class | Files | Interpretation |
|---|---:|---|
| `aggregated_bar_or_proxy` | 2 | states=['proxy_only_low_confidence']; examples=aligned_ibkr_nqz5_20251218_15m_1m_bid_ask.csv, richdata_kraken_spot_xbtusd_15m_vwap_count.csv |
| `json_summary_or_metadata` | 3 | states=['metadata_only']; examples=itch_AAPL.XNAS_2019-01-30_deltas.metadata.json, tardis_BTC-PERPETUAL.DERIBIT_2020-04-01_deltas.metadata.json, richdata_provider_l2_tradeflow_availability_summary.json |
| `market_l2_or_depth` | 5 | states=['too_thin_fixture']; examples=binance-futures_book_snapshot_25_BTCUSDT.csv, binance-futures_book_snapshot_5_BTCUSDT.csv, deribit_incremental_book_L2_BTC-PERPETUAL.csv, ... |
| `market_l2_orderbook_delta_parquet` | 2 | states=['support_too_thin_fixture']; examples=deltas.parquet, deltas.parquet |
| `private_account_order_lifecycle` | 2 | states=['not_market_wide_manipulation_proof']; examples=api-v1-order.csv, api-v1-execution-tradeHistory.csv |
| `quote_tick_bid_ask` | 3 | states=['candidate_quote_dynamics_only', 'support_too_thin']; examples=huobi-dm-swap_quotes_BTC-USD.csv, audusd-ticks.csv, usdjpy-ticks.csv |
| `trade_tape` | 2 | states=['candidate_tradeflow_only', 'support_too_thin']; examples=bitmex_trades_XBTUSD.csv, ethusdt-trades.csv |
| `unknown_or_unusable` | 1 | states=['not_enough_schema_evidence']; examples=quote_tick_data.csv |

## Decision

Do not rerun a `Manipulation` 95% gate from the current inputs. The candidate files contain some direct trade and quote data, but no accessible market-wide L2/L3/order-lifecycle dataset with enough verified support. OHLCV/bid-ask bars and account-level order history remain fail-closed for manipulation proof.

Next useful action: decode or acquire full L2/L3 order-book deltas, market-wide order lifecycle, or aligned event/social/on-chain evidence; then rerun unchanged RootTaxonomyV3 gates.
