# Tomac Local Source Label Sidecar Scan After 074844 v1

Run id: `20260512T075411+0800-codex-tomac-local-source-label-sidecar-scan-after-074844-v1`

Gate result: `tomac_local_source_label_sidecar_scan_after_074844_v1=no_source_label_or_control_sidecar_no_unlock`

## Scope

Read-only sidecar scan around `/Users/thrill3r/Downloads/Tomac` after the `074844` Databento GC raw recency disposition. This packet checks whether the Tomac/Databento local data family has adjacent source-owned `MainRegimeV2`, source-confidence, matched-control, direct-label, or order-lifecycle sidecars that could unlock Board A. It does not mutate target roots, derive labels from OHLCV, approve controls, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Filename scan under `/Users/thrill3r/Downloads/Tomac` for `label`, `regime`, `source`, `control`, `negative`, `spoof`, `order`, `lifecycle`, and `mainregime` patterns returned no source/control sidecar filename hits.
- Non-binary content scan for `MainRegimeV2`, `main_regime_v2`, `source_confidence`, `matched_negative`, `order_lifecycle`, `SPOOF`, `FLIP`, `regime_label`, and `direct_label` found only local report-style `market_regime_label` fields in:
  - `/Users/thrill3r/Downloads/Tomac/ict-cleaned-15m-expansion/expansion_sop_report.15m.json`
  - `/Users/thrill3r/Downloads/Tomac/ict-engine-expansion-sop-15m/expansion_sop_report.15m.json`
- CSV-header scan across Tomac CSV files found no `MainRegimeV2`, `main_regime_v2`, `source_confidence`, `matched_negative`, `order_lifecycle`, `SPOOF`, `FLIP`, `regime_label`, `direct_label`, `market_regime_label`, `source_panel`, or `confidence` header.
- Tomac contains raw Databento/Tomac futures packages for ES, EUR, GC, NQ, and YM plus local cleaned JSONs, factor states, strategy files, and backtest outputs. These are local runtime / strategy / OHLCV artifacts, not source-owned regime labels or owner-export controls.

## Decision

No Tomac sidecar supplies verifier-native R6 owner/export positives with matched controls and provenance, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, or a genuinely accepted cross-timeframe `MainRegimeV2` source export.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- Report: `docs/experiments/actionable-regime-confidence/runs/20260512T075411+0800-codex-tomac-local-source-label-sidecar-scan-after-074844-v1/tomac-local-source-label-sidecar-scan-after-074844-v1/tomac_local_source_label_sidecar_scan_after_074844_v1.md`
- CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T075411+0800-codex-tomac-local-source-label-sidecar-scan-after-074844-v1/tomac-local-source-label-sidecar-scan-after-074844-v1/tomac_local_source_label_sidecar_scan_after_074844_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T075411+0800-codex-tomac-local-source-label-sidecar-scan-after-074844-v1/checks/tomac_local_source_label_sidecar_scan_after_074844_v1_assertions.out`

## Next

Continue source/control acquisition only. Do not convert local Tomac OHLCV, cleaned JSONs, factor states, strategy rows, or backtest rows into source-owned labels or matched controls.
