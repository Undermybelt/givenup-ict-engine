# DataCite Source Route Probe After 072412 v1

Run id: `20260512T072832+0800-codex-datacite-source-route-probe-after-072412-v1`

Gate result: `datacite_source_route_probe_after_072412_v1=no_exact_required_source_export_no_unlock`

## Scope

Metadata-only DataCite source-route probe after the duplicate `072412` Zenodo route. This packet searches registered dataset DOI metadata for exact R3/R5/R6 unlock terms. It does not download raw row data, mutate R3/R5/R6 roots, approve metadata-only records, run direct verifier, run split calibration, run canonical merge, run provider/AutoQuant promotion, run downstream filter/Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Queries run: `11`.
- Failed queries: `0`.
- Total returned records inspected: `0`.
- Exact required-term hits in returned metadata: `0`.

## Decision

No DataCite metadata result exposed a required source/control export for `direct_manipulation_positive_rows`, `direct_manipulation_matched_controls`, `direct_manipulation_provenance`, `stock_market_regimes_2026_extension`, `native_subhour_source_label_rows`, or `MainRegimeV2`.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T072832+0800-codex-datacite-source-route-probe-after-072412-v1/datacite-source-route-probe-after-072412-v1/datacite_source_route_probe_after_072412_v1.json`
- CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T072832+0800-codex-datacite-source-route-probe-after-072412-v1/datacite-source-route-probe-after-072412-v1/datacite_source_route_probe_after_072412_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T072832+0800-codex-datacite-source-route-probe-after-072412-v1/checks/datacite_source_route_probe_after_072412_v1_assertions.out`
- Command output: `docs/experiments/actionable-regime-confidence/runs/20260512T072832+0800-codex-datacite-source-route-probe-after-072412-v1/command-output`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant selected-data research, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
