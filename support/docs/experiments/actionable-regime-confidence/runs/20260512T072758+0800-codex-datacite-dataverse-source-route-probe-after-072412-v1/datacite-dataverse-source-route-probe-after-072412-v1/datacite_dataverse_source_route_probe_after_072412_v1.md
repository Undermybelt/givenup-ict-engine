# Datacite/Dataverse Source Route Probe After 072412 v1

Run id: `20260512T072758+0800-codex-datacite-dataverse-source-route-probe-after-072412-v1`

Gate result: `datacite_dataverse_source_route_probe_after_072412_v1=no_required_source_route_no_unlock`

## Scope

Readback packet for the raw Datacite and Harvard Dataverse source-route probe after `072412`. This packet summarizes existing command outputs only. It does not mutate R3/R5/R6 target roots, approve any public-search result, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- The probe ran `24` source-route queries: `12` Datacite queries and `12` Harvard Dataverse dataset queries.
- All query exit files were `0`.
- Required exact/strict route searches returned no usable source/control rows:
  - Datacite `MainRegimeV2`: `0`; Dataverse `MainRegimeV2`: `0`.
  - Datacite `native_subhour_source_label_rows`: `0`; Dataverse `native_subhour_source_label_rows`: `0`.
  - Datacite strict `direct_manipulation_positive_rows`: `0`; Dataverse strict `direct_manipulation_positive_rows`: `0`.
  - Datacite strict `direct_manipulation_matched_controls`: `0`; Dataverse strict `direct_manipulation_matched_controls`: `0`.
  - Datacite strict `Oystacher`: `0`; Dataverse strict `Oystacher`: `0`.
- Datacite broad query `direct manipulation positive rows matched controls` returned broad false positives. The top titles were recursive-harmonic / COVID narrative records, not trading-owner exports, positives, matched controls, provenance, `MainRegimeV2`, or native-subhour labels.
- Datacite strict `3Red` returned figshare records about the RFC/TAPS `3RED` model, not 3 Red Trading / Oystacher / CFTC owner-export data.
- Dataverse broad query counts were high for generic phrases, but strict required searches were `0`; broad hits are search noise and are not source/control evidence.

## Decision

No Datacite or Harvard Dataverse source route supplied a valid Board A/B unlock. Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- Command output root: `docs/experiments/actionable-regime-confidence/runs/20260512T072758+0800-codex-datacite-dataverse-source-route-probe-after-072412-v1/command-output/`
- Summary JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T072758+0800-codex-datacite-dataverse-source-route-probe-after-072412-v1/datacite-dataverse-source-route-probe-after-072412-v1/datacite_dataverse_source_route_probe_after_072412_v1.json`
- Summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T072758+0800-codex-datacite-dataverse-source-route-probe-after-072412-v1/datacite-dataverse-source-route-probe-after-072412-v1/datacite_dataverse_source_route_probe_after_072412_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T072758+0800-codex-datacite-dataverse-source-route-probe-after-072412-v1/checks/datacite_dataverse_source_route_probe_after_072412_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant selected-data research, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
