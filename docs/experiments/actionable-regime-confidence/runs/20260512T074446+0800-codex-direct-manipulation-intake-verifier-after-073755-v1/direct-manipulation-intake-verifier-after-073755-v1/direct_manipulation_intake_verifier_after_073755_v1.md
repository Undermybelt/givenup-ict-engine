# Direct Manipulation Intake Verifier After 073755 v1

Run id: `20260512T074446+0800-codex-direct-manipulation-intake-verifier-after-073755-v1`

Gate result: `direct_manipulation_intake_verifier_after_073755_v1=schema_ready_unscored_non_promoting`

## Scope

Read-only verifier run against `/tmp/ict-engine-direct-manipulation-row-intake` using the existing fail-closed direct Manipulation row-intake verifier. This does not mutate target roots, approve the R6 decision package, run split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Verifier exit code: `0`.
- Verifier status: `schema_ready_unscored`.
- Positive rows: `73`.
- Matched negative rows: `73`.
- Matched group count: `70`.
- Decision: schema-ready rows are non-promoting until split calibration, source/control approval or owner-export-root merge permission, canonical merge, and downstream rerun gates are satisfied.

## Decision

Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; direct verifier promoting false; split calibration false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T074446+0800-codex-direct-manipulation-intake-verifier-after-073755-v1/direct-manipulation-intake-verifier-after-073755-v1/direct_manipulation_intake_verifier_after_073755_v1.json`
- CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T074446+0800-codex-direct-manipulation-intake-verifier-after-073755-v1/direct-manipulation-intake-verifier-after-073755-v1/direct_manipulation_intake_verifier_after_073755_v1.csv`
- Command output: `docs/experiments/actionable-regime-confidence/runs/20260512T074446+0800-codex-direct-manipulation-intake-verifier-after-073755-v1/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T074446+0800-codex-direct-manipulation-intake-verifier-after-073755-v1/checks/direct_manipulation_intake_verifier_after_073755_v1_assertions.out`

## Next

Continue source/control acquisition only. Do not run split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion until explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export exists.
