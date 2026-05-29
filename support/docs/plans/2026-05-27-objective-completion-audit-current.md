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
   `/tmp/ict-engine-goal-20260527-closure-snapshot-current6/objective_closure_snapshot.json`.
   Its factor child is time-variant within the day, but it still remains
   blocked on unresolved active-claim debt and therefore prevents truthful
   closure. The latest coordinated snapshot now reports
   `active_claims=5`, `live_factor_processes=1`,
   `active_claims_without_live_process=4`,
   `wait_only_active_claims_without_live_process=0`, with
   `attention_by_actionability={active_claim_debt:3, live_runtime_owner:1,
   stale_safe_takeover_candidate:1}`.
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
    `/tmp/ict-engine-goal-20260527-closure-snapshot-portable4/objective_closure_snapshot.json`,
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
  - the latest coordinated snapshot now shows one live factor process, four
    active claims outside live runtime ownership, no remaining
    `wait_only_without_live_process` rows, and one stale-safe takeover head on
    the canonical XLC claim;
  - this surface is concurrently mutating: even after coordinated packet
    portability fixes, new claims appeared before the next rerun, so blocker
    counts can worsen while old debt is still being reduced.

### V-013: coordinated closure packet portability had a hidden factor-child gap

- Severity: medium
- Evidence:
  - the parent `objective_closure_snapshot.json` had already become
    packet-portable, but the factor child compact payload still used local
    runtime paths such as `claims_dir=/tmp/...`, `run_root=/private/tmp/...`,
    and `exit_file=/private/tmp/...`;
  - the current packet contract now passes `--portable-paths` into
    `factor_claim_terminalization_audit.py`, and the fresh `portable4` packet
    rewrites those fields to packet-safe labels such as
    `claims_dir="ict-engine-agent-claims/board-b-factor-refinement"` and
    `run_root="ict-engine-..."`.
- Risk:
  - without this fix, the coordinated bundle looked reusable at the parent
    level while still embedding workstation-local tmp roots one layer below.
- Next:
  - keep the new factor child packet-safe regressions in the focused suite;
  - keep checking other child payloads for similar clone-portability drift.

### V-014: coordinated closure snapshot originally omitted the factor debt split, weakening packet-to-packet coordination

- Severity: medium
- Evidence:
  - the factor compact child already exposed
    `active_claims_without_live_process`,
    `wait_only_active_claims_without_live_process`,
    `stale_safe_takeover_candidates`, and
    `attention_groups.by_actionability`;
  - the parent `objective_closure_snapshot.json` originally dropped those
    fields and kept only the coarser
    `active_claims/live_factor_processes/blocking_reasons/attention_by_owner`
    surface;
  - the fresh same-turn coordinated snapshot at
    `/tmp/ict-engine-goal-20260528-closure-snapshot-debtsplit/objective_closure_snapshot.json`
    now proves the lifted fields are present in the factor child surface:
    `active_claims_without_live_process=10`,
    `wait_only_active_claims_without_live_process=2`,
    `stale_safe_takeover_candidates=8`, and
    `attention_by_actionability={active_claim_debt=1, live_runtime_owner=5, stale_safe_takeover_candidate=8, wait_only_without_live_process=1}`.
- Risk:
  - without this lift, the supposedly coordinated closure packet still required
    a second manual factor-child inspection to distinguish runtime occupancy
    from pure claim debt, making reuse across turns and agents weaker.
- Next:
  - keep the new `objective_closure_snapshot.py` regression in the focused
    suite;
  - continue treating the latest same-turn snapshot as authoritative because
    the factor surface is still drifting even though the packet contract is now
    stronger.

### V-015: coordinated closure snapshot still required a second factor-child read to get the first cleanup queue

- Severity: medium
- Evidence:
  - after the debt-split lift, the coordinated snapshot still exposed only the
    factor blocker shape, not the first exact cleanup targets;
  - the fresh same-turn coordinated snapshot at
    `/tmp/ict-engine-goal-20260528-closure-snapshot-queue/objective_closure_snapshot.json`
    now proves the factor child surface includes `attention_action_queue` with
    explicit:
    - `externalize_wait_only_claims`
    - `stale_safe_takeover_claims`
    - `live_runtime_run_roots`
  - the current snapshot-owned queue head is the wait-only claim
    `20260527T220432+0800-codex-tomac-tod-balanced-validation-maturity-materialization.claim`,
    while the same packet also names the current live run roots and stale
    takeover queue.
- Risk:
  - without this lift, every next-turn cleanup still required a second manual
    factor-child read, weakening the promised coordination/reuse value of the
    parent evidence packet.
- Next:
  - keep the new snapshot queue regression in the focused suite;
  - use the coordinated packet as the default first read for factor-closure
    cleanup, but still rerun it same-turn before any stronger closure claim
    because the queue and counts continue to drift.

### V-016: coordinated closure snapshot originally dropped child-level repair instructions for done and release

- Severity: medium
- Evidence:
  - the earlier parent packet preserved release unresolved gate ids and
    done-definition skipped gates, but still dropped the child `next_action`
    instructions that make those blockers actionable;
  - the fresh same-turn coordinated snapshot at
    `/tmp/ict-engine-goal-20260528-closure-snapshot-actions/objective_closure_snapshot.json`
    now proves the lifted fields exist:
    - `audits.done_definition.surface.next_action`
    - `audits.release_readiness.surface.unresolved_next_actions`
    - `summary.child_next_actions`
- Risk:
  - without these lifts, one packet could tell the next turn that completion is
    blocked, yet still force another child-audit read to know whether the next
    step is heavy verification, worktree slicing, or remote readback repair.
- Next:
  - keep the new snapshot actionability regression in the focused suite;
  - continue using the coordinated packet as the first read, but keep it
    same-turn fresh because both factor and release state still drift.

### V-017: parent summary previously remained generic even after child actions were preserved

- Severity: medium
- Evidence:
  - the earlier coordinated snapshot already preserved nested
    `child_next_actions`, but summary-level `next_action` still remained the
    generic `rerun the blocked child audits after fixing the named blocker surfaces`;
  - the fresh same-turn coordinated snapshot at
    `/tmp/ict-engine-goal-20260528-closure-snapshot-priority/objective_closure_snapshot.json`
    now proves the parent summary includes ordered
    `prioritized_next_actions` for done-definition, factor closure, and the two
    release blockers.
- Risk:
  - without a top-level ordered action list, the evidence bundle still forced
    the next turn to manually inspect nested child fields before deciding what
    to do first, which weakened its value as a reusable closure packet.
- Next:
  - keep the new priority-list regression in the focused suite;
  - continue treating the coordinated snapshot as the default first read, but
    keep rerunning it same-turn because the factor and release surfaces still
    drift.

### V-018: parent summary previously still required a nested factor-queue read to identify the first concrete factor target

- Severity: medium
- Evidence:
  - the earlier parent summary preserved a generic factor action, but still hid
    the exact wait-only queue head, stale-safe takeover head, and live runtime
    head inside nested `attention_action_queue`;
  - the fresh same-turn coordinated snapshot at
    `/tmp/ict-engine-goal-20260528-closure-snapshot-factorheads/objective_closure_snapshot.json`
    now proves the summary-level `prioritized_next_actions` contains all three
    concrete factor targets directly.
- Risk:
  - without this lift, the packet still forced nested factor-surface parsing
    before real blocker cleanup could start, weakening its consumer/maintainer
    value in time-variant Board B conditions.
- Next:
  - keep the new factor-head priority regression in the focused suite;
  - continue rerunning the coordinated snapshot same-turn because the queue head
    and live roots still move as claims and runtimes change.

### V-019: coordinated packet freshness previously had to be inferred from nested child timestamps

- Severity: medium
- Evidence:
  - earlier packets exposed child `report_timestamp` only inside each child
    surface, so the user still had to infer whether blocker counts were stale;
  - the fresh same-turn coordinated snapshot at
    `/tmp/ict-engine-goal-20260528-closure-snapshot-freshness/objective_closure_snapshot.json`
    now proves the parent summary includes both `child_report_timestamps` and
    `child_report_age_seconds`;
  - that same packet also demonstrates why this matters: factor closure changed
    from runtime-occupied to pure claim debt within the same session
    (`live_factor_processes=0`, `active_claims=6`).
- Risk:
  - without explicit freshness data, operators can over-trust an older packet
    and chase blockers that have already moved.
- Next:
  - keep the new freshness regression in the focused suite;
  - treat any packet with materially older child ages as advisory only and
    rerun before making stronger completion claims.

### V-020: parent priority list previously hid secondary live factor roots

- Severity: medium
- Evidence:
  - the 2026-05-28 live factor child surface listed two live runtime roots:
    `pid 35142` for
    `ict-engine-tomac-liquidity-sweep-adx-liquidity-pool-context-reopen-await-launch-20260527T231247+0800`
    and `pid 35854` for
    `ict-engine-tomac-wpr-adx-reference-hurst-profile-range-compression-release-liveprep-20260527T230800`;
  - before the fix, `summary.prioritized_next_actions` lifted only the first
    `live_runtime_run_roots[0]`, so a parent-packet consumer could wait on the
    liquidity-pool root while missing the WPR/reference-Hurst live owner;
  - the regenerated snapshot at
    `/tmp/ict-engine-goal-20260528-continuation-snapshot-after-multilive/objective_closure_snapshot.json`
    now lists both live runtime heads at the parent summary level.
