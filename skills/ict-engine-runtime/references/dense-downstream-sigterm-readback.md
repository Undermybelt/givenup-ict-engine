# Dense downstream SIGTERM readback and fail-closed classification

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use when a long downstream runner is killed by SIGTERM / exit -15 / 143 while training profitability factors.

## Pattern

If a downstream process dies by SIGTERM, do not treat it as a strategy verdict. First inspect sibling run directories for a completed run of the same source packet and branch.

For dense YF RSI/VWAP 1m branches, the useful evidence often exists in earlier `downstream-*` directories even when the newest process was killed before CatBoost or terminal summary.

## Required readback

1. Locate source run:
   - `support/docs/experiments/actionable-regime-confidence/runs/<source>/downstream-*`
2. Compare latest killed run with latest complete run.
3. Read:
   - `summaries/terminal_decision_summary.md`
   - `checks/terminal_metrics.json` if present
   - `checks/*.exit`
   - `state/<SYMBOL>/execution_tree_trace.json`, nested `output.*`
   - `state/<SYMBOL>/policy_training/structural_path_ranking_target_summary.json`
   - `state/<SYMBOL>/workflow_snapshot.json`
4. Report killed-process status separately from strategy verdict.

## Verdict rules

A killed process is `incomplete`, not fail/pass.

A prior complete run can still classify the branch. Use fail-closed when any live-ready floor fails:

- `hybrid_transition_hazard >= 0.60`
- `pda_hybrid_alignment=false`
- `execution_readiness < 0.65`
- path-ranker not visible/used or `ranker_validation_ready=false`
- `mature_rows < 30`
- execution tree stays `observe`, `transition_guardrail`, or `guarded`

Do not keep rerunning the same branch if complete evidence repeatedly shows high hazard + PDA mismatch + low readiness. Move the branch to observation and choose a low-hazard / PDA-aligned overlay or a new candidate.

## Session examples

### Fintech lending dense RSI/VWAP

Killed process: `proc_017f0343c8d9`, exit `143`, script `/tmp/run_yf_fintech_lending_rsi_vwap_reclaim_1m_dense_downstream_v1.py`.

Complete prior run:
`20260519T133856+0800-codex-yf-fintech-lending-rsi-vwap-reclaim-1m-dense-v1/downstream-20260519T135340+0800`

Verdict: `gate1_pass_downstream_fail_closed`.

Key blockers:
- execution: `observe / transition_guardrail / guarded`
- `hybrid_transition_hazard=0.6293519858490934`
- `execution_readiness=0.4614462727928709`
- `path_ranker_score_visible_to_execution_tree=false`
- `path_ranker_score_used_by_execution_tree=false`
- `ranker_validation_ready=false`
- `mature_rows=1`, `history_mature_rows=12`

A newer killed/partial FAST run reached only step 07 and was worse:
- `hybrid_transition_hazard=0.9758493406010252`
- `pda_hybrid_alignment=false`
- `execution_readiness=0.45336337186855646`

### Database software dense RSI/VWAP

Killed process: `proc_c8e550e3745f`, exit `-15`, script `support/docs/experiments/actionable-regime-confidence/scripts/run_yf_database_software_rsi_vwap_reclaim_1m_dense_downstream_v1.py`.

Complete prior run:
`20260519T063331+0800-codex-yf-database-software-rsi-vwap-reclaim-1m-dense-v1/downstream-20260519T102447+0800`

Verdict: `gate1_pass_downstream_fail_closed`.

Key blockers:
- exact branch survived and CatBoost trained
- execution: `observe / transition_guardrail / guarded`
- `hybrid_transition_hazard=0.9686632089505138`
- `pda_hybrid_alignment=false`
- `execution_readiness=0.5306123997766115`
- `path_ranker_score_visible_to_execution_tree=true`
- `path_ranker_score_used_by_execution_tree=false`
- `path_ranker_model_family=catboost`
- `path_ranker_runtime_source=history_path`
- `ranker_validation_ready=false`
- `mature_rows=1`, `history_mature_rows=9`
- `blocking_truth=bridge_needs_confirmation`, `bridge_probability_gap=0.032`

## Reporting shape

Keep the user-facing report short:

```text
Killed process = incomplete, not verdict.
Prior complete run = <path>
Decision = <gate/pass/fail-closed>
Blockers = hazard/readiness/PDA/ranker/mature rows
Next = observe/drop or retry only if the new run can change the blocker
```
