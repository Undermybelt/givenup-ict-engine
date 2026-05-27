# 2026-05-27 Consumer UX, Evidence Pack, and Practical Closure Tracker

Owner: Codex
Status: active
Route: `sd/ict-engine-maintenance-loop`

## Deterministic Answer

No. I do not have 100% confidence that the objective is complete.

Current-turn evidence still disproves full closure:

- `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-goal-20260527-done.json`
  reports `completion_ready=false` because all heavy gates are skipped by
  default.
- `python3 support/scripts/factor_claim_terminalization_audit.py --compact --output /tmp/ict-engine-goal-20260527-factor.json`
  exited `1` with `active_claims=10`, `promotion_allowed_true=0`, and
  `trade_usable_true=0`.
- `python3 support/scripts/release_readiness_audit.py --compact --check-remotes --output /tmp/ict-engine-goal-20260527-release.json`
  reports unresolved `worktree_clean_for_release`,
  `source_origin_matches_selected_source`, and
  `release_version_tag_available`.

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
- Factor claim audit still reports
  `status=needs_attention`, `active_claims=10`, `trade_usable_true=0`.
- Release readiness still reports `status=needs_fix` with three unresolved
  gates.

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
  `/tmp/ict-engine-goal-20260527-factor.json`,
  `/tmp/ict-engine-goal-20260527-release.json`,
  plus older handoff plans.

Reasonable next solution:

- Introduce one compact parity surface that names:
  - the canonical first-run command chain;
  - the current evidence roots for done-definition, factor hygiene, and release;
  - whether practical/trade-usable proof exists for the current tree.

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
- `python3 support/scripts/done_definition_audit.py --compact --output /tmp/ict-engine-goal-20260527-done-parity.json`
- `cargo test ranker_target_export_preserves_exact_provenance_prefixed_branch_paths -- --nocapture`
- `cargo test target_export_uses_exact_branch_trade_direction_over_snapshot_fallback -- --nocapture`
- `cargo test execution_candidate_preserves_trace_branch_path_for_neutral_no_trade -- --nocapture`
- `cargo test execution_candidate_preserves_strict_trend_pullback_trace_path_without_report_branch_path_but_does_not_promote -- --nocapture`
- `cargo clippy --all-targets -- -D warnings`
- `python3 support/scripts/done_definition_audit.py --run-all-heavy --compact --output /tmp/ict-engine-goal-20260527-done-heavy-rerun2.json`

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
- current bug slices landed before this heavy pass:
  - exact rooted target rows now preserve visible provenance-prefixed branch
    paths while keeping canonical score-key matching in
    `src/belief_core/ranking_label.rs`;
  - neutral non-actionable same-root execution-tree admissions now preserve
    trace branch paths but resolve to `candidate_status=no_trade` instead of
    incorrectly surfacing `execution_observe_only` in `src/analyze_shared.rs`.
- factor audit:
  `status=needs_attention`, `active_claims=10`, `live_factor_processes=0`,
  `trade_usable_true=0`.
- release readiness:
  `status=needs_fix`, `fail_count=3`, unresolved
  `worktree_clean_for_release`, `source_origin_matches_selected_source`,
  `release_version_tag_available`.

## Commit Boundary

This current slice is a narrow source+test+tracking-doc repair and is safe to
stage independently if verification stays clean. It does not claim:

- release readiness;
- factor promotion or `trade_usable=true`;
- completion of the full user objective.
