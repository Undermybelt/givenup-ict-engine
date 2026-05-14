# RootTransitionTriad Prompt-to-Artifact Audit v1

Run id: `20260511T192018+0800-codex-board-b-root-transition-triad-v1`.

## Requirement Check

| Requirement | Evidence | Status |
|---|---|---|
| Use accepted Board A context | `accepted_regime_id=BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation` in `branch-rc-spa/root_transition_triad_rc_spa_report_v1.json` | pass |
| Score exactly one recipe | `recipe_id=RootTransitionTriadV1` | pass |
| Preserve root-first branch paths | `branch_paths_evaluated=5` covering Bull, Bear, Sideways, Crisis, and scoped Manipulation | pass |
| Run branch RC-SPA hard gates | final shared `uv_run` pack in `branch-rc-spa/root_transition_triad_rc_spa_report_v1.json`; supplemental concurrent pack in `branch-rc-spa/root_transition_triad_report_v1.json` | pass for fail-closed evidence; no promotion because the final shared pack rejects |
| Promote downstream only if every required branch passes | final shared `uv_run` pack has `0/5` branches passed and `gate_result=fail:required_root_branch_hard_gates_failed` | pass, fail-closed |
| Update authoritative board | `docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md` cursor and ledger row for `20260511T192018` | pass |

## Result

`goal_complete=false` for stable profitability. The active recipe produced enough rows to score, but no promotion is allowed:

- final shared `uv_run` pack: max RC-SPA `76.25`, `0/5` required branches passed
- supplemental concurrent root pack: max RC-SPA `90.78068231417511`, `2/5` required branches passed
- both packs reject the recipe with `fail:required_root_branch_hard_gates_failed`
- scoped `Manipulation` remains `0` trade/PnL rows

Downstream state remains fail-closed and blocked by branch RC-SPA hard gates. The ict-engine dry-run is supplemental fail-closed evidence only and cannot be used as promoted branch consumption.

## Next Action

Use a fresh run root or non-overlapping file names for the next run. Source executable direct `Manipulation` entry/exit PnL rows and switch or repair the root-aware family for Bear/Sideways/Crisis. Do not run Pre-Bayes, BBN, CatBoost/path-ranker, or execution-tree promotion until every required root branch passes RC-SPA without relaxed gates.
