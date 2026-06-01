# 2026-05-08 Whole Repo Audit Debug Trail

- Reproduction baseline:
  - `cargo clippy --all-targets -- -D warnings`
- Current evidence:
  - Clippy fails on release-quality issues across provider catalog, market_state modules, auto_quant workspace profile helpers, orchestration helpers, reporting payload builders, and belief_core helper signatures.
  - This is the first blocking audit layer before broader CLI smoke and user-surface verification.
- Immediate hypothesis:
  - Some findings are straightforward hygiene regressions (`unused import`, `redundant field names`, `manual_strip`, `iter_cloned_collect`).
  - Some findings are structural pressure signals (`too_many_arguments`, dead code / unused helper surfaces) and need selective refactor rather than blind `allow`.
- Next actions:
  - Fix deterministic low-risk clippy violations first.
  - Re-run clippy.
  - Then run focused CLI smoke and record any remaining functional gaps.

## 2026-05-08 Round 2

- Reproduction:
  - Re-ran `cargo clippy --all-targets -- -D warnings` after first low-risk cleanup pass.
- Current reduced failure set:
  - `market_state/config.rs`: `available_profiles`, `UserWeightsTemplate`, `template`, `apply_to` are public but not exported/used outside local tests.
  - `market_state/liquidity.rs`: `detect_session` is public but not exported/used.
  - structural/reporting helpers still fail `clippy::too_many_arguments`:
    - `build_structural_path_plan_artifact_with_runtime_context_and_prior_state`
    - `emit_workflow_status_output`
    - `build_factor_backtest_output_payload`
    - `weighted_seed_beta_update`
    - `structural_path_ranking_target_export_summary`
    - `build_structural_temporal_summary_artifact`
    - `apply_structural_delayed_reward_feedback`
- Root-cause ranking:
  1. `market_state` dead-code is a boundary/export gap: public hot-pluggable helpers exist but the module only re-exports a subset.
  2. Remaining clippy failures are signature-design debt, not random bugs; they need input/context structs at the boundary instead of suppression.
- Next actions:
  - Export/legitimize the intended `market_state` hot-plug helpers.
  - Introduce small input structs for the public/near-public `too_many_arguments` functions, starting with workflow/reporting surfaces.

## 2026-05-08 Round 3

- Progress since Round 2:
  - Cleared deterministic clippy hygiene items across provider catalog, market_state behavior/liquidity/structure, auto_quant workspace profile, reporting helper plumbing, and assorted tests.
  - Re-exported `market_state` hot-plug helpers so the public API matches intended usage instead of tripping dead-code.
  - Refactored these wide signatures to input/context structs:
    - `build_factor_backtest_output_payload`
    - `emit_workflow_status_output`
    - `weighted_seed_beta_update`
    - `build_structural_temporal_summary_artifact`
    - `structural_path_ranking_target_export_summary`
    - `update_structural_policy_correction_stats`
    - `EnhancedAggregator::aggregate`
    - `MarketStateClassifier::aggregate_regimes`
- Current state:
  - A single whole-repo `cargo clippy --all-targets -- -D warnings` process is still running; do not start parallel clippy jobs.
  - Next action depends on its final remaining error set.

## 2026-05-08 Round 4

- Final whole-repo gate:
  - `cargo clippy --all-targets -- -D warnings`
  - result: pass
- Additional real-surface fixes landed after structural cleanup:
  - `workflow-status --human` no longer shows the NQ-specific personal provider lane for unrelated symbols like `NEWSYM`.
  - `factor-autoresearch-status` empty-state now returns an `ask-user` contract with explicit `--data` follow-up instead of an incomplete command.
- New repo-local artifact created:
  - `support/docs/audits/2026-05-08-whole-repo-limitations-and-keywords.md`

## 2026-05-12 Feedback Merge Performance

- Reproduction:
  - `cargo test test_merge_feedback_records_large_resolved_structural_batch_is_indexed -- --nocapture`
- Current evidence:
  - The focused test fails consistently with `merge_feedback_records` taking `8.36s` for a 3,000-record resolved structural batch against a 2s budget.
  - The merge path builds a feedback-key set once, then performs per-record linear scans over `feedback_history` to find matching unresolved records or existing resolved records by `feedback_resolution_key`.
- Root cause hypothesis:
  - Large batch ingestion becomes quadratic because every structural feedback record recomputes resolution keys while scanning the accumulated history.
