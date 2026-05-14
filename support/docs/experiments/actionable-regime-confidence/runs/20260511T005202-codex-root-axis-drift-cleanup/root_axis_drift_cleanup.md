# Root Axis Drift Cleanup

Loop id: `20260511T005202+0800-codex-root-axis-drift-cleanup`

Purpose: apply the user correction that `BullExpansion`, `BearExpansion`, `Consolidation`, `CrisisStress`, and `TransitionRecovery` read as child or signature labels, not active MainRegimeV2 root classes.

Decision:
- Active MainRegimeV2 root axis: `Bull`, `Bear`, `Sideways`, `Crisis`, direct-input-gated `Manipulation`, and residual `UnknownOrMixed`.
- Existing accepted packets for `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, `SessionLiquidityCoreViable`, and `ThinLiquidity` remain sub-regime or guardrail evidence only.
- Source-backed labels such as `BullExpansion`, `BearExpansion`, `Consolidation`, `CrisisStress`, and `TransitionRecovery` remain feature-direction provenance only unless the user explicitly changes the root taxonomy again.
- The unexecuted `20260511T004831-source-backed-root-classifier-probe` branch is not a valid completion attempt because it evaluates the wrong taxonomy layer.

Current evidence state:
- `Crisis` is the only current MainRegimeV2 root with accepted 95% evidence from the broader corrected root probe.
- `Bull`, `Bear`, and `Sideways` remain below 95% held-out Wilson gates in the corrected root runs.
- `Manipulation` remains `missing_required_inputs`; OHLCV proxies are not acceptable proof.
- Overall Board A state remains `blocked` / `partial_for_MainRegimeV2`, not complete.

Next action: obtain materially new signed-direction/sideways evidence for `Bull`, `Bear`, and `Sideways`, and direct tick/order-flow/L2/order-lifecycle or event/social evidence for `Manipulation`, before rerunning unchanged current-root gates.
