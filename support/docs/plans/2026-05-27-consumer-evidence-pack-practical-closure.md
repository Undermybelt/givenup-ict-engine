# 2026-05-27 Consumer UX, Evidence Pack, and Practical Closure Tracker

Owner: Codex
Status: active
Route: `sd/ict-engine-maintenance-loop`

## Deterministic Answer

No. I do not have 100% confidence that the objective is complete.

Current-turn evidence still disproves full closure:

- `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260527-closure-snapshot`
  now emits `/private/tmp/ict-engine-goal-20260527-closure-snapshot/objective_closure_snapshot.json`
  with child report timestamps and the exact current blocker surfaces:
  factor `active_claims=10`, `blocking_reasons=["active_claims"]`,
  `attention_by_owner={"codex":10}`; release unresolved
  `["worktree_clean_for_release","remote_readback"]`.
- `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-goal-20260527-done.json`
  reports `completion_ready=false` because all heavy gates are skipped by
  default.
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-goal-20260527-factor-postfix.json`
  was an earlier same-turn checkpoint with `active_claims=6`,
  `live_factor_processes=3`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `attention_groups.by_owner={"codex":6}`.
  The latest coordinated snapshot in this continuation now shows
  `active_claims=10`, `live_factor_processes=0`,
  `blocking_reasons=["active_claims"]`, `promotion_allowed_true=0`,
  `trade_usable_true=0`, and `attention_by_owner={"codex":10}`.
  The earlier classifier fix still stands: one old “live factor process” was a
  diagnostic false positive
  (`tomac_tod_balanced_provider_parity_probe.py`) rather than a real live lane.
- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-goal-20260527-release-resume3.json`
  currently reports unresolved `worktree_clean_for_release` and
  `remote_readback`; `release_version_tag_available` remains skipped behind the
  remote gate.

This file tracks the current closure loop for the user-facing objective:

- audit `ict-engine` from current local state;
- improve consumer UX where the public entry path is confusing or inconsistent;
- keep evidence packets lightweight, reusable, and coordinated;
- keep practical/live usefulness fail-closed until current artifacts prove it;
- commit only a verified coherent slice, not a broad shared-worktree sweep.

## Fresh Findings From 2026-05-27

### F1. Consumer first-run docs were inconsistent

Current proof:

- `AGENT.md` `User Service Contract` says the first run is
  `provider-status -> analyze --demo -> workflow-status --refresh --agent`.
- Before this slice, `AGENT.md` `Zero-Config Consumer Start`,
  `support/docs/consumer-quickstart.md`, and one `README.md` command block still
  showed `workflow-status --human` before `analyze --demo`.

Risk:

- New users get an empty or stale `workflow-status` read before the demo state
  exists.
- The public docs contradict the repo’s own authoritative contract, so a user
  cannot know which sequence is canonical.

This slice:

- Align all public first-run docs to the same canonical order:
  `provider-status -> analyze --demo -> workflow-status --refresh --agent ->
  pre-bayes-status -> policy-training-status`.
- Add automated parity coverage in `support/scripts/done_definition_audit.py`
  so future drift fails the `quickstart_surface` gate instead of surviving as a
  docs-only inconsistency.

Next hardening:

- Fold the compact parity details into a richer current-turn completion audit
  once heavy gates are rerun for this exact tree.

### F2. Full completion is still unproven in current-turn evidence

Current proof:

- Done-definition heavy is now green for the current tree, but factor and
  release closure are still red.
- The latest factor rerun still blocks closure:
  `status=needs_attention`, `active_claims=10`, `invalid_active_claims=0`,
  `live_factor_processes=2`, `trade_usable_true=0`,
  `attention_groups.by_owner={"codex":10}`.
- Same-turn evidence is still time-variant:
  - two stale/duplicate claims were terminalized from current evidence;
  - one probe-only TOMAC script was removed from live-process counts by fixing
    the classifier;
  - the mid-turn checkpoint improved to `6/3`, but later claim activity pushed
    the current closure surface back to `10/0`.
- Fresh release rerun now reports `status=needs_fix` with unresolved
  `worktree_clean_for_release` and `remote_readback`; tag availability is
  still skipped because the audit cannot currently trust the origin tag
  surface.

Implication:

- I cannot truthfully claim the repo is fully audited, consumer-optimized,
  evidence-pack-optimized, or practically ready end-to-end.
- Practical/live usefulness remains blocked by missing promotion/trade-usable
  evidence, not just by documentation quality.

### F3. Evidence-pack coordination is still only partially guarded

Current proof:

- The repo has strong packet conventions in `AGENT.md`,
  `support/docs/plans/2026-05-23-full-audit-bug-ux-closure-plan.md`, and the
  maintenance skill, but this turn still found first-run drift by manual audit.
