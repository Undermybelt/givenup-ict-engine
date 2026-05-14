# MainRegimeV2 Controlling Correction

Timestamp: 2026-05-11T01:36:12+0800

Purpose: re-apply the external correction as the controlling Board A contract.

Decision:
- Active root axis: `Bull`, `Bear`, `Sideways`, `Crisis`, direct-input-gated `Manipulation`, and residual `UnknownOrMixed`.
- `Manipulation` is either a fifth main class or an overlay state, but it cannot be accepted from OHLCV, liquidity, sweep-like, volume-ratio, or session subfactors.
- `BullExpansion`, `BearExpansion`, `Consolidation`, `CrisisStress`, `TransitionRecovery`, and similar labels are child/provenance evidence unless reissued through the active MainRegimeV2 root gate.
- The six existing accepted packets (`SessionLiquidityCoreViable`, `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, `ThinLiquidity`) are downgraded to `sub_regime_evidence_only`.

Current gate:
- `accepted_gate`: `partial_for_MainRegimeV2`
- Accepted active root: `Crisis`
- Missing active roots: `Bull`, `Bear`, `Sideways`, direct-input-gated `Manipulation`
- Thresholds relaxed: false
- Runtime code changed: false
- Trade usable: false

Concurrent-run readback:
- `20260511T012949-codex-tomac-gc-nq-main-regime-v2-root-gate` currently has only a temporary script artifact and no accepted root output recorded by this correction.
- That run does not change the controlling taxonomy until it emits calibration artifacts that pass the active root gate.

Next action:
- Acquire or decode calibration-grade direct L2/L3/MBO/order-lifecycle/event data across multiple instruments, periods, and contexts for `Manipulation`, and treat GC/NQ OHLCV only as candidate signed-direction/sideways input before rerunning unchanged MainRegimeV2 gates.