- Fix direction:
  - Maintain resolution-key indexes for unresolved and resolved records during the merge, updating them whenever a record is pushed, skipped, or replaces a pending record.

## 2026-05-12 CatBoost Branch Segment Export

- Reproduction:
  - `CARGO_TARGET_DIR=/tmp/ict-engine-codex-regime-bundle-bbn-target cargo test target_export_surfaces_branch_segments_as_catboost_features --lib -- --nocapture`
- Current evidence:
  - Focused test failed because the exported row for a branch-shaped `path_id` had `regime_profit_branch_path = null`.
  - The CSV header already exposed the branch segment columns, so the failure is row population, not schema exposure.
- Root cause hypothesis:
  - The structural target export combines candidate, feedback, regime-bundle, and history rows; some branch-shaped rows can reach the final current/history export without explicit branch field normalization.
- Fix direction:
  - Normalize branch-shaped target rows at the final export boundary before rendering current/history JSONL and CSV.

## 2026-05-12 Board A/B Document Dependency Root Cause

- Reproduction:
  - `rg -n "support/docs/(plans/2026-05-10|experiments/actionable-regime-confidence)" src support/scripts tests README.md support/docs/README.md`
  - `wc -l -c support/docs/plans/2026-05-10-actionable-regime-confidence-todo.md support/docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md`
- Current evidence:
  - The two May 10 Board A/B logs total more than 100,000 lines and about 12.6MB.
  - `src/` does not directly depend on those two May 10 board paths.
  - Docs, support scripts, and experiment checklists reference those paths as proof or coordination sources.
  - Runtime has state/artifact surfaces for provider, Pre-Bayes, BBN, structural path ranking, execution tree, and feedback, but experiment outcomes are not yet cleanly promoted/rejected into a compact runtime-consumable catalog.
- Root cause hypothesis:
  - The project confused coordination logs with product/runtime truth. Useful positive and negative results stayed embedded in historical prose and run roots instead of being distilled into explicit runtime artifacts or deletion candidates.
- Fix direction:
  - Add a curation boundary: extract run-root outcomes into a small machine-readable ledger with `promote`, `retain_negative`, `discard`, or `needs_review`, then route useful positive results into runtime artifacts/examples and useless or non-reproducible material into cleanup candidates. The old boards should become archive evidence only, never consumer or strategy dependencies.

## 2026-05-12 Candidate Pack Promotion Boundary

- Reproduction:
  - `python3 support/scripts/research/factor_candidate_resolver.py --repo-root . --build-packs --output-dir /tmp/ict-engine-candidate-curation-generic-final`
  - `python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver support.scripts.research.tests.test_factor_candidate_pack`
- Current evidence:
  - Seven distilled candidate packs now live under `support/examples/factor_candidate_packs/curated-auto-quant-v1/`.
  - The default zero-config candidate registry can build seven packs without a personal profile or historical board dependency.
  - Built candidates: VRP compression 15m, trend pullback dense 15m, liquidity sweep reclaim 15m wide, killzone breakout 1h, killzone displacement, FVG retrace 1h, and FVG retrace 5m.
  - The copied packs contain no `/Users`, `/tmp`, `/private`, or `Auto-Quant` paths.
  - Remaining non-buildable candidates are now classified as `missing_reusable_artifact` / `discard_until_reusable_artifact` instead of being kept alive by prose-only board references.
- Root cause status:
  - The first concrete document-dependency leak is fixed at the candidate-pack boundary: useful results are now repo-local machine artifacts, while prose-only results are excluded from the active loop.

## 2026-05-13 Candidate Pack Runtime Loop Surface

- Reproduction:
  - `python3 support/scripts/research/factor_candidate_resolver.py --repo-root . --list-buildable --output-format human`
  - `python3 support/scripts/research/factor_candidate_resolver.py --repo-root . --build-packs --output-dir /tmp/ict-engine-candidate-curation-generic-final`
  - `rg -n "/Users|/tmp|/private|Auto-Quant" /tmp/ict-engine-candidate-curation-generic-final/packs /tmp/ict-engine-candidate-curation-generic-final/candidate_registry.json /tmp/ict-engine-candidate-curation-generic-final/candidate_pack_index.json /tmp/ict-engine-candidate-curation-generic-final/candidate_spec_index.json /tmp/ict-engine-buildable-candidates.json || true`
  - `python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver support.scripts.research.tests.test_factor_candidate_pack`
