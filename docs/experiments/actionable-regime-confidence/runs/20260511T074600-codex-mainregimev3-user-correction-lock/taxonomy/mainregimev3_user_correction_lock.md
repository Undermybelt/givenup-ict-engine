# MainRegimeV3 User-Correction Lock

Run id: `20260511T074600+0800-codex-mainregimev3-user-correction-lock`

This lock resolves concurrent V2 writebacks in favor of the latest user correction in this turn: prior listed regimes were too granular, and the main layer should include `BullExpansion`, `BearExpansion`, `Manipulation`, and `Consolidation`, with other large classes considered through research.

## Superseded Conflicting Writebacks

- `20260511T074500+0800-codex-taxonomy-conflict-resolution`
- `20260511T074243+0800-codex-mainregimev2-external-correction-repoint`
- `20260511T074000+0800-codex-mainregimev2-reassert-after-v3-drift`

These sections stay in the board as historical conflict records, but they are not the active cursor.

## Active Roots

- `BullExpansion`
- `BearExpansion`
- `SidewaysConsolidation`
- `CrisisStress`
- `Manipulation`

Residual: `UnknownOrMixed`.

## Guardrails

- Prior V2 `Bull` / `Bear` / `Sideways` / `Crisis` packets are provenance until remapped and re-audited.
- `Manipulation` is top-level, but it still requires direct event/order-flow/order-lifecycle/wash/spoof labels.
- OHLCV-only manipulation proxies stay fail-closed.
- This lock accepts zero new 95% roots.

Gate result: `blocked_mainregimev3_user_correction_locked_acceptance_not_rerun`.

Next action: rerun attachability/full-coverage disposition against MainRegimeV3 roots and keep missing source-label cells blocked.
