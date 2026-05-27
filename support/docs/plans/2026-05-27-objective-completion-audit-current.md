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

1. Board B ownership is still crowded. The authoritative current readback is
   the coordinated snapshot at
   `/private/tmp/ict-engine-goal-20260527-closure-snapshot/objective_closure_snapshot.json`.
   Its factor child is time-variant within the day, but it still remains
   blocked on unresolved active-claim debt and therefore prevents truthful
   closure. The latest focused factor audit now proves the debt is mostly not
   runtime occupancy: `active_claims=11`, `live_factor_processes=1`,
   `active_claims_without_live_process=10`,
   `wait_only_active_claims_without_live_process=3`.
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

### V-002: current tree still has broad partially verified changes in objective-related owners

- Severity: high
- Evidence:
  - `src/belief_core/ranking_label.rs`
  - `src/application/orchestration/structural_playbook.rs`
  - multiple `support/scripts/auto_quant_external/*`
  - multiple `support/scripts/research/*`
  - focused suites now pass for `release_readiness_audit.py`,
    `factor_candidate_pack.py`, and `factor_candidate_resolver.py`, but the
    broader dirty-tree surface is still much larger than the rerun set.
- Risk:
  - verified hotspots are narrower now, but unrerun dirty owners can still hide
    branch-path, provider, or training-surface regressions.
- Next:
  - keep shrinking the unverified owner set;
  - do not treat the broad dirty tree as a valid completion baseline until the
    exact end-to-end chain is re-proved from a selected source slice.

### V-003: closed-loop proof is fragmented across older packets rather than re-proved on the current tree

- Severity: high
- Evidence:
  - older handoff packets prove isolated links;
  - current audit still has no fresh same-tree green closure chain;
  - the strongest available TOMAC root was rerun in this turn via
    `python3 support/scripts/research/tomac_tod_balanced_trade_label_sidecar.py --exact-root /tmp/ict-engine-tomac-tod-balanced-practical-repair-20260526T214903+0800/top1965_comp40_floor50_exact_suppressed --output-dir /tmp/ict-engine-tomac-practical-closure-20260527T165046+0800/sidecar-rerun`
    and remained fail-closed with `trade_count_parity=true`,
    `purged_cv_gate=reject`, bounded provider parity now proven, and remaining
    downstream blockers narrowed to
    `frequency.max_gap_days_gt_allowed:350.00>3.00`,
    `raw_scored_mature_rows_lt_30`, `production_validation_rows_lt_30`,
    `observation_validation_rows_lt_30`,
    `execution_readiness_lt_0.65`,
    `transition_hazard_gte_0.60`, and `actionable_false`.
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
  - older tracker text named one release blocker set, while later same-day
    reruns named a different blocker set;
  - the authoritative source is now the coordinated snapshot at
    `/private/tmp/ict-engine-goal-20260527-closure-snapshot/objective_closure_snapshot.json`,
    whose release child records both `report_timestamp` and the exact current
    `unresolved` gate list;
  - depending on live network/source state, the unresolved set can move between
    source-parity/tag-reuse blockers and remote-readback blockers.
- Risk:
  - repeating stale blocker names can send the next turn to the wrong fix lane
    and overstate what is actually knowable from the current network state.
- Next:
  - update all active closure trackers to cite the latest coordinated snapshot
    instead of copying mutable release gate names into prose;
  - treat release claims as blocked by dirty worktree, unpushed source drift,
    and version/tag reuse until the exact gate output changes again.

### V-007: factor-closure evidence is time-variant within the same audit day

- Severity: medium
- Evidence:
  - same-day reruns have already produced multiple different factor surfaces;
  - the coordinated snapshot now records the factor child's
    `report_timestamp`, `blocking_reasons`, and `attention_by_owner` so the
    latest truth can be read from one place;
  - despite numeric drift, the stable fact is unchanged: factor closure is
    still blocked by unresolved active claims and remains non-complete.
  - the same-turn classifier fix still matters: one prior live-process blocker
    was a diagnostic false positive
    (`tomac_tod_balanced_provider_parity_probe.py`), and that probe no longer
    inflates `live_factor_processes`.
- Risk:
  - completion language based on stale same-day packets is not reliable even
    within one audit session; factor closure can regress while docs still look
    unchanged.
- Next:
  - cite the coordinated snapshot in the active tracker instead of copying raw
    factor counts into prose;
  - if a stronger factor-completion claim is ever attempted, require same-turn
    rerun evidence rather than cached `/tmp` artifacts from earlier in the day.
