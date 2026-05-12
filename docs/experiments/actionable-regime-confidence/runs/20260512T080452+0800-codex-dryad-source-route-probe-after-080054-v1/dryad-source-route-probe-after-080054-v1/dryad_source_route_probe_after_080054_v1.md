# Dryad Source Route Probe After 080054 v1

Run id: `20260512T080452+0800-codex-dryad-source-route-probe-after-080054-v1`

Gate result: `dryad_source_route_probe_after_080054_v1=no_required_source_control_unlock`

## Scope

Read-only Dryad API source-route probe after `080054` stayed blocked. It checks whether Dryad exposes source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, R6 owner/export positives with matched controls, or a new accepted cross-timeframe `MainRegimeV2` source export. It does not mutate R3/R5/R6 target roots, approve public metadata as source/control evidence, derive labels, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Requests sent: `9`.
- Failed or parse-failed requests: `0`.
- Top metadata rows scanned: `45`.
- Required filename/token hits: `0`.
- Exact `MainRegimeV2` hits: `0`.
- R5 post-cutoff source-panel hits: `0`.
- R3 native-subhour Crisis hits: `0`.
- R6 owner/control hits: `0`.

## Decision

No Dryad route supplied verifier-native R6 owner/export positives with matched controls and approving provenance, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T080452+0800-codex-dryad-source-route-probe-after-080054-v1/dryad-source-route-probe-after-080054-v1/dryad_source_route_probe_after_080054_v1.json`
- Candidate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T080452+0800-codex-dryad-source-route-probe-after-080054-v1/dryad-source-route-probe-after-080054-v1/dryad_source_route_candidates_v1.csv`
- Request CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T080452+0800-codex-dryad-source-route-probe-after-080054-v1/dryad-source-route-probe-after-080054-v1/dryad_source_route_requests_v1.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T080452+0800-codex-dryad-source-route-probe-after-080054-v1/checks/dryad_source_route_probe_after_080054_v1_assertions.out`
- Command output root: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T080452+0800-codex-dryad-source-route-probe-after-080054-v1/command-output`

## Next

Continue source/control acquisition only before any direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
