# Board B Branch-Path Wire Contract Unit v1

Timestamp: `20260512T051137+0800`

Scope:
- Code-only wire-contract slice for `src/application/auto_quant/real_trades/wire.rs`.
- No selected historical data was chosen.
- No Auto-Quant training, canonical merge, Pre-Bayes, BBN, CatBoost/path-ranker, or execution-tree promotion run was performed.

Readback:
- `RealTradeRecord` now accepts record-level rooted branch-path fields: `regime_profit_branch_path`, `main_regime`, `sub_regime`, `sub_sub_regime_or_profit_factor`, and `profit_factor`.
- Record-level branch-path evidence is converted into `FeedbackRecord.structural_feedback.path_id` when explicit structural feedback refs are absent.
- The rooted branch path is also preserved as a `FeedbackFactorUsage` item with category `regime_profit_branch_path`.
- Path-only records recover `node_id`, `branch_id`, and `scenario_id` from the `main -> sub -> sub_sub -> profit_factor` shape.

Evidence:
- `checks/branch_path_wire_contract_unit_v1.out`

Gate:
- `diagnostic_only:branch_path_wire_contract_unit`.
- `pass:regime_profit_branch_path_unit_tests_2_passed`.
- `blocked:user_selected_historical_data_missing`.
- `promotion_allowed=false`.
- `update_goal=false`.
