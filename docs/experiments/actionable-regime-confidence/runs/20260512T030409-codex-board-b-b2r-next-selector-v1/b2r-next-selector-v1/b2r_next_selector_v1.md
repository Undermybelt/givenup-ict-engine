# Board B B2R Next Selector v1

Run id: `20260512T030409+0800-codex-board-b-b2r-next-selector-v1`

Decision: `do_not_start_downstream_or_duplicate_heavy_run`.

Inputs:
- `024509` / `CorrelationShockAbsorptionV1`: 47,843 variant rows, 13,275 selected rows, score `75.88863517875106`, gate `fail:required_root_branch_hard_gates_failed`.
- `024354` / `CryptoOptionsBreadthRootV1`: 859 variant rows, 492 selected rows, score `82.34627989071636`, gate `fail:required_root_branch_hard_gates_failed`.
- `205047` / `ManipulationStopTakeProfitGridV2`: `pass:direct_manipulation_stop_tp_candidate`, 771,495 branch rows, best `short_tp120_sl060_h72`.

Failure matrix:
- `Bull`: `support_present_but_unstable`. Do not add generic Bull rows. Require fold-stable positive net edge after costs and lower PBO/overfit.
- `Bear`: `thin_and_negative`. Use a Bear-dedicated short/defensive action surface with explicit root alignment and enough chronological folds.
- `Sideways`: `rows_present_edge_missing`. Use a range-carry or fade surface that abstains in trend contexts and proves positive LCB by fold.
- `Crisis`: `coverage_or_edge_weak`. Source older crisis windows or stress-specific provider panels, then score only if Crisis has multi-fold positive edge.
- `Manipulation(scoped)`: `component_available_not_combined_in_latest_packets`. Combine 205047 only as scoped component evidence after all price roots pass; do not count component readiness as price-root promotion.

Recommended next probe:
- `BearSidewaysCrisisAbstainCarryRepairV1`, only after the active root-panel jobs finish and the board has been re-read.
- Preserve `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`.
- Do not rerun downstream until all price roots pass unchanged RC-SPA and the `205047` Manipulation component remains component-only.

Concurrency guard:
- No heavy probe was started by this selector.
- Current cursor remains `025702` / `CryptoOptionsBreadthRootV1` fail-closed unless a newer board row supersedes it.
