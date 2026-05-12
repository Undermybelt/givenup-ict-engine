# OpenML / Dataverse Source Route Probe After 075932 v1

Run id: `20260512T080333+0800-codex-openml-dataverse-source-route-probe-after-075932-v1`

Gate result: `openml_dataverse_source_route_probe_after_075932_v1=no_required_source_control_unlock`

## Scope

Bounded public OpenML and Harvard Dataverse metadata probe after the `075932` Figshare/OSF route stayed fail-closed. This checks whether another public dataset route exposes source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, R6 owner/export positives with matched controls, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export. It does not mutate R3/R5/R6 target roots, approve public metadata as source/control evidence, download or derive labels, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Providers queried: OpenML and Harvard Dataverse.
- Requests sent: `16`.
- Request failures: `8`.
- Candidate rows scanned: `50`.
- Required metadata hits: `0`.
- Exact `MainRegimeV2` hits: `0`.
- R5 post-cutoff source-panel hits: `0`.
- R3 native-subhour Crisis hits: `0`.
- R6 owner/control hits: `0`.

## Decision

No OpenML or Harvard Dataverse route supplied verifier-native R6 owner/export positives with matched controls and approving provenance, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, or a genuinely accepted cross-timeframe `MainRegimeV2` source export.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T080333+0800-codex-openml-dataverse-source-route-probe-after-075932-v1/openml-dataverse-source-route-probe-after-075932-v1/openml_dataverse_source_route_probe_after_075932_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T080333+0800-codex-openml-dataverse-source-route-probe-after-075932-v1/openml-dataverse-source-route-probe-after-075932-v1/openml_dataverse_source_route_candidates_v1.csv`
- Request CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T080333+0800-codex-openml-dataverse-source-route-probe-after-075932-v1/openml-dataverse-source-route-probe-after-075932-v1/openml_dataverse_source_route_requests_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T080333+0800-codex-openml-dataverse-source-route-probe-after-075932-v1/checks/openml_dataverse_source_route_probe_after_075932_v1_assertions.out`

## Next

Continue source/control acquisition only before any direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
