# Source Root Stop Carry Long-Horizon Downstream v1

- Branch RC-SPA gate: `pass`
- Price roots passed: `4/4`; Manipulation component pass: `True`
- Downstream consumption: `blocked:downstream_branch_path_or_bbn_mapping_gap`
- Downstream promotable: `false`
- Primary blocker: `bbn_soft_evidence_unsupported_roots=Bear;ict_engine_structural_path_ranker_target_has_no_exact_board_b_branch_path_rows`

## Stage Results

- Pre-Bayes status exit: `0`; root BBN applied: `Bull,Sideways,Crisis`; unsupported roots: `Bear`
- BBN dry-run exit: `0`
- CatBoost available: `false`; apply scores exit: `0`; exact Board B target rows: `0`
- Execution-tree analyze exit: `0`; workflow execution-candidate exit: `0`

## Branch Path Preservation

The run-local bundles, strategy library, and CatBoost branch-score file preserve `regime_profit_branch_path`. The current ict-engine structural path-ranker target did not expose exact Board B branch-path rows, so runtime promotion remains blocked until that adapter surface can consume the same rooted paths.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/downstream-chain/source_root_stop_carry_longhorizon_downstream_v1.json`
- Root BBN probe summary: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/downstream-chain/root_bbn_probe_summary_v1.csv`
- Command outputs: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/downstream-chain/command-output`
- CatBoost metadata: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/downstream-chain/catboost/catboost_path_ranker_metadata_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/checks/source_root_stop_carry_longhorizon_downstream_v1_assertions.out`
