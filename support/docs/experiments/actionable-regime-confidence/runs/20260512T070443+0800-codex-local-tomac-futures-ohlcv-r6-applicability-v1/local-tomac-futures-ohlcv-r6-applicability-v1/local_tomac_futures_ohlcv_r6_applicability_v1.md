# Local Tomac Futures OHLCV R6 Applicability v1

Run id: `20260512T070443+0800-codex-local-tomac-futures-ohlcv-r6-applicability-v1`

Gate result: `local_tomac_futures_ohlcv_r6_applicability_v1=multi_futures_ohlcv_context_no_r6_r5_r3_unlock_no_downstream`

Board SHA-256 before artifact: `a43899d6603d94f6ff224f2bc84c04886084d0566036d2c099895a55cc78d4bf`

## Scope

Read-only audit of local Tomac/Databento futures packages after prior scans showed `mbo`-like symbology filenames. This run does not extract large archives, copy rows into `/tmp/ict-engine-board-a-r6-owner-export-v1`, mutate R3/R5/R6 roots, approve controls, run direct verifier, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Readback

- Local folders inspected: ES, NQ, YM, 6E, and GC futures folders under `/Users/thrill3r/Downloads/Tomac`.
- Metadata identifies Databento `GLBX.MDP3` jobs with schema `ohlcv-1m`.
- Visible data headers are OHLCV-only: `ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol`.
- ZIP/RAR listings contain OHLCV CSVs, `condition.json`, `metadata.json`, `manifest.json`, and symbology files only.
- Visible row coverage includes multi-year ES/NQ/YM/6E/GC rows and some post-`2026-01-30` OHLCV context, but no source-owned `MainRegimeV2` labels or R5 provenance.
- No bid/ask, order id, MBO/depth, order-lifecycle, normal-control label, manipulation label, or explicit source/control approval was found in the audited files.

## Decision

The Tomac folders are useful market-data context, not Board A source/control unlock evidence. They cannot satisfy R6 because they are OHLCV bars rather than verifier-native owner/export normal controls. They cannot satisfy R5 because they have no source-panel `Bull/Bear/Sideways/Crisis` labels plus provenance. They cannot satisfy R3 because they have no native sub-hour `MainRegimeV2` labels.

Accepted rows added `0`; R6 owner/export unlock `false`; R5 recency unlock `false`; R3 native-subhour unlock `false`; valid required-root unlock `false`; source/control evidence acquired `false`; canonical merge `false`; downstream promotion rerun `false`; strict full objective `false`; trade usable `false`; `update_goal=false`.

## Artifacts

- Inventory CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T070443+0800-codex-local-tomac-futures-ohlcv-r6-applicability-v1/local-tomac-futures-ohlcv-r6-applicability-v1/tomac_futures_local_inventory_v1.csv`
- Archive listing CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T070443+0800-codex-local-tomac-futures-ohlcv-r6-applicability-v1/local-tomac-futures-ohlcv-r6-applicability-v1/tomac_futures_archive_listing_v1.csv`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T070443+0800-codex-local-tomac-futures-ohlcv-r6-applicability-v1/local-tomac-futures-ohlcv-r6-applicability-v1/local_tomac_futures_ohlcv_r6_applicability_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T070443+0800-codex-local-tomac-futures-ohlcv-r6-applicability-v1/checks/local_tomac_futures_ohlcv_r6_applicability_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 recency rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant promotion, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
