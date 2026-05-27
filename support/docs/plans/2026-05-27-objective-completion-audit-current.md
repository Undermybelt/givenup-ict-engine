# Objective Completion Audit - Current

Date: 2026-05-27

## Requested Outcome

Audit whether `ict-engine` has actually finished the objective below, using the
current worktree and current runtime/readback evidence as authority:

- optimize factor training direction;
- ensure trained profit factors still work through each closed-loop stage in
  practical runtime, not only in training;
- ensure both training-time and post-training changes improve the closed loop
  rather than silently bypassing or weakening it;
- if code changes are needed, commit verified slices and keep progress tracked
  in a durable document.

## Current Verdict

Status: `not proven / not complete`

Reason:

1. Board B ownership is still crowded. `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
   now reports `active_claims=13`, `live_factor_processes=2`,
   `status=needs_attention`, and `next_action=terminalize or externalize active
   claims; wait for live factor processes to exit or claim them before
   closure`.
2. The authoritative release/closed-loop handoff
   `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`
   still records multiple `blocked` rows stating release/objective completion is
   not yet proven from the current tree.
3. The profitability lifecycle rebuild plan
   `support/docs/plans/2026-05-25-regime-conditioned-profitability-gate-rebuild-plan.md`
   explicitly says post-implementation loopholes must still be treated as part
   of the plan before closure.
4. The current worktree is broad and dirty. There is no fresh, end-to-end proof
   from this exact tree that one rooted profitability-factor chain can move from
   provider/material -> training/admission -> Pre-Bayes/filter -> BBN ->
   path-ranker -> execution tree -> feedback/update with non-observe practical
   readiness and without leaking false positives.

## Completion Requirements To Prove

The objective is only complete if current evidence proves all of the following:

1. Training-direction changes are actually better than the previous baseline,
   not just different.
2. Learning-only positive factors are allowed to continue training without
   being misreported as paper-ready or live-ready.
3. Paper/live practical flags cannot be inferred from stale artifacts, legacy
   strings, or diagnostic helpers.
4. Execution-tree closed-loop admission cannot bypass the live plane.
5. `workflow-status`, `policy-training-status`, and factor candidate exports
   all agree on the same lifecycle semantics.
6. At least one rooted profitability-factor chain is proved on current evidence
   to traverse the real runtime closed loop with correct fail-closed behavior at
   each stage.
7. Current dirty-tree modifications related to this objective are verified or
   isolated; otherwise the exact state under audit is untrusted.

## Baseline Evidence Read So Far

- `AGENT.md`
- `AGENTS.md`
- `support/docs/plans/2026-05-12-hotplug-personal-data-release-handoff-todo.md`
- `support/docs/plans/2026-05-25-regime-conditioned-profitability-gate-rebuild-plan.md`
- `support/docs/plans/2026-05-25-board-b-current.md`
- `support/docs/plans/2026-05-12-board-b-profit-factor-current.md`
- `src/application/factor_lifecycle/profitability_admission.rs`
- `src/application/entry_models/training_export.rs`
- `src/application/orchestration/factor_candidate.rs`
- `src/application/orchestration/workflow_status.rs`
- `src/application/orchestration/execution_tree.rs`
- `src/application/regime/consumer_bundle_adapter.rs`

## Current Gap / Vulnerability Ledger

### V-001: objective-level completion is still unproven

- Severity: critical
- Evidence:
  - Board B audit still blocked by active claims.
  - Release handoff explicitly says completion is not proven.
  - No fresh exact-tree end-to-end proof packet has been rerun in this audit.
- Risk:
  - claiming completion from partial historical packets would be false.
- Next:
  - build a current requirement-by-requirement evidence matrix;
  - identify which links are proven only by historical packets and which are
    missing on the current tree.

### V-002: current tree still has broad unverified changes in objective-related owners

- Severity: high
- Evidence:
  - `src/belief_core/ranking_label.rs`
  - `src/application/orchestration/structural_playbook.rs`
  - multiple `support/scripts/auto_quant_external/*`
  - multiple `support/scripts/research/*`
- Risk:
  - new branch-path canonicalization or helper changes could fix one mismatch
    while creating another, and there is no fresh verification bundle yet.
- Next:
  - inspect these diffs against the lifecycle contract;
  - run focused tests on each touched owner before treating the dirty tree as a
    valid baseline.

### V-003: closed-loop proof is fragmented across older packets rather than re-proved on the current tree

- Severity: high
- Evidence:
  - older handoff packets prove isolated links;
  - current audit has not yet re-executed a fresh same-tree proof chain.
- Risk:
  - current code may have drifted away from the last accepted packets.
- Next:
  - revalidate the narrowest high-signal command/test set for lifecycle,
    execution-tree admission, workflow-status normalization, and path-ranker
    branch-path canonicalization.

### V-004: imported branch/context surfaces still deserve bypass review

- Severity: medium
- Evidence:
  - the earlier implementation in
    `src/application/regime/consumer_bundle_adapter.rs` let imported
    strategy-library metadata set `decision_state=accepted` and propagate
    `trade_usable=true` into advisory hints.
- Risk:
  - if an upstream manifest marks practical flags true without runtime live-plane
    revalidation, downstream consumers can over-trust imported metadata and
    promote Pre-Bayes/BBN gate quality from an advisory branch trace.
- Next:
  - keep the new regression in the focused verification set whenever
    strategy-library metadata semantics change;
  - still re-prove that no other advisory import surface can mutate live-plane
    readiness without current runtime revalidation.
- Current readback:
  - `load_optional_or_strategy_library()` can source a strategy-library manifest
    when no explicit bundle path is provided, but
    `strategy_library_branch_context_to_adapter()` is now forced advisory-only:
    `decision_state=auto_quant_strategy_library_branch_context`,
    `latest_decision.trade_usable=false`,
    `bbn_evidence_hint.regime_trade_usable=false`, and
    `consumer_hints.trade_usable=false` even if the imported manifest claims
    `promotion_allowed=true` / `trade_usable=true`.
  - Focused regression
    `strategy_library_import_does_not_promote_practical_gate_from_metadata_flags`
    reproduced the old fail-open path, then passed after the fix.

### V-005: branch-path canonicalization is an active dirty-tree change and must be verified against downstream score matching

- Severity: medium
- Evidence:
  - current diff changes score-key derivation and canonicalizes branch paths in
    `src/belief_core/ranking_label.rs` and
    `src/application/orchestration/structural_playbook.rs`.
- Risk:
  - this can repair same-branch score matching, but it can also silently merge
    distinct provenance variants or break compatibility with retained history
    rows and external score artifacts.
- Next:
  - run the new focused tests plus downstream score-apply tests that cover
    current/history row matching for canonical branch input against exact
    provenance-prefixed persisted rows.

### V-006: release blocker tracking drifted away from the current authoritative audit

- Severity: medium
- Evidence:
  - older tracker text still named unresolved
    `source_origin_matches_selected_source` and
    `release_version_tag_available`;
  - fresh
    `python3 support/scripts/release_readiness_audit.py --compact --check-remotes`
    now reports unresolved `worktree_clean_for_release` and `remote_readback`,
    with `release_version_tag_available` skipped behind that remote gate.
- Risk:
  - repeating stale blocker names can send the next turn to the wrong fix lane
    and overstate what is actually knowable from the current network state.
- Next:
  - update all active closure trackers to quote the latest release audit output;
  - treat release claims as blocked by dirty worktree plus remote readback until
    the exact gate output changes again.

### V-007: factor-closure evidence is time-variant and already worsened during this audit

- Severity: medium
- Evidence:
  - the earlier 2026-05-27 factor packet reported `active_claims=10`,
    `live_factor_processes=0`;
  - the fresh rerun now reports `active_claims=13`,
    `live_factor_processes=2`, `blocking_reasons=["active_claims",
    "live_factor_processes"]`.
- Risk:
  - completion language based on stale same-day packets is not reliable even
    within one audit session; factor closure can regress while docs still look
    unchanged.
- Next:
  - quote fresh factor audit output in the active tracker;
  - if a stronger factor-completion claim is ever attempted, require same-turn
    rerun evidence rather than cached `/tmp` artifacts from earlier in the day.

### V-008: candidate-pack selection surfaces were still optimizing statistical attractiveness ahead of post-friction learnability

- Severity: medium
- Evidence:
  - `support/scripts/research/factor_candidate_pack.py` transfer scoring used
    `density + sharpe + breadth` but did not weight
    `long_run_expectancy_after_declared_friction`.
  - `support/scripts/research/factor_candidate_resolver.py` buildable candidate
    surfaces exposed `aggregate_trade_count`, `aggregate_label`, and
    `transfer_status`, but not `learning_admission_status` or
    declared-friction expectancy.
- Risk:
  - agents and humans choosing the next training lane can systematically prefer
    high-density/high-sharpe candidates that are still cost-unproven, which
    reinforces the exact failure mode where factor training looks productive but
    repeatedly fails practical closure.
- Next:
  - keep declared-friction profitability on the default buildable-candidate
    surface;
  - continue auditing other training-direction helpers for raw-profit or
    sharpe-only ranking keys.
- Current readback:
  - transfer scoring now adds a declared-friction profitability component and
    explicit profitability blockers/status.
  - buildable candidate surfaces now expose
    `learning_admission_status` and
    `long_run_expectancy_after_declared_friction`, with fallback compatibility
    for older curated packs that lack lifecycle fields.

## Immediate Verification Queue

1. Build a requirement-by-requirement current-tree evidence matrix for the full
   user objective.
2. Identify which links are only historically proven and which need a fresh
   exact-tree rerun.
3. Decide whether a new code-fix slice is actually required or whether the next
   blocker is missing runtime evidence rather than logic gaps.

## Focused Verification Completed

Rust focused tests:

- `cargo test --quiet workflow_factor_profitability_lifecycle -- --nocapture`
  -> pass (`3` tests)
- `cargo test --quiet policy_training_status_does_not_treat_legacy_execution_gate_pass_as_live_trade_usable -- --nocapture`
  -> pass (`1` test)
- `cargo test --quiet execution_tree_closed_loop_branch_admission_keeps_strict_trend_pullback_wait_for_reversion_observe_only -- --nocapture`
  -> pass (`1` test)
- `cargo test --quiet ranker_target_export_canonicalizes_provenance_prefixed_branch_paths -- --nocapture`
  -> pass (`1` test)
- `cargo test --quiet apply_external_scores_matches_provenance_prefixed_rows_from_canonical_branch_input -- --nocapture`
  -> pass (`1` test)
- `cargo test --quiet strategy_library_import_does_not_promote_practical_gate_from_metadata_flags -- --nocapture`
  -> pass (`1` test)
- `cargo test --quiet application::regime::consumer_bundle_adapter::tests:: -- --nocapture`
  -> pass (`7` tests)

Python/support-script focused tests:

- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  -> pass (`42/42`)
- `python3 -m unittest support.scripts.research.tests.test_mim_cost_window_feedback_builder -v`
  -> pass (`2/2`)
- `python3 -m unittest support.scripts.auto_quant_external.tests.test_fetch_external_ibkr_chunking support.scripts.auto_quant_external.tests.test_freqtrade_backtest_trade_export support.scripts.auto_quant_external.tests.test_next_slice_helpers -v`
  -> pass (`27/27`)
- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_pack -v`
  -> pass (`17/17`)
- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver -v`
  -> pass (`9/9`)

Current-turn compact audits:

- `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-goal-20260527-done-now.json`
  -> pass, but `completion_ready=false` because heavy gates remain skipped by
  default.
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-goal-20260527-factor-now.json`
  -> `status=needs_attention`, `active_claims=13`, `live_factor_processes=2`,
  `promotion_allowed_true=0`, `trade_usable_true=0`.
- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-goal-20260527-release-now.json`
  -> `status=needs_fix`, unresolved
  `worktree_clean_for_release`, `remote_readback`; tag availability still
  skipped behind the remote-readback gate.

Current-tree runtime smoke:

- Run root: `/tmp/ict-engine-objective-audit-now.H99bU1`
- Commands:
  - `cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-objective-audit-now.H99bU1/state --human`
  - `cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-objective-audit-now.H99bU1/state --refresh --agent`
  - `cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-objective-audit-now.H99bU1/state --output-format agent`
- Result:
  - `workflow-status`: `execution_gate_status=execution_observe_only`,
    `factor_profitability_lifecycle.live_trade_status=blocked`,
    `promotion_allowed=false`, `trade_usable=false`
  - `policy-training-status`: lifecycle summary remains
    `learning_admitted=0 paper_ready=0 live_ready=0 trade_usable=false`
- Interpretation:
  - current tree still appears fail-closed on the demo path;
  - this is good evidence against an obvious promotion regression, but it is
    not proof that the full objective is complete.

## Progress Log

- 2026-05-27: created current objective-completion audit ledger from the
  current worktree and baseline docs. Initial verdict remains `not proven`.
- 2026-05-27: completed focused Rust/Python verification and a fresh `/tmp`
  runtime smoke. No immediate fail-open regression reproduced; objective still
  remains `not proven` because end-to-end current-tree completion evidence is
  incomplete.
- 2026-05-27: fresh factor/release reruns changed the blocker surface again.
  Factor closure regressed to `active_claims=13`, `live_factor_processes=2`;
  release closure now fails on `worktree_clean_for_release` plus
  `remote_readback`, with tag availability skipped behind the remote gate.
- 2026-05-27: the current-turn compact reruns still show no promotion surface:
  `done_definition_audit` remains partial without heavy gates,
  `factor_claim_terminalization_audit` still has `promotion_allowed_true=0` and
  `trade_usable_true=0`, and the fresh `/tmp` demo smoke remains
  `execution_observe_only` / `live_trade_status=blocked`.
- 2026-05-27: reproduced and fixed a real advisory-import loophole.
  Strategy-library manifests can no longer self-assert `accepted` practical
  status or elevate BBN gate quality through imported `trade_usable=true`
  metadata; the new regression and focused adapter suite both pass.
- 2026-05-27: reproduced and fixed a training-direction surface bug.
  Candidate-pack transfer scoring and buildable candidate summaries now surface
  declared-friction profitability and learning-admission state instead of
  primarily steering selection through density/sharpe/breadth alone.