- Current evidence:
  - `--list-buildable` reports 7 buildable repo-local curated packs without reading historical Board A/B logs.
  - `candidate_pack_index.json` now emits relative `pack_dir` values such as `packs/family_f_vrp_compression_15m_v1`.
  - `source_candidate_pack_dir` remains repo-relative under `support/examples/factor_candidate_packs/curated-auto-quant-v1/...`.
  - The leak scan returns no `/Users`, `/tmp`, `/private`, or `Auto-Quant` hits across generated packs, registry, pack index, spec index, and list output.
  - Unit coverage is 16 tests OK.
- Root cause status:
  - The consumer/agent inspection path no longer requires opening the May 10 board logs or generating a temp pack tree just to see the useful candidates.

## 2026-05-13 Native Candidate Pack State Loop

- Reproduction:
  - `cargo test factor_candidate_pack -- --nocapture`
  - `cargo run --quiet -- factor-candidate-packs`
  - `cargo run --quiet -- factor-candidate-packs --symbol FACTOR_CANDIDATES --state-dir /tmp/ict-engine-candidates`
  - `jq '.[] | {artifact_kind, status, path, decision_hint}' /tmp/ict-engine-candidates/FACTOR_CANDIDATES/artifact_ledger.json`
  - `jq '{symbol, recent_artifacts: [.recent_artifacts[] | {artifact_kind, status, path}]}' /tmp/ict-engine-candidates/FACTOR_CANDIDATES/workflow_snapshot.json`
  - `cargo run --quiet -- artifact-status --symbol FACTOR_CANDIDATES --state-dir /tmp/ict-engine-candidates --latest-only`
  - `cargo run --quiet -- workflow-status --symbol FACTOR_CANDIDATES --state-dir /tmp/ict-engine-candidates --output-format json`
- Current evidence:
  - Native CLI command `factor-candidate-packs` reads the seven repo-local curated packs without Python.
  - With `--state-dir`, the command writes `factor_candidate_pack_inventory.json`, appends an `artifact_kind=factor_candidate_pack_inventory` ledger row with `status=ready`, and refreshes `workflow_snapshot.json`.
  - `artifact-status --latest-only` sees one `factor_candidate_pack_inventory` entry with `path_exists=true`.
  - `workflow-status` exposes `factor_candidate_pack_inventory` under `recent_artifacts`.
  - The focused Rust test filter passes 3 native candidate-pack tests. The run still reports the pre-existing `total_return` dead-code warning in `src/factor_lab/factor_definition.rs`.
  - Python resolver/pack tests still pass 16 tests.
- Root cause status:
  - The moved factor results now have a native project surface and a state/artifact-loop presence. They are still inspection/admission artifacts, not trade-usable promotions.

## 2026-05-13 Candidate Pack Policy Training Visibility

- Reproduction:
  - `cargo run --quiet -- policy-training-status --symbol FACTOR_CANDIDATES --state-dir /tmp/ict-engine-candidates --output-format human`
  - `cargo run --quiet -- policy-training-status --symbol FACTOR_CANDIDATES --state-dir /tmp/ict-engine-candidates --output-format json | jq '.factor_candidate_packs, .summary_line'`
  - `rm -rf /tmp/ict-engine-candidates-smoke && cargo run --quiet -- factor-candidate-packs --symbol FACTOR_CANDIDATES --state-dir /tmp/ict-engine-candidates-smoke && cargo run --quiet -- policy-training-status --symbol FACTOR_CANDIDATES --state-dir /tmp/ict-engine-candidates-smoke --output-format human`
- Current evidence:
  - Human output includes `Factor candidate packs: inventory=ready count=7 preferred_density=6 cross_market=6`.
  - JSON output exposes `factor_candidate_packs.inventory_ready=true`, `candidate_pack_count=7`, `preferred_density_count=6`, and `cross_market_candidate_count=6`.
  - Fresh `/tmp` smoke persists `factor_candidate_pack_inventory.json` first, then `policy-training-status` reads the same state and reports the candidate pack summary.
  - The overall `summary_line` now includes the factor candidate pack summary between entry-model readiness and structural path ranking readiness.
  - The structural path ranking line still reports `runtime_selection=disabled` and zero runtime matches, so these packs are visible to training/admission checks but are not promoted into execution.