- Risk:
  - without this, the coordinated evidence packet was not fully self-contained
    for multi-runtime factor closure; consumers still needed nested child JSON
    parsing to discover all current live owners.
- Current readback:
  - `summarize_snapshot()` now lifts up to three live runtime heads into
    `summary.prioritized_next_actions` to preserve compactness while avoiding
    single-head blindness;
  - `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
    passed `9/9` after the regression was added.
- Next:
  - continue treating the packet as non-completion evidence until both live
    roots terminalize and the factor child reports no active/live blockers;
  - rerun the coordinated snapshot before any stronger claim because the live
    runtime set is still moving.

### V-021: parent priority list duplicated wait-only stale-safe factor claims

- Severity: low
- Evidence:
  - the fresh same-turn coordinated snapshot at
    `/tmp/ict-engine-goal-20260528-codex-current-live/objective_closure_snapshot.json`
    remained red, but also showed a packet UX defect: wait-only claims that
    were also stale-safe takeover candidates appeared twice in
    `summary.prioritized_next_actions`, once as
    `wait_only_stale_safe_takeover_candidate` and again as
    `stale_safe_takeover_queue_head`;
  - this did not change completion truth, but it made the compact parent packet
    less lightweight and could make a next agent review the same claim twice.
- Risk:
  - duplicated parent actions weaken the packet's role as the single first-read
    coordination surface and can waste cleanup turns on already surfaced claim
    files.
- Current readback:
  - `summarize_snapshot()` now tracks factor claim files already surfaced by
    wait-only actions and skips duplicate stale-safe parent actions for the same
    claim file;
  - the regression
    `test_summarize_snapshot_deduplicates_wait_only_stale_factor_claim_actions`
    was added, and
    `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
    passed `13/13`;
  - the regenerated packet at
    `/tmp/ict-engine-goal-20260528-codex-current-dedup/objective_closure_snapshot.json`
    now lists four wait-only stale-safe claim actions plus two non-wait stale
    takeover actions, without duplicating the same wait-only claim files.
- Next:
  - keep this regression in the focused packet suite;
  - continue treating the packet as non-completion evidence because factor
    closure, done-definition heavy proof, and release readiness are still red.

### V-022: fresh active factor claims were phrased like terminalization targets

- Severity: medium
- Evidence:
  - the fresh same-turn coordinated snapshot at
    `/tmp/ict-engine-goal-20260528-codex-cont-current/objective_closure_snapshot.json`
    had no stale-safe factor queue and no live factor process, but still exposed
    a generic factor action of `terminalize or externalize active claims`;
  - direct claim inspection showed the remaining active claim was a fresh setup
    packet (`codex-tomac-practical-continuation-20260528T091403.claim`) created
    minutes earlier, so terminalization would have been the wrong default
    coordination instruction;
  - the later live packet at
    `/tmp/ict-engine-goal-20260528-codex-cont-fresh-action/objective_closure_snapshot.json`
    proves the repaired shape: the factor child now reports
    `fresh_active_claims_without_live_process=3` and the parent priority list
    says to wait for/inspect each fresh claim before terminalizing.
- Risk:
  - a downstream maintainer could treat fresh claim ownership as stale cleanup
    debt, collide with another agent's newly created lane, or erase useful
    coordination state before the owner has a chance to terminalize it.
- Current readback:
  - `factor_claim_terminalization_audit.py` now distinguishes
    `fresh_active_claims_without_live_process` from wait-only/stale cleanup
    targets and emits a `fresh_active_claims_without_live_process` queue in the
    compact child packet;
  - `objective_closure_snapshot.py` now lifts those fresh claim heads into
    parent `summary.prioritized_next_actions` with the reason
    `fresh_active_claim_without_live_runtime`;
  - focused verification passed:
    `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
    (`64/64`) and
    `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
    (`14/14`).
- Next:
  - keep fresh active claims as wait/inspect targets until they become stale,
    terminalized, or live-runtime owners;
  - continue treating the overall objective as not complete because the same
    live packet still has `trade_usable_true=0`, skipped heavy done-definition
    gates, and red release readiness.

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
  again to `active_claims=14`, `invalid_active_claims=0`,
  `live_factor_processes=1`, and `attention_groups.by_owner={"codex":14}`.
  This still leaves the repo far from a clean same-turn practical-closure
  surface even though the live runtime count is smaller than earlier in the day.
- 2026-05-27: added `support/scripts/objective_closure_snapshot.py`, a compact
  read-only aggregator that now writes one coordinated `/tmp` bundle for the
  canonical quickstart chain plus the live done/factor/release audit outputs.
  The safe default snapshot is now available at
  `/tmp/ict-engine-goal-20260527-closure-snapshot-portable4/objective_closure_snapshot.json`;
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
- 2026-05-27: coordinated packet portability now holds at both the parent and
  factor-child compact layers. The parent snapshot stores `python3`, relative
  child evidence filenames, and no workstation-local repo/output paths; the
  factor child compact packet now stores packet-safe `claims_dir`, `run_root`,
  and `exit_file` labels instead of local tmp roots.
- 2026-05-28: refreshed the authoritative coordinated snapshot at
  `/tmp/ict-engine-goal-20260528-closure-snapshot-current1/objective_closure_snapshot.json`.
  The objective is still `not_complete`: `done_definition` is green only at the
  light level with `completion_ready=false`, `factor_closure` is still blocked
  by `active_claims=2` with `live_factor_processes=0`, and release readiness
  still fails `worktree_clean_for_release` plus `remote_readback`. The latest
  factor surface still has `promotion_allowed_true=0` and
  `trade_usable_true=0`, so no current evidence supports a practical completion
  or `update_goal=true` claim.
- 2026-05-28: immediate follow-up claim audit showed the Board B surface had
  mutated again after stale-safe takeovers launched: `active_claims=5`,
  `live_factor_processes=3`, `active_claims_without_live_process=2`,
  `blocking_reasons=[active_claims, live_factor_processes]`, while
  `promotion_allowed_true=0` and `trade_usable_true=0` remained unchanged. This
  supersedes the snapshot only for current live occupancy and confirms no safe
  new launch/terminalization should happen until those live roots exit or write
  terminal evidence.
- 2026-05-28: refreshed the coordinated snapshot at
  `/tmp/ict-engine-goal-20260528-closure-recheck1/objective_closure_snapshot.json`.
  The current blocker surface narrowed to `active_claims=2` and
  `live_factor_processes=2`, both `live_runtime_owner`; still no
  `promotion_allowed_true` or `trade_usable_true`. A WPR/reference-Hurst live
  process was paired with a stale earlier `tomac_aq.exit=1`/stderr file, so
  `support/scripts/factor_claim_terminalization_audit.py` now marks compact live
  process `exit_file_state=stale_for_process` when the inferred exit file
  predates the current process. Regression:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed `60/60`; live compact readback at
  `/tmp/ict-engine-goal-20260528-factor-staleexit-check.json` showed the WPR
  root as `stale_for_process`, preventing stale failed artifacts from being
  mistaken for current terminal truth.
- 2026-05-28: refreshed the coordinated snapshot at
  `/tmp/ict-engine-goal-20260528-codex-refresh-current2/objective_closure_snapshot.json`.
  The objective remains `not_complete`: done-definition is only light-green
  with `completion_ready=false`, factor closure is blocked by one fresh
  wait-only prep claim, and release readiness still fails
  `worktree_clean_for_release` plus `remote_readback`. The factor child now
  reports `active_claims=1`, `live_factor_processes=0`,
  `active_claims_without_live_process=1`,
  `wait_only_active_claims_without_live_process=1`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`. The remaining claim is
  `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260528T011147+0800-codex-tomac-donchian-continuation-prep.claim`,
  created at `2026-05-28T01:11:47+0800` as prep-only staging; it is too fresh
  to take over or terminalize from this audit slice. Release readback remains
  blocked by `Connection closed by 198.18.0.190 port 22` for both origin and the
  release mirror. Focused regressions still pass:
  `test_objective_closure_snapshot` passed `9/9` and
  `test_factor_claim_terminalization_audit` passed `60/60`.
- 2026-05-28: refreshed again at
  `/tmp/ict-engine-goal-20260528-codex-refresh-current4/objective_closure_snapshot.json`
  after process drift. The objective is still `not_complete`, but the factor
  blocker shape changed from one wait-only prep claim to live runtime
  ownership: `active_claims=4`, `live_factor_processes=4`,
  `active_claims_without_live_process=0`,
  `wait_only_active_claims_without_live_process=0`,
  `stale_safe_takeover_candidates=0`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`. The transient Crabel NR7 `active_claim_debt` row from
  the prior packet gained a live AQ child under the same root and is now
  correctly classified as `live_runtime_owner`; no cleanup/takeover is safe.
  Release readiness remains red on `worktree_clean_for_release` and
  `remote_readback`, so a completion commit is still explicitly contradicted by
  current evidence.
