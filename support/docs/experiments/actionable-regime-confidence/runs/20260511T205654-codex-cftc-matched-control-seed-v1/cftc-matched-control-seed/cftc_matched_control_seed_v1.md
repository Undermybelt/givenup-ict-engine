# CFTC Matched Control Seed v1

Decision: `cftc_matched_control_seed_v1=direct_intake_schema_ready_unscored_confidence_gate_false`.

Result:
- Positive rows present: `2`.
- Matched control rows materialized under `/tmp`: `2`.
- Direct intake verifier status: `schema_ready_unscored`; return code `0`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

Interpretation:
- R6 is no longer blocked by the matched-control filename alone when this `/tmp` root is present.
- The control rows are same-report CFTC genuine-order seeds, not a broad heldout normal-market sample.
- This is schema-ready/unscored evidence only; Wilson95 calibration and broader direct species coverage still remain blocked.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T205654-codex-cftc-matched-control-seed-v1/cftc-matched-control-seed/cftc_matched_control_seed_v1.json`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T205654-codex-cftc-matched-control-seed-v1/cftc-matched-control-seed/direct_manipulation_row_intake_verifier.stdout.txt`
- Verifier stderr: `docs/experiments/actionable-regime-confidence/runs/20260511T205654-codex-cftc-matched-control-seed-v1/cftc-matched-control-seed/direct_manipulation_row_intake_verifier.stderr.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T205654-codex-cftc-matched-control-seed-v1/checks/cftc_matched_control_seed_v1_assertions.out`
