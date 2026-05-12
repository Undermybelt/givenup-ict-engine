# 121347 Execution Readiness Diagnostic v1

Run id: `20260512T122446+0800-codex-121347-execution-readiness-diagnostic-v1`
Source downstream root: `20260512T121347+0800-codex-115700-enriched-downstream-chain-v1`
Source AQ root: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`
Symbol: `B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700`

## Scope

This support-only slice re-runs read-only `workflow-status` surfaces against the existing `121347` state to identify the remaining execution-readiness blocker. It does not run new provider fetches, does not rerun Auto-Quant/TOMAC, does not mutate ict-engine runtime code, does not select historical data on the user's behalf, does not promote a candidate, and does not call `update_goal`.

## Prompt-to-Artifact Checklist

| Requirement | Evidence | Result |
|---|---|---|
| Preserve current Board B authority | Board file remains `docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md`; this packet is support-only for already-counted `121347` | pass |
| Keep regime-rooted branch path | Execution candidate path is `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1` | pass |
| Preserve required chain order | Diagnostic reads `workflow-status` after the existing Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree chain from `121347` | pass |
| Do not duplicate provider/AQ authority | No provider fetch or AQ/TOMAC command was run in this packet; source remains `115700` | pass |
| Inspect execution readiness/actionability | `execution_readiness=0.32853919817900823`, `execution_gate_status=execution_blocked`, `actionable=false`, `review_status=observe` | fail-closed |
| Inspect CatBoost/path-ranker branch evidence | Path-ranker score is visible in the structural recommended path: raw `0.9868275780976984`, calibrated probability `0.34309623430962344`, lower bound `0.2928391743629338`, runtime source `history_path` | pass but non-promoting |
| Respect selected-history/source-control gate | Workflow blocking truth remains `user_selected_historical_data_missing`; local board search confirms next qualifying action requires explicit selection of exactly one `HTF=1d`, `MTF=4h`, or `LTF=1h` before factor-research | fail-closed |
| Avoid promotion/update_goal | `promotion_allowed=false`, `trade_usable=false`, `update_goal=false` | pass |

## Commands

- `./target/debug/ict-engine workflow-status --symbol B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700 --state-dir docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/state_115700_enriched_downstream_chain_v1 --phase execution-candidate --output-format json`
- `./target/debug/ict-engine workflow-status --symbol B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700 --state-dir docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/state_115700_enriched_downstream_chain_v1 --output-format json`

Both commands exited `0`.

## Readback

- The structural recommended branch remains `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1`.
- Pre-Bayes/filter remains `pass_neutralized`.
- The structural branch candidate remains visible to workflow-status, but it is not executable: `candidate_status=execution_blocked`, `execution_readiness=0.32853919817900823`, `actionable=false`, `review_status=observe`.
- The execution candidate reason is `structural_recommended_path_visible_but_execution_or_pre_bayes_gate_not_ready`.
- The path-ranker surface is present, but its own gate stays observe: `path_ranker_execution_gate_status=observe`.
- Workflow blocking truth remains `user_selected_historical_data_missing`. The executable factor-research command is present in metadata, but the metadata kind is `ask_user`, and it requires explicit path selection before use.
- The broader workflow still lists pending actions `analyze:Review Pre-Bayes Evidence Gate`, `promotion:Block Promotion`, and `iteration:TUNE structure_ict`.

## Decision

This packet confirms the next blocker is not provider authority, AQ/TOMAC execution, row schema, BBN attachment, or CatBoost availability. The blocker is execution admissibility plus selected-history/source-control selection. The branch should stay fail-closed until one explicit data path is selected and the selected-data factor-research/downstream chain is rerun without relaxing Board B gates.

## Artifacts

- Execution candidate extract: `docs/experiments/actionable-regime-confidence/runs/20260512T122446+0800-codex-121347-execution-readiness-diagnostic-v1/121347-execution-readiness-diagnostic-v1/execution_candidate_extract.json`
- Workflow blocker extract: `docs/experiments/actionable-regime-confidence/runs/20260512T122446+0800-codex-121347-execution-readiness-diagnostic-v1/121347-execution-readiness-diagnostic-v1/workflow_blocker_extract.json`
- Raw command outputs: `docs/experiments/actionable-regime-confidence/runs/20260512T122446+0800-codex-121347-execution-readiness-diagnostic-v1/command-output/`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T122446+0800-codex-121347-execution-readiness-diagnostic-v1/checks/121347_execution_readiness_diagnostic_v1_assertions.out`

