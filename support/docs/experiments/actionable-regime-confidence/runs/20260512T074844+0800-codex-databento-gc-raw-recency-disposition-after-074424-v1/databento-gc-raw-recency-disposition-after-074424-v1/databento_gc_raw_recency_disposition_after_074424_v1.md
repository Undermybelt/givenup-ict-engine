# Databento GC Raw Recency Disposition After 074424 v1

Run id: `20260512T074844+0800-codex-databento-gc-raw-recency-disposition-after-074424-v1`

Gate result: `databento_gc_raw_recency_disposition_after_074424_v1=raw_ohlcv_post_cutoff_no_source_label_or_control_unlock`

## Scope

Bounded disposition of the local Databento/Tomac GC futures package found under Downloads after the post-074116 source-route probes. This packet does not mutate R3/R5/R6 target roots, derive labels, approve controls, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Local root: `/Users/thrill3r/Downloads/Tomac/gc future 2021-2025`.
- Manifest job id: `GLBX-20260108-BUR5BGXTKJ`; dataset `GLBX.MDP3`; schema `ohlcv-1m`; symbols `['GC.FUT']`.
- Continuous GC candidate rows: `5327112`; first timestamp `2011-01-02 18:00:00-05:00`; last timestamp `2026-04-14 19:59:00-04:00`.
- GLBX OHLCV manifest candidate rows: `5333532`; first timestamp `2021-01-06T00:00:00.000000000Z`; last timestamp `2026-01-05T23:59:00.000000000Z`.
- Archive present: `True`; archive size bytes `102402878`.
- Candidate CSV columns are OHLCV/symbology fields only. No `main_regime_v2_label`, `regime_label`, `source_confidence`, `direct_label`, `matched_negative_group_id`, or order-lifecycle control columns are present.

## Decision

The package is real local raw market data and the continuous GC file extends past `2026-01-30`, but it is not source-owned `MainRegimeV2` label evidence and not R6 owner-export control evidence. It cannot fill `/tmp/ict-engine-source-panel-recency-extension`, `/tmp/ict-engine-native-subhour-source-label-intake`, or `/tmp/ict-engine-board-a-r6-owner-export-v1` under the current Board A contract.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Next

Continue source/control acquisition only. Do not convert Databento raw OHLCV into source-owned labels or matched controls; wait for explicit source-owned post-cutoff label rows, verifier-native R3 labels, R6 controls, or explicit `FLIP` approval before downstream promotion.