- 2026-05-28: found and fixed an evidence-pack coordination loophole in
  `support/scripts/objective_closure_snapshot.py`: parent
  `summary.prioritized_next_actions` lifted only `live_roots[:3]`, so a packet
  with four live runtime roots could still require nested factor-child reading
  to see the fourth wait surface. The cap is now removed and
  `support/scripts/tests/test_objective_closure_snapshot.py` covers four live
  roots. Verification passed:
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  (`10/10`) and
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  (`60/60`). Fresh packet
  `/tmp/ict-engine-goal-20260528-codex-refresh-current6/objective_closure_snapshot.json`
  remains `not_complete`, but now lists all four live runtime queue heads in
  the parent summary. Factor closure is still red with `active_claims=5`,
  `live_factor_processes=4`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`; the new wait-only claim is fresh prep-only
  `20260528T012234+0800-codex-tomac-session-window-sweep-reclaim-prep.claim`,
  not stale cleanup debt.
- 2026-05-28: found and fixed the same parent-queue loophole for non-live claim
  queues. `objective_closure_snapshot.py` previously lifted only the first
  `externalize_wait_only_claims` entry and only the first
  `stale_safe_takeover_claims` entry into parent
  `summary.prioritized_next_actions`. The current code now lifts every
  wait-only and stale-safe queue entry, and
  `support/scripts/tests/test_objective_closure_snapshot.py` covers multiple
  entries for both queues. Verification passed:
  `test_objective_closure_snapshot` `11/11` and
  `test_factor_claim_terminalization_audit` `60/60`. Fresh packet
  `/tmp/ict-engine-goal-20260528-codex-refresh-current8/objective_closure_snapshot.json`
  proves parity: child wait-only entries `2` and parent wait-only actions `2`,
  child live roots `4` and parent live-root actions `4`. Objective status still
  remains `not_complete`; factor closure has `trade_usable_true=0`, and the two
  wait-only claims are both fresh prep-only waiting lanes rather than stale
  cleanup targets.
- 2026-05-28: after the stale-exit fix commit, a standalone compact audit
  briefly reported `active_claims=0` and `live_factor_processes=0`, but that
  zero-claim readback was not durable enough for a completion claim. The fresh
  coordinated snapshot at
  `/tmp/ict-engine-goal-20260528-current-refresh/objective_closure_snapshot.json`
  still reports `summary.status=not_complete` with
  `done_definition_not_completion_ready`, `factor_closure_blocked`, and
  `release_readiness_blocked`; its factor child saw a new live owner for
  `ict-engine-tomac-opening-drive-rvol-vwap-continuation-practical-20260528T011341+0800`
  (`pid=47989`) and kept `promotion_allowed_true=0` /
  `trade_usable_true=0`.
- 2026-05-28: one-minute live-owner poll at
  `/tmp/ict-engine-goal-20260528-after-poll.json` showed the Board B surface
  mutating further to `active_claims=4`, `live_factor_processes=5`,
  `active_claims_without_live_process=0`, and
  `wait_only_active_claims_without_live_process=0`. All active attention claims
  are current live runtime owners, not stale-safe takeover candidates, and the
  practical flags remain `promotion_allowed_true=0` / `trade_usable_true=0`.
  Therefore the current correct conclusion is still wait/recheck, not takeover,
  terminalization, or completion.
- 2026-05-28: current continuation snapshot at
  `/tmp/ict-engine-goal-20260528-continuation-now/objective_closure_snapshot.json`
  still reports `not_complete`. Factor closure is blocked by four active live
  runtime owners: opening-drive RVOL/VWAP (`pid=47989`), Donchian continuation
  (`pid=48896`), Crabel NR7 intraday expansion (`pid=50505`), and opening-drive
  two-leg participation-quality persistence lift (`pid=51930`). All remain
  `promotion_allowed_true=0` / `trade_usable_true=0`; their terminal summaries
  are still `launch_in_progress` or absent, so none can be terminalized from
  this audit slice. The parent snapshot now carries every live runtime root as
  a `prioritized_next_actions` entry. A later pre-commit snapshot at
  `/tmp/ict-engine-goal-20260528-precommit-snapshot-contract/objective_closure_snapshot.json`
  showed two fresh wait-only claims in addition to the four live roots; parent
  action queues now enumerate all wait-only, stale-safe, and live-runtime
  factor actions instead of truncating to a queue head. Regressions
  `test_summarize_snapshot_lists_every_live_factor_runtime_action` and
  `test_summarize_snapshot_lists_every_wait_only_and_stale_factor_action` lock
  this evidence-coordination contract. Verification:
  `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  passed `11/11`.
- 2026-05-28: current9 refresh at
  `/tmp/ict-engine-goal-20260528-codex-refresh-current9/objective_closure_snapshot.json`
  remains `summary.status=not_complete` with blockers
  `done_definition_not_completion_ready`, `factor_closure_blocked`, and
  `release_readiness_blocked`. Standalone factor audit
  `/tmp/ict-engine-goal-20260528-factor-refresh-current9.json` reports
  `active_claims=6`, `live_factor_processes=3`,
  `active_claims_without_live_process=3`,
  `wait_only_active_claims_without_live_process=3`,
  `stale_safe_takeover_candidates=0`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`. Direct `ps` confirms live PIDs `48896`, `50505`, and
  `63225` still exist. Donchian and Crabel terminal summaries remain
  `launch_in_progress`; the two-leg AQ root has round exit files but no
  terminal practical admission. Parent/child action parity holds for this
  packet: child wait-only entries `3` and parent wait-only actions `3`; child
  live roots `3` and parent live-root actions `3`. The safe action remains
  wait/recheck or owner externalization, not takeover, promotion, completion,
  or commit.
- 2026-05-28: current10/current11 found and fixed another consumer-automation
  loophole in `support/scripts/objective_closure_snapshot.py`: the coordinated
  snapshot could emit `summary.status=not_complete` while the CLI returned
  shell exit `0`. That was unsafe for reusable gate automation because a red
  packet could look successful to scripts. The new `snapshot_exit_code()` owner
  returns `1` for valid but unproven/red snapshots, `2` for `snapshot_failed`,
  and `0` only when `summary.completion_proven=true`. Focused TDD red/green
  covered this in
  `test_snapshot_exit_code_fails_closed_when_completion_is_unproven`. Live
  verification:
  `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260528-codex-refresh-current11`
  now returns `EXIT:1` while writing a valid `not_complete` packet. Current11
  factor closure is still worse, not better: `active_claims=7`,
  `live_factor_processes=3`, `active_claims_without_live_process=4`,
  `wait_only_active_claims_without_live_process=4`,
  `stale_safe_takeover_candidates=0`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`. The new fourth wait-only claim is fresh prep-only
  `20260528T013829+0800-codex-tomac-initial-balance-extension-session-filtered-cadence-lift-prep.claim`;
  no takeover or completion is safe.
- 2026-05-28: wait-split refresh tightened the factor-action classifier again.
  Fresh wait-only prep claims without a live process are now separated from
  stale-safe wait-only cleanup claims, and live-runtime-owned active claims no
  longer leak into the generic `terminalize or externalize active claims`
  action. Verification:
  `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed `65/65`; `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  passed `14/14`; `git diff --check -- <touched files>` passed. The current
  coordinated packet at
  `/tmp/ict-engine-goal-20260528-codex-next-waitsplit2/objective_closure_snapshot.json`
  deliberately exits shell `1` and reports `summary.status=not_complete` with
  blockers `done_definition_not_completion_ready`, `factor_closure_blocked`,
  and `release_readiness_blocked`. Factor closure currently has
  `active_claims=2`, `live_factor_processes=1`,
  `fresh_active_claims_without_live_process=2`, `promotion_allowed_true=0`,
  and `trade_usable_true=0`. Release readiness remains red on
  `worktree_clean_for_release`, `source_origin_matches_selected_source`, and
  `release_version_tag_available`. This is a verified actionability/classifier
  slice only; it is not objective completion.
- 2026-05-28: continuation heavy done-definition refresh closed one stale
  proof gap but exposed a parent-action UX loophole. Standalone heavy audit
  `python3 support/scripts/done_definition_audit.py --run-all-heavy --compact --output /tmp/ict-engine-goal-20260528-codex-cont2-heavy-done.json`
  passed all `8/8` gates with `completion_ready=true` and
  `evidence_level=full_enabled_gate_coverage`. The first heavy parent packet
  still listed done-definition as a `completion_proof_gap` priority even though
  that surface was green. `support/scripts/objective_closure_snapshot.py` now
  suppresses done-definition prioritized next actions when
  `completion_ready=true`, with regression
  `test_summarize_snapshot_does_not_prioritize_done_definition_when_full_coverage_passes`.
  Verification: `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  passed `15/15`. Live heavy parent packet
  `/tmp/ict-engine-goal-20260528-codex-cont2-heavy-snapshot2/objective_closure_snapshot.json`
  deliberately exits `1` but now has blockers only `factor_closure_blocked` and
  `release_readiness_blocked`; done-definition is green with
  `completion_ready=true`. Factor closure remains red with `active_claims=2`,
  `live_factor_processes=2`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`. Release readiness remains red on
  `worktree_clean_for_release` and `remote_readback`. This is still not
  objective completion.
