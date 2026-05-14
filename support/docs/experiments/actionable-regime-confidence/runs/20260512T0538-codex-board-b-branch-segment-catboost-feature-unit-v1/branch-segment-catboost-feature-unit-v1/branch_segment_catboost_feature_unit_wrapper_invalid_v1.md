# Branch Segment CatBoost Feature Unit Wrapper Invalid v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T0538-codex-board-b-branch-segment-catboost-feature-unit-v1`

This local wrapper is non-counting. The Cargo stdout reports the targeted unit test passed, but the surrounding zsh wrapper failed after Cargo returned because it attempted to assign to zsh's read-only `status` variable. As a result, this run root has no authoritative exit marker.

Use the separately registered terminal branch-segment feature rows for Board B accounting. Do not count this `0538` wrapper as promotion evidence, selected-data evidence, CatBoost/path-ranker maturity evidence, or `update_goal` authorization.

Gate:
- `invalid_wrapper:0538_branch_segment_catboost_feature_unit`
- `cargo_stdout_reports_pass=true`
- `authoritative_exit_marker_present=false`
- `count_as_board_b_evidence=false`
- `promotion_allowed=false`
- `update_goal=false`
