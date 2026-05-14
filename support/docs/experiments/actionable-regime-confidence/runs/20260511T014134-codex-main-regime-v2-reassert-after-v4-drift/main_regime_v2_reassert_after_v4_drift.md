# MainRegimeV2 Reassertion After V4 Drift

Timestamp: 2026-05-11T01:41:34+0800

Purpose: reverse a concurrent Board A drift that promoted `RootTaxonomyV4` over the user-corrected MainRegimeV2 axis.

Decision:
- Active root axis remains MainRegimeV2: `Bull`, `Bear`, `Sideways`, `Crisis`, direct-input-gated `Manipulation`, and residual `UnknownOrMixed`.
- `RootTaxonomyV4`, `BullExpansion`, `BearExpansion`, `Consolidation`, `CrisisStress`, and `TransitionRecovery` are provenance/child evidence only unless reissued through the active MainRegimeV2 root-class gate.
- The six accepted packets remain `sub_regime_evidence_only`.
- `Manipulation` remains fail-closed without calibration-grade direct tick/order-flow/L2/L3/MBO/order-lifecycle/event/social/on-chain evidence.

Tomac GC/NQ root-gate readback:
- Run: `docs/experiments/actionable-regime-confidence/runs/20260511T012949-codex-tomac-gc-nq-main-regime-v2-root-gate`
- Newly accepted 95 roots from GC/NQ OHLCV: none.
- Prior accepted root preserved: `Crisis`.
- Missing 95 roots remain: `Bull`, `Bear`, `Sideways`, direct-input-gated `Manipulation`.
- Gate: `partial_for_MainRegimeV2_Crisis_only_prior_evidence_preserved`.

Current gate:
- `accepted_gate`: `partial_for_MainRegimeV2`
- Thresholds relaxed: false
- Runtime code changed: false
- Trade usable: false
