# Current Objective Gap Chain Audit v1

- Run id: `20260512T000417-codex-current-objective-gap-chain-audit-v1`.
- Current cursor: `20260512T000801+0800-codex-r6-exact-split-support-debt-audit-v1`.
- Live direct verifier: `schema_ready_unscored` with positives `73` and controls `73`.
- R6 pooled direct gate: `True`; chronological split: `False`; heldout symbol: `False`; heldout venue: `False`.
- Perfect all-correct rows needed for Wilson95 >= 0.95: `73` per class/bucket.
- Prompt-to-artifact checklist status: failed/partial `8` of `10` requirements.
- Gate result: `current_objective_gap_chain_audit_v1=strict_objective_not_achieved_r6_split_species_r3_r5_and_chain_maturity_blocked`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; shared intake mutated: `false`; trade usable: `false`.

## Top Split Gaps
- `chronological_group_split / chronological_train`: positive `38` needs `+35`, negative `38` needs `+35`, min LCB `0.908187067416`.
- `chronological_group_split / chronological_test`: positive `18` needs `+55`, negative `18` needs `+55`, min LCB `0.824115449418`.
- `chronological_group_split / chronological_calibration`: positive `17` needs `+56`, negative `17` needs `+56`, min LCB `0.815676339628`.
- `heldout_venue_exact / COMEX/CME Globex`: positive `29` needs `+44`, negative `29` needs `+44`, min LCB `0.883026405534`.
- `heldout_venue_exact / CME Globex`: positive `9` needs `+64`, negative `9` needs `+64`, min LCB `0.700847246449`.
- `heldout_venue_exact / COMEX`: positive `8` needs `+65`, negative `10` needs `+63`, min LCB `0.675584380489`.
- `heldout_symbol_exact / E-mini S&P 500 futures`: positive `9` needs `+64`, negative `9` needs `+64`, min LCB `0.700847246449`.
- `heldout_venue_exact / NYMEX/CME Globex`: positive `8` needs `+65`, negative `8` needs `+65`, min LCB `0.675584380489`.

## Command Evidence
- `direct_manipulation_row_intake_verifier` returncode `0` summary `schema_ready_unscored`.
- `provider_status_agent` returncode `0` summary `returncode=0`.
- `provider_status_compact` returncode `0` summary `returncode=0`.
- `ict_auto_quant_status` returncode `0` summary `missing_dependency`.
- `analyze_demo` returncode `0` summary `returncode=0`.
- `pre_bayes_status` returncode `0` summary `latest_gate_status=pass_neutralized`.
- `evidence_quality_breakdown` returncode `0` summary `returncode=0`.
- `policy_training_status` returncode `0` summary `entry_models=2 matched_rows=[0, 0]`.
- `workflow_status_execution_candidate` returncode `0` summary `returncode=0`.
- `export_structural_path_ranking_target` returncode `0` summary `rows=3 mature_rows=0`.
- `local_auto_quant_run_help` returncode `2` summary `returncode=2`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T000417-codex-current-objective-gap-chain-audit-v1/current-objective-gap-chain-audit/current_objective_gap_chain_audit_v1.json`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T000417-codex-current-objective-gap-chain-audit-v1/current-objective-gap-chain-audit/current_objective_prompt_to_artifact_checklist_v1.csv`
- Split gap CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T000417-codex-current-objective-gap-chain-audit-v1/current-objective-gap-chain-audit/current_objective_r6_split_gap_v1.csv`
- Species audit JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T000417-codex-current-objective-gap-chain-audit-v1/current-objective-gap-chain-audit/current_objective_direct_species_audit_v1.json`
- Command CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T000417-codex-current-objective-gap-chain-audit-v1/current-objective-gap-chain-audit/current_objective_chain_commands_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T000417-codex-current-objective-gap-chain-audit-v1/checks/current_objective_gap_chain_audit_v1_assertions.out`

Next: source non-spoofing direct Manipulation rows and target the weakest chronology/symbol/venue buckets before rerunning calibration.
