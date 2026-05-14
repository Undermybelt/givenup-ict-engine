# Main-vs-Subclass Reassertion

Run id: `20260511T042004+0800-codex-main-vs-subclass-reassertion`

Scope: taxonomy correction only. No fresh market calibration was run, no runtime code changed, and no threshold was relaxed.

## Active Parent Axis

Board A completion accounting uses MainRegimeV2 parent roots:

- `Bull`
- `Bear`
- `Sideways`
- `Crisis`
- direct-input-gated `Manipulation`
- residual `UnknownOrMixed`

## Subclass / Provenance Boundary

The following labels are not active root completion targets unless reissued through an active parent-root gate:

- `BullExpansion`
- `BearExpansion`
- `SidewaysConsolidation`
- `CrisisCrash` / `CrisisStress`
- `RangeConsolidation`
- liquidity/session labels
- direct L2/order-book signatures

## Accounting Result

Accepted active roots after this correction:

- `Bull`
- `Crisis`

Still missing active roots:

- `Bear`
- `Sideways`
- direct-input-gated `Manipulation`

The `20260511T041213` `SidewaysConsolidation` reissue is retained only as child/provenance evidence. It does not complete parent `Sideways`.

Gate result: `taxonomy_reassertion_no_new_roots`.