- Current packet/readiness truth is fragmented across:
  `/tmp/ict-engine-goal-20260527-done.json`,
  `/tmp/ict-engine-goal-20260527-factor-clusters.json`,
  `/tmp/ict-engine-goal-20260527-release-resume3.json`,
  plus older handoff plans.
- This slice adds a coordinated compact parity surface:
  `python3 support/scripts/objective_closure_snapshot.py --compact --check-remotes --output-dir /tmp/ict-engine-goal-20260527-closure-snapshot`
  now emits `/private/tmp/ict-engine-goal-20260527-closure-snapshot/objective_closure_snapshot.json`
  plus the three child audit JSON files under the same root.
- The current compact factor audit now proves both same-owner crowding and one
  explicit family collision:
  `attention_groups.by_owner={"codex":12}` and
  `attention_clusters[0]={owner=codex, scope_family=TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> ParticipationQualityGuard -> NQCadenceLift, claim_count=2}`.
- A later same-turn checkpoint improved that surface:
  `attention_groups.by_owner={"codex":6}` and no duplicate cluster remains.
  The removed live-process false positive was
  `support/scripts/research/tomac_tod_balanced_provider_parity_probe.py`,
  which the compact audit now ignores.
- The latest rerun drifted again to
  `attention_groups.by_owner={"codex":10}` with
  `live_factor_processes=2`, which reinforces the same conclusion: the surface
  is still too active and time-variant to claim practical closure.

Reasonable next solution:

- Keep the new reporting-only cluster surface in the compact factor audit so the
  next turn can externalize or terminalize duplicate families by cluster instead
  of by manual row scanning.
- Still missing:
  - a green same-tree practical closure packet.

### F4. Reusable strategy-library provenance previously leaked caller-local paths

Current proof:

- `support/scripts/research/factor_candidate_pack.py` previously wrote
  `metadata.source_artifact=str(zip_path)` when building strategy-library
  manifests from `freqtrade` backtest zips.
- For absolute zip inputs, this embedded maintainer-local temp/workstation paths
  into exported evidence assets.
- The strategy-library projection then dropped `source_artifact`, weakening the
  provenance trail one layer downstream.

This slice:

- normalize `source_artifact` to a portable reference (`backtest.zip` for
  absolute local inputs);
- preserve the same portable field in the emitted strategy-library manifest;
- add regression coverage so clone-safe provenance stays enforced.

Implication:

- evidence packs become more reusable across clones and machines;
- provenance remains inspectable without pretending a caller-local absolute path
  is a public contract.

## Current Slice Verification Plan

- [x] Re-read routing, repo authority, and active audit plans.
- [x] Run fresh 2026-05-27 compact audits for done-definition, factor hygiene,
      and release readiness.
- [x] Identify at least one concrete user-facing inconsistency from current
      docs/state.
- [x] Patch the public first-run documentation to a single canonical order.
- [x] Add automated quickstart-order parity checks so drift fails fast.
- [x] Run fresh heavy done-definition gates for this tree after choosing a safe
      compute window.
- [ ] Resolve or explicitly isolate active factor claims before making stronger
      factor-completion statements.
- [ ] Build a clean selected export / source parity story before any release
      completion claim.

## Command Evidence

Executed in this turn:

- `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-goal-20260527-done.json`
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-goal-20260527-factor.json`
- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-goal-20260527-release.json`
- `python3 -m unittest support.scripts.tests.test_done_definition_audit.DoneDefinitionAuditTest.test_evaluate_quickstart_surface_fails_when_command_order_drifts support.scripts.tests.test_done_definition_audit.DoneDefinitionAuditTest.test_evaluate_quickstart_surface_passes_when_canonical_blocks_exist -v`
- `python3 -m unittest support.scripts.tests.test_done_definition_audit -v`
- `python3 -m unittest support.scripts.research.tests.test_factor_candidate_pack support.scripts.research.tests.test_factor_candidate_resolver -v`
- `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-goal-20260527-done-parity.json`
- `cargo test ranker_target_export_preserves_exact_provenance_prefixed_branch_paths -- --nocapture`
- `cargo test target_export_uses_exact_branch_trade_direction_over_snapshot_fallback -- --nocapture`
- `cargo test execution_candidate_preserves_trace_branch_path_for_neutral_no_trade -- --nocapture`
- `cargo test execution_candidate_preserves_strict_trend_pullback_trace_path_without_report_branch_path_but_does_not_promote -- --nocapture`
- `cargo test apply_external_scores_matches_provenance_prefixed_rows_from_canonical_branch_input -- --nocapture`
- `cargo clippy --all-targets -- -D warnings`
- `python3 support/scripts/done_definition_audit.py --run-all-heavy --compact --output /tmp/ict-engine-goal-20260527-done-heavy-rerun2.json`
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-goal-20260527-factor-recheck.json`
- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-goal-20260527-release-recheck.json`
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit -v`
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-goal-20260527-factor-clusters.json`
- `python3 -m unittest support.scripts.tests.test_factor_claim_terminalization_audit.FactorClaimTerminalizationAuditTest.test_live_process_classifier_ignores_tomac_provider_parity_probe_diagnostics -v`
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-goal-20260527-factor-after-claim-cleanup.json`
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-goal-20260527-factor-postfix.json`