- Current concurrency readback:
  - the latest factor audit still shows no invalid active claim surface;
  - closure is still blocked because the coordinated snapshot's factor child
    remains non-pass and still belongs to live `codex` attention claims, so the
    repo still lacks a clean same-turn factor-closure surface;
  - the latest focused audit now proves only one active claim owns live
    runtime, while ten active claims do not and three of those are already
    classified as wait-only debt.

### V-011: reusable strategy-library provenance was still leaking caller-local path assumptions

- Severity: medium
- Evidence:
  - `support/scripts/research/factor_candidate_pack.py` previously recorded
    `metadata.source_artifact=str(zip_path)` when converting a `freqtrade`
    backtest zip into strategy-library evidence;
  - absolute caller-local zip inputs therefore embedded workstation-specific
    paths into exported evidence assets;
  - the strategy-library projection dropped `source_artifact`, weakening
    provenance while still leaving the lower-layer leak unaddressed.
- Risk:
  - clone users can receive supposedly reusable evidence that still encodes a
    maintainer-local path contract;
  - provenance becomes less trustworthy because the unsafe lower-layer field is
    present but not consistently projected.
- Next:
  - keep the new portable-provenance regressions in the focused verification
    set;
  - continue checking other evidence/export surfaces for absolute-path leakage
    before any clone-portability completion claim.
- Current readback:
  - the builder now normalizes absolute zip inputs to portable
    `metadata.source_artifact="backtest.zip"` and preserves the same field in
    emitted strategy-library manifests;
  - focused suites
    `support.scripts.research.tests.test_factor_candidate_pack` and
    `support.scripts.research.tests.test_factor_candidate_resolver` now pass
    `36` tests.

### V-012: balanced-TOD sidecar was inventing downstream blockers instead of hydrating same-root evidence

- Severity: medium
- Evidence:
  - `support/scripts/research/tomac_tod_balanced_trade_label_sidecar.py`
    previously hard-coded `provider_parity=false`,
    `raw_scored_mature_rows=0`, `production_validation_rows=0`,
    `observation_validation_rows=0` in the admission summary passed to
    `simulated_feedback_admission_guard.py`;
  - the sibling downstream exact root already carried real same-root evidence in
    `checks/terminal_metrics.json` and `path_ranker_model/trainer_artifact.json`;
  - new focused regression
    `test_run_sidecar_hydrates_downstream_summary_from_sibling_artifacts`
    failed before the fix and passed after the owner was patched.
- Risk:
  - the practical-closure audit could overstate downstream failure by reusing
    synthetic placeholder values even when the exact root already had richer
    validation/readiness truth.
- Next:
  - keep the hydrated readback path in the focused verification set;
  - keep the provider-parity proof path in the focused verification set;
  - keep frequency semantics pair-aware for basket labels instead of reverting
    to aggregate daily-count gating.
- Current readback:
  - the sidecar now hydrates validation/readiness/actionability from the latest
    sibling `downstream-exact-tomac-tod-balanced*` root and consumes
    `checks/provider_parity_probe.json` when present;
  - a bounded live IBKR probe now exists at
    `checks/provider_parity_probe.json` with
    `decision=bounded_provider_parity_recent_rows_present` for
    `MNQ/MYM/MGC` on `1 D`;
  - rerunning the real same-root sidecar preserved the actual downstream state
    for this root: `raw_scored_mature_rows=1`,
    `production_validation_rows=1`, `observation_validation_rows=0`,
    `execution_readiness=0.4606046164602364`,
    `transition_hazard=0.6248959443126174`,
    `execution_candidate_actionable=false`;
  - the guard no longer misclassifies the multi-pair basket on aggregate daily
    trade count; after the frequency-owner fix the only surviving frequency
    blocker is the real pair-scoped gap
    `frequency.max_gap_days_gt_allowed:350.00>3.00`.

### V-010: current-turn heavy done-definition proof can lag behind blocker drift

- Severity: low
- Evidence:
  - `done_definition_audit.py --compact` finished immediately in this
    continuation;
  - `done_definition_audit.py --run-all-heavy --compact` lagged behind the
    latest factor/release blocker polls before eventually landing green at
    `/tmp/ict-engine-goal-20260527-done-heavy-live.json` with
    `completion_ready=true`, `evidence_level=full_enabled_gate_coverage`,
    `pass_count=8`, `fail_count=0`.
- Risk:
  - a mixed proof bundle can accidentally combine stale heavy green evidence
    with newer factor/release blocker truth and overstate how much of the
    closure chain was proved in the same instant.
