# Board B 220646 Target Surface Readback v1

- Source candidate: `20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-v1` / `SourceRootStopCarryLongHorizonV1`.
- Branch RC-SPA gate: `pass`; stable score `85.74074074074075`.
- Price roots passed: `4/4`; Manipulation component pass: `True`.
- Provider readback exit: `0`; Auto-Quant import/prior exits: `0` / `0`.
- BBN applied roots: `Bull,Sideways,Crisis`; unsupported roots: `Bear`.
- Real CatBoost trained: `True`; training rows `12329`; branch-score rows `4`.
- ict-engine structural target rows: `3`; exact Board B branch-path target rows: `0`.
- Execution-tree workflow exits: analyze `0`, execution-candidate `0`.
- Downstream promotable: `false`.
- Primary blocker: `one_or_more_downstream_commands_failed;bbn_soft_evidence_unsupported_roots=Bear;ict_engine_structural_path_ranker_target_has_no_exact_board_b_branch_path_rows`.

## Evidence

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T222451-codex-board-b-220646-target-surface-readback-v1/target-surface-readback/board_b_220646_target_surface_readback_v1.json`
- Root BBN probe summary: `docs/experiments/actionable-regime-confidence/runs/20260511T222451-codex-board-b-220646-target-surface-readback-v1/target-surface-readback/root_bbn_probe_summary_v1.csv`
- CatBoost metadata: `docs/experiments/actionable-regime-confidence/runs/20260511T222451-codex-board-b-220646-target-surface-readback-v1/catboost/catboost_path_ranker_metadata_v1.json`
- CatBoost branch scores: `docs/experiments/actionable-regime-confidence/runs/20260511T222451-codex-board-b-220646-target-surface-readback-v1/catboost/branch_path_scores_v1.csv`
- ICT Engine scores file: `docs/experiments/actionable-regime-confidence/runs/20260511T222451-codex-board-b-220646-target-surface-readback-v1/catboost/path_ranker_scores_for_ict_engine_v1.csv`
- Command outputs: `docs/experiments/actionable-regime-confidence/runs/20260511T222451-codex-board-b-220646-target-surface-readback-v1/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T222451-codex-board-b-220646-target-surface-readback-v1/checks/board_b_220646_target_surface_readback_v1_assertions.out`

## Interpretation

The run trained a real CatBoost branch scorer in an isolated uv/offline environment and pushed scores through ict-engine structural path-ranking/runtime commands. The exact Board B `regime_profit_branch_path` rows still do not appear in ict-engine's exported structural path-ranking target, so the current runtime can consume mapped structural scores but cannot yet promote this candidate as a closed-loop branch-path-preserving profitability packet.
