# Open Data Catalog Source Route Probe After 074116 v1

Run id: `20260512T074447+0800-codex-open-data-catalog-source-route-probe-after-074116-v1`

Gate result: `open_data_catalog_source_route_probe_after_074116_v1=no_required_source_control_unlock`

## Scope

This packet is source/control acquisition only. It queries public catalog metadata and does not mutate R3/R5/R6 target roots, approve any local or public candidate, select historical data, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Surfaces

- Data.gov dataset HTML search
- GitLab public project search
- OpenML dataset-name API
- AWS Open Data Registry HTML search

## Readback

- Requests sent: `36`.
- Failed or parse-failed requests: `0`.
- Top metadata rows scanned: `93`.
- Required filename hits: `0`.
- Owner hits: `0`.
- `MainRegimeV2` hits: `0`.
- R3 native-subhour hits: `0`.
- R5 recency hits: `0`.
- R6 required-file hits: `0`.
- Broad context hits: `0`.

## Decision

No open-data catalog metadata route supplied verifier-native R6 owner/export positives with matched controls and provenance, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.

Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; direct verifier false; split calibration false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T074447+0800-codex-open-data-catalog-source-route-probe-after-074116-v1/open-data-catalog-source-route-probe-after-074116-v1/open_data_catalog_source_route_probe_after_074116_v1.json`
- CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T074447+0800-codex-open-data-catalog-source-route-probe-after-074116-v1/open-data-catalog-source-route-probe-after-074116-v1/open_data_catalog_source_route_probe_after_074116_v1.csv`
- Command output root: `docs/experiments/actionable-regime-confidence/runs/20260512T074447+0800-codex-open-data-catalog-source-route-probe-after-074116-v1/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T074447+0800-codex-open-data-catalog-source-route-probe-after-074116-v1/checks/open_data_catalog_source_route_probe_after_074116_v1_assertions.out`

## Next

Continue source/control acquisition only before any direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
