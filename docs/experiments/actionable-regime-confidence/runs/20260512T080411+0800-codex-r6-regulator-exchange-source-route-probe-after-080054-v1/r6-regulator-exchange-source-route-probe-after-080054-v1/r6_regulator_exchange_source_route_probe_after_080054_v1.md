# R6 Regulator Exchange Source Route Probe After 080054 v1

Run id: `20260512T080411+0800-codex-r6-regulator-exchange-source-route-probe-after-080054-v1`

Gate result: `r6_regulator_exchange_source_route_probe_after_080054_v1=official_context_only_no_owner_export_control_unlock`

## Scope

Read-only official regulator/exchange source-route probe for R6 owner/export evidence after the `080054` completion audit stayed blocked. It checks CFTC, CME, DOJ, and SEC official pages for Oystacher/3Red/spoofing context and for actual source-owned positive-row exports plus matched normal/control rows. It does not mutate target roots, derive labels, approve prose as controls, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Board hash before artifact: `084ce3863ba79a8c26e3271bb5c1433d07a010d5dcfbce66afb8d51c24af95d1`.
- Sources checked: `6`.
- HTTP/status failures: `2`.
- Official context hits: `3`.
- Possible complete R6 row/control exports: `0`.

## Source Disposition

- `cftc` `press_release` `Oystacher 3Red CFTC consent order`: status `200`, context `oystacher;three_red;spoofing;market_depth;cancel_lifecycle;matched_controls_context`, required-export `none`, disposition `official_context_only_no_positive_or_control_rows`.
- `cftc` `legal_pleading_pdf` `Oystacher 3Red CFTC complaint`: status `200`, context `oystacher;three_red;market_depth`, required-export `none`, disposition `official_context_only_no_positive_or_control_rows`.
- `cme` `disciplinary_notice` `COMEX Oystacher disciplinary notice`: status `403`, context `none`, required-export `none`, disposition `no_relevant_source_control_terms`.
- `cftc` `press_release` `Panther Coscia spoofing broader official comparator`: status `200`, context `spoofing;cancel_lifecycle;matched_controls_context`, required-export `none`, disposition `official_context_only_no_positive_or_control_rows`.
- `doj` `speech` `DOJ futures markets spoofing takedown data analysis context`: status `200`, context `none`, required-export `none`, disposition `no_relevant_source_control_terms`.
- `sec` `press_release` `SEC spoofing scheme controls comparator`: status `403`, context `none`, required-export `none`, disposition `no_relevant_source_control_terms`.

## Decision

The official regulator/exchange pages provide useful R6 context for spoofing, market-depth/book-pressure behavior, cancellations, and monitoring/compliance language, but this packet found no source-owned machine-readable positive spoofing/layering rows, no matched normal/control rows, and no owner/export provenance that would satisfy Board A R6.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T080411+0800-codex-r6-regulator-exchange-source-route-probe-after-080054-v1/r6-regulator-exchange-source-route-probe-after-080054-v1/r6_regulator_exchange_source_route_probe_after_080054_v1.json`
- Source CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T080411+0800-codex-r6-regulator-exchange-source-route-probe-after-080054-v1/r6-regulator-exchange-source-route-probe-after-080054-v1/r6_regulator_exchange_source_route_sources_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T080411+0800-codex-r6-regulator-exchange-source-route-probe-after-080054-v1/checks/r6_regulator_exchange_source_route_probe_after_080054_v1_assertions.out`
- Command output root: `docs/experiments/actionable-regime-confidence/runs/20260512T080411+0800-codex-r6-regulator-exchange-source-route-probe-after-080054-v1/command-output/`

## Next

Continue source/control acquisition only. Do not promote official prose, disciplinary notices, complaints, or press releases as R6 owner/export rows or matched controls.