- The same slice also made the parent practical blocker explicit for the future
  all-child-green case: when factor closure is otherwise `pass` but reports
  `promotion_allowed_true=0` and `trade_usable_true=0`, the parent now emits
  `same_tree_practical_closure_unproven` instead of becoming surface-green.
- 2026-05-28: release-readiness remote diagnostics were tightened after
  `/tmp/ict-engine-goal-20260528-codex-cont3-current/objective_closure_snapshot.json`
  showed `remote_readback` failing on the release mirror with an SSH-style
  `Connection closed ... port 22` error despite an HTTPS mirror URL. The audit
  now builds a no-rewrite HTTPS fallback probe plan for GitHub HTTPS URLs and
  uses it for the release mirror, matching the existing origin fallback shape.
  Verification: `python3 -m unittest support.scripts.tests.test_release_readiness_audit -v`
  passed `19/19`. The post-fix live release audit at
  `/tmp/ict-engine-goal-20260528-codex-cont3-release-readiness.json` reached
  remote readback and now fails on the concrete release blockers
  `worktree_clean_for_release`, `source_origin_matches_selected_source`, and
  `release_version_tag_available`. The parent packet at
  `/tmp/ict-engine-goal-20260528-codex-cont3-post-release/objective_closure_snapshot.json`
  remains `not_complete` with fresh Board B factor claims and
  `promotion_allowed_true=0` / `trade_usable_true=0`.
- 2026-05-28: proof-reuse continuation closed the non-heavy parent snapshot UX
  gap without weakening completion gates. `support/scripts/objective_closure_snapshot.py`
  now accepts `--done-definition-proof <json>` and applies it only when the
  referenced `done_definition_audit.py` packet is full coverage
  (`completion_ready=true` with no skipped gates). When `--output-dir` is used,
  the proof is copied into the packet as `done_definition_proof.compact.json`
  so reusable evidence packs do not point back to an external `/tmp` file. TDD
  coverage added valid-proof, partial-proof rejection, and proof-staging
  regressions; `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  passed `19/19`. Live verification:
  `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --done-definition-proof /tmp/ict-engine-goal-20260528-codex-cont2-heavy-done.json --output-dir /tmp/ict-engine-goal-20260528-codex-cont4-proof-reuse-staged --timeout-seconds 300`
  exited `1` with `done_definition.proof_applied=true`, portable proof source
  `done_definition_proof.compact.json`, and blockers only
  `factor_closure_blocked` plus `release_readiness_blocked`. This is a
  reusable evidence-pack UX improvement, not objective completion.
- 2026-05-28: release-readback transport-drift diagnostics are now explicit.
  Root-cause evidence from the live host showed local git rewrite rules:
  `git config --show-origin --get-regexp '^(url\..*\.insteadof|http\..*\.proxy|core\.sshCommand)$'`
  returned `url.git@github.com:.insteadof https://github.com/`, which explains
  why an HTTPS fallback probe could still fail with SSH-style
  `Connection closed ... port 22`. `support/scripts/release_readiness_audit.py`
  now classifies this case as `https_probe_ssh_transport_drift` and its
  `remote_readback` next action explicitly tells operators to inspect
  `url.*.insteadof`, `core.sshCommand`, and `http.*.proxy` before treating it
  as generic network/auth failure. Verification:
  `python3 -m unittest support.scripts.tests.test_release_readiness_audit -v`
  passed `20/20`; targeted regression
  `test_remote_readback_failure_classifies_https_probe_ssh_transport_drift`
  passed. Fresh direct release audit
  `/tmp/ict-engine-goal-20260528-transport-drift-release-readiness.json`
  reached remote tags and now fails on the concrete release blockers
  `worktree_clean_for_release`, `source_origin_matches_selected_source`, and
  `release_version_tag_available`, while the coordinated parent packet
  `/tmp/ict-engine-goal-20260528-transport-drift-objective/objective_closure_snapshot.json`
  hit the intermittent transport-drift readback path and preserved the sharper
  next action. The same parent packet also proves factor-claim debt is cleared:
  `factor_closure.status=pass`, `active_claims=0`, and
  `live_factor_processes=0`, so the blocker moved from raw claim closure to
  `same_tree_practical_closure_unproven` because `promotion_allowed_true=0`
  and `trade_usable_true=0` remain false. This is still not objective
  completion.

## 2026-05-28 Current Refresh - Missing-Root Queue Actionability

Latest authoritative packet for this refresh:

- `/tmp/ict-engine-goal-20260528-codex-missingroot-queue/objective_closure_snapshot.json`

Commands:

```bash
python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-goal-20260528-codex-live-factor-now.json
python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-goal-20260528-codex-live-release-now.json
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --done-definition-proof /tmp/ict-engine-goal-20260528-heavy-done-current.json --output-dir /tmp/ict-engine-goal-20260528-codex-missingroot-queue --timeout-seconds 300
python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v
python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v
```

Current command truth:

- parent summary remains `status=not_complete` and shell exit `1`;
- done-definition remains green through staged proof
  (`completion_ready=true`, `evidence_level=full_enabled_gate_coverage`);
- factor child is again red from concurrent fresh claims:
  `active_claims=2`, `live_factor_processes=0`,
  `fresh_active_claims_without_live_process=2`,
  `promotion_allowed_true=0`, and `trade_usable_true=0`;
- release readiness remains red on `worktree_clean_for_release`,
  `source_origin_matches_selected_source`, and
  `release_version_tag_available`.

Loopholes found and fixed:

- When factor closure was `status=pass` but same-tree practical promotion was
  still unproven, the parent priority list could still include the child text
  `no claim terminalization blockers found` as a `practical_closure_blocked`
  action. The parent now suppresses generic factor child actions when the
  factor claim plane is already pass, leaving the specific
  `same_tree_practical_closure_unproven` action as the only factor action.
- When factor closure reported `missing_run_roots`, the compact child packet
  exposed only a generic next action and did not queue the exact affected
  claims. `factor_claim_terminalization_audit.py` now emits
  `attention_action_queue.missing_run_root_claims`, and
  `objective_closure_snapshot.py` lifts those exact claims into parent
  `summary.prioritized_next_actions`.

Verification:

- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
  passed `65/65`.
- `python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v`
  passed `20/20`.
- Live packet `/tmp/ict-engine-goal-20260528-codex-missingroot-queue/objective_closure_snapshot.json`
  remained red and listed the two fresh factor claims plus the three release
  blockers directly at parent priority level.

Requirement verdict updates:

- Evidence-pack coordination/reuse improved: parent packets no longer surface
  a no-op factor action after claim-plane pass, and missing-root blockers are
  directly actionable without a second child read.
- Practical end-to-end profitability factor remains
  `contradicted_by_current_state`; fresh factor claims exist and all practical
  flags are false.
- Completion commit remains invalid because same-tree practical closure and
  release readiness are still unproven.

## 2026-05-28 Current Refresh - Release No-Rewrite Fallback Readback

Latest authoritative packet for this refresh:

- `/tmp/ict-engine-goal-20260528-cont-norewrite-snapshot/objective_closure_snapshot.json`

Commands:

```bash
python3 -m unittest support.scripts.tests.test_release_readiness_audit -v
python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-goal-20260528-cont-release-norewrite.json
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --done-definition-proof /tmp/ict-engine-goal-20260528-heavy-done-current.json --output-dir /tmp/ict-engine-goal-20260528-cont-norewrite-snapshot --timeout-seconds 300
```

Current command truth:

- release child no longer reports `remote_readback` after true no-rewrite
  readback; unresolved release gates are now the concrete
  `worktree_clean_for_release`, `source_origin_matches_selected_source`, and
  `release_version_tag_available` gates;
- done-definition remains green through staged full proof;
- factor child remains red with wait-only claims, one missing run-root claim,
  one live runtime root, and `promotion_allowed_true=0` /
  `trade_usable_true=0`;
- parent summary remains `status=not_complete` with blockers
  `factor_closure_blocked` and `release_readiness_blocked`.

Loopholes found and fixed:

- The GitHub HTTPS fallback was named `https_public_no_rewrite`, but the probe
  inherited local git config. On this host `url.git@github.com:.insteadof
  https://github.com/` can rewrite HTTPS probes back to SSH and intermittently
  create false `remote_readback` blockers.
- `release_readiness_audit.py` now runs public GitHub HTTPS fallback probes
  with `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_NOSYSTEM=1`, and treats a
  successful fallback as effective readback while preserving raw probe
  diagnostics.

Verification:

- `python3 -m unittest support.scripts.tests.test_release_readiness_audit -v`
  passed `21/21`.
- Live release audit `/tmp/ict-engine-goal-20260528-cont-release-norewrite.json`
  reached origin and release mirror heads/tags and shifted release blockers to
  dirty worktree, source-origin drift, and tag reuse.
- Live objective packet `/tmp/ict-engine-goal-20260528-cont-norewrite-snapshot/objective_closure_snapshot.json`
  exited `1` and stayed red for the correct remaining factor/release blockers.

