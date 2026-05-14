# Local Databento Archive Readback After 082240 v1

Run id: `20260512T082629+0800-codex-local-databento-archive-readback-after-082240-v1`

Gate result: `local_databento_archive_readback_after_082240_v1=ohlcv_only_no_source_control_unlock`

## Scope

Read-only inspection of the local `databento.rar` archive found under Downloads. This packet checks whether the archive can satisfy the current Board A R6 source/control blocker. It does not extract files into repo state, mutate target roots, accept rows, run verifier/split calibration, rerun provider/Auto-Quant/Pre-Bayes/BBN/CatBoost/execution-tree, make a trade claim, or call `update_goal`.

## Archive Readback

- Archive: `/Users/thrill3r/Downloads/Tomac/gc future 2021-2025/databento.rar`
- Manifest job id: `GLBX-20260108-BUR5BGXTKJ`
- Dataset: `GLBX.MDP3`
- Schema: `ohlcv-1m`
- Symbols: `GC.FUT`
- Archive SHA-256: `60daf9e15e42a8c1884c7dbe36629dcea06fd13f0e20ec0ed0c9d1a74ee51112`

## Member Headers

| Member | Header | Has order-lifecycle/control columns |
|---|---|---|
| `gc_201101_202604.csv` | `ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol` | `False` |
| `nq_201101_202604.csv` | `ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol` | `False` |

## Decision

- The archive is real local Databento/CME data, but it is `ohlcv-1m` bar data only.
- It contains GC/NQ OHLCV headers (`ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol`) and no order-id, side, quote, book-depth, participant, source-section, or label columns needed for R6 source-owned positive/control rows.
- Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Next

Continue source/control acquisition only. This archive can remain local market context, not the required R6 owner/export source-control root. The live unblocker remains owner-approved/authenticated FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE order-lifecycle export with positives and matched normal controls, or explicit same-exhibit FLIP-as-control approval.
