# Board B Current Branch Contract Readback v1

Gate result: `board_b_current_branch_contract_readback_v1=branch_contract_preserved_runtime_fail_closed_user_selection_required_no_promotion`

This is a read-only current-state packet for Board B after the user restated that profitability factors must be rooted in regime discrimination and carried through filter / Pre-Bayes, BBN, CatBoost / path-ranking, and execution tree as a branch path. It does not edit the Current Cursor, start new Auto-Quant training, consume active CatBoost owner runs, mutate source/control roots, promote a candidate, or call `update_goal`.

Observed board hashes:
- Board B profitability TODO: `55696885e527bbb632432ba6e9b6107ba14f737fbb28ca6c03dfaa559108dd0a`
- Board A regime-confidence TODO: `a7eb7ed6523cafc19362e27cf0a6be4199f5c419a3919fcf5d221a69e9fe2c06`

Commands:
- `01_provider_status_agent`: exit `0`
- `02_auto_quant_status_combined`: exit `0`
- `03_pre_bayes_status_combined`: exit `0`
- `04_policy_training_status_combined`: exit `0`
- `05_workflow_structural_bundle_combined`: exit `0`
- `06_workflow_execution_candidate_combined`: exit `0`
- `07_board_hashes`: exit `0`
- `08_required_tmp_roots`: exit `0`
- `09_active_owner_processes`: exit `0`

Readback:
- Board B already encodes the required root-first contract: `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`, and downstream stages must preserve `parent_regime_root` plus `regime_profit_branch_path`.
- The combined Board B state still exposes `5` rooted branch paths for `NQRootAdaptiveCostCrisisRepairV3`, including Bull, Bear, Sideways, Crisis, and scoped Manipulation.
- Pre-Bayes/filter remains `observe_only`; BBN is visible only as read-only regime bundle evidence, while applied bundle status is `skipped`.
- CatBoost/path-ranking runtime is enabled and matches `5` candidate-set paths, but validation remains `0/30` production and `0/30` observation, with `mature_rows=0`.
- The structural bundle selects the exact scoped Manipulation branch path and reports raw path score `0.9496554995719656`, but its own next step requires asking the user to choose historical data.
- Execution candidate is not trade-usable: `actionable=false`, `ready=false`, `candidate_status=execution_blocked`, `pre_bayes_gate_status=observe_only`, and `execution_readiness=0.3210541039505038`.
- Provider status remains mixed: yfinance and Kraken CLI are ready; IBKR is gateway-reachable but dependency-unhealthy; TradingViewRemix MCP is unhealthy; Kraken public is dependency-unhealthy.
- Auto-Quant status for the combined state is `missing_dependency`, `healthy=false`, `bootstrap_needed=true`, and `data_ready=false`. The newer local-reuse packet improves a separate isolated state but does not unlock this combined Board B state.
- Required source/control roots remain absent: `/tmp/ict-engine-board-a-r6-owner-export-v1`, `/tmp/ict-engine-native-subhour-source-label-intake`, and `/tmp/ict-engine-source-panel-recency-extension`.
- Active owner Cargo processes for branch-segment CatBoost tests were present at readback time, so this packet does not consume those runs.

Decision:
- Count this packet once as current branch-contract/runtime blocker evidence.
- It confirms the user-requested branch shape is the correct contract and is present in Board B, but it does not unlock selected-data Auto-Quant training or downstream promotion.
- Promotion remains blocked by `user_selected_historical_data_missing`, `pre_bayes_observe_only`, `catboost_path_ranker_validation_0_of_30`, `execution_blocked`, absent required source/control roots, and active concurrent owner runs.
- `promotion_allowed=false`.
- `update_goal=false`.

Next:
- Preserve the Current Cursor next action. The next qualifying Board B action still requires an explicit user selection of exactly one recorded path: `HTF=1d`, `MTF=4h`, or `LTF=1h`. After that, run selected-data Auto-Quant/factor-research and only continue through filter / Pre-Bayes -> BBN -> CatBoost / path-ranking -> execution tree if the selected run creates nonzero mature rooted observations while preserving the exact `regime_profit_branch_path`.
