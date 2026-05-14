# RootTaxonomyV3 TransitionRecovery Contract Audit

Run id: `20260511T012153-codex-root-taxonomy-v3-transition-contract-audit`

## Result

- Branch status: superseded/provenance only after `20260511T011114-codex-main-regime-v2-axis-restored`.
- Runtime code changed: no.
- Fresh calibration rerun: no; this is a contract reconciliation slice.
- Thresholds relaxed: no.
- `future_*` / `target_*` predictor ban remains active.
- Trade usable: no.

This audit reconciles two prior facts:

- `20260511T004210-source-backed-root-materialization` accepted `TransitionRecovery` at 95% using `reversal_persistence16 >= 1`.
- `20260511T010718-codex-root-taxonomy-v3-schema-input-audit` made `TransitionRecovery` optional until a downstream consumer contract requires it, while still listing it in the wider RootTaxonomyV3 evidence inventory.

Decision for the superseded RootTaxonomyV3 branch: `TransitionRecovery` is not a required release-gate root unless a downstream consumer explicitly activates it. It remains optional/overlay evidence. This does not change the active Board A MainRegimeV2 state, where `Bull`, `Bear`, `Sideways`, and direct-input-gated `Manipulation` remain missing.

## Next Action

Acquire higher-signal signed-direction/range inputs and aligned historical manipulation L2/L3/order-lifecycle data, then rerun unchanged RootTaxonomyV3 gates for the missing required roots.
