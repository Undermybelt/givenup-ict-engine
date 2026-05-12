# Board B Branch Path Parity Audit v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T044138+0800-codex-board-b-branch-path-parity-audit-v1`

Scope: read-only audit of the existing `034002/downstream-combined-v1` evidence for `NQRootAdaptiveCostCrisisRepairV3`. This does not edit the Board B Current Cursor, does not select historical data, does not run new Auto-Quant training, does not promote any candidate, and does not call `update_goal`.

## Audited Source

- Source run: `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3`
- Downstream state: `downstream-combined-v1/state_combined_v1`
- Strategy library: `downstream-v2/strategy_library_nq_cost_crisis_repair_v3_manifest_1_0.json`
- Real trade wire: `downstream-v2/nq_cost_crisis_repair_real_trades_v3_wire_fixed.jsonl`
- Pre-Bayes policy: `downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/pre_bayes_policy_history.json`
- BBN: `downstream-combined-v1/state_combined_v1/auto-quant/B2R_NQ_COST_CRISIS_REPAIR_032157/bbn_network.json`
- CatBoost target: `downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/policy_training/structural_path_ranking_target.csv`
- CatBoost scores: `downstream-combined-v1/catboost/scores/current_scores.csv`
- Execution tree: `downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/execution_tree_trace.json`
- Workflow snapshot: `downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/workflow_snapshot.json`

## Result

Gate: `branch_path_parity_audit_v1=partial_path_preservation_no_promotion`.

The existing chain proves that some downstream artifacts can carry rooted branch paths, but it does not satisfy the user requirement that Auto-Quant profitability factors and every downstream layer preserve the same full branch path as first-class evidence.

Layer readback:

| Layer | Full rooted branch path preserved? | Readback |
|---|---:|---|
| Auto-Quant strategy manifest | partial | Four price-root paths are present: Bull, Bear, Sideways, Crisis. Scoped Manipulation is not in this strategy manifest. |
| Auto-Quant real trade wire | no | `15415` trade rows exist and carry root-level `regime_at_entry` plus `factors_used.category=regime_profit_branch_path`, but no full `main -> child -> leaf -> factor` string exists in the trade JSONL. Root counts: Bull `10663`, Sideways `3406`, Bear `762`, Crisis `584`. |
| Pre-Bayes/filter | no | `pre_bayes_policy_history.json` contains no full branch-path strings. Latest gate remains `observe_only`. |
| BBN | no | `bbn_network.json` contains generic BBN nodes. Its `market_regime` states are `bull`, `bear`, and `range`; it does not carry all five exact Board B paths as first-class BBN evidence. |
| CatBoost/path-ranker target | yes, not mature | `structural_path_ranking_target.csv` contains all five exact rooted current paths, but rows remain `unobserved`, `maturity_mask=false`, and validation is not promotable. |
| CatBoost current scores | yes, candidate-set only | `current_scores.csv` contains all five exact rooted paths. These are candidate-set scores, not calibrated closed-loop confidence. |
| Execution tree | partial/fail-closed | `execution_tree_trace.json` carries the exact Bull path in `closed_loop_branch_admission`, but status is `fail_closed`, `ready=false`, and `actionable=false`; the trace does not admit all five paths. |
| Workflow snapshot | blocked | `blocking_truth.reason=user_selected_historical_data_missing`; latest execution candidate is `no_trade` with `pre_bayes_gate_status=observe_only`. |

Observed exact paths at CatBoost/path-ranker layer:

- `Bear -> BearMarketDrawdown -> NQHighVixOversoldRebound -> NQRootAdaptiveCostCrisisRepairV3:bear_oversold_high_vix_rebound_h72`
- `Bull -> TrendExpansion -> NQSourceRootCarry -> NQRootAdaptiveCostCrisisRepairV3:bull_source_root_carry_h72`
- `Crisis -> ExtremeStress -> NQFlushRebound -> NQRootAdaptiveCostCrisisRepairV3:crisis_flush_rebound_h72`
- `Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72`
- `Sideways -> RangeConsolidation -> NQCalmVixZReversion -> NQRootAdaptiveCostCrisisRepairV3:sideways_calm_vix_z_revert_h72`

## Decision

- `branch_path_contract_satisfied=false`
- `auto_quant_trade_wire_full_path=false`
- `pre_bayes_full_path=false`
- `bbn_full_path=false`
- `catboost_full_path=true`
- `execution_tree_full_path=partial_fail_closed`
- `selected_historical_data=false`
- `promotion_allowed=false`
- `update_goal=false`

## Next

Keep `034002` as the fail-closed cursor. The next qualifying action remains explicit user selection of exactly one `HTF=1d`, `MTF=4h`, or `LTF=1h`, followed by selected-data factor-research/Auto-Quant in an isolated state-local workspace. The selected run should emit full `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor` fields into the Auto-Quant trade/factor rows before Pre-Bayes/filter, BBN, CatBoost/path-ranker, and execution-tree continuation.
