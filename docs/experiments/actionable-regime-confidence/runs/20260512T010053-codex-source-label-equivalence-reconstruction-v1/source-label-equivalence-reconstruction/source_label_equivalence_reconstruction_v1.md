# Source Label Equivalence Reconstruction v1

- Decision: `source_label_equivalence_reconstruction_v1=reconstructed_schema_ready_source_confidence_no_acceptance`.
- Shared root write: `created_required_files`.
- Rows reconstructed: `248440`; labels: `{'Bear': 54939, 'Bull': 104979, 'Crisis': 30623, 'Sideways': 57899}`.
- Source owners: `{'ahaanverma00': 3435, 'source-owned-stock-market-regimes-2000-2026': 245005}`.
- Market families: `{'india_equity_index': 3435, 'us_index': 26236, 'us_single_stock': 218769}`.
- Split counts: `{'calibration': 148976, 'heldout_market': 26236, 'heldout_time': 45384, 'test': 27844}`.
- Verifier status: `schema_ready_unscored`; return code `0`.
- Accepted source-confidence labels: `[]`.
- Prior row-count match: `True`; prior split-count match: `True`; prior rows hash match: `False`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; R6 canonical intake mutated: `false`; owner-export root mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Boundary

This reconstructs a missing `/tmp` source-label equivalence intake from the local stock-regime source file and a fresh Kaggle NIFTY public pull. It is schema repair only. The confidence gate remains fail-closed, and this does not authorize R6 canonical merge or downstream promotion.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T010053-codex-source-label-equivalence-reconstruction-v1/source-label-equivalence-reconstruction/source_label_equivalence_reconstruction_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260512T010053-codex-source-label-equivalence-reconstruction-v1/source-label-equivalence-reconstruction/source_label_equivalence_reconstruction_v1.md`
- Label split CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T010053-codex-source-label-equivalence-reconstruction-v1/source-label-equivalence-reconstruction/source_label_equivalence_reconstruction_label_split_v1.csv`
- Source owner CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T010053-codex-source-label-equivalence-reconstruction-v1/source-label-equivalence-reconstruction/source_label_equivalence_reconstruction_owner_v1.csv`
- Market family CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T010053-codex-source-label-equivalence-reconstruction-v1/source-label-equivalence-reconstruction/source_label_equivalence_reconstruction_market_v1.csv`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T010053-codex-source-label-equivalence-reconstruction-v1/source-label-equivalence-reconstruction/source_label_equivalence_reconstruction_gates_v1.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T010053-codex-source-label-equivalence-reconstruction-v1/command-output/source_label_equivalence_verifier.stdout.txt`
- Kaggle metadata stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T010053-codex-source-label-equivalence-reconstruction-v1/command-output/kaggle_nifty_metadata.stdout.txt`
- Kaggle download stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T010053-codex-source-label-equivalence-reconstruction-v1/command-output/kaggle_nifty_download.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T010053-codex-source-label-equivalence-reconstruction-v1/checks/source_label_equivalence_reconstruction_v1_assertions.out`
- Reproduction script: `docs/experiments/actionable-regime-confidence/runs/20260512T010053-codex-source-label-equivalence-reconstruction-v1/scripts/source_label_equivalence_reconstruction_v1.py`