Requirement verdict updates:

- Evidence-pack release readback is more reusable across hosts with local git
  rewrite config; the fallback probe now matches its no-rewrite name.
- Release readiness is still `contradicted_by_current_state`, but the blocker
  is now concrete source/worktree/tag state rather than transport ambiguity.
- Practical end-to-end profitability factor remains
  `contradicted_by_current_state`; no current packet has practical flags true.
- Completion commit remains invalid.

## 2026-05-28 Current Refresh - Tracked Practical Gate And Live Runtime Blockers

Latest authoritative packet for this refresh:

- `/tmp/ict-engine-goal-20260528-codex-after-tracked-practical/objective_closure_snapshot.json`

Commands:

```bash
python3 -m unittest support.scripts.tests.test_release_readiness_audit -v
python3 -m unittest support.scripts.tests.test_done_definition_audit -v
python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v
python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v
python3 support/scripts/done_definition_audit.py --output /tmp/ict-engine-goal-20260528-codex-done-current-full.json
python3 support/scripts/release_readiness_audit.py --compact --check-remotes > /tmp/ict-engine-goal-20260528-codex-release-current.json
python3 support/scripts/factor_claim_terminalization_audit.py --compact --portable-paths --output /tmp/ict-engine-goal-20260528-codex-factor-current.json
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260528-codex-after-tracked-practical
```

Current command truth:

- focused verification passed: release readiness `21/21`, done-definition
  `19/19`, objective snapshot `20/20`, and practical-admission scanner `12/12`;
- done-definition light gate is stronger but still not completion proof:
  `status=pass`, `completion_ready=false`,
  `evidence_level=partial_skipped_gates`, and skipped heavy gates
  `cargo_check_all_targets`, `cargo_clippy_all_targets_deny_warnings`,
  `cargo_test`, and `smoke_acceptance_tmp_state`;
- practical-admission source gate now passes only because tracked source is
  clean: `tracked_scanned_files=28`, `tracked_violation_count=0`, while
  untracked wrapper residue remains visible with `untracked_scanned_files=887`
  and `untracked_violation_count=193`;