- Root cause status:
  - Candidate成果 are no longer trapped behind the May 10 prose logs: native CLI state and `policy-training-status` can inspect the curated packs through the normal artifact ledger. The remaining real gate is an adapter from vetted pack evidence into Pre-Bayes/BBN/CatBoost/execution-tree admission, not more document work.

## 2026-05-13 Candidate Pack Structural Admission Target

- Reproduction:
  - `cargo test factor_candidate_admission -- --nocapture`
  - `rm -rf /tmp/ict-engine-candidates-admission && cargo run --quiet -- factor-candidate-admission-targets --symbol FACTOR_CANDIDATES --state-dir /tmp/ict-engine-candidates-admission --output-format human && cargo run --quiet -- policy-training-status --symbol FACTOR_CANDIDATES --state-dir /tmp/ict-engine-candidates-admission --output-format human`
  - `cargo run --quiet -- artifact-status --symbol FACTOR_CANDIDATES --state-dir /tmp/ict-engine-candidates-admission --latest-only`
  - `cargo run --quiet -- workflow-status --symbol FACTOR_CANDIDATES --state-dir /tmp/ict-engine-candidates-admission --output-format json`
- Current evidence:
  - New native command `factor-candidate-admission-targets` writes `factor_candidate_pack_inventory.json`, standard `policy_training/structural_path_ranking_target.*`, `factor_candidate_ranker_direct_model.json`, and `structural_path_ranking_trainer_artifact.json` from the repo-local curated packs.
  - Smoke output reports `factor_candidate_admission_targets rows=35 candidate_set_id=factor-candidate-admission:FACTOR_CANDIDATES:curated-auto-quant-v1`.
  - `policy-training-status` then reports `Factor candidate packs: inventory=ready count=7 preferred_density=6 cross_market=6` and `structural_path_ranking_target rows=35 history_rows=35 mature_rows=35 history_mature_rows=35`.
  - `policy-training-status` reports `trainer_artifact=ready trainer_status=present_validation_insufficient`; runtime stays disabled.
  - `artifact-status --latest-only` sees three path-existing ledger entries: `factor_candidate_pack_inventory` with `status=ready`, `structural_path_ranking_target` with `status=admission_pending`, and `structural_path_ranking_trainer_artifact` with `status=ready_observation_only`.
  - `workflow-status` exposes all three ledger entries under `recent_artifacts` with local paths redacted.
  - The exported structural rows are `direction=Observe`; candidate aggregate rows plus cross-market evidence rows become offline matured target observations (`training_weight_rows=35`, `raw_scored_mature=35/30`).
  - The export deliberately leaves `calibrated_rows=0`, `execution_gate_rows=0`, `production_validation=0/30`, and `runtime_selection=disabled`; this makes them trainable/inspectable by the normal admission surface with a registered observation-only trainer artifact, without making them trade-usable.
- Root cause status:
  - Useful candidate成果 now have a repo-local path from pack artifact -> artifact ledger -> policy-training inventory -> structural path ranking target export. Remaining work is real promotion evidence: mature outcomes, Pre-Bayes/BBN learning, CatBoost/path-ranker validation, execution-tree admission, and feedback/update closure.

## 2026-05-29 Retired Transition/PDA Gate Misdirection

