# 014426 Reference Drift Correction v1

Run id: `20260512T014726-codex-014426-reference-drift-correction-v1`
Gate result: `014426_reference_drift_correction_v1=referenced_root_absent_treat_as_stale_no_promotion`
Board hash before artifact: `81267de5f4bc420f89210457bd905df1385ca9adb649e21703d6a3b856e84ffa`

Readback:
- `docs/experiments/actionable-regime-confidence/runs/20260512T014426-codex-current-objective-completion-audit-after-014229-v1`: absent at final verification.
- `docs/experiments/actionable-regime-confidence/runs/20260512T014432-codex-board-b-220646-structural-candidate-handoff-readback-v1`: present, but only contains a Board B cargo-build command capture blocked on an artifact-directory file lock.
- `/tmp/ict-engine-board-a-r6-owner-export-v1`: absent.
- `/tmp/ict-engine-native-subhour-source-label-intake`: absent.
- `/tmp/ict-engine-source-panel-recency-extension`: absent.
- `/tmp/ict-engine-source-label-equivalence-intake`: present.

Correction:
- Treat board references to `014426` as stale/non-evidence unless the full local run root is restored with report, JSON, checklist/source-root CSV, assertions, and script.
- This correction does not change the Current Cursor, accept labels, acquire R6 controls, approve `FLIP` rows, mutate intake roots, rerun downstream promotion, or call `update_goal`.

Result:
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree rerun allowed: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

Next:
- Preserve the active R6 cursor. Continue from source-owned R6 normal controls or explicit `FLIP` approval plus canonical merge; keep R3/R5/cross-timeframe source inputs fail-closed until exact source-owned rows with provenance arrive.