- factor closure is red from live runtime owners:
  `active_claims=2`, `live_factor_processes=2`,
  `active_claims_without_live_process=0`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`;
- release readiness is red on `worktree_clean_for_release`,
  `source_origin_matches_selected_source`, and
  `release_version_tag_available`;
- parent summary remains `status=not_complete` with blockers
  `done_definition_not_completion_ready`, `factor_closure_blocked`, and
  `release_readiness_blocked`.

Loopholes found and fixed:

- `done_definition_audit.py` now includes a tracked-source
  `practical_admission_source_surface` gate. It runs the existing source
  checker over wrapper files, uses `git ls-files` to separate committed source
  from untracked multi-agent residue, and fails the done-definition audit if
  tracked wrappers regress into practical-admission fail-open patterns.
- `release_readiness_audit.py` now neutralizes local git config for public
  GitHub HTTPS fallback probes and preserves transport-drift diagnostics. A
  successful public fallback is effective remote readback, so release blockers
  now point at concrete worktree/source/tag facts when remotes are reachable.

Requirement verdict updates:

- Evidence-pack and audit UX improved: tracked practical-admission failures and
  host git rewrite drift are now first-class machine-readable gates instead of
  hidden loopholes.
- The full objective is still not complete: no same-tree practical closure
  packet has `promotion_allowed_true>0` and `trade_usable_true>0`, two live
  factor runtimes currently own claims, heavy done-definition gates were not
  rerun, and release readiness is red.
- A narrow audit-hardening commit is justified if it includes only the verified
  source/tests/docs above; a completion commit for the broader objective would
  still be false.

Precommit drift readback:

- `/tmp/ict-engine-goal-20260528-precommit-snapshot/objective_closure_snapshot.json`
  remains `status=not_complete` with blocker classes
  `done_definition_not_completion_ready`, `factor_closure_blocked`, and
  `release_readiness_blocked`.
- Factor closure drifted down to one live runtime owner (`pid=75414`, run root
  `ict-engine-tomac-ict-wpr-fractal-reclaim-continuation-20260528T182219+0800`)
  but practical flags stayed false.
- Release readiness drifted back to unresolved `remote_readback` plus
  `worktree_clean_for_release`; exact release gate names are still time-variant
  and must be rerun before the next release fix, but the full objective remains
  blocked either way.

## 2026-05-28 Current Refresh - Practical Source Debt Preserved In Compact Packets

Latest authoritative packet for this refresh:

- `/tmp/ict-engine-goal-20260528-cont-current/objective_closure_snapshot.json`

Commands:

```bash
python3 -m unittest support.scripts.tests.test_done_definition_audit support.scripts.tests.test_objective_closure_snapshot -v
python3 support/scripts/factor_claim_terminalization_audit.py --compact --portable-paths --output /tmp/ict-engine-goal-20260528-cont-factor.json
python3 support/scripts/release_readiness_audit.py --compact --check-remotes > /tmp/ict-engine-goal-20260528-cont-release.json
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260528-cont-current
```

Current command truth:

- focused verification passed `41/41` for done-definition and objective
  snapshot tests;
- compact done-definition now preserves passed practical-source debt details:
  `practical_admission_source_surface.status=pass`,
  `tracked_violation_count=0`, `untracked_violation_count=193`, and
  `untracked_violating_files=115`;
- parent summary remains `status=not_complete` and now includes blocker
  `practical_admission_source_debt` in addition to
  `done_definition_not_completion_ready`, `factor_closure_blocked`, and
  `release_readiness_blocked`;
- factor closure has drifted from a live process to a fresh active claim without
  live runtime:
  `20260528T183406+0800-codex-tomac-ict-wpr-fractal-reclaim-fullwindow-launch.claim`,
  still with `promotion_allowed_true=0` and `trade_usable_true=0`;
- release readiness remains red on `worktree_clean_for_release`,
  `source_origin_matches_selected_source`, and
  `release_version_tag_available`.

Loophole found and fixed:

- Before this slice, a compact done-definition child could drop details for a
  passed `practical_admission_source_surface`, so the parent objective packet
  could not see untracked unsafe wrapper residue. `done_definition_audit.py`
  now keeps minimal untracked debt fields for this passed gate, and
  `objective_closure_snapshot.py` promotes that debt to the parent blocker
  `practical_admission_source_debt` with an explicit next action.

Requirement verdict updates:

- Evidence-pack coordination is stronger: compact child packets now preserve a
  material non-release blocker even when the tracked-source gate passes.
- The full objective remains not complete. The practical-source debt is not a
  tracked-source failure, but it must be retired, quarantined, or explicitly
  tracked before objective closure because those wrappers can otherwise be
  mistaken for reusable evidence.
- A narrow commit of this compact-packet visibility slice is justified if it
  stages only the two audit scripts, their focused tests, and these tracking
  docs. A completion commit remains false.

Final same-turn drift readback:

- `/tmp/ict-engine-goal-20260528-cont-final/objective_closure_snapshot.json`
  supersedes the exact factor counts above. It still exits `1` and remains
  `status=not_complete`.
- Factor claim/runtime closure cleared during the turn:
  `factor_closure.status=pass`, `active_claims=0`, and
  `live_factor_processes=0`. This removes raw claim debt but does not prove
  practical closure because `promotion_allowed_true=0` and `trade_usable_true=0`.
- The parent blockers are now `done_definition_not_completion_ready`,
  `practical_admission_source_debt`, `same_tree_practical_closure_unproven`,
  and `release_readiness_blocked`.
- Release readiness remains red on `worktree_clean_for_release`,
  `source_origin_matches_selected_source`, and
  `release_version_tag_available`.

## 2026-05-28 Current Refresh - Quarantine, Remote-Side, And Tmp-Root Actionability

Latest authoritative packets for this refresh:

- heavy done-definition proof:
  `/tmp/ict-engine-goal-20260528-current-heavy-done.json`
- live release action check:
  `/tmp/ict-engine-goal-20260528-release-origin-action.json`
- live factor attribution check:
  `/tmp/ict-engine-goal-20260528-factor-after-tmpmatch.json`
- proofed parent snapshot:
  `/tmp/ict-engine-goal-20260528-origin-action-proofed-snapshot/objective_closure_snapshot.json`

Commands:

```bash
python3 support/scripts/done_definition_audit.py --run-all-heavy --compact --output /tmp/ict-engine-goal-20260528-current-heavy-done.json
python3 -m unittest support.scripts.tests.test_done_definition_audit support.scripts.tests.test_objective_closure_snapshot -v
python3 -m unittest support.scripts.tests.test_release_readiness_audit -v
python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v
python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-goal-20260528-release-origin-action.json
python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-goal-20260528-factor-after-tmpmatch.json
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --done-definition-proof /tmp/ict-engine-goal-20260528-current-heavy-done.json --output-dir /tmp/ict-engine-goal-20260528-origin-action-proofed-snapshot --timeout-seconds 300
```

Current command truth:

- full done-definition proof passed all `9/9` gates with
  `completion_ready=true`, including cargo check, clippy, cargo test, and
  smoke acceptance;
- focused verification passed: done/objective `45/45`, release readiness
  `22/22`, factor-claim audit `67/67`;
- practical-admission source debt is now explicitly quarantined, not hidden:
  tracked violations remain `0`, untracked residue remains `193` violations in
  `115` files, and the quarantine fingerprint matches
  `support/docs/audits/practical-admission-source-debt-quarantine.json`;
- release readiness still fails, but live readback now distinguishes sides:
  release mirror readback passed, origin readback timed out, and the action now
  says to restore `source origin` readback instead of blaming the release
  mirror;
- factor closure remains red, but the `/tmp` claim root vs `/private/tmp` live
  process alias is no longer double-counted as a fresh claim without live
  runtime. The live TOD stability-guard root is now owned by its active claim,
  leaving only two fresh no-live claims plus one live runtime in the live factor
  queue at `/tmp/ict-engine-goal-20260528-factor-after-tmpmatch.json`.

Loopholes found and fixed:

- Applying a full done-definition proof could previously replace the current
  light done-definition surface and drop current practical-source debt details.
  `objective_closure_snapshot.py` now merges proof status into the current
  surface, preserving current quarantine/debt evidence while using the heavy
  proof only for full-gate coverage.
- Untracked practical-admission wrapper debt could stay as a permanent parent
  blocker even after it was reviewed as untracked multi-agent residue. The
  new quarantine manifest records the exact fingerprint and keeps the debt
  visible as `quarantined_practical_admission_source_debt` without letting it
  masquerade as tracked-source failure or completion proof.
- `release_readiness_audit.py` previously emitted release-mirror recovery text
  even when only origin readback failed. It now records `failed_sides` and gives
  source-origin recovery text when the release mirror is readable.
- `factor_claim_terminalization_audit.py` compared `/tmp` and `/private/tmp`
  run roots literally, so macOS tmp aliasing could make a live-owned claim also
  appear in the fresh-without-live queue. Runtime ownership matching now
  normalizes tmp aliases and lane subdirs before comparing roots.

Requirement verdict updates:

- Evidence-pack coordination/reuse improved again: compact parent packets
  preserve proof, debt, quarantine, failed remote side, and live-runtime claim
  ownership in the right layers.
- The full objective remains `not_complete`: no same-tree practical closure
  packet has `promotion_allowed_true>0` and `trade_usable_true>0`, factor work
  is still active, and release readiness is still blocked by dirty worktree plus
  source-origin/tag state.
- A narrow commit of this verified audit-hardening slice is justified if it
  stages only the touched audit scripts, their tests, the quarantine manifest,
  and these tracking docs. A completion claim for the broader objective would
  still be false.

## 2026-05-29 Current Refresh - Scanner Timeout Detail And Tracked Wrapper Cleanup

Latest authoritative packet for this refresh:

- `/tmp/ict-engine-goal-20260529T160911+0800-tracked-wrapper-clean/objective_closure_snapshot.json`

Commands:

```bash
python3 support/scripts/research/downstream_practical_admission_source_check.py support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1.py
python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check support.scripts.tests.test_done_definition_audit support.scripts.tests.test_objective_closure_snapshot -v
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260529T160911+0800-tracked-wrapper-clean
```

Current command truth:

- direct scanner readback for
  `run_ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1.py` returned
  `ok=true` with no violations;
- focused verification passed `97/97` tests across the practical-admission
  scanner, done-definition audit, and objective-closure snapshot suites;
- the coordinated snapshot still exits `1` and remains `status=not_complete`;
- done-definition now passes its light gate surface:
  `done_definition.status=pass`, `unresolved=[]`, and the tracked
  practical-admission source debt is cleared with
  `tracked_violation_count=0` / `tracked_violating_files=0`;
- done-definition is not completion proof because the current run skipped
  heavy gates: `cargo_check_all_targets`,
  `cargo_clippy_all_targets_deny_warnings`, `cargo_test`, and
  `smoke_acceptance_tmp_state`;
- untracked source debt is still visible in the parent packet:
  practical-admission debt has `untracked_violation_count=268` across
  `153` files, and await-launch debt has `untracked_violation_count=46`;
- factor closure is red: `active_claims=3`, `live_factor_processes=1`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and the parent packet
  lists the fresh claim queue plus live runtime `pid=79642`;
- release readiness is red on `worktree_clean_for_release` and
  `source_origin_matches_selected_source`.

Loopholes found and fixed:

- A failed practical-source scanner run could previously collapse into a
  vague done-definition failure when the scanner timed out or returned a
  non-zero status without JSON violations. `done_definition_audit.py` now
  preserves `scanner_error`, `scanner_timeout_seconds`, `scanner_returncode`,
  `scanner_command`, `stdout`, and `stderr` on that gate; the parent
  `objective_closure_snapshot.py` now lifts those details so the coordinated
  packet can tell timeout/tooling failure from a clean source surface.
- One tracked wrapper still encoded density inside
  `survives_5bps_per_side`:
  `trades >= 6 and rec['5bps_per_side_total_profit_pct'] > 0`. That field name
  looked like pure cost-survival telemetry but also carried a density gate.
  The wrapper now records `trade_density_ok` separately and leaves
  `survives_2bps_per_side` / `survives_5bps_per_side` as cost-survival fields;
  downstream allowance still requires both `trade_density_ok` and 2bps
  survival.

Requirement verdict updates:

- Evidence-pack coordination/reuse improved: source-scan tooling failures are
  now inspectable from the parent packet, and the current tracked-source
  practical-admission failure was removed instead of quarantined.
- The full objective remains `not_complete`: there is still no same-tree
  practical closure packet, all practical factor counters are false, factor
  ownership is live/fresh-claim blocked, release readiness is red, and the
  latest done-definition proof is light-only rather than full heavy coverage.
- A narrow commit of this audit-hardening and tracked-wrapper cleanup slice is
  justified if it stages only the five touched source/test files plus this
  tracking update. A completion commit for the broader objective would still be
  false.

Post-commit heavy proof:

- commit landed: `29c4773a` (`Preserve objective scanner failure details`),
  current `HEAD=efec153cc638ab14dc1b6590e1840b58900376dc`;
- `/tmp/ict-engine-goal-20260529T161630+0800-postcommit-heavy-done.json`
  passed all enabled done-definition gates:
  `completion_ready=true`, `evidence_level=full_enabled_gate_coverage`,
  `pass_count=10`, `fail_count=0`, `skip_count=0`;
- `/tmp/ict-engine-goal-20260529T1624+0800-postcommit-proofed-snapshot/objective_closure_snapshot.json`
  applied that proof and removed the done-definition blocker, but still exits
  `1` with parent blockers `factor_closure_blocked` and
  `release_readiness_blocked`;
- factor closure remains red in that proofed packet:
  `active_claims=2`, `live_factor_processes=0`, `promotion_allowed_true=0`,
  and `trade_usable_true=0`;
- release readiness remains red on `worktree_clean_for_release` and
  `source_origin_matches_selected_source`.

## 2026-05-29 Current Refresh - Stale Proof Rejection And Fresh Factor-Lane Wait

Latest authoritative packets for this refresh:

- factor audit compact packet:
  `/tmp/ict-engine-goal-20260529T-current-factor.json`
- factor audit full packet:
  `/tmp/ict-engine-goal-20260529T-current-factor-full.json`
- first release readiness recheck:
  `/tmp/ict-engine-goal-20260529T-current-release.json`
- proofed parent snapshot with stale proof rejection:
  `/tmp/ict-engine-goal-20260529T-current-proofed-snapshot/objective_closure_snapshot.json`
- release readiness recheck after parent snapshot:
  `/tmp/ict-engine-goal-20260529T-current-release-recheck.json`

Commands:

```bash
git status --short --branch
python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-goal-20260529T-current-factor.json
python3 support/scripts/factor_claim_terminalization_audit.py --output /tmp/ict-engine-goal-20260529T-current-factor-full.json
python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-goal-20260529T-current-release.json
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --done-definition-proof /tmp/ict-engine-goal-20260529T161630+0800-postcommit-heavy-done.json --output-dir /tmp/ict-engine-goal-20260529T-current-proofed-snapshot --timeout-seconds 300
python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-goal-20260529T-current-release-recheck.json
```

Current command truth:

- live repo state remains a shared dirty tree on `main`, currently ahead of
  `origin/main`; release export cannot be claimed from this worktree;
- the previous heavy done-definition proof is stale for current `HEAD`:
  proof head `efec153cc638ab14dc1b6590e1840b58900376dc` versus current
  snapshot head `6e77adf40661a3cab14d410be5f87507d889c5e3`;
- the parent snapshot rejected the proof with
  `proof_applied=false` and `proof_rejected_reason=proof_head_mismatch`, so
  current done-definition completion evidence is light-only again:
  `completion_ready=false`, `evidence_level=partial_skipped_gates`, skipped
  heavy gates are cargo check, clippy, cargo test, and smoke acceptance;
- factor closure remains red but narrower than the earlier post-commit packet:
  current compact parent packet reports `active_claims=1`,
  `coordination_only_active_claims=3`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and no
  `same_tree_practical_closure` packet;
- the only real fresh factor-lane blocker in the current parent packet is
  `20260529T155611+0800-codex-tomac-ote-fvg-ob-session-directional-bias-launch.claim`;
- that run root is still not terminal: its read-only inspected
  `/tmp/ict-engine-tomac-ote-fvg-ob-session-directional-bias-prep-20260529T155611+0800/summaries/terminal_summary.json`
  says `status=launch_in_progress`, `launch_requested=true`,
  `scan_executed=false`, and `target_row_count=0`; no
  `checks/terminal_metrics.json` or `same_tree_practical_closure.json` exists;
- the newer local screen claim
  `20260529T162948+0800-codex-tomac-opening-compression-mtf-rvol-screen.claim`
  terminalized false-positive screen evidence during the refresh with
  `decision=drop_python_screen_no_robust_5bps_survivor`,
  `promotion_allowed=false`, and `trade_usable=false`;
- release readiness remains red. The first release audit had both remotes
  readable but failed `worktree_clean_for_release` and
  `source_origin_matches_selected_source`; the parent snapshot and immediate
  recheck then failed `remote_readback` for both origin and release mirror, so
  remote readback is currently environment-flaky and not release proof.

Loopholes found and classified:

- Stale heavy done-definition proof reuse is correctly fail-closed by the
  parent snapshot. No code change is needed for this behavior in this slice;
  the current blocker is evidence freshness, not snapshot logic.
- Coordination-only claims stay visible but no longer explain practical factor
  blockage once the current full packet is read. The live practical blocker is
  the single fresh OTE/FVG/OB launch claim, not the audit/inventory claims.
- The OTE/FVG/OB claim is under the fresh-claim wait window and lacks terminal
  metrics. Terminalizing it now would be a collision/ownership violation; the
  correct next action is to wait for owner progress or inspect again after
  stale-safe timeout.
- Release readiness cannot be recovered by docs-only proof because the current
  tree is dirty and remote readback is not stable. A clean selected export plus
  stable `--check-remotes` readback is still required.

Requirement verdict updates:

- The full objective remains `not_complete` with blockers
  `done_definition_not_completion_ready`, `factor_closure_blocked`, and
  `release_readiness_blocked` in the latest parent packet.
- There is still no current evidence of a practical/live-usable factor:
  `promotion_allowed_true=0`, `trade_usable_true=0`, and no validated
  same-tree practical closure packet.
- This slice is a tracking/evidence refresh only. It does not justify a
  completion claim for the broader objective and should not promote, release,
  or terminalize active fresh factor work.

## 2026-05-29 Current Refresh - Clean Worktree Release Proof Rejected On Remote Gate

Latest authoritative packets for this refresh:

- clean detached worktree release audit:
  `/tmp/ict-engine-goal-20260529T1642-clean-export-release.json`
- parent snapshot with clean release proof staged:
  `/tmp/ict-engine-goal-20260529T1642-clean-release-proof-parent/objective_closure_snapshot.json`

Commands:

```bash
git worktree add --detach /Users/thrill3r/.config/aegis/worktrees/ict-engine/release-proof-20260529T1642 a696d98f3be9f3ffe849d735933ddf9bdd11d390
git status --short --branch
python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-goal-20260529T1642-clean-export-release.json
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --release-readiness-proof /tmp/ict-engine-goal-20260529T1642-clean-export-release.json --output-dir /tmp/ict-engine-goal-20260529T1642-clean-release-proof-parent --timeout-seconds 300
```

Current command truth:

- isolated worktree path:
  `/Users/thrill3r/.config/aegis/worktrees/ict-engine/release-proof-20260529T1642`;
- isolated worktree `HEAD` is current committed tracker head
  `a696d98f3be9f3ffe849d735933ddf9bdd11d390` and `git status --short --branch`
  returned only `## HEAD (no branch)`;
