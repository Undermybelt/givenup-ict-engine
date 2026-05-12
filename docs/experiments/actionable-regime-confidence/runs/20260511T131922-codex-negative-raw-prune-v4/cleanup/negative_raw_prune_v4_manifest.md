# Negative Raw Prune Manifest v4

Run ID: `20260511T131922+0800-codex-negative-raw-prune-v4`

## Scope

- Purpose: act on the disk-footprint warning by pruning old negative/provenance raw intermediates before running more evidence loops.
- Preserved: current board markdown, JSON reports, Markdown reports, checks/assertions, scripts, the existing `20260511T131311` direct `Manipulation` matrix, the concurrent `20260511T131411` source-consensus timeframe gate, `20260511T130916` `MainRegimeV2` relock, `20260511T130655` derived timeframe probe, and board-referenced raw artifacts such as the CFTC feature table and persistent HMM posterior scores.
- Removed: duplicated Auto-Quant dependency/cache trees copied under old repo-local experiment state dirs, plus three failed/partial generated feature matrices whose compact JSON/check artifacts remain.
- Runtime code changed: false.
- Thresholds changed: false.
- Board cursor changed: false.

## Removed Repo-Local Raw/Intermediate Artifacts

| Path | Size Before | SHA-256 Before | Reason |
|---|---:|---|---|
| `docs/experiments/actionable-regime-confidence/runs/20260510T191125-board-b-nq-5m-factor-research/state/.deps/auto-quant` | `3.6M` | directory | duplicated managed dependency/cache tree; not a regime evidence artifact |
| `docs/experiments/actionable-regime-confidence/runs/20260510T191144-board-b-factor-research-mtf1h/ict-engine/state/.deps/auto-quant` | `11M` | directory | duplicated managed dependency/cache tree; not a regime evidence artifact |
| `docs/experiments/actionable-regime-confidence/runs/20260510T191350-codex-nq-structural-replay36/structural-replay-nq-36/state/auto-quant/auto-quant/.deps/auto-quant` | `11M` | directory | duplicated managed dependency/cache tree; compact run readbacks remain |
| `docs/experiments/actionable-regime-confidence/runs/20260510T200154-hermes-loop-full-chain-reaudit/state-copy/auto-quant/auto-quant/.deps/auto-quant` | `3.6M` | directory | duplicated managed dependency/cache tree; compact reaudit packets remain |
| `docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/autoquant/state/auto-quant/auto-quant/.deps/auto-quant` | `11M` | directory | duplicated managed dependency/cache tree; candidate-search report/checks remain |
| `docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/ict-engine/state-copy/auto-quant/auto-quant/.deps/auto-quant` | `3.6M` | directory | duplicated managed dependency/cache tree; state-copy evidence summaries remain |
| `docs/experiments/actionable-regime-confidence/runs/20260511T003739-source-backed-root-gate-mtf/root-v2-source-backed/source_backed_root_feature_table.csv` | `28M` | `5b5dcacfd79e1e7b4768a6a02a2eaa89ab89bb1c9237de96a36950385079f3d7` | obsolete partial source-backed root matrix; compact report/check preserve `accepted_gate=partial_for_MainRegimeV2_source_backed_roots`, blocked roots, and guardrails |
| `docs/experiments/actionable-regime-confidence/runs/20260510T204325-hermes-a8-transition-sidecar/sidecar/a8_transition_sidecar_features.csv` | `7.2M` | `7f6968022d36e443c25742791e7232303a51215af6401bfb55370c853ecb4d90` | failed sidecar feature matrix; evidence packet records `accepted_95_candidates=0` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T205000-hermes-a9-tv-formula-recipes/recipes/a9_tv_formula_features.csv` | `7.8M` | `7a7ec44a7d308ecf6310fb82d824eacedb5ca2ed45ddacf0bb08fb1c7fd033b2` | failed TV-formula feature matrix; evidence packet records `accepted_95_candidates=0` |

## Verification

- `lsof` returned no open handles for the three deleted CSV files before removal.
- Post-delete existence check returned no remaining selected paths.
- `docs/experiments/actionable-regime-confidence/runs` dropped from `351M` to `263M`.
- Board cursor was read before cleanup as `20260511T131311+0800-codex-direct-manipulation-variety-matrix-v1`; post-cleanup readback showed another agent had advanced it to `20260511T131411+0800-codex-source-consensus-timeframe-gate-v1`. This cleanup did not edit the board to avoid racing that work.

## Follow-Up Guardrail

Negative, partial, or provenance loops should keep replay-sized matrices, provider downloads, and managed dependency caches outside the repo run tree. Repo-local run roots should keep compact JSON/MD/check evidence and prune raw intermediates immediately after assertions exist.
