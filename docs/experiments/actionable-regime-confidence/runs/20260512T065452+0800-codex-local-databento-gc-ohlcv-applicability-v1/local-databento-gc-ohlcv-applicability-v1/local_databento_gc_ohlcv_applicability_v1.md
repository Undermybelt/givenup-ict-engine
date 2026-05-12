# Local Databento GC OHLCV Applicability v1

Run id: `20260512T065452+0800-codex-local-databento-gc-ohlcv-applicability-v1`

Gate result: `local_databento_gc_ohlcv_applicability_v1=source_owned_ohlcv_context_no_r6_r5_r3_unlock_no_downstream`

## Scope

Read-only applicability audit of the local Databento-looking folder found during the current Board A source/control search:

- `/Users/thrill3r/Downloads/Tomac/gc future 2021-2025`

This packet does not extract/copy rows into `/tmp/ict-engine-board-a-r6-owner-export-v1`, does not mutate `/tmp/ict-engine-source-panel-recency-extension`, does not approve TSIE, does not run canonical merge, does not rerun downstream promotion, does not make a trade claim, and does not call `update_goal`.

## Local Evidence

| Path | Observed shape | Applicability |
|---|---|---|
| `databento.rar` | RAR archive, 98 MiB, SHA-256 `60daf9e15e42a8c1884c7dbe36629dcea06fd13f0e20ec0ed0c9d1a74ee51112` | Archive contains `gc_201101_202604.csv` and `nq_201101_202604.csv`; visible file names do not establish labels or controls. |
| `manifest.json` | Job `GLBX-20260108-BUR5BGXTKJ`; file URLs under Databento batch path `DGU3SABE`; output file `glbx-mdp3-20210106-20260105.ohlcv-1m.csv` | Source-owned batch metadata for GC OHLCV bars only. |
| `metadata.json` | Query dataset `GLBX.MDP3`, schema `ohlcv-1m`, symbols `GC.FUT`, `stype_in=parent`, `start=2021-01-06`, `end=2026-01-06` | Confirms minute OHLCV bar schema, not MBO/order-lifecycle/depth/control labels. |
| `gc_201101_202604.csv` | Header `ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol`; `5,327,112` data rows; date range `2011-01-02` to `2026-04-14`; unique symbol `GC.n.0` | Useful GC bar context, but no label/control/source verdict fields. |
| `glbx-mdp3-20210106-20260105.ohlcv-1m.csv` | Same OHLCV header; `5,333,532` data rows; date range `2021-01-06` to `2026-01-05`; `707` symbols | Useful Databento GC batch bars, but not Board A source/control evidence. |

## Decision

This folder is credible local Databento/GLBX OHLCV context for GC futures, and it overlaps the broad R6 product family and some relevant calendar periods. It is still not a valid Board A unlock under the current contract:

- Not R6 owner/export control evidence: visible schemas are OHLCV bars, not source-owned normal controls, MBO/depth/order-lifecycle rows, or manipulation/non-manipulation labels.
- Not R5 recency evidence: no `stock_market_regimes_2026_extension.csv` or `source_panel_recency_provenance.json`, and no post-cutoff `MainRegimeV2` source-panel label rows.
- Not R3 native-subhour evidence: no verifier-native `MainRegimeV2` labels and no `Crisis`-capable label packet.
- Not canonical merge input and not downstream promotion evidence.

## Accounting

- Accepted rows added: `0`
- Valid required-root unlock: `false`
- Source/control evidence acquired: `false`
- Canonical merge: `false`
- Downstream promotion rerun: `false`
- Strict full objective: `false`
- Trade usable: `false`
- `update_goal=false`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 recency rows, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before running direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