- clean release audit proved `worktree_clean_for_release=pass`,
  `cargo_release_policy=pass`, and `release_docs_fresh_for_selected_tag=pass`;
- the same audit still exited `1` because `remote_readback` failed on source
  `origin`; release mirror readback passed only via the no-rewrite HTTPS
  fallback, and `release_version_tag_available` was skipped because the remote
  gate was unresolved;
- parent snapshot staged the release proof but rejected it with
  `proof_applied=false` and `proof_rejected_reason=proof_has_skipped_gates`;
- during the parent refresh, factor occupancy drifted from one fresh factor
  claim to active runtime work: factor closure reported `active_claims=5`,
  `live_factor_processes=5`, `promotion_allowed_true=0`, `trade_usable_true=0`,
  and no same-tree practical closure packet.

Loopholes found and classified:

- Clean export evidence is not enough when remote/tag gates are skipped. The
  parent correctly refused to use a partial release proof to hide current dirty
  tree noise or remote uncertainty.
- The release blocker is now more precise: a clean committed export at current
  `HEAD` can clear local worktree cleanliness, but release readiness still
  requires stable source-origin readback and tag availability.
- Factor closure is live-runtime blocked again because new external factor
  processes started while this read-only release proof was running. Do not
  terminalize or reuse those roots from this objective audit slice.

Requirement verdict updates:

- The full objective remains `not_complete` with current parent blockers
  `done_definition_not_completion_ready`, `factor_closure_blocked`, and
  `release_readiness_blocked`.
- A truthful completion commit is still impossible: heavy done-definition proof
  is not current, factor work is active/live, no practical factor closure packet
  exists, and release remote/tag proof is incomplete.

## 2026-05-29 Current Refresh - Current Heavy Done Proof Clears Done-Definition Blocker

Latest authoritative packets for this refresh:

- current heavy done-definition proof:
  `/tmp/ict-engine-goal-20260529T1650-current-heavy-done.json`
- final parent snapshot using the current done proof:
  `/tmp/ict-engine-goal-20260529T1703-current-final-proofed-snapshot/objective_closure_snapshot.json`

Commands:

```bash
python3 support/scripts/done_definition_audit.py --run-all-heavy --compact --output /tmp/ict-engine-goal-20260529T1650-current-heavy-done.json
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --done-definition-proof /tmp/ict-engine-goal-20260529T1650-current-heavy-done.json --release-readiness-proof /tmp/ict-engine-goal-20260529T1642-clean-export-release.json --output-dir /tmp/ict-engine-goal-20260529T1703-current-final-proofed-snapshot --timeout-seconds 300
```

Current command truth:

- heavy done-definition proof is now current for `HEAD=836cbc4b46e003f0110243717c46a9c7fc1f4483`;
- all ten enabled done-definition gates passed:
  `completion_ready=true`, `evidence_level=full_enabled_gate_coverage`,
  `pass_count=10`, `fail_count=0`, `skip_count=0`;
- final parent snapshot applied the done proof with `proof_applied=true` and
  removed `done_definition_not_completion_ready` from the objective blockers;
- the final parent snapshot still exits `1` with blockers
  `factor_closure_blocked` and `release_readiness_blocked`;
- factor closure at final snapshot time:
  `active_claims=1`, `live_factor_processes=2`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and no `same_tree_practical_closure` packet;
- release readiness at final snapshot time:
  unresolved `worktree_clean_for_release` and
  `source_origin_matches_selected_source`; the older clean release proof was
  rejected as `proof_head_mismatch` because it was for `a696d98f`, before the
  second tracker commit.

Loopholes found and classified:

- The broad objective is no longer blocked by stale done-definition proof. Any
  future completion claim must still rerun or reuse a same-head heavy proof, but
  as of this packet the done-definition surface itself is green.
- Factor closure remains the practical-use blocker: live runtimes exist and no
  same-tree practical closure packet exists, so `promotion_allowed_true=0` and
  `trade_usable_true=0` remain the only truthful practical count.
- Release cleanliness proof must be regenerated after every commit. A clean
  detached audit from `a696d98f` cannot clear release readiness for
  `836cbc4b`.

Requirement verdict updates:

- Current objective status remains `not_complete`, now for two live blockers:
  factor closure and release readiness.
- No evidence currently proves practical/live trading usefulness.
- Next safe actions are to wait for or inspect the two live factor runtime
  roots after they exit, then rerun factor closure; separately rerun a clean
  selected-export release audit at current `HEAD` only when remote/source-origin
  readback is stable enough to prove tag availability.

Post-commit caveat:

- The commit that records this section necessarily advances `HEAD`. Treat the
  heavy done-definition proof above as evidence for its named commit only
  (`836cbc4b46e003f0110243717c46a9c7fc1f4483`). Before any future completion,
  release, or current-HEAD proof claim, rerun the heavy done-definition audit
  against the then-current `HEAD` and use that same-head packet in the parent
  objective snapshot.

## 2026-05-29 Current Refresh - Workdoc Terminal Parsing Fix Landed, Objective Still Blocked

Latest authoritative packets for this refresh:

- factor audit after the workdoc terminal parsing fix:
  `/tmp/ict-engine-goal-20260529T-current3-factor.json`
- release audit after the workdoc terminal parsing fix:
  `/tmp/ict-engine-goal-20260529T-current3-release.json`
- parent objective snapshot:
  `/tmp/ict-engine-goal-20260529T-current3-objective/objective_closure_snapshot.json`

