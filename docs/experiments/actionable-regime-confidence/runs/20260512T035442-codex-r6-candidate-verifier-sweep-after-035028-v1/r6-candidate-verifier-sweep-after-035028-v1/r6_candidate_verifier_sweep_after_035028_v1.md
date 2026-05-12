# R6 Candidate Verifier Sweep After 035028 v1

Generated: 2026-05-11T19:55:30Z

Gate result: `r6_candidate_verifier_sweep_after_035028_v1=candidate_bundles_schema_ready_unscored_no_auto_promotion`

## Scope

This packet runs the existing fail-closed direct-manipulation row intake verifier against complete R6-shaped candidate bundles found by the `035028` inbox repoll. It does not copy files into the required owner-export root, mutate source roots, accept labels, approve `FLIP` rows, run canonical merge, rerun downstream promotion, or call `update_goal`.

## Inputs

- Repoll source: `docs/experiments/actionable-regime-confidence/runs/20260512T035028-codex-source-control-inbox-repoll-after-034813-v1`
- Verifier: `docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py`
- Board hash observed before summary artifact: `471f921458f4a8641f5d83d54ca3d38c821debda46a0d0e9304f4096c083e5ed`

## Verifier Results

| Candidate root | Exit | Status | Positive rows | Matched negative rows | Matched groups |
|---|---:|---|---:|---:|---:|
| `/tmp/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1.staging` | 0 | schema_ready_unscored | 77 | 77 | 74 |
| `/tmp/ict-engine-direct-manipulation-row-intake` | 0 | schema_ready_unscored | 73 | 73 | 70 |
| `/tmp/ict-engine-r6-direct-intake-reconstruction-v55/intake` | 0 | schema_ready_unscored | 73 | 73 | 70 |
| `/tmp/ict-engine-r6-direct-intake-v56-clean-readback/intake` | 0 | schema_ready_unscored | 73 | 73 | 70 |

## Decision

- Verifier-native bundle candidates found: `4`.
- Schema-ready candidate roots: `4`.
- Chronological Wilson95 calibration run here: `false`.
- Heldout symbol/venue calibration run here: `false`.
- Required owner-export root complete: `false`.
- Explicit approval present: `false`.
- `FLIP` controls accepted under current contract: `false`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Next

The next safe action is to run chronological and heldout-symbol/venue Wilson95 calibration against the schema-ready candidate bundles in an isolated artifact root. Only after that, and only with explicit approval or a source-owned owner-export root handoff, should canonical merge and the downstream promotion chain be attempted.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T035442-codex-r6-candidate-verifier-sweep-after-035028-v1/r6-candidate-verifier-sweep-after-035028-v1/r6_candidate_verifier_sweep_after_035028_v1.json`
- CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T035442-codex-r6-candidate-verifier-sweep-after-035028-v1/r6-candidate-verifier-sweep-after-035028-v1/r6_candidate_verifier_summary_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T035442-codex-r6-candidate-verifier-sweep-after-035028-v1/checks/r6_candidate_verifier_sweep_after_035028_v1_assertions.out`
- Command outputs: `docs/experiments/actionable-regime-confidence/runs/20260512T035442-codex-r6-candidate-verifier-sweep-after-035028-v1/command-output/`
