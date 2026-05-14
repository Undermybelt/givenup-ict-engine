# NIFTY Source Label Equivalence Intake v1

- Decision: `nifty_source_label_equivalence_intake_v1=partial_schema_ready_no_full_objective`.
- Shared intake write: `created_required_files`.
- Verifier status: `schema_ready_unscored`.
- Row count: `3435`; labels: `{'Bull': 1213, 'Crisis': 991, 'Sideways': 1231}`.
- Date range: `2012-02-02` to `2026-03-20`.
- Accepted confidence rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Interpretation

The source-owned NIFTY daily regime dataset has owner-described labels that can be mapped into a partial MainRegimeV2 equivalence package for `Bull`, `Sideways`, and `Crisis`.
This does not create a Bear row set, does not provide native sub-hour labels, and does not close the strict Board A objective.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212819-codex-nifty-source-label-equivalence-intake-v1/nifty-source-label-equivalence-intake/nifty_source_label_equivalence_intake_v1.json`
- Report: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212819-codex-nifty-source-label-equivalence-intake-v1/nifty-source-label-equivalence-intake/nifty_source_label_equivalence_intake_v1.md`
- Counts CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212819-codex-nifty-source-label-equivalence-intake-v1/nifty-source-label-equivalence-intake/nifty_source_label_equivalence_counts_v1.csv`
- Staging intake root: `/tmp/ict-engine-nifty-source-label-equivalence-intake-v1`
- Shared intake root: `/tmp/ict-engine-source-label-equivalence-intake`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T212819-codex-nifty-source-label-equivalence-intake-v1/command-output/source_label_equivalence_verifier.stdout.txt`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212819-codex-nifty-source-label-equivalence-intake-v1/checks/nifty_source_label_equivalence_intake_v1_assertions.out`
