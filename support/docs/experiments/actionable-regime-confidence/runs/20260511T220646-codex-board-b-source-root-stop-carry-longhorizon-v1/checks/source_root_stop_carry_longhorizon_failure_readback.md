# Source Root Stop/Carry Long Horizon Failure Readback

Run id: `20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-v1`.

## Decision

- Process exit: `1`
- Scored artifacts emitted: `false`
- Branch RC-SPA report exists: `false`
- Variant rows emitted: `0`
- Selected rows emitted: `0`
- Gate result: `fail:wrapper_expected_missing_patch_module`
- Downstream consumption: `not_started:no_rc_spa_report`

## Error

The wrapper failed before scoring:

`AttributeError: module 'source_root_stop_carry_v1_base' has no attribute 'patch_module'`

The imported `220019` source script is now an artifact verifier, not the original scoring implementation that exposed the expected wrapper hook. This run is operational failure evidence only.

## Next

Do not use this run as profitability evidence. A long-horizon retry must be self-contained or import an actual scorer implementation, then rerun the unchanged Bull/Bear/Sideways/Crisis plus scoped `205047` Manipulation gate.