- Reproduction:
  - `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  - `ps -axo pid,ppid,etime,command | rg -i "auto.?quant|tomac|factor|run_tomac|fetch_external|ibkr|python3"`
  - `rg -n "pda_hybrid_alignment|hybrid_transition_hazard|transition_hazard" src support/scripts tests support/docs/command-output-contract.md AGENT.md AGENTS.md README.md Cargo.toml`
- Current evidence:
  - Compact claim audit showed `trade_usable_true=0`, `promotion_allowed_true=0`, four fresh active claims, and one live Auto-Quant process; this slice did not promote a factor.
  - Historical commits had already tried to retire these fields as live gates: `1c8c9327 Remove transition hazard live gates`, `1877fcd7 fix(board-b): keep PDA telemetry out of hard gates`, and `e4db0e61 Align blocker report PDA telemetry gates`.
  - Current `workflow_status.rs` still copied `/output/hybrid_transition_hazard` into candidate/readback `transition_hazard` and copied `/output/pda_hybrid_alignment` into candidate/readback `pda_hybrid_alignment`.
  - `regime_root_survivor_blocker_report.py` still rendered those fields under downstream practical readback, and `pa_agent_intake.py` still shipped default `strict_gate_policy` entries requiring `transition_hazard_lt` and `pda_hybrid_alignment`.
- Root cause:
  - Incomplete retirement: producer telemetry remained, then agent-facing readbacks and default templates preserved old gate-shaped names. Later factor-training agents could mistake telemetry/legacy fields for current practical-admission requirements.
- Fix boundary:
  - Keep upstream telemetry if present, but stop surfacing it as execution candidate/practical admission state.
  - Remove retired gate keys from PA intake defaults and blocker-report downstream readback.
  - Extend the downstream practical-admission source checker to flag retired PDA/transition gate templates.
- Verification target:
  - Focused Rust workflow-status tests must show same-root trace admission remains actionable while `transition_hazard` and `pda_hybrid_alignment` are absent from candidate output.
  - Focused Python tests must pass for blocker report, source checker, PA intake, and migration readback.
- Verification run:
  - `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v` passed 35 tests.
  - `python3 -m unittest support.scripts.research.tests.test_regime_root_survivor_blocker_report support.scripts.research.tests.test_pa_agent_intake support.scripts.research.tests.test_factor_lifecycle_migration_readback -v` passed 28 tests.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-codex-retired-gates cargo test same_root_trace_admission_does_not_surface_retired_telemetry_as_candidate_gate -- --nocapture` passed.
  - `python3 support/scripts/research/downstream_practical_admission_source_check.py support/scripts/research/pa_agent_intake.py support/scripts/research/regime_root_survivor_blocker_report.py support/scripts/research/factor_lifecycle_migration_readback.py --pretty` reported all checked files ok.
  - `rustfmt --check src/application/orchestration/workflow_status.rs` and scoped `git diff --check` passed.
  - Full `cargo fmt --check` still fails on pre-existing formatting drift in `src/application/orchestration/structural_playbook.rs` and `src/application/regime/consumer_bundle_adapter.rs`; those files were not touched in this slice.

## 2026-05-29 Live-Ready Naming Versus Funded Fill Semantics

- Reproduction target:

## 2026-05-30 Fixed Bps Source Check False Positives And Ladder Misses

- Reproduction:
  - `python3 -m unittest support.scripts.research.tests.test_fixed_bps_cost_model_source_check -v`
  - ad hoc probe: nested comparison under subtraction
    - source: `return 1.0 - float(trades >= 0.10)`
    - current result: false positive `fixed_bps_cost_formula`
  - ad hoc probe: direct compare without subtraction
    - source: `return trades_per_day >= 0.10`
    - current result: pass
  - ad hoc probe: indirect ladder alias
    - source:
      - `BPS_LEVELS = (0, 5, 15)`
      - `for bps in BPS_LEVELS: ...`
    - current result: pass, so the ladder is missed when referenced through a named constant
- Current evidence:
  - The new percent-space heuristic in `support/scripts/research/fixed_bps_cost_model_source_check.py::contains_bps_formula` only checks for:
    - a trade-count name
    - a literal from `PERCENT_SPACE_COST_LITERALS`
    - any subtraction anywhere in the same `ast.BinOp` subtree
  - It does not exclude `ast.Compare`, so `trades >= 0.10` becomes a false hard-coded-cost hit when wrapped inside another subtraction expression.
  - `is_fixed_bps_ladder` recognizes only literal tuple/list/set nodes attached directly to `for bps in ...`; it does not resolve `Name` aliases bound to constant numeric sequences.
- Root-cause hypothesis:
  1. The percent-literal fallback is too structural and needs a comparison guard.
  2. The ladder detector needs simple name-resolution for constant numeric sequences before evaluating the `for bps in ...` iterator.
- Next actions:
  - Add focused failing tests for the nested-compare false positive and the named-ladder false negative.
  - Patch only the source checker logic needed to make those tests pass.
  - Re-run the focused unittest module, then run the source checker over the edited file set.
  - Inspect `policy-training-status` and `workflow-status` lifecycle readbacks that expose `paper_ready`, `live_ready`, and `live_trade_status`.