- Next:
  - keep light and heavy proof timestamps explicit;
  - keep distinguishing the green done-definition bundle from the still-red
    factor/release blockers rather than collapsing them into one completion
    verdict.

### V-009: one tracker test selector had already drifted away from the current tree

- Severity: low
- Evidence:
  - the tracker previously named
    `cargo test --quiet ranker_target_export_canonicalizes_provenance_prefixed_branch_paths -- --nocapture`;
  - on the current tree that selector matches zero tests;
  - the exact current test is
    `cargo test --quiet ranker_target_export_preserves_exact_provenance_prefixed_branch_paths -- --nocapture`,
    which passes.
- Risk:
  - a stale selector can create a false impression that current branch-path
    protection was re-proved when the command actually exercised nothing.
- Next:
  - keep the exact current test names in the tracker;
  - treat zero-test filtered runs as weak evidence that must be corrected before
    any completion claim.

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
  - the default `--list-buildable` surface is now fail-closed for training
    direction: it returns `buildable_count=0`, `legacy_excluded_count=8`, and
    no default candidates when all reusable packs require synthesized legacy
    lifecycle readback.
  - legacy synthesized packs remain inspectable only through explicit opt-in:
    `--list-buildable --include-legacy-buildable` returns the same `8`
    inspection-only legacy packs with `surface_freshness=legacy_candidate_pack_synthesized_lifecycle`.

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
- `cargo test --quiet ranker_target_export_preserves_exact_provenance_prefixed_branch_paths -- --nocapture`
  -> pass (`1` test)
- `cargo test --quiet target_export_uses_exact_branch_trade_direction_over_snapshot_fallback -- --nocapture`
  -> pass (`1` test)
- `cargo test --quiet apply_external_scores_matches_provenance_prefixed_rows_from_canonical_branch_input -- --nocapture`
  -> pass (`1` test)
- `cargo test --quiet execution_candidate_preserves_trace_branch_path_for_neutral_no_trade -- --nocapture`
  -> pass (`1` test)
- `cargo test --quiet execution_candidate_preserves_strict_trend_pullback_trace_path_without_report_branch_path_but_does_not_promote -- --nocapture`
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
  -> pass (`19/19`)

Current-turn compact audits:

- `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-goal-20260527-done-now.json`
  -> pass, but `completion_ready=false` because heavy gates remain skipped by
  default.
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-goal-20260527-factor-clusters.json`
  -> earlier same-turn cluster checkpoint:
  `status=needs_attention`, `active_claims=12`,
  `invalid_active_claims=0`, `live_factor_processes=4`,
  `promotion_allowed_true=0`, `trade_usable_true=0`,
  `attention_groups.by_owner={"codex":12}`,
  `attention_clusters[0].claim_count=2`.
- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-goal-20260527-release-resume3.json`
  -> `status=needs_fix`, unresolved
  `worktree_clean_for_release`,
  `remote_readback`; `release_version_tag_available` remains skipped behind the
  remote gate.

Earlier same-day runtime smoke (not rerun in this continuation):

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
  An earlier same-turn checkpoint moved factor closure back to
  `active_claims=12`, `invalid_active_claims=0`,
  `live_factor_processes=4`, with `attention_groups.by_owner={"codex":12}` and
  a duplicate `NQCadenceLift` family cluster; release closure now fails on
  `worktree_clean_for_release` and `remote_readback`, with tag availability
  still blocked behind the remote gate.
- 2026-05-27: the latest compact factor rerun in this continuation drifted
  again to `active_claims=10`, `invalid_active_claims=0`,
  `live_factor_processes=2`, and `attention_groups.by_owner={"codex":10}`.
  This removed the earlier duplicate-family cluster but still leaves the repo
  far from a clean same-turn practical-closure surface.
- 2026-05-27: added `support/scripts/objective_closure_snapshot.py`, a compact
  read-only aggregator that now writes one coordinated `/tmp` bundle for the
  canonical quickstart chain plus the live done/factor/release audit outputs.
  The safe default snapshot is now available at
  `/private/tmp/ict-engine-goal-20260527-closure-snapshot/objective_closure_snapshot.json`;
  a heavier `--run-all-heavy` attempt currently fails closed with a structured
  timeout snapshot instead of crashing.
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
- 2026-05-27: patched the human `--list-buildable` summary to surface
  `legacy_excluded_count` and print the explicit
  `--include-legacy-buildable` hint; the matching resolver regression now
  passes in the same focused suite.
