# Direct Input Inventory

Loop id: `20260511T005259+0800-codex-persistent-root-state-and-direct-input-audit`

Summary:

- `scanned_file_count`: `54`
- `ohlcv_like_file_count`: `52`
- `options_surface_like_file_count`: `2`
- `direct_candidate_file_count`: `1`
- `chronological_direct_candidate_file_count`: `1`
- `l2_or_order_lifecycle_candidate_file_count`: `0`
- `direct_manipulation_inputs_chronological_calibration_usable`: `False`
- `decision`: `missing_required_inputs`

Notes:
- OHLCV or options-greek files are not sufficient to accept Manipulation.
- A usable Manipulation packet needs chronological tick/trade plus bid/ask, L2/depth, order lifecycle, venue event, or crypto event/social/on-chain evidence.

Direct candidate examples:

- `/Users/thrill3r/Auto-Quant/user_data/data/options/bybit_BTC.csv` rows=500 matches={'bid_ask': ['ask_price', 'bid_price']}