- Current evidence:
  - `src/application/factor_lifecycle/profitability_admission.rs` does not require funded real-money broker fills for live readiness. Its live blockers are execution readiness, execution gate status, Pre-Bayes status, execution-tree status/branch, path-ranker consumption, and ranker validation.
  - `src/application/entry_models/training_export.rs` reports `live_ready_count` from explicit lifecycle statuses `live_trade_ready` / `live_trade_usable` plus mature training evidence.
  - The agent/user-facing output lacks an explicit machine-readable clarification that `live_ready` means deployability from the evidence chain and not funded-live-loss/fill proof.
- Root cause hypothesis:
  - The gate logic is mostly fail-closed and does not demand real-money loss, but the readback contract uses `live_*` naming without a deployability alias or `funded_live_fill_required=false`, so humans and downstream agents can misread it as requiring capital-at-risk live fills.
- Fix boundary:
  - Do not relax any practical gates.
  - Add explicit deploy-readiness/readiness-contract fields to the lifecycle readbacks while preserving legacy `live_ready`/`live_trade_status` compatibility fields.
  - Add regression coverage proving `live_trade_usable` can be counted from mature lifecycle evidence without any broker-fill evidence field.
- Verification run:
  - `CARGO_TARGET_DIR=/tmp/ict-engine-codex-live-ready-semantics cargo test -q policy_training_status_exposes_deploy_ready_without_funded_live_fill_requirement -- --nocapture` passed.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-codex-live-ready-semantics cargo test -q workflow_factor_profitability_lifecycle_marks_deploy_ready_without_funded_live_fill -- --nocapture` passed.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-codex-live-ready-semantics cargo test -q lifecycle_decision_serializes_as_snake_case_planes -- --nocapture` passed.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-codex-live-ready-semantics cargo test -q policy_training_status_ -- --nocapture` passed 11 focused tests.
  - `CARGO_TARGET_DIR=/tmp/ict-engine-codex-live-ready-semantics cargo test -q workflow_factor_profitability_lifecycle_ -- --nocapture` passed 6 focused tests.
  - `python3 -m unittest support.scripts.research.tests.test_regime_root_survivor_blocker_report -v` passed 19 tests.
  - `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure support.scripts.tests.test_factor_claim_terminalization_audit -v` passed 99 tests.
  - `python3 -m py_compile support/scripts/research/regime_root_survivor_blocker_report.py` passed.
  - `rustfmt --check` on touched Rust files and scoped `git diff --check` passed.
- Follow-up root-cause audit:
  - A stale same-named experiment script still existed at `support/docs/experiments/actionable-regime-confidence/scripts/regime_root_survivor_blocker_report.py`. It was easy to confuse with the live `support/scripts/research/regime_root_survivor_blocker_report.py` and still emitted `hard_gate.transition_hazard_lt=0.60` plus `hard_gate.pda_hybrid_alignment=true`.
  - `python3 support/scripts/research/downstream_practical_admission_source_check.py support/docs/experiments/actionable-regime-confidence/scripts/regime_root_survivor_blocker_report.py` reproduced the problem with `retired_field_used_as_practical_gate_template` violations before repair.
  - The experiment script now renames those historical values to `retired_telemetry` and emits `current_gate_shape.retired_transition_pda_telemetry_gate=false`; `status()` treats readiness as a probe that still requires lifecycle validation rather than practical admission.
  - `support/docs/experiments/actionable-regime-confidence/scripts/test_regime_root_survivor_blocker_report_identity.py` covers the old report shape so `transition_hazard`, `transition_hazard_lt`, `pda_hybrid_alignment`, and `pda_hybrid_alignment_true` do not re-enter as gate fields.
  - The practical-admission source checker also has focused coverage for hand-written `same-tree-practical-closure/v1` packets versus the canonical `same_tree_practical_closure.py` builder path, closing another same-family promotion shortcut.
- Follow-up verification run:
  - `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v` passed 38 tests.
  - `python3 support/scripts/research/downstream_practical_admission_source_check.py support/docs/experiments/actionable-regime-confidence/scripts/regime_root_survivor_blocker_report.py --pretty` reported `practical_admission_source_ok`.
  - `python3 support/docs/experiments/actionable-regime-confidence/scripts/test_regime_root_survivor_blocker_report_identity.py -v` passed 4 tests.
  - `python3 -m py_compile support/scripts/research/downstream_practical_admission_source_check.py support/docs/experiments/actionable-regime-confidence/scripts/regime_root_survivor_blocker_report.py support/docs/experiments/actionable-regime-confidence/scripts/test_regime_root_survivor_blocker_report_identity.py` passed.

## 2026-05-30 Same-Tree Closure Deploy-Ready Contract Tightening

- Reproduction target:
  - `same_tree_practical_closure.py` was still the final `trade_usable=true` packet owner, but it accepted the legacy lifecycle tuple with `live_ready_count` and `live_trade_status=ready` alone.
  - `factor_claim_terminalization_audit.py` surfaced any valid-looking closure packet that passed the helper, so a future packet could still omit the deploy-readiness clarification and revive the funded-fill misread.
- Root cause:
  - The earlier readback repair clarified `policy-training-status`, `workflow-status`, and blocker reports, but the canonical objective-closure packet schema did not yet require `deploy_ready=true`, `funded_live_fill_required=false`, or the readiness contract string.
- Fix boundary:
  - Tighten only the canonical same-tree practical closure owner and its audit consumer.
  - Require `deploy_ready_count>0` in `policy_training_summary.factor_profitability_lifecycle` alongside the legacy positive `live_ready_count` / `live_trade_usable_count`.
  - Require both terminal metrics and closure packet to declare `funded_live_fill_required=false` and `readiness_contract=deploy_ready_from_backtest_autoquant_provider_or_paper_sim_execution_chain_not_funded_fill`.
  - Preserve strict practical gates; this does not make any current factor trade-usable.
- Producer compatibility:
  - `run_tomac_nq_compound_trend_rrr_chopfilter_practical_lifecycle_v1.py` and `run_tomac_nq_bidir_opening_drive_exact_downstream_v1.py` now pass deploy-readiness fields from policy lifecycle surfaces into terminal metrics before calling the canonical helper.
- Verification run:
  - `python3 -m unittest support.scripts.research.tests.test_same_tree_practical_closure support.scripts.tests.test_factor_claim_terminalization_audit -v` passed 104 tests.
  - `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v` passed 43 tests.
  - `python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v` passed 40 tests.
  - `python3 support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_nq_compound_trend_rrr_chopfilter_practical_lifecycle_v1.py -v` passed 3 tests.
  - `python3 support/docs/experiments/actionable-regime-confidence/scripts/test_tomac_nq_bidir_opening_drive_exact_downstream_v1.py -v` passed 12 tests.
  - `python3 support/scripts/research/downstream_practical_admission_source_check.py support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_nq_compound_trend_rrr_chopfilter_practical_lifecycle_v1.py support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_nq_bidir_opening_drive_exact_downstream_v1.py --pretty` reported both files `practical_admission_source_ok`.

## 2026-05-31 Objective Snapshot Timeout Leaves Nested Audit Children

- Reproduction:
  - `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --timeout-seconds 180 --output-dir /tmp/ict-engine-consumer-ux-evidence-audit-20260531T1316-after-quarantine-refresh-codex`
  - Result: exit code `2`, `summary.status=snapshot_failed`, `failed_audit=done_definition`, `error=missing_json_output`, command error `timeout`.
- Current evidence:
  - The same light done-definition shape completed as a direct child at `/tmp/ict-engine-done-definition-after-practical-quarantine-refresh-20260531T1314.json` with `summary.status=pass`, `fail_count=0`, `skip_count=4`, `completion_ready=false`.
  - After the parent timeout, `ps -axo pid,ppid,pgid,etime,stat,command` showed orphaned nested scanners:
    - `fixed_bps_cost_model_source_check.py --tracked --compact` with `PPID=1` and independent `PGID` values.
  - A concurrent full-heavy done-definition audit was also active:
    `/tmp/ict-engine-done-definition-heavy-20260531T-current-6929d5b-duplicate-count.json`.
- Root cause hypothesis:
  - `objective_closure_snapshot.py::run_command` kills only the direct child process group on timeout.
  - `done_definition_audit.py::run_command` starts nested scanners with `start_new_session=True`, so they are not in the direct done-definition process group and can survive as orphaned scanner processes when the parent objective wrapper times out.
- TDD Route:
  - Mode: auto
  - Decision: strict
  - Reason: shared objective-packet timeout behavior; stale nested audit processes can distort later evidence packets.
  - Verification: add a focused unit test for descendant process groups on parent timeout before editing `objective_closure_snapshot.py`.
