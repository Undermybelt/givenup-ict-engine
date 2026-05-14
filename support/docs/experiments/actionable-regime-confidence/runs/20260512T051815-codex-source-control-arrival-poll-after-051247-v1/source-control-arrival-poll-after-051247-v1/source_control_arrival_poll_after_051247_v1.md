# Source Control Arrival Poll After 051247 v1

Run id: `20260512T051815-codex-source-control-arrival-poll-after-051247-v1`

Gate result: `source_control_arrival_poll_after_051247_v1=no_required_unlock_root_no_control_approval_no_promotion`

## Scope

This poll resumes after the terminal non-promoting `050609` model screen, the `051145` read-only runtime-chain packet, the `051153` provider/source-root readbacks, and the `051247` official owner-data route refresh. It checks whether the required source/control unlock arrived locally before any direct-verifier or downstream promotion rerun.

## Readback

- Current board hash before the poll: `ae2ccacdb08f43ed38dce0d0658185a314e4a7cc729425c7f680f72d00fc5fd3`.
- Required R6 owner-export root `/tmp/ict-engine-board-a-r6-owner-export-v1`: absent.
- Required R3 native sub-hour source-label root `/tmp/ict-engine-native-subhour-source-label-intake`: absent.
- Required R5 source-panel recency-extension root `/tmp/ict-engine-source-panel-recency-extension`: absent.
- Existing equivalence sidecar `/tmp/ict-engine-source-label-equivalence-intake`: present, but not one of the required unlock roots.
- Known private-tmp R6 sidecars remain discoverable, but they are not the approved owner-export root and do not carry explicit same-event/FLIP control approval.
- The Tomac/Databento GC local archive is `GLBX.MDP3` `ohlcv-1m` CSV data, not MBO/depth/order-lifecycle rows and not source-owned `MainRegimeV2` labels.

## Decision

- Accepted rows added: `0`.
- Accepted regime-confidence labels: `0`.
- Source/control evidence acquired: `false`.
- Explicit control approval: `false`.
- Canonical merge: `false`.
- Downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree rerun: `false`.
- Strict full objective: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Boundary

This packet does not copy sidecars into `/tmp/ict-engine-board-a-r6-owner-export-v1`, does not approve same-exhibit `FLIP` controls, does not unpack or mutate Downloads data, does not run direct verifier/calibration on non-target roots, and does not run downstream promotion.

## Next

Preserve the Current Cursor next action: send or otherwise satisfy the CME and Cboe/CFE owner-export requests, preserving ticket/export/license identifiers in provenance; alternatively obtain explicit `FLIP`-as-control approval. Only then copy verifier-native files into the approved target root under a shared lock and rerun direct verifier, split calibration, provider/AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback.
