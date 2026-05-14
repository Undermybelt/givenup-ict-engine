# PumpOlymp Live API Direct Preflight

Run ID: `20260511T111647+0800-codex-pumpolymp-live-api-direct-preflight`

## Scope

This preflight checks the live PumpOlymp web/API surface for direct `Manipulation` rows usable by Board A.

## Readback

- API base extracted from app bundle: `https://api.pumpolymp.com`.
- Summary total: `27224`.
- Summary first-page count: `25`.
- First-page unique pairs: `15`.
- First-page start time span: `2026-01-15T00:17:57` to `2026-01-15T03:08:52`.
- Positive pump documents available: `true`.
- Same-asset/venue negative controls available from probed endpoints: `false`.
- Manual/adjudicated event-label source visible from probed endpoints: `false`.

## Schema

- Summary item keys: `dedupe_key, end_block, end_time_utc, external_links, growth_x, id, pair_address, pair_name, peak_block, peak_price, peak_time_utc, points_count, start_block, start_price, start_time_utc, token0_address, token0_decimals, token0_symbol, token1_address, token1_decimals, token1_symbol, window_seconds`.
- Latest detail item keys: `dedupe_key, end_block, end_time_utc, external_links, growth_x, id, pair_address, pair_name, peak_block, peak_price, peak_time_utc, points, points_count, start_block, start_price, start_time_utc, token0_address, token0_decimals, token0_symbol, token1_address, token1_decimals, token1_symbol, window_seconds`.
- Point keys: `block_number, log_pos, price, receipt_index, timestamp_utc`.

## Decision

- Accepted parent-root slots added: `0`.
- Accepted direct `Manipulation` rows added: `0`.
- Gate result: `blocked_pumpolymp_live_api_positive_only_no_negative_controls`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

This is a useful direct-positive acquisition lead, but it remains positive-only detector output from a BSC/DexScreener-style pair archive. It does not satisfy the current Board A direct gate without same-pair non-pump controls or adjudicated event-label provenance.
