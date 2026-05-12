# Direct L2 / Parquet / DBN Readability Audit

Loop id: `20260511T012129+0800-codex-direct-l2-parquet-dbn-readability-audit`

Result: no qualifying direct manipulation input set is available yet.

Decoded Parquet candidates:
- `/Users/thrill3r/nautilus_trader/tests/test_data/nautilus/64-bit/deltas.parquet`: order_book_delta_parquet rows=1077 state=support_too_thin_fixture qualifies=False
- `/Users/thrill3r/nautilus_trader/tests/test_data/nautilus/128-bit/deltas.parquet`: order_book_delta_parquet rows=1077 state=support_too_thin_fixture qualifies=False
- `/Users/thrill3r/nautilus_trader/tests/test_data/binance/btcusdt-quotes.parquet`: quote_tick_parquet rows=451 state=partial_quote_context_only qualifies=False
- `/Users/thrill3r/nautilus_trader/tests/test_data/binance/btcusdt-trades.parquet`: trade_tape_parquet rows=2001 state=partial_tradeflow_only qualifies=False
- `/Users/thrill3r/nautilus_trader/tests/test_data/quote_tick_eurusd_2019_sim_rust.parquet`: quote_tick_parquet rows=10000 state=partial_quote_context_only qualifies=False
- `/Users/thrill3r/nautilus_trader/tests/test_data/quote_tick_usdjpy_2019_sim_rust.parquet`: quote_tick_parquet rows=10000 state=partial_quote_context_only qualifies=False

DBN/Zstd candidates:
- `/Users/thrill3r/nautilus_trader/tests/test_data/databento/order_book_deltas_catalog/databento/orderbooks_mbo_2024-05-08T00-00-00_2024-05-08T00-00-02.dbn.zst`: dbn_magic=True size=183688 state=decoder_missing_or_sample_too_short qualifies=False
- `/Users/thrill3r/nautilus_trader/tests/test_data/databento/esh4-glbx-mdp3-20231224.mbo.dbn.zst`: dbn_magic=True size=53814 state=decoder_missing_or_sample_too_short qualifies=False
- `/Users/thrill3r/nautilus_trader/tests/test_data/databento/esh4-glbx-mdp3-20231225.mbo.dbn.zst`: dbn_magic=True size=997238 state=decoder_missing_or_sample_too_short qualifies=False

Large dataset references:
- `/Users/thrill3r/nautilus_trader/tests/test_data/large/tardis_BTC-PERPETUAL.DERIBIT_2020-04-01_deltas.metadata.json`: records=19239597 referenced_exists=False state=large_direct_dataset_metadata_only
- `/Users/thrill3r/nautilus_trader/tests/test_data/large/itch_AAPL.XNAS_2019-01-30_deltas.metadata.json`: records=1779561 referenced_exists=False state=large_direct_dataset_metadata_only

Next: Acquire the actual large Tardis/ITCH delta Parquet files or a supported DBN decoder plus sufficiently long MBO sample before rerunning Manipulation gates.
