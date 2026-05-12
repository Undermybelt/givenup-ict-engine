# Local Order-Lifecycle / Depth Source Scan After 070840 v1

Run id: `20260512T071316+0800-codex-local-order-lifecycle-depth-source-scan-after-070840-v1`

This is a read-only local source/control acquisition slice for the R6 blocker. It looks beyond the Tomac-only audit for local order-lifecycle, MBO/MBP, depth, order-book, quote/trade, or source-control candidate files under `Downloads`, `Auto-Quant`, `/tmp`, and existing Board A experiment artifacts.

## Readback

- No actual `.dbn` files were found in the searched local roots.
- No MBO/MBP, market-depth, order-lifecycle, or source-owned normal-control data files were found.
- `/tmp` returned no matching candidate source/control files.
- External data-source matches under `Downloads/external-data-sources` are provider/client/example code only, not row exports or labels.
- The visible Tomac / Databento archives remain OHLCV context:
  - `GLBX-20260404-NQ.zip` metadata says dataset `GLBX.MDP3`, schema `ohlcv-1m`, symbol `NQ.FUT`.
  - `GLBX-20260404-NQ.zip` contains `glbx-mdp3-20100606-20260403.ohlcv-1m.csv`.
  - `nq future 2021-2025.zip` and `es future 2021-2025.zip` contain `glbx-mdp3-20110101-20251231.ohlcv-1m.csv`.
  - `gc future 2021-2025/databento.rar` lists `gc_201101_202604.csv` and `nq_201101_202604.csv`.
  - Sample headers are OHLCV: `ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol`.

## Decision

Gate: `local_order_lifecycle_depth_source_scan_after_070840_v1=local_search_found_ohlcv_and_code_only_no_r6_r5_r3_unlock_no_downstream`.

Accepted rows added: `0`.
Valid required-root unlock: `false`.
Source/control evidence acquired: `false`.
R6 owner/export unlock: `false`.
R5 recency unlock: `false`.
R3 native-subhour unlock: `false`.
Canonical merge: `false`.
Downstream promotion rerun: `false`.
Strict full objective: `false`.
Trade usable: `false`.
`update_goal=false`.

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.
