# Public Codehost Source Route Probe After 074116 v1

Run id: `20260512T074424+0800-codex-public-codehost-source-route-probe-after-074116-v1`

Gate result: `public_codehost_source_route_probe_after_074116_v1=no_required_source_export_no_unlock`

## Scope

Source/control acquisition only after the `074116` manual R3 settlement. This packet searches public code-host surfaces for exact R3/R5/R6 artifact names and owner-export terms. It does not mutate target roots, approve code-host hits as source/control rows, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Public Surfaces Queried

- grep.app public GitHub code index API
- GitHub repository search API
- GitHub code search API availability/readback
- GitLab public project search API

## Summary

- Requests sent: `48`
- Failed or blocked requests: `38`
- Top records scanned: `0`
- Nonzero provider search totals: `0`
- Required filename hits: `0`
- Owner hits: `0`
- `MainRegimeV2` hits: `0`
- R3 native-subhour hits: `0`
- Crisis-context hits: `0`
- R5 recency hits: `0`
- R6 filename/owner hits: `0`

## Web Search Fallback

Exact web queries for `MainRegimeV2`, `native_subhour_source_label_rows`, `stock_market_regimes_2026_extension`, `direct_manipulation_positive_rows`, `direct_manipulation_matched_controls`, and `direct_manipulation_provenance` returned no visible required artifact-name results. The Oystacher / 3Red query surfaced CFTC release `7504-16` at `https://www.cftc.gov/PressRoom/PressReleases/7504-16`, but that is context-only enforcement text and does not expose owner-export rows, matched controls, provenance, or a source/control approval package.

## Decision

No required source/control root unlocked. Public code-host hits, if any, are discovery metadata/code-snippet evidence only and are not accepted as verifier-native R6 owner/export positives plus matched controls, source-owned post-`2026-01-30` R5 source-panel rows, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or explicit source/control approval.

Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T074424+0800-codex-public-codehost-source-route-probe-after-074116-v1/public-codehost-source-route-probe-after-074116-v1/public_codehost_source_route_probe_after_074116_v1.csv`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T074424+0800-codex-public-codehost-source-route-probe-after-074116-v1/public-codehost-source-route-probe-after-074116-v1/public_codehost_source_route_probe_after_074116_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T074424+0800-codex-public-codehost-source-route-probe-after-074116-v1/checks/public_codehost_source_route_probe_after_074116_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
