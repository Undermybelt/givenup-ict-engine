# Non-R6 Source Intake Current Readback v2

Decision: `non_r6_source_intake_current_readback_v2=roots_absent_r5_upstream_unchanged_no_rows_acquired`.

This is a supplemental readback after the active R6 cursor moved to the V70 external-control source scan. It does not edit the Current Cursor, approve `FLIP` controls, mutate any intake root, relax thresholds, or rerun downstream gates.

Result:
- Non-R6 intake roots ready: `0/3`.
- Required files present: `0/6`; exact required-file hits under bounded `/tmp`, `/private/tmp`, and `Downloads` search: `0`.
- Source-label equivalence verifier: exit `2`, status `blocked`, reason `missing_required_files`.
- R5 source-panel recency verifier: exit `2`, status `blocked`, reason `missing_required_files`.
- R3 native-subhour root: absent.
- R5 Kaggle source listing still contains the February source package files only; no post-`2026-01-30` extension file was found.
- Local stock-market-regimes source panel max date remains `2026-01-30`; post-cutoff rows: `0`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Canonical merge allowed: `false`; downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: `false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T004822-codex-non-r6-source-intake-current-readback-v2/non-r6-source-intake-current-readback/non_r6_source_intake_current_readback_v2.json`
- Intake roots CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T004822-codex-non-r6-source-intake-current-readback-v2/non-r6-source-intake-current-readback/non_r6_source_intake_roots_v2.csv`
- R5 upstream listing CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T004822-codex-non-r6-source-intake-current-readback-v2/non-r6-source-intake-current-readback/r5_upstream_current_listing_v2.csv`
- Command output: `docs/experiments/actionable-regime-confidence/runs/20260512T004822-codex-non-r6-source-intake-current-readback-v2/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T004822-codex-non-r6-source-intake-current-readback-v2/checks/non_r6_source_intake_current_readback_v2_assertions.out`

Next:
- Preserve the active R6 next action: supply source-owned normal controls for the `17` Oystacher cells through the mapped CME/Cboe source-owner routes, or explicitly approve the same-exhibit `FLIP`-as-control exception.
- For non-R6 hardening, populate the exact R2/R3/R5 intake roots with source-owned or owner-approved rows and provenance before rerunning unchanged verifiers.
