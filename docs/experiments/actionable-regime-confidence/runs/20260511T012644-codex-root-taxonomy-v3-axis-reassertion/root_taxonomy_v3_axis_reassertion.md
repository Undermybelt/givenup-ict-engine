# Superseded RootTaxonomyV3 Axis Reassertion Drift

Run id: `20260511T012644-codex-root-taxonomy-v3-axis-reassertion`

## Reason

This artifact tried to reactivate RootTaxonomyV3 after `20260511T011114-codex-main-regime-v2-axis-restored`. The later user correction says those labels read as child classes under the main regime axis, so this artifact is now wrong-axis provenance only.

## Superseded Axis

Do not use RootTaxonomyV3 as the active axis. Treat these labels as child/provenance evidence:

- `BullExpansion`
- `BearExpansion`
- `Consolidation`
- direct-input-gated `Manipulation`
- `CrisisStress`
- optional/overlay `TransitionRecovery`
- residual `UnknownOrMixed`

The active root labels remain `Bull`, `Bear`, `Sideways`, `Crisis`, direct-input-gated `Manipulation`, and residual `UnknownOrMixed`.

## Superseded Branch Gate State

- Accepted required 95 root: `CrisisStress`
- Accepted optional overlay evidence: `TransitionRecovery`
- Missing required 95 roots: `BullExpansion`, `BearExpansion`, `Consolidation`, `Manipulation`
- Residual only: `UnknownOrMixed`

Board A remains blocked under the active MainRegimeV2 gate because only `Crisis` has accepted root evidence; `Bull`, `Bear`, `Sideways`, and direct-input-gated `Manipulation` are still missing. Runtime code changed: false. Thresholds relaxed: false.
