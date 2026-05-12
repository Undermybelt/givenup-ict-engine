# AIMM Direct Manipulation Candidate Audit

Run ID: `20260511T091339+0800-codex-aimm-direct-manipulation-candidate-audit`

Board: Board A, `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`

## Result

- Candidate: AIMM public repositories and arXiv-linked supplementary materials.
- Accepted direct `Manipulation` label sources: `0`.
- Accepted label rows materialized: `0`.
- Accepted MainRegimeV2 root-label slots: `0`.
- Gate result: `blocked_aimm_public_materials_no_ground_truth_labels`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Source Checks

| Source | URL | Decision | Evidence |
|---|---|---|---|
| `sneela/aimm-framework` | `https://github.com/sneela/aimm-framework` | `rejected_demo_framework_no_ground_truth_labels` | Public tree exposes illustrative framework code plus `data/sample_market_data.csv`; no positive/negative manipulation label rows were found. |
| `sneela/aimm-supplementary-material` | `https://github.com/sneela/aimm-supplementary-material` | `rejected_supplement_excludes_labels_and_ground_truth` | Public supplementary README states that labels, ground truth, real market data, trading signals, feature engineering, and model weights are not included. |
| AIMM arXiv page | `https://arxiv.org/abs/2512.16103` | `methodology_provenance_only` | Paper/supplementary metadata supports methodology provenance, but public repos do not materialize replayable labeled market-manipulation rows. |

## Next Action

Do not count AIMM public materials as accepted `Manipulation` evidence unless the authors publish ground-truth positive/negative rows; continue with authenticated Dune export or another materialized direct-label dataset.