Commands:

```bash
python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v
python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-goal-20260529T-current3-factor.json
python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-goal-20260529T-current3-release.json
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260529T-current3-objective --timeout-seconds 300
```

Current command truth:

- `HEAD=154e0565e57687b1b9fcb1991a9357e34e838612` contains the verified
  `Fix factor claim workdoc terminal parsing` code/test slice;
- focused factor-claim regression suite passed: 87 tests, 0 failures;
- the fix prevents a nonterminal workdoc workflow section such as
  `## TDD Route` with `Decision: skipped` from falsely terminalizing a live
  active claim, while preserving terminal/final workdoc readback handling;
- standalone factor audit briefly showed no claim terminalization blockers, but
  the later parent snapshot saw fresh shared-worktree drift again:
  `active_claims=2`, `live_factor_processes=3`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `same_tree_practical_closure=null`;
- release audit remote readback now passed directly for both source origin and
  release mirror, and `release_version_tag_available=pass` for `v0.1.8`;
- release audit still exited `1` with unresolved `worktree_clean_for_release`
  and `source_origin_matches_selected_source`; current source is ahead of
  `origin/main` by 135;
- parent objective snapshot exited `1` with blockers
  `done_definition_not_completion_ready`, `factor_closure_blocked`, and
  `release_readiness_blocked`.

Loopholes found and classified:

- Workdoc process-route decisions are not terminal factor evidence. The current
  parser now requires terminal/final sections, explicit terminal fields,
  terminal-looking status, or terminal-looking decisions before using a workdoc
  to terminalize a claim.
- A passing momentary factor audit is not stable closure in the shared tree.
  Another live/fresh factor lane appeared before the parent snapshot, so factor
  closure must be judged from the current parent packet, not the earlier
  standalone pass.
- Remote readback is no longer the release blocker in this refresh. The live
  blockers are dirty selected source state and source-origin mismatch.

Requirement verdict updates:

- Current objective status remains `not_complete`.
- No current evidence proves practical/live trading usefulness:
  `promotion_allowed_true=0`, `trade_usable_true=0`, and no validated
  same-tree practical closure packet.
- Any future completion claim must rerun heavy done-definition proof at the
  then-current `HEAD`, wait for or explicitly claim/terminalize live factor
  lanes, and prove release readiness from a clean selected export with source
  origin alignment.

## 2026-05-29 Current Refresh - Practical Closure Requires Full Lifecycle Tuple

Latest authoritative packets for this refresh:

- factor audit before this closure-contract hardening:
  `/tmp/ict-engine-goal-20260529T-current5-factor.json`
- release audit before this closure-contract hardening:
  `/tmp/ict-engine-goal-20260529T-current5-release.json`
- parent snapshot after the lifecycle tuple commit and quarantine-schema repair:
  `/tmp/ict-engine-goal-20260529T-current9-after-quarantine-alt/objective_closure_snapshot.json`

Commands:

```bash
python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-goal-20260529T-current5-factor.json
python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-goal-20260529T-current5-release.json
python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v
python3 -m unittest support.scripts.tests.test_done_definition_audit -v
python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260529T-current9-after-quarantine-alt --timeout-seconds 120
```

Current command truth:

- focused factor-claim regression suite passed: 88 tests, 0 failures;
- done-definition audit regression suite passed: 31 tests, 0 failures;
- objective snapshot regression suite passed: 40 tests, 0 failures;
- `factor_claim_terminalization_audit.py` now rejects a
  `same_tree_practical_closure` evidence packet unless it includes the full
  lifecycle tuple: `learning_admission_status=admitted`,
  `paper_admission_status=ready`, and `live_trade_status=ready`;
- the positive fixture for a valid same-tree practical closure now carries that
  tuple, and the negative fixture proves `live_trade_status=ready` alone cannot
  satisfy practical closure when learning/paper admission remain
  `not_evaluated`;
- current factor audit in the latest parent snapshot is blocked by fresh
  shared-worktree claims: `active_claims=3`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`;
- release audit still exited `1` with unresolved `worktree_clean_for_release`
  and `source_origin_matches_selected_source`; remote readback and tag
  availability passed.
- parent snapshot after the lifecycle tuple hardening exposed a separate
  fail-closed blocker: `practical_admission_source_debt`, because the original
  quarantine accepted only one fingerprint while the shared untracked-wrapper
  residue can oscillate between two reviewed signatures for the same 268-count,
  153-file debt set;
- parent snapshot after the quarantine-schema repair shows the reviewed
  practical-admission debt is quarantined and staged, not hidden:
  `quarantined_practical_admission_source_debt` remains visible with 268
  untracked violations across 153 files, while objective status remains
  `not_complete` on `done_definition_not_completion_ready`,
  `factor_closure_blocked`, and `release_readiness_blocked`.

Loopholes found and classified:

- A same-tree closure packet that only says `promotion_allowed=true`,
  `trade_usable=true`, and `live_trade_status=ready` is insufficient. It can
  skip the learning and paper-admission stages that are required to prove the
  provider -> execution -> feedback -> training chain is actually reusable and
  live-practical.
- The closure contract now fails closed until the evidence packet proves all
  three lifecycle statuses and the existing same-root, validation, ranker, and
  command-exit requirements.
- The practical-admission quarantine drift was reviewed rather than ignored.
  Counts and file set stayed unchanged at 268 violations across 153 untracked
  files; the stable signature change was limited to
  `run_tomac_nq_bidir_opening_drive_exact_downstream_v1.py` switching the
  `promotion_allowed`, `trade_usable`, and `update_goal` values between
  `promotion_ready` and `live_ready`. Both signatures still violate the
  extension-complete guard and remain untracked unsafe debt, not release or
  trade evidence. The quarantine reader now supports an explicit
  `reviewed_alternative_untracked_violations_sha256` list while still requiring
  schema, decision, violation count, and violating file count to match.

Requirement verdict updates:

- Current objective status remains `not_complete`.
- This hardening improves the practical-use proof standard but does not create
  a practical factor. Current verified practical counts remain
  `promotion_allowed_true=0`, `trade_usable_true=0`, with no validated
  same-tree practical closure packet.
- Externalizing the reviewed untracked debt can prevent fingerprint oscillation
  from producing false new debt, but it does not retire the debt. Objective
  completion still requires a validated same-tree practical closure packet,
  heavy done-definition proof, clean/sanitized release readiness with selected
  source alignment, and either retiring/tracking/fixing those wrappers or
  preserving an explicit matching quarantine while all other gates prove the
  requested end state.

## 2026-05-29 Current Refresh - Extension-Complete Source Gate Tightened

Latest authoritative packet for this refresh:

- parent objective snapshot with remote checks:
  `/tmp/ict-engine-goal-20260529-codex-resume-current-remote/objective_closure_snapshot.json`

Commands:

```bash
python3 -m unittest support.scripts.research.tests.test_downstream_practical_admission_source_check -v
python3 -m unittest support.scripts.tests.test_done_definition_audit -v
python3 -m unittest support.scripts.tests.test_objective_closure_snapshot -v
python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260529-codex-resume-current-remote --timeout-seconds 300
```

Current command truth:

- `downstream_practical_admission_source_check.py` now fails closed when a
  wrapper passes positive/local `extension_complete` into
  `practical_admission_flags(...)`, including hardcoded `True`,
  `bool(metrics.get("extension_complete"))`, and direct-return helper calls;
- focused verification passed: practical-admission source checker `31/31`,
  done-definition audit `31/31`, and objective snapshot `43/43`;
- tracked practical-admission violations remained `0`; quarantined untracked
  practical debt remained visible at `270` violations across `155` untracked
  files, including the two stricter `extension_complete` findings;
- the remote-checked parent snapshot still exited `1` with blockers
  `done_definition_not_completion_ready`, `factor_closure_blocked`, and
  `release_readiness_blocked`;
- factor closure stayed non-practical: `active_claims=2`,
  `fresh_active_claims_without_live_process=2`, `live_factor_processes=0`,
  `promotion_allowed_true=0`, `trade_usable_true=0`, and
  `same_tree_practical_closure=null`;
- release remote readback passed, but release readiness still failed on
  `worktree_clean_for_release` and `source_origin_matches_selected_source`.

Loopholes found and classified:

- `extension_complete` is lifecycle proof, not a wrapper-local convenience
  argument. Any practical source that manufactures positive `extension_complete`
  from local metrics or hardcoded truth can falsely convert branch-local
  admission into `promotion_allowed`, `trade_usable`, or `update_goal`.
- Returning the helper result directly is a source-shape bypass unless generic
  calls are checked, not only assignment RHS calls. The checker now scans all
  `practical_admission_flags(...)` call sites for unsafe positive
  `extension_complete`.

Requirement verdict updates:

- Current objective status remains `not_complete`.
- This slice raises the proof standard for practical-use wrappers but does not
  create or prove a practical factor. Verified practical counts remain
  `promotion_allowed_true=0` and `trade_usable_true=0`.
- Next proof requirements are unchanged: current heavy done-definition proof,
  no active/live factor closure blockers, a validated same-tree practical
  closure packet, and release readiness from a clean selected source with source
  origin alignment.