Readback summary:

- done-definition:
  `status=pass`, `completion_ready=false`, `skip_count=4`.
- done-definition parity slice:
  targeted RED->GREEN quickstart-order tests now pass, full
  `support.scripts.tests.test_done_definition_audit` passes `16` tests, and the
  refreshed compact audit still reports `quickstart_surface=status=pass`.
- done-definition heavy rerun:
  `/tmp/ict-engine-goal-20260527-done-heavy-rerun2.json` now reports
  `status=pass`, `completion_ready=true`, `pass_count=8`, `fail_count=0`.
  The fresh current-turn heavy rerun
  `/tmp/ict-engine-goal-20260527-done-heavy-live.json` also now reports
  `status=pass`, `completion_ready=true`,
  `evidence_level=full_enabled_gate_coverage`, `pass_count=8`,
  `fail_count=0`.
- current bug slices landed before this heavy pass:
  - exact rooted target rows now preserve visible provenance-prefixed branch
    paths while keeping canonical score-key matching in
    `src/belief_core/ranking_label.rs`;
  - neutral non-actionable same-root execution-tree admissions now preserve
    trace branch paths but resolve to `candidate_status=no_trade` instead of
    incorrectly surfacing `execution_observe_only` in `src/analyze_shared.rs`.
- score-apply provenance gap:
  a targeted regression test is now added for canonical external score input
  against exact provenance-prefixed persisted rows; current-tree execution now
  passes.
- portable evidence-pack provenance gap:
  strategy-library manifests built from absolute `freqtrade` zip inputs now
  emit `metadata.source_artifact="backtest.zip"` instead of leaking an
  absolute local path, and the focused `factor_candidate_pack` /
  `factor_candidate_resolver` suite now passes `31` tests.
- factor audit:
  the current rerun at `/tmp/ict-engine-goal-20260527-factor-clusters.json`
  reports `status=needs_attention`, `active_claims=12`,
  `invalid_active_claims=0`, `live_factor_processes=4`,
  `stale_safe_takeover_candidates=6`, `trade_usable_true=0`, and
  `attention_groups.by_owner={"codex":12}`.
  The new compact `attention_clusters` surface also shows the largest duplicate
  family directly:
  `TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> ParticipationQualityGuard -> NQCadenceLift`
  with `claim_count=2`.
  This improves evidence-pack coordination, but it still does not prove
  practical closure because no current-turn rooted lane has become
  `trade_usable=true`.
- later same-turn factor checkpoint:
  `/tmp/ict-engine-goal-20260527-factor-postfix.json` now reports
  `status=needs_attention`, `active_claims=6`, `invalid_active_claims=0`,
  `live_factor_processes=3`, `stale_safe_takeover_candidates=0`,
  `trade_usable_true=0`, and `attention_groups.by_owner={"codex":6}`.
  The code fix also proved one prior live-process blocker was false:
  `tomac_tod_balanced_provider_parity_probe.py` is a read-only diagnostic
  probe and is now excluded from live-process classification.
- latest factor rerun in this continuation:
  the compact audit now reports `status=needs_attention`,
  `active_claims=10`, `invalid_active_claims=0`,
  `live_factor_processes=2`, `stale_safe_takeover_candidates=0`,
  `trade_usable_true=0`, and `attention_groups.by_owner={"codex":10}`.
  The earlier classifier fix still holds, but fresh live launch/replay activity
  has expanded the current blocker surface again.
- compact closure snapshot:
  `/private/tmp/ict-engine-goal-20260527-closure-snapshot/objective_closure_snapshot.json`
  now records the canonical quickstart chain and the coordinated child audit
  evidence roots in one place. Its current blockers are
  `done_definition_not_completion_ready`,
  `factor_closure_blocked`,
  `release_readiness_blocked`.
- release readiness:
  the current rerun at `/tmp/ict-engine-goal-20260527-release-resume3.json`
  reports `status=needs_fix`, `fail_count=2`, unresolved
  `worktree_clean_for_release`, `remote_readback`;
  `release_version_tag_available` is still skipped because the
  remote-readback gate is red.
  The latest fallback probe is stronger because the public HTTPS readback for
  `givenup-ict-engine` now succeeds while the local SSH `origin` transport and
  the release mirror readback still fail.

## Commit Boundary

This current slice is a narrow source+test+tracking-doc repair and is safe to
stage independently if verification stays clean. It does not claim:

- release readiness;
- factor promotion or `trade_usable=true`;
- completion of the full user objective.
