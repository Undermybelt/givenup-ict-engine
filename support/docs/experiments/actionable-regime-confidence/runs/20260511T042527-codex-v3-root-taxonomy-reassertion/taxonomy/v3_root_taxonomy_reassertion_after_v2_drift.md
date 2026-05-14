# MainRegimeV3SourceBacked Reassertion After V2 Drift

Run id: `20260511T042527+0800-codex-v3-root-taxonomy-reassertion`

Purpose: repair the later `20260511T042400+0800-codex-main-regime-v2-reassert-after-v3-drift` writeback, which conflicted with the user's latest correction that `BullExpansion`, `BearExpansion`, `Manipulation`, and `SidewaysConsolidation` belong on the main regime layer.

## Current Accounting

| Root | Status |
|---|---|
| `BullExpansion` | accepted_95 via `20260511T035045+0800-codex-kaggle-bull-coverage-buffer-gate` |
| `BearExpansion` | accepted_95 via `20260511T041923+0800-codex-yahoo-sourcebacked-parent-root-gate`; source `Bear` crosswalked to negative expansion after source-backed drawdown and return-ratio rule |
| `SidewaysConsolidation` | accepted_95 via `20260511T041213+0800-codex-sideways-consolidation-legacy-reissue` and reinforced by `20260511T041923+0800-codex-yahoo-sourcebacked-parent-root-gate` source `Sideways` rule |
| `CrisisCrash` | accepted_95 via prior `CrisisStress` / `CrisisCrash` evidence |
| `Manipulation` | missing_required_inputs / below-95 direct gates |
| `UnknownOrMixed` | residual_only |

The `20260511T042400` SystemsLab HGB direct manipulation gate is retained as negative evidence for `Manipulation`: calibration/test Wilson95 `0.863904` / `0.832241`, test coverage `0.000674`, no threshold relaxation, runtime code changed false, trade usable false.

## Decision

- Active root axis is `MainRegimeV3SourceBacked`.
- Main roots/root-or-overlay: `BullExpansion`, `BearExpansion`, `SidewaysConsolidation`, `CrisisCrash`, direct-input-gated `Manipulation`, residual `UnknownOrMixed`.
- `Bull`, `Bear`, `Sideways`, and `Crisis` may be source labels, but they do not demote the active root names.
- MainRegimeV2 parent-only writebacks are historical provenance only after this correction.
- Missing active root remains `Manipulation`.

Gate result: `v3_root_taxonomy_reasserted_after_v2_drift_with_bear_crosswalk`.

Runtime code changed: false. Thresholds relaxed: false. Fresh calibration rerun by this reassertion: false. Trade usable: false.
