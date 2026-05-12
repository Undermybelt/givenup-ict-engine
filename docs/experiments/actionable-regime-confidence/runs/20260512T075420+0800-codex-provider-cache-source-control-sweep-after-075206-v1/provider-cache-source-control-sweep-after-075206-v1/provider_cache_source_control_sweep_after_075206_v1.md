# Provider Cache Source/Control Sweep After 075206 v1

Run id: `20260512T075420+0800-codex-provider-cache-source-control-sweep-after-075206-v1`

Gate result: `provider_cache_source_control_sweep_after_075206_v1=no_valid_required_root_no_unlock`

## Scope

Bounded source/control acquisition sweep after the `075206` current-objective audit. It checks exact R3/R5/R6 target roots plus local provider/cache roots associated with Auto-Quant, TradingView, IBKR, Kraken, Tomac/Databento, and the Board A runtime. It does not mutate target roots, derive labels, approve controls, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Board hash before artifact: `c9b35cdca873724ec024969ff0a5fc17498b7c5bb99e4aaa2d3b694b23eef4e9`.
- Provider/cache candidate hits: `124`.
- Provider/cache absent roots: `2`.
- Provider/cache truncated scans: `3`.
- R6 owner/export unlock: `false`.
- R5 recency unlock: `false`.
- R3 native-subhour unlock: `false`.
- Valid required-root unlock: `false`.

## Decision

No provider/cache path supplied verifier-native R6 owner/export positives with matched controls and approving provenance, source-owned post-`2026-01-30` R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export.

Accepted rows added `0`; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T075420+0800-codex-provider-cache-source-control-sweep-after-075206-v1/provider-cache-source-control-sweep-after-075206-v1/provider_cache_source_control_sweep_after_075206_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T075420+0800-codex-provider-cache-source-control-sweep-after-075206-v1/provider-cache-source-control-sweep-after-075206-v1/provider_cache_source_control_candidates_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T075420+0800-codex-provider-cache-source-control-sweep-after-075206-v1/checks/provider_cache_source_control_sweep_after_075206_v1_assertions.out`

## Next

Continue source/control acquisition only before direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
