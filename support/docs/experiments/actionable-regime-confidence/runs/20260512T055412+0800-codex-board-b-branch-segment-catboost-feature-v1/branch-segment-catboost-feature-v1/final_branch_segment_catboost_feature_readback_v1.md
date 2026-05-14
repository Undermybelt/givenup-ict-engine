# Final Branch Segment CatBoost Feature Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T055412+0800-codex-board-b-branch-segment-catboost-feature-v1`

Purpose: terminal code-contract evidence that rooted regime branch segments are first-class CatBoost/path-ranker target fields and direct-model categorical features.

Implemented surface:
- `StructuralPathRankingTargetRow` carries `regime_profit_branch_path`, `parent_regime_root`, `main_regime`, `sub_regime`, `sub_sub_regime_or_profit_factor`, and `profit_factor`.
- CSV export includes those columns.
- `structural_path_ranking_trainer_manifest().feature_columns` includes those fields.
- Direct-model categorical scoring can read the branch segment fields.
- Structural target export populates the fields from exact rooted paths shaped as `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`.

Terminal evidence:
- `target_export_surfaces_branch_segments_as_catboost_features.exit`: `0`
- `target_export_surfaces_group_final.exit`: `0`
- `branch_segment_fields_direct_model_final.exit`: `0`
- `rustfmt_check_final.exit`: `0`

Important correction:
- `rustfmt_check_after_direct_model.exit` is `1`; the later `rustfmt_check_final.exit` is the terminal formatting evidence and is `0`.

Gate:
- This is code-contract evidence only.
- It does not provide user-selected historical data.
- It does not run selected-data Auto-Quant training.
- It does not create nonzero mature rooted selected observations.
- It does not prove production CatBoost/path-ranker validation or execution-tree admissibility.
- Board B remains blocked on `user_selected_historical_data_missing`.
