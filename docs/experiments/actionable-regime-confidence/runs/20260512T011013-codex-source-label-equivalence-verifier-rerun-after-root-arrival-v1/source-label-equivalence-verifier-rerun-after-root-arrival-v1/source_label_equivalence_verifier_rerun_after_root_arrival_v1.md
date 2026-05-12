# Source-Label Equivalence Verifier Rerun After Root Arrival v1

- Run id: `20260512T011013-codex-source-label-equivalence-verifier-rerun-after-root-arrival-v1`.
- Intake root: `/tmp/ict-engine-source-label-equivalence-intake`.
- Verifier: `docs/experiments/actionable-regime-confidence/runs/20260511T182922-codex-source-label-equivalence-intake-verifier-v1/equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py`.
- Gate result: `source_label_equivalence_verifier_rerun_after_root_arrival_v1=schema_ready_unscored_no_confidence_acceptance`.
- Verifier exit code: `0`.
- Verifier status: `schema_ready_unscored`.
- Verified rows: `248440`.
- Package counts: `price_root_equivalence_us_index_futures=248440`.
- Rows SHA-256: `337a2b26fb5c82a27be3548404532e2577017cbb7c26e46683628cafeaed0f25`.
- Provenance SHA-256: `a373b77b4a34041f15004faaccc3f1d629c9c05b946894db0ae741186853a56b`.

## Evidence

- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T011013-codex-source-label-equivalence-verifier-rerun-after-root-arrival-v1/command-output/source_label_equivalence_intake_verifier_stdout.json`
- Verifier stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T011013-codex-source-label-equivalence-verifier-rerun-after-root-arrival-v1/command-output/source_label_equivalence_intake_verifier_stderr.txt`
- Verifier exit code: `docs/experiments/actionable-regime-confidence/runs/20260512T011013-codex-source-label-equivalence-verifier-rerun-after-root-arrival-v1/command-output/source_label_equivalence_intake_verifier_exit_code.txt`
- Summary JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T011013-codex-source-label-equivalence-verifier-rerun-after-root-arrival-v1/source-label-equivalence-verifier-rerun-after-root-arrival-v1/source_label_equivalence_verifier_rerun_after_root_arrival_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T011013-codex-source-label-equivalence-verifier-rerun-after-root-arrival-v1/checks/source_label_equivalence_verifier_rerun_after_root_arrival_v1_assertions.out`

## Boundary

This is schema evidence only. It does not compute calibrated confidence, does not accept any MainRegimeV2 root, does not satisfy R3 native sub-hour validation, does not satisfy R5 recency extension, does not satisfy R6 direct Manipulation controls, and does not allow provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree promotion rerun.

## Next

Run the unchanged chronological and heldout-market/timeframe confidence gates for this source-label equivalence root, while preserving the active R6 owner-export blocker and keeping downstream promotion fail-closed until all required source/control roots exist.
